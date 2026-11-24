# Continuous 8031 line bytes through a candidate DSC2847 input

The earlier [controller-bit dispatch](CONTROLLER-BIT-DISPATCH.md) executed the
8031 scrambler locally and supplied a fabricated run of 16 zero-data bytes
to DSC2847 D at 38E. This experiment instead takes four byte streams emitted
at USART data address 01 by [12 uninterrupted 8031 main-loop iterations](MAIN-LOOP-SERIAL.md).
Those runs preserve the controller's RAM/SFR state and include its receive,
decode, state-step, frame-send and line-side scrambler paths. The streams
cover both observed state branches and both 23-bit scrambler tap choices.

For the DSC2847 side, bytes are expanded **least-significant bit first**, as
the controller scrambler handles them. One bit is supplied at each D read at
38E in the existing [photo-constrained A/I fixture](PHOTO-FIELDS.md#photo-constrained-startup-and-controller-bit-run),
with initial Q=5. This is an explicit serial-to-D timing and wiring
hypothesis. It is **not** a traced USART-to-DSC2847 net. The four streams are
run separately, then concatenated into one 224-bit microcode execution to
test whether changing controller modes leaves history in the candidate path.

| Controller selector | Port-01 bytes | Bits consumed at 38E | Dispatch groups |
| --- | --- | ---: | ---: |
| 00 | `06 F8 84 1C 90 CF B1 09` | 64 | 64 |
| 20 | `E7 7B 97 DE 79 DB 6B 8E` | 64 | 64 |
| 40 | `F9 07 F8 1C 1C F0` | 48 | 48 |
| 60 | `F8 07 F8 9C 0F C2` | 48 | 48 |
| Concatenated | all 28 bytes above | 224 | 224 |

All five DSC2847 runs are clean and consume their complete prescribed bit
streams. At 38F, each bit selects `(bit−5) mod 256`, consistent with the
fixture's Q=5. The candidate four-word ALU Y group is always `[11,11,6,6]`
for bit 0 and `[11,11,16,16]` for bit 1. For a given current bit, the
reconstructed post-group RAM, Q, flags and stack have **one state** across
every visit, including the concatenated run. Q stays 5. There is no
Am27S31 read after the first dispatch and no advancing phase in this path.

This is a stronger controller-derived negative result than the local
scrambler fixture: the controller stream and its state-dependent mode changes
are executed, then the same microcode path is exercised continuously. It
still only excludes **this** input route, startup and field mapping as a
demonstrated DPSK transmitter. The ALU Y groups have no traced connection to
the physical line-output converter; other paths and mappings remain open.

The [report](results/main-loop-dsp-bridge/report.json) records every byte,
bit count, dispatch count, group and state diversity, and source hashes. The
combined [witness trace](results/main-loop-dsp-bridge/witness-trace.jsonl),
[scenario](results/main-loop-dsp-bridge/witness-scenario.json) and
[mapping](results/main-loop-dsp-bridge/witness-mapping.json) specify the full
controller-to-DSC fixture. Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/main_loop_dsp_bridge.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -p 'test_main_loop_dsp_bridge.py'
```

The controller USART-ready status, timer events and received selector are
diagnostic. The DSC2847 A/I photo routes, ROM enable, dispatch timing and
initial Q are also hypotheses. G2's transmitter, receiver/echo-canceller and
functional routine identification therefore remain outstanding. The next
useful path needs controller-dependent retained phase and a repeatable
physical-output candidate, or a receive/echo update linked to the ADC input.
