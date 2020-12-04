This project simulates the Arlo Basestation to communicate with cameras.

Based on reconstructing the communication between a VMB4000r3 and Arlo Pro 2 cameras.

Currently it just listens and responds to registration and status requests so the RTMP
stream can be connected to on the camera.

To get the cameras to connect to us we capture the WPA-PSK using WPS Push Button with the following
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

# Work In Progress

## Video recording

The FFmpeg library doesn't send RTCP Response Received messages very often, and the camera seems to timeout
the stream, and force itself to reauth to the wifi if this happens. This means FFmpeg and dependent apps
seem to kill the camera after about 6seconds. libVLC seems to work, also Live555 - openRTSP

## Audio streaming

The UDP port 5000 on the cameras constantly listens for RTP traffic with the following encoding:

Audio: pcm_mulaw, 8000 Hz, mono, s16, 64 kb/s

```
ffmpeg -re -i piano2.wav  -ar 8000 -sample_fmt s16 -ac 1 -f rtp rtp://172.14.1.194:5000
```
