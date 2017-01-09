#upython standard libraries
import utime, ujson, network

#DEBUG = False
DEBUG = True

#read the SECRET configuration file, NOTE this contains PRIVATE keys and 
#should never be posted online
config = ujson.load(open("SECRET_CONFIG.json",'r'))

def do_connect():
    #check on the network status and wait until connected 
    print("Configuring network settings:")
    ns = config['network_settings']

    has_connection = False

    #first configure the station interface
    wlan = network.WLAN(network.STA_IF)
    sta_if_active = ns.get('sta_if_active', False) #default to inactive station interface
    wlan.active(sta_if_active)
    print("\tSTA_IF active = %s" % sta_if_active)
    if sta_if_active:
        for cn in ns['connections']:
            print("\tAttempting to connect to essid = '%s'" % cn[0])
            wlan.connect(cn[0],cn[1])
            #check that we have actually connected
            # NOTE this is import after calling machine.reset()
            for i in range(10):
                if wlan.isconnected():
                    print("\tWLAN is connected!")
                    print("\tnetwork_config:", wlan.ifconfig())
                    has_connection = True
                    break
                utime.sleep_ms(1000)
                if DEBUG:
                    print("\twaiting for WLAN to connect")
            else:
                print("\tWarning: Failed to connect to external network!")

    #next configure access point interface
    ap = network.WLAN(network.AP_IF)
    #default to active access point if we don't already have a connection
    ap_if_active = ns.get('ap_if_active',not has_connection)
    print("\tAP_IF active = %s" % ap_if_active)
    ap.active(ap_if_active)
    if ap_if_active:
        ap_essid = ns.get('ap_essid')
        if not ap_essid is None:
            print("\tsetting AP essid = '%s'" % ap_essid)
            ap.config(essid=ns['ap_essid'])
        
if __name__ == "__main__":
    do_connect()
