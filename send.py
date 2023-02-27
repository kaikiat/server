import time
import imagezmq
import socket
from picamera2 import Picamera2, Preview
from libcamera import Transform

# Receiver address, use ifconfig to check
ADDRESS = 'tcp://192.168.1.21:5556' 
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

if __name__ == "__main__":
    print('Setting up picam2')
    time.sleep(DELAY)
    while True:
        print('Preparing to capture photo')
        start = time.time()
        byte_response = capture_and_send()
        response = int(byte_response.decode())
        end = time.time()
        print(f'{response}, Time taken: {end-start}')