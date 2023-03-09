import os
import shutil
import socket
import sys
import io
import time
from ultralytics import YOLO
from PIL import Image
import cv2
# create a socket object
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
count =0
# get local machine name
host = socket.gethostname()
print(host)
port = 5000
#
# # create a socket object
# # bind to the port
# serversocket.bind(("192.168.24.156", port))
serversocket.bind(("192.168.1.21", port))


# model = YOLO('best.pt')
model = YOLO('best2.pt')
#from cv2
#img = cv2.imread("received_image.jpg")
#img = cv2.imread("test.jpg")

time_limit = 1 # seconds

try:
    shutil.rmtree("./runs/detect/predict")
except:
    pass
while True:
    check = 0
    try:
        print("waiting for connection")
        # queue up to 5 requests
        serversocket.listen(5)
        # establish a connection
        clientsocket, addr = serversocket.accept()
        clientsocket.settimeout(time_limit)
        print("Got a connection from %s" % str(addr))

        # receive the size of the image data
        while True:
            try:
                size_data = clientsocket.recv(1024)
                size_data = size_data.tobytes()
                print("received length")
                size = int.from_bytes(size_data,byteorder='big')

                # receive the actual image data
                data = b''
                received_size = 0


                while received_size < size:
                    #print("receiving image in parts")
                    part = clientsocket.recv(1024)
                    data += part
                    received_size += len(part)

            except socket.timeout:
                print("Timeout occurred while receiving data. Breaking out of loop.")
                print("Result:" + "-1")

                break
            except Exception as e:
                clientsocket.close()


        #img = Image.open(io.BytesIO(data))
        # validate that all of the data has been received
        if len(data) != size:
            print("Error: Incomplete data received")

        else:
            print("received image")
            with open(str(count) + ".jpg", "wb") as f:
                f.write(data)
            f.close()
            img = str(count) + ".jpg"

            print("writing to empty file")
            results = model.predict(source=img,save=True)

            print("Sending results")
            for box in results[0].boxes:
                for c in box.cls:
                    check=1
                    finalresult = model.names[int(c)]
                    print(model.names[int(c)])
                    message_bytes = finalresult.encode("utf-8")
                    clientsocket.send(message_bytes)
            os.remove(str(count) + ".jpg")
            count += 1
        if (check == 0):
            print("Result:" + "-1")
            clientsocket.send("-1".encode("utf-8"))


        clientsocket.close()
    except Exception as e:
        print(e)
        continue

