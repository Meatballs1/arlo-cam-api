import json
import socket
import sqlite3

from arlo.messages import Message
import arlo.messages
from helpers.safe_print import s_print

class Camera:
    def __init__(self, ip, registration):
        self.registration = registration
        self.ip = ip
        self.id = 0
        self.serial_number = registration["SystemSerialNumber"]
        self.hostname = f"{registration['SystemModelNumber']}-{self.serial_number[-5:]}"
        self.status = None

    def __getitem__(self,key):
        return self.registration[key]

    def sendMessage(self,message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect((self.ip, 4000))
            self.id += 1
            message['ID'] = self.id
            s_print(f">[{self.ip}][{self.id}] {message['Type']}")
            sock.sendall(message.toNetworkMessage())
            data = sock.recv(1024)
            if len(data) > 0:
                ack = Message.fromNetworkMessage(data.decode(encoding="utf-8"))
                if (ack != None):
                    if (ack['ID']==message['ID']):
                        s_print(f"<[{self.ip}][{self.id}] ACK")

    def update_status(self,status):
        self.status = status

    def persist(self):
        with sqlite3.connect('arlo.db') as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO camera VALUES (?,?,?,?,?)", (self.ip, self.serial_number, self.hostname, repr(self.registration), repr(self.status)))
            conn.commit()

    def enablePIR(self):
        enablePIR = Message(arlo.messages.REGISTER_SET_PIR_ARMED)
        sendMessage(enablePIR)

    def setUserStreamActive(self):
        userStreamActive = Message(arlo.messages.REGISTER_SET_USER_STREAM_ACTIVE)
        sendMessage(userStreamActive)

    @staticmethod
    def from_db_serial(serial):
        with sqlite3.connect('arlo.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM camera WHERE serial = ?", (serial,))
            result = c.fetchone()
            if result is not None:
                (ip,serial_number,hostname,registration,status) = result
                _registration = Message.from_json(registration)
                cam = Camera(ip,_registration)
                _status = Message.from_json(status)
                cam.update_status(_status)
                return cam
            else:
                return None
