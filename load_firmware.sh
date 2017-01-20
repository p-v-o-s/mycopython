#!/bin/bash -x
esptool.py -p /dev/ttyUSB0 --baud 460800 erase_flash
esptool.py -p /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 firmware-combined.bin
