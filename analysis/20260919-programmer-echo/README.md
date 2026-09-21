# Offline analysis: RF5 and 27256 programmer-output echo

## Finding

Both anomalous captures exactly match a model in which the readback path
returns the programmer's last parallel data-output value instead of ROM data.
The model uses the actual `willem-v30/src/willem.c` core, with callbacks that
simulate this fault. It reproduces every byte, including the special first
`00`: zero differences across 2048 bytes for RF5 and 32768 bytes for 27256.
This is strong evidence for programmer-output echo, not proof of its physical
cause. No hardware operations were performed during this analysis.

The model explicitly assumes that data routed to the parallel output bus is
retained and appears at the serial readback input. It is a behavioral fault
model, not a verified transistor-level schematic of this PCB5.0E clone.

## Why these particular bytes appear

The core shifts addresses most-significant bit first using LPT D0 as clock
and D1 as serial address data. At the end of an address shift:

- D0 is low because the last clock pulse has ended.
- D1 contains address bit A0, contributing `00` for even addresses or `02` for odd.
- D2 is initially low, but the first read's serial input-clock sequence leaves
  it high. Subsequent address shifts clear D0/D1 while preserving D2 (`04`).
- D3 through D7 stay zero in this read sequence.

When the multiplexer returns to the parallel-data position, the output is
therefore `00` for the initial address-zero read, then `04 | (A0 << 1)`.
That predicts exactly `00 06 04 06 04 06 ...` for sequential reads from zero.
The isolated first byte is explained by reader initialization, without any
special ROM content at address zero. A13/A14 and all other upper address bits
do not affect this signature because only the final shifted bit remains on D1.

The upstream [pinned Geepro driver](https://raw.githubusercontent.com/danielg4/geepro/a08efcaf6479730d552c5f96bad0a2a01bf0635f/drivers/willem.cpp)
contains the corresponding D0/D1 address shift, multiplexer switch, and D2
read-clock sequence in `willem_set_par_addr_pin` and `willem_get_par_data_pin`.
This supports the signal interpretation; it does not establish the exact
physical fault on this board.

## Evidence and limits

| Capture | Size | Differences from output-echo model |
|---|---:|---:|
| RF5, both original reads identical | 2048 | 0 |
| 27256, one original read | 32768 | 0 |
| Known EktaSoft AT28C64 control, both reads match reference | 8192 | 8102 |

The RF5 anomaly predates the new R27256 command and larger DOS buffer.
The same new executable subsequently read the known AT28C64 image correctly
twice. This argues against the new buffer/file-writing code or a persistent
serial-transfer problem as the common cause. The modeled protocol core was
unchanged by the R27256 addition; its hash is recorded in `results.json`.

All runs log initial `DATA=00 STATUS=77 CONTROL=0b`, including the successful
control. These idle snapshots do not distinguish success from failure.
No per-byte hardware trace or live voltage measurements were captured.
The saved DIP diagrams show software requirements, not measured switch state.

Both failures used DIP8 ON and DIP4 OFF; the good AT28C64 used DIP8 OFF and
DIP4 ON. RF5 used special 2716 routing, while 27256 and AT28C64 used Normal.
The failed EPROM reads used 5 ms power settling; the successful EEPROM reads
used 200 ms and a different startup control order. These are correlated
changes, not enough evidence to assign blame to a particular switch or delay.
After startup, 27256 and AT28C64 use the same byte-read routine and final
steady-state control settings; RF5 differs in the DB25 pin17 control level.

## Likely explanation and next discriminating checks

The leading interpretation is that the chip did not successfully drive the
read bus and the programmer's output state was read back. Possible causes
include a disabled chip (CE/OE or EPROM read-mode routing), missing chip power,
poor contact, a defective chip, or a programmer buffer/multiplexer problem.
A simple address-line alias alone does not naturally explain why two different
chips reproduce the programmer's initial state and A0-dependent output exactly.

The successful AT28C64 test demonstrates working transport and data capture
in its current configuration, but cannot validate the EPROM-specific paths or
retroactively classify the previous all-FF reads as blank.

Useful follow-up experiments, not performed here:

1. Check EPROM read-mode supply and enable levels at the chip pins against
   its actual datasheet, with its correct DIP/routing configuration.
2. Test a known-programmed EPROM in the appropriate EPROM setup to distinguish
   EPROM routing/control from a fault in the unknown chips.
3. Use a read-only diagnostic with a changed address order. The echo model
   predicts the startup exception follows the first operation rather than
   always ROM address zero, and subsequent data follow A0 alone. This would
   distinguish reader-state feedback from fixed stored bytes. Such a diagnostic
   should be implemented and reviewed separately, without changing write lines.

## Reproduce the model

From this dumps repository:

```sh
cc -std=c89 -Wall -Wextra -Werror \
  -I/home/ddanila/fun/willem-v30/include \
  /home/ddanila/fun/willem-v30/src/willem.c \
  analysis/20260919-programmer-echo/model.c -o /tmp/willem-echo-model
/tmp/willem-echo-model rf5 > /tmp/rf5-echo.bin
/tmp/willem-echo-model 27256 > /tmp/27256-echo.bin
cmp /tmp/rf5-echo.bin /home/ddanila/fun/dosravi/sessions/rf5-20260919-chip10-read1/RF510A.BIN
cmp /tmp/27256-echo.bin /home/ddanila/fun/dosravi/sessions/27256-20260919-chip01-read1/E25601A.BIN
```

The anomalous captures and acquisition records are retained only in local
DOSRAVI sessions, because output echo is not ROM content. The comparisons
require those local files and originally exited zero. Capture and model SHA-256 values are in
`results.json`. No programmer access is required.

## Later finding

The [27256 code audit](../20260920-27256-ce-audit/README.md) identified an
incorrect high CE state in R27256 v1. The comparison above describing the
same 27256/AT28C64 steady-state control was a description of that buggy code,
not a valid requirement. The corrected 27256 startup holds CE low. This
does not identify the cause of the earlier RF5 echo.
