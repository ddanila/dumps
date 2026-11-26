# Frozen six-bit rule under a one-visit-late Y capture

The [phase-96 replay](JOINT-MASK04-12A-SIXTH-PHASE96.md) recovered both
new eight-byte payloads at all three fixed gains. This challenge keeps
its phase-96 transmitter, bus-0/Q=0.5 line, nominal gain, 91-key
receive table and payloads unchanged. It samples both real-PROM `3F8`
Y outputs one receive-loop visit later: visits 47/94 instead of the
development fixture's 46/93.

| Selector | Known-key errors | Unknown data dibits | New transition keys | Full line-byte handoff |
| --- | ---: | ---: | ---: | --- |
| `40` | 0 | 26/64 | 16 | no |
| `60` | 0 | 22/64 | 14 | no |

The late capture has no wrong predictions on keys already in the
frozen table, but too many new keys to decode complete bytes. The
modeled 8251/8031 payload handoff therefore cannot be established for
this clock choice. This is a failed **capture-clock candidate**, not a
failure of the earlier 46/93 fixture or a G2 blocker. It also shows
that exact performance at two carrier starts does not establish
capture-edge tolerance.

The [machine report](results/joint-mask04-12a-sixth-late-capture.json)
contains the Y values, exact unknown indices, transition keys, real-PROM
trace digests, readout result and source hashes. Reproduce with:

```sh
python3 g2/joint_mask04_12a_sixth_late_capture.py
```

The actual ADC latch edge, storage and decision circuit remain
untraced. C3/G2 stay open. Next try a timing signal or multi-visit
decision supported by the available photos, with the rule frozen
before any fresh-data validation. Keep the 46/93 result conditional
until its physical clock can be constrained independently.
