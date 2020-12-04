import socket
import sys
import json
import threading
import sqlite3
from arlo.messages import Message
import arlo.messages
from arlo.camera import Camera
from helpers.safe_print import s_print
from helpers.recorder import Recorder
import api.api
import time

with sqlite3.connect('arlo.db') as conn:
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS camera (ip text, serial text, hostname text, status text, register_set text)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_serial ON camera (serial)")
    conn.commit()

recorder_lock = threading.Lock()
recorders = {}

TIMEOUT=300

class CameraThread(threading.Thread):
    def __init__(self,connection,ip,port):
        threading.Thread.__init__(self)
        self.connection = connection
        self.ip = ip
        self.port = port
    
    def run(self):
        #print(f"Connection from {self.ip}")
        while True:
            timestr = time.strftime("%Y%m%d-%H%M%S")
            data = self.connection.recv(1024)
            if len(data) > 0:
                msg = Message.fromNetworkMessage(data.decode(encoding="utf-8"))

                if (msg['Type'] == "registration"):
                    camera = Camera(self.ip, msg)
                    camera.persist()
                    s_print(f"<[{self.ip}][{msg['ID']}] Registration from {msg['SystemSerialNumber']} - {camera.hostname}")
                    registerSet = Message(arlo.messages.REGISTER_SET_INITIAL)
                    camera.send_message(registerSet)
                elif (msg['Type'] == "status"):
                    s_print(f"<[{self.ip}][{msg['ID']}] Status from {msg['SystemSerialNumber']}")
                    camera = Camera.from_db_serial(msg['SystemSerialNumber'])
                    camera.update_status(msg)
                    camera.persist()
                elif (msg['Type'] == "alert"):
                    alert_type = msg['AlertType']
                    s_print(f"<[{self.ip}][{msg['ID']}] {msg['AlertType']}")
                    ## TODO More logic around if a recorder has already started. Also should timeout recorder
                    if alert_type == "pirMotionAlert":
                       s_print(f"RECORDING")
                       recorder = Recorder(self.ip, f"/tmp/{self.ip}{timestr}.mpg", TIMEOUT)
                       with recorder_lock:
                           if self.ip in recorders:
                               s_print("Stopping existing recording")
                               recorder[self.ip].stop()
                           recorders[self.ip] = recorder
                       recorder.run()
                    elif alert_type == "motionTimeoutAlert":
                       s_print(f"STOP RECORDING")
                       with recorder_lock:
                           recorders[self.ip].stop()
                           del recorders[self.ip]
                else:
                    s_print(f"<[{self.ip}][{msg['ID']}] Unknown message")
                    s_print(msg)

                ack = Message(arlo.messages.RESPONSE)
                ack['ID'] = msg['ID']
                s_print(f">[{self.ip}][{msg['ID']}] ACK")
                self.connection.sendall(ack.toNetworkMessage())
                self.connection.close()
                break


class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
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
                    threads.append(newthread)
                    newthread.start()
                except KeyboardInterrupt as ki:
                    break
                except Exception as e:
                    print(e)

        for t in threads:
            t.join()


server_thread = ServerThread()
server_thread.start()
flask_thread = api.api.get_thread()
server_thread.join()
flask_thread.join()
