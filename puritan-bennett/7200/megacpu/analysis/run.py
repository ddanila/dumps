#!/usr/bin/env python3
from pathlib import Path
import argparse, json, collections, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from unicorn import *
from unicorn.x86_const import *

BASE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument("--steps", type=int, default=1000000)
p.add_argument("--output", default="results/strict")
p.add_argument("--mock", action="store_true")
p.add_argument("--explore", action="store_true")
p.add_argument("--analog", action="store_true")
p.add_argument("--native-far-return", action="store_true")
p.add_argument("--continue-faults", action="store_true")
p.add_argument("--fault-code", type=lambda x: int(x, 0))
a = p.parse_args()
out = BASE / a.output
out.mkdir(parents=True, exist_ok=True)
u = Uc(UC_ARCH_X86, UC_MODE_16)
u.mem_map(0, 0x110000)
for n in [0, 1, 2, 3, 4, 5, 6, 8]:
    data = next(BASE.parent.glob(f"chip{n}-*.bin")).read_bytes()
    u.mem_write(0xF0000 if n == 0 else (n - 1) * 65536, data)
u.mem_write(0x60000, b"\xff" * 65536)
u.mem_protect(0, 0x80000, UC_PROT_READ | UC_PROT_EXEC)
u.mem_protect(0xF0000, 0x10000, UC_PROT_READ | UC_PROT_EXEC)
regs = {
    name: globals()["UC_X86_REG_" + name]
    for name in [
        "AX",
        "BX",
        "CX",
        "DX",
        "SI",
        "DI",
        "BP",
        "SP",
        "CS",
        "DS",
        "ES",
        "SS",
        "IP",
        "EFLAGS",
    ]
}
u.reg_write(UC_X86_REG_CS, 0xF000)
u.reg_write(UC_X86_REG_IP, 0xFFF0)
u.reg_write(UC_X86_REG_EFLAGS, 2)
ports = {}
io = []
events = []
read_sites = collections.defaultdict(set)
writes = collections.Counter()
tx = collections.defaultdict(bytearray)
coverage = collections.Counter()
reads = collections.Counter()
trace = collections.deque(maxlen=2000)
missing = []
reason = "instruction budget"
steps = 0
instructions = {}
call_edges = collections.Counter()
last_call = None
decoder = Cs(CS_ARCH_X86, CS_MODE_16)


def state():
    return {k: u.reg_read(v) for k, v in regs.items()}


def pc():
    return (u.reg_read(UC_X86_REG_CS) * 16 + u.reg_read(UC_X86_REG_IP)) & 0xFFFFF


def code(uc, addr, size, _):
    global steps, reason, last_call
    if last_call is not None:
        call_edges[(last_call, addr)] += 1
    if addr not in instructions:
        raw = bytes(u.mem_read(addr, min(size, 15)))
        ins = next(decoder.disasm(raw, u.reg_read(UC_X86_REG_IP), count=1), None)
        instructions[addr] = {
            "cs": u.reg_read(UC_X86_REG_CS),
            "ip": u.reg_read(UC_X86_REG_IP),
            "bytes": raw.hex(),
            "mnemonic": ins.mnemonic if ins else "?",
            "operands": ins.op_str if ins else "?",
        }
    last_call = addr if instructions[addr]["mnemonic"] in ("call", "lcall") else None
    steps += 1
    coverage[addr] += 1
    trace.append((addr, bytes(u.mem_read(addr, min(size, 15))).hex()))
    if addr == 0x53BEE:
        events.append(
            {
                "kind": "diagnostic failure entry",
                "state": state(),
                "stack": bytes(
                    u.mem_read(
                        u.reg_read(UC_X86_REG_SS) * 16 + u.reg_read(UC_X86_REG_SP), 32
                    )
                ).hex(),
            }
        )
        if a.continue_faults:
            sp = u.reg_read(UC_X86_REG_SP)
            ip, cs = struct.unpack(
                "<HH", u.mem_read(u.reg_read(UC_X86_REG_SS) * 16 + sp, 4)
            )
            u.reg_write(UC_X86_REG_SP, (sp + 18) & 65535)
            u.reg_write(UC_X86_REG_CS, cs)
            u.reg_write(UC_X86_REG_IP, ip)
            return
    if addr == 0x3A180:
        if a.fault_code is not None:
            u.mem_write(
                u.reg_read(UC_X86_REG_SS) * 16 + u.reg_read(UC_X86_REG_SP) + 4,
                struct.pack("<H", a.fault_code),
            )
        events.append(
            {
                "kind": "application fault entry",
                "state": state(),
                "stack": bytes(
                    u.mem_read(
                        u.reg_read(UC_X86_REG_SS) * 16 + u.reg_read(UC_X86_REG_SP), 32
                    )
                ).hex(),
            }
        )
    if addr == 0x3A39F and coverage[addr] > 1:
        reason = "application terminal fault loop"
        uc.emu_stop()
        return
    if not a.native_far_return and bytes(u.mem_read(addr, 1))[0] in (0xCA, 0xCB, 0xCF):
        sp = u.reg_read(UC_X86_REG_SP)
        ss = u.reg_read(UC_X86_REG_SS)
        ip, cs = struct.unpack("<HH", u.mem_read(ss * 16 + sp, 4))
        extra = (
            struct.unpack("<H", u.mem_read(addr + 1, 2))[0]
            if bytes(u.mem_read(addr, 1))[0] == 0xCA
            else 0
        )
        if bytes(u.mem_read(addr, 1))[0] == 0xCF:
            u.reg_write(
                UC_X86_REG_EFLAGS,
                struct.unpack("<H", u.mem_read(ss * 16 + sp + 4, 2))[0],
            )
            extra = 2
        u.reg_write(UC_X86_REG_SP, (sp + 4 + extra) & 65535)
        u.reg_write(UC_X86_REG_CS, cs)
        u.reg_write(UC_X86_REG_IP, ip)
        return
    if a.explore and addr == 0x7E39D and coverage[addr] % 100 == 0:
        events.append({"kind": "synthetic timer2 IRQ", "step": steps})
        intr(u, 0x13, None)
        return
    if a.explore and addr == 0xF86B4:
        events.append({"kind": "skip board POST loop", "address": addr})
        u.mem_write(0xAFE91, b"\x15")
    if a.mock and addr == 0xFE601:
        events.append({"kind": "timer POST completion flag", "address": addr})
        u.mem_write(0x80DF2, b"\x2a")
    if addr == 0xFE012:
        reason = "POST failure"
        uc.emu_stop()
        return
    if a.mock and addr == 0xFE439:
        events.append({"kind": "watchdog reset with retained RAM", "address": addr})
        u.reg_write(UC_X86_REG_CS, 0xF000)
        u.reg_write(UC_X86_REG_IP, 0xFFF0)
        return
    if 0x60000 <= addr < 0x70000:
        missing.append({"kind": "execute", "address": addr, "state": state()})
        reason = "missing ROM execution"
        uc.emu_stop()
    if coverage[addr] > 5000000:
        reason = "repeated instruction threshold"
        uc.emu_stop()


def read(uc, access, addr, size, value, _):
    if a.analog and addr == 0x90000:
        u.mem_write(addr, bytes([u.mem_read(addr, 1)[0] & 0x3F]))
        u.mem_write(0x90001, b"\x00\x08")
    if addr < 0x80000 or addr >= 0xF0000:
        reads[addr] += 1
        read_sites[addr].add(pc())
    if 0x60000 <= addr < 0x70000 and len(missing) < 100:
        missing.append({"kind": "read", "address": addr, "size": size, "pc": pc()})


def inp(uc, port, size, _):
    v = (
        4
        if a.explore and port in (0xBD11, 0xBD10, 0xBD01, 0xBD00)
        else (
            0xEF
            if a.mock and port == 0xC200 and pc() >= 0xF8700 and pc() < 0xF9000
            else ports.get(port, 0xFFFF)
        )
    ) & ((1 << (8 * size)) - 1)
    if len(io) < 10000:
        io.append(["in", pc(), port, size, v])
    return v


def output(uc, port, size, value, _):
    ports[port] = value
    if port in (0xBD02, 0xBD03, 0xBD12, 0xBD13) and size == 1:
        tx[port].append(value)
    if len(io) < 10000:
        io.append(["out", pc(), port, size, value])


def write(uc, access, addr, size, value, _):
    writes[addr >> 12] += 1


def intr(uc, number, _):
    global reason
    ip, cs = struct.unpack("<HH", u.mem_read(number * 4, 4))
    if not (cs or ip):
        reason = f"unhandled interrupt {number:02x}"
        uc.emu_stop()
        return
    sp = (u.reg_read(UC_X86_REG_SP) - 6) & 65535
    ss = u.reg_read(UC_X86_REG_SS)
    u.mem_write(
        ss * 16 + sp,
        struct.pack(
            "<HHH",
            u.reg_read(UC_X86_REG_IP),
            u.reg_read(UC_X86_REG_CS),
            u.reg_read(UC_X86_REG_EFLAGS) & 65535,
        ),
    )
    u.reg_write(UC_X86_REG_SP, sp)
    u.reg_write(UC_X86_REG_EFLAGS, u.reg_read(UC_X86_REG_EFLAGS) & ~0x300)
    u.reg_write(UC_X86_REG_CS, cs)
    u.reg_write(UC_X86_REG_IP, ip)


u.hook_add(UC_HOOK_MEM_WRITE, write)
u.hook_add(UC_HOOK_CODE, code)
u.hook_add(UC_HOOK_MEM_READ, read)
u.hook_add(UC_HOOK_INSN, inp, None, 1, 0, UC_X86_INS_IN)
u.hook_add(UC_HOOK_INSN, output, None, 1, 0, UC_X86_INS_OUT)
u.hook_add(UC_HOOK_INTR, intr)
try:
    u.emu_start(0xFFFF0, 0x100000, count=a.steps)
except UcError as e:
    reason = str(e)
r = {
    "profile": {
        "mock": a.mock,
        "explore": a.explore,
        "analog": a.analog,
        "continue_faults": a.continue_faults,
        "native_far_return": a.native_far_return,
        "fault_code": a.fault_code,
    },
    "events": events,
    "writes_by_4k_page": dict(writes),
    "reason": reason,
    "steps": steps,
    "state": state(),
    "unique_instructions": len(coverage),
    "missing": missing,
    "trace": list(trace),
    "io": io,
}
(out / "result.json").write_text(json.dumps(r, indent=2) + "\n")
(out / "memory.bin").write_bytes(bytes(u.mem_read(0, 0x100000)))
(out / "coverage.json").write_text(json.dumps(dict(coverage), sort_keys=True) + "\n")
(out / "reads.json").write_text(json.dumps(dict(reads), sort_keys=True) + "\n")
print(reason, steps, {k: hex(v) for k, v in state().items()}, "unique", len(coverage))
print("last IO", io[-15:])

(out / "read-sites.json").write_text(
    json.dumps({k: sorted(v) for k, v in read_sites.items()}, sort_keys=True) + "\n"
)
for port, data in tx.items():
    (out / f"tx-{port:04x}.bin").write_bytes(data)

(out / "instructions.json").write_text(json.dumps(instructions, sort_keys=True) + "\n")
(out / "calls.json").write_text(
    json.dumps(
        [
            {"source": s, "target": t, "count": c}
            for (s, t), c in sorted(call_edges.items())
        ],
        indent=2,
    )
    + "\n"
)
(out / "display-fault-buffer.txt").write_text(
    bytes(u.mem_read(0x8C450, 20)).decode("ascii", errors="backslashreplace") + "\n"
)
