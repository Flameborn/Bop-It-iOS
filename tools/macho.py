"""Minimal reader for the thin 32-bit ARM Mach-O made by tools/decompile.py.

Resolves addresses of Objective-C string constants (the __cfstring section) and plain
C strings to their text, so decompiled code that passes addresses can be read.
"""

import struct
from functools import cache
from pathlib import Path

BINARY = Path(__file__).resolve().parent.parent / "research" / "BopIt_armv7"
LC_SEGMENT = 0x1


class MachO:
    def __init__(self, path: Path = BINARY) -> None:
        self.data = path.read_bytes()
        self.sections: dict[str, tuple[int, int, int]] = {}
        self.segments: list[tuple[int, int, int]] = []
        _magic, _cpu, _sub, _type, ncmds, _size, _flags = struct.unpack("<7I", self.data[:28])
        offset = 28
        for _ in range(ncmds):
            cmd, cmdsize = struct.unpack("<2I", self.data[offset:offset + 8])
            if cmd == LC_SEGMENT:
                vmaddr, vmsize, fileoff = struct.unpack("<3I", self.data[offset + 24:offset + 36])
                self.segments.append((vmaddr, vmsize, fileoff))
                nsects = struct.unpack("<I", self.data[offset + 48:offset + 52])[0]
                for i in range(nsects):
                    s = offset + 56 + i * 68
                    sectname = self.data[s:s + 16].rstrip(b"\0").decode()
                    segname = self.data[s + 16:s + 32].rstrip(b"\0").decode()
                    addr, size, off = struct.unpack("<3I", self.data[s + 32:s + 44])
                    self.sections[f"{segname},{sectname}"] = (addr, size, off)
            offset += cmdsize

    def file_offset(self, address: int) -> int | None:
        for vmaddr, vmsize, fileoff in self.segments:
            if vmaddr <= address < vmaddr + vmsize:
                return fileoff + address - vmaddr
        return None

    def c_string(self, address: int) -> str | None:
        offset = self.file_offset(address)
        if offset is None:
            return None
        end = self.data.find(b"\0", offset)
        raw = self.data[offset:end]
        if not raw or len(raw) > 2000:
            return None
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def u32(self, address: int) -> int | None:
        offset = self.file_offset(address)
        if offset is None:
            return None
        return struct.unpack("<I", self.data[offset:offset + 4])[0]

    @cache
    def cfstrings(self) -> dict[int, str]:
        """Address of each constant NSString to its text."""
        found: dict[int, str] = {}
        addr, size, off = self.sections.get("__DATA,__cfstring", (0, 0, 0))
        for entry in range(0, size, 16):
            _isa, flags, pointer, length = struct.unpack("<4I", self.data[off + entry:off + entry + 16])
            text_offset = self.file_offset(pointer)
            if text_offset is None:
                continue
            if flags & 0x4:  # UTF-16 contents
                raw = self.data[text_offset:text_offset + length * 2]
                text = raw.decode("utf-16-le", errors="replace")
            else:
                text = self.data[text_offset:text_offset + length].decode("utf-8", errors="replace")
            found[addr + entry] = text
        return found
