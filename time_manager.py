try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

import network
import machine
import utime

# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600

host = "pool.ntp.org"

#DEBUG = False
DEBUG = True

class TimeManager(object):
    def __init__(self):
        #load the station network interface so we can determine connection status
        self.sta_if = network.WLAN(network.STA_IF)
        self.rtc = machine.RTC()

    def request_ntp_time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1b
        addr = socket.getaddrinfo(host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        # There's currently no timezone support in MicroPython, so
        # utime.localtime() will return UTC time (as if it was .gmtime())
        t = val - NTP_DELTA
        tm = utime.localtime(t)
        if DEBUG:
            print("Received NTP time t=%d, tm=%r" % (t,tm))
        return tm
    
    def get_datetime(self, force_RTC_time = False, sync_RTC = True):
        if self.sta_if.isconnected() and not force_RTC_time:
            try:
                tm = self.request_ntp_time()
                dt = tm[0:3] + (0,) + tm[3:6] + (0,)
                if sync_RTC:
                    if DEBUG:
                        print("Synchronizing RTC to NTP time")
                        print("RTC time before:",self.rtc.datetime())
                    self.rtc.datetime(dt) #sync the RTC
                    if DEBUG:
                        print("RTC time after:",self.rtc.datetime())
            except OSError as err:
                print("WARNING! got exception: %s" % err)
        return self.rtc.datetime()
            
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    import network_setup
    network_setup.do_connect()
    TM = TimeManager()
    print(TM.get_datetime())
#    print(TM.get_datetime(force_RTC_time = True))
#    utime.sleep(1)
#    print(TM.get_datetime())
#    print(TM.get_datetime(force_RTC_time = True))
#    utime.sleep(1)
#    print(TM.get_datetime())
#    print(TM.get_datetime(force_RTC_time = True))
