# The common terminal tail and the 084 self-loop

Under both current register-role candidates, 084 is the only decoded direct
BRT to its own address. Its modeled ALU operation is an AND with no register
or Q load, and the branch is unconditional under the saved rule. It selects
no external D operand. Changing the supplied input bytes or running more
cycles therefore cannot release this modeled loop.

The useful structural label is **common terminal tail**, not a proven hardware
halt, sample boundary, or controller wait. No external output enable, restart
signal or clock-gating function has been identified here.

## Shared structure

Fifteen reachable branch sites enter 078–084 under the ROM-backed graph.
They enter at different points, so this is not a single fixed epilogue executed
identically by every path. The decoded tail includes:

| Address | Structural role under the saved hypotheses |
| --- | --- |
| 078–079 | Conditional skips |
| 07D,080 | Direct calls to 085 |
| 07E,081 | Computed calls into the one-word 08A–099 table |
| 082–083 | Final fallthrough instructions |
| 084 | Unconditional self-branch, no datapath load |
| 085–089 | Four RAM-shift destination instructions followed by POP |

The last row describes destination codes, not a demonstrated serial-output
routine. The current decode does not shift Q in that helper, and repeated
microinstructions do not by themselves identify a DAC or external shift
register. Incoming branch sites and the full 078–089 listing are saved in
the reports.

The 084 decode is `A AND Q`, with A selecting R0 in original roles or R7 in
swapped roles. Its output and flags settle to the same values on repeated
execution while RAM, Q, PC and stack stay unchanged. The study checks five
A values, every byte-valued Q, and D=00/FF: 2,560 component steps per mapping,
5,120 total. These finite checks support the decoded no-load/self-branch
structure; they do not model possible physical external side effects.

## Stack context matters

The conservative reset graph reaches 084 in two logical stack contexts:
empty, or containing 02B. Both current mappings have the same contexts.
This graph explores all declared branch outcomes; the second context is not
claimed to occur under the selected fitted flag policy.

The saved shortest path for the second context goes through PLP at 02B.
TSK at 02D skips BLT at 02E, leaving that loop frame on the stack. The path
then branches from 031 to 05B, completes the separate 05D–063 loop, and jumps
from 06E to 084. Thus 02B is a **loop frame**, not an ordinary call return.
The selected marked-input reset traces from the preceding study reach 084
with empty logical stack.

## Why unconditional fallthrough is not a repair

A counterfactual probe begins at 085 with each graph-derived stack context:

| Starting logical stack | Result of allowing execution beyond 084 |
| --- | --- |
| Empty | 085–088 execute; POP at 089 attempts a stack underflow |
| [02B] | POP at 089 returns to 02B using the retained loop frame; the explored continuation has no stack exception |

These probes are diagnostic entries, excluded from reset coverage. They do
not change the runner or claim that hardware actually exits 084 this way.
They show that simply making 084 conditional and allowing it to fall through
would not provide a valid general release mechanism for the observed empty-
stack arrivals. Silently repairing or clearing the stack would hide that
counterexample.

Likewise, the model's RST operation does not clear its stack. There is no
basis here for automatically treating every arrival at 084 as a safe reset
boundary. A concrete external restart hypothesis must account for both
control-store entry and retained stack state, and must remain separately
labeled until supported by evidence.

## Consequences for the plan

The emulator now has reset-started, input-dependent execution before reaching
this tail, but the terminal behavior remains unresolved. More repetitions at
084 cannot identify additional arithmetic or I/O. The remaining work should
focus on control/transfer evidence around this tail and on the still-unexplained
words, rather than forcing an escape to improve coverage. No restart event,
interrupt, stack repair or physical output strobe is introduced by this study.
The full plan remains incomplete.

## Reproduce and verify

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/terminal_study.py \
  --out /tmp/nokia-terminal-study
```

[Configuration](terminal-search.json), [summary](results/terminal-study/summary.json),
and [original-role report](results/terminal-study/original.json) preserve
arrival paths, escape diagnostics, incoming branches, listing and stationary
checks. All three reports regenerate byte for byte. The existing 57-test
functional/assumption suite passes; the study additionally checks its 5,120
component steps and rejects a graph with exploration exceptions.
