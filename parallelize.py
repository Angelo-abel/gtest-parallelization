#!/usr/bin/env python

import argparse
import subprocess
import math
from multiprocessing import Pool, Lock

global_lock = Lock()

def run_test(test_args):
    res = subprocess.Popen(test_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = res.communicate()

    out_text = out.decode('utf-8').strip().split('\n')

    # This is the case when the test case dies early
    if len(out_text) < 8:

        global_lock.acquire()
        print('|==================================================|')
        print('|>>>FAILING TEST CASE DETECTED-- LIKELY SEGFAULT<<<|')
        print('|==================================================|')
        print('|>>>Printing out GTEST output followed by stderr<<<|')
        print('|==================================================|')
        print(out.decode('utf-8').strip())
        print('\n▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲')
        print('▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼\n')
        print(err.decode('utf-8').strip())
        print('\n▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲\n')
        global_lock.release()

        return out, err
    
    test_name = out_text[1][27:]
    if out_text[7].startswith('[       OK ]'):
        return out, None
    else:
        global_lock.acquire()
        print('|==================================================|')
        print('|>>> FAILING TEST CASE DETECTED-- INVALID VALUE <<<|')
        print('|==================================================|')
        print('|>>>Printing out GTEST output followed by stderr<<<|')
        print('|==================================================|')
        print(out.decode('utf-8').strip())
        print('\n▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲')
        print('▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼\n')
        print(err.decode('utf-8').strip())
        print('\n▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲\n')
        global_lock.release()
        
        return out, err

parser = argparse.ArgumentParser(description='Utility script for running GTEST binaries in parallel.')

parser.add_argument('--concurrency', default='1', type=int)
parser.add_argument('--gtest_binary', required=True, metavar='GTEST Binary Name')
parser.add_argument('--gtest_filter', metavar='GTEST Regex Filter')
parser.add_argument('--gtest_args', metavar='GTEST Test Arguments')

args = parser.parse_args()
arg_dict = vars(args)

# run command to fetch stdout
res = subprocess.run(['./' + arg_dict['gtest_binary'], '--gtest_filter=' + arg_dict['gtest_filter'],  '--gtest_list_tests'], stdout=subprocess.PIPE)

gtest_listing_string = res.stdout.decode('utf-8')

gtest_listings = gtest_listing_string.split('\n')[1:-1]
tests = []

currentTest = ''
for test in gtest_listings:
    test = test.strip()
    if test[-1] == '.':
        currentTest = test
    else:
        tests.append(currentTest + test)

concurrency = min(len(tests), arg_dict['concurrency'])

arg_lists = []
for i in range(len(tests)):
    arg_lists.append(['./' + arg_dict['gtest_binary'], '--gtest_filter=' + tests[i], *arg_dict['gtest_args'].split(' ')])

pool = Pool(processes=concurrency)
result = pool.map(run_test, arg_lists)

fails = 0
for res in result:
    if res[1] != None:
        fails += 1

output = '|>>>We ran ' + str(len(result)) + ' test cases, passing ' + str(len(result) - fails) + ' test case(s) and failing ' + str(fails) + ' test case(s)!<<<|'
outer = '|' + ('=' * (len(output) - 2)) + '|'

global_lock.acquire()
print(outer)
print(output)
print(outer)
global_lock.release()
