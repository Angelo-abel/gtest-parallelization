#!/usr/bin/env python

import argparse
import subprocess
import math
from multiprocessing import Pool, Lock

BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
WHITE  = "\033[0;37m"
RESET = "\033[0;0m"

global_lock = Lock()

def colorize(s):
    s = s.replace("[       OK ]", GREEN + "[       OK ]" + RESET) 
    s = s.replace("[ RUN      ]", GREEN + "[ RUN      ]" + RESET) 
    s = s.replace("[  PASSED  ]", GREEN + "[  PASSED  ]" + RESET) 
    s = s.replace("[==========]", GREEN + "[==========]" + RESET) 
    s = s.replace("[----------]", GREEN + "[----------]" + RESET) 
    s = s.replace("[  FAILED  ]", RED + "[  FAILED  ]" + RESET) 
    
    return s

def run_test(test_args, verbose):
    res = subprocess.Popen(test_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = res.communicate()

    out_text = out.decode('utf-8').split('\n')

    # This is the case when the test case dies early
    if len(out_text) < 8:

        global_lock.acquire()
        print(RED, '|==================================================|', RESET, sep='')
        print(RED, '|>>>FAILING TEST CASE DETECTED-- LIKELY SEGFAULT<<<|', RESET, sep='')
        print(RED, '|==================================================|', RESET, sep='')
        print(RED, '|>>>Printing out GTEST output followed by stderr<<<|', RESET, sep='')
        print(RED, '|==================================================|', RESET, sep='')
        print(YELLOW, '▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼', RESET, sep='')
        print(colorize(out.decode('utf-8').strip()))
        print(YELLOW, '▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲', RESET, sep='')
        print(YELLOW, '▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼', RESET, sep='')
        print(colorize(err.decode('utf-8').strip()))
        print(YELLOW, '▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲', RESET, sep='')
        global_lock.release()

        return out, err
    
    test_name = out_text[1][out_text[1].index('=') + 2:]
    if 'OK' in out_text[7]:
        if verbose: 
            global_lock.acquire()
            print(colorize(out.decode('utf-8').strip()))
            global_lock.release()

        return out, None
    else:
        global_lock.acquire()
        print(RED, '|==================================================|', RESET, sep='')
        print(RED, '|>>> FAILING TEST CASE DETECTED-- INVALID VALUE <<<|', RESET, sep='')
        print(RED, '|==================================================|', RESET, sep='')
        print(RED, '|>>>Printing out GTEST output followed by stderr<<<|', RESET, sep='')
        print(RED, '|==================================================|', RESET, sep='')
        print(YELLOW, '▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼', RESET, sep='')
        print(colorize(out.decode('utf-8').strip()))
        print(YELLOW, '▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲', RESET, sep='')
        print(YELLOW, '▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼', RESET, sep='')
        print(colorize(err.decode('utf-8').strip()))
        print(YELLOW, '▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲', RESET, sep='')
        global_lock.release()
        
        return out, err

def run_test_terse(test_args):
    run_test(test_args, False)

def run_test_verbose(test_args):
    run_test(test_args, True)

def parse_input():

    parser = argparse.ArgumentParser(description='Utility script for running GTEST binaries in parallel.')

    parser.add_argument('GTEST Binaries', type=argparse.FileType(), nargs='+', help='Give a space delimited list of relative filenames of the test-binaries to run.')
    parser.add_argument('-f','--gtest_filter', default='*', help='Filter to use to determine which unit tests to run')
    parser.add_argument('-a', '--gtest_args', default='', help='Pass in a string of other commandline arguments to be forwarded to the GTEST binary.')
    parser.add_argument('-c ', '--concurrency', type=int, default='1', help='How many concurrent unit tests to run')
    parser.add_argument('-v', '--verbose', action='store_true', help='Specify this flag if you want output for all arguments instead of just failing tests.')

    return parser.parse_args()

def main():
    arg_dict = vars(parse_input())
    gtest_filter = arg_dict['gtest_filter']
    concurrency = arg_dict['concurrency']
    gtest_args = arg_dict['gtest_args'].split(' ')
    verbose = arg_dict['verbose']

    test_names = {}
    for f in arg_dict['GTEST Binaries']:
        test_names[f.name] = []

        res = subprocess.run(['./' + f.name, '--gtest_filter=' + gtest_filter, '--gtest_list_tests'], stdout=subprocess.PIPE)
        res_listing = [test_name.strip() for test_name in res.stdout.decode('utf-8').split('\n')[1:-1]]

        current_test = ''
        for test_name in res_listing:
            if test_name[-1] == '.':
                current_test = test_name
            else:
                test_names[f.name].append(current_test + test_name)

    arg_lists = []
    for file_name in test_names:
        for test_name in test_names[file_name]:
            arg_lists.append(['./' + file_name, '--gtest_filter=' + test_name, *gtest_args])

    test_runner = run_test_verbose if verbose else run_test_terse

    with Pool(processes=concurrency) as pool:
        result = pool.map(test_runner, arg_lists)

    fails = 0
    print(result)
    for res in result:
        # We only return None in the second position in the tuple if the test passed.
        if res[1] != None:
            fails += 1

    total_cases = str(len(result))
    passing_cases = str(len(result) - fails)
    failing_cases = str(fails)

    output = YELLOW + '|>>> We ' + GREEN + 'passed ' + passing_cases + '/' + total_cases + YELLOW + ' test case(s), ' + RED + 'failing ' + failing_cases + YELLOW + ' test case(s)!<<<|' + RESET
    outer = '|' + ('=' * (len(output) - 2 - 6 * 6)) + '|'

    global_lock.acquire()
    print(outer)
    print(output)
    print(outer)
    global_lock.release()

if __name__ == '__main__':
    main()
