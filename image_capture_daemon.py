import time
from time import sleep
from picamera import PiCamera

class App():
    def __init__(self):
        self.image_capture_folder = '/tmp'
    def run(self):
        while True:
            camera = PiCamera()
            camera.resolution = (1024, 768)
            camera.start_preview()
            sleep(10)
            print('Capturing images to folder ' + self.image_capture_folder + '...')
            for filename in camera.capture_continuous(self.image_capture_folder + '/img{timestamp:%Y-%m-%d-%H-%M-%S}.jpg'):
                print('Captured %s' % filename)
                # Sleep 10 seconds before taking next picture
                sleep(10)

app = App()
app.run()