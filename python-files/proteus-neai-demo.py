import sys
import json
import time
import threading
import random
from iotconnect import IoTConnectSDK
from datetime import datetime
import os
import importlib
import config
import subprocess
import pexpect

cpid = config.cpid
env = config.env
UniqueId = config.unique_id

#This dictionary is what the main program will periodcially send as telemetry to IoTConnect
telemetry = {
    "NEAI_phase":"Not yet specified",
    "NEAI_state":"Not yet specified",
    "NEAI_progress_percentage":0,
    "NEAI_status":"Not yet specified",
    "NEAI_similarity_percentage":0
}

#The main program sets this to false when the program needs to terminate
stop_flag = False

connected_flag = False
	
SId = ""
Sdk=None
interval = 5
directmethodlist={}
ACKdirect=[]
device_list=[]

SdkOptions={
	"certificate" : { 
		"SSLKeyPath"  : "/home/weston/proteus-neai-demo-main/certificates/pk_" + UniqueId + ".pem", 
		"SSLCertPath" : "/home/weston/proteus-neai-demo-main/certificates/cert_" + UniqueId + ".crt",
		"SSLCaPath"   : "/home/weston/proteus-neai-demo-main/certificates/aws_cert/root-CA.pem"
	},
    "offlineStorage":{
        "disabled": False,
	    "availSpaceInMb": 0.01,
	    "fileCount": 5,
        "keepalive":60
    },
    "skipValidation":False,
    "discoveryUrl":"https://awsdiscovery.iotconnect.io",
    "IsDebug": False,
    "cpid" : cpid,
    "sId" : SId,
    "env" : env,
    "pf"  : "aws"
}

def DeviceCallback(msg):
    global Sdk
    print("\n--- Command Message Received in Firmware ---")
    print(msg)
    #command_dict = json.dump(msg)
    cmdType = None
    if msg != None and len(msg.items()) != 0:
        cmdType = msg["ct"] if "ct"in msg else None
    if cmdType == 0:
        data=msg
        if data != None:
            if "id" in data:
                if "ack" in data and data["ack"]:
                    Sdk.sendAckCmd(data["ack"],7,"sucessfull",data["id"])  #fail=4,executed= 5,sucess=7,6=executedack
            else:
                if "ack" in data and data["ack"]:
                    Sdk.sendAckCmd(data["ack"],7,"sucessfull") #fail=4,executed= 5,sucess=7,6=executedack
    else:
        print("rule command",msg)
    # If the command is recognized as a PROTEUS NEAI Command
    if msg["cmd"] in ["start_ad", "stop_ad", "reset_knowledge", "learn"]:
        # Send the command to the downstream JSON
        command_dict = {"command":msg["cmd"]}
        with open("/home/weston/proteus-neai-demo-main/communication-jsons/downstream_commands.json", "w") as downstream_file:
            json.dump(command_dict, downstream_file)


def DeviceFirmwareCallback(msg):
    global Sdk,device_list
    print("\n--- firmware Command Message Received ---")
    print(json.dumps(msg))
    cmdType = None
    if msg != None and len(msg.items()) != 0:
        cmdType = msg["ct"] if msg["ct"] != None else None
    if cmdType == 1:
        data = msg
        if data != None:
            if ("urls" in data) and data["urls"]:
                for url_list in data["urls"]:
                    if "tg" in url_list:
                        for i in device_list:
                            if "tg" in i and (i["tg"] == url_list["tg"]):
                                Sdk.sendOTAAckCmd(data["ack"],0,"sucessfull",i["id"]) #Success=0, Failed = 1, Executed/DownloadingInProgress=2, Executed/DownloadDone=3, Failed/DownloadFailed=4
                    else:
                        Sdk.sendOTAAckCmd(data["ack"],0,"sucessfull") #Success=0, Failed = 1, Executed/DownloadingInProgress=2, Executed/DownloadDone=3, Failed/DownloadFailed=4


def DeviceConectionCallback(msg):
    print("DEVICE CONNECTION CALLBACK")  
    cmdType = None
    if msg != None and len(msg.items()) != 0:
        cmdType = msg["ct"] if msg["ct"] != None else None
    #connection status
    if cmdType == 116:
        #Device connection status e.g. data["command"] = true(connected) or false(disconnected)
        print(json.dumps(msg))
	
def TwinUpdateCallback(msg):
    global Sdk
    if msg:
        print("--- Twin Message Received ---")
        print(json.dumps(msg))
        if ("desired" in msg) and ("reported" not in msg):
            for j in msg["desired"]:
                if ("version" not in j) and ("uniqueId" not in j):
                    Sdk.UpdateTwin(j,msg["desired"][j])


def sendBackToSDK(sdk, dataArray):
    sdk.SendData(dataArray)
    time.sleep(interval)


def DirectMethodCallback1(msg,methodname,rId):
    global Sdk,ACKdirect
    print(msg)
    print(methodname)
    print(rId)
    data={"data":"succed"}
    ACKdirect.append({"data":data,"status":200,"reqId":rId})


def DirectMethodCallback(msg,methodname,rId):
    global Sdk,ACKdirect
    print(msg)
    print(methodname)
    print(rId)
    data={"data":"fail"}
    ACKdirect.append({"data":data,"status":200,"reqId":rId})


def DeviceChangeCallback(msg):
    print(msg)


def InitCallback(response):
    print(response)


#This function resets the bluetooth system to make sure that no devices are connected at the start of the program
def setup_bluetooth():
    setup_process = pexpect.spawn('bluetoothctl', encoding='utf-8')
    setup_process.expect('#')
    setup_process.sendline('power off')
    time.sleep(1)
    setup_process.sendline('power on')
    time.sleep(1)
    setup_process.close()
    try:
        os.system("rm /home/root/ble_catalog.json")
    except Exception:
        print("No existing BLE catalog to delete")


#This loop controls the BLE connection between the gateway and the proteus and spawns the program that dictates the behavior of the proteus
def BLE_loop():
    global connected_flag
    last_message = ""
    downstream_dict = {"command":""}
    #Clearing message buffer
    upstream_dict = {"message":""}
    with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_message.json", "w") as upstream_file:
        json.dump(upstream_dict, upstream_file)
    with open("/home/weston/proteus-neai-demo-main/communication-jsons/downstream_commands.json", "w") as downstream_file:
        json.dump(downstream_dict, downstream_file)
    while stop_flag == False:
        print("Establishing BLE connection to PROTEUS")
        # Restart bluetooth services
        setup_bluetooth()
        # Take note of the time that the BLE process is started
        start_time_second = int(datetime.now().second)
        # Start BLE process
        proteus_connection_process = subprocess.Popen(['python3', '/home/weston/proteus-neai-demo-main/python-files/proteus-neai-ble-comms.py'])
        while stop_flag == False:
            # Check pulse of BLE process
            still_alive = proteus_connection_process.poll()
            # If BLE process is dead
            if still_alive is not None:
                print('Proteus BLE process ended (likely disconnected from device). Restarting process...')
                # Restart BLE process
                break
            # Check to see if program has successfully kicked off
            with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_message.json", "r") as upstream_file:
                try:
                    message_dict = json.load(upstream_file)         
                    message = message_dict["message"]
                    # If message buffer is still in default state
                    if message == "":
                        now = int(datetime.now().second)
                        time_delta = now - start_time_second
                        # If it has been over 30 seconds since the proteus communication thread started
                        if time_delta > 30 or (time_delta < 0 and time_delta > -30):
                            # Restart the BLE process
                            break
                    elif message != last_message:
                        print("MESSAGE FROM PROTEUS: " + message)
                        last_message = message
                        connected_flag = True
                except Exception as e:
                    print("PROBLEM OPENING JSON FILE (PROBABLY BEING WRITTEN TO CURRENTLY)")
                    print(e)
       
            # Open JSON data
            with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_data.json", "r") as upstream_file:
                try:
                    data = json.load(upstream_file)
                except:
                    print("PROBLEM OPENING JSON FILE (PROBABLY BEING WRITTEN TO CURRENTLY)")
            # Copy JSON data into local dictionary
            telemetry["NEAI_phase"] = data["phase"]
            telemetry["NEAI_state"] = data["state"]
            telemetry["NEAI_progress_percentage"] = data["progress"]
            telemetry["NEAI_status"] = data["status"]
            telemetry["NEAI_similarity_percentage"] = data["similarity"]
            time.sleep(0.25)


def main():
    global SId,cpid,env,SdkOptions,Sdk,ACKdirect,device_list,stop_flag, telemetry, connected_flag
    ble_thread = None
    try:
        with IoTConnectSDK(UniqueId,SdkOptions,DeviceConectionCallback) as Sdk:
            try:
                ble_thread = threading.Thread(target=BLE_loop)
                ble_thread.start()
                Sdk.onDeviceCommand(DeviceCallback)
                Sdk.onTwinChangeCommand(TwinUpdateCallback)
                Sdk.onOTACommand(DeviceFirmwareCallback)
                Sdk.onDeviceChangeCommand(DeviceChangeCallback)
                Sdk.getTwins()
                device_list=Sdk.Getdevice()
                while True:
                    if connected_flag == True:
                        dObj = [{
                            "uniqueId": UniqueId,
                            "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                            "data": telemetry
                        }]
                        sendBackToSDK(Sdk, dObj)
                    else:
                        time.sleep(1)
                    
            except KeyboardInterrupt:
                print ("Keyboard Interrupt Exception")
                stop_flag = True
                if ble_thread != None and ble_thread.is_alive():
                    ble_thread.join()
                sys.exit(0)

            except Exception as ex:
                stop_flag = True
                if ble_thread != None and ble_thread.is_alive():
                    ble_thread.join()
                print(ex)
                sys.exit(0)

                 
    except KeyboardInterrupt:
        print ("Keyboard Interrupt Exception")
        stop_flag = True
        if ble_thread != None and ble_thread.is_alive():
            ble_thread.join()
        sys.exit(0)

    except Exception as ex:
        stop_flag = True
        if ble_thread != None and ble_thread.is_alive():
            ble_thread.join()
        print(ex)
        sys.exit(0)


if __name__ == "__main__":
    main()
