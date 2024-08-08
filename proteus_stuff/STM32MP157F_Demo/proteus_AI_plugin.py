import time
import sys
import pexpect
import os
import importlib
import subprocess
import json
import fcntl
import plugin_queue
import datetime

#The main program sets this to false when the program needs to terminate
stop_flag = False

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
    '''setup_process = pexpect.spawn('bluetoothctl', encoding='utf-8')
    setup_process.expect('#')
    setup_process.sendline('power off')
    time.sleep(0.5)
    setup_process.sendline('power on')
    time.sleep(0.5)
    setup_process.sendline('exit')
    time.sleep(0.5)
    setup_process.close()'''
    os.system("btmgmt le off")
    os.system("btmgmt le on")
    try:
        os.system("rm /home/root/ble_catalog.json")
    except:
        print("No existing BLE catalog to delete")


#This loop is what the dedicated proteus thread will run when started in the main loop
def main_loop():
    last_message = ""
    downstream_dict = {"command":""}
    #Clearing message buffer
    upstream_dict = {"message":""}
    with open("/home/weston/proteus_stuff/STM32MP157F_Demo/upstream_message.json", "w") as upstream_file:
        json.dump(upstream_dict, upstream_file)
    with open("/home/weston/proteus_stuff/STM32MP157F_Demo/downstream_commands.json", "w") as downstream_file:
        json.dump(downstream_dict, downstream_file)
    while stop_flag == False:
        print("Establishing BLE connection to PROTEUS")
        # Restart bluetooth services
        setup_bluetooth()
        # Take note of the time that the BLE process is started
        helper_start_time_minute = int(datetime.datetime.now().minute)
        # Start BLE process
        proteus_connection_process = subprocess.Popen(['python3', '/home/weston/proteus_stuff/STM32MP157F_Demo/ai_plugin_helper.py'])
        while stop_flag == False:
            # Check pulse of BLE process
            still_alive = proteus_connection_process.poll()
            # If BLE process is dead
            if still_alive is not None:
                print('Proteus BLE process ended (likely disconnected from device). Restarting process...')
                # Restart BLE process
                break
            # Check to see if program has successfully kicked off
            with open("/home/weston/proteus_stuff/STM32MP157F_Demo/upstream_message.json", "r") as upstream_file:
                try:
                    message_dict = json.load(upstream_file)         
                    message = message_dict["message"]
                    # If message buffer is still in default state
                    if message == "":
                        now = int(datetime.datetime.now().minute)
                        time_delta = now - helper_start_time_minute
                        # If it has been over a minute since the proteus communication thread started
                        if time_delta > 1 or (time_delta < 0 and time_delta > -59):
                            # Restart the BLE process
                            break
                    elif message != last_message:
                        print("MESSAGE FROM PROTEUS: " + message)
                        last_message = message
                except Exception as e:
                    print("PROBLEM OPENING JSON FILE (PROBABLY BEING WRITTEN TO CURRENTLY)")
                    print(e)
       
            # Open JSON data
            with open("/home/weston/proteus_stuff/STM32MP157F_Demo/upstream_data.json", "r") as upstream_file:
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
