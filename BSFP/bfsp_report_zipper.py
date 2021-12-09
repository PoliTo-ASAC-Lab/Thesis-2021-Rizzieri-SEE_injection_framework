"""
--- BSFP Test Reports zipper ---
When executed, it elaborates all the reports in ./exec_reports/ and 
generates a summary file merging together all the reports.
Also writes down which files have been taken into account.

Report example "./report/bfsp_report_s1614855618_n50.txt", with line numbers:
[Not Verbose]
0   verbose_report= False
1   injection_num= 50
2   rand_seed= 1614855618
3   distinct_exit_codes= 4
4   |0|SUCCESS| 38
5   |-11|SIGSEGV| 9
6   |-4|SIGILL| 1
7   |1|GENERAL_ERROR| 2
8   terminated_deadlock= 0
9   no_file= 4
10  correct_results= 34
11  faulty_results= 12

[Verbose]
0   verbose_report= True
1   injection_num= 50
2   rand_seed= 1614855618
3   
4       --EXIT_CODES_ANALYSIS--
5   distinct_exit_codes= 4
6   |0|SUCCESS| 38
7   |-11|SIGSEGV| 9
8   |-4|SIGILL| 1
9   |1|GENERAL_ERROR| 2
10  terminated_deadlock= 0
11  terminated_deadlock_processes= []
12  
13      --FUNCTIONAL_ANALYSIS--
14  no_file= 4
15  no_file_processes= [0, 29, 42, 48]
16  correct_results= 34
17  faulty_results= 12
18  faulty_results_processes= [7, 8, 10, 11, 13, 17, 22, 32, 34, 39, 40, 43]

"""
from glob import glob
import datetime
from exit_code_dict import ec_dict

DEBUG = False

def report_zipper():
    # Initializing total counters
    injection_total_cnt = 0
    terminated_deadlock_total_cnt = 0
    no_file_total_cnt = 0
    correct_results_total_cnt = 0
    faulty_results_total_cnt = 0

    exitcode_types_total_list = []
    exitcode_cnt_total_list = []

    # Parsing files
    print("Parsing files...")

    reports_filenames = glob("./exec_reports/bfsp_exec_report_s*.txt")
    for r_filename in reports_filenames:
        print(f"\n\t{r_filename}")

        with open(r_filename) as report:
            report_lines = report.read().splitlines() #lines of file are now accessible in this list

            verbose = True if (report_lines[0].split(" ")[1] == "True") else False # retrieving verbosity
            if DEBUG: print(f"verbose {verbose}")

            injection_total_cnt += int(report_lines[1].split(" ")[1]) 
            if DEBUG: print(f"inj cnt {injection_total_cnt}")
            
            index = 3 if not verbose else 5 # VERBOSE vs NOT VERBOSE REPORT!
            if DEBUG: print("index = "+str(index))

            exit_codes_lines = int(report_lines[index].split(" ")[1]) 
            if DEBUG: print(f"exit_codes_lines {exit_codes_lines}")

            index += 1
            for i in range(index,index+exit_codes_lines): #reading exit code with relative counters
                exit_code = int(report_lines[i].split(" ")[0].split("|")[1]) #exit code type
                if DEBUG: print(exit_code)

                exit_code_cnt = int(report_lines[i].split(" ")[1]) #num of processes that exited with this exit code
                if DEBUG: print(f"\tcnt = {exit_code_cnt}")

                ec_found = False
                for j in range(0, len(exitcode_types_total_list)):
                    if exit_code == exitcode_types_total_list[j]:  # already seen exit code
                        ec_found = True
                        exitcode_cnt_total_list[j] += exit_code_cnt 
                        break
                if not ec_found: # new exit code encoutered
                    exitcode_types_total_list.append(exit_code)
                    exitcode_cnt_total_list.append(exit_code_cnt)

            i += 1
            terminated_deadlock_total_cnt += int(report_lines[i].split(" ")[1])
            if DEBUG: print(f"terminated_deadlock_total_cnt = {terminated_deadlock_total_cnt}")

            i += 1 if not verbose else 4 # VERBOSE vs NOT VERBOSE REPORT!
            no_file_total_cnt += int(report_lines[i].split(" ")[1])
            if DEBUG: print(f"no_file_total_cnt = {no_file_total_cnt}")

            i += 1 if not verbose else 2 # VERBOSE vs NOT VERBOSE REPORT!
            correct_results_total_cnt += int(report_lines[i].split(" ")[1])
            if DEBUG: print(f"correct_results_total_cnt = {correct_results_total_cnt}")

            i += 1
            faulty_results_total_cnt += int(report_lines[i].split(" ")[1])
            if DEBUG: print(f"faulty_results_total_cnt = {faulty_results_total_cnt}")



    # Printing summary
    print("Printing summary report...",end="")

    timestamp = (datetime.datetime.now()+datetime.timedelta(hours=3)).strftime("%Y-%m-%d@%H%M")
    summary_filename = f"./exec_reports/SUMMARIES/BFSP_SUMMARY_{timestamp}.txt"
    with open(summary_filename,"w+") as summary:
        summary.write("Files involved in this summary:\n")
        for filename in reports_filenames:
            summary.write("\t"+filename+"\n")

        summary.write(f"\nTotal injected bitflips = {injection_total_cnt}")

        summary.write("\n\n\t--- EXIT CODE ANALYSIS ---")
        summary.write(f"\nDistinct exit codes = {len(exitcode_types_total_list)}")
        for i in range(0,len(exitcode_types_total_list)):
            ec_num = exitcode_types_total_list[i]
            ec_cnt = exitcode_cnt_total_list[i]
            ec_percentage = round(100*exitcode_cnt_total_list[i]/injection_total_cnt, 3)
            summary.write(f"\n\tExit code {ec_num} ({ec_dict[ec_num]}) -> {ec_cnt} [{ec_percentage}%]")
        terminated_deadlock_percentage = round(100*terminated_deadlock_total_cnt/injection_total_cnt,3)
        summary.write(f"\n\tTerminated due to deadlock -> {terminated_deadlock_total_cnt} [{terminated_deadlock_percentage}%]")

        summary.write("\n\n\t--- FUNCTIONAL ANALYSIS ---")
        no_file_percentage = round(100*no_file_total_cnt/injection_total_cnt,2)
        summary.write(f"\nOutput file produced -> {injection_total_cnt-no_file_total_cnt} [{100-no_file_percentage}%]")
        summary.write(f"\nOutput file NOT produced -> {no_file_total_cnt} [{no_file_percentage}%]\n")

        correct_results_percentage = round(100*correct_results_total_cnt/injection_total_cnt,2)
        summary.write(f"\nCorrect results -> {correct_results_total_cnt} [{correct_results_percentage}%]")
        summary.write(f"\nFaulty results -> {faulty_results_total_cnt} [{round(100-correct_results_percentage,2)}%]")


    print(f"\n...OK - See summary report at {summary_filename}\n\n")


if __name__ == '__main__':
    report_zipper()