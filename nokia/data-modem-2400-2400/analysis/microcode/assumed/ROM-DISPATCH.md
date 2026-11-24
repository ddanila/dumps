# Am27S31 data constrains dispatch targets

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The independent 512-byte Am27S31 dump contains bytes that match the microcode
entry points investigated in earlier experiments. This gives a stronger basis
for target lists than the broad structural pools alone. It supports a candidate
connection from the lookup ROM to sequencer address selection, but does not
establish the intervening wiring, index generation or high address bits.

A [ROM-tail follow-up](ROM-TAIL.md) tests D0/D1 at the outer call and
site-specific restrictions at the nested call. It supplies the first observed
2C4 lookup under that alternative while preserving this baseline.

## Independent ROM evidence

| ROM range | Observed data | Proposed role |
| --- | --- | --- |
| 0E0–0E7 | `09 0F 0B 13 22 0D 32 54` | Low address targets for branch 008, bank 000 |
| 0F0–0FF | `C6 C6 C6 30 80 80 30 00 00 00 00 17 CB 00 00 00` | Targets for branch 26F, bank 200 |
| 080–0CF | Five 16-byte rows; eight distinct byte values | Candidate short-return targets for calls 21F/2C4, bank 200 |
| 000–00F | Exact signed `round(127 sin(2πn/16))` | Previously identified full sine period |
| 100–140 | Exact `round(127 sin(πn/128))`, n=0…64 | Newly verified quarter sine period, 65 samples |

The script checks the full dump's SHA-256 and preserves raw bytes. All 65
quarter-wave samples match exactly. Neither waveform establishes a carrier
frequency, sample rate or connection to the DAC.

The 080–0CF rows point to `221, 224, 225, 229, 22B, 22C, 22D, 2B3` when bank
200 is supplied. All eight have safe return paths in the current static model.
Repeating the role check with banks 000, 100 and 300 gives respectively 2/8,
2/8 and 5/8 safe-return targets. This supports bank 200 relative to those
alternatives. It is not a probability or proof of address wiring.

The bytes also refine prior guesses: the low-handler list includes 00F and
00B, while omitting the guessed 03A entry; the bank-200 branch list includes
2CB and omits several speculative boundary roots. These differences are
accepted even where they reduce static reachability.

## Execution comparisons

The experiment starts from the preceding bounded-pool scenario and replaces
targets with the independent ROM bytes. Repeated bytes retain separate indices;
they are not collapsed into unique-target lists. The scenario supplies indices
uniformly, which does not claim the real device uses that distribution. In
particular, the selector among the five 16-byte call rows is still unknown.

| Hypothesis | Static reachable | Dynamic, 128 seeds × 1,000 cycles | Stack result |
| --- | --- | --- | --- |
| ROM bytes for 008/26F; prior call pools | 993 | 967 / 1,021 = 94.71% | Clean |
| Also use 080–0CF bytes for 21F/2C4 | 983 | 939 / 1,021 = 91.97% | Clean |
| Instead assign 0D0–0DF to 21F | 993 | Not promoted to dynamic suite | Possible overflow at 212, 21F, 223, 2C4, 2FE |

The second scenario is the working ROM-backed candidate. Its maximum observed
stack depth is three. It clears the numerical coverage target with a more
constrained data source, but still relies on the earlier hypotheses for other
computed sites. Its 38 statically unresolved words remain listed in the graph.
The higher coverage of the first scenario is not used to dismiss the independent
call-table evidence. The rejected 0D0 alternative remains saved; those bytes
may have a different role or require correlated indices not modeled here.

A million-cycle integrated run uses Q-independent mapping 2, external D=55,
and seed 2, selected because it exercises 26F and 21F. A separate 1,000-cycle
seed-3 example exercises 008. Their dispatch traces are joined back to the
actual lookup bytes and record the proposed ROM address, byte, bank and next
PC. Each reconstructed value is checked against the executed target. These
are **candidate address-path logs**, not measured physical bus transfers.
The assignment to 2C4 is not independently exercised by these examples.

## Relation to the boards

The Am27S31 is tentatively associated with 810241 on DSC3557, as recorded in
the [hardware investigation](../../../README.md); that sticker association is
still unconfirmed. The target matches give a concrete candidate role for this
ROM beyond waveform constants: supplying low sequencer-address bytes to the
DSC2847 processor. The physical route through buffers/connectors and the two
high address bits are still untraced.

DED3558 contains the photographed DAC0830. The sine tables supply plausible
waveform data, but no microcode output strobe or DAC address has been identified.
Existing virtual ALU-output captures therefore retain their virtual labels.

The controller ROM independently establishes six-byte mode-0 input and four-byte
mode-0 output transfers with P1 handshakes, plus a read at external address
8004. Those observations do not identify which bits communicate with DSC2847;
no arbitrary controller-to-microcode bridge is introduced by this experiment.
Sample timing and physical ADC/DAC/controller exchanges remain open requirements.

## Implementation and reproduction

Sparse tables may now explicitly set `allow_duplicate_targets: true`, because
real lookup tables contain repeated bytes. Without that flag, duplicates still
raise an error. Repeated indices preserve their ordering and multiplicity in
execution; static edges are naturally deduplicated. All earlier scenarios
retain their behavior. Tests cover ROM hashes, byte-preserving target generation,
repeated entries, and rejection of inconsistent reconstructed lookups. The
functional/assumption suite passes 45 tests.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/rom_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-rom-study
```

[Configuration](rom-dispatch.json), [independent evidence](results/rom-study/rom-evidence.json),
[comparison summary](results/rom-study/summary.json),
[selected scenario](results/rom-study/scenario-rom_calls.json),
[selected graph](results/rom-study/graph-rom_calls.json),
[integration](results/rom-study/integrated/summary.json), and
[reconstructed lookups](results/rom-study/dispatch-lookups.json) preserve the
assumptions and observations. Raw PROMs, controller ROM and photographs remain
unchanged.
