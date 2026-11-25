# Extended controller polling-loop replay

[`main_loop_long.py`](main_loop_long.py) extends the existing
[`main_loop_probe.c`](main_loop_probe.c) fixture from 12 to 64 uninterrupted
polling-loop iterations without changing the 8031 ROM or its peripheral event
rules. It runs selectors `00`, `20`, `40` and `60`. All four complete with no
emulator errors and return to `1ED3`. Every port-01 byte independently matches
the 23-bit controller scrambler applied to the recorded input and history.
The exact per-iteration state, four-byte frame, line-side source and transmitted
byte are in [the machine-readable report](results/main-loop-long.json).

| Selector bit 6 | State path in 64 iterations | Port-01 bytes | Source bytes | Third frame byte changes |
| --- | --- | ---: | --- | --- |
| 0 (`00`, `20`) | A1×2, A2×2, B8×2, B4×58 | 60 | `00` in B8, then `FF` in B4 | `A1 → 81` at iteration 17; `81 ↔ C1` every four iterations from 18 through 46 |
| 1 (`40`, `60`) | A1×2, A2×2, A3×2, A4×8, A5×32, A6×2, then A3/A4/A5 again | 54 | `FF` in A4, `03` in A5 | `A1 → 81` at 25, `81 → C1` at 26, `C1 → 81` at 30; resets at A6/A3 |

Bit 5 changes the scrambler delay but does not change these state/frame paths.
On the B4 path, the full frame at the repeated toggle is
`D0 47 81 EA` ↔ `D0 47 C1 EA`; on A5 it is
`D0 42 81 BA` ↔ `D0 42 C1 BA`. Thus bit 6 of the third frame byte is a
concrete controller-controlled, repeated toggle to test as a possible DSP
phase-control signal. Its physical destination and meaning are not established.
The line-side port-01 bytes are scrambled and do not themselves demonstrate
the repeated `11` dibits required for the segment-1 reference signature.
The [direct-stream screen](CONTROLLER-SEGMENT1-STREAM-SCREEN.md) now checks
both serial bit orders and both dibit alignments across the full recorded
streams; no identical-dibit run exceeds six symbols. This excludes a direct
32-symbol segment-1 source under those tested groupings.
The [segment-2 comparison](CONTROLLER-SEGMENT2-PATTERN.md) finds an exact
64-bit V.26 ter scrambled-ones pattern in each of the two A4 blocks for both
selector `40` (GPC) and `60` (GPA), beginning at the second bit of A4's
first port-01 byte. That is a positive digital synchronization signature,
not a measured line waveform.

This fixture starts at A0 with specified RAM and USART-ready responses, injects
the same seven receive bytes on every polling pass, and forces timer17's high
bit at each loop boundary. The iteration spacing is therefore **not** a
measured time interval; a four-iteration toggle cannot be assigned a symbol
or phase-reversal rate from this run. The subsequent
[frame-edge experiment](PHOTO-FRAME-TOGGLE-EDGE-PULSE.md) showed conditional
half-turns but placed them 16 symbols apart under its explicit byte/symbol
alignment, too sparse for direct segment-1 reversals. The next test should
seek a controller command or DSC-side pattern source while keeping the frame
destination and analog output route explicit.
