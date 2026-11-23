# External peripheral programming helper

Controller routine 1D05–1D30 writes a fixed prefix followed by caller-selected
bytes to one external address, then returns. The unchanged ROM produces:

```
80 00 40 R3 [FF if (R3 AND 03) == 0] R2
```

R0 selects the low address byte; P2 supplies the high byte for these MOVX @R0
operations. The routine does not change R0, R2, R3, P2, or internal RAM. ACC ends
with R2 and RET removes the caller's two-byte return address from the stack.
The inserted FF depends only on R3, not R2. No external read or serial SBUF
transfer occurs here.

The existing board analysis identifies two P8251A devices and interprets this
as their reset/mode/command setup. This study establishes the emitted byte
sequence independently of whether an external device accepts it. It does not
model USART state, clocks, receive/transmit readiness, or pin timing.

## Caller relationships

The following are static observations from the disassembly, not full caller
execution tests:

- Startup at 1E04–1E10 programs address 06 using R3=RAM35 and command 35 with
  bit 5 replaced by the complement of RAM2E bit 0.
- Startup at 1E1E–1E24 programs address 05 with R3=CC and R2=15, yielding
  `80 00 40 CC FF 15`.
- The output routine at 047E–0484 uses that same address-05 sequence when its
  branch conditions select it. At 0487–0493 it programs address 06 as above.
- Helper 1CE1 chooses RAM35 from received RAM2D: bit 7 selects EC; otherwise
  bit 5/bit 4 select 6E, 7E, 6A, 66 for pairs 00, 01, 10, 11 respectively.
  Thus EC takes the optional-FF path while the four other modes do not.

These links explain why continuous execution beyond 046C must include bus
writes even before the four output bytes reach the separate shift-chain
transmitter at 0899. The programming helper and that transmitter are different
interfaces.

## Verification

[Configuration](../../controller-program-scenario.json) records local entry,
bank-zero/disabled-interrupt assumptions and test inputs. The
[study](../../controller_program_study.py) compares the complete ordered bus
write sequence, all internal RAM, return PC/SP, ACC, P1, and P2 against its
independent reference. All **7,168 cases** pass with no emulator exceptions.

The fixtures cover all 256 R3 values against eight R2 values at each of the
control addresses 05 and 06, plus all 256 P2 values with six representative
modes at both addresses. All 36 instruction starts are visited. This is not an
exhaustive cross product of every register input. The
[report](../../results/controller-program-study/report.json) stores 12 witnesses,
coverage, source/ROM hashes, and deterministic execution/fixture digests.

```sh
python3 nokia/data-modem-2400-2400/analysis/controller_program_study.py
```

The remainder of output construction, interrupt effects, peripheral device
responses, and end-to-end polling/transmission integration remain unverified.
