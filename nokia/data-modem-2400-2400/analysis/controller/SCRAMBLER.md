# Two 23-bit self-synchronizing data transforms

The controller contains a byte-parallel scrambler and its matching descrambler.
Their equations follow directly from the XOR/shift operations, and an independent
bit-serial implementation matches unchanged ROM execution. This identifies a
data-processing algorithm without assigning it to a particular modem standard
or claiming a recovered DSP connection.

## Bit-level meaning

Bits are processed least-significant first within each byte. Let x[n] be the
unscrambled input and y[n] the scrambled output. The selected short delay d
is either 5 or 18; the long delay is always 23:

```
scramble:   y[n] = x[n] XOR y[n-d] XOR y[n-23]
descramble: x[n] = y[n] XOR y[n-d] XOR y[n-23]
```

The scrambler feeds its **output** back into history, while the descrambler
stores its **input**. That difference is why otherwise similar instructions
form an inverse pair. As a delay polynomial this is 1 + D^d + D^23.

The 23-bit history is packed as `((high & 7F) << 16) | (middle << 8) | low`.
Bit zero is the oldest stored bit; bit 22 is the newest. For each bit the
reference takes taps at history bits 0 and 23-d, shifts history right once,
and inserts the feedback bit at bit 22. The unused high bit is discarded
when a byte is processed; a gated-off call leaves it untouched.

| Role | ROM entry | Input / output | History | Selection |
| --- | --- | --- | --- | --- |
| Scramble | 053E | RAM37 → RAM38 | RAM3F–41 | RAM24.0 set: d=5; clear: d=18 |
| Descramble | 05A3 | RAM39 → RAM3A, 3C, 3E | RAM42–44 | RAM24.1 set: d=5; clear: d=18 |

The five-bit path explicitly feeds results from early bits of the current
byte into its later bits. The eighteen-bit path can compute every tap from
prior history. This explains the differing byte-level XOR expressions.

## Handshake and caller context

Scrambling runs only when RAM21.1 is set and RAM21.2 is clear. It clears .1
and sets .2 after processing. The ordinary entry at 0537 first reads control
address 05 and requires status bit 0; this local study starts at 053E after
that external-read gate.

Descrambling requires RAM21.3 set and RAM21.4 clear. It clears .3, sets .4,
and sets .6 after processing. Its output is also copied to RAM3E, which the
output-construction routine uses as a rotating P1.4 pattern. Thus those pattern
bytes can contain processed data, rather than only fixed status patterns.

Static caller evidence connects RAM38 to the external data write at 1DA6,
and an external data read at 1DC6 to RAM39. These are accesses to control/data
pairs 05/01. Physical address decoding, scheduling, and the relationship to
the DSP remain separate questions.

## Verification

The [bit-serial reference](../controller_scrambler.py) is independent of
the ROM's byte-parallel implementation. The
[study](../controller_scrambler_study.py) executes both local routines with
bank zero and interrupts disabled, comparing all 128 internal-RAM bytes,
return PC/SP, absence of exceptions, and absence of peripheral events.

All **43,008 ROM comparisons pass**, covering all 134 instruction starts from
053E through 061F. Cases include every input byte against zero and each of
24 history basis bits (including the discarded high bit), every handshake-flag
byte, and 4,096 random histories/data combinations for each role and delay.
The sweep is not exhaustive over all 23-bit histories.

Additional reference-level checks process 16,384 bytes through matching
scramble/descramble streams with exact recovery. Different initial histories
converge after 23 received bits; the check requires exact recovery from the
fourth byte onward. A single corrupted scrambled bit affects decoded positions
0, d, and 23, as predicted by the feed-forward descrambling equation. These
stream checks compose the reference models; they are not separate long-running
ROM executions.

[Configuration](../controller-scrambler-scenario.json) records assumptions
and fixture sizes. The [report](../results/controller-scrambler-study/report.json)
contains 24 witnesses, coverage, source/ROM hashes and execution/fixture digests.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_scrambler_study.py
```

This interprets controller firmware, not the four-PROM DSP microprogram. It
narrows the surrounding modem data flow but does not resolve the microcode's
remaining disconnected entries or physical input/output mapping.
