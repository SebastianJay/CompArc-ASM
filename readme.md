RISCy Assembler
===
A simple assembler for the UVa Computer Architecture (ECE 4435) instruction set architecture. A description of the ISA is given in ISA.pdf -- the objective of the class assignments is to design a classic RISC pipeline microarchitecture that implements the ISA. I do not claim credit for designing the ISA!

The script was written in Python 2.7 (if you only have Python 3.x, try a 2-to-3 script?). Run the file with one command line parameter that's the path to the assembly code file. The output will be a new file with the binary machine code on the same path with a prepended "bin" (e.g. if input file is code.txt, output will be bin.code.txt).

Syntax
---
Each line is specified in format:

**Labels**
```
[label name]:
```
A label cannot start with a number, must end with a colon, and cannot be a reg ID; label names must be unique.

**Instructions**
```
[opcode] [comma separated operands]
```

**Operand**
* for various opodes, reg ID = a register label (e.g. r0, r1, r15)
* for LIL/LIH, SWI, LD, ST, jumps, and branches, signed value/int = a number (e.g. 7, -15, hFF)
* for branches, signed offset = EITHER a number OR a label name (which then gets translated into a number by the assembler)
* for jump, you must use a reg ID, followed by a number
* for LIL, instead of an integer you can use a label (to set up a jump) -- however BR is recommended for jumping to labels

**Number format:**
* if hex
```
h[hex string]
```
* if decimal
```
[- if negative][decimal string]
```

Neither labels, opcodes, nor operands are case sensitive (therefore for labels, "main" and "Main" will conflict). Comments can be added inline with #. Single line comments are fine as well if they start with #.

Example assembly
---
```
main:
lil r4, -22
lil r5, hFF
lih r5, h7F
add r0, r1
br main     #goes back to top
```

Memory
---
You can specify arbitrary data in a separate file and include it in the program by using the `--mem [path to memory file]` command line arg. This memory will be inserted into the generated machine code at the specified start addresses within the file itself. Data words are specified in either hex or binary. A word that is followed by a colon indicates a memory address; otherwise it is interpreted as data to be placed at sequential offsets from that location. An example file is shown below.
```
0050:   #the following memory will start at address 0x0050
0001    # address 0x0050 has 0x0001
00FF    # address 0x0051 has 0x00FF
0002    # address 0x0052 has 0x0002
0005    # and so on..
0004
FFFF
0000000011111111:   #another block of memory will start at 0x00FF
1010101010101010    # address 0x00FF has 0xAAAA
1111000011110000    # address 0x0100 has 0xF0F0
ABCD                # we can use hex and binary interchangeably
FC02
0000000010110100
```
