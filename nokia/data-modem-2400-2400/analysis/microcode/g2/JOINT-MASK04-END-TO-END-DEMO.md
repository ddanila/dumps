# One executable conditional transmit-to-receive modem chain

The [single-run demonstration](joint_mask04_end_to_end_demo.py) joins the
previously separate transmitter and receiver results for call selector
`40`, payload `3B D6 81 4F A9 02 75 EC`, carrier offset 203 and 0.85×
receive level. The 8031's scrambler routine is **executed locally** for
each source byte with carried history. Its line octets are
`39 A3 AF 06 78 1A D5 8A`, exactly matching the independent scrambler
model. A one-symbol buffered TxD-pair hypothesis presents those bits to
the DSC D127 input; a full paced 8251 transmit/main-loop execution is
not part of this run.

The joint mask-`04` emulator executes the real control and table PROMs,
producing 846 candidate `12A` samples. A selected photo-compatible
DAC08 byte order, modeled A2 mute and Q=0.5 line filter produce the
receive waveform. Its A1 tone window peaks at **2,100 Hz**. The short
segment-1 window peaks at 2,400 Hz while its symbols impose 180° phase
reversals; the short random-data window peaks at 1,650 Hz. Those FFT
bins do **not** establish the 1,800 Hz stationary data-mode line peak
required by C2. A separate [stationary D127=`B0` control](JOINT-MASK04-STATIONARY-CARRIER-CONTROL.md)
does peak at 1,800 Hz on all six candidate DAC bus orders. The DAC
pins, analog output/filter and actual sample clock remain assumed.

The modeled waveform is quantized for the assumed ADC input without
clipping. A separate known-carrier reference decoder misses dibit 40;
the frozen thirteen-bit phase witness makes **zero** wrong decisions.
The real PROM receiver supplies 65 captured symbols and the modeled
capture/phase/serial circuit presents the recovered bits to a paced
8251 receive model. The unchanged 8031 receive routine descrambles
`39 A3 AF 06 78 1A D5 8A` back to the original eight payload bytes,
with zero modeled status errors. The output trace and PCM hashes match
the previously saved untouched offset-203 holdout.

The [source-hashed machine report](results/joint-mask04-end-to-end-demo.json)
records both PROM trace digests, line samples, reference and frozen-gate
decisions, recovered line bytes and 8031 bytes. Reproduce from the
microcode directory with `python3 g2/joint_mask04_end_to_end_demo.py`.
This demonstrates what the **conditional** joint mapping can do end to
end. It does not identify the board's DAC/ADC/USART nets, verify the
analog line or instantiate the thirteen-bit gate in photographed logic;
C2, C3 and G2 remain open. An independent pin/line constraint is next
for C2, while a package-budgeted
receive gate and serial path are next for C3.

The later [paced A4 challenge](JOINT-MASK04-PACED-A4-THIRTEENBIT.md) replaces
the generated transmit octets with the controller/8251 model's actual
shifted TxD stream for call and answer. Both pass the same frozen
thirteen-bit receive route under the stated board assumptions.
