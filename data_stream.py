import socket
from ucollections import OrderedDict

class DataStreamError(Exception):
    def __init__(self, info = None):
        if info is None:
            info = OrderedDict()
        self.info = info
    def __repr__(self):
        return "DataStreamError(method = %s, error = %r)" % (self.info['method'],self.info['error'])
    def log_info(self, **kwargs):
        msg = ["# DataStreamClient context info:"]
        for key, val in self.info.items():
            msg.append("\t%s: %r" % (key, val))
        if kwargs:
            msg.append("\n# additional context info:")
            for key, val in kwargs.items():
                msg.append("\t%s: %r" % (key, val))
            msg = "\n".join(msg)
        return msg

class DataStreamClient(object):
    # Data Stream Service is modeled on the Phant project
    HTTP_GET_TEMPLATE = "GET /input/{public_key}?private_key={private_key}&{params} HTTP/1.0\r\nHost: {host}:{port}\r\n\r\n"
    SUCCESS_REPLY     = "1 success"
    def __init__(self, host, port, public_key, private_key, debug = False):
        self.host        = host
        self.port        = port
        self.public_key  = public_key
        self.private_key = private_key
        self._debug      = debug
        self._info       = OrderedDict()

    def push_data(self, items):
        if self._debug:
            print("### DataStreamClient.push_data ###")
        try:
            self._info['method'] = 'DataStreamClient.push_data'
            self._info['items'] = items
            
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
            if self._debug:
                print("REQUEST: %r" % req)
            self._info['request'] = req
            
            #open a web socket and send GET request
            sock = socket.socket()
            addr = socket.getaddrinfo(self.host, self.port)[0][-1]
            self._info['addr'] = addr
        
            sock.connect(addr)
            if self._debug:
                print("Connection made to addr:",addr)
            sock.send(bytes(req,'utf8'))
            
            #receive reply
            buff = []
            while True:
                data = sock.recv(100)
                if data:
                    buff.append(str(data, 'utf8'))
                else:
                    break
            reply = "".join(buff)
            if self._debug:
                print("REPLY: %r" % reply)
            header, text = reply.split("\r\n\r\n",1)
            self._info['reply_header'] = header
            self._info['reply_text'] = text
            
            #chek the reply
            if not text.strip() == self.SUCCESS_REPLY: #GET request failed
                raise Exception('request_failed')
                
            return (header,text)
            
        except Exception as exc:
            #tack on contextual information to exception
            self._info['error'] = exc
            wrapped_exc = DataStreamError(self._info)
            raise wrapped_exc
            
        finally:#make sure socket gets closed no matter what errors
            sock.close()
