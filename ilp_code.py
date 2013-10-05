from cvxopt import matrix
import cvxopt.glpk as glpk
import numpy as np
import json
import argparse
from pandas import DataFrame
import pandas as pd
import math

parser = argparse.ArgumentParser(description="account assignment based on SPI maximization")

parser.add_argument('-c','--company', help="number of companies", required=True, type=int)
parser.add_argument('-r', '--reps', help="number of reps", required=True, type=int)
parser.add_argument('-f', '--spi', help="spi data file", required=True, type=str)
parser.add_argument('-s', '--sop', help="sop data file", required=True, type=str)
parser.add_argument('-t', '--time', help="max running time", required=False, default=1000, type=int)
parser.add_argument('-o', '--outfile', help="output file name", required=False, default='output.csv', type=str)
args = parser.parse_args()


number_of_company = args.company
number_of_reps = args.reps
spi_file = args.spi
sop_file = args.sop
max_time = args.time
outfile = args.outfile

print '[INFO] number of companis: ' + str(number_of_company)
print '[INFO] number of reps: ' + str(number_of_reps)
print '[INFO] location of spi data file: '+ spi_file
print '[INFO] location of sop data file: '+ sop_file
print '[INFO] the process will run for at most %s seconds' % (str(max_time))

c = matrix(json.load(open(spi_file)))
c = 0-c
#print c
print '[INFO] %s records loaded from spi file' % (str(len(c)))

if len(c) != number_of_reps*number_of_company:
    print '[ERROR] expecting number of companies and number of reps to satisfy c*r = %s' % (str(len(c)))
    quit()

print '[INFO] SUCCESS: spi data loaded'

s = json.load(open(sop_file))
print '[INFO] %s records loaded from SOP file' % (str(len(s)))

if len(s) != number_of_company:
    print '[ERROR] length of SOP data is not the same as number of company'
    quit()

print '[INFO] SUCCESS: SOP data loaded'

#-------------------------------------------------------------------------

#quit()
I = np.eye(number_of_company)
for i in range(number_of_reps-1):
    #print i
    I = np.concatenate((I, np.eye(number_of_company)), axis = 1)

A = matrix(I)

#print A

b = matrix(np.ones(number_of_company))

#print b

#print matrix(np.transpose(np.ones(3)))

#constraints

Z = np.zeros((number_of_reps, number_of_company), dtype=np.float)


#--------number of accounts--------------------
I = Z.copy()
I[0,] = np.ones((1, number_of_company), dtype=np.float)

for i in range(1,number_of_reps):
    #print i
    K = Z.copy()
    #print K
    K[i,] = np.ones((1,number_of_company), dtype=np.float)
    #print matrix(K)
    I = np.concatenate((I, K), axis = 1)

I = np.concatenate((I, -I), axis = 0)

ones = np.ones(number_of_reps)
ca = ones.copy()
ca = ca * math.ceil(number_of_company/number_of_reps*1.1)

cal = ones.copy()
cal = cal * (-1) * math.ceil(number_of_company/number_of_reps*0.9)
constraint_account_no = np.concatenate((ca, cal), axis =0)
constraint = constraint_account_no
#constraint_account_no =  matrix(constraint_account_no)
#print matrix(I)

#quit()

IS = Z.copy()
IS[0,] = s

for i in range(1, number_of_reps):
    K = Z.copy()
    K[i,] =s
    IS = np.concatenate((IS,K), axis = 1)

IS = np.concatenate((IS, -IS), axis = 0)

cs = ones.copy()
cs = cs*(np.sum(s)/number_of_reps*1.5)

csl = ones.copy()
csl = csl * ( - np.sum(s)/number_of_reps*0.5)
constraint_sop = np.concatenate((cs, csl), axis = 0)

#print IS
#print constraint_sop

#I = np.concatenate((I, IS), axis = 0)
#constraint = np.concatenate((constraint_account_no, constraint_sop), axis = 0)

#print I
#print constraint
#quit()



#------------------------------------------
G = matrix(I)
h = matrix(constraint)

#print h
#quit()
#G = matrix(json.load(open('G_constraints_left.json')))
#print G
#standard is left less or equal to right
#G = matrix([[-1.0, -1.0, 0.0, 1.0], [1.0, -1.0, -1.0, -2.0]])

#h = matrix(json.load(open('h_constraints_right.json')))
#print h
#h = matrix([1.0, -2.0, 0.0, 4.0])
#print glpk.options
#glpk.options['LPX_K_MIPGAP'] = '1.0'
#glpk.options['LPX_K_MIP_GAP'] = 1.0
#glpk.options['LPX_K_GMI_CUTS'] = 'GLP_ON'
#glpk.options['LPX_K_TOLOBJ'] = 0.007
glpk.options['LPX_K_TMLIM'] = max_time
#glpk.options['LPX_K_PRESOL']= 1
#print glpk.options
#quit()
status, result = glpk.ilp(c = c, G=G, h=h, A = A, b = b, B= set(range(0,len(c))))

final_spi = -int(np.sum(np.multiply(np.array(result), np.array(c))))
print '[INFO] final optimal spi value is %s' % (str(final_spi))

with open('output/config.txt','a') as f:
    if final_spi > 0:
	f.write(spi_file+'\t1\t'+str(final_spi)+'\n')
    else:
	f.write(spi_file+'\t0\t'+str(final_spi)+'\n')

#print result
result = np.array(result, np.int)
result = np.reshape(result, (number_of_company, number_of_reps), 'F')


allocation = {'account_id':[], 'reps_id':[]}

i = 0
for each in result:
    for j in range(number_of_reps):
        if each[j] == 1:
            allocation['account_id'].append(i+1)
            allocation['reps_id'].append(j+1)
    i = i+1

allocation = DataFrame(allocation, columns=['account_id', 'reps_id'])

print '[INFO] generate results in file'
allocation.to_csv(outfile, sep=',', header=False, index=False)
#f = open('output.csv','w')
#f.write(str(result))
#f.close()

