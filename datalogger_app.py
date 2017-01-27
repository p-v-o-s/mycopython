#upython standard libraries
import os, time, sys, utime, ujson, gc, micropython, network, machine
from ucollections import OrderedDict

#local imports
import network_setup
from data_stream  import DataStreamClient
from time_manager import TimeManager
from am2315 import AM2315
from mhz14  import MHZ14

WEEKDAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

DATA_CACHE_FILENAME = "data_cache.csv"

#read the SECRET configuration file, NOTE this contains PRIVATE keys and 
#should never be posted online
config = ujson.load(open("SECRET_CONFIG.json",'r'))

#GPIO setup
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



#connect to the network
sta_if, ap_if = network_setup.do_connect(**config['network_setup'])

pulse_led(500)
time.sleep(0.5)
pulse_led(500)

#initialize the RTC via the TimeManager class
TM = TimeManager(**config['time_manager'])
print(TM.get_datetime())

#configure the persistent data stream client
dsc = DataStreamClient(**config['data_stream'])



#preallocate slots in the data dictionary
d = OrderedDict() #stores sample data
d['rtc_timestamp'] = None
d['local_hour']    = None
d['humid']         = None
d['temp']          = None
d['co2_ppm']       = None

app_cfg = config['datalogger_app']
debug           = app_cfg.get('debug', False)
tz_hour_shift   = app_cfg.get('tz_hour_shift', -5)
sample_interval = app_cfg.get('sample_interval', 60)

previous_connection_state = True #on reboot, will cause data_cache to be opened if sta_if is not connected

while True:
    start_ms = utime.ticks_ms()
    try:
        #get the current time
        dt = TM.get_datetime() #(year, month, weekday, hour, min, second, millisecond)
        if debug:
            print("raw dt =",dt)
        year, month, day, weekday, hour, minute, second, millisecond = dt
        d['rtc_timestamp'] = "{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}".format(
              year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        local_hour = (hour + tz_hour_shift) % 24
        d['local_hour']    = local_hour
        print("The day of the week is {day_name} and the local hour is {local_hour:d}.".format(day_name=WEEKDAYS[weekday], local_hour = local_hour))
        #acquire a humidity and temperature sample
        ht_sensor.get_data(d)  #adds fields 'humid', 'temp'
        #acquire CO2 concentration sample
        co2_sensor.get_data(d) #adds field 'co2_ppm'
        #debug reporting
        if debug:
            print("Data to be logged:",d)
        #check to see if we are still connected
        #connected -------------------------------------------------------------
        if sta_if.isconnected():
            #flash led once
            pulse_led(1000)
            if previous_connection_state == True: #NORMAL we continue to be connected
                if debug:
                    print("Network is connected.")
                #push data to the data stream
                reply = dsc.push_data(d.items())
                if debug:
                    print(reply)
            else:                                 #RECOVERY we had just been disconnected and now we are online
                if debug:
                    print("Network connection has been restablished!")
                #load data from flash cache and transmit all at once
                data_cache.close()
                data_cache = open(DATA_CACHE_FILENAME,'r')
                for line in data_cache:
                    #reconstruct items from values that were stored
                    vals = line.strip().split(",")
                    items = zip(d.keys(),vals)
                    if debug:
                        print("pushing cached items:",items)
                    #push data to the data stream
                    reply = dsc.push_data(items)
                #finish data backlog upload, now erase the cache
                if debug:
                    print("erasing cache file")
                data_cache.close()
                os.remove(DATA_CACHE_FILENAME)
            #set the state on completion
            previous_connection_state = True
        #disconnected ----------------------------------------------------------
        else:
            #flash led twice quickly as warning
            pulse_led(500)
            utime.sleep_ms(500)
            pulse_led(500)
            if previous_connection_state == True: #LOCAL DATA CACHE START
                if debug:
                    print("Network connection has just been lost!")
                #open flash cache file and start logging data to it
                data_cache = open(DATA_CACHE_FILENAME,'a')
            #LOCAL DATA CACHE
            #format data as CSV
            line = ",".join(map(str,d.values()))
            if debug:
                print("Writing line to cache file:",line)
            data_cache.write(line)
            data_cache.write("\n")
            data_cache.flush()
            #set the state on completion
            previous_connection_state = False
    except Exception as exc:
        #write error to log file
        #errorlog = open("errorlog.txt",'w')
        #sys.print_exception(exc, errorlog)
        #errorlog.close()
        if debug:
            sys.print_exception(exc) #print to stdout
            #re raise the exception to halt the program
            raise exc
    finally:
        #do cleanup at end of loop
        #force garbage collection
        gc.collect()
        #print some debugging info
        if debug:
            print("Memory Free: %d" % gc.mem_free())
            print(micropython.mem_info())
        #delay until next interval
        loop_ms = utime.ticks_ms() - start_ms
        leftover_ms = sample_interval*1000 - loop_ms
        if leftover_ms > 0:
            utime.sleep_ms(leftover_ms)
