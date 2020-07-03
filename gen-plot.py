import numpy as np
import getopt
import sys

def help_quit(arg) :
    print(msg_help)
    quit()

def set_gnuplot_file(arg) :
    global parameters
    parameters['gnuplot-file'] = arg
    
def set_stats_file(arg) :
    global parameters
    parameters['stats-file'] = arg

def set_legend(arg) :
    global parameters
    parameters['stats-file'] = arg

msg_help = 'Usage: gen-plot [ -h ] [ -g gnuplot-file ] [ -s stats-file ] [ -l legend ] datafile [ datafile [ ... ] ]'
parameters = {
    'gnuplot-name':'viterbi.gnu',
    'stats-name':'stats.data',
    'legend':'Errorbar: +/- 1 std dev (5 runs)',
    'option-string':'hg:s:l:'
}

option_bindings = {
    '-h' : help_quit,
    '-g' : set_gnuplot_file,
    '-s' : set_stats_file,
    '-l' : set_legend
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

options_sanity_check()

options,filenames = getopt.getopt(sys.argv[1:],parameters['option-string'])
for option in options :
    fn = option_bindings.get(option[0])
    fn(option[1])

file_count = len(filenames)
data = np.zeros((file_count,40))
pstr = ''
for i in range(file_count) :
    fn = filenames[i]
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
        data[i,ch] = 1-rx/(1.*tx)
    fh.close()

mean = data.mean(axis=0)
std = data.std(axis=0)
print(100*mean,100*std)

fh = open(parameters['stats-file'],'w')
for i in range(40) :
    fh.write("%d %f %f\n"%(i,100*mean[i],100*std[i]))
fh.close()

fh = open(parameters['gnuplot-file'],'w')
fh.write('set xlabel "channel"\n')
fh.write('set ylabel "PER (percent)"\n')
fh.write('plot [-1:40][0:*] "%s" with error title "%s"'%(parameters['stats-file'],parameters['legend']) + pstr + '\n')
fh.close()
