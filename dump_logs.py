import os

# FIXME get from config file instead
DATA_CACHE_FILENAME = "data_cache.csv"
ERROR_LOG_FILENAME  = "error_log.txt"


print('#'*80)
print("# Dumping data chat file '%s'" % ERROR_LOG_FILENAME)
print('#')

if ERROR_LOG_FILENAME in os.listdir():
    f = open(ERROR_LOG_FILENAME,'r')
    print(f.read())
else:
    print("%r" % None)

print('#'*80)
print("# Dumping data cache file '%s'" % DATA_CACHE_FILENAME)
print('#')

if DATA_CACHE_FILENAME in os.listdir():
    f = open(DATA_CACHE_FILENAME,'r')
    print(f.read())
else:
    print("%r" % None)
