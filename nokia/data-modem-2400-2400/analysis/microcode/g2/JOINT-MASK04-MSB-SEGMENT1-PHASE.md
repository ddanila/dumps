# Segment-1 half-turns in executed candidate DAC MSB samples

The [free-clock transmitter replay](JOINT-MASK04-FREE-CLOCK-MSB.md)
found a 2,100 Hz A1 peak and zero reference-decoder errors for the
controller-derived A3/A4 stream, but did not measure segment-1 phase
reversals in the candidate DAC samples. This
[follow-up](joint_mask04_msb_segment1_phase.py) runs the same fixed
mask-`04` map for **1,248,256 real-PROM instructions per call/answer
selector** and captures eight candidate samples per symbol at each
free-clock phase `127`–`12A`. The full trace and sample hashes match the
earlier replay.

For each capture, the script takes the assumed DAC code's MSB alone,
forms a complex phasor from each eight-sample symbol at 2,100 Hz in A1
or 1,800 Hz in A3, and measures the phase difference between adjacent
symbols. It uses raw candidate DAC input bits, without the earlier
assumed analog bandpass or reference decoder.

| Controller selector | Capture phases | A1 adjacent phase | A3 adjacent phase | A3 comparisons |
| --- | --- | --- | --- | ---: |
| Call `40` | `127`, `128`, `129`, `12A` | 0° | ±180° | 31 per phase |
| Answer `60` | `127`, `128`, `129`, `12A` | 0° | ±180° | 31 per phase |

The reported deviations from 0° and 180° are below 5×10⁻¹² degrees,
only floating-point roundoff. The *full-byte* sample hashes differ
across the four phases, while the **MSB sample hash is identical** at
all four phases within each selector. The A1/A3 input schedule is shared
between call and answer, so those two runs are not independent training
patterns. Their A4 data differs and the full PROM traces are separately
checked.

This is a direct digital witness for the proposed segment-1 180°
reversals in an executed DSC output bit, alongside the earlier A1 tone
and A3/A4 data checks. It is conditional on the candidate Y7→latch→DAC08
B1/pin-5 route and the 9,600-sample/s timing hypothesis. The photo does
not verify that bit's wiring, the latch clock, current-output conversion,
filter or line connector. Thus it narrows C2's output behavior but does
not identify a measured line signal or pass C2. Test the photo-compatible
B1/latch route or an independent analog-output constraint next; missing
continuity is not a reason to stop the runnable candidates.

The [machine report](results/joint-mask04-msb-segment1-phase.json) contains
248 A1 and 248 A3 adjacent-angle measurements, trace and sample hashes, and source
hashes. Reproduce from the microcode directory with
`python3 g2/joint_mask04_msb_segment1_phase.py`.
