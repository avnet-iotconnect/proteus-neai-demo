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
import proteus_AI_plugin

cpid = config.cpid
env = config.env
UniqueId = config.unique_id
	
SId = ""
Sdk=None
interval = 5
directmethodlist={}
ACKdirect=[]
device_list=[]

SdkOptions={
	"certificate" : { 
		"SSLKeyPath"  : "/home/weston/proteus_stuff/STM32MP157F_Demo/device_certificates/pk_" + UniqueId + ".pem", 
		"SSLCertPath" : "/home/weston/proteus_stuff/STM32MP157F_Demo/device_certificates/cert_" + UniqueId + ".crt",
		"SSLCaPath"   : "/home/weston/proteus_stuff/STM32MP157F_Demo/aws_cert/root-CA.pem"
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
        with open("/home/weston/proteus_stuff/STM32MP157F_Demo/downstream_commands.json", "w") as downstream_file:
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


def main():
    global SId,cpid,env,SdkOptions,Sdk,ACKdirect,device_list,plugin
    try:
        with IoTConnectSDK(UniqueId,SdkOptions,DeviceConectionCallback) as Sdk:
            try:
                sensor_thread = threading.Thread(target=proteus_AI_plugin.main_loop)
                sensor_thread.start()
                Sdk.onDeviceCommand(DeviceCallback)
                Sdk.onTwinChangeCommand(TwinUpdateCallback)
                Sdk.onOTACommand(DeviceFirmwareCallback)
                Sdk.onDeviceChangeCommand(DeviceChangeCallback)
                Sdk.getTwins()
                device_list=Sdk.Getdevice()
                while True:
                    dObj = [{
                        "uniqueId": UniqueId,
                        "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "data": proteus_AI_plugin.telemetry
                    }]
                    sendBackToSDK(Sdk, dObj)
                    
            except KeyboardInterrupt:
                print ("Keyboard Interrupt Exception")
                proteus_AI_plugin.stop_flag = True
                sensor_thread.join()
                sys.exit(0)

            except Exception as ex:
                proteus_AI_plugin.stop_flag = True
                sensor_thread.join()
                print(ex)
                sys.exit(0)

                 
    except KeyboardInterrupt:
        print ("Keyboard Interrupt Exception")
        #proteus_AI_plugin.stop_flag = True
        #sensor_thread.join()
        sys.exit(0)

    except Exception as ex:
        #proteus_AI_plugin.stop_flag = True
        #sensor_thread.join()
        print(ex)
        sys.exit(0)


if __name__ == "__main__":
    main()
