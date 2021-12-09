import gdb
#import time
#print(f"I'd inject program \"{c_prog_name}\" at {break_address} in {target_register} -> {bit_pos}-th bit")

gdb.execute(f'file {c_prog_name}', True, True)
gdb.execute(f"break main", True, True)
c_prog_name = c_prog_name.split('/')[-1] #already contains injection number info!
gdb.execute(f'run {args} > bitflipped_results/res_{c_prog_name}.dat', True, True)

#### at first break ( _start )
gdb.execute(f"step {rand_line}", True, True) # step RAND_NUM of lines
gdb.execute(f"stepi {rand_instr}", True, True) # step RAND_NUM instructions 

#########################
##### B I T F L I P #####
#########################

#gdb.write(f'\n\tBITFLIPPING register {target_register}\n')

#gdb.execute("info registers")
register_value = gdb.execute(f"print {target_register}", True,True)
# GETTING REGISTER VALUE
if(target_register in ['$sp','$pc']): 
    # $sp = (void *) 0xbefff388
    register_value = int(register_value.split()[4][2:], 16)
else:
    # $r1 = 23465632
    register_value = int(register_value.split()[2])
print(f"got -> {register_value} ({str(bin(register_value))[2:].zfill(32)})")

#######################
# BITFLIP-A INJECTION #
#######################

if (register_value >> bit_pos_A)%2 == 0: # is it 0 or 1?
    mask = 1 << bit_pos_A # 0 --> force to 1
    new_register_value_A = register_value | mask
else:
    mask = ~(1 << bit_pos_A) # 1 --> force to 0
    new_register_value_A = register_value & mask
print(f"BITFLIP_A set -> {new_register_value_A} ({str(bin(new_register_value_A))[2:].zfill(32)})")

#######################
# BITFLIP-B INJECTION #
#######################

if (new_register_value_A >> bit_pos_B)%2 == 0: # is it 0 or 1?
    mask = 1 << bit_pos_B # 0 --> force to 1
    new_register_value_B = new_register_value_A | mask
else:
    mask = ~(1 << bit_pos_B) # 1 --> force to 0
    new_register_value_B = new_register_value_A & mask
print(f"BITFLIP_B set -> {new_register_value_B} ({str(bin(new_register_value_B))[2:].zfill(32)})")

print(f"TRIED TO EXECUTE --> set {target_register}={new_register_value_B}")
gdb.execute(f"set {target_register}={new_register_value_B}")

############################################
##### RETRIEVE INFERIOR MEMORY MAPPING #####
############################################

inferior_pid = gdb.selected_inferior().pid
gdb.execute(f"!pmap {inferior_pid} -d", True, True) #mem-map of inferior printed to gdb.stdout

###########################
##### C O N T I N U E #####
###########################

gdb.execute("continue ")


print(f"---> Inferior_PID= {inferior_pid}")


# Retrieving exit code of inferior
prog_exit_code = (gdb.execute('p $_exitcode', True, True)).split()[2]
print(f"---> Exit_code= {prog_exit_code}")

# Generating core dump if inferior crashed
if prog_exit_code != "0":
    gdb.execute(f"generate-core-file ./core_dumps/cdump_{c_prog_name}.dump", True)

# Retrieving signal info, if inferior signaled
sig_check = int(gdb.execute('p $_isvoid($_siginfo)',True,True).split()[2])
#print(f"sig_check = {sig_check}")
if sig_check == 0: # inferior signaled
    sig_num = gdb.execute('p $_siginfo.si_signo',True,True)
    sig_num = sig_num.split()[2]
    print(f"---> Signal_num= -{sig_num}")

