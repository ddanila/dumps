# Held-I0 candidate exposes a D-driven ROM walk

The [photo constraints](PHOTO-FIELDS.md) suggest U10's active-low E2 signal
near U5 D0, with U5 Q0 approaching U2 I0, and the E2-side net approaching
U2 A1. The simple [capture-edge check](PHOTO-ENABLE-TIMING.md#capture-edge-check)
cannot latch E2 high together with valid U10 data on one edge. A separate
hold path or another I0 driver would be needed. The experiments here therefore
use a **timing hypothesis**, not recovered board wiring: U10 reads with E2=0,
U2 A1=0, while U2 I0 retains an earlier 1. U11 E4 and the U2 I7/A0 candidate
remain high. The controller-to-D38E and ROM-enable routes are also assumed.

[`photo_i0_hold_screen.py`](photo_i0_hold_screen.py) runs all 256 startup Q
bytes for 512 real-PROM instructions under each of five photo-constrained
Am2901 mappings, then supplies 128 bits produced by the unchanged 8031 ROM
to D38E at Q=5. Every mapping has 32 Q seeds that reach the recurring input.
In the Q=5 controller runs, all bits are consumed and ROM operands are selected
at 389, 38A and 38C on 127 visits each. **Each site reads only one address
throughout the run**; the four-word group after the first bit has one fixed
pattern per current bit in q1–q4. The fitted-swapped variant has two patterns
for each bit. These runs show neither a changing carrier lookup nor a physical
DAC sample stream. The [full report](results/photo-i0-hold-screen.json) retains
the per-mapping startup classes, addresses, group patterns and trace digests.

The Q=0 startup class is different. With the original scenario's stub byte
`D127=1`, q3 and q4 make **118 selected ROM reads at 129 with 118 distinct
addresses** in 512 instructions. q1 and q2 repeatedly read one address there;
fitted-swapped takes another path. A changing address alone looked promising,
so [`photo_127_rom_walk.py`](photo_127_rom_walk.py) varied the byte supplied at
127 while keeping the same real PROMs and q3 mapping. At the *n*th 129 visit,
starting with *n*=1, the executed address obeys exactly:

`0x100 + ((3 + sum(D127[1..n])) mod 256)`.

| Held D127 byte | 129 reads in 2,048 cycles | Distinct addresses | Result |
| ---: | ---: | ---: | --- |
| 0 | 502 | 1 | Fixed lookup at 103 |
| 1 | 253 | 253 | Walks 104…1FF, then 100 and exits the loop |
| 2 | 502 | 128 | Visits alternate low-byte positions |
| 3 | 255 | 255 | Walks in steps of three, then reaches 100 |
| 4 | 502 | 64 | Visits every fourth low-byte position |
| 16 | 502 | 16 | Visits sixteen positions |
| 255 | 3 | 3 | Reaches 100 on the third read |

Changing the other recurring D input at 12A between 0, 1 and 3 while holding
D127=1 leaves the 129 address walk unchanged in three 512-cycle runs. This
isolates the tested index update to D127 under this mapping.

Feeding the actual 128 controller-derived bits to hypothetical D127 makes
the address follow their cumulative number of 1s. Reversing bit order changes
the trace, although both streams end at address 13C after 128 bits because
they contain the same number of 1s. The [saved recurrence report](results/photo-127-rom-walk.json)
includes the input order, addresses, ROM values, run digests and source hashes.

This identifies a **D-driven ROM-index recurrence in the declared emulator
fixture**. The earlier 118 changing addresses came from the scenario's
constant-one D stub, not an established oscillator or controller connection.
The loop may be useful for a table walk, but its physical D source, output
route, sample timing and role in the modem are unresolved. It does not meet
G2's transmitter or receiver checks.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_i0_hold_screen.py
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_127_rom_walk.py
```
