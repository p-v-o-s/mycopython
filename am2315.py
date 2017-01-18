import utime
import machine
#import board, bitbangio

DEBUG = False
#DEBUG = True

CMD_NULL_REQUEST       = bytes(())
CMD_REQUEST_HUMID_TEMP = bytes((0x03,0x00,0x04))


class AM2315(object):
    """driver for Aosong AM2315 - Encased I2C Temperature/Humidity Sensor 
       based on github.com/adafruit/Adafruit_AM2315
    """
    def __init__(self, scl = 5, sda = 4, i2c_addr = 0x5C):
        #if scl is None:
        #    scl = board.GPIO5
        #if sda is None:
        #    sda = board.GPIO4
        #self._i2c = bitbangio.I2C(scl,sda) #FIXME wakeup doesn't work yet
        self._i2c = machine.I2C(-1,machine.Pin(scl),machine.Pin(sda))
        self._addr = i2c_addr
        self._data_buff = bytearray(8)
        self.active = False
        
    def init(self):
        for i in range(5):
            try:
                self._wakeup()
                self.active = True
                break
            except Exception:
                print("failed attempt #%d to wakup addr: 0x%02x" % (i,self._addr))
                utime.sleep_ms(1000)
        else:
            print("WARNING: Initialization of AM2315 sensor failed!\n\tsetting attribute active=False")
            self.active = False
            
    def _wakeup(self):
        ## Wake up the sensor by writing its address on the bus
        try:
            self._i2c.writeto(self._addr, CMD_NULL_REQUEST)
        except OSError: #this is expected from a sleeping sensor with no ACK
            if DEBUG:
                print("on first attempt, no ACK from addr: 0x%02x" % self._addr)
        utime.sleep_ms(10)
        #repeat to confirm ACK
        try:
            self._i2c.writeto(self._addr, CMD_NULL_REQUEST)
        except OSError: #not expected
            raise Exception("on second attempt, no ACK from addr: 0x%02x" % self._addr)
            
    def get_data(self, d = None):
        if d is None:
            d = {}
        if not self.active:
            return d
        else:
            self._wakeup()
            self._i2c.writeto(self._addr,CMD_REQUEST_HUMID_TEMP)
            utime.sleep_ms(10)
            self._i2c.readfrom_into(self._addr,self._data_buff)
            db = self._data_buff
            
            d['humid'] = (256*db[2] + db[3])/10.0
            temp  = (256*(db[4] & 0x7F) + db[5])/10.0
            if db[4] >= 128:
                temp = -temp
            d['temp'] = temp
            return d
            
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    ht_sensor = AM2315()
    ht_sensor.init()
    d = {}
    ht_sensor.get_data(d)
    print(d)
