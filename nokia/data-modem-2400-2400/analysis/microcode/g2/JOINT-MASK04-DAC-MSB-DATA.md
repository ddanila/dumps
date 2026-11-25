# The assumed DAC MSB alone carries the tested tone and DPSK data

The [carrier-bin audit](JOINT-MASK04-DAC-BIT-CONTRIBUTIONS.md) found that
the assumed DAC top bit accounts for the exact 2,100/1,800 Hz components
in held-input real-PROM streams. This [follow-up](joint_mask04_dac_msb_data.py)
tests whether the same bit also carries the controller-derived A3→A4
data decisions. It executes the **fixed mask-`04` joint map** for both call
and answer selectors, 1,248,256 PROM microinstructions each, capturing
832 candidate DAC samples per run at both U10 D2 latch phases. The trace,
post-ROM sample and selected-bus hashes match the previous full-PROM
[joint-map edge replay](JOINT-MASK04-TX-PROM-EDGE.md).

For each of six photo-compatible DAC bus orders, the script passes the
complete code, only code bit 7, or only bits 0–6 through the same assumed
1,950 Hz Q=1 bandpass and independent known-carrier reference decoder.
Every surviving bus assigns Am2901 Y7 to code bit 7; on a DAC08 this
would be **B1, pin 5**.

| Signal presented to assumed filter | A1 tone peak | Call A3→A4 errors | Answer A3→A4 errors |
| --- | ---: | ---: | ---: |
| Full candidate DAC code | 2,100 Hz | 0/62 | 0/62 |
| Top bit only (`code & 0x80`) | **2,100 Hz** | **0/62** | **0/62** |
| Lower seven bits only (`code & 0x7F`) | Not used as a tone criterion | 22–23/62 | 22–23/62 |

The result holds for both latch phases and all six bus orders: 24
evaluations of the two executed controller streams. Those repeated cases
share the same top-bit route and are not 24 independent data streams.
The top-bit result narrows the *digital* output hypothesis sharply. A
single Y7→sample latch→DAC08 B1 connection, if present, is sufficient
for the tested tone and reference-decoded A3/A4 transitions after the
assumed filter. The lower bits can still shape the waveform and affect
other conditions; their error count does not show that they are unused
by the physical modem.

The [machine report](results/joint-mask04-dac-msb-data.json) retains
trace/capture hashes and every bus/phase score. Reproduce from the
microcode directory with `python3 g2/joint_mask04_dac_msb_data.py`.
The photos do not establish Y7→latch, the latch clock, DAC08 B1, or the
analog line route. The controller timing is projected onto the DSC
schedule, and the decoder/filter are external diagnostics. This is a
stronger candidate constraint, not a C2 pass or a receiver result.
