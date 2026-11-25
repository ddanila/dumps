# State-indexed counter generates the observed frame-bit toggles

The extended [counter probe](main_loop_counter_long.py) runs the unchanged
8031 ROM through 64 uninterrupted polling iterations for each selector
`00`, `20`, `40` and `60`. It instruments the existing output-byte builder at
PC `012F` and `0266`, using the same synthetic receive, ready-status and
timer-expiry events as the [long frame replay](MAIN-LOOP-LONG.md). All 256
builder executions match the independently checked
[`output32` reference](../../controller/OUTPUT32.md) for RAM32, RAM49, RAM4A
and RAM65; RAM32 also equals the third serial frame byte in every iteration.

After the initial flag24.5 reload of RAM49 to ten and its countdown, the
controller loads a new value from ROM address `01BE + (state AND 3F)` and
rotates the table byte left twice. The relevant observed cases are:

| State | Table address / byte | RAM49 reload | Third-byte bit-6 toggle iterations | Count |
| --- | --- | ---: | --- | ---: |
| A1 | `01DF` / `01` | 4 | Earlier [held-A1 fixture](A1-COUNTER-PHASE.md) only | — |
| B4 (`00`, `20`) | `01F2` / `08` | 32 | 18, 22, 26, 30, 34, 38, 42, 46 | 8 |
| A5 (`40`, `60`) | `01E3` / `02` | 8 | 26, 30 | 2 |

For B4 the reload occurs at iteration 17, with RAM49 going `0→32` and
frame byte `A1→81`. The next build decrements to 31 and flips bit 6,
giving `C1`; subsequent flips occur whenever the decremented counter's low
two bits are `11`. A5 similarly reloads `0→8` at iteration 25, then flips
at 26 and 30. This explains both the four-build spacing and the finite
number of toggles from actual controller instructions and ROM data. The
`20` and `60` selector variants alter scrambler delay, not these counter
trajectories.

This strengthens the controller-to-DSP command candidate: bit 6 is a
deliberate, state-dependent finite pattern, rather than a random side effect
of the USART data. It does **not** show what receives the frame or what the
pattern means. The polling fixture forces timer underflow and seven receive
events per iteration; an output build has no measured duration here. The
previous [two-visit DSC edge-pulse replay](PHOTO-FRAME-TOGGLE-EDGE-PULSE.md)
remains a conditional mechanism, not a demonstrated physical connection.
The next useful check is to identify the serial-frame recipient or constrain
how this bit is sampled, then compare the resulting reversal spacing with
the V.26 ter operating sequence. The [machine report](results/main-loop-counter-long.json)
retains every builder input/output, action, table byte, selector and source
hash.
