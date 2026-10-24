import time
from helpers.safe_print import s_print
from webhooks import webhook
from webhooks.senders import targeted


class WebHookManager:

    def __init__(self, config):
        self.config = config

    # --- public helpers called from the server -----------------------------

    def motion_detected(self, ip, friendly_name, hostname, serial_number, zone, file_name):
        r = self.motion(ip, friendly_name, hostname, serial_number, zone, file_name, time.time(),
                        url=self.config['MotionRecordingWebHookUrl'], encoding="application/json", timeout=5)
        s_print(str(r))

    def audio_detected(self, ip, friendly_name, hostname, serial_number, file_name):
        r = self.audio(ip, friendly_name, hostname, serial_number, file_name, time.time(),
                       url=self.config['AudioRecordingWebHookUrl'], encoding="application/json", timeout=5)
        s_print(str(r))

    def camera_registered(self, ip, friendly_name, hostname, serial_number, registration):
        r = self.registration(ip, friendly_name, hostname, serial_number, registration, time.time(),
                              url=self.config['RegistrationWebHookUrl'], encoding="application/json", timeout=5)
        s_print(str(r))

    def status_updated(self, ip, friendly_name, hostname, serial_number, status):
        r = self.status(ip, friendly_name, hostname, serial_number, status, time.time(),
                        url=self.config['StatusUpdateWebHookUrl'], encoding="application/json", timeout=5)
        s_print(str(r))

    # --- webhook senders ----------------------------------------------------
    # Each payload carries an "event" discriminator so a single endpoint can
    # tell the event types apart.

    @webhook(sender_callable=targeted.sender)
    def motion(self, ip, friendly_name, hostname, serial_number, zone, file_name, _time, url, encoding, timeout):
        return {"event": "motion", "ip": ip, "friendly_name": friendly_name, "hostname": hostname,
                "serial_number": serial_number, "zone": zone, "file_name": file_name, "time": _time}

    @webhook(sender_callable=targeted.sender)
    def audio(self, ip, friendly_name, hostname, serial_number, file_name, _time, url, encoding, timeout):
        return {"event": "audio", "ip": ip, "friendly_name": friendly_name, "hostname": hostname,
                "serial_number": serial_number, "file_name": file_name, "time": _time}

    @webhook(sender_callable=targeted.sender)
    def registration(self, ip, friendly_name, hostname, serial_number, registration, _time, url, encoding, timeout):
        return {"event": "registration", "ip": ip, "friendly_name": friendly_name, "hostname": hostname,
                "serial_number": serial_number,
                "model_number": registration.get("SystemModelNumber"),
                "firmware_version": registration.get("SystemFirmwareVersion"),
                "battery_percent": registration.get("BatPercent"),
                "signal_strength": registration.get("SignalStrengthIndicator"),
                "time": _time}

    @webhook(sender_callable=targeted.sender)
    def status(self, ip, friendly_name, hostname, serial_number, status, _time, url, encoding, timeout):
        return {"event": "status", "ip": ip, "friendly_name": friendly_name, "hostname": hostname,
                "serial_number": serial_number,
                "battery_percent": status.get("BatPercent"),
                "signal_strength": status.get("SignalStrengthIndicator"),
                "temperature": status.get("Temperature"),
                "charging_state": status.get("ChargingState"),
                "time": _time}
