# mycopython
This project is a simple internet-connected open datalogging device that is geared towards mushroom growroom (or greenhouse) monitoring - the acquired measurements include temperature, relative humidity (%RH), and carbon dioxide concentration (ppm). The intended hardware platform is the [ESP8266](https://espressif.com/en/products/hardware/esp8266ex/overview) WiFi running a customized build of Adafruit's [CircuitPython](https://circuitpython.readthedocs.io/en/latest/README.html) firmware (a fork of the micropython project).  Early prototypes have been based on [Adafruit's Feather HUZZAH board](https://www.adafruit.com/product/2821), with an [AM2315 - Encased I2C Temperature/Humidity Sensor](https://www.adafruit.com/products/1293), and a Winsen [MH-Z14](http://www.winsen-sensor.com/products/ndir-co2-sensor/mh-z14.html) or [MH-Z19B](http://www.winsen-sensor.com/products/ndir-co2-sensor/mh-z19b.html) NDIR CO2 sensor.  The [custom CircuitPython firmware](https://github.com/open-eio/circuitpython)  customized with software serial functionality to avoid comaptibility issues with using the ESP8266's hardware UARTs (see this [Micropython forum thread](https://forum.micropython.org/viewtopic.php?t=2204) for more info).

## Device Firmware/Software Loading on Debian Linux/Ubuntu
### Install required packages
```
sudo apt-get install screen python-pip python-serial
sudo pip install adafruit-ampy esptool --upgrade
```
### Flash the CircuitPython firmware
Run the shell script `./load_firmware.sh`, either with `sudo` prepended or adding the user account to the `dialout` group (for `/dev/tty*` read/write permissions).  
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
