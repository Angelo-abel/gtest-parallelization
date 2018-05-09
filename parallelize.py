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
    segfault_text = 'FAILING TEST CASE DETECTED: POSSIBLE SEGFAULT!'
    invalid_text = 'FAILING TEST CASE DETECTED: INVALID VALUE!'
    output_text = 'Printing out stdout followed by stderr'

    segfault_spaces = ' ' * int((len(segfault_text) - len(output_text)) / 2)
    invalid_spaces = ' ' * int((len(invalid_text) - len(output_text)) / 2)

    arrow_count = 50

    res = subprocess.Popen(test_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = res.communicate()

    out_text = out.decode('utf-8').strip().split('\n')

    # This is the case when the test case dies early
    if '[ RUN      ]' in out_text[-1]:
        global_lock.acquire()
        print(RED, '|====' + ('=' * len(segfault_text)) + '====|', RESET, sep='')
        print(RED, '|>>> ' + segfault_text + ' <<<|', RESET, sep='')
        print(RED, '|>>> ' + segfault_spaces + output_text + segfault_spaces + ' <<<|', RESET, sep='')
        print(RED, '|====' + ('=' * len(segfault_text)) + '====|', RESET, sep='')
        print(YELLOW, '▼' * arrow_count, RESET, sep='')
        print(colorize(out.decode('utf-8').strip()))
        print(YELLOW, '▲' * arrow_count, RESET, sep='')
        print(YELLOW, '▼' * arrow_count, RESET, sep='')
        print(colorize(err.decode('utf-8').strip()))
        print(YELLOW, '▲' * arrow_count, RESET, sep='')
        global_lock.release()

        return out, err
    
    if True in ['[       OK ]' in line for line in out_text]:
        if verbose: 
            global_lock.acquire()
            print(colorize(out.decode('utf-8').strip()))
            global_lock.release()

        return out, None
        
    global_lock.acquire()
    print(RED, '|====' + ('=' * len(invalid_text)) + '====|', RESET, sep='')
    print(RED, '|>>> ' + invalid_text + ' <<<|', RESET, sep='')
    print(RED, '|>>> ' + invalid_spaces + output_text + invalid_spaces + ' <<<|', RESET, sep='')
    print(RED, '|====' + '=' * len(invalid_text) + '====|', RESET, sep='')
    print(YELLOW, '▼' * arrow_count, RESET, sep='')
    print(colorize(out.decode('utf-8').strip()))
    print(YELLOW, '▼' * arrow_count, RESET, sep='')
    print(colorize(err.decode('utf-8').strip()))        
    print(YELLOW, '▲' * arrow_count, RESET, sep='')
    global_lock.release()
    
    return out, err

def run_test_terse(test_args):
    return run_test(test_args, False)

def run_test_verbose(test_args):
    return run_test(test_args, True)

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
    for res in result:
        # We only return None in the second position in the tuple if the test passed.
        if res[1] != None:
            fails += 1

    total_cases = str(len(result))
    passing_cases = str(len(result) - fails)
    failing_cases = str(fails)

    output = YELLOW + '|>>> Out of ' + total_cases + ' case(s), ' + GREEN + passing_cases + ' passed' + YELLOW + ' and ' + RED + failing_cases + ' failed' + YELLOW + '! <<<|' + RESET
    output_len = len(output) - len(YELLOW) * 3 - len(GREEN) - len(RED) - len(RESET)
    outer = YELLOW + '|' + ('=' * (output_len - 2)) + '|' + RESET

    global_lock.acquire()
    print(outer)
    print(output)
    print(outer)
    global_lock.release()

if __name__ == '__main__':
    main()
