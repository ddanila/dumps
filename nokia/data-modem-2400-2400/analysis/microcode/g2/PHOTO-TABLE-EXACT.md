# Exact 3C5/3DA transform under the held photo-pin candidate

The earlier [reached-call report](PHOTO-TABLE-CALLERS.md) compared each table
result with a sign selection of the *entire* 16-bit source pair. That test
mostly failed. Inspecting its before/after values suggested that the held
E4/I7/A0 candidate instead selects the **high byte of each source word** at
both byte positions. The [executable check](photo_table_exact_transform.py)
now tests that precise rule with the real control PROM words.

Let `H(v) = 0x0101 × (v >> 8)`, so `H(0x1234) = 0x1212`. For source words
`X=RAM[4:5]` and `Y=RAM[8:9]`, both four-entry tables write these 16-bit
values to RAM[10:11] and RAM[12:13], modulo 65536:

| Entry | Output pair |
| ---: | --- |
| 0 | `(H(X), H(Y))` |
| 1 | `(H(X), −H(Y))` |
| 2 | `(−H(X), −H(Y))` |
| 3 | `(−H(X), H(Y))` |

For example, `X=1234`, `Y=5678` gives `(1212,5656)`, `(1212,A9AA)`,
`(EDEE,A9AA)`, `(EDEE,5656)`. Changing only the source low bytes or the
previous output pair does not change these results in the tested fixture.

The local sweep varies eight source pairs, three previous output pairs and
three Q values for all four entries of both tables under each of the five
photo-compatible mappings: **2,880/2,880** four-word executions match the
formula. Independently, the saved reset-path traces contain **140/140**
matching calls with E4 held high (28 per mapping). Thus this formula describes
both local arithmetic and the *actually reached* calls in that declared
scenario. It also explains why the earlier full-word sign-selection check
matched only a small fraction: it expected the low source bytes to survive.

The result identifies a four-way sign selection in the **held E4=I7=A0=1,
E2=I0=A1=0 model**. It is compatible with quadrant selection as an arithmetic
role, but does not prove DPSK modulation: no controller dibit has been tied to
the table entry, no continuing phase or carrier is shown, and RAM[10:13] has
no traced DAC route. The pin continuations, latch phase and shared Am2901
instruction controls remain hypotheses. The [split-slice candidate](PHOTO-SPLIT-CALLERS.md)
already changes reached table operands, so this exact formula is specific to
the shared-control mapping tested here.

The [report](results/photo-table-exact-transform.json) records the source,
prior-output and Q fixtures, a word-by-word witness, per-mapping checks and
source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/photo_table_exact_transform.py
```
