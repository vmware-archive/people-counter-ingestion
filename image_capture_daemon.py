import time
from time import sleep
from picamera import PiCamera
import argparse
import os

class App():
    def __init__(self):
        # Initialization function which parses command-line arguments from the user as well as set defaults

        # Default values
        self.camera_warmup_delay = 2
        image_storage_folder_default = '/tmp'
        image_resolution_default = [1024, 768]
        image_capture_interval_default = 10
        image_filename_format_default = 'image{timestamp:%Y-%m-%d-%H-%M-%S}.jpg'

        # Parse values from the command line
        parser = argparse.ArgumentParser(description='People counter image ingestion service')
        parser.add_argument('--image-storage-folder', '-f', dest='image_storage_folder', default=image_storage_folder_default, 
            help='Folder in the filesystem where images will be stored (default: {0})'.format(image_storage_folder_default))
        parser.add_argument('--image-resolution', '-r', dest='image_resolution', type=int, nargs=2, default=image_resolution_default, 
            help='Resolution for the images taken by the camera. Must be 2 integers. The max resolution is 2592 1944 (default: {0} {1})'.format(str(image_resolution_default[0]), str(image_resolution_default[1])))
        parser.add_argument('--image-capture-interval', '-i', dest='image_capture_interval', type=int, default=image_capture_interval_default,
            help='Delay in seconds between image captures (default: {0})'.format(str(image_capture_interval_default)))
        parser.add_argument('--image-filename-format', '-o', dest='image_filename_format', default=image_filename_format_default,
            help='''The name given to the image files. Acceptable values are any string plus {counter} and/or {timestamp} (default: {0}). 
                Examples: image{counter}.jpg yields files like image1.jpg, image2.jpg, ...; 
                image{counter:02d}.jpg yields files like image01.jpg, image02.jpg, ...; 
                foo{timestamp}.jpg yields files like foo2013-10-05 12:07:12.346743.jpg, foo2013-10-05 12:07:32.498539, ...;
                bar{timestamp:%H-%M-%S-%f}.jpg yields files like bar12-10-02-561527.jpg, bar12-10-14-905398.jpg;
                foo-bar{timestamp:%H%M%S}-{counter:03d}.jpg yields files like foo-bar121002-001.jpg, foo-bar121013-002.jpg, foo-bar121014-003.jpg, ...'''.format(image_filename_format_default))
        self.args = parser.parse_args()
        self.validate(args)
    
    def validate(self, args):
        # This function does validation of the command-line arguments

        if not os.access(args.image_storage_folder, os.W_OK):
            raise Exception('The folder {0} specified for image storage is not writtable'.format(args.image_storage_folder))
        if args.image_resolution[0] > 2592 or args.image_resolution[1] > 1944:
            raise Exception('The resolution provided {0} exceeds the max allowed resolution 2592x1944 for the camera'.format(args.image_resolution))
        if '{counter}' not in args.image_filename_format and '{timestamp}' not in args.image_filename_format:
            raise Exception('The image file format provided did not contain {counter} or {timestamp} in it')

    def run(self):
        while True:
            camera = PiCamera()
            camera.resolution = tuple(self.args.image_resolution)
            camera.start_preview()
            sleep(self.camera_warmup_delay)
            print('Capturing images to folder ' + self.args.image_storage_folder + '...')
            for filename in camera.capture_continuous(self.args.image_storage_folder + '/' + self.args.image_filename_format):
                print('Captured %s' % filename)
                # Sleep 10 seconds before taking next picture
                sleep(self.args.image_capture_interval)

app = App()
app.run()