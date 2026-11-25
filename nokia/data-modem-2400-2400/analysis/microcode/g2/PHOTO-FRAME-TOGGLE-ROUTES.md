# The observed frame toggle is not a reversal through either held D127 route

The [64-iteration controller replay](MAIN-LOOP-LONG.md) found repeated third
frame bytes `81` and `C1` in B4 and A5. They differ only in bit 6. The
[route screen](photo_frame_toggle_routes.py) takes those actual frames and
tests two already proposed CD4094-to-D127 routes against the unchanged DSC
PROMs, using the `q3` mapping, Q=0 and the upper Am27S31 bank. Each case
executes 3,000 microinstructions, with 740 PC129 ROM/Y visits independently
checked against the recovered phase recurrence. The 640 candidate DAC codes
used for spectral comparison are **projected beyond** those executed visits.

| Third frame byte | Decoded-mode D127 / projected peak | Direct D0/D4-crossing D127 / projected peak |
| --- | --- | --- |
| `A1` | `B0` / 1,800 Hz | `B0` / 1,800 Hz |
| `81` | `88` / 2,100 Hz | `90` / 600 Hz |
| `C1` | `88` / 2,100 Hz | `D0` / 3,000 Hz |

The decoded-mode route ignores bit 6. Its transition from `A1` to `81` is
driven by bit 5 and changes the carrier to 2,100 Hz; subsequent `81`/`C1`
toggles leave it unchanged. The direct crossing passes bit 6 through D127,
but as a **held** input it changes the phase increment and hence the
candidate carrier frequency. Its 600/3,000 Hz alternation is not a 1,800 Hz
carrier with 180° reversals. Thus neither tested held route explains
segment-1 reversals from this frame toggle.

This result does not identify the frame's physical recipient or what B4/A5
mean. A brief edge-qualified pulse, another CD4094 output, or an independent
line-side command path could use the same bit differently. The next useful
test is to find whether bit 6 is sampled transiently at a symbol boundary or
sent elsewhere, and to run a bounded pulse-width/phase screen with the
observed `81`/`C1` sequence as stimulus. Keep the port-01 bitstream and
timer-forcing assumptions explicit. The [machine report](results/photo-frame-toggle-routes.json)
contains the exact controller-frame occurrences, PROM-read checks, projected
spectra and source hashes.
