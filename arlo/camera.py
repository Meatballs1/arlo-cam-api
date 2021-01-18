import json
import socket
import sqlite3
import time
import sys

from arlo.messages import Message
from arlo.socket import ArloSocket
import arlo.messages
from helpers.safe_print import s_print
from helpers.recorder import Recorder

class Camera:
    def __init__(self, ip, registration):
        self.registration = registration
        self.ip = ip
        self.id = 0
        self.serial_number = registration["SystemSerialNumber"]
        self.hostname = f"{registration['SystemModelNumber']}-{self.serial_number[-5:]}"
        self.status = {}
        self.friendly_name = self.serial_number

    def __getitem__(self,key):
        return self.registration[key]

    def send_message(self,message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            sock.settimeout(5.0)
            try:
                sock.connect((self.ip, 4000))
            except OSError as msg:
                print('Connection to camera failed: {msg}')
                return False

            result = False
            try:
                arloSock = ArloSocket(sock)
                self.id += 1
                message['ID'] = self.id
                s_print(f">[{self.ip}][{self.id}] {message['Type']}")
                arloSock.send(message)
                ack = arloSock.receive()
                if (ack != None):
                    if (ack['ID']==message['ID']):
                        if ('Response' in ack and ack['Response'] != "Ack"):
                            s_print(f"<[{self.ip}][{self.id}] {ack['Response']}")
                            result = False
                        else:
                            s_print(f"<[{self.ip}][{self.id}] Ack")
                            result = True
            except:
                print(f'Exception: {sys.exc_info()}')
            finally:
                return result

    def persist(self):
        with sqlite3.connect('arlo.db') as conn:
            c = conn.cursor()
            # Remove the IP for any redundant camera that has the same IP...
            c.execute("UPDATE camera SET ip = 'UNKNOWN' WHERE ip = ? AND serialnumber <> ?", (self.ip, self.serial_number))
            c.execute("REPLACE INTO camera VALUES (?,?,?,?,?,?)", (self.ip, self.serial_number, self.hostname, repr(self.registration), repr(self.status), self.friendly_name))
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

    def set_activity_zones(self,args):
        activity_zones = Message(arlo.messages.ACTIVITY_ZONE_ALL)
        # TODO:Set The Co-ordinates  
        return self.send_message(activity_zones)

    def unset_activity_zones(self,args):
        activity_zones = Message(arlo.messages.ACTIVITY_ZONE_DELETE)
        return self.send_message(activity_zones)

    def set_quality(self,args):
        quality = args["quality"].lower()
        if quality == "low":
            ra_params = Message(arlo.messages.RA_PARAMS_LOW_QUALITY)
            registerSet = Message(arlo.messages.REGISTER_SET_LOW_QUALITY)
        elif quality == "medium":
            ra_params = Message(arlo.messages.RA_PARAMS_MEDIUM_QUALITY)
            registerSet = Message(arlo.messages.REGISTER_SET_MEDIUM_QUALITY)
        elif quality == "high":
            ra_params = Message(arlo.messages.RA_PARAMS_HIGH_QUALITY)
            registerSet = Message(arlo.messages.REGISTER_SET_HIGH_QUALITY)
        elif quality == "subscription":
            ra_params = Message(arlo.messages.RA_PARAMS_SUBSCRIPTION_QUALITY)
            registerSet = Message(arlo.messages.REGISTER_SET_SUBSCRIPTION_QUALITY)
        else:
            return False

        return self.send_message(ra_params) and self.send_message(registerSet)


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

    def mic_request(self, enabled):
        register_set = Message(arlo.messages.REGISTER_SET)
        register_set['AudioMicEnable'] = enabled
        return self.send_message(register_set)

    def speaker_request(self, enabled):
        register_set = Message(arlo.messages.REGISTER_SET)
        register_set['AudioSpkrEnable'] = enabled
        return self.send_message(register_set)

    def record(self, duration, is4k):
        self.status_request() # Cameras tend to be unresponsive so send a status request to wake up
        timestr = time.strftime("%Y%m%d-%H%M%S")
        path = f"/tmp/{self.serial_number}{timestr}-user.mpg", duration
        if is4k:
            addr = f'{self.ip}:555'
        else:
            addr = f'{self.ip}:554'
        recorder = Recorder(addr, path, duration)
        recorder.run()
        return path

    @staticmethod
    def from_db_serial(serial):
        with sqlite3.connect('arlo.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM camera WHERE serialnumber = ?", (serial,))
            result = c.fetchone()
            return Camera.from_db_row(result)

    @staticmethod
    def from_db_ip(ip):
        with sqlite3.connect('arlo.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM camera WHERE ip = ?", (ip,))
            result = c.fetchone()
            return Camera.from_db_row(result)

    @staticmethod
    def from_db_row(row):
        if row is not None:
            (ip,serial_number,hostname,registration,status,friendly_name) = row
            _registration = Message.from_json(registration)
            cam = Camera(ip,_registration)
            cam.status = Message.from_json(status)
            cam.friendly_name = friendly_name
            return cam
        else:
            return None

