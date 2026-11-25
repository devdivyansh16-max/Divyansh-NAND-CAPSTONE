// Box.asm
// Roll number: 2501730385
// K = 85; K mod 4 = 1; width = 32 pixels (2 words)
// Starts at screen row 85; height = 20 rows.
// A key press draws the box; key release clears it.

(START)
    @KBD
    D=M
    @DRAW
    D;JNE
    @CLEAR
    0;JMP

(DRAW)
    // First word of row 85 = SCREEN + 32*85 = 19104
    @19104
    D=A
    @R13
    M=D

    // Twenty rows
    @20
    D=A
    @R14
    M=D

(DRAW_LOOP)
    // First 16 pixels
    @R13
    A=M
    M=-1

    // Second 16 pixels
    @R13
    D=M
    @1
    D=D+A
    @R13
    A=D
    M=-1

    // Advance to the same column in the next screen row
    @R13
    D=M
    @32
    D=D+A
    @R13
    M=D

    // Decrease remaining row count
    @R14
    MD=M-1
    @DRAW_LOOP
    D;JGT

    @START
    0;JMP

(CLEAR)
    // First word of row 85
    @19104
    D=A
    @R13
    M=D

    @20
    D=A
    @R14
    M=D

(CLEAR_LOOP)
    // Clear first 16 pixels
    @R13
    A=M
    M=0

    // Clear second 16 pixels
    @R13
    D=M
    @1
    D=D+A
    @R13
    A=D
    M=0

    // Advance by 32 words to the next row
    @R13
    D=M
    @32
    D=D+A
    @R13
    M=D

    @R14
    MD=M-1
    @CLEAR_LOOP
    D;JGT

    @START
    0;JMP
