# Nand2Tetris Capstone – K = 85

Roll number: 2501730385

## Personal calculations
- K = 85
- K mod 3 = 1: assembler reports invalid instructions with source line numbers.
- K mod 4 = 1: box width = 32 pixels = 2 words per row.
- Starting row = 85; height = 20 rows.
- First screen word = 16384 + 32*85 = 19104.

## Files
- Part_B_Assembler/assembler.py: two-pass Hack assembler.
- Part_C_Box/Box.asm: keyboard-controlled box drawing program.
- Part_C_Box/Box.hack: assembled machine code.

## Assemble
From the project root:
```bash
python Part_B_Assembler/assembler.py Part_C_Box/Box.asm --k 85
```

## Important
Part A HDL files are not fabricated here. Build CPU.hdl, Memory.hdl and Computer.hdl
from the Nand2Tetris course chips and verify them with the official test scripts.
Add the tested HDL files and genuine screenshots before submission.
