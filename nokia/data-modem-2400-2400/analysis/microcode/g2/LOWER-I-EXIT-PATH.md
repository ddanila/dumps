# The D3F8-sensitive loop exit returns to a caller, then stalls under tested timings

The [selected-input experiment](LOWER-I-D3F8-INPUT.md) found that D3F8 bits
can change the `3ED–3FA` loop and cause an exit at `3EE`. The
[exit-path runner](lower_i_exit_path.py) follows that path for a one-visit
impulse and the real 128-bit 8031 scrambler stream on each of D1–D3. It uses
the same read-valid PROM-data hypothesis (I7/A0 from inverted U10 D6,
I0/A1 from U11 D2, lower I6 from U11 D0), Q=5, and 1,580 cycles per run.
The D3F8 source, latch wiring and flag timing are still untraced.

With **previous-flag** timing, the constant-D3F8 control remains in the loop
for all 192 site visits. All six changed-input runs exit. In each, `3FA`
produces zero, `3ED` tests that preceding zero and goes to `3EE`, and `3EE`
returns through the stack to caller `18D`. The caller passes through `270`
once and reaches `1E9/1EA`. Q falls to zero, but the final 256 cycles still
alternate between those two words; `1EA` keeps taking its loop branch. This
tail selects no external D read and reaches none of the fixture's virtual
output capture sites.

| D3F8 lane | Impulse: first `3EE` cycle | 8031 stream: first `3EE` cycle |
| --- | ---: | ---: |
| D1 | 291 | 267 |
| D2 | 243 | 347 |
| D3 | 315 | 467 |

With **current-flag** timing, even the constant control exits at cycle 59
after only two D3F8 visits. It later reaches an `1EC/1ED` poll under the
fixture's default external byte. The three controller-lane runs have exactly
the same full trace digest as that constant control: their changing bits have
not reached the D3F8 site. Four virtual output captures occur on this path,
but they provide no D3F8-dependent sample stream and are not identified
DAC08 input writes.

The [machine report](results/lower-i-exit-path.json) records the exit producer,
branch test, return target, downstream PCs, tail state, virtual captures,
trace digests and source hashes. The comparison identifies a conditional
subroutine exit, not a sustained modulation or receive decision. The next
experiment should change a plausible timing or input route that lets real
controller bits or ADC samples survive into repeated output or decision
events, while keeping the assumed physical connections explicit.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_exit_path.py
```
