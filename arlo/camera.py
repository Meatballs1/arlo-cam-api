import json
import socket
from arlo.messages import Message
import arlo.messages

class Camera:
    def __init__(self, address, registration):
        self.registration = registration
        self.address = address
        self.id = 0
        self.hostname = f"{registration['SystemModelNumber']}-{registration['SystemSerialNumber'][-5:]}"

    def __getitem__(self,key):
        return self.registration[key]

    def sendMessage(self,message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect((self.address, 4000))
            self.id += 1
            message['ID'] = self.id
            sock.sendall(message.toNetworkMessage())
            data = sock.recv(1024)
            if len(data) > 0:
                ack = Message.fromNetworkMessage(data.decode(encoding="utf-8"))
                if (ack != None):
                    if (ack['ID']==message['ID']):
                        print(f"Client {self.address} ACK")

    def enablePIR(self):
        enablePIR = Message(arlo.messages.REGISTER_SET_PIR_ARMED)
        sendMessage(enablePIR)

    def setUserStreamActive(self):
        userStreamActive = Message(arlo.messages.REGISTER_SET_USER_STREAM_ACTIVE)
        sendMessage(userStreamActive)
