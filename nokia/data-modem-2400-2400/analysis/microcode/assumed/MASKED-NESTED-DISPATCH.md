# An input mask selects both nested ROM calls from reset

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

Under q3, a nonzero external-input mask can select 2BC at 21F and then select
its inner callee at 2C4. This extends the earlier [nested reset examples](NESTED-RESET.md),
which selected 2BC through a scenario index and entered with Q=0. The two call
indices now come from executed datapath state; the earlier dispatch choices
still use the retained seed-115 scenario.

## Reset input path

Start from zero RAM/Q at 000 with the existing previous-flag condition policy,
default D=CC, and early CC-then-zero replies at 117/106. Three reads change:

- D at 107 is zero, capturing FF in R7. In the observed caller state R0=FF,
  this permits the carry tests at 2F5/2F6 to fall through to the input path.
- D at 2E0 loads a byte a into Q.
- D at 2E1 ANDs a second byte b into Q, giving `m=a&b`.

The two reads change no RAM registers. The following 2E2 uses fixed carry zero,
so its flags/Y no longer depend on the separate input bytes. All 65,536 a/b
pairs are checked through these three decoded operations with the observed
R0=FF, R5=0 entry values. This validates collapsing the input pairs by mask;
it is not 65,536 complete reset runs.

There is no optional BRT gate. The ordinary branches take the mask through
3BB and the return wrapper at 2FD. This entry has one real caller frame, so
the [tail-call contract](TAIL-STACK-CONTRACT.md) is satisfied. No frame or
register is injected. At 21A–21E, q3 increments R4, copies R1 to R2, and
exposes Q on Y immediately before 21F. The call itself computes zero AND Q,
so current Y is zero while Q and previous Y both equal m.

## Outer lookup and nonzero preparation

The retained outer table has 82 entries based at ROM offset 080, with target
bank 200. Its index is reduced modulo 82. Only index 81 selects byte BC at ROM
address 0D1 and therefore target 2BC. Of all byte masks, this occurs for:

| Mask (hex) | Independent a/b pairs producing it | Outer table index |
| --- | ---: | ---: |
| 51 | 243 | 81 |
| A3 | 81 | 81 |
| F5 | 9 | 81 |

Thus 333 of the 65,536 independent pairs have a mask that selects this nested
wrapper under the retained table interpretation. The runtime sweep tests each
of the 256 masks from reset using a=m and b=FF. All 256 runs reach 084 cleanly.
The table's source dump, ranges, banks and bytes are hash-checked; their
association with these call sites remains a hypothesis.

In the three nested runs, the q3 preparation preserves Q=m and gives
`R0=m>>1`, `R2=R5=0`, and `R4=((CC+m)&FF)>>1`. The temporary R2 value written
at 2BD is overwritten at 2C2. Unlike q2's preparation formula, q3 copies R5
at 2C2; it does not retain D+Q there.

## Inner lookup and returned data

The inner table spans ROM 090–0CF. With Q as its index, the three masks select:

| Mask | Inner index (decimal) | ROM address → target | Q at wrapper return | First 084 cycle |
| --- | ---: | --- | --- | ---: |
| 51 | 17 | 0A1 → 22B | 51 preserved | 228 |
| A3 | 35 | 0B3 → 225 | CC loaded by callee | 230 |
| F5 | 53 | 0C5 → 225 | CC loaded by callee | 230 |

All enter 21F at cycle 178, 2BC at 179 and the inner call at 187. The live stack
grows from two frames at 21F to three in 2BC and four in the selected leaf.
The leaves return through 2C5, 220 and 2FF; the final POP returns normally to
213. This demonstrates actual nonzero data through the nested calling context,
not just reachability of its instruction addresses.

Twelve matched controls change one index source at a time for these masks:

- Previous Y at either call selects the same index as Q and gives the same
  observed return path. This experiment cannot distinguish those two sources.
- Current Y at 21F is zero and selects 221 directly, bypassing 2BC. Its
  temporary load and nested 228 call precede the 225 reload; these controls
  reach 084 at cycle 227.
- Current Y at 2C4 selects inner index zero, targeting 2B3. These nested
  cases preserve the incoming mask and reach 084 at cycle 234 instead.

All controls remain clean. Successful execution alone does not identify the
physical index source. Earlier dispatch choices retain their seeded scenario
selection; this is not a fully datapath-addressed model of the whole program.

## Evidence and checks

[Configuration](masked-nested-dispatch.json), [runner](masked_nested_dispatch.py)
and [report](results/masked-nested-dispatch/report.json) preserve 256 full
reset outcomes, 12 source controls, 15 full witness traces, all local mask
counts, boundary register/stack states, ROM provenance and source hashes.
The study reproduces byte for byte. The 99-test suite checks nonzero nested
entry, maximum depth four, and the differing inner targets.

The new interpretation at 21A–220 and q3-specific preparation annotation bring
coverage to 372 used words. External byte meaning, physical dispatch wiring,
and the wider DSP purpose remain unresolved; the full plan is not complete.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/masked_nested_dispatch.py --out /tmp/nokia-masked-nested
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
