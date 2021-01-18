import socket
import sys
import json
import threading
import sqlite3
import time
import yaml

from arlo.messages import Message
from arlo.socket import ArloSocket
import arlo.messages
from arlo.camera import Camera
from helpers.safe_print import s_print
from helpers.recorder import Recorder
from helpers.webhook_manager import WebHookManager
import api.api

with open(r'config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

webhook_manager = WebHookManager(config)

with sqlite3.connect('arlo.db') as conn:
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS camera (ip text, serialnumber text, hostname text, status text, register_set text, friendlyname text)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_serialnumber ON camera (serialnumber)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_ip ON camera (ip)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_friendlyname ON camera (friendlyname)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_camera_hostname ON camera (hostname)")
    conn.commit()

recorder_lock = threading.Lock()
recorders = {}


WIFI_COUNTRY_CODE=config['WifiCountryCode']
MOTION_RECORDING_TIMEOUT=config['MotionRecordingTimeout']
AUDIO_RECORDING_TIMEOUT=config['AudioRecordingTimeout']
RECORDING_BASE_PATH=config['RecordingBasePath']
RECORD_ON_MOTION_ALERT=config['RecordOnMotionAlert']
RECORD_ON_AUDIO_ALERT=config['RecordOnAudioAlert']

class ConnectionThread(threading.Thread):
    def __init__(self,connection,ip,port):
        threading.Thread.__init__(self)
        self.connection = ArloSocket(connection)
        self.ip = ip
        self.port = port

    def run(self):
        while True:
            timestr = time.strftime("%Y%m%d-%H%M%S")
            msg = self.connection.receive()
            if msg != None:
                if (msg['Type'] == "registration"):
                    camera = Camera.from_db_serial(msg['SystemSerialNumber'])
                    if camera is None:
                        camera = Camera(self.ip, msg)
                    else:
                        camera.registration = msg
                    camera.persist()
                    s_print(f"<[{self.ip}][{msg['ID']}] Registration from {msg['SystemSerialNumber']} - {camera.hostname}")
                    if msg['SystemModelNumber'] ==  'VMC5040':
                        registerSet = Message(arlo.messages.REGISTER_SET_INITIAL_ULTRA)
                    else:
                        registerSet = Message(arlo.messages.REGISTER_SET_INITIAL)
                    registerSet['WifiCountryCode'] = WIFI_COUNTRY_CODE
                    camera.send_message(registerSet)
                elif (msg['Type'] == "status"):
                    s_print(f"<[{self.ip}][{msg['ID']}] Status from {msg['SystemSerialNumber']}")
                    camera = Camera.from_db_serial(msg['SystemSerialNumber'])
                    camera.ip = self.ip
                    camera.status = msg
                    camera.persist()
                elif (msg['Type'] == "alert"):
                    camera = Camera.from_db_ip(self.ip)
                    alert_type = msg['AlertType']
                    s_print(f"<[{self.ip}][{msg['ID']}] {msg['AlertType']}")
                    if alert_type == "pirMotionAlert" and RECORD_ON_MOTION_ALERT:
                       filename = f"{RECORDING_BASE_PATH}{camera.serial_number}_{timestr}_motion.mpg"
                       recorder = Recorder(self.ip, filename, MOTION_RECORDING_TIMEOUT)
                       with recorder_lock:
                           if self.ip in recorders:
                               recorder[self.ip].stop()
                           recorders[self.ip] = recorder
                       recorder.run()
                       webhook_manager.motion_detected(camera.ip,camera.friendly_name,camera.hostname,camera.serial_number,msg['PIRMotion']['zones'],filename)
                    elif alert_type == "audioAlert" and RECORD_ON_AUDIO_ALERT:
                       recorder = Recorder(self.ip, f"{RECORDING_BASE_PATH}{camera.serial_number}_{timestr}_audio.mpg", AUDIO_RECORDING_TIMEOUT)
                       with recorder_lock:
                           if self.ip in recorders:
                               recorder[self.ip].stop()
                           recorders[self.ip] = recorder
                       recorder.run()
                    elif alert_type == "motionTimeoutAlert":
                       with recorder_lock:
                           if self.ip in recorders and recorders[self.ip] is not None:
                               recorders[self.ip].stop()
                               del recorders[self.ip]
                else:
                    s_print(f"<[{self.ip}][{msg['ID']}] Unknown message")
                    s_print(msg)

                ack = Message(arlo.messages.RESPONSE)
                ack['ID'] = msg['ID']
                s_print(f">[{self.ip}][{msg['ID']}] Ack")
                self.connection.send(ack)
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
                    new_thread = ConnectionThread(connection,ip,port)
                    threads.append(new_thread)
                    new_thread.start()
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
