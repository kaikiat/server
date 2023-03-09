import socket
import sys


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# get local machine name
host = "yeet"

port = 5000

# connection to hostname on the port.
s.connect((host, port))
# send the size of the image data
size = len(data)
clientsocket.send(str(size).encode())

# send the actual image data
clientsocket.send(data)
# send a thank you message to the client.
file = "example.jpg"
with open(file, "rb") as f:
    data = f.read()
    s.sendall(data)

# receive data from the server
print(s.recv(1024).decode("utf-8"))

# close the client socket
s.close()