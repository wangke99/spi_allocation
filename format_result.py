from pandas import DataFrame, SeriesAOAOA
import pandas as pd

config = pd.read_csv('output/config.txt', header=None, sep='\t')
config.columns = ['spi_file', 'status', 'spi']

unfinished = config[config['status'] == 0]

config = config[config['status'] == 1]
config['bucket'] = config['spi_file'].map(lambda x: x.replace('input/','').replace('_spi.json',''))
config['output'] = config['bucket'].map(lambda x: 'output/'+x+'_output.txt')
config['account_mapper'] = config['bucket'].map(lambda x: 'input/'+x+'_account_map.txt')
config['rep_mapper'] = config['bucket'].map(lambda x: 'input/'+x+'_rep_map.txt')
config['output_file'] = config['bucket'].map(lambda x: 'final_output/'+x+'_final_output.txt')


config = config[['bucket', 'output', 'account_mapper', 'rep_mapper', 'output_file']]


#print config

for each in config.itertuples():
    bucket = each[1]
    output = each[2]
    account_mapper = each[3]
    rep_mapper = each[4]
    output_file = each[5]

    #print output
    
    d = pd.read_csv(output, header=None, sep=',')
    d.columns=['account_index','rep_index']
    a = pd.read_csv(account_mapper, header=None, sep='\t')
    a.columns=['account', 'account_index']
    r = pd.read_csv(rep_mapper, header=None, sep='\t')
    r.columns=['rep', 'rep_index']

    output_data = d.merge(a, left_on = ['account_index'], right_on = ['account_index'])
    output_data = output_data.merge(r, left_on=['rep_index'], right_on = ['rep_index'])
    output_data = output_data[['account', 'rep']]
    
    print '[INFO] Wrting allocation plan for bucket: %s' % (bucket)
    print '[INFO] %s - %s accounts are allocated' % (bucket, str(len(output_data)))
    output_data.to_csv(output_file, header=None, sep=',', index=False)


print '[INFO] Updating output config file at output/config.txt'
print '[INFO] %s buckets remaining' % (len(unfinished))
unfinished.to_csv('output/config.txt', header=None, sep='\t', index=False)