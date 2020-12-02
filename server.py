import socket
import sys
import json
import threading
from arlo.messages import Message
import arlo.messages
from arlo.camera import Camera

cameras = {}
cameraLock = threading.Lock()
class CameraThread(threading.Thread):
    def __init__(self,connection,ip,port):
        threading.Thread.__init__(self)
        self.connection = connection
        self.ip = ip
        self.port = port
    
    def run(self):
        while True:
            print(f"Connection from {self.ip}")
            data = self.connection.recv(1024)
            if len(data) > 0:
                msg = Message.fromNetworkMessage(data.decode(encoding="utf-8"))
                ack = Message(arlo.messages.RESPONSE)
                ack['ID'] = msg['ID']
                self.connection.sendall(ack.toNetworkMessage())
                self.connection.close()

                if (msg['Type'] == "registration"):
                    camera = Camera(self.ip, msg)
                    print(f"Registration from {self.ip} - {msg['SystemSerialNumber']} - {camera.hostname}")
                    cameraLock.acquire()
                    try:
                        cameras[msg['SystemSerialNumber']] = camera
                    finally:
                        cameraLock.release()
                    registerSet = Message(arlo.messages.REGISTER_SET_INITIAL)
                    print("Sending initial register set")
                    camera.sendMessage(registerSet)
                elif (msg['Type'] == "status"):
                    print(f"Status from {ip} - {msg['SystemSerialNumber']}")
                break

threads = []
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('', 4000)
    sock.bind(server_address)

    sock.listen(12)
    while True:
        try:
            (connection, (ip, port)) = sock.accept()
            newthread = CameraThread(connection,ip,port)
            newthread.start()
            threads.append(newthread)
        except KeyboardInterrupt as ki:
            break
        except Exception as e:
            print(e)

for t in threads:
    t.join()
