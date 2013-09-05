from pandas import DataFrame, Series
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


print config

