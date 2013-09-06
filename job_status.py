from pandas import DataFrame, Series
import pandas as pd

try:
    d = pd.read_csv('output/config.txt', header=None, sep='\t')
except:
    print '[INFO] No optimization job is finished yet or no job is running.'
    quit()

d.columns = ['input', 'status', 'spi']

d = d.drop_duplicates()

d['bucket'] = d['input'].map(lambda x: x.replace('input/','').replace('_spi.json',''))

success = d[d['status'] == 1]
failed = d[d['status'] == 0]

finished = len(d)

print '[INFO] %s buckets have finished optimizing' % (str(finished))

if len(success)>0:
    print '---------------------------------'
    print 'Successful optimizations'
    print '---------------------------------'
    for each in success.itertuples():
        bucket = each[4]
        spi = each[3]
        print '[INFO] Bucket: %s finished successfully with spi value at %s' % (str(bucket), str(spi))

if len(failed)>0:
    print '---------------------------------'
    print 'Failed optimizations'
    print '---------------------------------'
    for each in failed.itertuples():
        bucket = each[4]
        spi = each[3]
        print '[INFO] Bucket: %s failed' % (str(bucket))
    
