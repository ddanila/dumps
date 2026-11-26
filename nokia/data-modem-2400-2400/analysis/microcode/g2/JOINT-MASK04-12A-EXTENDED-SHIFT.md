# Extending the `12A` line tail does not fix the call decision

The [buffered-line replay](JOINT-MASK04-12A-BUFFERED-LINE.md) found one
wrong call dibit at +6 samples, its largest available positive offset.
This [follow-up](joint_mask04_12a_extended_shift.py) holds the last
offered data value for six more candidate DAC samples, then tests +4
through +12 on the same six photo-compatible bus orders. It retains the
same real-PROM transmitter, A2 mid-code gate, analog filter and
known-carrier reference decoder.

The original 846 `12A` bytes match their saved SHA-256 in both selector
modes. For +4 through +6, the PCM hashes, wrong counts and wrong indices
also match the saved replay. At +6, all six buses give **1/64 wrong call**
(index 35) and **0/64 wrong answer** dibits. At +7, four buses give one
wrong call dibit (index 46), while two give two (indices 46 and 51);
no bus gives an exact call result. Offsets +8 through +12 increase the
call error count to at least 7. The extended tail therefore excludes a
later whole-sample window as the sole repair for this fixture.

The next C2 test should vary a photo-compatible latch phase or analog
gain/filter route and check independent data, while retaining the
existing assumed DAC bus and gate controls. This experiment does not
identify the physical line circuit or the DSC receive/USART decision
path; C2/C3 remain open and G2 active.

The [machine report](results/joint-mask04-12a-extended-shift.json) has
all bus/offset decisions and hashes. Reproduce with
`python3 g2/joint_mask04_12a_extended_shift.py`.
