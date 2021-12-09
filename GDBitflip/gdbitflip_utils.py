# GDBitflip functions module
import os
from os import path
import sys
import subprocess
from ARM_CortexA9_info import ec_dict
from crc32 import CRC32_hash

def clear_work_directories():
    print("Clearing/Creating working directories...")

    results_folder = "./bitflipped_results"
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

    exec_logs_path = "./exec_logs"
    if not path.exists(exec_logs_path):
        print("\tCreated ./exec_logs/ !")
        os.mkdir(exec_logs_path)   


    if (path.exists("./core_dumps")):
        for filename in os.listdir("./core_dumps"):
            filepath = ""
            filepath = os.path.join("./core_dumps", filename)
            os.remove(filepath)
    else:
        print("\tCreated ./core_dumps !")
        os.mkdir("./core_dumps")  

    print("...OK")


def outcome_parser(inj_num,
                   exec_log_file,
                   gdb_proc_output,
                   mem_mapping_l,
                   PID_l,
                   exit_code_l,
                   ):
    i = inj_num
    
    ### Retrieving memory mapping from gdb output
    FOUND_MMAP = False
    mem_map = ""
    for line in gdb_proc_output.splitlines(): # split lines
        splitted_line = line.split() # split every line around " "
        if splitted_line != []: # if not empty line
            if not FOUND_MMAP:
                if splitted_line[0] == "Address": #"pmap" command output begins with this line
                    FOUND_MMAP = True
                    mem_map += line+"\n"
            else: #FOUND_MMAP = True, I'm reading mem_map
                mem_map += line+"\n"
                if splitted_line[0] == "mapped:": #"pmap" command output ends with this line
                    break
    else:
        print("No memory map found!")
    if mem_map != "":
        mem_mapping_l.append(mem_map)
        #print("MEM_MAP received from gdb:\n\n"+mem_map)

    ### Retrieving PID, Exit-code, Exit-signal
    for line in gdb_proc_output.splitlines(): # split lines
        splitted_line = line.split() # split every line around " "

        if splitted_line != []: # if not empty line
            if splitted_line[0] == "--->": # interesting lines begin with "--->"
                exec_log_file.write(f"\n[{i+1}] {line}") # write interesting line to file

                if splitted_line[1] == "Inferior_PID=": # e.g. "---> Inferior_PID= {inferior_pid}"
                    PID_l.append(int(splitted_line[2])) # saving PID

                elif splitted_line[1] == "Exit_code=": # e.g. "---> Exit_code= 0"
                    if splitted_line[2] == "0":
                        exit_code_l.append(0) # saving exit code 

                elif splitted_line[1] == "Signal_num=": # e.g. "---> Signal_num= -{sig_num}"
                    exit_code_l.append(int(splitted_line[2]))  


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
                        args,
                        injection_num,  
                        report_filepath,
                        verbose_report):
    """
    Performs thr functional analysis by comparing the CRC32 hashes of file
    ./bitflipped_results/golden_results_{binary_name} 
    with file
    ./bitflipped_results/results_{i}_{binary_name}
    """
    funct_faulty_cnt = 0
    funct_faulty_l = [] 
    funct_noFile_cnt = 0
    funct_noFile_l = []
    
    binary_name = c_prog_name.split("/")[-1]

    # Hashing golden results
    golden_res_filename = f"./bitflipped_results/golden_results_{binary_name}.dat"
    subprocess.run(f"{c_prog_name} {args}",shell=True,stdout=open(golden_res_filename,'w+'))#,stderr=subprocess.DEVNULL)
    golden_hash = CRC32_hash(golden_res_filename) # GOLDEN RESULTS

    # Comparing with other results
    for i in range(0,int(injection_num)):
        faulty_res_filename = f"./bitflipped_results/res_{binary_name}_inj{i}.dat"
        if os.path.exists(faulty_res_filename): # result file exists
            faulty_hash = CRC32_hash(faulty_res_filename)
            if faulty_hash != golden_hash:
                funct_faulty_cnt += 1
                funct_faulty_l.append(i)
        else: #result file do not exists
            print(f"unable to find {faulty_res_filename}")
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