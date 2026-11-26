# One more sampled Y bit removes observed gain/phase transition collisions

The existing receive feature takes first-visit `3F8` Y bits 5–7 and
second-visit Y bit 7 at assumed ADC visits 46 and 93. Its four-bit
state transition has two contradictory labels when the 75%-level
fresh-payload runs are combined with the half-quadrant carrier-start
runs: keys `D9` and `9D`. A fixed decision function of only those
four-bit before/after states cannot decode both fixtures exactly.

This screen reruns the real-PROM receiver on the fresh payloads at
75%, 100% and 125% line level in both selector modes, plus the two
half-quadrant fresh-payload streams. It retains the **full Y bytes**
at both capture visits. All eight reconstructed four-bit state
sequences exactly match their earlier saved reports. Among the twelve
unused single-bit extensions tested, three remove every transition
label collision across these eight development runs:

| Extra fifth state bit | Distinct development transition keys | Conflicting keys |
| --- | ---: | ---: |
| First-visit Y bit 4 | 60 | 0 |
| Second-visit Y bit 5 | 57 | 0 |
| Second-visit Y bit 6 | 55 | 0 |

The three rules were **frozen from development data**, then challenged
on separate real-PROM DSC replays of the unchanged controller's
consecutive A4/A5 stream. For every rule and both selectors, all 96
measurable transitions, including the 32 held-out A5 dibits, match
the offered data with **zero wrong and zero unknown** decisions.
The earlier A4-trained four-state map was not used to fill missing
transition keys. Thus one extra observed output bit is sufficient to
make a static transition table work across the tested gain and
half-quadrant phase cases without per-run phase relabeling.

This is a circuit *candidate*, not a found Nokia net. A five-bit state
needs two timed Y captures, state memory, and a before/after decision
function; the photographs do not yet identify their pins or logic.
The 55–60 observed table entries do not prove behavior on the other
possible ten-bit transition keys or other waveforms. Next constrain
the two capture clocks and a photo-compatible latch/logic route, then
freeze one fifth-bit choice and test new payloads, start phases and
levels. C2/C3/G2 remain active; the uncertain wiring is a labelled
hypothesis, not a blocker.

The [development report](results/joint-mask04-12a-fifth-receive-bit.json)
contains all raw Y captures and conflict counts. The
[holdout report](results/joint-mask04-12a-fifth-bit-holdout.json)
contains the independent controller-derived A4/A5 captures, trained
key coverage and decisions. Reproduce from the microcode directory:

```sh
python3 g2/joint_mask04_12a_fifth_receive_bit.py
python3 g2/joint_mask04_12a_fifth_bit_holdout.py
```
