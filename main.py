#upython standard libraries
import sys, time, ujson, gc, micropython, network

#local imports
from am2315 import AM2315
from mhz14  import MHZ14
from data_stream import DataStreamClient

#DEBUG = False
DEBUG = True

SAMPLE_DELAY = 10 #seconds

#read the SECRET configuration file, NOTE this contains PRIVATE keys and 
#should never be posted online
config = ujson.load(open("SECRET_CONFIG.json",'r'))

#configure humidity/temperature sensor interface
ht_sensor = AM2315()

#configure CO2 sensor interface
co2_sensor = MHZ14()

#check on the network status and wait until connected 
#NOTE this is import after calling machine.reset()
wlan = network.WLAN(network.STA_IF)
for i in range(5):
    if wlan.isconnected():
        break
    time.sleep(1.0)
    if DEBUG:
        print("waiting for WLAN to connect")
else:
    raise Exception("timed out waiting for network connection")

#configure the persistent data stream client
dbs = config['database_server_settings']
dsc = DataStreamClient(host=dbs['host'],
                       public_key=dbs['public_key'],
                       private_key=dbs['private_key'])

#dsc.open_connection()
d = {} #stores sample data
while True:
    try:
        #acquire a humidity and temperature sample
        ht_sensor.get_data(d)
        #acquire CO2 concentration sample
        co2_sensor.get_data(d)
        #debug reporting
        if DEBUG:
            print(d)
        #push data to the data stream
        #reply = dsc.push_data(d.items())
        if DEBUG:
            print(reply)
    except Exception as exc:
        #write error to log file
        errorlog = open("errorlog.txt",'w')
        sys.print_exception(exc, errorlog)
        errorlog.close()
        if DEBUG:
            sys.print_exception(exc) #print to stdout
            #re raise the exception to halt the program
            raise exc
    #force garbage collection
    gc.collect()
    #print some debugging info
    if DEBUG:
        print("Memory Free: %d" % gc.mem_free())
        print(micropython.mem_info())
    #wait a bit before taking another sample
    time.sleep(SAMPLE_DELAY)
