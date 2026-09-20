# Second 27256: anomalous capture, 2026-09-20

The owner swapped in a different 27256 and confirmed readiness with the same
Normal routing, DIP1B3 and 28-pin placement. Full markings were not supplied.

One conservative read returned 32768 bytes exactly matching the first chip's
[anomalous capture](../27256-20260919-chip01/): initial `00`, then alternating
`06`/`04`, CRC16 `5DFA`. This also exactly matches the offline programmer-output
echo model. The scan took 448.305 seconds, returned zero and reported safe
VCC/VPP shutdown. Actual chip contents remain unknown.

Reproduction on a second physical 27256 strengthens the case for a shared
27256 setup/read-path problem, but does not identify the exact cause or prove
either chip functional. No repeat read or programming was performed.

## Reader defect identified

The [2026-09-20 code audit](../../analysis/20260920-27256-ce-audit/README.md)
found that R27256 v1 incorrectly used the 2764 high CE/PGM state, instead of
the required low state. This is the leading explanation for these captures.
The correction was subsequently uploaded and tested as recorded below.

## First corrected-reader result

Build `dosravi-27256-ce-fix-v2`, uploaded as `RD256V2.COM` and verified by
CRC32 `2253EE15`, returned 32768 bytes of FF on the same installed chip.
The echo disappeared. CRC16 is `FF00`; the scan took 448.855 seconds,
returned zero, and reported safe VCC/VPP shutdown. This is consistent with
a blank chip, but a repeat and known-programmed 27256 control remain absent.
As requested, the all-FF binary is retained only in the DOSRAVI session,
not this repository. Its session and identity are recorded in the manifest.
