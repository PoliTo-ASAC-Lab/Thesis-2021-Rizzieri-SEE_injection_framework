# BFSP [v1.05]
Bitflip Fault Simulation Platform by Daniele Rizzieri (2021)

## Requirements
Required Linux packages:
- python3
- procps
- gdb
- systemd-coredump

## Test Binary File Guidelines
In order to be properly testable, the program under test must be compliant with the following guidelines: 
1) Application's output must be redirected to the standard output virtual file (i.e., it must be instructed to print the functional results to screen/console)
2) Application's behaviour and functional output must be fully deterministic: the tester must ensure that the entire code does not depend on time or other random variables. 
Examples: 
	- if some kind of randomization function is involved, the tester must fix the randomization seed;
	- if some kind of time related function is involved, the tester must either suppress it or fix the time dependant variable;
3) The test application must be compiled from code, following the here reported guidelines: 
    1. During the compilation the debug symbols must be included using the GCC option "-g"
    2. The application must be statically linked, through the "-static" compilation option
    3. When compiling, the tester should avoid the compiler optimization options "-o#"


## Quick Start 
1) Remember to set a value for the global setting variables in the code, not accessible via command parameters (see ***bfsp.py*** for more details):
	- binary file name
	- binary arguments
	- hang timeout

2) Put SW executable file*** under test in ./run/ folder\
		[*** Read carefully ***Test Binary File Guidelines*** section]

3) Type "python3 bfsp.py -h" or "python3 bfsp.py --help" for usage info:

>\> Usage: python3 bfsp.py -n N [options]\
> &nbsp;&nbsp;&nbsp;required:\
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-n N,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;N = number of injections\
> &nbsp;&nbsp;&nbsp;options:\
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\-s r_seed,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Set the random seed to r_seed\
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\-v, --verbose,&nbsp;&nbsp;&nbsp;To produce verbose output report\
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\-c, --clean,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;To clean the bitflipped libraries folder and exit\
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\-z, --zip,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;To compact all the reports in ./reports/ in a summary\

4) See crash report in the file indicated at end of execution.

5) See execution report in the file indicated at end of execution.

### Output File Locations 
- ./bitflipped_binaries/ --> binaries with injected bitflips
- ./bitflipped_binaries/results/ --> functional results of the binaries 
- ./core_dumps/ --> coredump files of crashed processes in 
- ./gdb_logs/ --> log files from gdb analysis of the coredumps 
- ./exec_reports/ --> reports with info about the exit codes and hang processes 
- ./crash_reports/ --> reports with info about the crashed processes 
