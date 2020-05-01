#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#
import time
from time import sleep
import argparse
import os
import logging
import threading
import sys
import signal
from string import Template
import datetime
import paho.mqtt.client as mqtt
import json
import socket
from object_store.providers.minio_object_store import MinioObjectStore as store
from data_source.connected_devices.usb_camera import USBCamera as device

format = "%(asctime)s - %(levelname)s: %(threadName)s - %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

mqtt_client_connection_error = ""

# Define event callbacks for MQTT client
def on_connect(client, userdata, flags, rc):
    global mqtt_client_connection_error
    logging.debug("Connected with result code: " + str(rc))
    if rc != 0 and rc != 3:
        mqtt_client_connection_error = "Connection to MQTT broker failed with error code: {0}".format(str(rc))

def on_publish(client, obj, mid):
    logging.debug("mid: " + str(mid))

class App():
    def __init__(self):
        # Initialization function which parses command-line arguments from the user as well as set defaults

        # Variables needed for the internal mechanisms of the class
        self.folder_lock = threading.RLock()
        self.mqtt_client = mqtt.Client()
        self.mqtt_qos_level = 0

        # Assign event callbacks for MQTT client
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_publish = on_publish

        # Default values for the command line arguments
        image_capture_interval_seconds_default = 10
        image_cache_size_default = 10
        image_cleanup_interval_minutes_default = 1
        mqtt_topic_default = 'image/latest'

        # Parse values from the command line
        parser = argparse.ArgumentParser(description='People counter image ingestion service')
        parser.add_argument('--image-capture-interval', '-i', dest='image_capture_interval_seconds', type=int, 
            default=image_capture_interval_seconds_default,
            help="Delay in seconds between image captures (default: {0})".format(str(image_capture_interval_seconds_default)))
        parser.add_argument('--image-cache-size', '-c', dest='image_cache_size', type=int, default=image_cache_size_default,
            help="Number of files to keep in the object store (default: {0})".format(image_cache_size_default))
        parser.add_argument('--image-cleanup-interval', '-u', dest='image_cleanup_interval_minutes', type=int,
            default=image_cleanup_interval_minutes_default,
            help="Delay in minutes between image deletion of images that exceeds the cache size (default: {0}"
                .format(str(image_cleanup_interval_minutes_default)))
        parser.add_argument('--mqtt-username', '-n', dest='mqtt_username', required=True,
            help='Username to access MQTT instance to publish messages about new available images (default: none)')
        parser.add_argument('--mqtt-password', '-p', dest='mqtt_password', required=True,
            help='Password for the MQTT user that can publish messages about new available images (default: none)')
        parser.add_argument('--mqtt-hostname', '-s', dest='mqtt_hostname', required=True,
            help='Hostname of the MQTT instance to publish messages about new available images (default: none)')
        parser.add_argument('--mqtt-port', '-e', dest='mqtt_port', type=int, required=True,
            help="Host port to use to connect to MQTT instance to publish messages about new available images (default: none)")
        parser.add_argument('--mqtt-topic', '-o', dest='mqtt_topic', default=mqtt_topic_default, 
            help="MQTT topic to publish mesages about new available images (default: {0})".format(mqtt_topic_default))
        parser.add_argument('--pulse-device-id', '-v', dest='pulse_device_id', required=True,
            help='Pulse ID associated with the camera device (default: none)')
        parser.add_argument('--object-store-module-arguments', '-b', dest='object_store_module_arguments', required=True,
            help='JSON string with the arguments to the object store module (default: none)')
        parser.add_argument('--data-source-module-arguments', '-a', dest='data_source_module_arguments', required=True,
            help='JSON string with the arguments to the data source module (default: none)')
        self.args = parser.parse_args()
        self.validate()
        self.object_store = store()
        self.object_store.initialize(self.args.object_store_module_arguments)
        self.device = device()
        self.device.initialize(self.args.data_source_module_arguments)
    
    def validate(self):
        # This function does validation of the command-line arguments
        if self.args.image_capture_interval_seconds <= 0:
            raise Exception("The interval to capture images must be a number greater than 0. Value given: {0}"
                .format(self.args.image_capture_interval_seconds))
        if self.args.image_cache_size <= 1:
            raise Exception("The number of images to keep on disk must be at least 2. Value given: {0}"
                .format(self.args.image_cache_size))
        if self.args.image_cleanup_interval_minutes <= 0:
            raise Exception("The interval to clean up images must be a number greater than 0. Value given: {0}"
                .format(self.args.image_cleanup_interval_minutes))

    def start_garbage_collection(self):
        # This function cleans up the directory where images are stored based on a limit on a number of images to keep defined by the user

        while True:
            logging.debug("Sleeping for %d minutes", self.args.image_cleanup_interval_minutes)
            sleep(self.args.image_cleanup_interval_minutes * 60)
            with self.folder_lock:
                logging.debug('Lock acquired')
                self.device.clean_local_cache()
                self.clean_object_store()
                logging.debug('About to release lock')

    def clean_object_store(self):
        try:
            filename_tup = self.object_store.list_objects()
        except Exception as e:
            logging.error("An error occurred that prevented the listing of images in the image folder. Error: %s", str(e))
            return

        # Exit the function if no images are present
        file_list_size = len(filename_tup)
        if file_list_size <= self.args.image_cache_size:
            logging.debug("Image storage folder has not exceeded the max number of files allowed: %d. No clean up performed", self.args.image_cache_size)
            return
        
        # Delete all images past the max number of images allowed. Oldest files are deleted first.
        if file_list_size > 0:
            filename_tup.sort(key= lambda x: x[1])
            logging.debug("Files found: {0}".format(filename_tup))
            number_of_items_to_delete = file_list_size - self.args.image_cache_size
            for i in range(number_of_items_to_delete):
                target_file = filename_tup[i][0]
                try:
                    self.object_store.delete(target_file)
                except Exception as e:
                    logging.error("An error occurred that prevented the deletion of the file ({0}) in the image folder. Error: {1}".format(target_file, str(e)))
                    continue

    def start_image_collection(self):
        logging.info("Starting data collection")
        while True:
            with self.folder_lock:
                logging.debug('Lock acquired')
                try:
                    data = self.device.capture_data()
                    if data.upload_file_exists():
                        storage_path = self.object_store.upload(data.get_upload_file_path())
                        data.set_storage_path(storage_path)
                    data.set_device_id(self.args.pulse_device_id)
                    json_payload = data.to_json()
                    logging.debug("Publishing on topic: '%s' message: '%s'", self.args.mqtt_topic, json_payload)
                    self.mqtt_client.publish(self.args.mqtt_topic, json_payload, self.mqtt_qos_level)
                except Exception as e:
                    logging.error("An error occurred that prevented the capture of data with the device. Error: %s", str(e))
                    logging.info("Sleeping for %d seconds before retrying data capture", self.args.image_capture_interval_seconds)
                    sleep(self.args.image_capture_interval_seconds)
                    logging.debug('About to release lock')
                    continue
                logging.debug('About to release lock')

            logging.debug("Sleeping for %d seconds", self.args.image_capture_interval_seconds)
            sleep(self.args.image_capture_interval_seconds)

    def signal_handler(self, sig, frame):
        logging.info('You pressed Ctrl+C. Exiting program...')
        self.mqtt_client.loop_stop()
        sys.exit(0)

    def run(self):
        # Initialize the MQTT client
        global mqtt_client_connection_error
        logging.info("Connecting to MQTT broker...")
        self.mqtt_client.username_pw_set(self.args.mqtt_username, self.args.mqtt_password)
        self.mqtt_client.connect(self.args.mqtt_hostname, self.args.mqtt_port)
        self.mqtt_client.loop_start()
        sleep(10)
        if mqtt_client_connection_error != "":
            raise Exception(mqtt_client_connection_error)
        logging.info("Success")

        # Start all the threads
        image_collection_thread = threading.Thread(target=self.start_image_collection, name='ImageCollectionThread', daemon=True)
        garbage_collection_thread = threading.Thread(target=self.start_garbage_collection, name='GarbageCollectionThread', daemon=True)
        image_collection_thread.start()
        garbage_collection_thread.start()
        logging.debug('All threads initialized')
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.pause()

app = App()
try:
    app.run()
except Exception as e:
    # Make sure to end the MQTT connection in case of errors
    logging.error("An error occurred that prevented the application from running. Error: %s", str(e))
    if app.mqtt_client is not None:
        app.mqtt_client.loop_stop()
        