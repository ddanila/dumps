# Three diagnostic nibble encodings carry all 128 controller bits into the ROM loop

The [held-byte classification](LOWER-I-HELD-NIBBLE-CYCLES.md) found ten
D3F8 low nibbles that individually sustain the `3ED–3FA` loop. The
[stream screen](lower_i_nibble_stream_bridge.py) maps each zero/one bit from
the ROM-executed 8031 scrambler to every ordered pair of those ten nibbles:
90 different two-level encodings. It uses the same real DSC PROMs,
Am27S31 and untraced candidate control mapping, Q=`05` and zero RAM.

At one new bit per D3F8 visit, **three** pairs consume all 128 offered bits:

| Zero / one nibble | D3F8 visits | Distinct selected `3F7` addresses | Controller/zero address differences in first 128 visits |
| --- | ---: | ---: | ---: |
| `5/3` | 149 | 25 | 118 |
| `7/8` | 149 | 28 | 122 |
| `F/2` | 149 | 10 | 124 |

The first 128 D3F8 reads select exactly the offered bytes in each witness.
For `5/3`, ALU Y differs from its all-zero control at 119, 116 and 113 of
the first 128 visits to `3F8`, `3F9` and `3FA` respectively. The other two
pairs also change those three sites extensively. This is an executed,
controller-dependent **internal** ROM/ALU path under the stated assumptions.

The timing check limits its physical interpretation. Consecutive D3F8
visits in each witness are exactly eight microcycles apart. At the plan's
unmeasured `14.4 MHz / k`, `k=1…4`, microcycle hypothesis, one bit per visit
would require a 450 kbit/s–1.8 Mbit/s source, far above the modem's 1,200
baud line symbols and 2,400 bit/s data stream. At that clock range, a
2,400 bit/s bit would span about 188–750 loop visits. Holding each bit for
2, 4, 8 or 16 visits causes **all
three** paths to exit before consuming the full stream. The shortest
photo-compatible input encoder is still untraced: even `5/3` changes two
D pins when the bit changes. The 8031 scrambler was executed locally,
without a complete controller/DSP timing connection.

The [report](results/lower-i-nibble-stream-bridge.json) retains every pair,
the longer-hold results, selected-input checks, ROM/ALU comparisons and
trace digests. It does not identify DAC08 bytes or establish C2. The next
test should constrain how a controller or receive signal could supply D3F8,
and whether a slower input schedule can survive with a different state or
clock phase; no missing pin trace blocks that experiment.
