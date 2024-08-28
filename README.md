# PROTEUS NEAI Anomaly Detection Demo on STM32MP157F-DK2 (For IoTConnect on AWS)

This demo will use a [Discovery kit with STM32MP157F MPU](https://www.st.com/en/evaluation-tools/stm32mp157f-dk2.html) and an [STEVAL-PROTEUS1 Sensor Module](https://www.st.com/en/evaluation-tools/steval-proteus1.html) to run an IoTConnect program to monitor AI-based Anomaly-Detection data in real-time on the IoTConnect cloud platform using AWS. 

<img src=".//media/image34.png"/> 

## Step 1: Make an IoTConnect Account
* To get started making an IoTConnect account, you can contact our team at info@iotconnect.io

## Step 2: Sign in to IoTConnect Account
* This demo uses IoTConnect on AWS.
* An IoTConnect account is required to continue with this guide. If you need to create an account, a free 2-month subscription is available. Please follow the [Creating a New IoTConnect Account](https://github.com/avnet-iotconnect/avnet-iotconnect.github.io/blob/main/documentation/iotconnect/subscription/subscription.md) guide and return to this guide once complete.

## Step 3: Import a Template for Your Device 
* Within this git repo, navigate to the PROTEUS_MP157F_Demo directory and click on the file called MP157F_template.JSON.

<img src=".//media/image31.png"/>

* Download the template file to your PC by clicking on the download button for the file, shown below.

<img src=".//media/image29.png"/>
  
* On the far-left side of the screen is a navy-blue toolbar, hover your cursor over the icon that looks like a processor chip and choose “Device” out of the dropdown options (shown below). 

<img src=".//media/image1.png"/>

* On the toolbar at the bottom of the page, select the “Templates” tab.

<img src=".//media/image2.png"/>

* On the Templates page, click the “Create Template” button in the top right corner of the screen. 

<img src=".//media/image3.png"/>

* In the upper-right area of the scree, click on the "Import" button.

<img src=".//media/image30.png"/>

* In the resulting pop-up window, click on the "Browse" button, navigate to where you have the template file downloaded, and select the template file. Click on the "Save" button afterwards.

<img src=".//media/image32.png"/>

## Step 4: Create a Your Device in IoTConnect
* Navigate back to the “Device” menu and click on “Create Device” in the top right corner of the screen.

<img src=".//media/image5.png"/>
     
* Enter the following information and then click “Save and View”:
   * Unique Id: <Your UniqueID/DisplayName Here>
   * Display Name: <Your UniqueID/DisplayName Here>
   * Entity: (Any Generic Entity Will Work)
   * Template: MP157F
   * Device Certificate: Auto-Generated
 
      * **NOTE: For setup simplicity, this demo is deisgned for the Unique ID and the Display Name to be exactly the same, so it is critical that you make them identical to each other. It will not work otherwise.**
 
<img src=".//media/image6.png"/>

* In the resulting page, click “Connection Info” in the top-right corner of the page.

<img src=".//media/image7.png"/>

* Click on the yellow and green certificate icon in the top-right corner of the resulting pop-up to download the zipped certificate package.

<img src=".//media/image8.png"/>

* Extract the certificate package folder and save the resulting certificates folder to a known location. You will relocate them later into the setup.

## Step 6: Flash IoTConnect-Compatible Image to STM32MP157F-DK2 Board
* To download the zipped image folder, [click here](https://saleshosted.z13.web.core.windows.net/sdk/st/stmp1/proteus/OSTL_6.1_IoTConnect_Compatible.zip).
* Unzip the folder to a known location.
* Download and Install the [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html) software (the utility for flashing the image to the device).
   * You may have to create an ST account (it's free) to get access to the software download.
* Set up the STM32MP157F-DK board for flashing:
   * On the underside of the board, flip both of the large dipswitches (directly opposite of the HDMI port) to the "OFF" position.
  
      <img src=".//media/image16.png"/>
      
   * Power the board with a USB-C cable connected to the "PWR_IN" USB-C port connected to a 5VDC supply with at least 1.0A of output.
   
      <img src=".//media/image19.png"/>
      
   * Connect the USB-C "USB" port of your board to your PC with the included USB-C cable.
      * If your PC does not have a USB-C port, you may use a USB-A to USB-C cable and connect it to a normal USB-A port on your PC.
   
      <img src=".//media/image20.png"/>
   
   * Insert the included SD card into the SD card slot on the board.
      
   * Push the "RESET" button on your board to ensure it boots into flashing mode (the LCD display of the board should be black when it has booted into flashing mode).

<img src=".//media/image18.png"/>
      
* Run the STM32CubeProgrammer software and click on the "Open file" tab.

<img src=".//media/image21.png"/>
      
* Navigate to the directory where you have the unzipped "OpenSTLinux_IoTConnect_Compatible" folder, and then navigate through the folder to get to this directory: {Your preliminary directory}\OSTL_6.1_IoTConnect_Compatible\images\stm32mp1\flashlayout_st-image-weston\optee
   * Select the FlashLayout_sdcard_stm32mp157F-dk2-optee.tsv file and then click "Open." 
   
<img src=".//media/image22.png"/>
      
* Next, click on the "Browse" button to select the binaries path.
   
<img src=".//media/image23.png"/>
   
* Navigate once again to the directory where you have the unzipped "OpenSTLinux_IoTConnect_Compatible" folder, and then navigate through the folder to get to this directory: {Your preliminary directory}\OSTL_6.1_IoTConnect_Compatible\images\stm32mp1
   * Select the stm32mp1 folder and then click "Select folder."

<img src=".//media/image24.png"/>
      
* Back in the STM32CubeProgrammer window, on the right-hand side of the screen, if the "Port" is listed as "No DFU...," make sure your USB cable is connected both to your PC and the board, and then click the revolving arrows icon.

<img src=".//media/image25.png"/>
     
* When the device is recognized by the software, the port listing will be "USB" followed by a number, such as 1. The serial number of your board should also be listed beneath the port name.

<img src=".//media/image26.png"/>
    
* You are ready to flash. Click the "Download" button to begin the flashing process.
   * The STM32MP157F-DK2 will turn off and on several times throughout the flashing process. It is important to not unplug or disturb it during the process. Given the size of the image it will usually take **up to 45 minutes** to flash.
   * It is worth noting that the LCD screen on the board will turn on with some output text during the flash process, so do not be alarmed.

<img src=".//media/image27.png"/>
   
* When the flash has completed successfully, this pop-up in the STM32CubeProgrammer window will appear.

<img src=".//media/image28.png"/>
   
* Now, flip the large dipswitches on the underside of your board both to the "ON" position, and once again hit the reset button to properly boot the new image from the SD card.

<img src=".//media/image17.png"/>
   
* **For the first boot after flashing, the board takes a few minutes to turn on.**

* To complete the setup process:
   * Connect your board to the internet by either using an ethernet cable, or by following the optional Wi-Fi configuration step below.
   * You will also need to connect the STM32MP157 Discovery kit to your PC using a USB-A to micro-USB cable. Connect to the assigned COM Port using serial console application, such as [Tera Term](https://ttssh2.osdn.jp/index.html.en), or a browser application like [Google Chrome Labs Serial Terminal](https://googlechromelabs.github.io/serial-terminal/). Optionally, you may connect the board to an external monitor using the HMDI port and a keyboard/mouse.
 
## Step 7: Prepare PROTEUS Sensor Module
* To prepare your PROTEUS, you will need a custom NEAI Anomaly Detection firmware file. For the purposes of this simple demo, you can download a pre-made one by clicking on the PDMWBSOC.bin file in the repository, and then clicking as shown here:

<img src=".//media/app_image_5.png"/>

* Since the firmware flashing will be done from a smartphone, you will need to send and save this file to your smartphone (email is probably the easiest way). 

* After assembling your PROTEUS sensor module, power it on using a micro-usb cable.

* On a smartphone (IOS or Android), install the ST BLE Sensor App.

<img src=".//media/app_image_1.png"/>

* Turn your device's bluetooth on, and then open the app. The PROTEUS module should be discovered. If not, refresh the page until it is.

* Take note of the MAC address of your PROTEUS, including the colons. You will need to use this in the config file during the next step.

<img src=".//media/app_image_2.png"/> 

* After tapping on your PROTEUS in the device discovery screen, tap on the gear icon in the top-right of your screen, and then "Firmware Upgrade" in the resulting pop-up.

<img src=".//media/app_image_3.png"/>

* Tap on the blue folder icon, select the PDMWBSOC.bin file, and then tap the "UPGRADE" button to flash the firmware.

<img src=".//media/app_image_4.png"/>

* After the flash has completed, the PROTEUS will automatically reboot and you can close out of the app. Your PROTEUS is now ready to use.

## Step 8: Prepare Necessary Files
* In another browser tab, navigate to [the top of this repository](https://github.com/avnet-iotconnect/proteus-neai-demo/tree/main) and download the repository's zip file as shown here:

<img src=".//media/image_a.png"/>

* Unzip the downloaded folder and then open it.
  
* Navigate to the *proteus-neai-demo-main* directory (the name of the overall repo and the first sub-directory will have the same name after extraction)
  
* Copy the interior *proteus-neai-demo-main* directory to a flash drive.

* In the *proteus-neai-demo-main* directory on your flash drive, navigate to the *device_certificates* folder.

* Copy your two individual device certificates from the folder you saved in Step 4 into this folder. **You cannot copy the whole certificate folder, you must copy the individual *.pem* and *.crt* files.**

* Back in the *proteus-neai-demo-main* directory, open up the file *config.py* in a generic text editor.

* To find your CPID and Environment, navigate to your main IoTConnect dashboard page, hover your cursor over the gear icon on the tollbar located on the far-left side of the page, and then click "Key Vault":

<img src=".//media/image9.png"/>

* Your CPID and Environment will be shown as in the image below:

<img src=".//media/image10.png"/>

* Copy your CPID and Environment into the *cpid* and *env* fields of *config.py*, **within the quotation marks.**

* Enter the Unique ID for your device from Step 4 into the *unique_id* field, **within the quotation marks.**

* Enter the MAC address for your PROTEUS from step 7 into the *mac_address* field, **including colons, letters lower-cased, within the quotation marks.**

* Save the *config.py* file and close the text editor.

* Now remove the flash drive from your PC and insert it into a USB port on the STM32MP157F-DK2 gateway.

## Step 9: Configure the Gateway

* These steps can be completed using the serial terminal connected to the ST Discovery board, or using the weston terminal directly on the gateway.

* First, get admin privileges by entering this command:
  * ```su```

* Create a directory for the flash drive to mount to with this command:
  * ```mkdir /media/usbdrive```

* Now, mount the flash drive using this command:
  * ```mount /dev/sda1 /media/usbdrive```
    * If that command fails (will only fail if you have plugged/unplugged the flash drive from the gateway more than once), use this longer command instead:
      * ```mount /dev/sdb1 /media/usbdrive || mount /dev/sdc1 /media/usbdrive || mount /dev/sdd1 /media/usbdrive```

* **Wi-Fi Configuration (OPTIONAL)**
  * To connect the gateway to the wireless network, execute this command:
    * ```/media/usbdrive/Proteus-NEAI-Demo/Wifi_Setup.sh```
      * NOTE: You will be asked to enter your network SSID and password during this script, as well as if it is your first time connecting the gateway to Wi-Fi
        * If you have already connected the gateway to Wi-Fi before and need to change the SSID or password, simply run the script again and answer **Y** to the first prompt
 
* Execute this command to run the rest of the automatic gateway setup:
  * ```/media/usbdrive/Proteus-NEAI-Demo/Proteus_Demo_Setup.sh```
  * **NOTE: This setup script may take several minutes to complete.** 
 
* The main IoTConnect program has been configured to run on boot, so now reboot the gateway with the command:
  * ```reboot```

## Step 10: Remotely Command the Proteus and View the Data
* Navigate back to the “Devices” menu and locate your device in the list.
   * You should see that the entry in the "Device Status" column shows a green "CONNECTED" label.

<img src=".//media/image13.png"/>

* After clicking on youir device, click on the "Command" button on the left sidebar, then select the "Activate Learning" from the dropdown, and click "Execute Command"

<img src=".//media/image_101.png"/>

* For the next 10 seconds, the device will "learn" what the "NORMAL" state is, so it is imperative that the PROTEUS is left alone during the entire learning duration.
  * To play it safe, it is recommended to leave the PROTEUS alone for 20-30 seconds after sending the "Activate Learning" command. It has a built-in learning timer, so it the learning phase does not need to be manually ended.
 
* After the 20-30 seconds are up, you can send the "Activate Anomaly Detection" command.

* To view the Anomaly Detection data, navigate to the "Live Data" page (also on the left toolbar) and pay attention to the "NEAI_status" and "NEAI_similarity_percentage" entries.

* In the example below, during the entries that reported as "NORMAL," the PROTEUS was left sitting ona  table, just as it was during the learning phase. During the entries that reported as "ANOMALY," the PROTEUS was being lightly shaken around.

 <img src=".//media/image_102.png"/>

 * To teach the PROETUS a new NORMAL state:
   * First send the "Stop Anomaly Detection" command.
   * Next send the "Reset Knowledge" command to wipe the previous learning, and then wait for approximately 10 seconds.
   * Then, put the PROTEUS in the environment/state that it should recognize as "normal" and then send the "Activate Learning" command.
   * Your PROTEUS now has learned a new normal state and anomaly detection can be activated again.

