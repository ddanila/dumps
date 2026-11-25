# Full controller-driven transmit trace under the joint TX/ADC map

The [mask `08` field map](results/joint-upper-source-mask08-mapping.json)
previously kept a changing held `D127` transmitter path and sustained,
upper-nibble-sensitive ADC execution. The [full replay](joint_upper_full_tx_replay.py)
now uses that **same mapping** with both real control-store and Am27S31 PROMs
over the existing uninterrupted A1 tone → A2 silence → A3 `FF` sync → A4
TxD data input sequence. The D127 input sequence comes from the executed
8031 frame and TxRDY fixtures for call selector `40` and answer selector
`60`; the DSC ingress gate and timing are labelled hypotheses.

Each selector completes 1,248,256 DSC microinstructions and 312,054
`PC129` ROM visits. At the hypothetical free-running 9,600-sample/s
Y-to-DAC latch, each produces 832 codes. Both code hashes match the earlier
q3 transmitter replay exactly, including the 2,100 Hz A1 tone candidate
and the A3/A4 data waveform. The independent reference decoder makes
0 errors in 62 A3/A4 decisions for each selector. The [saved report](results/joint-upper-full-tx-replay.json)
records the trace digests, phase milestones, sample hashes and source hashes.

This is a stronger *conditional* compatibility result: one fixed field map
can run the full modeled transmit stream and the previously tested ADC
streams. The high I0/I7 inversion, two slice crosslinks, D127 gate,
high-slice A-pin diagnostic levels, DAC byte order, latch clock, analog
output and receive output routes remain untraced. A q3-identical candidate
sample stream does not establish the physical line waveform. The next test
is to find a receive decision on the same map that generalizes to
nonperiodic inputs, then constrain how it reaches USART RxD and the echo
path.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_full_tx_replay.py
```
