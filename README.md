# Arlo Cam API

This project simulates the Arlo Basestation to communicate with cameras.

Based on reconstructing the communication between a VMB4000r3 and Arlo Pro 2 cameras.

It won't work with the mobile app, and there is no real plan to support this at present. However,
it does allow you to use your Arlo cameras as normal RTSP camera sources for other media recorders.

We can either emulate the basestation using the same SSID and capture and re-use the WPA-PSK to make 
the cameras connect to us. Or we can try and use WPS to get the cameras to sync to our own basestation.

Currently running this on a Raspberry Pi 1b with a TP-Link TL-WN722N USB WiFi adapter.

# Install

Tested working on Raspberry Pi OS Lite released 2nd December 2020:

```
sudo apt install -y python3-pip vlc
pip3 install -r requirements.txt
```

# Run

```
python3 server.py
```

# API

The service spins up a REST API on TCP port 5000. The api.postman_collection.json config
contains all of the functioning endpoints to import into Postman.

# Webhooks

I've put a basic webhook in to trigger when motion is detected. This needs further work to capture more events.

# Temperature Sensor

A camera on battery power reports near ambient temperatures for it's temperature, although I haven't measured quite
how big the difference is. This can be retrieved with a status request via the API.

# Capturing Arlo Basestation Wifi Details

To get the cameras to connect to us we can capture the WPA-PSK using WPS Push Button with the following
configuration:

wpa.conf:

```
ctrl_interface=/var/run/wpa_supplicant
ctrl_interface_group=0
update_config=1
device_name=NTGRDEV
manufacturer=broadcom technology, Inc.
```

Then run the following commands and press the button on the base station or use the app to put it
into pairing mode:

```
systemctl stop NetworkManager.service
wpa_supplicant -t -Dwext -i wlan0 -c wpa.conf
iwconfig wlan0 essid NETGEAR05
wpa_cli -i wlan0 wps_pbc
```

If successful the wpa.conf should contain the WPA-PSK and you can configure your own wireless network
with the same ESSID and key.

# Pairing a camera to your own basestation

The cameras seem fairly happy to connect to any basestation when they the 'Sync' button is pressed. With hostapd the following configuration was used:

```
beacon_int=100
ssid=${SSID}
interface=${WIFI_IFACE}
driver=${DRIVER}
channel=${CHANNEL}
ctrl_interface=$CONFDIR/hostapd_ctrl
ctrl_interface_group=0
ap_isolate=$ISOLATE_CLIENTS
eap_server=1
wps_pin_requests=/var/run/hostapd.pin-req
config_methods=label display push_button keypad
wps_state=2
ap_setup_locked=1
ieee80211n=1
ignore_broadcast_ssid=0
```

PBC can be activated using:

```
hostapd_cli wps_pbc
```

# Work In Progress

## Video recording

The FFmpeg library doesn't send RTCP Response Received messages very often, and the camera seems to timeout
the stream, and force itself to reauth to the wifi if this happens. This means FFmpeg and dependent apps
seem to kill the camera after about 6seconds. libVLC seems to work, also Live555 - openRTSP.

## Audio streaming

The UDP port 5000 on the cameras constantly listens for RTP traffic with the following encoding:

Audio: pcm_mulaw, 8000 Hz, mono, s16, 64 kb/s

```
ffmpeg -re -i piano2.wav  -ar 8000 -sample_fmt s16 -ac 1 -f rtp rtp://172.14.1.194:5000
ffmpeg -f alsa -channels 1 -i hw:1  -ar 8000 -sample_fmt s16 -ac 1 -f rtp rtp://172.14.1.194:5000
```

Where hw:1 matches source input hardware device etc

Sending audio whilst the camera is streaming appears to kill audio...
