# Controller frame and line bits select two q3 phase-walk regimes

The [joined runner](photo_127_frame_line_joint.py) offers the unchanged
8031 main-loop's **frame lane 1** at candidate `D127` and its actual
USART-01 line bytes, expanded LSB-first, at candidate `D12C`. It tests all
four representative controller selector classes and holds each line bit
for 1, 4 or 8 visits. The q3 Am2901 mapping, held-I0 circuit, ROM bank,
input routes and relative timing are hypotheses. The frame values are `47`
for selectors `00`/`20` and `42` for selectors `40`/`60`; the latter two
have different controller state branches but the same frame lane.

All 12 real-PROM DSC runs complete 4,200 microinstructions. Every reached
`D127` and `D12C` read selects the offered controller value, and every
`12E` ROM address follows the executed cumulative-sum phase rule. With
`47`, the first loop makes 155 ROM visits, enters `12C`, and consumes the
line bits. With `42`, the first loop makes 1,040 visits in the bounded run;
`12C` is never reached.

| Selector | Frame lane 1 | Line bits / ones | `D12C` visits at hold 1 / 4 / 8 | Hold-8 outcome |
| --- | ---: | ---: | ---: | --- |
| `00` | `47` | 64 / 26 | 884 / 884 / 884 | all 64 bits consumed; phase `D1` |
| `20` | `47` | 64 / 43 | 884 / 884 / 359 | phase reaches `00`, exits to `084` at cycle 2,170 |
| `40` | `42` | 48 / 24 | 0 / 0 / 0 | remains in first loop |
| `60` | `42` | 48 / 24 | 0 / 0 / 0 | remains in first loop |

At shorter holds, both `47` classes consume their full bitstreams and then
read an explicit idle zero. At hold eight, selector `20` presents 43 ones;
the second phase walk reaches zero on its 255th presented one and exits
before the full stream. Selector `00` presents only 26 ones, so eight holds
leave its phase at `D1` and the loop continues. These are consequences of
the executed modulo-256 recurrence, not claims that the physical modem uses
these exact input routes or timing. The
[machine report](results/photo-127-frame-line-joint.json) preserves each
case, selected-input count, phase, wait cycle and trace digest.

No run reaches the candidate `392` or `39E` output sites, and no DAC08 byte
or line waveform has been identified. This is an internal, controller-data-
dependent control-flow witness. The next test must connect a retained or
transient phase/ROM value to a photo-compatible DAC latch or find a different
output path. The negative direct frame-to-D12C tone-step result remains
separate: here the frame at D127 selects which phase loop consumes the
line bits.

The [oscillator-derived hold replay](PHOTO-127-LINE-RATE-HOLDS.md) tests
the same direct bit route at 2,400 bit/s for four candidate microcycle
divisors. The `47` classes exit during the first or second bit; the `42`
classes never enter the second loop. Thus the present joined short-hold
control-flow witness is not a sustained line-rate modulator.
