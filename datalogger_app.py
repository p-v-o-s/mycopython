#upython standard libraries
import os, time, sys, utime, ujson, gc, micropython, network, machine
from ucollections import OrderedDict

from machine import WDT


#local imports
import network_setup
from data_stream  import DataStreamError, DataStreamClient
from time_manager import TimeManager
from am2315 import AM2315
from mhz14  import MHZ14

WEEKDAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

# FIXME get from config file instead
DATA_CACHE_FILENAME = "data_cache.csv"
ERROR_LOG_FILENAME  = "error_log.txt"

#read the SECRET configuration file, NOTE this contains PRIVATE keys and 
#should never be posted online
config = ujson.load(open("SECRET_CONFIG.json",'r'))

#load configuration for this module
app_cfg = config['datalogger_app']
DEBUG   = app_cfg.get('debug', False)

#-------------------------------------------------------------------------------
# File system setup

#erase the previous data cache file
if DATA_CACHE_FILENAME in os.listdir():
    if DEBUG >= 1:
        print("Removing file %s" % DATA_CACHE_FILENAME)
    os.remove(DATA_CACHE_FILENAME)

#erase the previous error log file
if DEBUG == 0:
    if ERROR_LOG_FILENAME in os.listdir():
        print("Removing file %s" % ERROR_LOG_FILENAME)
        os.remove(ERROR_LOG_FILENAME)

#-------------------------------------------------------------------------------
# Hardware setup

led_pin  = machine.Pin(2, machine.Pin.OUT)

def pulse_led(duration_ms = 1000):
    led_pin.low() #is active low on Feather HUZZAH
    utime.sleep_ms(duration_ms)
    led_pin.high()
    
pulse_led(1000)

#configure humidity/temperature sensor interface
ht_sensor = AM2315()

#configure CO2 sensor interface
co2_sensor = MHZ14()

ht_sensor.init()   #wakes the sensor up
co2_sensor.init()  #wakes the sensor up

# ------------------------------------------------------------------------------
# Network/Services setup

sta_if, ap_if = network_setup.do_connect(**config['network_setup'])

pulse_led(500)
time.sleep(0.5)
pulse_led(500)

#initialize the RTC via the TimeManager class
TM = TimeManager(**config['time_manager'])
print(TM.get_datetime())

#configure the persistent data stream client
dsc = DataStreamClient(**config['data_stream'])


################################################################################
# Main Loop
################################################################################
sample_interval     = app_cfg.get('sample_interval', 60)
tz_hour_shift       = app_cfg.get('tz_hour_shift', -5)
watchdog_timeout_s = app_cfg.get('watchdog_timeout_s', 600)



#preallocate slots in the data dictionary
d = OrderedDict() #stores sample data
d['rtc_timestamp'] = None
d['local_hour']    = None
d['humid']         = None
d['temp']          = None
d['co2_ppm']       = None

#on reboot, will cause data_cache to be opened if sta_if is not connected
previous_connection_state = True
current_connection_state  = True

while True:
    start_ms = utime.ticks_ms()
    try:
        if DEBUG >= 1:
            print("-"*80)
            print("--- MAIN LOOP START ---")
        #get the current time
        dt = TM.get_datetime() #(year, month, weekday, hour, min, second, millisecond)
        if DEBUG >= 1:
            print("raw dt =",dt)
        year, month, day, weekday, hour, minute, second, millisecond = dt
        d['rtc_timestamp'] = "{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}".format(
              year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        local_hour = (hour + tz_hour_shift) % 24
        d['local_hour']    = local_hour
        if DEBUG >= 1:
            print("The day of the week is {day_name} and the local hour is {local_hour:d}.".format(day_name=WEEKDAYS[weekday], local_hour = local_hour))
        #acquire a humidity and temperature sample
        ht_sensor.get_data(d)  #adds fields 'humid', 'temp'
        #acquire CO2 concentration sample
        co2_sensor.get_data(d) #adds field 'co2_ppm'
        #Minimal Rporting
        tmp = "{local_hour:02d}:{minute:02d}:{second:02d} - Data to be logged:"
        report_header = tmp.format(local_hour = local_hour,
                            minute = minute,
                            second = second,
                           )
        print(report_header)
        for key, val in d.items():
            print("\t%s: %s" % (key,val))
        #check to see if we are still connected
        # CONNECTED ------------------------------------------------------------
        current_connection_state = sta_if.isconnected()
        if current_connection_state == True:
            #flash led once
            pulse_led(1000)
            #NORMAL we continue to be connected
            if previous_connection_state == True:
                if DEBUG >= 1:
                    print("Network is connected.")
                #push data to the data stream
                reply = dsc.push_data(d.items())
                if DEBUG >= 1:
                    print("<REPLY>\n<HEADER>\n{}\n</HEADER>\n<TEXT>\n{}</TEXT>\n</REPLY>".format(*reply))
            #RECOVERY we had just been disconnected and now we are online
            else:
                if DEBUG >= 1:
                    print("Network connection has been restablished!")
#                #load data from flash cache and transmit all at once
#                try:
#                    data_cache = open(DATA_CACHE_FILENAME,'r')
#                    for line in data_cache:
#                        #reconstruct items from values that were stored
#                        vals = line.strip().split(",")
#                        items = zip(d.keys(),vals)
#                        if DEBUG >= 1:
#                            print("pushing cached items:",items)
#                        #push data to the data stream
#                        reply = dsc.push_data(items)
#                    #finish data backlog upload, now erase the cache
#                    if DEBUG >= 1:
#                        print("erasing cache file")
#                finally:
#                    data_cache.close()
#                    os.remove(DATA_CACHE_FILENAME)
            #set the state on completion
            previous_connection_state = True
        # DISCONNECTED----------------------------------------------------------
        else:
            #flash led twice quickly as warning
            pulse_led(500)
            utime.sleep_ms(500)
            pulse_led(500)
            if previous_connection_state == True: #LOCAL DATA CACHE START
                if DEBUG >= 1:
                    print("Network connection has just been lost!")
                #open flash cache file and start logging data to it
                #data_cache = open(DATA_CACHE_FILENAME,'a')
#            #LOCAL DATA CACHE
#            #format data as CSV
#            line = ",".join(map(str,d.values()))
#            if DEBUG >= 1:
#                print("Writing line to cache file:",line)
#            data_cache.write(line)
#            data_cache.write("\n")
#            data_cache.flush()
            #set the state on completion
            previous_connection_state = False
    #---------------------------------------------------------------------------
    # Error Handling
    except Exception as exc:
        if DEBUG >= 1:
            print("*"*80)
            print("*** ERROR_HANDLER ***")
            #write error to log file
            errorlog = open(ERROR_LOG_FILENAME,'a')
            dt = TM.get_datetime(force_RTC_time = True)
            timestamp = "{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}".format(
                         year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            #ouput the header with timestamp
            errorlog.write("#"*80)
            errorlog.write("\n# {timestamp} - datalogger_app handled error\n".format(timestamp=timestamp))
            errorlog.write("#"*(len(timestamp)+2))
            errorlog.write("\n")
            sys.print_exception(exc, errorlog)
        
            #count the number of data points in the cache
            data_cache_size = 0
            if DATA_CACHE_FILENAME in os.listdir():
                try:
                    data_cache = open(DATA_CACHE_FILENAME,'r')
                    data_cache_size = len(data_cache.readlines)
                finally:
                    data_cache.close()
            
            log_info_func = getattr(exc,'log_info', None) #object, method name, default
            if log_info_func:
                errorlog.write("#"*3)
                errorlog.write("\n")
                errorlog.write(log_info_func(
                                   current_connection_state  = current_connection_state,
                                   previous_connection_state = previous_connection_state,
                                   data_cache_size = data_cache_size,
                               ))
            errorlog.write("\n\n")
            errorlog.close()
            sys.print_exception(exc) #print to stdout
            print("*"*80)
        if DEBUG >= 2:
            #re raise the exception to halt the program
            raise
        
    #---------------------------------------------------------------------------
    # Cleanup
    finally:
        if DEBUG >= 1:
            print("-"*80)
            print("--- CLEANUP ---")
        #do cleanup at end of loop
        #force garbage collection
        gc.collect()
        #print some debugging info
        if DEBUG >= 1:
            print("Memory Free: %d" % gc.mem_free())
            print(micropython.mem_info())
        #delay until next interval
        loop_ms = utime.ticks_ms() - start_ms
        leftover_ms = sample_interval*1000 - loop_ms
        if leftover_ms > 0:
            utime.sleep_ms(leftover_ms)
