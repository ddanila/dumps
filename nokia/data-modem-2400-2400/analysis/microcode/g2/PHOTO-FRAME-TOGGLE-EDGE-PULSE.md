# A two-visit edge pulse retains a half-turn in the PROM phase state

The two held-byte routes in [the previous screen](PHOTO-FRAME-TOGGLE-ROUTES.md)
do not turn the observed frame-bit toggle into a 1,800 Hz phase reversal.
This [bounded counterexample](photo_frame_toggle_edge_pulse.py) tests an
explicit **transient** alternative. The photographed SN74LS280 parity part
could compare successive frame-bit values and U24 74LS161 could limit a
pulse, but their relevant nets are untraced. The scenario adds D127 bit 6
for two PC127 visits at each change of the third frame byte's bit 6, while
retaining the previously tested four-visit dibit pulses from real port-01
bytes. It does not assert that those parts actually implement the gate.

The unchanged 8031 ROM supplies selector-`00` B4 iterations 18–25:
four `D0 47 C1 EA` frames followed by four `D0 47 81 EA` frames. Their eight
port-01 bytes are `F8 4F 0F 3C 65 08 F5 EC`, or 32 LSB-first dibits. The
observed frame edges map to candidate symbols 0 and 16 under the explicit
one-byte/four-symbol alignment. The 8031 run forces timer expiry each
iteration, so this alignment and edge spacing are diagnostic assumptions,
not natural segment-1 timing.
Under this alignment, the two edges cannot directly supply the continuous
180° reversal at every one of 32 symbol intervals required by
[ITU-T V.26 ter §2.7.1](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I%21%21PDF-E&lang=e&type=items).
The [separate repeated-dibit replay](PHOTO-SEGMENT1-REPEATED-DIBIT.md)
tests that required cadence without assigning it to B4.

The DSC emulator runs the same 32 dibits twice, once with frame bit 6 held
fixed for the edge gate and once with the two pulses. Each run executes
384,256 microinstructions without an error and independently checks 96,054
selected PC129 ROM addresses, bytes and ALU Y results. Relative to the
fixed-bit control, the pulse run ends symbols 0–15 **128/256 phase-index
steps away**, then returns to zero offset for symbols 16–31 after the second
pulse. The candidate DAC samples after the second pulse's first sample
match the control exactly. Over the first 16 symbols, the signed correlation
between candidate DAC-code sequences is −0.644; this bus projection is not
an ideal inverted sine. A width screen of 1–4 visits gives offsets 64, 128,
192 and 0, so only two visits produce the required half-turn under this
particular D127-bit rule.

This shows a **conditional mechanism** in the running microprogram: a brief
input change can rotate its retained phase state while the dibit-driven
carrier continues. It does not identify B4 as segment 1, demonstrate a
physical edge detector or clock, prove pulse shaping, or establish the
DAC-to-line path. The next check should constrain the frame bit's actual
destination or an independently supported timing rule, then repeat the
reversal and 2,100 Hz tests on the same board mapping. The exact phase
checkpoints, codes, digests and source hashes are in the
[machine report](results/photo-frame-toggle-edge-pulse.json).
