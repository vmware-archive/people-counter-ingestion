import time

class App():
    def __init__(self):
        self.image_capture_folder = '/tmp'
    def run(self):
        while True:
            print("Howdy!  Gig'em!  Whoop!")
            time.sleep(10)

app = App()
app.run()