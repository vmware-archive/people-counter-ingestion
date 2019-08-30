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

format = "%(asctime)s - %(levelname)s: %(threadName)s - %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

class App():
    def __init__(self):
        # Initialization function which parses command-line arguments from the user as well as set defaults

        # Default values
        self.image_cache_size = 10
        self.image_cleanup_interval_minutes = 1
        self.camera_warmup_delay = 2
        self._filename_counter = 1
        self.folder_lock = threading.RLock()
        self.camera = PiCamera()
        image_storage_folder_default = '/tmp'
        image_resolution_default = [1024, 768]
        image_capture_interval_seconds_default = 10
        image_filename_template_default = 'image{timestamp:%Y-%m-%d-%H-%M-%S}.jpg'
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
            help='Folder in the filesystem where images will be stored (default: {0})'.format(image_storage_folder_default))
        parser.add_argument('--image-resolution', '-r', dest='image_resolution', type=int, nargs=2, default=image_resolution_default, 
            help='Resolution for the images taken by the camera. Must be 2 integers. The max resolution is 2592 1944 (default: {0} {1})'.format(str(image_resolution_default[0]), str(image_resolution_default[1])))
        parser.add_argument('--image-capture-interval', '-i', dest='image_capture_interval_seconds', type=int, default=image_capture_interval_seconds_default,
            help='Delay in seconds between image captures (default: {0})'.format(str(image_capture_interval_seconds_default)))
        parser.add_argument('--image-filename-template', '-t', dest='image_filename_template', default=image_filename_template_default,
            help=image_filename_template_help)
        self.args = parser.parse_args()
        self.validate()
    
    def validate(self):
        # This function does validation of the command-line arguments

        if not os.access(self.args.image_storage_folder, os.W_OK):
            raise Exception('The folder {0} specified for image storage is not writtable'.format(self.args.image_storage_folder))
        if self.args.image_resolution[0] > self.camera.MAX_RESOLUTION[0] or self.args.image_resolution[1] > self.camera.MAX_RESOLUTION[1]:
            raise Exception('The resolution provided {0} exceeds the max allowed resolution 2592x1944 for the camera'.format(self.args.image_resolution))
        if '{counter' not in self.args.image_filename_template and '{timestamp' not in self.args.image_filename_template:
            raise Exception('The image file template provided {0} did not contain {{counter}} or {{timestamp}} in it'.format(self.args.image_filename_template))

    def start_garbage_collection(self):
        # This function cleans up the directory where images are stored based on a limit on a number of images to keep defined by the user

        logging.info("Starting garbage collection on folder %s", self.args.image_storage_folder)
        while True:
            logging.debug("Sleeping for %d minutes", self.image_cleanup_interval_minutes)
            sleep(self.image_cleanup_interval_minutes * 60)

            filenames = os.listdir(self.args.image_storage_folder)
            full_file_paths = []
            search_criteria = self.args.image_filename_template.split('.')
            search_criteria = search_criteria[len(search_criteria) - 1]
            logging.debug("Looking for files with extention {0}".format(search_criteria))

            # Find all the files with a particualar extention
            for filename in filenames:
                if search_criteria in filename:
                    full_file_paths.append(os.path.join(self.args.image_storage_folder, filename))

            # Exit the function if no images are present
            file_list_size = len(full_file_paths)
            if file_list_size <= self.image_cache_size:
                logging.debug("Image storage folder has not exceeded the max number of files allowed: {0}. No clean up performed".format(str(self.image_cache_size)))
                continue
            
            # Delete all images past the max number of images allowed. Oldest files are deleted first.
            if file_list_size > 0:
                full_file_paths.sort(key=os.path.getctime)
                logging.debug("Files found: %s",full_file_paths)
                number_of_items_to_delete = file_list_size - self.image_cache_size
                logging.debug("Lock acquired")
                with self.folder_lock:
                    for i in range(number_of_items_to_delete):
                        logging.debug("Deleting file: {0}".format(full_file_paths[i]))
                        os.remove(full_file_paths[i])
                    logging.debug("About to release lock")

    def start_image_collection(self):
        with self.camera:
            self.camera.resolution = tuple(self.args.image_resolution)
            self.camera.start_preview()
            # Camera warm-up time
            sleep(self.camera_warmup_delay)

            logging.info('Capturing images to folder %s...', self.args.image_storage_folder)
            for filename in self.camera.capture_continuous(os.path.join(self.args.image_storage_folder, self.args.image_filename_template)):
                logging.debug('Captured image %s', filename)
                # Sleep 10 seconds before taking next picture
                logging.debug("Lock acquired")
                with self.folder_lock:
                    logging.debug("Sleeping for %d seconds", self.args.image_capture_interval_seconds)
                    sleep(self.args.image_capture_interval_seconds)
                    logging.debug("About to release lock")

    def get_image_filename(self):
        formatted_filename = self.args.image_filename_template
        if '{counter}' in self.args.image_filename_template:
            formatted_filename = self.args.image_filename_template.format(counter = self._filename_counter)
            self._filename_counter += 1
        if '{timestamp}' in self.args.image_filename_template:
            formatted_filename = self.args.image_filename_template.format(timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
        return formatted_filename

    def signal_handler(self, sig, frame):
        logging.info('You pressed Ctrl+C. Exiting program...')
        sys.exit(0)

    def run(self):
        image_collection_thread = threading.Thread(target=self.start_image_collection, name="ImageCollectionThread", daemon=True)
        garbage_collection_thread = threading.Thread(target=self.start_garbage_collection, name="GarbageCollectionThread", daemon=True)
        image_collection_thread.start()
        garbage_collection_thread.start()
        logging.debug("All threads initialized")
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.pause()

app = App()
app.run()