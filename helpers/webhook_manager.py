import time
from helpers.safe_print import s_print
from webhooks import webhook
from webhooks.senders import targeted
class WebHookManager:

    def __init__(self,config):
        self.config = config

    def motion_detected(self, ip,friendly_name,hostname,serial_number,zone,file_name):
        r = self.motion(ip,friendly_name,hostname, serial_number,zone,file_name,time.time(), url=self.config['MotionRecordingWebHookUrl'],encoding="application/json", timeout=5)
        s_print(str(r))
        

    @webhook(sender_callable=targeted.sender)
    def motion(self, ip, friendly_name,hostname,serial_number,zone,file_name,_time, url, encoding, timeout):
        return {"ip":ip,"friendly_name":friendly_name,"hostname":hostname,"serial_number":serial_number,"zone":zone,"file_name":file_name,"time":_time}
