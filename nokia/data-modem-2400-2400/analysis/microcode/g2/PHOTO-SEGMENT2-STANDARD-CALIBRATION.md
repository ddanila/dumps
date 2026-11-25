# Real controller segment-2 bits calibrate the candidate DSC phase path

The [controller pattern check](CONTROLLER-SEGMENT2-PATTERN.md) found the
exact 64-bit V.26 ter segment-2 GPC and GPA patterns in the A4/A5 port-01
stream. This [PROM replay](photo_segment2_standard_calibration.py) feeds
those recorded bits, grouped into 32 symbols, through two explicit versions
of the earlier four-visit D127 parity/counter pulse. Both use the same
candidate q3 Am2901 mapping, upper PROM bank and 9,600-sample/s Y129
capture. The only difference is which serial bit reaches D127 pulse lane 0
and lane 1.

| Selector / pattern | First serial bit at D127 bit 0 | First serial bit at D127 bit 1 |
| --- | ---: | ---: |
| `40` / GPC | 6 errors / 30 aligned decisions | **0 / 30** |
| `60` / GPA | 8 errors / 30 aligned decisions | **0 / 30** |

Each of the four runs executes **384,256** real-PROM microinstructions and
checks **96,054** PC129 ROM reads and ALU Y values. Reconstructed samples
on the earlier Q4/Q5-swap bus match the executed trace SHA-256 before the
12 photo-B5-compatible candidate bus orders are scored. All 12 give the
same result in each row. With the serial lanes exchanged, the internal
phase offset follows the negative of the standard cumulative phase in all
32 symbols; the candidate DAC output's matched-filter decisions follow
the standard's left-digit-first phase changes. The decoder does not supply
independent decisions for the first and last symbols because of its fixed
sample alignment.

This corrects an input-label ambiguity in the earlier
[dibit replay](PHOTO-MAIN-DIBIT-PULSE.md) and
[DAC bus screen](PHOTO-DAC-BUS-PERMUTATIONS.md). Those experiments grouped
the first serial bit as the **low** digit of a numeric dibit, whereas V.26
ter names it as the **left** digit. Their zero-error counts establish
conditional phase information in that internal labeling; they do not by
themselves establish standard-compliant 90°/270° assignments. The present
run shows one simple **swapped two-lane hypothesis** that gives the correct
segment-2 phase decisions from actual controller bits. It does not prove
the parity gate, bit-lane wiring, DAC clock/bus, pulse shape or analog line
path, so C2 remains open. The
[machine report](results/photo-segment2-standard-calibration.json) retains
all four trace digests, bus scores, symbol offsets and source hashes.
