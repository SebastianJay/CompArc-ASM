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
