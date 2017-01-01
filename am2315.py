import time
import machine

DEBUG = False
#DEBUG = True

NULL_BUFFER = bytearray(0)
REQUEST_HUMID_TEMP = bytearray(b"\x03\x00\x04")

class AM2315(object):
    """driver for Aosong AM2315 - Encased I2C Temperature/Humidity Sensor 
       based on github.com/adafruit/Adafruit_AM2315
    """
    def __init__(self, SCL = 5, SDA = 4, i2c_addr = 0x5C):
        self._i2c = machine.I2C(machine.Pin(SCL),machine.Pin(SDA))
        self._addr = i2c_addr
        self._data_buff = bytearray(8)
        
    def _wakeup(self):
        ## Wake up the sensor by writing its address on the bus
        try:
            self._i2c.writeto(self._addr, NULL_BUFFER)
        except OSError: #this is expected from a sleeping sensor with no ACK
            if DEBUG:
                print("on first attempt, no ACK from addr: 0x%02x" % self._addr)
        time.sleep_ms(10)
        #repeat to confirm ACK
        try:
            self._i2c.writeto(self._addr, NULL_BUFFER)
        except OSError: #not expected
            raise Exception("on second attempt, no ACK from addr: 0x%02x" % self._addr)
            
    def get_data(self, d = None):
        self._wakeup()
        self._i2c.writeto(self._addr,REQUEST_HUMID_TEMP)
        time.sleep_ms(10)
        self._i2c.readfrom_into(self._addr,self._data_buff)
        db = self._data_buff
        if d is None:
            d = {}
        d['humid'] = (256*db[2] + db[3])/10.0
        temp  = (256*(db[4] & 0x7F) + db[5])/10.0
        if db[4] >= 128:
            temp = -temp
        d['temp'] = temp
        return d
