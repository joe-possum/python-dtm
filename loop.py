import serial
import sys
import time

cmdtx = b'\x20\x04\x0e\x00\x00\xff\x00\x01'
cmdrx = b'\x20\x02\x0e\x01\x00\x01'
cmdend = b'\x20\x00\x0e\x02'
verbose = 0

def render(b) :
    s = ''
    for i in range(len(b)) :
        s += "%02x"%b[i]
    return s

def wait(s) :
    global verbose
    if verbose : print("waiting for event")
    h = s.read(4)
    if verbose : print("header: %s"%(render(h)))
    if 0xa0 != h[0] :
        print("Bad response")
        quit()
    l = h[1]
    if verbose : print("reading data")
    d = s.read(l)
    if verbose : print("data: %s"%(render(d)))
    return h + d

def send(s,cmd) :
    global verbose
    l = len(cmd) - 4
    if l != cmd[1] :
        print("bad command %s"%(render(cmd)))
    if verbose : print("sending %s"%(render(cmd)))
    s.write(cmd)
    if verbose : print("reading response")
    done = 0
    while not done :
        h = s.read(4)
        if verbose : print("header: %s"%(render(h)))
        if 0xa0 == h[0] :
            print("Unexpected event")
        if 0x20 == h[0] :
            done = 1
        l = h[1]
        if verbose : print("reading data")
        d = s.read(l)
        if verbose : print("data: %s"%(render(d)))
    return h + d
        
tx = serial.Serial(sys.argv[1],baudrate=115200)
rx = serial.Serial(sys.argv[2],baudrate=115200)
channel = 0
if len(sys.argv) > 3 :
    channel = int(sys.argv[3])

if verbose : print("tx:",tx)
if verbose : print("rx:",rx)

b = tx.read_all()
if len(b) :
    print("read %d bytes from tx: %s"%(len(b),render(b)))

b = rx.read_all()
if len(b) :
    print("read %d bytes from rx: %s"%(len(b),render(b)))
    
fh = open('viterbi.data','w')

for channel in range(40) :
    
    cmdtx = cmdtx[:6] + chr(channel).encode() + cmdtx[7:] 
    cmdrx = cmdrx[:4] + chr(channel).encode() + cmdrx[5:]

    send(tx,cmdtx)
    wait(tx)
    send(rx,cmdrx)
    wait(rx)
    
    if verbose : print("sleeping")
    time.sleep(120)
    
    send(tx,cmdend)
    evt = wait(tx)
    tx_count = evt[6] + (evt[7] << 8)
    
    send(rx,cmdend)
    evt = wait(rx)
    rx_count = evt[6] + (evt[7] << 8)
        
    print("channel: %d, sent: %d, received: %d, PER: %f"%(channel,tx_count,rx_count,100*(1-rx_count/tx_count)))
    
    fh.write('%d %d %d\n'%(channel,tx_count,rx_count))

tx.close()
rx.close()
fh.close()
