# mycopython
This project is a simple internet-connected open datalogging device that is geared towards mushroom growroom (or greenhouse) monitoring - the acquired measurements include temperature, relative humidity (%RH), and carbon dioxide concentration (ppm). The intended hardware platform is the [ESP8266](https://espressif.com/en/products/hardware/esp8266ex/overview) WiFi chip running a customized build of Adafruit's [CircuitPython](https://circuitpython.readthedocs.io/en/latest/README.html) firmware (a fork of the micropython project).  Early prototypes have been based on [Adafruit's Feather HUZZAH board](https://www.adafruit.com/product/2821), with an [AM2315 - Encased I2C Temperature/Humidity Sensor](https://www.adafruit.com/products/1293), and a Winsen [MH-Z14](http://www.winsen-sensor.com/products/ndir-co2-sensor/mh-z14.html) or [MH-Z19B](http://www.winsen-sensor.com/products/ndir-co2-sensor/mh-z19b.html) NDIR CO2 sensor.  The [custom CircuitPython firmware](https://github.com/open-eio/circuitpython) has added software serial functionality to avoid comaptibility issues with using the ESP8266's hardware UARTs (see this [Micropython forum thread](https://forum.micropython.org/viewtopic.php?t=2204) for more info).  The node can be configured to send data packets into a data stream on a remote server.  So far we have implemented sending HTTP GET requests with data as parameters to a [Phant](https://learn.sparkfun.com/tutorials/pushing-data-to-datasparkfuncom/what-is-phant) server.  We have also prototyped live data visualization using the [Google Charts API](https://developers.google.com/chart/) to plot data fetched from the Phant stream.

## Device Firmware/Software Loading on Debian Linux/Ubuntu
### Install required packages
```
sudo apt-get install screen python-pip python-serial
sudo pip install adafruit-ampy esptool --upgrade
```
### Configuration
Make the needed edits to the `SECRET_CONIFG_dummy.json` file and save as `SECRET_CONFIG.json`.
#### network settings
```json
"network_setup" : {
        "debug"        : false,
        "ap_if_active" : false,
        "ap_essid"     : "mycopython-ap",
        "sta_if_active": true,
        "connections": [["your_wifi_essid","your_wifi_password"]],
    },
```
At the moment the implementation is limited to only one network in the connections list, future enhancements will allow trying addition options in sequence until a connection is made. Setting `"ap_if_active": true` will active the node's wireless access point, which may be useful for debugging purposes when a wireless LAN is not availble; however, this access point could be a security risk, so it should be disabled during deployment.
#### time manager settings
```json
"time_manager" : {
        "debug"      : false,
        "host"       : "pool.ntp.org",
        "port"       : 123,
    },
```
This configures the NTP service for synchronizing the real time clock.  Default settings should work in most cases.
#### data stream settings
```json
"data_stream" : {
        "debug"      : false,
        "host"       : "https://data.sparkfun.com/",
        "port"       : 80,
        "public_key" : "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "private_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
```
The default `"host"` (https://data.sparkfun.com/) is for development purposed and has limitations; it should be changed if you plan to set up your own Phant or compatible server.  When a new stream is created the public and private keys are given out.  NOTE: you should never keep the `"private_key"` in public version control repos (like this github repo) which would enable anyone to inject bogus data packets.
#### datalogger_app settings
"datalogger_app" : {
        "debug"           : 0,
        "sample_interval" : 60,
        "tz_hour_shift"   : -5,
}
These setting affect the main data acquisition loop: `"sample_interval"` is in seconds; `"tz_hour_shift"` sets the local hour relative to UTC; and `"debug"` has three levels -- `0` basic reporting and error messages available in REPL, `1` verbose debugging infomation and logging of errors to `error_log.txt` file (run `import dump_logs` in REPL to view); `2` same as `1` but exceptions will halt the application and dump traceback to REPL.

### Flash the CircuitPython firmware
Plug the device into any available USB port on your computer.  Run the shell script `./load_firmware.sh`, either with `sudo` prepended or adding the user account to the `dialout` group (for `/dev/tty*` read/write permissions).  
Alternatively, these commands can be run with the proper parameters:
```
esptool.py -p /dev/ttyUSB0 --baud 460800 erase_flash
esptool.py -p /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 firmware-combined.bin
```
### Install the micropython application files
Run `./load_scripts.sh` with the proper permissions. Or, alternatively:
```
ampy -p /dev/ttyUSB0 -b 115200 put SECRET_CONFIG.json
ampy -p /dev/ttyUSB0 -b 115200 put network_setup.py
ampy -p /dev/ttyUSB0 -b 115200 put data_stream.py
ampy -p /dev/ttyUSB0 -b 115200 put time_manager.py
ampy -p /dev/ttyUSB0 -b 115200 put am2315.py
ampy -p /dev/ttyUSB0 -b 115200 put mhz14.py
ampy -p /dev/ttyUSB0 -b 115200 put dump_logs.py
ampy -p /dev/ttyUSB0 -b 115200 put datalogger_app.py
ampy -p /dev/ttyUSB0 -b 115200 put main.py
ampy -p /dev/ttyUSB0 -b 115200 put boot.py
```

### Test the system in the REPL
Run the shell script `./run_repl.sh`, either with `sudo` prepended or adding the user account to the `dialout` group (for `/dev/tty*` read/write permissions). Alternatively, you can run this command run with the proper parameters:
```
screen /dev/ttyUSB0 115200
```
Use the key-stroke `<ctrl-c>` to halt the running code and enter into the REPL. Here is an example session that checks the filesystem - on a fresh installation you should see similar output when you enter the same commands:
```
Adafruit CircuitPython v1.8.5-20161020-563-g4ae191a on 2017-01-18; ESP module with ESP8266
>>> import os
>>> os.listdir()
['boot.py', 'SECRET_CONFIG.json', 'network_setup.py', 'data_stream.py', 'time_manager.py', 'am2315.py', 'mhz14.py', 'dump_logs.py', 'datalogger_app.py', 'main.py']
>>> import dump_logs
################################################################################
# Dumping data chat file 'error_log.txt'
#
None
################################################################################
# Dumping data cache file 'data_cache.csv'
#
None
>>> 
```
Finally, use the keystroke `<ctrl-d>` to soft reboot the application.  Avoid pressing any keys and in 5 seconds the `datalogger_app` should start up; below is example output:
```
PYB: soft reboot
#6 ets_task(40100164, 3, 3fff850c, 4)
WebREPL is not configured, run 'import webrepl_setup'
Waiting for connection on UART 0...timed out.
Loading datalogger_app
Configuring network settings:
        STA_IF active = True
        Attempting to connect to essid = 'dolphnet'
        WLAN is connected!
        network_config: ('192.168.1.170', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        AP_IF active = False
(2017, 1, 30, 0, 6, 6, 4, 0)
# 01:06:04
  - Data to be logged:
        rtc_timestamp: 2017-01-30T06:06:04
        local_hour: 1
        humid: 23.2
        temp: 20.39999
        co2_ppm: 400
  - Data Stream Server response: 1 success

# 01:07:04
  - Data to be logged:
        rtc_timestamp: 2017-01-30T06:07:04
        local_hour: 1
        humid: 23.2
        temp: 20.39999
        co2_ppm: 400
  - Data Stream Server response: 1 success
```
Check to see if your data stream has new points being added.  The device can now be unplugged from your computer and plugged into a USB wall power supply.  The onboard LED will flash for 1 sec once when data is being sampled at the start of each cycle.
