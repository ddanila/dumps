# Lookup-ROM feedback into the ALU

The runner now tests actual Am27S31 bytes as the ALU D input, addressed by
the preceding executed instruction's Y output. This replaces the constant
external byte for this experiment. It does not recover the board's address
latch, memory selection, or read qualification.

The result is negative for the immediate algorithm question: all four decode
variants still enter the sampled paired-arithmetic tables with zero source
pairs. ROM feedback alone, under these policies, does not establish useful
signal processing or distinguish the layouts.

A [128-seed writer-provenance follow-up](OPERAND-PROVENANCE.md) finds the same
zero-input limitation and identifies the last instructions writing those bytes.

## Assumptions and trace contract

`io.read.mode` is `am27s31`; its optional `address` object specifies
`source: previous_y`, `bank: 0` or `256`, an explicit byte `initial_y`, and
status/evidence. Address = bank + previous Y. Each instruction samples that
address before executing and replaces the retained Y afterward. This policy
requires integrated mode and a matching `expected_sha256` for the 512-byte dump:

```
312fa21f50203c7b84ec0a4b4aea62ca343b2a579c38687111342368b1f04d58
```

The fixed bank bit and unconditional latch updates are hypotheses. Branch and
call indices remain scenario-driven to isolate this experiment. Their ROM
lookup interpretations and ALU input reads are separate model inputs, **not a
coherent physical shared-bus model**. External RAM and actual DAC/controller
transactions remain unmodeled.

Each bounded trace record includes `external_read` with address, byte,
`selected_by_alu`, and assumption status. Only source codes 5, 6 and 7 select
D as an operand. Selection does not prove the result depends on D: an AND
with zero, for example, masks it. The summary counts all sampled addresses
and selected operands separately. Retained Y is included in the transition
digest and final state. Existing scenarios without this policy keep their
previous behavior and output format.

## Measurements

Four layouts × two banks × 16 seeds × 1,000 cycles gives 128 clean runs.
The number of distinct sampled ROM addresses is:

| Decode variant | Lower bank | Upper bank |
| --- | --- | --- |
| 1 | 29 | 68 |
| 2 | 25 | 89 |
| 3 | 29 | 73 |
| 4 | 31 | 92 |

Each variant/bank profile observes four completed calls among sites 3C2,
3D7 and 3EC. Every source pair reconstructed at entry from the actual trace
is zero. These are reset-run observations, not injected arithmetic fixtures.
They neither validate nonzero rotation semantics nor prove external RAM is
the missing ingredient.

The million-cycle example (variant 2, upper bank, seed 2) finishes cleanly,
samples 34 distinct addresses, selects D in only 46 instructions, and records
50 register-change events. Address 100 is sampled 999,894 times. Thus one
million sampled reads should not be described as one million useful data
operations. This small-seed experiment does not replace the earlier 91.97%
coverage result.

## Verification and reproduction

The functional/assumption suite passes 47 tests. The feedback test checks a concrete three-step address/value chain:
001 → byte 31, 031 → byte FF, 0FF → byte 00 (hex), with the current byte
becoming the next address. It also distinguishes unselected D, rejects
sequencer-only execution, and checks invalid bank and ROM hash handling.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/feedback_study.py \
  --integrated-cycles 1000000 --out /tmp/nokia-feedback-study
```

[Configuration](feedback-search.json), [comparison summary](results/feedback-study/summary.json),
[million-cycle summary](results/feedback-study/integrated/summary.json), and
[bounded trace](results/feedback-study/integrated/trace.jsonl) preserve the inputs
and observations. Full million-cycle replays check this feedback run and the
previous index-source experiment; the 128-run comparison is regenerated
independently. The full plan remains incomplete, particularly routine
identification and the relationship between computation and physical I/O.
