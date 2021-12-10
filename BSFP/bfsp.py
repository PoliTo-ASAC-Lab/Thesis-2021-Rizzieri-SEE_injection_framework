#!/usr/bin/env python3

import os
from os import path
import random
import sys
import subprocess
import time
import shlex

import bfsp_utils
import bfsp_report_zipper
import crash_doctor

from bitman import bitflip
from bitman_MEU import bitflip_MEU

from crc32 import CRC32_hash

########## SETTING VARIABLES ##########

#./fft 4 8192 -i
c_prog_name = "fft"
c_prog_args = "4 8192 -i" #c_prog arguments as string, divided by " "

timeout = 5 # after this execution time the process is considered hanging
            # WARNING: if too low will cause test overkilling
cluster_size = 200 # how many processes will run "at a time"
uP_cool_down_time = 3 # how many seconds between a cluster and the other, to cool down uP
########## END SETTING VARIABLES ##########

########## PARAMETER PARSING ##########
def exit_usage():
    usage = "\nUsage: python3 bfsp.py -n <N> -m <1/2/3> [options]"
    usage += "\n   required:"
    usage += "\n\t-n <N>,\t\tN = number of injections"
    usage += "\n\t-m <1/2/3>\t\tMode selection: 1-SEU, 2-MBU, 3-ClearContent"
    usage += "\n   options:"
    usage += "\n\t-s r_seed,\tSet the random seed to r_seed"
    usage += "\n\t-v, --verbose,\tTo produce verbose output report "
    usage += "\n\t-c, --clean,\tto clean the bitflipped binaries folder and exit"
    usage += "\n\t-z, --zip,\tTo compact all the reports in ./exec_reports/ in a summary\n"
    sys.exit(usage) 

if "-h" in sys.argv or "--help" in sys.argv:
    exit_usage()


if(len(sys.argv) < 3):
    exit_usage()
else:
    #Injection Number setting (REQUIRED)
    if "-n" in sys.argv:
        param_n_index = sys.argv.index("-n")+1
        param_n = sys.argv[param_n_index]
        if (param_n.isnumeric() and int(param_n) > 0 and int(param_n) < 20000):
            injection_num = int(param_n)
        else:
            sys.exit("Invalid number of injections! (0-20000")
    else:
        exit_usage()

    #Mode Selection (REQUIRED)
    if "-m" in sys.argv:
        param_mode_index = sys.argv.index("-m")+1
        param_mode = sys.argv[param_mode_index]
        if (param_mode.isnumeric() and int(param_mode) > 0 and int(param_mode) < 4):
            selected_mode = int(param_mode)
        else:
            sys.exit("Invalid mode! (1-SEU, 2-MBU, 3-ClearContent)")
    else:
        exit_usage()

    # Random Seed setting
    r_seed = int(time.time())
    if "-s" in sys.argv:
        param_seed_index = sys.argv.index("-s")+1
        param_seed = sys.argv[param_seed_index]
        if (param_seed.isnumeric() and int(param_seed) > 0):
            r_seed = int(param_seed)
        else:
            sys.exit("Invalid random seed!")

    # Verbosity setting
    verbose_report = False
    if "-v" in sys.argv or "--verbose" in sys.argv:
        verbose_report = True
    
    # Clean mode
    if "-c" in sys.argv or "--clean" in sys.argv:
        bfsp_utils.clear_faulty_directory()
        sys.exit()

    # Report zipping mode
    if "-z" in sys.argv or "--zip" in sys.argv:
        bfsp_report_zipper.report_zipper()
        sys.exit()

########## END PARAMETER PARSING ##########



if __name__ == '__main__':

    print('\n\n\t**** BFSP v1.05: Bitflip Fault Simulation Platform by Daniele Rizzieri ***\n\n\n')
    test_start_time = int(time.time())

    ########## Clearing the faulty binaries folder ##########
    """
    Deletion of all the bitflipped binaries in ./bitflipped_binaries/ and previous results file
    If the faulty binaries folder doesn't exists, it is created
    If the reports folder doesn't exists, it is created
    """
    bfsp_utils.clear_faulty_directory()


    ########## Bitflip Injection ##########
    """
    Starting from the golden binary (fault free) many copies are made, each of them with a flipped bit
    NOTE: {injection num} bitflipped copies are made and stored in ./bitflipped_binaries/
    """
    random.seed(r_seed)
    
    if selected_mode == 1:
        bfsp_utils.bitflip_injection_SEU(c_prog_name, injection_num)
    elif selected_mode == 2:
        bfsp_utils.bitflip_injection_MBU(c_prog_name, injection_num)
    elif selected_mode == 3:
        bfsp_utils.bitflip_injection_CLEAR(c_prog_name, injection_num)



    ########## Executing the golden binary ##########
    """
    The golden binary (fault free) is executed
    This is done to retrieve the golden result file
    """
    # Executable check
    if not path.exists(f"./run/{c_prog_name}"):
        sys.exit("Binary executable file MISSING in ./run/ !")

    print("3) Executing the golden binary...",end="\r")
    golden_res_filename = f"./run/results_GOLDEN_{c_prog_name}.dat"
    
    command = f"./run/{c_prog_name} {c_prog_args}"
    command_l = shlex.split(command)
    process_global = subprocess.Popen(command_l, stdout=open(golden_res_filename,"w"))
    process_global.wait()
    print("3) Executing the golden binary...OK")



    ########## Fault simulation of binaries ##########
    """
    Executes faulty binaries one cluster at a time 
    -> (size of clusters tunable via "cluster_size") 
    Between a cluster and the next one lets the uP cool down for t seconds 
    -> (cool down time tunable via "uP_cool_down_time")
    """
    print("4) Fault simulating the binaries (a cluster at a time)\n\n")
    terminated_l = []
    process_l = [] #process list
    exitcode_l = [] #exit codes list
    mem_mapping_l = [] #memory mappings list
    start_f = 0

    while start_f+cluster_size < int(injection_num):

        bfsp_utils.faulty_bins_exec(start_f, start_f+cluster_size,
                                    c_prog_name,
                                    c_prog_args,
                                    process_l, 
                                    exitcode_l,
                                    mem_mapping_l,
                                    terminated_l,
                                    timeout)

        start_f += cluster_size
        bfsp_utils.uP_cool_down(uP_cool_down_time)
    remaining = injection_num-start_f

    bfsp_utils.faulty_bins_exec(start_f, start_f+remaining,
                                c_prog_name,
                                c_prog_args,
                                process_l, 
                                exitcode_l,
                                mem_mapping_l,
                                terminated_l,
                                timeout)

    print("\n\t\t***************************************")
    print(f"\t\t******* END OF FAULT SIMULATION *******")
    print("\t\t***************************************\n")


    ########## Execution analysis + report printing ##########
    """
    Initializing report file
    Executing exit codes analysis and functional analysis
    """
    print("\n\n5) Reporting the execution analysis...")

    report_filepath = f"./exec_reports/bfsp_exec_report_s{r_seed}_n{injection_num}.txt"
    if path.exists(report_filepath):
        os.remove(report_filepath)
    out_file = open(report_filepath,"a+")
    out_file.write(f"verbose_report= {verbose_report}")
    out_file.write(f"\ninjection_num= {injection_num}")
    out_file.write(f"\nrand_seed= {r_seed}")
    out_file.close()

    bfsp_utils.exit_code_analysis(exitcode_l, 
                        terminated_l,
                        report_filepath,
                        verbose_report)

    bfsp_utils.functional_analysis(c_prog_name,
                        injection_num,  
                        report_filepath,
                        verbose_report)

    test_exec_time = divmod(time.time()-test_start_time, 60)
    print(f"...OK - Test execution time = {int(test_exec_time[0])} minutes {int(test_exec_time[1])} seconds")
    print(f"\nSee execution report at:\n{report_filepath}\n\n")



    ########## Crash Analysis + crash report printing ##########
    """
    Runs crash_doctor to understand what caused te crash, reports 
    useful info of the session in a file in ./crash_reports/
    """

    # Retrieving PIDs
    PID_l = []
    for p in process_l:
        PID_l.append(p.pid)

    crash_report_filename = f"./crash_reports/bfsp_crash_report_s{r_seed}_n{injection_num}.txt"
    crash_doctor.crash_reporter(PID_l,
                                exitcode_l,
                                mem_mapping_l,
                                crash_report_filename,
                                c_prog_name)


