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

    def send_message(self,message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = False
            try:
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
                            if ('Response' in ack and ack['Response'] != "Ack"):
                                s_print(f"<[{self.ip}][{self.id}] {ack['Response']}")
                                result = False
                            else:
                                s_print(f"<[{self.ip}][{self.id}] Ack")
                                result = True
            finally:
                return result

    def update_status(self,status):
        self.status = status

    def persist(self):
        with sqlite3.connect('arlo.db') as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO camera VALUES (?,?,?,?,?)", (self.ip, self.serial_number, self.hostname, repr(self.registration), repr(self.status)))
            conn.commit()

    def pir_led(self,args):
        register_set = Message(arlo.messages.REGISTER_SET)
        enabled = args['enabled']
        sensitivity = args['sensitivity']

        register_set["SetValues"] = {
            "PIREnableLED":enabled,
            "PIRLEDSensitivity":sensitivity
            }

        return self.send_message(register_set)

    def set_quality(self,args):
        quality = args["quality"].lower()
        if quality == "low":
            ra_params = Message(arlo.messages.RA_PARAMS_LOW_QUALITY)
        elif quality == "medium":
            ra_params = Message(arlo.messages.RA_PARAMS_MEDIUM_QUALITY)
        elif quality == "high":
            ra_params = Message(arlo.messages.RA_PARAMS_HIGH_QUALITY)
        else:
            return False

        return self.send_message(ra_params)

    def arm(self,args):
        register_set = Message(arlo.messages.REGISTER_SET)
        pir_target_state = args['PIRTargetState']
        video_motion_estimation_enable = args['VideoMotionEstimationEnable']
        audio_target_state = args['AudioTargetState']

        register_set["SetValues"] = {
                "PIRTargetState":pir_target_state,
                "PIRStartSensitivity":80,
                "PIRAction":"Stream",
                "VideoMotionEstimationEnable":video_motion_estimation_enable,
                "VideoMotionSensitivity":80,
                "AudioTargetState":audio_target_state,
                "DefaultMotionStreamTimeLimit":10 # Unclear what this does, only set in normal traffic when 'Disarmed'
            }

        return self.send_message(register_set)

    def set_user_stream_active(self,active):
        register_set = Message(arlo.messages.REGISTER_SET)
        register_set['SetValues']['UserStreamActive'] = int(active)
        return self.send_message(register_set)

    def status_request(self):
        _status_request = Message(arlo.messages.STATUS_REQUEST)
        return self.send_message(_status_request)

    def snapshot_request(self, url):
        _snapshot_request = Message(arlo.messages.SNAPSHOT)
        _snapshot_request['DestinationURL'] = url
        return self.send_message(_snapshot_request)

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
