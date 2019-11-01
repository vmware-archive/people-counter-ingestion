import time
from time import sleep
from picamera import PiCamera
import argparse
import os
import logging
import threading
import sys
import signal
from string import Template
import datetime
import paho.mqtt.client as mqtt

format = "%(asctime)s - %(levelname)s: %(threadName)s - %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

mqtt_client_connection_error = ""

# Define event callbacks for MQTT client
def on_connect(client, userdata, flags, rc):
    global mqtt_client_connection_error
    logging.debug("Connected with result code: " + str(rc))
    if rc != 0 or rc != 3:
        mqtt_client_connection_error = "Connection to MQTT broker failed with error code: {0}".format(str(rc))

def on_message(client, obj, msg):
    logging.debug(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(client, obj, mid):
    logging.debug("mid: " + str(mid))

class App():
    def __init__(self):
        # Initialization function which parses command-line arguments from the user as well as set defaults

        # Variables needed for the internal mechanisms of the class
        self.camera_warmup_delay = 2
        self._filename_counter = 1
        self.folder_lock = threading.RLock()
        self.camera = PiCamera()
        self.mqtt_client = mqtt.Client()
        self.mqtt_qos_level = 0

        # Assign event callbacks for MQTT client
        self.mqtt_client.on_message = on_message
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_publish = on_publish

        # Default values for the command line arguments
        self.image_filename_template_default = "image{timestamp:%Y-%m-%d-%H-%M-%S}.jpg"
        image_storage_folder_default = '/tmp'
        image_resolution_default = [1024, 768]
        image_capture_interval_seconds_default = 10
        image_cache_size_default = 10
        image_cleanup_interval_minutes_default = 1
        mqtt_topic_default = 'image/latest'
        image_filename_template_help = '''The name given to the image files. 
                Acceptable values are any string plus {counter} and/or {timestamp} (default: image{timestamp:%%Y-%%m-%%d-%%H-%%M-%%S}.jpg).
                Examples: image{counter}.jpg yields files like image1.jpg, image2.jpg, ...;
                image{counter:02d}.jpg yields files like image01.jpg, image02.jpg, ...;
                foo{timestamp}.jpg yields files like foo2013-10-05 12:07:12.346743.jpg, foo2013-10-05 12:07:32.498539, ...;
                bar{timestamp:%%H-%%M-%%S-%%f}.jpg yields files like bar12-10-02-561527.jpg, bar12-10-14-905398.jpg;
                foo-bar{timestamp:%%H%%M%%S}-{counter:03d}.jpg yields files like foo-bar121002-001.jpg, foo-bar121013-002.jpg, foo-bar121014-003.jpg, ...''' 

        # Parse values from the command line
        parser = argparse.ArgumentParser(description='People counter image ingestion service')
        parser.add_argument('--image-storage-folder', '-d', dest='image_storage_folder', default=image_storage_folder_default, 
            help="Folder in the filesystem where images will be stored (default: {0})".format(image_storage_folder_default))
        parser.add_argument('--image-resolution', '-r', dest='image_resolution', type=int, nargs=2, default=image_resolution_default, 
            help="Resolution for the images taken by the camera. Must be 2 integers (default: {0} {1})"
                .format(str(image_resolution_default[0]), str(image_resolution_default[1])))
        parser.add_argument('--image-capture-interval', '-i', dest='image_capture_interval_seconds', type=int, 
            default=image_capture_interval_seconds_default,
            help="Delay in seconds between image captures (default: {0})".format(str(image_capture_interval_seconds_default)))
        parser.add_argument('--image-filename-template', '-t', dest='image_filename_template', default=self.image_filename_template_default,
            help=image_filename_template_help)
        parser.add_argument('--image-cache-size', '-c', dest='image_cache_size', type=int, default=image_cache_size_default,
            help="Number of images to keep on disk (default: {0})".format(image_cache_size_default))
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
        self.args = parser.parse_args()
        self.validate()
    
    def validate(self):
        # This function does validation of the command-line arguments

        if not os.access(self.args.image_storage_folder, os.F_OK):
            raise Exception("The folder ({0}) specified for image storage does not exist"
                .format(self.args.image_storage_folder))
        if not os.access(self.args.image_storage_folder, os.R_OK):
            raise Exception("The folder ({0}) specified for image storage is not readable"
                .format(self.args.image_storage_folder))
        if not os.access(self.args.image_storage_folder, os.X_OK):
            raise Exception("The folder ({0}) specified for image storage does not have execute permissions"
                .format(self.args.image_storage_folder))
        if not os.access(self.args.image_storage_folder, os.W_OK):
            raise Exception("The folder ({0}) specified for image storage is not writtable"
                .format(self.args.image_storage_folder))
        if self.args.image_resolution[0] > self.camera.MAX_RESOLUTION[0] or self.args.image_resolution[1] > self.camera.MAX_RESOLUTION[1]:
            raise Exception("The resolution provided ({0}) exceeds the max allowed resolution ({1}) for the camera"
                .format(self.args.image_resolution, self.camera.MAX_RESOLUTION))
        if '{counter' not in self.args.image_filename_template and '{timestamp' not in self.args.image_filename_template:
            logging.warn("The image file template provided: {0} did not contain {{counter}} or {{timestamp}} in it. The default template: {1} will be used"
                .format(self.args.image_filename_template, self.image_filename_template_default))
            self.args.image_filename_template = self.image_filename_template_default
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

        logging.info("Starting garbage collection on folder %s", self.args.image_storage_folder)
        while True:
            logging.debug("Sleeping for %d minutes", self.args.image_cleanup_interval_minutes)
            sleep(self.args.image_cleanup_interval_minutes * 60)

            try:
                filenames = os.listdir(self.args.image_storage_folder)
            except Exception as e:
                logging.error("An error occurred that prevented the listing of images in the image folder. Error: %s", str(e))
                continue

            full_file_paths = []
            search_criteria = self.args.image_filename_template.split('.')
            search_criteria = search_criteria[len(search_criteria) - 1]
            logging.debug("Looking for files with extention %s", search_criteria)

            # Find all the files with a particualar extention
            for filename in filenames:
                if search_criteria in filename:
                    full_file_paths.append(os.path.join(self.args.image_storage_folder, filename))

            # Exit the function if no images are present
            file_list_size = len(full_file_paths)
            if file_list_size <= self.args.image_cache_size:
                logging.debug("Image storage folder has not exceeded the max number of files allowed: %d. No clean up performed", self.args.image_cache_size)
                continue
            
            # Delete all images past the max number of images allowed. Oldest files are deleted first.
            if file_list_size > 0:
                try:
                    full_file_paths.sort(key=os.path.getctime)
                except Exception as e:
                    logging.error("An error occurred that prevented the access to creation time of files in the image folder. Error: %s", str(e))
                    continue
                logging.debug("Files found: {0}".format(full_file_paths))
                number_of_items_to_delete = file_list_size - self.args.image_cache_size
                logging.debug('Lock acquired')
                with self.folder_lock:
                    for i in range(number_of_items_to_delete):
                        logging.debug("Deleting file: %s", full_file_paths[i])
                        try:
                            os.remove(full_file_paths[i])
                        except Exception as e:
                            logging.error("An error occurred that prevented the deletion of the file ({0}) in the image folder. Error: {1}".format(full_file_paths[i], str(e)))
                            continue
                    logging.debug('About to release lock')

    def start_image_collection(self):
        with self.camera:
            self.camera.resolution = tuple(self.args.image_resolution)
            self.camera.start_preview()
            # Camera warm-up time
            sleep(self.camera_warmup_delay)

            logging.info("Capturing images to folder %s...", self.args.image_storage_folder)
            while True:
                logging.debug('Lock acquired')
                with self.folder_lock:
                    filename = self.generate_image_filename()
                    try:
                        self.camera.capture(os.path.join(self.args.image_storage_folder, filename))
                        payload = "Image {0} is available".format(filename)
                        logging.debug("Publishing on topic '%s' message '%s'", self.args.mqtt_topic, payload)
                        self.mqtt_client.publish(self.args.mqtt_topic, payload, self.mqtt_qos_level)
                    except Exception as e:
                        logging.error("An error occurred that prevented the capture of the image with the camera. Error: %s", str(e))
                        logging.info("Sleeping for %d seconds before retrying image capture", self.args.image_capture_interval_seconds)
                        sleep(self.args.image_capture_interval_seconds)
                        logging.debug('About to release lock')
                        continue
                    logging.debug('About to release lock')
                logging.debug("Captured image %s", filename)

                logging.debug("Sleeping for %d seconds", self.args.image_capture_interval_seconds)
                sleep(self.args.image_capture_interval_seconds)


    def generate_image_filename(self):
        # Helper function to get the formatted filename for continues image capturing

        logging.debug("Generating filename from template %s", self.args.image_filename_template)
        formatted_filename =  self.args.image_filename_template.format(counter = self._filename_counter, timestamp = datetime.datetime.now())
        if '{counter' in self.args.image_filename_template:
            self._filename_counter += 1

        return formatted_filename

    def signal_handler(self, sig, frame):
        logging.info('You pressed Ctrl+C. Exiting program...')
        self.mqtt_client.loop_stop()
        sys.exit(0)

    def run(self):
        # Initialize the MQTT client
        global mqtt_client_connection_error
        logging.info("Connecting to MQTT broker...")
        self.mqtt_client.username_pw_set(self.args.mqtt_username, self.mqtt_client.mqtt_password)
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
    app.mqtt_client.loop_stop()