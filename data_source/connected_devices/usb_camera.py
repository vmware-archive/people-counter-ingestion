
#
# Copyright © 2019 VMware, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: BSD-2-Clause
#
import numpy as np
import cv2 as cv
from time import sleep
import logging
import json
import os
from data_source.data_source import DataSourceInterface
from data_source.data import CapturedData
import datetime
import uuid
import atexit

class USBCamera(DataSourceInterface):
    
    def initialize(self, jsonArgs):
        # The function should initialize any connections that need
        # to be made or any variables that will be required
        format = "%(asctime)s - %(levelname)s: %(threadName)s - %(message)s"
        logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")
        
        # Parse JSON arguments
        args = json.loads(jsonArgs)

        # Setup default values
        image_filename_prefix_default = "image-"
        self.image_filename_extension_default = ".jpg"
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
        if 'image_filename_prefix' in args:
            self.image_filename_prefix = args['image_filename_prefix']
        else:
            self.image_filename_prefix = image_filename_prefix_default
        if 'image_filename_extension' in args:
            self.image_filename_extension = args['image_filename_extension']
        else:
            self.image_filename_extension = self.image_filename_extension_default
        if 'image_cache_size' in args:
            self.image_cache_size = args['image_cache_size']
        else:
            self.image_cache_size = image_cache_size_default
        if 'device_index' in args:
            self.device_index = args['device_index']
        else:
            raise Exception("You must specify a device index for the camera you wish to use to take photos")
            
        self.camera = cv.VideoCapture(self.device_index)
        self.validate()

        # Change the camera settings  
        self.camera.set(cv.CAP_PROP_FRAME_WIDTH, self.image_resolution[0])
        self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, self.image_resolution[1])
        # Camera warm-up time
        sleep(camera_warmup_delay)

    def capture_data(self):
        """
        Takes a picture with the USB camera

        Returns:
        CapturedData: Object that holds the file location and the creation timestamp
        """
        logging.info("Capturing image to folder %s...", self.image_storage_folder)
        filename = self.generate_image_filename()
        filepath = os.path.join(self.image_storage_folder, filename)
        try:
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Can't receive frame (stream end?). Exiting ...")
            cv.imwrite(filepath, frame)
        except Exception as e:
            logging.error("An error occurred that prevented the capture of the image with the camera. Error: %s", str(e))
            raise e
        data = CapturedData(datetime.datetime.now().timestamp(), upload_file_path=filepath)
        logging.debug("Captured image %s", filename)

        return data

    def clean_local_cache(self):
        try:
            filenames = os.listdir(self.image_storage_folder)
        except Exception as e:
            logging.error("An error occurred that prevented the listing of images in the image folder. Error: %s", str(e))
            return

        full_file_paths = []
        logging.debug("Looking for files with extention %s", self.image_filename_extension)

        # Find all the files with a particualar extention
        for filename in filenames:
            if self.image_filename_extension in filename:
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
        if 'jpg' not in self.image_filename_extension and 'png' not in self.image_filename_extension:
            logging.warn("The image filename extension provided '{0}' is not supported. Supported filename extensions are: .jpg and .png. The default extension: {1} will be used"
                .format(self.image_filename_extension, self.image_filename_extension_default))
            self.image_filename_extension = self.image_filename_extension_default
        if self.image_cache_size <= 1:
            raise Exception("The number of images to keep on disk must be at least 2. Value given: {0}"
                .format(self.image_cache_size))
        if not self.camera.isOpened():
            raise Exception("Could not open video device to use to capture pictures. Check the permissions of the user running the program and try again.")
        
    def generate_image_filename(self):
        # Helper function to get the formatted filename for continues image capturing

        logging.debug("Generating filename with prefix '%s' and extension '%s'", self.image_filename_prefix, self.image_filename_extension)
        formatted_filename =  self.image_filename_prefix + str(uuid.uuid4()) + self.image_filename_extension

        return formatted_filename

    @atexit.register
    def release_camera(self):
        self.camera.release()

