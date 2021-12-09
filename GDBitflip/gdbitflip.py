import os
from os import path
import sys
import random
import subprocess
import time

import gdbitflip_utils
import ARM_CortexA9_info
import crash_wizard
import gdbitflip_report_zipper

#########################################################
#################### R E M I N D E R #################### 
#########################################################
"""
The binary file under test must be compiled with debug symbols
using -g option and the source files should be accessible.
"""

########## PARAMETER PARSING ##########
def exit_usage():
    usage = "\nUsage: python3 gdbitflip.py PATH/TO/BINARY -n <num> [--args <num_args> ARGS] [options]"
    usage += "\n\n   required:"
    usage += "\n\tPATH/TO/BINARY\t\tPath (relative or absolute) to binary file under test"
    usage += "\n\t-n <num>,\t\t\t<num> = number of injections"
    usage += "\n\t-m 1/2/3/4\t\tMode selection: 1-SEU, 2-MBU, 3-ClearContent, 4-PresetContent"
    usage += "\n\n   optional:"
    usage += "\n\t--args <num_args> ARGS\t<num_args> = number of args of binary;"
    usage += "\n\t\t\t\tARGS = argument of program divided by space"
    usage += "\n\t-s r_seed,\t\tSet the random seed to r_seed"
    usage += "\n\t-v, --verbose,\t\tTo produce verbose execution report"
    usage += "\n\t-c, --clean,\t\tTo clean the bitflipped results folder and exit"
    usage += "\n\t-z, --zip,\t\tTo compact all the reports in ./exec_reports/ in a summary\n"
    usage += "\n\n"
    sys.exit(usage)

if "-h" in sys.argv or "--help" in sys.argv:
    exit_usage()

if(len(sys.argv) < 3):
    exit_usage()
else:
    # Binary Name setting (REQUIRED)
    c_prog_name = sys.argv[1]
    if not path.exists(c_prog_name):
        print(f"\n\n{c_prog_name}: No such file or directory.")
        exit_usage()

    # Program under test arguments
    args = ""
    if "--args" in sys.argv:
        base_args_param_index = sys.argv.index("--args")
        NUM_ARGS = sys.argv[base_args_param_index+1]
        if NUM_ARGS.isnumeric() and int(NUM_ARGS) > 0 and int(NUM_ARGS) < 10:
            NUM_ARGS = int(NUM_ARGS)
        else:
            print("\n\n\t\tInvalid inferior program arguments\n\n")
            exit_usage()

        for i in range(1,NUM_ARGS+1):
            args += " "+sys.argv[base_args_param_index+1+i]

        print(f"[CHECK] Platform will execute binary under test in this way:\n\n\t{c_prog_name} {args}\n\n")            


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
        if (param_mode.isnumeric() and int(param_mode) > 0 and int(param_mode) < 5):
            selected_mode = int(param_mode)
            if selected_mode == 1:
                print("--> Selected SEU injection mode")
            elif selected_mode == 2:
                print("--> Selected MBU injection mode")
            elif selected_mode == 3:
                print("--> Selected ClearContent injection mode")
            elif selected_mode == 4:
                print("--> Selected PresetContent injection mode")
        else:
            sys.exit("Invalid mode! (1-SEU, 2-MBU, 3-ClearContent, 4-PresetContent)")
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
        gdbitflip_utils.clear_faulty_directory()
        sys.exit()

    # Report zipping mode
    if "-z" in sys.argv or "--zip" in sys.argv:
        gdbitflip_report_zipper.report_zipper()
        sys.exit()

########## END PARAMETER PARSING ##########


if __name__ == '__main__':

    #args = "300000"

    hang_timeout = 10 #time after which the process is considered hang
    random.seed(r_seed)
    test_start_time = int(time.time())    

    ############################################################################
    ##### 0) Clearing working directories                                  #####
    ############################################################################
    gdbitflip_utils.clear_work_directories()

    ############################################################################
    ##### 1) Generating bitflip parameters                                 #####
    ############################################################################
    """
    For sake of repeatability, these random choices are done all together.
    """

    rand_line_step_l = []
    rand_instr_step_l = []
    rand_reg_l = []
    rand_bit_pos_l = []
    rand_bit_pos_A_l = []
    rand_bit_pos_B_l = []
    registers = ARM_CortexA9_info.registers

    #### Retrieving SLOC
    cmd = f"gdb {c_prog_name} -batch -ex 'set listsize unlimited' -ex 'list'"
    code_lines_count = int(subprocess.check_output(cmd, shell=True, encoding="utf-8",universal_newlines=True).splitlines()[-1].split()[0])
    #exit(f"Binary file was made from a source containing {code_lines_count} lines.")
    

    for j in range(injection_num):
        rand_line_step_l.append(random.randint(0,code_lines_count))    
        rand_instr_step_l.append(random.randint(0,1000))
        rand_reg_l.append(random.choice(registers))
        
        # bit to be flipped in SEU
        rand_bit_pos_l.append(random.randint(0,31))

        # adiacent bits to be flipped in MBU
        bit_pos_A = random.randint(0,30)
        rand_bit_pos_A_l.append(bit_pos_A)
        rand_bit_pos_B_l.append(bit_pos_A+1)


    ############################################################################
    ##### 2) Fault Injection --> Invoking GDB to execute inner_script.py   #####
    ############################################################################
    
    exec_log_filename = f"./exec_logs/gdbitflip_exec_log_s{r_seed}_n{injection_num}.log"
    if path.exists(exec_log_filename):
        os.remove(exec_log_filename)
    with open(exec_log_filename,'w+') as exec_log_file:  

        #### Preparing report file
        header = f"bin_name= {c_prog_name}\nseed= {r_seed}\ninjection_num= {injection_num}"
        exec_log_file.write(f"bin_name= {c_prog_name}\n")
        exec_log_file.write(f"seed= {r_seed}\n\n")
        exec_log_file.write(f"injection_num= {injection_num}")

        #### Injecting
        PID_l = []
        exit_code_l = []
        terminated_l = []
        mem_mapping_l = []

        ## Creating support copy of binary
        subprocess.run(f"cp {c_prog_name} {c_prog_name}_inj-1",shell=True)

        print("")

        for i in range(0,injection_num):
            exec_log_file.write("\n")

            # Renaming the binary file to be able to track it as process
            subprocess.run(f"mv {c_prog_name}_inj{i-1} {c_prog_name}_inj{i}",shell=True)

            # Starting GDB to execute and bitflip program under test
            cmd = f"gdb -batch"
            cmd += f" -ex 'py inj_num = {i}'"
            cmd += f" -ex 'py c_prog_name = \"{c_prog_name}_inj{i}\"'"
            cmd += f" -ex 'py args = \"{args}\"'"
            cmd += f" -ex 'py rand_line = {rand_line_step_l[i]}'"
            cmd += f" -ex 'py rand_instr = {rand_instr_step_l[i]}'"
            cmd += f" -ex 'py target_register = \"{rand_reg_l[i]}\"'"
            cmd += f" -ex 'py bit_pos = {rand_bit_pos_l[i]}'"
            cmd += f" -ex 'py bit_pos_A = {rand_bit_pos_A_l[i]}'"
            cmd += f" -ex 'py bit_pos_B = {rand_bit_pos_B_l[i]}'"

            if selected_mode == 1:
                cmd += f" -ex 'source inner_script.py' "
            elif selected_mode == 2:
                cmd += f" -ex 'source inner_script_MEU.py' "
            elif selected_mode == 3:
                cmd += f" -ex 'source inner_script_CLEAR.py' "
            elif selected_mode == 4:
                cmd += f" -ex 'source inner_script_PRESET.py' "

            gdb_proc = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, encoding="utf-8")#, stderr = subprocess.DEVNULL)
            

            try:
                gdb_proc.wait(hang_timeout) # HANG DETECTION

            except subprocess.TimeoutExpired: # inferior process hang!
                #### killing inferior process
                inferior_name = c_prog_name.split('/')[-1]
                cmd = f"pgrep --lightweight --newest {inferior_name}"

                try:
                    inferior_pid = int(subprocess.check_output(cmd, shell=True, encoding = "utf-8"))
                    print(f"\nPROCESS HANG, killing PID={inferior_pid}")

                
                    time.sleep(3)

                    try:
                        os.kill(inferior_pid, 1) #sending SIGHUP
                    except ProcessLookupError as ex:
                        print("Didn't find process")
                        print(ex)
                
                    PID_l.append(inferior_pid)
                    terminated_l.append(i)

                except subprocess.CalledProcessError as ex:
                    print(f"\nOUTPUT: {ex.stdout}")
                    print(f"\nERROR: {ex.stderr}")

            
            else: # inferior process did exit!
                gdb_proc_output = gdb_proc.stdout.read() # gets output from subprocess
                
                #### Analysing outcomes
                gdbitflip_utils.outcome_parser( i, 
                                                exec_log_file, 
                                                gdb_proc_output,
                                                mem_mapping_l, 
                                                PID_l, 
                                                exit_code_l)

            print(f"\tDONE {i+1} injections",end="\r")
    print("\n")
    
    # Removing support copy of binary
    subprocess.check_output(f"rm {c_prog_name}_inj{i}",shell=True)


    ####################################################
    ############### 3) Reporting results ###############
    ####################################################

    print(f"Gathered data from {len(exit_code_l) + len(terminated_l)} processes.")

    exec_report_filename = f"./exec_reports/GDBitflip_exec_report_s{r_seed}_n{injection_num}.txt"
    if path.exists(exec_report_filename):
        os.remove(exec_report_filename)
    out_file = open(exec_report_filename,"w+")
    out_file.write(f"verbose_report= {verbose_report}")
    out_file.write(f"\ninjection_num= {len(exit_code_l) + len(terminated_l)}")
    out_file.write(f"\nrand_seed= {r_seed}")
    out_file.close()

    ####################################################
    ####### E X I T - C O D E    A N A L Y S I S ####### 
    ####################################################

    gdbitflip_utils.exit_code_analysis(exit_code_l, 
                                  terminated_l,
                                  exec_report_filename,
                                  verbose_report)

    ####################################################
    ###### F U N C T I O N A L    A N A L Y S I S ######
    ####################################################

    gdbitflip_utils.functional_analysis(c_prog_name,
                                        args,
                                        injection_num,  
                                        exec_report_filename,
                                        verbose_report)

    print(f"See execution log at {exec_log_filename}")
    print(f"See execution report at {exec_report_filename}")

    ####################################################
    ########### C R A S H   A N A L Y S I S ############
    ####################################################

    crash_report_filename = f"./crash_reports/GDBitflip_crash_report_s{r_seed}_n{injection_num}.txt"
    crash_wizard.crash_reporter(PID_l, 
                                exit_code_l, 
                                mem_mapping_l,
                                crash_report_filename,
                                c_prog_name)




  
    test_exec_time = divmod(time.time()-test_start_time, 60)
    print(f"...OK - Test execution time = {int(test_exec_time[0])} minutes {int(test_exec_time[1])} seconds")