# Candidate own-transmit echo is not suppressed in the fixed D3F8 fixture

The joint map runs a full controller-derived transmit stream and a separate
ADC-sensitive `D3F8` path. The [echo-feed experiment](joint_upper_echo_feed_probe.py)
connects those two *modeled* paths: it reconstructs the first 128 selected
DAC codes of A4 from the executed call (`40`) or answer (`60`) transmit
trace, verifies the complete code hash against that trace, delays the
samples by three 9,600-Hz sample periods, and scales them by one half.
This is a diagnostic analog echo hypothesis, not a traced board loopback.

The experiment offers the echo as complementary ADC bytes held for
188/187 `D3F8` visits per sample. It also runs a zero-input control, an
independent remote DPSK signal, and remote-plus-echo. All receive runs
complete 24,000 real-PROM ADC visits. The observed byte is `Y3F8` at the
center of each held sample, the same signal-like site from the
[sampled-state screen](JOINT-UPPER-SAMPLED-STATE-DPSK.md). Output change is
measured as a signed modulo-256 difference from the corresponding zero or
remote-only run, then normalized by injected echo RMS in four 32-sample
windows.

| Input comparison | Call `40` output-change / echo RMS | Answer `60` output-change / echo RMS |
| --- | --- | --- |
| Echo-only minus zero | 0.988, 0.959, 0.965, 0.975 | 0.988, 0.959, 0.965, 0.977 |
| Remote-plus-echo minus remote-only | 1.090, 1.044, 1.016, 1.014 | 1.090, 1.044, 1.016, 1.010 |

The change stays close to the injected echo rather than falling to a
small residual. The [saved report](results/joint-upper-echo-feed-probe.json)
includes exact RMS values, inputs, paired trace digests and source hashes.
This excludes a simple, rapidly converging echo-suppression interpretation
of **this fixed `D3F8` fixture and `Y3F8` readout**. It does not rule out
echo cancellation elsewhere in the microprogram or under a controller
training mode: no controller-to-DSC train/freeze connection is identified
here, the A4 window lasts only 128 samples, and the DAC, analog loopback,
ADC and output paths remain assumed. C4 still requires a mode-qualified
training/freeze replay with a justified output site.

Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/joint_upper_echo_feed_probe.py
```
