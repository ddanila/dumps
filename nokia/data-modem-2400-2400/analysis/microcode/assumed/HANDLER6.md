# Handler 6: masked capture and two Q drains

Under q3, the 09E handler combines an independently captured input byte with
the input code, preserves a masked and halved result, and clears Q through two
shift loops. The control flow and complete final register state can be predicted
for every input in the documented reset scenario. This gives a routine-level
interpretation of 09E–0CD and its exit at 0DE; its modem purpose remains unknown.

## Inputs and result

Use the [handler timing](HANDLER-TIMING.md) previous-flag scenario: input reads
002/076 sum into Q, 109 selects with Q, 117/106 receive `[1,0]`, and other
computed calls use index 2. The selected input codes are `c=6,14,...,254`, so
`c&7=6` reaches 09E. Change the input at 107 to `(x+1)&FF`; the early wait
captures x into R7 without changing which handler is selected. All other
external reads remain 1. Initial RAM and Q are zero.

At entry, R4 is `c+1` and R7 is x. The surviving result is:

```
m = x & (c+1)
t = (m + (1 if m != 0 else 0)) & 255
h = t >> 1
```

At terminal 084, Q is zero and the only potentially nonzero registers are:

| Register | Final value |
| --- | --- |
| R4 | 2 |
| R7 | x |
| R12, R15 | h |
| R13 | t |

All other registers are zero, including R2 after the terminal store table
selects register 2. For example, code 6 and captured byte 7 give `m=7`,
`t=8`, and `h=4`. Code FE and captured FF give `m=FF`, which wraps to zero
before the right shift. This is not a saturating or ordinary rounded divide
by two at that boundary.

## How the handler produces it

- 09E–0AC increments Q twice, copies register values, and overwrites temporary
  R13 values. At 0AB, R13 becomes R4. The Q increment at 0A3 wraps only for
  code FE; this causes 0A4 to execute the otherwise skipped 0A5, which preserves Q.
- 0AD writes `R13=R7&R13`. In the selected Am2901B logical-flag model its
  carry is one exactly when this mask is nonzero. 0AE adds R1 (zero here)
  and that carry, producing t. Thus the logical carry is part of the data
  calculation, not merely a branch condition.
- 0AF reloads Q from R0. 0B0 shifts Q right and writes `R15=t>>1`.
  The call at 0B1 drains Q to zero through 1E9–1EB; it also clears R0.
- 0B2–0B6 clears R0, loads Q with default input 1, then shifts it to zero
  and calls the drain again. The second call executes one loop iteration.
- 0B7–0CD clears the remaining Q/R0 intermediates, forms R4=2, copies
  `R15+1` into R2, and copies R15 into R12. These temporary R2 contents
  are overwritten by the terminal tail's register-2 store.
- 0CD transfers to 0DE. The preceding zero result makes 0DE select 079,
  leading to the terminal tail. The alternative 0DF path is not used here.

The first drain executes
`bit_length(((c+2)&255)>>1)+1` iterations under previous-zero timing.
If that count is n, first execution of 084 is at cycle
`115 + 2*n + (1 if c==254 else 0)` from reset. The captured byte changes
retained values but not instruction count. These counts do not identify a
physical sample rate or clock frequency.

## Evidence and limitations

The exhaustive study executes all 32 handler codes and all 256 captured bytes:
8,192 complete zero-reset runs of 160 instructions. All reach 084 cleanly;
7,948 preserve a nonzero half-value, and exactly one has the FF-mask wrap.
All 128 possible half-values occur. First-terminal cycles range from 118 to
131. The study checks the formula
against final RAM/Q, the intermediate mask and carry, both drain counts,
carry-dependent skip, terminal cycle, and balanced stack. Full modeled-state
recurrence verifies terminal behavior under the held inputs. Eight full trace
witnesses include zero, nonzero, largest result, and FF-wrap cases.

The named routine applies to q3 with previous flags, defined logical carry,
zero-fill shifts and this diagnostic input schedule. Conditions 1 and 6 are
fixed false in this scenario, so alternative branches are not assigned the
same meaning. No external output strobe, DAC consumer, or controller command
meaning is inferred from the internal register result.

[Configuration](handler6-study.json), [runner](handler6_study.py), and
[report and saved witnesses](results/handler6-study/report.json).

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/handler6_study.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
