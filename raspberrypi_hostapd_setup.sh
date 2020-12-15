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

echo net.ipv4.ip_forward=1 > /etc/sysctl.d/routed-ap.conf

cat << EOF >> /etc/dhcpcd.conf
interface wlan0
    static ip_address=10.14.0.1/24
    static routers=192.168.4.1
    nohook wpa_supplicant
EOF

cat << EOF > tee /etc/dnsmasq.conf
interface=wlan0
dhcp-range=10.14.0.100,10.14.0.199,255.255.255.0,24h
domain=arlo
address=/gateway.arlo/10.14.0.1
EOF

rfkill unblock wlan

cat << EOF > /etc/hostapd/hostapd.conf
country_code=GB
interface=wlan0
ssid=$SSID
hw_mode=g
channel=11
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
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
ignore_broadcast_ssid=1
EOF

cat << EOF > /etc/iptables/rules.v4
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -i eth0 -p tcp -m tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp -m tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT
COMMIT
EOF

