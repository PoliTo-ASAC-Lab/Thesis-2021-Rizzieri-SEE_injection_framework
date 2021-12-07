# bitflip function [By Sarah Azimi]

def bitflip(golden_number, bit_pos):
    #print (f"number is:{bin(golden_number)} and bit position is:{bit_pos}")
    if (golden_number >> bit_pos)%2 == 0:
    	# force to 1
        mask = 1 << bit_pos
        faulty_number = golden_number | mask
    else:
    	# force to 0
        mask = ~(1 << bit_pos)
        faulty_number = golden_number & mask
    #print (f"faulty number:{bin(faulty_number)}")
    return faulty_number
