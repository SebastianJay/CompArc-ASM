import sys
import argparse
import os.path

regop = {
    'r0':   '0000',
    'r1':   '0001',
    'r2':   '0010',
    'r3':   '0011',
    'r4':   '0100',
    'r5':   '0101',
    'r6':   '0110',
    'r7':   '0111',
    'r8':   '1000',
    'r9':   '1001',
    'r10':  '1010',
    'r11':  '1011',
    'r12':  '1100',
    'r13':  '1101',
    'r14':  '1110',
    'r15':  '1111',
}

arithop = {
    'add':  '00000',
    'adc':  '00001',
    'sub':  '00010',
    'sbc':  '00011',
    'and':  '00100',
    'or':   '00101',
    'xor':  '00110',
    'not':  '00111',
    'sl':   '01000',
    'srl':  '01001',
    'sra':  '01010',
    'rra':  '01110',
    'rr':   '01101',
    'rl':   '01100',
}

branchop = {
    'br':   '0000',
    'bc':   '1000',
    'bo':   '0100',
    'bn':   '0010',
    'bz':   '0001'
}

auxop = {
    'ld':   '001',
    'st':   '010',
    'lil':  '0',
    'lih':  '1',
    'jmp':  '0',
    'jal':  '1'
}

#takes a signed int value and returns a binary string
#the string is as long as is specified in bits
def dectobin(num, bits):
    neg = False
    if num < 0:
        num = num + (1 << (bits-1))
        neg = True
    res = bin(num)[2:]
    res = '0'*(bits-1 - len(res)) + res
    if len(res) < bits:
        if neg:
            res = '1' + res
        else:
            res = '0' + res
    return res

#takes a string representing a decimal or hex number
# returns parsed int or errs and exits if format not met
def parseint(string):
    base = 10
    if string[0] == 'h':
        string = string[1:]
        base = 16
    try:
        return int(string, base)
    except ValueError:
        print 'ERROR: malformed integer constant (bad constant='+string+')'
        sys.exit()

#returns whether a char is in [0-9]
def isnum(char):
    return ord(char[0]) >= 48 and ord(char[0]) <= 57

#takes a list of register labels and errs and exits if a label is not valid
def regcheck(reglst):
    for reg in reglst:
        if reg not in regop:
            print 'ERROR: unknown operand (bad operand ='+reg+')'
            sys.exit()
    return reglst

#takes a list of strings raw contents of assembly file and int start location of program
#returns a list of binary strings corresponding to program
def convert(lines, startaddr):
    lbmap = {}
    ind = startaddr
    #do first pass to look for labels
    for line in lines:
        #check if line is a label
        if line[-1] == ':':
            if len(line) <= 1:
                print 'ERROR: empty label'
                sys.exit()
            label = line[0:-1]
            if isnum(line[0]):
                print 'ERROR: cannot begin label with number (bad label ='+label+')'
                sys.exit()
            if label in lbmap:
                print 'ERROR: multiple labels with same name (bad name='+label+')'
                sys.exit()
            if label in regop.keys():
                print 'ERROR: label with register ID (bad name='+label+')'
                sys.exit()
            lbmap[label] = ind
        #otherwise it should be regular instruction
        else:
            ind += 1

    ind = startaddr
    binlines = []
    #do second pass to parse instructions
    for line in lines:
        if line[-1] == ':':
            continue
        else:
            args0 = line.split(' ', 1)    #split by whitespace
            args0 = [arg.strip() for arg in args0 if len(arg.strip()) > 0]
            args1 = []
            if len(args0) > 1:
                args1 = args0[1].split(',') #split by comma
                args1 = [arg.strip() for arg in args1 if len(arg.strip()) > 0]
            #match opcode
            opcode = args0[0]
            ins = None
            if opcode == 'nop':
                ins = '0000000000000000'
            elif opcode == 'ei':
                ins = '0000000000001001'
            elif opcode == 'di':
                ins = '0000000000001000'
            elif opcode == 'swi':
                val = parseint(args1[0])
                if val < 0 or val > 7:
                    print 'ERROR: SWI int not valid (bad int='+val+')'
                suffix = dectobin(val, 3)
                ins = '0000000000010' + suffix
            elif opcode == 'usr':
                ins = '0000000000011000'
            elif opcode == 'ld' or opcode == 'st':
                reglst = regcheck(args1[0:2])
                val = parseint(args1[2])
                if val < 0 or val > 31:
                    print 'ERROR: offset too large for load/store (bad offset='+val+')'
                suffix = dectobin(val, 5)
                ins = auxop[opcode] + regop[reglst[0]] + regop[reglst[1]] + suffix
            elif opcode == 'mov':
                reglst = regcheck(args1)
                ins = '011' + regop[reglst[0]] + regop[reglst[1]] + '00000'
            elif opcode == 'lil' or opcode == 'lih':
                reglst = regcheck(args1[0:1])
                if args1[1] in lbmap:
                    val = lbmap[args1[1]]
                else:
                    val = parseint(args1[1])
                if val < -128 or val > 127:
                    print 'ERROR: constant too large in load immediate (bad constant='+str(val)+')'
                suffix = dectobin(val, 8)
                ins = '100' + regop[reglst[0]] + auxop[opcode] + suffix
            elif opcode in arithop.keys():
                reglst = regcheck(args1)
                ins = '101' + regop[reglst[0]] + regop[reglst[1]] + arithop[opcode]
            elif opcode == 'jmp' or opcode == 'jal':
                reglst = regcheck(args1[0:1])
                val = parseint(args1[1])
                if val < -128 or val > 127:
                    print 'ERROR: constant too large in jmp/jal (bad constant='+str(val)+')'
                suffix = dectobin(val, 8)
                ins = '110' + regop[reglst[0]] + auxop[opcode] + suffix
            elif opcode in branchop.keys():
                if args1[0] in lbmap:
                    val = lbmap[args1[0]] - ind     #pc relative offset
                else:
                    val = parseint(args1[0])
                if val < -128 or val > 127:
                    print 'ERROR: constant too large in branch (bad constant='+str(val)+')'
                suffix = dectobin(val, 8)
                ins = '111' + branchop[opcode] + '0' + suffix
            else:
                print 'ERROR: unknown opcode (bad opcode = '+opcode+')'
                sys.exit()
            if ins is None:
                print 'ERROR: unhandled instruction'
                sys.exit()
            binlines.append(ins)
            ind += 1
    return binlines

#takes a hex or binary string and returns a binary string
def parsememline(line):
    if len(line) == 4:
        return dectobin(int(line, 16), 16)
    elif len(line) == 16:
        return line
    else:
        print 'ERROR: bad line length in memory file (must be hex or binary, zero padded)'

#takes in list of string raw contents of memory file and returns
# list of (int start location of block, list of binary string memory contents)
def readmem(lines):
    lineblocks = []
    currblock = []
    startaddr = 0
    for line in lines:
        if line[-1] == ':':
            if currblock:
                lineblocks.append((startaddr, currblock))
                currblock = []
            startaddr = int(parsememline(line[:-1]), 2)
        else:
            memline = parsememline(line)
            currblock.append(memline)
    if currblock:
        lineblocks.append((startaddr, currblock))
    return lineblocks

def main():
    ##parse command line arguments
    parser = argparse.ArgumentParser(description='ECE 4435 assembler')
    parser.add_argument('asmfile', help='path to input assembly file')
    parser.add_argument('--hex', action='store_true', help='print output as hex strings')
    parser.add_argument('--start', default=8, help='set decimal address of first instruction of program (8 by default)')
    parser.add_argument('--mem', default='', help='path to auxiliary memory file')
    args = vars(parser.parse_args(sys.argv[1:]))

    startaddr = args['start']
    outhex = args['hex']
    mempath = args['mem']
    inpath = args['asmfile']

    #read memory blocks if a mem file is specified
    lineblocks = []
    if mempath:
        with open(mempath, 'U') as fin:
            lines = fin.read().split('\n')
        #strip out comments and leading/trailing whitespace
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if len(line) > 0 and line[0] != '#']
        for i, line in enumerate(lines):
            if '#' in line:
                lines[i] = line[0:line.index('#')]
        lines = [line.strip() for line in lines]
        #convert lines into (int start location, list of binary string) mem blocks
        lineblocks = readmem(lines)

    #read the main program file
    with open(inpath, 'U') as fin:
        lines = fin.read().split('\n')
    #remove empty lines, single line comments and convert to lowercase
    lines = [line.lower() for line in lines if len(line) > 0 and line[0] != '#']
    #remove comments that are part of code line
    for i, line in enumerate(lines):
        if '#' in line:
            lines[i] = line[0:line.index('#')]
    #convert assembly into list of binary strings
    binlines = convert(lines, startaddr)

    #identify the max address of program or data
    maxind = startaddr + len(binlines) - 1
    for block in lineblocks:
        maxind = max(maxind, block[0] + len(block[1]) - 1)
    #create a large enough space for the merged program/data, all zero initialized
    proglines = ['0000000000000000'] * (maxind + 1)
    #fill in lines from memory
    for block in lineblocks:
        mstartaddr = block[0]
        for i, line in enumerate(block[1]):
            proglines[mstartaddr+i] = line
    #fill in lines from the program
    for i, line in enumerate(binlines):
        proglines[startaddr+i] = line
    #designate memory at address 0 to be where the start of the program is
    proglines[0] = dectobin(startaddr, 16)

    #convert to hex if option specified
    if outhex:
        proglines = [hex(int(line, 2))[2:] for line in proglines]
    #join binary strings into one buffer
    outbuf = '\n'.join(proglines) + '\n'

    #print out the whole program as new file
    pathparts = os.path.split(inpath)
    with open(os.path.join(pathparts[0], 'bin.' + pathparts[1]), 'w') as fout:
        fout.write(outbuf)

if __name__ == '__main__':
    main()
