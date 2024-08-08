import time
import sys
import pexpect
import os
import importlib
import subprocess
import json

#This dictionary is what the main loop of the main 
#program will periodcially send as telemetry to IoTConnect
telemetry = {
    "NEAI_phase":"Not yet specified",
    "NEAI_state":"Not yet specified",
    "NEAI_progress_percentage":0,
    "NEAI_status":"Not yet specified",
    "NEAI_similarity_percentage":0
}


#This function resets the bluetooth system to make 
#sure that no devices are connected at the start of the program
def setup_bluetooth():
    setup_process = pexpect.spawn('bluetoothctl', encoding='utf-8')
    setup_process.expect('#')
    setup_process.sendline('power off')
    time.sleep(1)
    setup_process.sendline('power on')
    time.sleep(1)
    setup_process.close()


#This loop is what the dedicated proteus thread will run when started in the main loop
def main_loop():
    while True:
        print("Establishing BLE connection to PROTEUS")
        setup_bluetooth()
        proteus_connection_process = subprocess.Popen(['python3', '/home/weston/PROTEUS_MP157F_AI_Demo/proteus_ai_level_2.py'])
        while True:
            still_alive = proteus_connection_process.poll()
            if still_alive is not None:
                print('Proteus BLE process ended (likely disconnected from device). Restarting process...')
                break
            with open("/home/weston/PROTEUS_MP157F_AI_Demo/data_queue.json", "r") as jsonFile:
                data = json.load(jsonFile)
            telemetry["NEAI_phase"] = data["phase"]
            telemetry["NEAI_state"] = data["state"]
            telemetry["NEAI_progress_percentage"] = data["progress"]
            telemetry["NEAI_status"] = data["status"]
            telemetry["NEAI_similarity_percentage"] = data["similarity"]
            time.sleep(1)
