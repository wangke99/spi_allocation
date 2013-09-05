from pandas import DataFrame, Series
import pandas as pd
import math
import os


def scale_mapping(i):
    i = int(i)
    if i <= 15000:
        return 100
    elif i <= 30000:
        return 400
    elif i <=90000:
        return 1000
    else:
        return 86401

config = pd.read_csv('input/config.txt', header=None, sep='\t')
config.columns = ['bucket', 'accounts', 'reps', 'output']

config['scale'] = config['accounts']*config['reps']
config['time'] = config['scale'].apply(scale_mapping)

max_time = float(max(config['time']))
days = int(math.floor(max_time/(24.0*60.0*60.0)))
hours = int(math.floor((max_time - float(days*24*60*60))/(60.0*60.0)))
minutes = int(math.ceil((max_time - days * 24*60*60 - hours * 60*60)/60))


print '[INFO] Number of optimization processes to run: %s' % (str(len(config)))
print '[INFO] The process will take about %s days %s hours %s minutes to finish' %(days, hours, minutes)

os.system('which python')

for each in config.itertuples():
    bucket = each[1]
    accounts = str(int(each[2]))
    reps = str(int(each[3]))
    spi = 'input/'+bucket+'_spi.json'
    sop = 'input/'+bucket+'_sop.json'
    output = 'output/'+each[4]
    time = str(each[6])
    log = 'model_log/'+bucket+'_log.txt'

    command_string = 'python ilp_code.py -c %s -r %s -f %s -s %s -t %s -o %s > %s &' % (accounts, reps, spi, sop, time, output, log )
    print '[INFO] Start optimizing bucket %s' % (bucket)
    print '[INFO] Full command: %s ' % (command_string)
    print '[INFO] Algorithm log will be generated at %s' % (log)
    os.system(command_string)
    
    
