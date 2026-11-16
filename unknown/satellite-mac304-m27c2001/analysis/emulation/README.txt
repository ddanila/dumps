MAC 3.04 satellite firmware execution harness
===========================================
Portable source package. No compiled executables are distributed; the acquired ROM is two directories above.
Requirements: a C compiler (cc), POSIX shell, Python 3 standard library.
Nothing writes to the input ROM. Build products stay in build/; results go to --out. All peripheral activity
is simulated locally. No receiver, smart card, RF hardware or account is used.

Quick reproduction (ROM path may be relative):
  python3 run_all.py --rom /path/to/mac304-m27c2001.bin --out /tmp/sat-reproduced

Single run:
  ./build.sh
  python3 run.py --rom ../../mac304-m27c2001.bin --out /tmp/sat-reset --mock 5

The full suite takes roughly one to several minutes depending on host.
It transiently creates large per-case traces in OUT/details, then retains
compact JSON, selected gzipped traces and the HTML gallery. Use --keep-details
for all raw logs/memory snapshots. Evidence gzip headers use mtime=0.
The runner requires this firmware SHA-256:
8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a

Open output/gallery/index.html directly in a browser; no server required.
output/gallery/frames.txt is readable text; frames.json preserves exact
bytes per row and separate OSD memory pages. This is NOT pixel-accurate
font/video emulation. Control bytes use a placeholder in the visual preview.
output/SUMMARY.json and output/results/*.json are the test results.
The parent analysis report (../README.md) explains evidence, mocks and limitations.

Reproduction modes (cumulative):
0: banked ROM and RAM only, no external I2C master.
1: emulate I2C slave-transmit completion, no reply packet.
2: reply 84 followed by seven zero bytes (deliberately incorrect length).
3: reply 84 40 00 (passes initial status request; not other transactions).
4: synthetic adaptive reply: command and length copied from firmware's wait
   mailbox. This is a path-exploration oracle, NOT protocol validation.
5: mode4 plus P1.0 input low, so bit-banged IMbus reads return zero, including
   ready/busy status. Full firmware bit-banging still executes.

Call files: one line per call, six hexadecimal fields plus optional decimal
wait ticks before that call:
  BANK ENTRY R7 R5 R6 LANGUAGE [DELAY_TICKS]
Example, initialize national subset and draw French main menu:
  2 abf1 0 0 0 7
  0 c9ee 0 0 0 7
Then:
  python3 run.py --rom ROM.bin --out /tmp/menu --calls calls.txt

Calls are injected at bank0:FEEA after real reset/startup and >4,000,000 ticks,
through firmware far-call wrapper07C5, returning to a harness sentinel010A.
CPU instructions are never skipped. X7447 is seeded before each call;
ABF1/AADC executes the OSD national-subset initialization in screen tests.
The full persistent language setter ED89 (including settings I/O) is not used.
--set-xram HEXADDR=HEXBYTE,... records explicit fixtures before each call.
Do not use a fabricated field value as evidence of real hardware state.

Exit codes: 0 normal completion; 1 malformed input/call plan; 2 illegal
opcode; 3 invalid bank; 4 call plan unfinished at tick limit. Reset-only
runs intentionally finish after a finite budget. Full suite expects code4
for five power-down actions and asserts their final PCON=02 classification.
It requires exact planned return counts for ordinary call plans.

Artifacts from a detailed run:
- trace.log: first execution of each bank-aware PC, I/O samples, bank changes,
  I2C status injections, CALL/RETURN/END state. Not a complete instruction log.
- coverage.tsv: actual opcode dispatch counts, common region0; banks0..3
  represented as regions1..4. A PC alias in another bank is a separate entry.
- screen-NNNN.bin: persistent 64KiB OSD address snapshot after each return.
- call-NNNN.bin: only the ordered OSD data-byte write stream for that call.
- osd-writes.tsv: tick/address/value, includes boot and calls.
- language-slots.tsv: tick/call-index/hook-PC/language/pointer-tag/slot.
- imbus-writes.tsv: semantic register-write entry observations.
- settings-writes.tsv: setting ID, pointer metadata and every outgoing byte.
  These are observed requests, not proven writes to physical EEPROM.
- xram.bin / iram.bin: final memory snapshots (IRAM includes SFR image).

Core provenance: emu8051/ contains five MIT upstream source/license files.
UPSTREAM.json pins commit and original/modified SHA256 hashes. core-fixes.patch
contains stack, instruction timing and optional instrumentation changes.
The supplied core regression test checks upper-IRAM stack isolation and
one/two-cycle timing. This is not an exhaustive 8051 conformance suite.

Source test specs service-tests.json and catalog-index.json were supplied
by independent static analysis during this task. Their predictions are
compared with execution; static specifications alone are not test passes.
