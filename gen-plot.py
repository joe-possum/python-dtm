import numpy as np

viterbi = np.zeros((5,40))
pstr = ''
for i in range(5) :
    fn = 'viterbi-%d.data' % (1+i)
    pstr += ','
    pstr += '"' + fn + '" using 1:(100*(1-$3/$2)) w d notitle'
    print("fn",fn)
    fh = open(fn,'r')
    while 1 :
        line = fh.readline()
        if None == line or 0 == len(line) : break
        tokens = line.split()
        if 3 != len(tokens) :
            raise RuntimeError("not 3 tokens")
        ch = int(tokens[0])
        tx = int(tokens[1])
        rx = int(tokens[2])
        print("ch,tx,rx:",ch,tx,rx,rx/(1.*tx))
        viterbi[i,ch] = 1-rx/(1.*tx)
    fh.close()

mean = viterbi.mean(axis=0)
std = viterbi.std(axis=0)
print(100*mean,100*std)

fh = open('stats.data','w')
for i in range(40) :
    fh.write("%d %f %f\n"%(i,100*mean[i],100*std[i]))
fh.close()

fh = open('viterbi.gnu','w')
fh.write('set xlabel "channel"\n')
fh.write('set ylabel "PER (percent)"\n')
fh.write('plot [-1:40][0:*] "stats.data" with error title "Errorbar: +/- 1 std dev (5 runs)"' + pstr + '\n')
fh.close()
