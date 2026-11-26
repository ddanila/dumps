# What the microprogram does under the tested assumptions

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The executable interpretation is an input-driven collection of arithmetic
routines. It prepares registers, captures external bytes, selects one of eight
handlers, performs byte or paired-byte arithmetic, and either stores results or
waits. Several waits repeat forever for fixed inputs. A terminal branch also
repeats forever in the current scenarios; reaching it does not demonstrate a
physical reset or completion handshake.

This account joins the evidence in the [address listing](PROGRAM-READING.md).
The G1 account below does not combine its six candidate datapath mappings into
one machine. The later joint mask-`04` G2 profile is described separately.
Most handler contracts below use **q3, previous flags, zero reset and diagnostic
input replies**. Handler 0 uses current flags; alternative branches sometimes
need a different condition source or timed external line. Each linked study
specifies those differences and includes its actual traces and predictions.
Addresses are hexadecimal. Arithmetic on a byte wraps modulo 256.

## Startup and selection

The [startup contract](STARTUP-CONTRACT.md) explains the path from 003 through
100–109. Inputs at 002 and 076 accumulate into Q, giving a code c. Two calls
to 112 prepare registers, with the second input capture replacing the first.
Two separate waits capture bytes into R6 and R7. Under previous-flag timing,
the input on the first instruction controls repetition while the second
instruction supplies the retained byte: loop control and captured data are
independent.

With the declared Q-based dispatch, c modulo eight selects a handler. Before
dispatch, R0=FF, R2=1, R4=c plus the second preparation input, and R6/R7 hold
their respective capture bytes minus one. Other RAM registers are zero.
Startup takes 37 instructions plus two per unsuccessful wait reply. This is
a microinstruction count, not a measured board clock or sample rate.

The alternative early dispatch at 008 enters a separate family of capture and
comparison paths. These converge on a fixed-register wait at 05D or on the
terminal tail. An external read occurring inside a loop does not necessarily
control its exit: [the early-wait study](EARLY-WAIT.md) proves cases in which
the retained registers make the loop permanent. The
[early-entry studies](EARLY-ENTRY32.md) and [final blocks](FINAL-BLOCKS.md)
explain the remaining branches, including the Q-clearing call at 044.

## The eight handlers

The table describes computational roles established in particular reset
scenarios. A handler number is the tested dispatch index, not an identified
Nokia command number. Complete register formulas, branch boundaries and cycle
counts are in the linked studies.

| Index / entry | Established behavior | Scope that matters |
| --- | --- | --- |
| 0 / 11A | Tests retained registers, performs temporary input arithmetic and finishes with Q=FF; the startup R4 capture survives. [Study](HANDLER0.md) | Current flags and matched BLT-side replies allow this path; temporary Q captures are overwritten. |
| 1 / 148 | Adds two external bytes and retains their wrapped sum shifted right once in R14. Shift loops make execution time depend on the input. [Study](HANDLER1.md) | This is `((u+v)&255)>>1`, so it is not ordinary averaging when the sum overflows. Timed branches also expose input-parity effects. |
| 2 / 18B | Builds an FE/FF comparison value, drains a wrapped input sum, waits for a matching reply, then loads and stores a payload. [Study](HANDLER2-BODY.md) | The release reply depends on the earlier mask/carry result; the sum affects timing while the later payload determines Q and the terminal half-value. |
| 3 / 300 | Performs externally gated preparation and enters paired arithmetic; an alternative path constructs a second component and drains Q twice. [Main path](EXTERNAL-LINE.md), [alternative](HANDLER3-DRAINS.md) | Timed external conditions are explicit hypotheses. Values visible on Y can be overwritten before terminal entry. |
| 4 / 259 | Selects inputs using sum carry and comparison, then follows a large family of computed continuations that preserve, replace or add captured values before indexed stores. [Main study](HANDLER4.md), [bank continuations](HANDLER4-BANK.md), [alternatives](HANDLER4-ALTERNATIVES.md) | The later dispatch index and external schedule determine which contract applies. Nested calls retain real stack frames. |
| 5 / 345 | Prepares paired values, calls the paired-output loop, then selects different compositions of capture, complement and carry-loop helpers. [Study](HANDLER5-BRANCHES.md) | Returning fixtures give final Q=0, c or FF. With different captured values the initial paired call repeats and never reaches these continuations. |
| 6 / 09E | Masks a captured byte, conditionally increments it, and shifts it into retained state; later diversions capture other inputs and choose terminal entries. [Main study](HANDLER6.md), [early diversion](HANDLER6-EARLY.md), [late diversion](HANDLER6-LATE.md) | Carry and flag timing change the boundary behavior. The current-flag exit at 1DC–1DE is a separate tested context. |
| 7 / 133 | Input addition carry and a captured-byte comparison choose zero, one or three transform calls. [Study](HANDLER7.md) | The reset witnesses have zero transform source pairs and fixed table entry two; their one-pass returns do not prove termination for arbitrary nonzero transform state. |

## Shared arithmetic and result handling

The small helpers provide register capture, conditional copies, sums,
differences, complements and shifts. Their names describe observed effects.
They should not be renamed as multiplication, filtering or modem functions
without further evidence. Some calls have identical retained RAM/Q but expose
different intermediate values on the ALU output Y; the
[short-helper contracts](SHORT-HELPERS.md) preserve that distinction.

The [paired arithmetic](PAIR-WAIT.md) treats R4/R5 and R6/R7 as little-endian
16-bit values U and V in the q3 contexts. Its four declared table entries
expose respectively `(2U,2V)`, `(0,2V)`, `(0,0)` or `(2U,0)`, modulo 65536.
The final high byte controls return. Consequently the routine can return with
a nonzero low byte, or repeat every 12 instructions without changing its
source values. Repetition is not evidence of a progressing oscillator phase.

Other tables admit paired quarter-turn interpretations under q2 local
fixtures. Those identities were constraints used in choosing the candidate
mapping, so they are not independent proof of a recovered rotation algorithm.
Source-overlapping entries require different formulas. The
[program listing](PROGRAM-READING.md) keeps these profile scopes separate.

The terminal family at 078–084 uses shift helpers and indexed register stores.
Some paths enter at 07B and preserve values that earlier terminal instructions
would overwrite. Index overlap also matters: writing one destination can
change a value used later. The [register contract](Q3-REGISTER-CONTRACT.md)
checks these cases rather than treating all destinations as interchangeable.
At 084 the current execution scenarios remain in a terminal branch. The
[terminal-tail analysis](TERMINAL-TAIL.md) explains why a universal restart
interpretation is unsupported.

## The other boards and observable output

The ROM contains an identified quarter-sine region. Experiments feed actual
dump bytes into arithmetic and record their downstream effects, rather than
inferring a sine generator just from the table's presence. The
[ROM-operand study](SINE-OPERAND.md) and [read-gate study](ROM-GATE.md) also show
why several physical read-enable hypotheses remain possible.

The [controller-to-DAC experiment](FRAME-DAC-BRIDGE.md) supplies a complete,
explicit connection hypothesis. The actual 8031 firmware builds and transmits
four bytes. The harness waits for all four transmission completions and the
subsequent latch edge, then routes those unchanged bytes into a fresh
microcode run. Partial transfers do not start that run.

For transmitted bytes c,p,l,h, this experiment computes:

```
S = ROM[256 + ((p+c) & 255)]
U = (S+c) & 255
V = ((l-1) & 255) + 256*((h-1) & 255)
output bytes = low/high of 2U, then low/high of (2V modulo 65536)
```

The declared DAC routing latches the first low byte. The two verified frames
give held DAC codes 34 and 146, with repeated transfers every 12
microinstructions. One frame reads the quarter-sine region and the other reads
a different real ROM location. Neither transaction advances the ROM address
after its first lookup, so neither demonstrates a generated waveform.

ROM address setup, read and output occur at microcycles 44, 45 and 55–58.
The cross-board clock ratio and startup latency are scenario parameters.
These establish a reproducible relative timing model; no physical sample
frequency or analog waveform is recovered. The controller-to-microcode byte
routing, reset request and DAC strobes remain declared assumptions, and this
experiment supplies no controller return protocol.

## Later joint-map modem candidates

The later [joint mask-`04` listing](PROGRAM-READING.md#g2-modem-function-candidates-on-the-joint-mask-04-map)
adds evidence-scoped modem-function names for the executed 127–12A transmit
loop and 3F8–3FE/3EB–3ED receive update and readout. The same mapping sustains
the tested controller-driven transmit samples and retains ADC-dependent state.
The candidate DAC route reproduces a 2,100 Hz tone and reference dibit
decisions. A later [two-visit receive readout](../g2/RECEIVER-MASK04-DUAL-FEATURE-CONSENSUS.md)
recovers all 611 measurable dibits in a held-out 13-angle PROM run; its
[zero-run handoff](../g2/RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md) also gives the
controller's executed `AF→B0` transition for two intermediate-angle streams
under aligned external-sync timing. The physical DAC, ADC and USART paths
remain unverified, so C2 and C3 stay open.

A newer [row-phase readout](../g2/JOINT-MASK04-12A-ROW0-TWENTY-STATE.md)
uses two executed receive Y snapshots and the first `3ED` row bit. On six
fresh controller-payload runs at three line levels it recovers all 64
measurable dibits, the exact eight line bytes and the exact eight source
bytes after modeled USART/8031 handoff. The
[timing replay](../g2/JOINT-MASK04-12A-ROW0-SERIAL-TIMING.md) gives that
candidate 2,961 microcycles of setup before its assumed RxC sample. New
[call and answer row captures](../g2/JOINT-MASK04-12A-ALL-ROW-LATCH.md)
show that a latch clocked on every `3ED` row loses the needed row-0 bit;
an external qualifier or another hold path is necessary for this readout.
The executed microprogram exposes input-dependent phase information, while
the phase gates, capture storage and serial output remain circuit hypotheses.

## What the coverage numbers establish

The historical 28.80% is the union of 294 visited addresses in the original
sequencer runs, out of 1,021 used words. It is not a percentage of recovered
modem functionality. Many long runs spend nearly all their cycles at 084.
The newer separate sequencer sweep visits 941 words (92.16%). Integrated
long runs check actual arithmetic and I/O, including a continuing ROM/carry
feedback loop, but do not cover that whole union.

Every used word now has an evidence-linked annotation under at least one
stated interpretation. The default graph reaches 999 words; the remaining 22
have explicit entry-policy explanations and reset witnesses. Those witnesses
do not prove one globally safe physical decode. A relaxed graph can still
reach 2FF without its required incoming caller frame; the
[stack contract](TAIL-STACK-CONTRACT.md) retains that counterexample.

Thus the current program reading supplies concrete arithmetic, dataflow,
branch and timing contracts, and a working assumed connection to the other
boards. Identifying the original modulation, demodulation or filter algorithm
would require distinguishing the remaining hardware hypotheses. The plan
allows those hypotheses to stay explicit rather than blocking execution.
