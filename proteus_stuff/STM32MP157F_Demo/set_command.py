import json
import sys
import time

input = sys.argv[1]
command_dict = {"command":input}
with open("/home/weston/proteus_stuff/STM32MP157F_Demo/downstream_commands.json", "w") as downstream_file:
    json.dump(command_dict, downstream_file)
time.sleep(5)
