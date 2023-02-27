## Getting started
1. In your local computer, run `python main.py`, make sure you are connected to MDP-1. the server will start accepting images from the RPI.
2. In the RPI, add the following code and change the host address
```
import time
import imagezmq
import socket
from picamera2 import Picamera2, Preview
from libcamera import Transform

ADDRESS = 'tcp://192.168.1.21:5556' # Receiver address, use ifconfig to check
HOST = socket.gethostname()
DELAY = 2

sender = imagezmq.ImageSender(connect_to=ADDRESS)

# Configure picam
picam2 = Picamera2()
config = picam2.create_still_configuration(
    transform=Transform(hflip=True, vflip=True))
picam2.configure(config)
picam2.start()

def capture_and_send():
    try:

        nparray = picam2.capture_array()
        response = sender.send_image(HOST, nparray)
        return response
    except Exception as e:
        print (e.__class__.__name__)
```
3. To invoke the function use
```
byte_response = capture_and_send()
response = int(byte_response.decode())
```