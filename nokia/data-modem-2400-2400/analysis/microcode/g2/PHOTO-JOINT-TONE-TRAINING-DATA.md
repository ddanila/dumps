# One candidate phase path across A1 tone, A2 gate, A3 reversals and A4 data

The [reproducible replay](photo_joint_tone_training_data.py) executes the real
DSC PROMs without resetting the q3 phase loop between four controller states.
For each call/answer selector it runs **1,248,256 microinstructions**, checks
all **312,054** PC129 ROM reads and ALU results, and reconstructs the candidate
DAC codes independently. The [machine-readable result](results/photo-joint-tone-training-data.json)
records the controller frames, sample digest, phase checkpoints and decoder
scores.

The Timer-1-paced 8031 replay gives the following nonempty four-byte frames:

| State | Selector 40 | Selector 60 | Candidate interpretation |
| --- | --- | --- | --- |
| A1 | `80 02 A1 7A` ×11, `80 02 81 7A` ×1, `80 02 C1 7A` ×3519 | same first 12, then `C1` ×3529 | Late `81`/`C1` selects tone; early `A1` selects the data step |
| A2 | `80 02 E8 7A` ×11, `80 02 C8 7A` ×1, `80 02 88 7A` ×72 | same | Candidate capture gate off |
| A3 | `D0 42 A1 BA` ×11, `D0 42 81 BA` ×18, `D0 42 C1 BA` ×4 | `A1` ×11, `81` ×19, `C1` ×4 | Data step, regardless of changing third byte |
| A4 | `D0 42 A1 BA` ×8 | same | Data step |

Some iterations have no new frame (`46` in selector 40 A1, `1` in selector 60
A1 and `1` in selector 40 A3). A missing send leaves the previous latched
word in this candidate model. The controller fixture holds RAM15 positive at
dispatch and uses synthetic receive/status events; these are executed frame
counts under that fixture, not measurements of the board.

Assume the four bytes shift into four CD4094 stages in the tested cascade
order, so logical chip 0 holds the last byte and chip 1 holds the third.
Define `capture = chip1.bit0` and
`tone = capture & chip0.bit6 & ~chip1.bit5`. The candidate D127 input is
`88` when `tone` is true and `B0` otherwise. This is one fixed two-byte
decode over the observed frames. Its gates and wires have **not** been traced.
It selects the tone only after A1's first 11 frames; it does not explain a
physical output gate merely by naming `capture`.

The joined diagnostic stream uses 32 late-A1 tone symbols, 8 A2 capture-off
symbols, 32 A3 symbols sourced from the 8251A's programmed `FF` sync fill,
and the exact 32 segment-2 dibits from the TxRDY-paced controller's nine
shifted bytes. The A4 input begins at shifted-data bit 1, the only tested
start among nine offsets with zero matched-filter errors in both modes in the
[alignment screen](USART-DATA-START-ALIGNMENT.md). The A1/A2 windows are short
diagnostic excerpts, not their full natural durations. A2 continues the
internal phase loop with `B0`; analog silence would require a separate
capture/hold behavior.

The candidate output captures the upper-ROM `129` Y code every 375 visits
and applies each of the 12 photo-B5-compatible DAC bus orders. All 12 yield
a **2,100 Hz peak** in the 256-sample A1 excerpt; the selected order has
`R²(2100)=0.335990` versus `R²(1800)=0.001732`. The 12 tone-fit R² values
span `0.285540–0.359162`, so the code stream is distinctly distorted; a
peak alone is not a compliant answer-tone waveform. The phase after both the
tone and capture-off excerpts is `03`, and A3's first four carrier-relative
phase offsets are `128, 0, 128, 0`. The same uninterrupted trace then gives
**0/62 errors** in both modes for every candidate bus using the external
matched-filter reference decoder. These are conditional DAC-code results,
not recovered bits from the DSC receiver.

The separate [A3→A4 control](PHOTO-SEGMENT1-TO-SEGMENT2-CONTINUOUS.md)
substituted unmodulated `00` for A3 and made 31/62 errors; the
[nine-offset screen](USART-DATA-START-ALIGNMENT.md) made at least 14/62
errors at every start except bit 1. Together they constrain the decoder and
symbol path, but do not establish the TxRDY-to-DSC circuit, the DAC latch
clock and bus, the analog line output, or the physical answer-tone gate.

Next discriminate the output path: use the photographs and PROM edge timing
to propose explicit 74LS273/74LS373 latch-clock and byte-bus routes, then
test whether the same uninterrupted code stream reaches a line-side output
under one fixed clock/gate. Continue independently with receive and echo
paths. Missing continuity is not a G2 blocker; it limits which physical
claims this conditional replay can support.
