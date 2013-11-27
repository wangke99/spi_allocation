from pandas import DataFrame, Series
import pandas as pd

import warnings
import jaydebeapi, jpype

import os
import pickle
import json

import argparse
import math


import yaml
user_name = ''
dwh_password = ''
salesforce_password = ''
easydata_secret = ''

try:
    print '[INFO] loading login configurations ... '
    f = open('/home/kewang/config/config.yaml')
    config = yaml.safe_load(f)
    user_name = config['user_name']
    dwh_password = config['dwh_password']
    salesforce_password = config['salesforce_password']
    easydata_secret = config['easydata_secret']
    dwh_string = config['dwh_string']
    f.close()
    print '[INFO] load login configuration: SUCCESS ... '
except:
    print '[ERROR] unable to load configurations...'
    print '[ERROR] quit program now ...'
    quit()

parser = argparse.ArgumentParser(description="Get data from data warehouse and transform it to the format needed for optimization")

parser.add_argument('-m', '--max_scale', help='maximum scale for each bucket', required=False, default=0, type=int)
parser.add_argument('-t', '--data_table', help='the name of the data table, default to test table', required=False, default='dm_biz.ke_allocation_input_test', type=str)

args = parser.parse_args()

max_scale = args.max_scale
data_table = args.data_table

if max_scale == 0:
    print '[INFO] No additional optimization on model size'
elif max_scale >0 :
    print '[INFO] Max model scale at %s' % (str(max_scale))
else:
    print '[ERROR] Max model scale specified, %s, is not valid' % (str(max_scale))
    print '[ERROR] Quiting program. Please check and re-try.'
    quit()

def start_jvm():
    jdbcdrvpath = '/home/kewang/drivers/jdbc'
    jar = "%s/terajdbc4.jar:%s/tdgssconfig.jar" %(jdbcdrvpath, jdbcdrvpath)
    jargs= '-Djava.class.path=%s' % jar
    #jvm_path = jpype.getDefaultJVMPath()
    jpype.startJVM('/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/amd64/server/libjvm.so', jargs)

def dwh_query(query, col, user, password, dwh = dwh_string):
    dwh_link = "" % (dwh)
    cnx = jaydebeapi.connect("com.teradata.jdbc.TeraDriver",dwh_link,user,password)
    cursor = cnx.cursor()
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    data = {}
    for each in col:
        data[each]=[]

    for row in rows:
        for each in col:
            data[each].append(row[col.index(each)])
    data = DataFrame(data, columns=col)
    cursor.close()
    del cursor
    cnx.close()
    return data


start_jvm()

s = ['account_id', 'account_map', 'rep_id', 'rep_map', 'spi', 'sop', 'bucket']

sql = """
select *
from
(
select account_id , RANK() OVER  (partition by bucket, rep_id order by sop desc, ACCOUNT_ID) as account_map,  rep_id, rank () over ( partition by bucket, account_id order by rep_id) as rep_map,
spi, sop , bucket
from  %s
) a
order by bucket, rep_map, account_map ;
""" % (data_table)
print '[INFO] querying data from %s ...' % (data_table)

try:
    data = dwh_query(query=sql, col=s, user=user_name, password=dwh_password)
except Exception, e:
    print '[ERROR] Error pulling data from data warehouse'
    print '[ERROR] %s' % (str(e))
    quit()
    
print '[INFO] data pulled from dwh; processing ...'

if max_scale > 0:
    buckets = data['bucket'].unique()
    temp = {'account_id':[],'account_map':[], 'rep_id':[], 'rep_map':[], 'spi':[], 'sop':[], 'bucket':[]}
    temp = DataFrame(temp, columns = s)
    for each in buckets:
        # take each bucket
        d = data[data['bucket']==each]
        # number of unique companies
        c = len(d['account_id'].unique())
        # number of reps
        r = len(d['rep_id'].unique())
        if c*r<=max_scale:
            temp = pd.concat([temp, d], axis = 0)
        else:
            # at the max scale, the number of companies for each small bucket
            i = int(math.ceil(float(max_scale)/float(r)))
            # the number of buckets
            t = int(math.floor(float(c)/float(i)))
            #print c, r, i ,t
            # company index range
            t = [i * e for e in range(1,t+2)]
            t[-1] = int(c)+1
            #print t
            start = 0
            for e in t:
                sd =d[(d['account_map']<=e) & (d['account_map']>start)]
                sd['bucket']=sd['bucket'].map(lambda x: x+'_opt_key_'+str(int(e/i)))
                account_map = sd[['account_id']].drop_duplicates()
                account_map['account_index'] = range(1, len(account_map)+1)
                rep_map = sd[['rep_id']].drop_duplicates()
                rep_map['rep_index'] = range(1, len(rep_map)+1)
                sd = sd.merge(account_map, left_on=['account_id'], right_on = ['account_id'])
                sd = sd.merge(rep_map, left_on = ['rep_id'], right_on = ['rep_id'])
                sd['account_map'] = sd['account_index']
                sd['rep_map'] = sd['rep_index']
                sd = sd[['account_id', 'account_map', 'rep_id', 'rep_map','spi', 'sop', 'bucket']]
                start = e
                temp = pd.concat([temp, sd], axis = 0)
    #print temp
    #for each in temp.itertuples():
    #    print each
        #break
    #quit()
    data = temp
        
#for each in data.itertuples():
#    print each
#    break

#quit()

buckets = data['bucket'].unique()

print '[INFO] data loaded for the following buckets:'
print ', '.join(list(buckets))


for each in buckets:
    bucket = data[data['bucket']==each]
    accounts = len(bucket['account_id'].unique())
    reps = len(bucket['rep_id'].unique())
    account_map = bucket[['account_id', 'account_map']].drop_duplicates()
    #print account_map
    rep_map = bucket[['rep_id', 'rep_map']].drop_duplicates()
    #print rep_map
    
    account_map.to_csv('input/'+each+'_account_map.txt', sep='\t', index=False, header=False, encoding='utf-8')
    rep_map.to_csv('input/'+each+'_rep_map.txt', sep='\t', index=False, header=False, encoding='utf-8')

    with open('input/'+each+'_spi.json', 'w') as f:
        json.dump(list(bucket['spi']),f)

    with open('input/'+each+'_sop.json', 'w') as f:
        json.dump(list(bucket['sop'])[:accounts], f)

    with open('input/config.txt', 'a') as f:
	f.write(each+'\t'+str(accounts)+'\t'+str(reps)+'\t'+each+'_output.txt\n')
        #json.dump({'bucket': each, 'accounts': accounts, 'reps': reps, 'output': each+'output'}, f)

    print '[INFO] input data generated for bucket: %s' % (each)


