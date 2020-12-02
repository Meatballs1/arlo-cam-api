import socket
import sys
import json
import arlo.messages
from arlo.camera import Camera

cameras = {}
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('', 4000)
    sock.bind(server_address)

    sock.listen(1)
    try:
        while 1:
            connect, client_address = sock.accept()
            print(f"Connection from {client_address}")
            data = connect.recv(1024)
            msg = Message.fromNetworkMessage(data.decode(encoding="utf-8"))
            ack = Message(messages.RESPONSE)
            ack['ID'] = msg['ID']
            connect.sendall(ack.toNetworkMessage())
            connect.close()

            if (msg['Type'] == "registration"):
                print(f"Registration from {client_address} - {msg['SystemSerialNumber']}")
                print(msg)
                camera = Camera(client_address[0], msg)
                cameras[msg['SystemSerialNumber']] = camera
                registerSet = Message(messages.REGISTER_SET_INITIAL)
                print("Sending initial register set")
                camera.sendMessage(registerSet)
            elif (msg['Type'] == "status"):
                print(f"Status from {client_address} - {msg['SystemSerialNumber']}")
                print(msg)
    finally:
        sock.close()
       
