#!/usr/bin/env python3
"""Check acquisition integrity and independent observable execution outcomes."""

from pathlib import Path
import hashlib
import json
import struct

BASE = Path(__file__).resolve().parent
for line in (BASE.parent / "SHA256SUMS").read_text().splitlines():
    digest, name = line.split(maxsplit=1)
    assert hashlib.sha256((BASE.parent / name).read_bytes()).hexdigest() == digest, name
boot = next(BASE.parent.glob("chip0-*.bin")).read_bytes()
assert boot[0xFFF0:0xFFF5] == bytes.fromhex("ea0000c0ff")
assert sum(boot[0x8002:]) & 65535 == struct.unpack_from("<H", boot, 0x8000)[0] == 0xFEED
expected = {
    "strict": "POST failure",
    "mock": "POST failure",
    "explore": "application terminal fault loop",
    "analog": "application terminal fault loop",
    "format-ab": "application terminal fault loop",
    "continued": "Write to write-protected memory (UC_ERR_WRITE_PROT)",
    "native-return": "Write to write-protected memory (UC_ERR_WRITE_PROT)",
}
summaries = []
for name, reason in expected.items():
    run = BASE / "results" / name
    result = json.loads((run / "result.json").read_text())
    assert result["reason"] == reason, (name, result["reason"])
    assert not result["missing"], (name, result["missing"])
    if name in {"explore", "analog", "format-ab"}:
        code = {"explore": "04", "analog": "09", "format-ab": "AB"}[name]
        assert (
            f"ERR99{code} DO NOT USE" in (run / "display-fault-buffer.txt").read_text()
        )
        coverage = json.loads((run / "coverage.json").read_text())
        assert all(
            str(a) in coverage for a in [0xFFC00, 0xFE65F, 0x7DFC0, 0x76574, 0x3A180]
        )
        # Reset/POST, actual ROM checksum, INT BA runtime, serial send and formatter all execute.
        assert len((run / "tx-bd13.bin").read_bytes()) == 29
        assert (
            (run / "tx-bd13.bin")
            .read_bytes()
            .startswith(bytes.fromhex("7f007f1b1b1b1b1b0c"))
        )
        pages = json.loads((run / "result.json").read_text())["writes_by_4k_page"]
        assert all(
            0x80 <= int(p) < 0xF0 for p in pages
        ), "CPU wrote outside RAM/peripheral window"
    summaries.append(
        {
            "profile": name,
            "reason": reason,
            "steps": result["steps"],
            "unique_instructions": result["unique_instructions"],
            "missing_accesses": len(result["missing"]),
        }
    )
menu = json.loads((BASE / "catalog/option-menu.json").read_text())
assert len(menu) == 26 and all(len(x["label"]) == 36 for x in menu)
assert "VOLUME APNEA PARAMETERS" in menu[0]["label"]
assert "PULSE OXIMETRY MISCELLANEOUS" in menu[-1]["label"]
strings = json.loads((BASE / "catalog/strings.json").read_text())
assert any("26300-85-V" in s["text"] for s in strings)
(BASE / "results/summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
print(
    "Verified: original hashes, reset/checksum, seven outcomes, original-code messages, serial output, ROM protection, option records."
)
