# Fourth outgoing byte: state code plus three flags

Controller code 006E–012C completely rebuilds RAM 33, the fourth outgoing byte.
Its upper five bits come from a state-dependent code; its lower three bits come
from explicit flags. The former RAM 33 value does not survive. The serial
routine later XORs this byte with F8, inverting the five code bits while leaving
the three flag bits unchanged.

This provides a firmware-level output format. The physical recipient and the
meanings of the encoded states are not assigned by this study. The other three
output builders remain separate work.

## Five-bit state code

Let S be state byte 34. The routine computes a temporary byte K:

| S range | K source |
| --- | --- |
| 00–7F | Zero |
| 80–9F | ROM at `00B5 + (S AND 1F)` |
| A0–BF | ROM at `0095 + (S AND 1F)` |
| C0–FF | Constant 5C |

Only `K AND F8` survives in RAM 33. In particular, constant 5C contributes 58
in RAM and A0 after the serial XOR. The lower bits of the ROM table bytes are
not retained in this byte, although later code still has the full K in R2.
The two 32-byte ROM tables are data, not instructions; the linear disassembly
at those addresses is not an executable routine.

[State-code table](../results/controller-output-study/state-codes.csv)
records all 256 state values, raw K, and the upper bits before and after serial
normalization. It does not attach speculative modem-state names to the codes.

## Three flag bits

RAM 33.0 is always copied from RAM 23.5. The pair RAM 33.2:33.1 uses the first
matching condition below; bit numbers refer to internal RAM, not physical pins.

| Condition, in priority order | Bits 2:1 |
| --- | --- |
| `(S AND F8) == E8` | 11 |
| RAM 24.6 set, or both RAM 23.7 and received RAM 2D.7 clear | 01 |
| RAM 30.5 clear, or S=B3, or either RAM 23.5/23.6 set | 10 |
| RAM 23.7 set, or RAM 2D.2 set while RAM 23.1 is clear | 11 |
| Otherwise | 00 |

The RAM 23/24 flags are among those produced by the earlier
[input decoder](DECODE.md). RAM 30.5 is the value already present
when this builder runs; it must not be replaced with a later rewritten byte.

The code initially ORs the old low three bits of RAM 33 into scratch RAM 20,
but then explicitly assigns all three bits before writing RAM 33. That explains
why the result is independent of the previous output byte.

## Exhaustive local check

[Reference](../controller_output.py) describes the lookup and flag rules.
[Configuration](../controller-output-scenario.json) fixes register bank zero,
disabled interrupts, and a local entry at 006E. The probe stops at 012F,
immediately after the RAM 33 write, without executing the remaining builders.

The study checks all 256 state bytes against all 256 assignments of the eight
relevant flag bits: 65,536 executions. Another 2,048 cases vary every prior
RAM 33 value at eight representative states. All 67,584 cases match all 128
internal-RAM bytes, stop PC, and unchanged stack pointer, with no emulator
exceptions. This includes the saved state in R3, full code byte in R2, and
scratch byte 20, rather than checking only the output byte.

The suite executes 57 instruction starts. The sole unvisited instruction in
this section, excluding table data, is the AJMP at 00F5: it follows a second
E8-group equality check that cannot succeed after the earlier check has already
rejected that group. The reference and probes preserve this distinction rather
than counting embedded data as uncovered executable code.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_output_study.py
```

[Report](../results/controller-output-study/report.json) contains source/ROM
hashes, fixture and execution digests, coverage, and 26 complete witnesses.
Probe output is checked as a stream to keep memory bounded during the exhaustive
sweep. The independently tested serial-output routine supplies the F8 transform;
this local experiment does not claim to execute an entire polling iteration.
