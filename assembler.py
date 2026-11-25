#!/usr/bin/env python3
"""
Hack assembler for the Nand2Tetris Hack platform.

Usage:
    python assembler.py Add.asm --k 85

The optional K controls the capstone feature:
    K % 3 == 0: write labels and variables to symbols.txt
    K % 3 == 1: report invalid instructions with source line numbers
    K % 3 == 2: warn about duplicate labels

The assembler always reports errors with line numbers; for K % 3 == 1
this is the required additional feature.
"""

import argparse
import re
import sys
from pathlib import Path

PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576,
}
for i in range(16):
    PREDEFINED[f"R{i}"] = i

DEST = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}
JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}
COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "M": "1110000",
    "!D": "0001101", "!A": "0110001", "!M": "1110001",
    "-D": "0001111", "-A": "0110011", "-M": "1110011",
    "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
    "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
    "D+A": "0000010", "D+M": "1000010",
    "D-A": "0010011", "D-M": "1010011",
    "A-D": "0000111", "M-D": "1000111",
    "D&A": "0000000", "D&M": "1000000",
    "D|A": "0010101", "D|M": "1010101",
}

SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")


class AssemblerError(Exception):
    pass


def clean_source(path):
    """Return (clean_instruction, original_line_number) pairs."""
    result = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, raw in enumerate(source, start=1):
            line = raw.split("//", 1)[0].strip()
            if line:
                result.append((re.sub(r"\s+", "", line), line_number))
    return result


def assemble(source_path, k):
    source = clean_source(source_path)
    symbols = dict(PREDEFINED)
    label_addresses = {}
    duplicate_labels = []
    rom_address = 0

    # PASS 1: labels
    for instruction, line_number in source:
        if instruction.startswith("(") and instruction.endswith(")"):
            label = instruction[1:-1]
            if not SYMBOL_RE.fullmatch(label):
                raise AssemblerError(f"Line {line_number}: invalid label '{instruction}'")
            if label in symbols:
                duplicate_labels.append((label, line_number))
                if k % 3 == 2:
                    print(f"Warning: Line {line_number}: label '{label}' is written more than once.")
            else:
                symbols[label] = rom_address
                label_addresses[label] = rom_address
        else:
            if instruction.startswith("(") or instruction.endswith(")"):
                raise AssemblerError(f"Line {line_number}: malformed label '{instruction}'")
            rom_address += 1

    # PASS 2: A- and C-instruction conversion
    output = []
    variable_addresses = {}
    next_variable = 16

    for instruction, line_number in source:
        if instruction.startswith("(") and instruction.endswith(")"):
            continue

        if instruction.startswith("@"):
            value = instruction[1:]
            if not value:
                raise AssemblerError(f"Line {line_number}: missing A-instruction value")
            if value.isdigit():
                address = int(value)
                if not 0 <= address <= 32767:
                    raise AssemblerError(f"Line {line_number}: A-instruction value must be 0..32767")
            else:
                if not SYMBOL_RE.fullmatch(value):
                    raise AssemblerError(f"Line {line_number}: invalid symbol '{value}'")
                if value not in symbols:
                    symbols[value] = next_variable
                    variable_addresses[value] = next_variable
                    next_variable += 1
                address = symbols[value]
            output.append(format(address, "016b"))
            continue

        # C-instruction: dest=comp;jump
        if instruction.count("=") > 1 or instruction.count(";") > 1:
            raise AssemblerError(f"Line {line_number}: invalid C-instruction '{instruction}'")
        if ";" in instruction:
            left, jump = instruction.split(";", 1)
        else:
            left, jump = instruction, ""
        if "=" in left:
            dest, comp = left.split("=", 1)
        else:
            dest, comp = "", left

        if dest not in DEST:
            raise AssemblerError(f"Line {line_number}: invalid destination '{dest}'")
        if comp not in COMP:
            raise AssemblerError(f"Line {line_number}: invalid computation '{comp}'")
        if jump not in JUMP:
            raise AssemblerError(f"Line {line_number}: invalid jump '{jump}'")

        output.append("111" + COMP[comp] + DEST[dest] + JUMP[jump])

    output_path = source_path.with_suffix(".hack")
    output_path.write_text("\n".join(output) + "\n", encoding="utf-8")

    if k % 3 == 0:
        symbols_path = source_path.parent / "symbols.txt"
        with symbols_path.open("w", encoding="utf-8") as f:
            f.write("Symbol\tAddress\tType\n")
            for name, address in sorted(PREDEFINED.items(), key=lambda item: item[1]):
                f.write(f"{name}\t{address}\tpredefined\n")
            for name, address in sorted(label_addresses.items(), key=lambda item: item[1]):
                f.write(f"{name}\t{address}\tlabel\n")
            for name, address in sorted(variable_addresses.items(), key=lambda item: item[1]):
                f.write(f"{name}\t{address}\tvariable\n")
        print(f"Symbol table saved to: {symbols_path}")

    print(f"Success: {len(output)} machine instructions written to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Assemble Hack .asm source into .hack machine code.")
    parser.add_argument("asm_file", help="Input Hack assembly file, e.g. Add.asm")
    parser.add_argument("--k", type=int, required=True, help="Your personal number K (last two roll-number digits)")
    args = parser.parse_args()

    path = Path(args.asm_file)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if path.suffix.lower() != ".asm":
        print("Error: input file must have the .asm extension", file=sys.stderr)
        sys.exit(1)

    try:
        assemble(path, args.k)
    except (AssemblerError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
