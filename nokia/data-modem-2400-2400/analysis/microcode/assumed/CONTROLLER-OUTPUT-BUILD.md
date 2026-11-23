# Continuous output construction and immediate override

The unchanged controller ROM executes continuously from 006E through 046A,
stopping at 046C. All four previously studied byte builders compose correctly:
the fourth byte uses the **old** RAM30, the third consumes the raw state code
left in R2, and the first two are built afterward. No register values are
injected between sections and no instructions are skipped.

The [reference](../../controller_output.py) function `output_build` composes
those local references, then models the immediate tail:

- When newly built RAM30 bit 3 is set, rotate RAM3D left once and put the
  rotated byte's bit 7 on P1.3. Otherwise set RAM3D=FF and P1.3=1.
- RAM30 bit 5 similarly controls RAM3E and P1.4.
- P1.5 receives raw state code K bit 1.
- If received byte C (RAM2C) bit 0 is set, OR RAM30 with FE and clear P1.3
  and P1.4. The pattern rotations have already happened and remain stored.

Thus the event-qualified RAM30 bit 2 preserved by its builder can subsequently
be forced high. The reference keeps the scratch byte RAM20 equal to RAM30
**before** this override, matching the ROM. These pin assignments are observed
controller behavior; their electrical destinations and physical timing remain
unidentified. A circular eight-bit pattern repeats after eight active calls
unless another writer changes it.

## Verification and limits

The [scenario](../../controller-output-build-scenario.json) supplies state,
flags, six normalized input bytes, all four prior outputs, three counters,
and both pattern bytes. Register bank zero and disabled interrupts are explicit
local assumptions. The seeded sweep uses 128 combinations for each of all 256
state values: **32,768 comparisons pass**, checking all 128 internal-RAM bytes,
P1, PSW.F0, unchanged stack pointer, and stop PC, with no emulator exceptions.

All 397 reachable instruction starts in this prefix are visited. The two ROM
tables are excluded as data; 00F5 is excluded because the earlier E8-group
branch makes it unreachable, as documented in the fourth-byte study. The
[report](../../results/controller-output-build-study/report.json) stores 24
witnesses, coverage, fixture/execution digests, ROM hash and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_output_build_study.py
```

This is not the complete 006E routine or a complete polling iteration. At
046C the routine proceeds to mode selection at 1CE1 and conditional peripheral
writes via 1D05, then calls 1933, 0C5B and 077C before returning at 04F9.
Those accesses and subsequent effects need their own reference and logged
external assumptions before combining this prefix with serial transmission.
