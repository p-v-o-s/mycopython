import time
import machine

DEBUG = False
#DEBUG = True


class AM2315(object):
    REQUEST_HUMID_TEMP = "\x03\x00\x04"
    def __init__(self, SCL = 5, SDA = 4, i2c_addr = 0x5C):
        self._i2c = machine.I2C(machine.Pin(SCL),machine.Pin(SDA))
        self._addr = i2c_addr
        self._data_buff = bytearray(8)
    def _wakeup(self):
        ## Wake up the sensor by scanning
        found_addrs = self._i2c.scan()
        if not self._addr in found_addrs:
            #try again, first time wakes up sensor
            time.sleep_ms(10)
            found_addrs = self._i2c.scan()
        if self._addr in found_addrs:
            if DEBUG:
                print("found I2C device with addr: %02x" % self._addr)
        else:
            #sensor not found
            print("WARNING: i2c.scan did not detect I2C device with addr: %02x" % self._addr)
    def get_data(self):
        self._wakeup()
        self._i2c.writeto(self._addr,self.REQUEST_HUMID_TEMP)
        time.sleep_ms(10)
        self._i2c.readfrom_into(self._addr,self._data_buff)
        db = self._data_buff
        d = {}
        d['humid'] = (256*db[2] + db[3])/10.0
        temp  = (256*(db[4] & 0x7F) + db[5])/10.0
        if db[4] >= 128:
            temp = -temp
        d['temp'] = temp
        return d


am2315 = AM2315()
for i in range(5):
    time.sleep(1.0)
    print(am2315.get_data())
