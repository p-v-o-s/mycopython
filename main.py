#upython standard libraries
import time, ujson

#local imports
from am2315 import AM2315
from data_stream import DataStreamClient

#DEBUG = False
DEBUG = True

SAMPLE_DELAY = 10 #seconds

#read the SECRET configuration file, NOTE this contains PRIVATE keys and 
#should never be posted online
config = ujson.load(open("SECRET_CONFIG.json",'r'))

#configure sensor interface
ht_sensor = AM2315()


#configure the persistent data stream client
dbs = config['database_server_settings']
dsc = DataStreamClient(host=dbs['host'],
                       public_key=dbs['public_key'],
                       private_key=dbs['private_key'])

d = {} #stores sample data
while True:
    #acquire a data sample
    ht_sensor.get_data(d)
    if DEBUG:
        print(d)
    #push data to the data stream
    reply = dsc.push_data(d.items())
    if DEBUG:
        print(reply)
    #wait a bit before taking another sample
    time.sleep(SAMPLE_DELAY)













