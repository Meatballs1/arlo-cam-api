#!/bin/bash
SSID=NETGEAR05
WPA_PSK=X

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

DEBIAN_FRONTEND=noninteractive apt install -y hostapd dnsmasq netfilter-persistent iptables-persistent
systemctl unmask hostapd
systemctl enable hostapd

useradd arlo -m -r -s /usr/sbin/nologin
cp -r ../arlo-cam-api/ /opt/arlo-cam-api
chown -R arlo:arlo /opt/arlo-cam-api
sudo -u arlo pip3 install -r /opt/arlo-cam-api/requirements.txt

echo net.ipv4.ip_forward=1 > /etc/sysctl.d/routed-ap.conf

cat << EOF >> /etc/dhcpcd.conf
interface wlan0
    static ip_address=172.14.0.1/24
    static routers=172.14.0.1
    nohook wpa_supplicant
EOF

cat << EOF > tee /etc/dnsmasq.conf
interface=wlan0
dhcp-range=172.14.0.100,172.14.0.199,255.255.255.0,infinite
domain=arlo
address=/gateway.arlo/172.14.0.1
EOF

rfkill unblock wlan

cat << EOF > /etc/hostapd/hostapd.conf
country_code=GB
interface=wlan0
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
ssid=$SSID
hw_mode=g
channel=11
macaddr_acl=0
auth_algs=1
wpa=2
wpa_passphrase=$WPA_PSK
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
eap_server=1
config_methods=label display push_button keypad
wps_state=2
ap_setup_locked=1
ieee80211n=1
wps_pin_requests=/var/run/hostapd.pin-req
ignore_broadcast_ssid=0
EOF

cat << EOF > /etc/iptables/rules.v4
*filter
:INPUT DROP [731:160138]
:FORWARD DROP [49:5435]
:OUTPUT ACCEPT [194:17010]
-A INPUT -i lo -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i eth0 -p tcp -m tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A INPUT -p tcp -m tcp --dport 5000 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A INPUT -i wlan0 -p tcp -m tcp --dport 4000 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A INPUT -i wlan0 -p udp -m udp --dport 67 -j ACCEPT
-A INPUT -i wlan0 -p udp -m udp --dport 53 -j ACCEPT
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -p icmp -j ACCEPT
-A FORWARD -i eth0 -p tcp -m tcp --dport 554 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A FORWARD -i wlan0 -p tcp -m tcp --sport 554 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -i wlan0 -p udp -j ACCEPT
-A FORWARD -i eth0 -p udp -j ACCEPT
-A OUTPUT -o lo -j ACCEPT
-A OUTPUT -p icmp -j ACCEPT
-A OUTPUT -p tcp -m tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp -m tcp --sport 554 -m conntrack --ctstate ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp -m tcp --sport 5000 -m conntrack --ctstate ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp -m tcp --sport 4000 -m conntrack --ctstate ESTABLISHED -j ACCEPT
-A OUTPUT -p udp -m udp --sport 53 -j ACCEPT
-A OUTPUT -p udp -m udp --sport 67 -j ACCEPT
-A OUTPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT
COMMIT

EOF

cat << EOF > /lib/systemd/system/arlo.service
[Unit]
Description=Arlo Control Service
After=multi-user.target
StartLimitIntervalSec=

[Service]
WorkingDirectory=/opt/arlo-cam-api/
User=arlo
Type=idle
ExecStart=/usr/bin/python3 /opt/arlo-cam-api/server.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

echo "Now sudo reboot..."
