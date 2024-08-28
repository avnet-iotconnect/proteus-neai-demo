#!/bin/bash

apt-get update
apt-get upgrade -y
apt-get install python3-pip -y
pip3 install paho-mqtt==1.6.1
apt-get install opus-tools -y
cp -r /media/usbdrive/proteus-neai-demo-main /home/weston
cd /home/weston/proteus-neai-demo-main/iotc-python-sdk-master-std-21-patch/iotconnect-sdk-1.0
python3 setup.py install
cd /home/weston/proteus-neai-demo-main
pip3 install blue_st_sdk-1.5.0-py3-none-any.whl
cp /home/weston/proteus-neai-demo-main/iotconnect.service /etc/systemd/system
systemctl enable iotconnect
