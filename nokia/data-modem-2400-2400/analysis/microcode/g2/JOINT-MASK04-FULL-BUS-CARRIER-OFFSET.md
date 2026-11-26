# Carrier-offset challenge for the full-byte Tx→Rx candidate

The [non-zero AGC holdout](JOINT-MASK04-FULL-BUS-AGC-HOLDOUT.md) showed exact
line-byte recovery under two payloads and affine level changes. This test
keeps its full-byte DAC order `[4,0,6,1,3,2,5,7]`, `127` sample site,
Q=1 line filter, 128-sample preamble AGC target and fixed-first receive
readout. It shifts the **modeled analog carrier** by −7 or +7 Hz using a
fixed 63-sample-radius Hilbert FIR and complex rotation. Relative phase is
zero at A3 start. The per-stream DAC-to-PCM gain stays at its nominal value;
the first 128 A3 samples are still uncorrected. No receiver table, capture
visit, threshold or calibration target is fitted to the offset cases.

The zero-offset PCM reproduces the saved full-byte waveform exactly for
both selectors. The repeated real-PROM transmitter Y7 hashes match the
earlier non-zero streams. Each of the six cases then executes 780,047
real-PROM receive instructions. The independent reference receiver decodes
all 64 differential decisions in every case without error.

| Selector | Offset | Frozen 46/93 wrong/unknown data dibits | Margin wrong/unknown | Fixed-first wrong/unknown | Exact eight bytes? |
| --- | ---: | ---: | ---: | ---: | --- |
| `40` call | −7 Hz | 0/5 | 2/1 | 1/1 | No |
| `40` call | 0 Hz | 0/2 | 0/0 | 0/0 | Yes |
| `40` call | +7 Hz | 0/7 | 2/0 | 2/0 | No |
| `60` answer | −7 Hz | 0/6 | 0/0 | 0/0 | Yes |
| `60` answer | 0 Hz | 0/9 | 1/0 | 0/0 | Yes |
| `60` answer | +7 Hz | 0/5 | 2/2 | 1/2 | No |

The fixed `46/93` rule makes **no wrong data decision** in this fixture,
but its abstentions vary with offset. The frozen margin fallback fills some
of them incorrectly; call fails at both offsets and answer fails at +7 Hz.
At call −7 Hz, one data dibit remains unknown. Thus the prior exact-byte
result does not establish ±7 Hz tolerance for the proposed external
decision rule. The negative result is specific to this assumed analog
shift, phase alignment, ADC timing and fixed-first readout. It does not
show that the DSC PROMs or Nokia modem lack carrier tracking.

Next, test a phase-aware decision or capture-clock hypothesis against these
saved shifted streams, using the real PROM Y bytes and controls. Freeze any
new rule before trying a fresh payload or phase start. The converter, AGC,
tracking and USART circuits are still untraced; C2/C3 remain open and G2
active under the [working blocker rule](../PLAN.md#uncertainty-is-a-reason-to-experiment-not-a-goal-blocker).

Run `python3 g2/joint_mask04_full_bus_carrier_offset.py` from the microcode
directory. The [machine report](results/joint-mask04-full-bus-carrier-offset.json)
records source hashes, PROM trace digests, ADC hashes, all tested visit-pair
scores, wrong/unknown indices and recovered bytes.
