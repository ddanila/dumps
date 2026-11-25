# One controller frame bit is a candidate A2 DAC hold gate

The fixed mask-`04` transmit map continues to produce changing DAC candidate
codes during A2. Its [PROM-edge replay](JOINT-MASK04-TX-PROM-EDGE.md) found
that holding the last A1 code would make the assumed filtered line quiet,
but did not identify a signal that could hold it. This
[controller test](controller_a2_latch_gate.py) runs the unchanged 8031 ROM
through A1→A2→A3→A4 with Timer 1 pacing, reconstructs the held four-byte
CD4094 frame after each send, and screens all 32 frame bits for the required
high–low–high state pattern.

| Selector | A1 held third bytes | A2 held third bytes | A3 held third bytes | A4 held third byte |
| --- | --- | --- | --- | --- |
| `40` | `81 A1 C1` | `88 C8 E8` | `81 A1 C1` | `A1` |
| `60` | `81 A1 C1` | `88 C8 E8` | `81 A1 C1` | `A1` |

Across 3,577/3,542 A1, 84 A2, 34 A3 and eight A4 iterations per selector,
**third-frame-byte bit 0 is the only frame bit** that stays high in A1/A3/A4
and low in A2. The photographed [74LS373 near the DAC section](DAC08-OUTPUT.md)
is a pin-compatible candidate consumer. [TI's SN74LS373 datasheet](https://www.ti.com/lit/ds/symlink/sn74ls373.pdf)
states that its Q outputs follow D while C/LE pin 11 is high and hold the
last D level when C/LE goes low, provided OC pin 1 keeps outputs enabled.
Connecting this CD4094 bit to C/LE could therefore hold a candidate DAC
code during A2 without adding a state decoder. **That connection is assumed,
not traced.** The 74LS373 data route to the DAC or 74LS273 also remains
unknown.

The script joins this executed controller result to the saved real-PROM DAC
screen. Across two selectors, six photo-compatible DAC bus orders and two
PROM-edge latch phases, passing the changing A2 codes gives late-A2 RMS
**0.998245–0.998451** of late-A1 RMS under the assumed bandpass. Holding the
last A1 code gives **0.000000** at the reported precision, with **0/1,488**
post-A2 data-decision errors. This is a concrete candidate control-to-output
mechanism for the silence interval, not proof that the Nokia board uses it.

The controller uses synthetic receive/status events and holds RAM15 positive
at state dispatch. The DAC numbers reuse an earlier executed PROM trace; this
script does not co-simulate controller and DSC clocks. The 74LS373 LE net,
data bus, 74LS273 strobe, DAC08 bus, analog filter and line route remain
unverified. C2 and G2 stay open. Next, test the bit-to-LE gate on a single
continuous controller/PROM time base with the existing tone, A2, reversal
and data controls; a failed result would reject this wiring/timing candidate,
not block G2.

The [machine report](results/controller-a2-latch-gate.json) records all
observed frames and the 24 DAC comparisons. Reproduce from the microcode
directory with `python3 g2/controller_a2_latch_gate.py`.
