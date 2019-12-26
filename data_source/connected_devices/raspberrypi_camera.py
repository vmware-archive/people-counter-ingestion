
#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#
from picamera import PiCamera
from time import sleep
import logging
import json
import os
from data_source.data_source import DataSourceInterface
from data_source.data import CapturedData
import datetime

class RaspberryPiCamera(DataSourceInterface):
    
    def initialize(self, jsonArgs):
        # The function should initialize any connections that need
        # to be made or any variables that will be required
        format = "%(asctime)s - %(levelname)s: %(threadName)s - %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")
        
        # Parse JSON arguments
        args = json.loads(jsonArgs)

        # Setup default values
        self.image_filename_template_default = "image{timestamp:%Y-%m-%d-%H-%M-%S}.jpg"
        image_storage_folder_default = '/tmp'
        image_resolution_default = [1024, 768]
        image_cache_size_default = 10
        camera_warmup_delay = 2
        self._filename_counter = 1

        # Initialize variables to defaults if they were not provided in the JSON payload
        if 'image_storage_folder' in args:
            self.image_storage_folder = args['image_storage_folder']
        else:
            self.image_storage_folder = image_storage_folder_default
        if 'image_resolution' in args:
            self.image_resolution = args['image_resolution']
        else:
            self.image_resolution = image_resolution_default
        if 'image_filename_template' in args:
            self.image_filename_template = args['image_filename_template']
        else:
            self.image_filename_template = self.image_filename_template_default
        if 'image_cache_size' in args:
            self.image_cache_size = args['image_cache_size']
        else:
            self.image_cache_size = image_cache_size_default
            
        self.camera = PiCamera()
        self.validate()

        # Change the camera settings  
        self.camera.resolution = tuple(self.image_resolution)
        self.camera.start_preview()
        # Camera warm-up time
        sleep(camera_warmup_delay)

    def capture_data(self):
        """
        Uploads a file to Minio.

        The function uploads a file from the path in the filesystem specified and uploads
        it to a bucket in Minio.

        Parameters:
        filepath (string): The absolute path of the file to upload
        bucket_name (string): Optional argument to indicate the bucket to use to upload the file

        Returns:
        string: The location of the image in Minio
        """
        logging.info("Capturing image to folder %s...", self.image_storage_folder)
        filename = self.generate_image_filename()
        try:
            filepath = os.path.join(self.image_storage_folder, filename)
            self.camera.capture(filepath)
            data = CapturedData(datetime.datetime.now().timestamp(), upload_file_path=filepath)
        except Exception as e:
            logging.error("An error occurred that prevented the capture of the image with the camera. Error: %s", str(e))
                
        logging.debug("Captured image %s", filename)

        return data

    def clean_local_cache(self):
        try:
            filenames = os.listdir(self.image_storage_folder)
        except Exception as e:
            logging.error("An error occurred that prevented the listing of images in the image folder. Error: %s", str(e))
            return

        full_file_paths = []
        search_criteria = self.image_filename_template.split('.')
        search_criteria = search_criteria[len(search_criteria) - 1]
        logging.debug("Looking for files with extention %s", search_criteria)

        # Find all the files with a particualar extention
        for filename in filenames:
            if search_criteria in filename:
                full_file_paths.append(os.path.join(self.image_storage_folder, filename))

        # Exit the function if no images are present
        file_list_size = len(full_file_paths)
        if file_list_size <= self.image_cache_size:
            logging.debug("Image storage folder has not exceeded the max number of files allowed: %d. No clean up performed", self.image_cache_size)
            return
        
        # Delete all images past the max number of images allowed. Oldest files are deleted first.
        if file_list_size > 0:
            try:
                full_file_paths.sort(key=os.path.getctime)
            except Exception as e:
                logging.error("An error occurred that prevented the access to creation time of files in the image folder. Error: %s", str(e))
                return
            logging.debug("Files found: {0}".format(full_file_paths))
            number_of_items_to_delete = file_list_size - self.image_cache_size
            for i in range(number_of_items_to_delete):
                logging.debug("Deleting file: %s", full_file_paths[i])
                try:
                    os.remove(full_file_paths[i])
                except Exception as e:
                    logging.error("An error occurred that prevented the deletion of the file ({0}) in the image folder. Error: {1}".format(full_file_paths[i], str(e)))
                    continue

    ######################HELPER METHODS########################

    def validate(self):
        if not os.access(self.image_storage_folder, os.F_OK):
            raise Exception("The folder ({0}) specified for image storage does not exist"
                .format(self.image_storage_folder))
        if not os.access(self.image_storage_folder, os.R_OK):
            raise Exception("The folder ({0}) specified for image storage is not readable"
                .format(self.image_storage_folder))
        if not os.access(self.image_storage_folder, os.X_OK):
            raise Exception("The folder ({0}) specified for image storage does not have execute permissions"
                .format(self.image_storage_folder))
        if not os.access(self.image_storage_folder, os.W_OK):
            raise Exception("The folder ({0}) specified for image storage is not writtable"
                .format(self.image_storage_folder))
        if self.image_resolution[0] > self.camera.MAX_RESOLUTION[0] or self.image_resolution[1] > self.camera.MAX_RESOLUTION[1]:
            raise Exception("The resolution provided ({0}) exceeds the max allowed resolution ({1}) for the camera"
                .format(self.image_resolution, self.camera.MAX_RESOLUTION))
        if '{counter' not in self.image_filename_template and '{timestamp' not in self.image_filename_template:
            logging.warn("The image file template provided: {0} did not contain {{counter}} or {{timestamp}} in it. The default template: {1} will be used"
                .format(self.image_filename_template, self.image_filename_template_default))
            self.image_filename_template = self.image_filename_template_default
        if self.image_cache_size <= 1:
            raise Exception("The number of images to keep on disk must be at least 2. Value given: {0}"
                .format(self.image_cache_size))
        
    def generate_image_filename(self):
        # Helper function to get the formatted filename for continues image capturing

        logging.debug("Generating filename from template %s", self.image_filename_template)
        formatted_filename =  self.image_filename_template.format(counter = self._filename_counter, timestamp = datetime.datetime.now())
        if '{counter' in self.image_filename_template:
            self._filename_counter += 1

        return formatted_filename

