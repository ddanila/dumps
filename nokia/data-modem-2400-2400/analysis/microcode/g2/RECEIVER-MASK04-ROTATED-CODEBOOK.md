# A fixed row-pair lookup cannot absorb 45° carrier rotation

The [codebook replay](receiver_mask04_rotated_codebook.py) asks whether the
executed `3ED` row-0/row-3 bytes at ADC visit 47 contain an unambiguous
phase state under rotated carriers. It runs six complete 192,047-cycle
real-PROM traces: three independent random dibit streams each at 45° and
135°. The independent reference receiver decodes all six. Four trace and
capture hashes match the earlier [rotation screen](RECEIVER-MASK04-CARRIER-PHASE-SCREEN.md).

The diagnostic phase labels come from the known reference waveform phase
plus the alternating 1,800 Hz carrier term at this sample instant. This
label rule exactly matches the prior fixed Boolean phase readout on all
eight nominal fresh traces. The labels are **external ground truth**, not
an executed DSC output. A full-byte pair and a low-nibble pair give the
same state counts in this fixture.

| Frozen lookup trained on seed `5A17` | Training | Two independent streams |
| --- | ---: | ---: |
| 45° table, seven pair states | 0/12 errors, full coverage | **5/24 errors, full coverage** |
| 135° table, six pair states | One conflicting pair; 3/12 decisions unknown | 17/24 decisions unknown |

The conflict is concrete: pair `(F3,F2)` occurs at 45° with two different
reference phase labels in the three traces. At 135° the same pair also has
two labels. No deterministic stateless map from that pair alone can be
correct on all those symbol states. Combining 45° and 135° training traces
with no phase alignment gives six conflicting pair states; allowing every
constant quadrant offset for 135° reduces the minimum to **one** conflict
at offset +1, but does not remove `(F3,F2)`. This offset screen avoids
mistaking a harmless global phase rotation for a receiver failure.

This result narrows the next photo-compatible consumer: a fixed gate or
lookup at one ADC visit is insufficient for the rotated fixtures. A
multi-visit or stateful readout may disambiguate the pair, and a different
input mapping may change the code entirely. No actual U12/U24 wiring,
carrier tracker, symbol clock or USART-01 RxD route is established. C3
remains open and G2 continues without waiting for a continuity trace.
The [machine report](results/receiver-mask04-rotated-codebook.json) records
all pair bytes, phase labels, scores and source hashes. Reproduce from the
microcode directory with
`python3 g2/receiver_mask04_rotated_codebook.py`.
