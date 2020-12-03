import socket
import sys
import json
import threading
import sqlite3
from arlo.messages import Message
import arlo.messages
from arlo.camera import Camera
from helpers.safe_print import s_print
import api.api

with sqlite3.connect('arlo.db') as conn:
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS camera (ip text, serial text, hostname text, status text, register_set text)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_serial ON camera (serial)")
    conn.commit()

class CameraThread(threading.Thread):
    def __init__(self,connection,ip,port):
        threading.Thread.__init__(self)
        self.connection = connection
        self.ip = ip
        self.port = port
    
    def run(self):
        #print(f"Connection from {self.ip}")
        while True:
            data = self.connection.recv(1024)
            if len(data) > 0:
                msg = Message.fromNetworkMessage(data.decode(encoding="utf-8"))

                if (msg['Type'] == "registration"):
                    camera = Camera(self.ip, msg)
                    camera.persist()
                    s_print(f"<[{self.ip}][{msg['ID']}] Registration from {msg['SystemSerialNumber']} - {camera.hostname}")
                    registerSet = Message(arlo.messages.REGISTER_SET_INITIAL)
                    camera.sendMessage(registerSet)
                elif (msg['Type'] == "status"):
                    s_print(f"<[{self.ip}][{msg['ID']}] Status from {msg['SystemSerialNumber']}")
                    camera = Camera.from_db_serial(msg['SystemSerialNumber'])
                    camera.update_status(msg)
                    camera.persist()
                elif (msg['Type'] == "pirMotionAlert"):
                    s_print(f"<[{self.ip}][{msg['ID']}] PIR motion alert")
                else:
                    s_print(f"<[{self.ip}][{msg['ID']}] Unknown message")
                    s_print(msg)

                ack = Message(arlo.messages.RESPONSE)
                ack['ID'] = msg['ID']
                s_print(f">[{self.ip}][{msg['ID']}] ACK")
                self.connection.sendall(ack.toNetworkMessage())
                self.connection.close()
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
