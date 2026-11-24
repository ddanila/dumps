# Handler 4: bank-200 input replacement and capture preservation

The bank-200 alternatives at 26F either replace earlier captures through two
nested input helpers, or load a payload while retaining those captures. Both
paths end with two indexed stores of half the payload. This connects the
previously unnamed 200–219 body to complete reset executions under q3.

## Entry and declared inputs

Use the previous-flag [handler timing](HANDLER-TIMING.md) scenario with input
code c congruent to 4 modulo 8, its established PLP replies, and global table
index i from 7 through 15. Leave other reads at their defaults except:

- p = external byte at 225, the nested payload load;
- l = external byte at 2EC;
- a = external byte at 28E;
- b = external byte at 293.

The global index also selects the initial paired arithmetic row, the 21F leaf
and both terminal register destinations. These uses are deliberately coupled,
not silently assigned independent indices. At 26F, cycle 92, all tested codes
and indices have Q=1, R0=FF, R3=(-c-2)&FF, R4=2, R12=c+1, R14=1 and R15=2;
other registers and the active stack depth are zero. The initial paired call
returns with a zero final high byte for all four selected rows.

## The three routes

| Index | Path after 26F | Effect before common terminal helpers |
| --- | --- | --- |
| 7–10, 13–15 | 200 → 281–286 → 201–203 → 2CB → 204–216 | Replace captured values through 2EC and 28E |
| 12 | 2CB → 204–216 | Same replacement, nine instructions shorter |
| 11 | 217 → 21A → 218–219 | Load payload, preserve earlier captures |

On the long path, 281 decrements R15 from 2 to 1. Selector 6 is false, so 284
falls through to 285 and 286 returns to 201. The arithmetic at 200/201/202/203
and 282–286 otherwise exposes transient results. 2CB observes the prior carry
and goes directly to 2CD on the 200 route. Direct dispatch to 2CB instead
arrives with carry zero, executes 2CC (exposing Q-1=0), and falls through
to 2CD. Both paths then take 2CE unconditionally to 204. No optional BRT
gate is introduced; 2CF is outside these paths.

204 copies zero R2 into R12. 207–20C successively replace R15, ending at zero;
209's R4 sum is overwritten by 20D's input load. 20F sets R3=FF, while
210/211 expose differences without storing them. These preliminary R3/R4/R15
values are replaced again by the following helpers.

212 calls [2EC](INPUT-TAIL.md) with R0=FF and R7=0. Its comparison necessarily
takes 2F6 → 3BB; the nested 21A call increments l into R4 and 21F selects 225,
loading Q=p. The path returns through 220 and 2FF to the actual caller at 213.
There are three live return frames at its deepest point; none is synthesized.

213 calls 28E. Under q3, 28E stores R3=(p+a)&FF; 291 copies p into R0.
293 overwrites the earlier R15 difference with (p-b)&FF, and 295 increments it
before returning. Thus R15=(p-b+1)&FF. 214/215 expose differences and 216
branches to 078 while computing XNOR(p,p)=FF. The earlier decrement at 281
has no surviving RAM effect, although its transient output and timing differ.

The short path calls 21A directly at 217. This increments the existing R4=2
to 3, copies zero R1 into R2, and loads Q=p through the same 225 leaf.
R0 remains FF; R3, R12, R14 and R15 preserve their entry values. 219 exposes
XNOR(FF,p)=p and branches to 078. When p=0, the previous-zero test at 078
skips 079, saving one instruction. This skip never occurs on the long path.

## Complete final register contract

All expressions below wrap to eight bits before a stated right shift. Start
with this state, then apply the indexed-store overwrite in the last paragraph:

| Register | Long routes | Short route, i=11 |
| --- | --- | --- |
| R0 | p >> 1 | p >> 1 |
| R2 | (p+1)&FF | (p+1)&FF |
| R3 | (p+a)&FF | (-c-2)&FF |
| R4 | (l+1)&FF | 3 |
| R5 | ((-p)&FF) >> 1 | ((-p)&FF) >> 1 |
| R12 | 0 | c+1 |
| R14 | 1 | 1 |
| R15 | (p-b+1)&FF | 2 |
| All others | 0 | 0 |

Both terminal stores then leave **Ri=p>>1**, overriding the table above if
needed. In particular i=12 replaces R12, i=14 replaces R14, and i=15 replaces
R15. Q=p survives. The first execution of terminal 084 is cycle 183 on the
200 route, 174 on the direct 2CB route, and 130 minus one when p=0 on the
217 route. Every path reaches terminal with zero active stack depth and a
maximum depth of three. These counts are microinstructions, not sample times.

## Evidence and scope

The runner checks 3,456 complete reset executions: all 32 codes, nine indices,
four payload boundaries (00,01,80,FF), and three independent-input tuples.
Eight saved witnesses include all three paths, the p=0 skip, and the R14/R15
store overlaps. Regression tests add independent random bytes and perturb
inputs whose writes are subsequently overwritten. Checks compare full RAM/Q,
entry state, selected branches, nested return addresses, stack depth and exact
terminal timing. Witnesses are replayable without local state injection.

The scope remains q3, previous flags, the stated external inputs and table
policy. Varying the earlier handler-4 selection inputs or captured R7 may
change the entry premise; those combinations are not claimed here. Physical
input channels, consumers of transient Y and the modem purpose remain open.
The q3 interpretation of 28E differs from its existing q1/q2/q4 annotations.

[Configuration](handler4-bank.json), [runner](handler4_bank.py),
[report and witnesses](results/handler4-bank/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler4_bank.py
```
