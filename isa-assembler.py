'''
Targeted for Python 2.7 (if you only have Python 3.x, try a 2-to-3 script?)
Run the file with one command line parameter that's the path to the assembly code file
The output will be a new file with the binary machine code on the same path with a prepended "bin."
    (e.g. if input file is code.txt, output will be bin.code.txt)

each line specified in format:
if label
    [label name]:
    label cannot start with a number, must end with a colon, and cannot be a reg ID; label names must be unique
if instruction
    [opcode] [comma separated operands]
    operand must be
        for various opodes, reg ID = a register label, r0 through r15
        for LIL/LIH or SWI, signed value/int = a number
            for LIL, instead of an integer you can use a label (to set up a jump) -- however the range is small
        for branch, signed offset = EITHER a number OR a label
        for jump, you must use a reg ID, followed by a number
    a number follows the format:
    if hex
        h[hex string]
    if decimal
        [- if negative][decimal string]
neither labels nor operands are case sensitive (therefore for labels, "main:" and "Main:" will conflict)
comments can be added inline with #; single line comments are fine as well if they start with #

Example assembly corresponding to the ISA
main:
lil r4, -22
lil r5, hFF
lih r5, h7F
add r0, r1
br main     #goes back to top

Software provided as is, yada yada. If you find a bug let me know.
The parser is ad-hoc so if you have syntax errors the script might crash.
--Jay Sebastian
'''

import sys
import argparse
import os.path

#modify this value to be the memory location where the program begins
startaddress = 10
outhex = False

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

def isnum(char):
    return ord(char[0]) >= 48 and ord(char[0]) <= 57

def regcheck(reglst):
    for reg in reglst:
        if reg not in regop:
            print 'ERROR: unknown operand (bad operand ='+reg+')'
            sys.exit()
    return reglst

def convert(lines):
    lbmap = {}
    ind = startaddress
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

    ind = startaddress
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

def main():
    parser = argparse.ArgumentParser(description='ECE 4435 assembler')
    parser.add_argument('asmfile', help='path to input assembly file')
    parser.add_argument('--hex', action='store_true', help='print output as hex strings')
    parser.add_argument('--start', default=10, help='set decimal address of first instruction of program (10 by default)')
    args = vars(parser.parse_args(sys.argv[1:]))

    startaddress = args['start']
    outhex = args['hex']
    inpath = args['asmfile']

    with open(inpath, 'U') as fin:
        lines = fin.read().split('\n')

    #remove empty lines, single line comments and convert to lowercase
    lines = [line.lower() for line in lines if len(line) > 0 and line[0] != '#']
    #remove comments that are part of code line
    for i, line in enumerate(lines):
        if '#' in line:
            lines[i] = line[0:line.index('#')]
    binlines = convert(lines)
    if outhex:
        binlines = [hex(int(line, 2))[2:] for line in binlines]
    outbuf = '\n'.join(binlines) + '\n'

    pathparts = os.path.split(inpath)
    with open(os.path.join(pathparts[0], 'bin.' + pathparts[1]), 'w') as fout:
        fout.write(outbuf)

if __name__ == '__main__':
    main()
