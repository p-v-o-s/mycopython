DEBUG = False
DEBUG = True

import socket


class DataStreamClient(object):
    HTTP_GET_TEMPLATE = "GET /input/{public_key}?private_key={private_key}&{params} HTTP/1.0\r\nHost: {host}:{port}\r\n\r\n"
    
    def __init__(self, host, port, public_key, private_key):
        self.host        = host
        self.port        = port
        self.public_key  = public_key
        self.private_key = private_key

    def push_data(self, items):
        #pack data into a parameters list
        params = "&".join(["%s=%s" % kv for kv in items])
        #format data into an HTTP GET request
        req = self.HTTP_GET_TEMPLATE.format(
            public_key  = self.public_key,
            private_key = self.private_key,
            params      = params,
            host        = self.host,
            port        = self.port,
        )
        if DEBUG:
            print(req)
        #open a web socket and send GET request
        sock = socket.socket()
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        if DEBUG:
            print("Connection made to addr:",addr)
        sock.connect(addr)
        sock.send(bytes(req,'utf8'))
        #receive reply
        buff = []
        while True:
            data = sock.recv(100)
            if data:
                buff.append(str(data, 'utf8'))
            else:
                break
        sock.close()
        reply = "".join(buff)
        if DEBUG:
            print(reply)
        return reply
