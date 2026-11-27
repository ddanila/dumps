# Matched-gain two-bit receive challenge and gate screen

The [33-code two-bit phase lookup](JOINT-MASK04-12A-TWO-BIT-PHASE-HOLDOUT.md)
passed four real-PROM/controller streams at 0.75× receive gain. This test
reruns the **same carrier starts and controller payloads** at calibrated
1.0× gain. The transmitter trace hashes agree pairwise, while the
receive PCM and PROM traces change, isolating the receiver-gain input.

| Frozen table | Carrier starts | New nine-bit keys | Wrong transitions between known keys | Clipping |
| --- | --- | --- | ---: | ---: |
| 33 codes | `149`, `151` | `015`, `04C`, `1C8` in each of four streams | 0 in each | 0 |
| 36 codes | fresh `153`, `155` | `05C` in each of four streams | 0 in each | 0 |

The first four calibrated-gain streams add three consistently constrained
phase labels (`015→1`, `04C→3`, `1C8→0`) to the 34-stream graph. All four
then replay exact modeled line and executed controller bytes, but that is
**development evidence**: those streams supplied the labels. The resulting
36-code table was frozen before new payloads at `153`/`155`. Each new
stream reaches `05C`, so the frozen table again refuses to classify the
full stream. Joining these four streams gives one 37-code graph with zero
conflicts and constrains `05C→3`; its exact line/controller replay is
again development evidence, not an independent pass. The 1.0× independent
holdout thus shows correct known-state transitions, but incomplete state
coverage. It does not establish a functioning frozen 1.0× receiver.

The [observed-state logic screen](results/joint-mask04-12a-two-bit-logic-screen.json)
enumerates all nine-input product cubes that avoid wrong labels and finds
minimum sum-of-products covers for both phase bits under all four global
phase offsets. The first phase bit requires at least **five products**
at offsets 1/3 and six at offsets 0/2. The second needs as few as two
products at offset 3. For example, one offset-3 fit on the 37 observed
keys is:

```text
P0 = (s1 & ~s3) | (~s0 & ~s1 & ~s6) |
     (s2 & ~s5 & s7) | (~s0 & ~s1 & ~s2 & s8) |
     (~s2 & ~s7 & ~s8)
P1 = ~s2 | (s6 & ~s7)
```

Here `s0`–`s6` are the earlier seven-bit state, `s7` is row-0 Y1 at
visit `46`, and `s8` is `3F8` Y4 at visit `94`. The photographed U15
S64 has four AOI products, so a **single direct U15 output cannot
implement P0** even with all unobserved keys treated as don't-cares.
A multistage route using other photographed gates remains to test.
These equations are an observed-state fit only; 475 of 512 nine-bit keys
are unconstrained, and no physical net or gate delay is established.

Reproduce the raw challenges with
`joint_mask04_12a_two_bit_gain1_matched.py` and
`joint_mask04_12a_two_bit_gain1_frozen36.py`. The saved-data graph and
controller replays use `joint_mask04_12a_two_bit_gain1_extension.py` and
`joint_mask04_12a_two_bit_gain1_frozen36_audit.py`. The logic enumeration
uses `joint_mask04_12a_two_bit_logic_screen.py`. Their corresponding
source-hashed JSON reports are under `results/` with matching stems.

Next freeze the 37-code table for new calibrated-gain data and try a
multistage gate/capture implementation within the photographed package
budget. Keep C3/G2 active and the analog/serial nets as explicit
assumptions.
