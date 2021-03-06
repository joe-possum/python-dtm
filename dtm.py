import serial
import sys
import time

cmdtx = b'\x20\x04\x0e\x00\x00\xff\x00\x01'
cmdrx = b'\x20\x02\x0e\x01\x00\x01'
cmdend = b'\x20\x00\x0e\x02'

def render(b) :
    s = ''
    for i in range(len(b)) :
        s += "%02x"%b[i]
    return s

def wait(s) :
    #print("waiting for event")
    h = s.read(4)
    #print("header: %s"%(render(h)))
    if 0xa0 != h[0] :
        print("Bad response")
        quit()
    l = h[1]
    #print("reading data")
    d = s.read(l)
    #print("data: %s"%(render(d)))
    return h + d

def send(s,cmd) :
    l = len(cmd) - 4
    if l != cmd[1] :
        print("bad command %s"%(render(cmd)))
    #print("sending %s"%(render(cmd)))
    s.write(cmd)
    #print("reading response")
    done = 0
    while not done :
        h = s.read(4)
        #print("header: %s"%(render(h)))
        if 0xa0 == h[0] :
            print("Unexpected event")
        if 0x20 == h[0] :
            done = 1
        l = h[1]
        #print("reading data")
        d = s.read(l)
        #print("data: %s"%(render(d)))
    return h + d
        
tx = serial.Serial(sys.argv[1],baudrate=115200)
rx = serial.Serial(sys.argv[2],baudrate=115200)
channel = 0
if len(sys.argv) > 3 :
    channel = int(sys.argv[3])

cmdtx = cmdtx[:6] + chr(channel).encode() + cmdtx[7:] 
cmdrx = cmdrx[:4] + chr(channel).encode() + cmdrx[5:]

#print("tx:",tx)
#print("rx:",rx)

b = tx.read_all()
if len(b) :
    print("read %d bytes from tx: %s"%(len(b),render(b)))
b = rx.read_all()
if len(b) :
    print("read %d bytes from rx: %s"%(len(b),render(b)))
    
send(tx,cmdtx)
wait(tx)
send(rx,cmdrx)
wait(rx)

#print("sleeping")
time.sleep(90)

send(tx,cmdend)
evt = wait(tx)
tx_count = evt[6] + (evt[7] << 8)

send(rx,cmdend)
evt = wait(rx)
rx_count = evt[6] + (evt[7] << 8)

tx.close()
rx.close()

print("channel: %d, sent: %d, received: %d, PER: %f"%(channel,tx_count,rx_count,100*(1-rx_count/tx_count)))
