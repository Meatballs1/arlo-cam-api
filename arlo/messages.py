import json

class Message:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __getitem__(self,key):
        return self.dictionary[key]

    def __setitem__(self,key,value):
        self.dictionary[key] = value

    def __contains__(self,item):
        return item in self.dictionary

    def toNetworkMessage(self):
        msgJson = json.dumps(self.dictionary,separators=(',', ':'))
        length = len(msgJson)
        final = f"L:{length} {msgJson}"
        return str.encode(final)

    def toJSON(self):
        return json.dumps(self.dictionary,separators=(',', ':'))

    def __repr__(self):
        return json.dumps(self.dictionary,separators=(',', ':'))

    def __str__(self):
        return json.dumps(self.dictionary, indent=4) 

    @staticmethod
    def from_json(json_data):
        if (json_data is not None and json_data != "None"):
            return Message(json.loads(json_data))
        else:
            return None

    @staticmethod
    def fromNetworkMessage(data):
        if data.startswith("L:"):
            delimiter = data.index(" ")
            dataLength = int(data[2:delimiter])
            json_data = data[delimiter+1:delimiter+1+dataLength]
            return Message(json.loads(json_data))
        else:
            return None

# ID is an incrementing number
#FROM CAMERA
REGISTRATION = {
        "Type":"registration",
        "ID":1,
        "SystemSerialNumber":"YOURSERIAL",
        "SystemModelNumber":"VMC4030P",
        "SystemFirmwareVersion":"1.125.15.0_35_1191",
        "UpdateSystemModelNumber":"VMC4030P",
        "CommProtocolVersion":1,
        "BatPercent":89,
        "SignalStrengthIndicator":4,
        "LogFrequency":2,
        "BatTech":"Rechargeable",
        "ChargerTech":"None",
        "ChargingState":"Off",
        "ThermalShutdownRechargeMaxTemp":60,
        "Temperature":20,
        "InterfaceVersion":1,
        "Capabilities":["IRLED","PirMotion","NightVision","Temperature","BatteryLevel","Microphone","Speaker","SignalStrength","Solar","BatteryCharging","H.264Streaming","JPEGSnapshot","AutomatedStop","BEC","RaParams"],
        "HardwareRevision":"H3",
        "Sync":False,
        "BattChargeMinTemp":0,
        "BattChargeMaxTemp":60,
        "ThermalShutdownMinTemp":-20,
        "ThermalShutdownMaxTemp":74,
        "BootSeconds":4
        }
#FROM CAMERA
STATUS = {
        "Type":"status",
        "ID":2,
        "SystemFirmwareVersion":"1.125.15.0_35_1191",
        "HardwareRevision":"H3",
        "SystemSerialNumber":"YOURSERIAL",
        "UpdateSystemModelNumber":"VMC4030P",
        "BatPercent":89,
        "BatTech":"Rechargeable",
        "ChargerTech":"None",
        "ChargingState":"Off",
        "WifiCountryDetails":"AT/36",
        "Bat1Volt":7.814,
        "Temperature":20,
        "Battery1CaliVoltage":7.814,
        "SignalStrengthIndicator":4,
        "Streamed":0,
        "UserStreamed":0,
        "MotionStreamed":0,
        "IRLEDsOn":0,
        "PoweredOn":17,
        "CameraOnline":1,
        "CameraOffline":16,
        "WifiConnectionCount":1,
        "WifiConnectionAttempts":1,
        "PIREvents":0,
        "FailedStreams":0,
        "FailedUpgrades":0,
        "SnapshotCount":0,
        "LogFrequency":2,
        "CriticalBatStatus":0,
        "ISPOn":15,"TimeAtPlug":0,
        "TimeAtUnPlug":0,
        "PercentAtPlug":0,
        "PercentAtUnPlug":0,
        "ISPWatchdogCount":0,
        "ISPWatchdogCount2":0,
        "SecsPerPercentCurr":0,
        "SecsPerPercentAvg":0,
        "DdrFailCnt":0,
        "RtcpDiscCnt":0,
        "DhcpFCnt":48,
        "RegFCnt":340,
        "TxErr":0,
        "TxFail":0,
        "TxPhyE1":0,
        "TxPhyE2":0
        }

#FROM CAMERA
ALERT = {
        "Type":"alert",
        "ID":7,
        "AlertType":"pirMotionAlert",
        "PIRMotion":{
            "Triggered":True,
            "TriggerLevel":7970,
            "TriggerRtpTime":0,
            "TriggerSysTime":1,
            "zones":[],
            "MdZones":0,
            "MdPrevZones":0,
            "PirTrigger":0,
            "z0Intensity":0,
            "z0Counter":0,
            "z1Intensity":0,
            "z1Counter":0,
            "z2Intensity":0,
            "z2Counter":0,
            "z3Intensity":0,
            "z3Counter":0
            }
        }
# FROM CAMERA - SMART ENABLED?
ALERT_SMART = {
        "Type":"alert",
        "ID":-1,
        "AlertType":"pirMotionAlert",
        "PIRMotion":{
            "Triggered":True,
            "TriggerLevel":0,
            "TriggerRtpTime":0,
            "TriggerSysTime":2857,
            "zones":[],
            "MdZones":1,
            "MdPrevZones":0,
            "PirTrigger":2,
            "z0Intensity":40,
            "z0Counter":320,
            "z1Intensity":0,
            "z1Counter":0,
            "z2Intensity":0,
            "z2Counter":0,
            "z3Intensity":0,
            "z3Counter":0
            }
        }

#FROM CAMERA - ZONE ALERT?
ALERT_ZONE = {
        "Type":"alert",
        "ID":-1,
        "AlertType":"pirMotionAlert",
        "PIRMotion":{
            "Triggered":True,
            "TriggerLevel":0,
            "TriggerRtpTime":0,
            "TriggerSysTime":1823,
            "zones":["3cfe3b01-944d-422a-9f99-34c130d23299","b44327ff-c1c4-4208-a890-f1de0c8b5192"],
            "MdZones":7, # Motion Detection Zones?
            "MdPrevZones":0,
            "PirTrigger":1,
            "z0Intensity":100, #Zone 0 all zones?
            "z0Counter":960,
            "z1Intensity":100, #Zone 1
            "z1Counter":896,
            "z2Intensity":24, # Zone2 etc
            "z2Counter":192,
            "z3Intensity":0,
            "z3Counter":0
            }
        }

#FROM CAMERA
ALERT_TIMEOUT = {
        "Type":"alert",
        "ID":9,
        "AlertType":"motionTimeoutAlert",
        "StreamDuration":18
        }

#FROM CAMERA
ALERT_AUDIO = {
        "Type":"alert",
        "ID":-1,
        "AlertType":"audioAlert",
        "AudioDetect":{
            "AudioTriggered":True,
            "AudioTriggerLevel":2672,
            "AudioTriggerRtpTime":0,
            "AudioTriggerSysTime":0
            }
        }

#FROM CAMERA
ALERT_AUDIO_TIMEOUT = {
        "Type":"alert",
        "ID":-1,
        "AlertType":"audioTimeoutAlert",
        "StreamDuration":10
        }

CAMERA_AUDIO_VOLUME = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "AudioSpkrVolume":0 #0 is 85%, 4=100%, -62=0%
            }
        }

CAMERA_SPEAKER = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "AudioSpkrEnable":False
            }
        }

CAMERA_MIC = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "AudioMicEnable":False
            }
        }

STATUS_REQUEST = {"Type":"statusRequest","ID":19}

RA_PARAMS_OFF_QUALITY = {
        "Type":"raParams",
        "ID":-1,
        "Params":{
            "1080p":{
                "minbps":102400,
                "maxbps":1228800,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":1024000,
                "cbrbps":1024000
                },
            "360p":{
                "minbps":51200,
                "maxbps":512000,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":409600,
                "cbrbps":409600
                },
            "480p":{
                "minbps":51200,
                "maxbps":614400,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":512000,
                "cbrbps":512000
                },
            "720p":{
                "minbps":51200,
                "maxbps":1024000,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":768000,
                "cbrbps":768000
                }
            }
        }

RA_PARAMS_LOW_QUALITY = {
        "Type":"raParams",
        "ID":-1,
        "Params":{
            "1080p":{
                "minbps":102400,
                "maxbps":532480,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":409600,
                "cbrbps":409600
                },
            "360p":{
                "minbps":51200,
                "maxbps":307200,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":102400,
                "cbrbps":102400
                },
            "480p":{
                "minbps":51200,
                "maxbps":409600,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":307200,
                "cbrbps":307200
                },
            "720p":{
                "minbps":51200,
                "maxbps":532480,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":409600,
                "cbrbps":409600
                }
            }
        }

RA_PARAMS_MEDIUM_QUALITY = {
        "Type":"raParams",
        "ID":-1,
        "Params":{
            "1080p":{
                "minbps":102400,
                "maxbps":640000,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":512000,
                "cbrbps":512000
                },
            "360p":{
                "minbps":51200,
                "maxbps":409600,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":204800,
                "cbrbps":204800
                },
            "480p":{
                "minbps":51200,
                "maxbps":409600,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":409600,
                "cbrbps":409600
                },
            "720p":{
                "minbps":51200,
                "maxbps":599040,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":460800,
                "cbrbps":460800
                }
            }
        }

RA_PARAMS_HIGH_QUALITY = {
        "Type":"raParams",
        "ID":-1,
        "Params":{
            "1080p":{
                "minbps":102400,
                "maxbps":819200,
                "minQP":35,
                "maxQP":40,
                "vbr":True,
                "targetbps":614400,
                "cbrbps":614400
                },
            "360p":{
                "minbps":51200,
                "maxbps":512000,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":409600,
                "cbrbps":409600
                },
            "480p":{
                "minbps":51200,
                "maxbps":614400,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":512000,
                "cbrbps":512000
                },
            "720p":{
                "minbps":51200,
                "maxbps":665600,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":512000,
                "cbrbps":512000
                }
            }
        }

RA_PARAMS_SUBSCRIPTION_QUALITY = {
        "Type":"raParams",
        "ID":-1,
        "Params":{
            "1080p":{
                "minbps":102400,
                "maxbps":1228800,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":1024000,
                "cbrbps":1024000
                },
            "360p":{
                "minbps":51200,
                "maxbps":512000,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":409600,
                "cbrbps":409600
                },
            "480p":{
                "minbps":51200,
                "maxbps":614400,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":512000,
                "cbrbps":512000
                },
            "720p":{
                "minbps":51200,
                "maxbps":1024000,
                "minQP":24,
                "maxQP":38,
                "vbr":True,
                "targetbps":768000,
                "cbrbps":768000
                }
            }
        }

#  Destination URL includes serial number
# Camera will POST with a multipart form containing file parameter.
# Will not include temp.jpg in URL
SNAPSHOT = {
        "Type":"fullSnapshot",
        "ID":-1,
        "DestinationURL":"http://172.14.1.1/snapshot/YOURSERIAL_d293116d/temp.jpg"
        }

REGISTER_SET_USER_STREAM_ACTIVE = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "UserStreamActive":0  # 0 Active 1 Disabled
            }
        }
        
# Generic registerSet
REGISTER_SET = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            }
        }

#Enable/Disable motion sensitivity
REGISTER_SET_PIR = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "PIREnableLED":True,
            "PIRLEDSensitivity":80
            }
        }

REGISTER_SET_ARMED = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "PIRTargetState":"Armed",
            "PIRStartSensitivity":80,
            "PIRAction":"Stream",
            "VideoMotionEstimationEnable":True,
            "VideoMotionSensitivity":80,
            "AudioTargetState":"Disarmed"
            }
        }

REGISTER_SET_DISARMED = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "PIRTargetState":"Disarmed",
            "AudioTargetState":"Disarmed",
            "VideoMotionEstimationEnable":False,
            "DefaultMotionStreamTimeLimit":10
            }
        }
REGISTER_SET_ARM_AUDIO = {
        "Type":"registerSet",
        "ID":12,
        "SetValues":{
            "PIRTargetState":"Armed",
            "PIRStartSensitivity":80,
            "PIRAction":"Stream",
            "AudioTargetState":"Armed",
            "AudioStartSensitivity":2,
            "AudioAction":"Stream",
            "VideoMotionEstimationEnable":True,
            "VideoMotionSensitivity":80
            }
        }

REGISTER_SET_INITIAL = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
                "AudioMicVolume":4,
                "AudioSpkrEnable":False,
                "VideoExposureCompensation":0,
                "VideoMirror":False,
                "VideoFlip":False,
                "VideoWindowStartX":0,
                "VideoWindowStartY":0,
                "VideoWindowEndX":1280,
                "VideoWindowEndY":720,
                "MaxMissedBeaconTime":10,
                "MaxStreamTimeLimit":1800,
                "VideoAntiFlickerRate":50,
                "WifiCountryCode":"EU",
                "NightVisionMode":True,
                "HdrControl":"off",
                "MaxUserStreamTimeLimit":1800,
                "MaxMotionStreamTimeLimit":120,
                "VideoMode":"superWide",
                "JPEGOutputResolution":"",
                "ChargeNotificationLed":0, # Battery Fully Charged Indicator
                "AudioMicAGC":0,
                "VideoOutputResolution":"1080p",
                "VideoTargetBitrate":1000, #600 originally
                "Audio0EncodeFormat":0,
                "Audio1EncodeFormat":1,
                "ArloSmart":True, # False originally
                "AlertBackoffTime":0,
                "PIRTargetState":"Disarmed",
                "AudioTargetState":"Disarmed",
                "VideoMotionEstimationEnable":False,
                "DefaultMotionStreamTimeLimit":10
                }
        }

REGISTER_SET_INITIAL_SUBSCRIPTION = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "VideoExposureCompensation":0,
            "VideoMirror":False,
            "VideoFlip":False,
            "VideoWindowStartX":0,
            "VideoWindowStartY":0,
            "VideoWindowEndX":1274,
            "VideoWindowEndY":718,
            "MaxMissedBeaconTime":10,
            "MaxStreamTimeLimit":1800,
            "VideoAntiFlickerRate":50,
            "WifiCountryCode":"EU",
            "NightVisionMode":True,
            "HdrControl":"off",
            "MaxUserStreamTimeLimit":1800,
            "MaxMotionStreamTimeLimit":120,
            "VideoMode":"superWide",
            "JPEGOutputResolution":"",
            "ChargeNotificationLed":0,
            "AudioMicAGC":0,
            "VideoOutputResolution":"1080p",
            "VideoTargetBitrate":1000,
            "Audio0EncodeFormat":0,
            "Audio1EncodeFormat":1,
            "ArloSmart":True,
            "AlertBackoffTime":0
            }
        }

REGISTER_SET_TURNED_OFF = {
        "Type":"registerSet",
        "ID":-1,
        "SetValues":{
            "VideoExposureCompensation":0,
            "VideoMirror":False,
            "VideoFlip":False,
            "VideoWindowStartX":0,
            "VideoWindowStartY":0,
            "VideoWindowEndX":1274,
            "VideoWindowEndY":718,
            "MaxMissedBeaconTime":10,
            "MaxStreamTimeLimit":1800,
            "VideoAntiFlickerRate":50,
            "WifiCountryCode":"EU",
            "NightVisionMode":True,
            "IRLedState":"off",
            "IRCutState":"engaged", # PowerSaving?
            "HdrControl":"off",
            "MaxUserStreamTimeLimit":1800,
            "MaxMotionStreamTimeLimit":120,
            "VideoMode":"superWide",
            "JPEGOutputResolution":"",
            "ChargeNotificationLed":0,
            "AudioMicAGC":0,
            "VideoOutputResolution":"1080p",
            "VideoTargetBitrate":1000,
            "Audio0EncodeFormat":0,
            "Audio1EncodeFormat":1,
            "ArloSmart":True,
            "AlertBackoffTime":0
            }
        }

RESPONSE = {
        "Type":"response",
        "ID":-1,
        "Response":"Ack"
        }

ACTIVITY_ZONE = {
        "Type":"motionZone",
        "ID":-1,
        "intrZone":[
                {
                    "name":"Zone 2",
                    "id":"5461bdfe-ab83-4b58-8325-848dd2c30dda",
                    "coords":[{"x":0.264449,"y":0.3},{"x":0.864449,"y":0.3},{"x":0.864449,"y":1},{"x":0.264449,"y":1}],
                    "color":41210
                }
            ]
        }
ACTIVITY_ZONE_ALL = {
        "Type":"motionZone",
        "ID":-1,
        "intrZone":[
            {
                "name":"Zone 3",
                "id":"2d10c7b1-72c7-4a42-8500-f75dbbbc860d",
                "coords":[{"x":0.1,"y":0.1},{"x":0.7,"y":0.1},{"x":0.7,"y":0.8},{"x":0.1,"y":0.8}],
                "color":15790130
                },
            {
                "name":"Zone 2",
                "id":"4a9b190b-eae2-49eb-93f8-3e924f13a179",
                "coords":[{"x":0.1,"y":0.1},{"x":0.7,"y":0.1},{"x":0.7,"y":0.8},{"x":0.1,"y":0.8}],
                "color":41210
                },
            {
                "name":"Zone 1",
                "id":"e8c8412d-5700-4567-9709-84c8b6bcd893",
                "coords":[{"x":0.1,"y":0.1},{"x":0.7,"y":0.1},{"x":0.7,"y":0.8},{"x":0.1,"y":0.8}],
                "color":8524960
                }
            ]
        }

ACTIVITY_ZONE_DELETE = {
        "Type":"motionZone",
        "ID":-1,
        "intrZone":[]
        }
