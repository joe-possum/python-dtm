#7/10/2020
import serial
import sys
import time
import getopt

verbose = 0
emulate = 0

packet_types = { 'prbs9':0 }
phys = { '1m':1, '2m':2, '125k':3, '500k':4 }

def help_quit(arg) :
    print(msg_help)
    quit()

def set_lower_channel(arg) :
    global parameters
    parameters['lower-channel'] = int(arg)

def set_upper_channel(arg) :
    global parameters
    parameters['upper-channel'] = int(arg)

def set_iterations(arg) :
    global parameters
    parameters['iterations'] = int(arg)

def set_packet_type(arg) :
    global parameters
    if None == packet_types.get(arg) :
        print('Invalid packet-type specified.  Recognized packet-types: '%(' '.join(packet_types.keys())))
        help_quit()
    parameters['packet-type'] = arg
    
def set_phy(arg) :
    global parameters
    if None == phys.get(arg) :
        print('Invalid phy specified.  Recognized phys: '%(' '.join(phys.keys())))
        help_quit()
    parameters['phy'] = arg
    
def set_duration(arg) :
    global parameters
    parameters['duration-seconds'] = int(arg)

def set_byte_count(arg) :
    global parameters
    parameters['byte_count'] = int(arg)

def set_out_filename(arg) :
    global parameters
    print("set-out-filename: %s"%(arg))
    parameters['out-filename'] = arg

msg_help = 'Usage: python-dtm [ -h ] [ -l <lower-channel> ] [ -u <upper-channel> ] [ -i <iterations> ] [ -p <packet-type> ] [ -d <duration-seconds> ] [ -b <byte-count> ] [ -y <phy> ] -o <out-filename> <tx-port> [ <rx-port> [ <rx-port> [ ... ] ] ]'
parameters = {
    'lower-channel':0,
    'upper-channel':39,
    'iterations':1,
    'packet-type':'prbs9',
    'duration-seconds':1,
    'byte-count':255,
    'phy':'1m',
    'out-filename':'asd',
    'option-string':'hl:u:i:p:y:d:b:o:'
}

option_bindings = {
    '-h' : help_quit,
    '-l' : set_lower_channel,
    '-u' : set_upper_channel,
    '-i' : set_iterations,
    '-p' : set_packet_type,
    '-d' : set_duration,
    '-b' : set_byte_count,
    '-y' : set_phy,
    '-o' : set_out_filename
}

def options_sanity_check() :
    global parameters, option_bindings
    bindings = option_bindings.copy()
    error = 0
    str = parameters['option-string'].replace(':','')
    for i in range(len(str)) :
        opt = '-'+str[i]
        if None == bindings.get(opt) :
            print('No option binding for %s'%(opt))
            error = 1
        else :
            bindings.pop(opt)
    for i in bindings :
        print('No entry in option-string for %s'%(i))
        error = 1
    if error : quit()


def render(b) :
    s = ''
    for i in range(len(b)) :
        s += "%02x"%b[i]
    return s

class emulator :
    global verbose
    def __init__(self,port) :
        self.state = 0
        self.dtm = 0
        self.local = []
        self.buf = []
        self.port = port
        if verbose : print("emulator(%s)"%(port))
    def write(self,cmd) :
        self.local += list(cmd)
        while True :
            if len(self.local) < 1 : return
            if 0x20 != self.local[0] :
                raise RuntimeError("state 0: recv %s"%(render(self.local)))
            if len(self.local) < 2 : return
            if len(self.local) < self.local[1] : return
            bgclass = cmd[2]
            if 0x0e != bgclass : raise RuntimeError("bgclass 0x%02x not emulated"%(bgclass))
            method = cmd[3]
            if 0x00 == method :
                if 4 != cmd[1] : raise RuntimeError("dtm-tx: bad length %s"%(render(self.local)))
                packet = cmd[4]
                length = cmd[5]
                channel = cmd[6]
                phy = cmd[7]
                self.local = self.local[8:]
                if 0 == self.dtm :
                    self.buf += b'\x20\x02\x0e\x00\x00\x00'
                    self.buf += b'\xa0\x04\x0e\x00\x00\x00\x00\x00'
                    self.dtm = 1
                    if verbose : print('emulator: port:%s: enter dtm-tx, buf: %s'%(self.port,render(self.buf)))
                    return
                self.buf += b'\x20\x02\x0e\x00\x80\x01'
            elif 0x01 == method :
                if 2 != cmd[1] : raise RuntimeError("dtm-rx: bad length %s"%(render(self.local)))
                channel = cmd[4]
                phy = cmd[5]
                self.local = self.local[6:]
                if 0 == self.dtm :
                    self.buf += b'\x20\x02\x0e\x01\x00\x00'
                    self.buf += b'\xa0\x04\x0e\x00\x00\x00\x00\x00'
                    self.dtm = 2
                    if verbose : print('emulator: port:%s: enter dtm-rx, buf: %s'%(self.port,render(self.buf)))
                    return
                self.buf += b'\x20\x02\x0e\x01\x80\x01'
            elif 0x02 == method :
                if 0 != cmd[1] : raise RuntimeError("dtm-end: bad length %s"%(render(self.local)))
                self.local = self.local[4:]
                if 0 != self.dtm :
                    self.buf += b'\x20\x02\x0e\x02\x00\x00'
                    self.buf += b'\xa0\x04\x0e\x00\x00\x00\x34\x12'
                    self.dtm = 0
                    if verbose : print('emulator: port:%s: enter dtm-idle, buf: %s'%(self.port,render(self.buf)))
                    return
                self.buf += b'\x20\x02\x0e\x02\x80\x01'
    def read(self,count) :
        if count > len(self.buf) : raise RuntimeError("Deadlock")
        rc = self.buf[:count]
        self.buf = self.buf[count:]
        if verbose : print('emulator: port:%s: read return %s, buf: %s'%(self.port,render(rc),render(self.buf)))
        return bytes(rc)
    def read_all(self) :
        rc = buf
        buf = ''
        return rc
    def close(self) :
        return

class bgapi :
    global verbose, emulate
    def __init__(self,port) :
        self.events = []
        if emulate :
            self.fh = emulator(port)
            return
        self.fh = serial.Serial(port,baudrate=115200)
        self.port = port
        b = self.fh.read_all()
        if verbose and len(b) :
            print("read %d bytes from %s: %s"%(len(b),port))
    def get_packet(self) :
        if verbose : print('get_packet(%s): reading header'%(self.port))
        header = self.fh.read(4)
        if verbose : print('get_packet(%s): got header: %s'%(self.port,render(header)))
        length = header[1]
        if verbose : print('get_packet(%s): reading data (%d bytes)'%(self.port,length))
        data = self.fh.read(length)
        if verbose : print('get_packet(%s): got data: %s'%(self.port,render(data)))
        return header + data
    def send_command(self,command) :
        if verbose : print('send_command(%s,%s)'%(self.port,render(command)))
        if 0x20 != command[0] :
            raise RuntimeError("send_command(%s): Not a command: %s"%(self.port,render(command)))
        length = command[1]
        if len(command[4:]) != length :
            raise RuntimeError("send_command(%s): Bad command length: %s"%(self.port,render(command)))
        self.fh.write(command)
        while True :
            p = self.get_packet()
            if 0xa0 == p[0] :
                self.events.append(p)
            elif 0x20 == p[0] :
                return p
            else : raise RuntimeError("Weird packet: %s"%(render(p)))
    def dtm_tx(self,packet,length,channel,phy) :
        p = self.send_command(b'\x20\x04\x0e\x00'+bytes([packet,length,channel,phy]))
        return (p[-1] << 8) | p[-2]
    def dtm_rx(self,channel,phy) :
        p = self.send_command(b'\x20\x02\x0e\x01'+bytes([channel,phy]))
        return (p[-1] << 8) | p[-2]
    def dtm_end(self) :
        p = self.send_command(b'\x20\x00\x0e\x02')
        return (p[-1] << 8) | p[-2]
    def wait_dtm_completed(self) :
        while True :
            if len(self.events) :
                if verbose : print('wait_dtm_completed(%s): fetching from backlog'%(self.port))
                rc = self.events[0]
                events = self.events[1:]
            else :
                if verbose : print('wait_dtm_completed(%s): fetching from get_packet'%(self.port))
                rc = self.get_packet()
            if b'\xa0\x04\x0e\x00' == rc[0:4] :
                if verbose : print('wait_dtm_completed(%s): match completed, result: %04x, count: %04x'%(self.port,rc[4]+(rc[5]<<8),rc[6]+(rc[7]<<8)))
                return rc
    def close(self) :
        self.fh.close()

options_sanity_check()

options,ports = getopt.getopt(sys.argv[1:],parameters['option-string'])
print("options: ",options)
print("ports",ports)
for option in options :
    fn = option_bindings.get(option[0])
    fn(option[1])
    
if len(ports) < 1 :
    print("At minimum, tx-port must be specified")
    help_quit('')
if len(parameters['out-filename']) < 1 :
    print('-o <out-filename> is not optional')
    help_quit('')
    
tx = bgapi(ports[0])
if verbose : print("tx:",tx)

rx = []
for cp in ports[1:] :
    r = bgapi(cp)
    rx.append(r)
if verbose : print("rx:",rx)

def measure(fh, tx, rx, channel) :
    global parameters
    rx_count = []
    for r in rx :
        if r.dtm_rx(channel,1) : raise RuntimeError(r)
        r.wait_dtm_completed()

    if tx.dtm_tx(
            packet_types[parameters['packet-type']],
            parameters['byte-count'],
            channel,
            phys[parameters['phy']]
            ) : raise RuntimeError(tx)
    tx.wait_dtm_completed()
    
    if verbose : print("sleeping")
    time.sleep(parameters['duration-seconds'])
    
    if tx.dtm_end() : raise RuntimeError(tx)
    evt = tx.wait_dtm_completed()
    tx_count = evt[6] + (evt[7] << 8)
    
    for i in range(len(rx)) :
        rx[i].dtm_end()
        evt = rx[i].wait_dtm_completed()
        rx_count.append(evt[6] + (evt[7] << 8))
        
    ps = "channel: %d, sent: %d, PER:"%(channel,tx_count)
    
    fh.write('%d %d'%(channel,tx_count))
    for i in range(len(rx)) :
        fh.write(' %d'%(rx_count[i]))
        ps += ' %.1f'%(100-100*rx_count[i]/tx_count)
    fh.write('\n')
    print(ps)
    
def sweep_channel(fh, tx, rx) :
    global parameters
    for channel in range(parameters['lower-channel'],1+parameters['upper-channel']) :
        measure(fh, tx, rx, channel)

filename = parameters['out-filename']
subs = filename.count('%') - 2*filename.count('%%')
if subs > 1 : raise RuntimeError("out-filename may have no more than 1 %d replacement")
elif 0 == subs and parameters['iterations'] > 1 :
    filename = filename.replace('.','-%d.')
    subs = 1

for index in range(parameters['iterations']) :
    if subs : fh = open(filename%(1+index),'w')
    else : fh = open(filename,'w')
    sweep_channel(fh,tx,rx)
    fh.close()

tx.close()
for r in rx :
    r.close()
