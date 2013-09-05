from pandas import DataFrame, Series
import pandas as pd

import warnings
import jaydebeapi, jpype

import os
import pickle
import json

import yaml
user_name = ''
dwh_password = ''
salesforce_password = ''
easydata_secret = ''

try:
    print 'loading configurations ... '
    f = open('/home/kewang/config/config.yaml')
    config = yaml.safe_load(f)
    user_name = config['user_name']
    dwh_password = config['dwh_password']
    salesforce_password = config['salesforce_password']
    easydata_secret = config['easydata_secret']
    dwh_string = config['dwh_string']
    f.close()
    print 'SUCCESS ... '
except:
    print 'unable to load configurations...'
    print 'quit program now ...'



def start_jvm():
    jdbcdrvpath = '/home/kewang/drivers/jdbc'
    jar = "%s/terajdbc4.jar:%s/tdgssconfig.jar" %(jdbcdrvpath, jdbcdrvpath)
    jargs= '-Djava.class.path=%s' % jar
    #jvm_path = jpype.getDefaultJVMPath()
    jpype.startJVM('/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/amd64/server/libjvm.so', jargs)

def dwh_query(query, col, user, password, dwh = dwh_string):
    dwh_link = "jdbc:teradata://%s.corp.linkedin.com/DBS_PORT=1025,DATABASE=DWH,LOGMECH=LDAP" % (dwh)
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
select account_id , RANK() OVER  (partition by bucket, rep_id order by ACCOUNT_ID) as account_map,  rep_id, rank () over ( partition by bucket, account_id order by rep_id) as rep_map,
spi, sop , bucket
from  dm_biz .ke_allocation_input_test
) a
order by bucket, rep_map, account_map ;
"""
print 'querying dwh...'
data = dwh_query(query=sql, col=s, user=user_name, password=dwh_password)

print 'data pulled from dwh; processing ...'

buckets = data['bucket'].unique()

print 'data loaded for the following buckets:'
print ', '.join(list(buckets))



for each in buckets:
    bucket = data[data['bucket']==each]
    accounts = len(bucket['account_id'].unique())
    reps = len(bucket['rep_id'].unique())
    account_map = bucket[['account_id', 'account_map']].drop_duplicates()
    rep_map = bucket[['rep_id', 'rep_map']].drop_duplicates()

    account_map.to_csv('input/'+each+'_account_map.txt', sep='\t', index=False, header=False, encoding='utf-8')
    rep_map.to_csv('input/'+each+'_rep_map.txt', sep='\t', index=False, header=False, encoding='utf-8')

    with open('input/'+each+'_spi.json', 'w') as f:
        json.dump(list(bucket['spi']),f)

    with open('input/'+each+'_sop.json', 'w') as f:
        json.dump(list(bucket['sop'])[:accounts], f)

    with open('input/config.txt', 'a') as f:
	f.write(each+'\t'+str(accounts)+'\t'+str(reps)+'\t'+each+'_output.txt\n')
        #json.dump({'bucket': each, 'accounts': accounts, 'reps': reps, 'output': each+'output'}, f)

    print 'input data generated for bucket: %s' % (each)


