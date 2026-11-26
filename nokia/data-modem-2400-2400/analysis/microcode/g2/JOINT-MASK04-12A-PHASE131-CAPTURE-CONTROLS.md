# Capture-wire and adjacent-visit controls for the gain failure

The [gain sweep](JOINT-MASK04-12A-MODE-PHASE131-GAIN-SWEEP.md) localized
the frozen package circuit's errors to phase bit 0 at candidate states
`48` and `2F`. These controls ask whether a simple mischosen capture
wire or one-visit edge explains the failure before changing the gate
equations. They use saved or rerun **real-PROM** receiver captures under
the same assumed `D3EB` mode and DAC/line/ADC route.

The [single-wire screen](joint_mask04_12a_phase131_single_wire_screen.py)
replaces exactly one of the seven captured bits with any bit of Y3F8
or row-0 Y at visit `46` or `93`, in either polarity. That is **448**
candidate substitutions. It replays the frozen circuit on 16 prior
call/answer cases (1,024 dibits) and six higher-gain cases (384 dibits).
The original route has zero prior errors and 72 higher-gain errors.
All **137** substitutions that preserve zero prior errors still have
72 higher-gain errors. The best total score from any substitution is
66 errors, but it moves all 66 into previously passing runs. No
single available wire substitution repairs the combined evidence.

The [adjacent-capture run](joint_mask04_12a_phase131_adjacent_capture.py)
re-executes both real-PROM receivers on the exact saved, **unclipped**
1.150× PCM. It retains Y3F8 and row-0 Y at visits `46`, `47`, `93`
and `94`; the complete receiver trace, PC path and raw gate edges match
the original 1.150× run. The frozen circuit then screens all eight
choices of first Y visit `46/47`, second Y visit `93/94` and row-0
visit `46/47`. Each choice has **12/64 call and 11/64 answer errors at
identical decision indices**. The state codes do change for some
choices, but a one-visit shift in these capture groups does not fix
the readout.

The [single-wire report](results/joint-mask04-12a-phase131-single-wire-screen.json)
and [adjacent-visit report](results/joint-mask04-12a-phase131-adjacent-capture.json)
save the candidate counts, real-PROM run hashes, captured states,
decision indices and limitations. Reproduce from the microcode
directory with:

```sh
python3 g2/joint_mask04_12a_phase131_single_wire_screen.py
python3 g2/joint_mask04_12a_phase131_adjacent_capture.py
```

These controls reject only the stated one-wire and one-visit changes.
The board's actual latch and serial connections are still untraced;
earlier or later capture sites and multiwire preprocessing remain
possible. C3 and G2 stay open. The next experiment is a labelled
multistage phase-bit-0 correction targeted at `48` and `2F`, followed
by a fresh real-PROM gain/phase holdout. Keep any extra gate or net as
an explicit photo-compatible assumption.
