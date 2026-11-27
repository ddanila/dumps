# Philips P2776-family terminal firmware

Firmware for a **Philips P2776-family terminal**, recovered from an Intel D27010
EPROM. It contains NEC V25/V35-family code, terminal emulations, English/German/
French setup screens, diagnostics, and 512 packed 9×16 glyphs. The exact board,
terminal variant, firmware revision and build date have not been established.

The original ROM self-test **passes** when its checksum is evaluated through the
NEC CPU’s memory mapping. Address FFFFFh exposes the IDB register, not the final
EPROM byte; treating the dump as ordinary flat memory produces a false failure.

## Contents

- [d27010.bin](d27010.bin): complete 128 KiB image.
- [Full analysis](analysis/README.md): identification, architecture, startup,
  diagnostics, configuration, fonts, terminal parser, interfaces and limitations.
- [Font atlas](analysis/results/font-atlas.svg): all 512 glyphs, reconstructed
  from the ROM’s own expansion algorithm.
- [Disassembly](analysis/results/disassembly.txt): annotated recursive traversal
  with NEC-specific instructions and explicitly seeded dispatch targets.
- [Execution results](analysis/results/execution.json): original-ROM checksum,
  configuration, parser, reply and font-expansion checks.

## Acquisition

Read on 2026-11-27 with the T48, `27C010@DIP32` profile and electronic ID checking
skipped (`-x`). Contacts passed. Two 131,072-byte reads were identical; 87,098
bytes differ from FFh. No programming or erasing was performed.

The original session remains at
`rom-programmers/sessions/intel-d27010-blank-check-20261127-065441`.
The [reader logs and result](evidence/) are retained unchanged. The programmer
reported its existing firmware/support warnings; matching independent reads
and the firmware’s own checksum provide additional integrity evidence.

SHA-256:
`f8bf2df93c70c01c9f7b4bae5ce335a935d03deb4ba41bec691152e7bc041980`.

## Comparison and status

No match was found among 69 other manifest-listed local images, two public
Philips service-processor ROMs, or four layouts combining those public ROMs.
Those public images are from different hardware. This bounded comparison does
not establish that the firmware is absent from all public collections; see
[comparison results](analysis/results/comparisons.json) and
[reference sources](analysis/reference-sources.json).

Static analysis and focused execution are complete for the scope documented in
the report. This is not a working full-machine emulator or a verified hardware
boot. The other queued chips were not analyzed as part of this investigation.
