# 7/9/2020
import serial
import sys
import time

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
if verbose : print("tx:",tx)
b = tx.read_all()
if len(b) :
    print("read %d bytes from tx: %s"%(len(b),render(b)))

rx = []
for cp in sys.argv[2:] :
    r = serial.Serial(cp,baudrate=115200)
    rx.append(r)
    b = r.read_all()
    if len(b) :
        print("read %d bytes from rx: %s"%(len(b),render(b)))
if verbose : print("rx:",rx)

def measure(fh, tx, rx, channel) :
    cmdtx = b'\x20\x04\x0e\x00\x00\xff\x00\x01'
    cmdrx = b'\x20\x02\x0e\x01\x00\x01'
    cmdend = b'\x20\x00\x0e\x02'
    cmdtx = cmdtx[:6] + chr(channel).encode() + cmdtx[7:] 
    cmdrx = cmdrx[:4] + chr(channel).encode() + cmdrx[5:]

    rx_count = []
    for r in rx :
        send(r,cmdrx)
        wait(r)
    
    send(tx,cmdtx)
    wait(tx)

    if verbose : print("sleeping")
    time.sleep(1)
    
    send(tx,cmdend)
    evt = wait(tx)
    tx_count = evt[6] + (evt[7] << 8)
    
    for i in range(len(rx)) :
        send(rx[i],cmdend)
        evt = wait(rx[i])
        rx_count.append(evt[6] + (evt[7] << 8))
        
    ps = "channel: %d, sent: %d, PER:"%(channel,tx_count)
    
    fh.write('%d %d'%(channel,tx_count))
    for i in range(len(rx)) :
        fh.write(' %d'%(rx_count[i]))
        ps += ' %.1f'%(100-100*rx_count[i]/tx_count)
    fh.write('\n')
    print(ps)
    
def sweep_channel(fh, tx, rx) :
    for channel in range(40) :
        measure(fh, tx, rx, channel)

for index in range(1,41) :
    fh = open('2v13p6-4303a-4104a-%d.data'%(index),'w')
    sweep_channel(fh,tx,rx)
    fh.close()

tx.close()
for r in rx :
    r.close()

