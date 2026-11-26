# Frozen changed-mode receiver gates at carrier offset 128

The [phase-128 challenge](joint_mask04_12a_mode_phase128_challenge.py)
freezes the [12-state changed-mode gates](JOINT-MASK04-12A-MODE-TWELVE-HOLDOUT.md),
the Q=0.5 line, +5 sample shift and assumed `81→A1` input at `3EB`
read 48,001. It changes the transmitter R1 carrier offset from 120 to
128 and uses a new eight-byte payload in each selector. Both complete
real-PROM transmit→line→receive runs sustain the same four-row capture
schedule and feed the modeled 8251/executed 8031 handoff.

| Selector | Reference dibit errors | Frozen gate errors | Recovered bytes |
| --- | ---: | ---: | --- |
| Call `40` | 0/64 | **0/64** | Eight exact line bytes and eight exact controller bytes |
| Answer `60` | 0/64 | **0/64** | Eight exact line bytes and eight exact controller bytes |

The [audit](joint_mask04_12a_mode_phase128_audit.py) independently
recomputes each phase difference from saved real-PROM capture values,
checks the exact source bytes, and confirms no controller errors or
overruns. Each stream visits six previously labeled states, with state
`09` present in 32 of 65 symbols. The earlier `01`-mode graph assigns
that same seven-bit code a different phase label; the assumed mode
selector remains necessary for this conditional readout. No new state
appears here, so the result tests carrier-start transfer **within the
known state alphabet**, not arbitrary carrier/gain robustness.

The [machine run](results/joint-mask04-12a-mode-phase128-challenge.json)
and [audit](results/joint-mask04-12a-mode-phase128-audit.json) preserve
payloads, hashes, captured values, decoded bytes and limitations.
Reproduce from the microcode directory with:

```sh
python3 g2/joint_mask04_12a_mode_phase128_challenge.py
python3 g2/joint_mask04_12a_mode_phase128_audit.py
```

C3 and G2 remain open and active. The phase gates, `3EB` mode net,
capture storage, RxD/RxC and SYNDET path are still assumptions. Next
test a carrier/gain condition that introduces new states, and separately
constrain a photo-compatible mode-selector/serializer route.
