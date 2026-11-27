# The settled-`12A` DAC candidate peaks at 1,800 Hz under a stationary data input

The [end-to-end run](JOINT-MASK04-END-TO-END-DEMO.md) uses a short,
scrambled 32-dibit payload. Its random-data FFT peak is 1,650 Hz; that
window is not a clean way to measure the carrier frequency. The
[stationary control](joint_mask04_stationary_carrier_control.py) keeps
the same real-PROM mapping, carrier offset 203, 846 candidate samples,
early settled-`12A` output site and six photo-compatible DAC08 byte
orders. It replaces only the D127 data-mode input after segment 1 with
constant `B0`. This is a counterfactual input control, not an executed
8031 TxD payload.

The resulting A1 tone window peaks at **2,100 Hz**, and the stationary
data-mode window peaks at **1,800 Hz on all six candidate DAC buses**.
This matches the executed R1 recurrence: 375 visits of D127=`B0`
advance the eight-bit phase by 208 steps per sample, equivalent to
−48/256 of a cycle at the assumed 9,600 Hz sample clock. The
[source-hashed report](results/joint-mask04-stationary-carrier-control.json)
contains all six code hashes, both spectral peaks and the PROM trace
digest.

The test establishes a frequency signature of the **candidate digital
sample stream** under an explicit stationary condition. It does not
identify the physical DAC08 inputs, analog line node or sample-clock
net, and it does not make the random-data window's peak 1,800 Hz.
C2 and G2 remain open while those physical routes are constrained.
