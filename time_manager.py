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


class TimeManager(object):
    # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
    NTP_DELTA = 3155673600
    def __init__(self,
                 host = "pool.ntp.org",
                 port = 123,
                 debug = False,
                ):
        #load the station network interface so we can determine connection status
        self.sta_if = network.WLAN(network.STA_IF)
        self.rtc = machine.RTC()
        self.host = host
        self.port = port
        self._debug = debug

    def request_ntp_time(self):
        if self._debug:
            print("### TimeManager.request_ntp_time ###")
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1b
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            addr = socket.getaddrinfo(self.host, self.port)[0][-1]
            res = sock.sendto(NTP_QUERY, addr)
            msg = sock.recv(48)
            val = struct.unpack("!I", msg[40:44])[0]
            # There's currently no timezone support in MicroPython, so
            # utime.localtime() will return UTC time (as if it was .gmtime())
            t = val - self.NTP_DELTA
            tm = utime.localtime(t)
            if self._debug:
                print("Received NTP time t=%d, tm=%r" % (t,tm))
            return tm
        finally:
            sock.close()
    
    def get_datetime(self, force_RTC_time = False, sync_RTC = True):
        if self._debug:
            print("### TimeManager.get_datetime ###")
        if self.sta_if.isconnected() and not force_RTC_time:
            try:
                tm = self.request_ntp_time()
                dt = tm[0:3] + (0,) + tm[3:6] + (0,)
                if sync_RTC:
                    if self._debug:
                        print("Synchronizing RTC to NTP time")
                        print("RTC time before:",self.rtc.datetime())
                    self.rtc.datetime(dt) #sync the RTC
                    if self._debug:
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
