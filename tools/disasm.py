"""Disassemble Thumb code at an address and show 32-bit constants built with movw/movt.

Usage: python tools/disasm.py ADDRESS [BYTES]
Constants that look like floats are also shown as floats.
"""

import struct
import sys

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

from macho import MachO


def main() -> None:
    start = int(sys.argv[1], 16)
    length = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x100
    macho = MachO()
    offset = macho.file_offset(start)
    low: dict[str, int] = {}
    for ins in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(macho.data[offset:offset + length], start):
        note = ""
        ops = [o.strip() for o in ins.op_str.split(",")]
        if ins.mnemonic.startswith("movw") and len(ops) == 2 and ops[1].startswith("#"):
            low[ops[0]] = int(ops[1][1:], 0)
        elif ins.mnemonic.startswith("movt") and len(ops) == 2 and ops[0] in low:
            value = (int(ops[1][1:], 0) << 16) | low.pop(ops[0])
            as_float = struct.unpack("<f", struct.pack("<I", value))[0]
            note = f"  ; {ops[0]} = {value:#010x} = float {as_float:g}"
        elif ins.mnemonic.startswith("mov") and len(ops) == 2 and ops[1].startswith("#0x3"):
            value = int(ops[1][1:], 0)
            note = f"  ; float {struct.unpack('<f', struct.pack('<I', value))[0]:g}"
        print(f"{ins.address:#07x} {ins.mnemonic} {ins.op_str}{note}")
        if ins.mnemonic.startswith("pop") and "pc" in ins.op_str:
            break


if __name__ == "__main__":
    main()
