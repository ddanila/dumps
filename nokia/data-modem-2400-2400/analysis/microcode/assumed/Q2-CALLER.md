# q2 reset reaches zero-target polls through explicit external replies

The retained q2 mapping can reach the [masked external poll](MASK-VARIANTS.md)
from reset under the separately declared previous-flag/defined-carry policy.
The target in these runs is always zero. This establishes a coherent sequence
of modeled waits, not a nonzero data-processing target or physical handshake.

## Why nonzero constant input stops earlier

Under q2, 074 writes FF to R0 for every tested input byte. Its ALU sources are
internal registers, unlike fitted_original's D-dependent complement at that
address. The reset trace records 074 as the last R0 writer at the early waits.

117 computes R0+D and stores the low byte in R6. BLT at 118 repeats while
that preceding addition carries. With R0=FF, every D except zero produces
carry. Therefore constant nonzero D remains in the two-instruction 117/118
loop and never reaches the masked poll.

After this wait returns, 106/107 performs the corresponding carry-qualified
wait into R7. The tested reply profiles change D at 117 and 106, while their
following BLT instructions still sample the default D. Previous-flag timing
means the reply at the preceding instruction determines the branch; the later
read may still change the stored R6/R7 value. The model does not assume these
instructions sample an identical external byte.

## Target provenance

After replies release those waits, dispatch index zero leads through 11B to
126. At entry, R0=FF, Q=0 and R10=0. R10 has no preceding writer in the trace;
it retains its explicit zero reset value. 126 loads R10 into Q, so the target
at comparison 129 is zero. A nonzero D produces `Q−D mod 256` and repeats;
a later zero reply permits return through 12B, which restores Q from R10.

The subsequent call at 11D reaches 12C with Q still zero and R0 still FF.
Its comparison at 12E similarly waits for zero. These are ordinary ROM calls
and returns, with no injected register results or control-flow changes.

## Controlled reset experiments

The [study](q2_caller_study.py) runs all 256 default input bytes in three
profiles, retaining global dispatch index zero and the same initial state:

| Profile | External-input rule | Outcomes |
| --- | --- | --- |
| Constant | D everywhere | D=00 reaches 084; 255 other bytes repeat at 117/118 |
| Early replies | 117 and 106 read D once, then zero | D=00 reaches 084; 255 other bytes repeat at 127–12A |
| All replies | Also give 129 and 12E D once, then zero | All 256 reach 084 after both masked helpers return |

All **768 runs** complete without model or stack errors. Non-return cases
have repeated datapath/stack/flag states and identical remaining input-stream
suffixes, with periods two or four. They are not classified from a timeout.
The reply streams are explicit diagnostic stubs, not recovered transactions.
All-reply runs reaching the terminal 084 loop do not demonstrate a continuous
modem workload.

The checker follows R0/R10 provenance, both helper entries and returns, the
comparison result, and the initial data-independent R0=FF setup. The report
records constant D in the run configuration; detailed per-read events are
present for the sequence profiles. Missing per-read fields in historical
constant-mode trace records are retained as null rather than invented events.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/q2_caller_study.py
```

[Configuration](q2-caller-study.json) records the exact mapping/scenario
combination and reply sites. The [report](results/q2-caller-study/report.json)
contains all summaries, writer chains, loop states, and source/trace hashes.
Twelve witnesses retain complete 512-cycle traces and mapping/scenario files.

## Implication

The q2 interpretation is no longer only a local fixture: its polls are reached
from modeled reset through ordinary caller paths. However, these paths provide
only a reset-zero target, so they do not establish the purpose or source of
nonzero target data. The physical D source, shared condition policy, and useful
processing after the waits remain unresolved. Default mappings and scenarios
are unchanged.
