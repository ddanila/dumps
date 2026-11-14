#!/usr/bin/env python3
"""Generate raw text inventory, address-based candidate xrefs and observed code."""

from pathlib import Path
import bisect, collections, csv, hashlib, html, json, re, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

BASE = Path(__file__).resolve().parent
OUT = BASE / "catalog"
OUT.mkdir(exist_ok=True)
roms = {}
for n in (0, 1, 2, 3, 4, 5, 6, 8):
    p = next(BASE.parent.glob(f"chip{n}-*.bin"))
    roms[n] = (0xF0000 if n == 0 else (n - 1) * 65536, p.read_bytes())
strings = []
for n, (base, data) in roms.items():
    for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
        if not m.group().strip():
            continue
        strings.append(
            dict(
                chip=n,
                offset=m.start(),
                address=base + m.start(),
                length=len(m.group()),
                text=m.group().decode(),
                pointer_candidates=[],
                observed_readers=[],
            )
        )
strings.sort(key=lambda s: s["address"])
starts = [s["address"] for s in strings]


def containing(addr):
    i = bisect.bisect_right(starts, addr) - 1
    if i >= 0 and addr < starts[i] + strings[i]["length"]:
        return strings[i]


# Four bytes interpreted as little-endian offset:segment. These are candidates,
# not proof that arbitrary data is a pointer or that a call site displays text.
missing_pointers = []
for n, (base, data) in roms.items():
    for off in range(len(data) - 3):
        ofs, seg = struct.unpack_from("<HH", data, off)
        addr = (seg * 16 + ofs) & 0xFFFFF
        s = containing(addr)
        if s and addr == s["address"]:
            s["pointer_candidates"].append(f"{base+off:05x}")
        if 0x60000 <= addr < 0x70000 and off % 2 == 0:
            missing_pointers.append(
                dict(source=f"{base+off:05x}", target=f"{addr:05x}")
            )
reads = collections.defaultdict(set)
coverage = collections.Counter()
for run in sorted((BASE / "results").glob("*")):
    if run.name not in {"strict", "mock", "explore", "analog", "format-ab"}:
        continue
    if (run / "read-sites.json").exists():
        for addr, pcs in json.loads((run / "read-sites.json").read_text()).items():
            s = containing(int(addr))
            if s:
                reads[s["address"]].update(f"{pc:05x}" for pc in pcs)
    if (run / "coverage.json").exists():
        coverage.update(
            {
                int(k): v
                for k, v in json.loads((run / "coverage.json").read_text()).items()
            }
        )
for s in strings:
    s["observed_readers"] = sorted(reads[s["address"]])
(OUT / "strings.json").write_text(json.dumps(strings, indent=2) + "\n")
with (OUT / "strings.csv").open("w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(
        [
            "chip",
            "offset_hex",
            "physical_hex",
            "length",
            "text",
            "candidate_pointer_locations",
            "observed_read_PC",
        ]
    )
    for s in strings:
        w.writerow(
            [
                s["chip"],
                f"{s['offset']:04x}",
                f"{s['address']:05x}",
                s["length"],
                s["text"],
                " ".join(s["pointer_candidates"]),
                " ".join(s["observed_readers"]),
            ]
        )
(OUT / "missing-pointer-candidates.json").write_text(
    json.dumps(missing_pointers, indent=2) + "\n"
)
md = Cs(CS_ARCH_X86, CS_MODE_16)
with (OUT / "executed.asm").open("w") as f:
    f.write(
        "; Executed instruction addresses, decoded from original ROM bytes.\n; Physical-address branch rendering is for navigation, not segmented relocation.\n"
    )
    for addr, count in sorted(coverage.items()):
        for n, (base, data) in roms.items():
            if base <= addr < base + len(data):
                ins = next(
                    md.disasm(data[addr - base : addr - base + 15], addr, count=1), None
                )
                if ins:
                    f.write(
                        f"{addr:05x}  {ins.bytes.hex():<24} {ins.mnemonic:<8} {ins.op_str:<40} ; executions={count}\n"
                    )
                break
# Decode fixed-width option records separately; printable runs otherwise join metadata.
b = roms[1][1]
menus = []
for addr in range(0x50BD, 0x54BF, 41):
    menus.append(
        dict(
            address=f"{addr:05x}",
            label=b[addr : addr + 36].decode("ascii", errors="replace"),
            metadata=b[addr + 36 : addr + 41].hex(),
        )
    )
(OUT / "option-menu.json").write_text(json.dumps(menus, indent=2) + "\n")
rows = []
for s in strings:
    rows.append(
        "<tr><td>%s</td><td>%05x</td><td><pre>%s</pre></td><td>%s</td><td>%s</td></tr>"
        % (
            s["chip"],
            s["address"],
            html.escape(s["text"]),
            ", ".join(s["pointer_candidates"]),
            ", ".join(s["observed_readers"]),
        )
    )
(OUT / "strings.html").write_text(
    """<!doctype html><meta charset="utf-8"><title>PB7200 ROM text inventory</title><style>body{font:16px system-ui;margin:2em;background:#f5f6fa}input{font:inherit;padding:.6em;width:70%}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #ccd;padding:.4em;text-align:left;vertical-align:top}pre{white-space:pre-wrap;margin:0;max-width:65ch}th{position:sticky;top:0;background:#dde}td{overflow-wrap:anywhere}</style><h1>7200 ROM text inventory</h1><p>Raw printable runs (4+ characters), including false positives and joined records. Pointer matches are candidates; observed reads include checksums and table copies, not necessarily display use.</p><input placeholder="Search text, address, chip or reader" oninput="for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())"><table><thead><tr><th>Chip</th><th>Physical address</th><th>Text</th><th>Candidate pointer locations</th><th>Observed reader PCs</th></tr></thead><tbody>"""
    + "".join(rows)
    + "</tbody></table>"
)
summary = dict(
    strings=len(strings),
    strings_with_candidate_pointers=sum(bool(s["pointer_candidates"]) for s in strings),
    strings_read=sum(bool(s["observed_readers"]) for s in strings),
    executed_addresses=len(coverage),
    missing_pointer_candidates=len(missing_pointers),
)
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(summary)
