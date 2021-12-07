# BFSP functions module

import os
from os import path
import ctypes
import random
import sys
import subprocess
import time
import shlex

from exit_code_dict import ec_dict
from bitman import bitflip
from crc32 import CRC32_hash

def uP_cool_down(t):
    print("\nCooling down uP for ",end="")
    for i in range(0,t):
        print(f"...{t-i}")
        time.sleep(1)
    print("...GO")

def wait_exec(t):
    print("\n\nLetting processes execute for ",end="")
    for i in range(0,t):
        print(f"...{t-i}")
        time.sleep(1)
    print("...GO\n")

def clear_faulty_directory():
    print("1) Clearing/Creating faulty binaries directory...")

    faulty_bin_folder = "./bitflipped_binaries/"
    if (path.exists(faulty_bin_folder)):
        for filename in os.listdir(faulty_bin_folder):
            filepath = ""
            filepath = os.path.join(faulty_bin_folder, filename)
            #print(f"filepath:{filepath}")
            if os.path.isfile(filepath):
                os.remove(filepath)
    else:
        print("\tCreated ./bitflipped_binaries/ !")
        os.mkdir(faulty_bin_folder)


    results_folder = "./bitflipped_binaries/results"
    if (path.exists(results_folder)):
        for filename in os.listdir(results_folder):
            filepath = ""
            filepath = os.path.join(results_folder, filename)
            # print(f"filepath:{filepath}")
            os.remove(filepath)
    else:
        print(f"\tCreated {results_folder} !")
        os.mkdir(results_folder)


    reports_path = "./exec_reports"
    if not path.exists(reports_path):
        print("\tCreated ./exec_reports/ !")
        os.mkdir(reports_path)       


    SUMMARIES_path = "./exec_reports/SUMMARIES"
    if not path.exists(SUMMARIES_path):
        print("\tCreated ./exec_reports/SUMMARIES !")
        os.mkdir(SUMMARIES_path)    


    run_path = "./run"
    if not path.exists(run_path):
        print("\tCreated ./run/ !")
        os.mkdir(run_path)
        exit("\n\tPLEASE PUT BINARY UNDER TEST AND INPUT FILE(S) IN IT!")

    print("...OK")


def bitflip_injection(c_prog_name, injection_num):
    print("2) Performing fault injection on golden_content...")
    with open(f"./run/{c_prog_name}", "rb") as golden_file:
        golden_content = golden_file.read()
    golden_file.close()

    for i in range(0, int(injection_num)):
        byte_cord = random.randint(0, len(golden_content) - 1)
        number = golden_content[byte_cord]
        bit_cord = random.randint(0, 7)
        faulty_number = bitflip(number, bit_cord)
        faulty_bin_content = bytearray(golden_content)
        faulty_bin_content[byte_cord] = faulty_number
        faulty_bin_filename = f"./bitflipped_binaries/inj_{i}_{c_prog_name}"
        #print (f"golden byte: {golden_content [byte_cord]}, faulty byte:{faulty_bin_content[byte_cord]},{byte_cord} ")
        with open(faulty_bin_filename, "wb") as faulty_file:
            faulty_file.write(faulty_bin_content)
        faulty_file.close()

        if not((i+1)%50) : print(f"\tDONE {i+1} injections",end="\r")
    print(f"\tDONE {i+1} injections")
    print("\t...OK")

    print("\n\tSetting permission +x to bitflipped binaries...")
    permission_setter = subprocess.Popen(['chmod','-R','+x','./bitflipped_binaries'])
    permission_setter.wait()
    print("\t...OK")

    print("...OK")


def faulty_bins_exec(start, end, 
                    c_prog_name,
                    c_prog_args,
                    process_l, 
                    exitcode_l,
                    mem_mapping_l,
                    terminated_l,
                    timeout):
    """
    Executes the faulty binaries in the range ({start},{end}) 
    from the binaries contained in {faulty_bin_folder}
    Appends processes to {process_l} list
    Appends "terminated-due-to-deadlock" processes to {terminated_l} list
    """
    print("\t\t###########################################################")
    print(f"\t\t######## Fault simulation of binaries {start} to {end} ########")
    print("\t\t###########################################################\n")
    print(f"\nExecuting binaries from #{start} to #{end}...")
    
    
    for i in range(start, end):
        faulty_res_filename = f"./bitflipped_binaries/results/results_{i}_{c_prog_name}.dat"

        # Executing i-th binary
        command = f"./bitflipped_binaries/inj_{i}_{c_prog_name} {c_prog_args}"
        command_l = shlex.split(command)
        proc = subprocess.Popen(command_l, stdout=open(faulty_res_filename,"w"))
        process_l.append(proc)
        #print(f"Started process {i} executing {faulty_bin_filename}")
        
        # Retrieving memory mapping of process while still alive
        mem_map = subprocess.check_output(f"pmap {proc.pid} -d", shell=True, universal_newlines=True)
        mem_mapping_l.append(mem_map)

        if not((i+1)%50) : print(f"\tExecuted {i+1} faulty binaries",end="\r")
    print("\n\t...OK")

    wait_exec(timeout) #deadlock detection

    # ******* Retrieving exit codes *******
    for i in range(start, end):
        process_exit_code = process_l[i].poll() # return exit code if process finished, "None" otherwise
        if process_exit_code == None:
            process_l[i].terminate()
            terminated_l.append(i)
            exitcode_l.append(-15)
            print(f"Terminating process[{i}]")
        else:
            print(f"Exit code of faulty process#{i}:{process_exit_code}")
            exitcode_l.append(process_exit_code)


def exit_code_analysis(exitcode_l, 
                        terminated_l,
                        report_filepath,
                        verbose_report):
    """
    Analyses and catalogs the exit_codes of the several processes
    """
    exitcode_classification_l = []
    exitcode_classification_l.append(0)
    exitcode_cnt_l = []
    exitcode_cnt_l.append(0)

    # counting exit codes by processes
    for exit_c in exitcode_l:
        exitcode_Found = False
        for j in range(0, len(exitcode_classification_l)):
            if exit_c == exitcode_classification_l[j]:
                exitcode_Found = True
                exitcode_cnt_l[j] += 1
                break
        if not exitcode_Found:
            exitcode_classification_l.append(exit_c)
            exitcode_cnt_l.append(1)

    # ******* Printing the results *******
    out_file = open(report_filepath,"a+")
    if verbose_report: out_file.write(f"\n\n\t--EXIT_CODES_ANALYSIS--") 
    out_file.write(f"\ndistinct_exit_codes= {len(exitcode_classification_l)}")
    for i in range(0,len(exitcode_classification_l)):
        ec_num = exitcode_classification_l[i]
        out_file.write(f"\n|{ec_num}|{ec_dict[ec_num]}| {exitcode_cnt_l[i]}")
    out_file.write(f"\nterminated_deadlock= {len(terminated_l)}")
    if verbose_report: out_file.write(f"\nterminated_deadlock_processes= {terminated_l}")
    out_file.close()   

def functional_analysis(c_prog_name,
                        injection_num,  
                        report_filepath,
                        verbose_report):
    """
    Performs thr functional analysis by comparing the CRC32 hashes of file
    ./golden_results_{c_prog_name} 
    with file
    ./bitflipped_binaries/results/results_{i}_{c_prog_name}
    """
    funct_faulty_cnt = 0
    funct_faulty_l = [] 
    funct_noFile_cnt = 0
    funct_noFile_l = []
    
    # Hashing golden results
    gold_res_filename = golden_res_filename = f"./run/results_GOLDEN_{c_prog_name}.dat"
    golden_hash = CRC32_hash(gold_res_filename) # GOLDEN RESULTS

    # Comparing with other results
    for i in range(0,int(injection_num)):
        faulty_res_filename = f"./bitflipped_binaries/results/results_{i}_{c_prog_name}.dat"
        if os.path.exists(faulty_res_filename): # result file exists
            faulty_hash = CRC32_hash(faulty_res_filename)
            if faulty_hash != golden_hash:
                funct_faulty_cnt += 1
                funct_faulty_l.append(i)
        else: #result file do not exists
            funct_noFile_cnt += 1
            funct_noFile_l.append(i)

    # ******* Printing the results *******
    out_file = open(report_filepath,"a+")
    if verbose_report: out_file.write(f"\n\n\t--FUNCTIONAL_ANALYSIS--")
    out_file.write(f"\nno_file= {funct_noFile_cnt}")
    if verbose_report: out_file.write(f"\nno_file_processes= {funct_noFile_l}")
    out_file.write(f"\ncorrect_results= {injection_num -funct_noFile_cnt -funct_faulty_cnt}")    
    out_file.write(f"\nfaulty_results= {funct_faulty_cnt}")
    if verbose_report: out_file.write(f"\nfaulty_results_processes= {funct_faulty_l}")
    out_file.close()