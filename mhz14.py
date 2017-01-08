import time
import machine

DEBUG = False
DEBUG = True


CMD_REQUEST_PPM          = bytes((0xFF,0x01,0x86,0x00,0x00,0x00,0x00,0x00,0x79))
CMD_CALIBRATE_ZERO_POINT = bytes((0xFF,0x01,0x87,0x00,0x00,0x00,0x00,0x00,0x78))

#note that byte i=3 must be set to the "high byte" reading and byte i=4 set to
#the "low byte" reading for the maximum concentration range AND byte i=8
#should be computed as the checksum = (~sum(b[1:8]) + 1) & 0xFF
CMD_CALIBRATE_SPAN_POINT = bytearray((0xFF,0x01,0x88,0x00,0x00,0x00,0x00,0x00,0x00))

class MHZ14(object):
    """driver for Winsen MHZ-14 - NDIR CO2 SENSOR
       http://www.winsen-sensor.com/products/ndir-co2-sensor/mh-z14.html
    """
    def __init__(self, tx = 12, rx = 14,):
        self._ser = machine.SoftUART(machine.Pin(tx),machine.Pin(rx), baudrate=9600)
        self._data_buff = bytearray(9)
        
    def get_data(self, d = None, timeout = 2.0):
        self._ser.write(CMD_REQUEST_PPM)
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise Exception("data request timed out")
            time.sleep_ms(10)
            self._ser.readinto(self._data_buff)
            if DEBUG:
                print(self._data_buff)
            if self._data_buff[0] == 0xFF: #possibly valid data
                break
        db = self._data_buff
        #compute checksum to validate data
        checksum = ~sum(db[1:8])+1 & 0xFF
        if DEBUG:
            print(db,checksum)
        if checksum != db[8]:
            raise Exception("bad checksum")
        if d is None:
            d = {}
        d['ppm'] = (256*db[2] + db[3])
        return d
        
    def calibrate_zero_point(self):
        self._ser.write(CMD_REQUEST_PPM)
        
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    mhz = MHZ14()
    d = {}
    mhz.get_data(d)
    print(d)
