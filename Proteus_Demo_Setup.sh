#!/bin/bash

apt-get update
apt-get upgrade -y
apt-get install python3-pip -y
pip3 install paho-mqtt==1.6.1
cp -r /media/usbdrive/Proteus-NEAI-Demo-main /home/weston
cd /home/weston/Proteus-NEAI-Demo-main/iotconnect-python-sdk-v1.0/iotconnect-sdk-1.0
python3 setup.py install
cd /home/weston/Proteus-NEAI-Demo-main
pip3 install blue_st_sdk-1.5.0-py3-none-any.whl
cp /home/weston/Proteus-NEAI-Demo-main/iotconnect.service /etc/systemd/system
systemctl enable iotconnect
