#upython standard libraries
import time, ujson

#local imports
from am2315 import AM2315
from data_stream import DataStreamClient

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

#test acquiring and push one data sample
d = {} #stores sample data

#acquire a data sample
ht_sensor.get_data(d)
print(d)
#push data to the data stream
reply = dsc.push_data(d.items())
print(reply)
