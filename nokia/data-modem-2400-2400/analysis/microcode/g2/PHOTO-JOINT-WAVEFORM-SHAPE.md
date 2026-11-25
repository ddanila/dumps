# Pulse-shaped reference favors the PC129 byte over other ALU sites

Tone frequency and external dibit decisions alone accepted all four Y sites
in the [free-running-clock replay](PHOTO-JOINT-FREE-CLOCK-SITES.md). The
[shape screen](photo_joint_waveform_shape_screen.py) now compares their
**actual full-PROM sample bytes** with an independent 100%-rolloff
raised-cosine reference waveform. It executes both 1,248,256-instruction
joined traces again and verifies all eight site-stream SHA-256 values against
the prior run before fitting. The [result JSON](results/photo-joint-waveform-shape-screen.json)
contains every site/bus/mode fit.

For each of the 12 photo-B5-compatible DAC bus orders, the screen fits the
central 448 samples of the 64-symbol A3→A4 segment. It allows a constant
carrier phase through two quadrature coefficients, either symbol and carrier
orientation, and an integer timing shift of −8…8 samples. It does **not**
fit an analog filter or change the actual dibits. The reference fits itself
to R²≈1 under the same method.

| Candidate | Mean R² across GPC/GPA, best bus for that site |
| --- | ---: |
| Y at `127` or `128` | 0.653 |
| Y at `129` | **0.757** |
| Y at `12A` | 0.608 |

`129` wins for **all 12 fixed bus orders**, by R² margins of about
0.092–0.131 over the best other site with the *same* bus. Its best order maps
Y input bits 0…7 to DAC-code bits `[4, 0, 6, 1, 3, 2, 5, 7]`; it gives
R²=0.761 for GPC and 0.752 for GPA, both at a −4-sample reference shift.
Another order scores 0.756 on average, so the byte permutation remains
ambiguous. All of these orders retain only the photographed **Q4→DAC08 B5**
segment; the other seven data wires are hypotheses.

This is stronger evidence for `129` than the earlier tone/decision checks:
its ROM-selected Y byte has a closer shape to the independently generated
pulse-shaped signal than the phase-accumulator bytes at `127`/`128` or the
`12A` result. The absolute fit is still well below one. It does not show that
the DAC08 actually receives this byte, that the 74LS373/74LS273 clocks have
the assumed timing, or that an analog filter yields the required line
waveform. It also does not demonstrate DSC receive or echo processing.

Next test explicit photo-compatible 74LS373 hold and 74LS273 clock/data
routes against this same byte stream, including the output's analog spectral
shape. Keep alternate sites live until an independent connection or signal
constraint rejects them; C2 remains open.
