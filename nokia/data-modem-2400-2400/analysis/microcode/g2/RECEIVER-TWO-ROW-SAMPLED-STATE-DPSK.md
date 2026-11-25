# Sampled state on the conditional two-row receive path

The alternating 0/2 dispatch fixture sustains the 128-sample ADC stream, and
earlier pulse runs show long-lived input-dependent state. This experiment asks a
narrower question: can a fixed, signal-motivated readout of that state recover
the reference waveform's differential symbols?

`receiver_two_row_sampled_state_dpsk.py` runs the real PROMs under the same
photo-compatible, **untraced** joint mapping and interleaved dispatch fixture as
`receiver_two_row_decision_screen.py`. It captures seven streams, then four
fresh seeded streams. For each 8-bit ADC sample, it inspects the start, center
or end of its 94/93-visit hold, with a phase shift of at most two visits. It
tests Y at 3F8/3F9/3FA, Q and R10–R13 as offset-binary or signed samples. A
separate known-carrier matched filter and differential decoder evaluates those
candidate sample streams. Five symbol lags are checked. This decoder is a
diagnostic instrument, **not** recovered DSC microcode.

Across 1,200 tested readouts, none recovers all 36 training dibits. The best
training choice is offset-binary Y at 3F8, one visit after the end point, with
zero symbol lag: 1/36 training errors and 5/48 holdout errors. On four fresh
16-dibit streams it makes 1, 4, 2 and 4 errors among 12 checked symbols each
(11/48 total). The reference PCM decodes at 0 errors on all these streams.
The tested readout therefore exposes some signal information but does not pass
the receiver criterion. The physical ADC, dispatch and output connections
remain hypotheses; no missing trace blocks the next experiment.

The next useful discriminator is a stateful phase estimator or a different
photo-compatible readout/clock route, with a fresh holdout. It must improve
both held-out dibit decisions and the relation to the executed ROM/ALU state
before being treated as a DSC receive mechanism. Exact parameters, source
hashes and trace digests are in
`results/receiver-two-row-sampled-state-dpsk.json`.
