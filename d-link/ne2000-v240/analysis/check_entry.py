#!/usr/bin/env python3
"""Run the original option-ROM installer twice with synthetic BIOS RAM."""

from pathlib import Path
import json, struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SS, UC_X86_REG_SP

p = Path(__file__).resolve().parent
rom = (p.parent / "ne2000-v240-2764.bin").read_bytes()
assert rom[:3] == bytes.fromhex("55aa10") and len(rom) == 8192 and sum(rom) % 256 == 0
u = Uc(UC_ARCH_X86, UC_MODE_16)
u.mem_map(0, 0x100000)
u.mem_write(0xC8000, rom)
original = bytes.fromhex("78563412")
u.mem_write(0x64, original)
steps = 0
returned = False


def code(uc, addr, size, _):
    global steps, returned
    steps += 1
    if addr == 0x10000:
        returned = True
        uc.emu_stop()


u.hook_add(UC_HOOK_CODE, code)
r = []
for trial in (1, 2):
    returned = False
    steps = 0
    u.reg_write(UC_X86_REG_CS, 0xC800)
    u.reg_write(UC_X86_REG_IP, 3)
    u.reg_write(UC_X86_REG_SS, 0x7000)
    u.reg_write(UC_X86_REG_SP, 0xFFF0)
    u.mem_write(0x7FFF0, struct.pack("<HH", 0, 0x1000))
    u.emu_start(0xC8003, 0xFFFFF, count=200)
    assert returned
    vector = bytes(u.mem_read(0x64, 4))
    saved = bytes(u.mem_read(0x300, 4))
    marker = bytes(u.mem_read(0x304, 2))
    assert (
        vector == bytes.fromhex("610000c8")
        and saved == original
        and marker == bytes.fromhex("6e6a")
    )
    r.append(
        {
            "trial": trial,
            "returned": returned,
            "instructions_including_return_sentinel": steps,
            "int19_vector": vector.hex(),
            "saved_original_vector": saved.hex(),
            "installation_marker": marker.hex(),
        }
    )
(p / "entry-results.json").write_text(json.dumps(r, indent=2) + "\n")
print(json.dumps(r))
