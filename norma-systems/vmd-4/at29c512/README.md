# AT29C512 PLCC32: anomalous first capture

Owner provenance: Norma Systems VMD-4 Mainboard v1.1, 1999. Acquisition
2026-11-07 using the top onboard socket identified by owner as PLCC32,
Normal routing DIP634, 5V and programming VPP off as instructed. Owner
confirmed insertion and jumper setup; pin31 WE/read rails were not measured.

RD29V1.COM / R29C512 /PROFILE:conservative /FASTADDR completed with exit 0,
65536 bytes, read_ms=359095 and logged VCC off/VPP off. Transfer CRC verified.
However the data is **02 at offset 0000 and BF at every other offset**.
This is anomalous, not accepted as firmware and not confirmed blank or failed
silicon. Onboard routing, WE/CE/OE levels, supply and contacts need checking.
Software success and stable transfer do not prove correct electrical reads.

CRC32 cb2769ff; SHA256
bed8b303ec4394b75d1d39226cae09d5006a926e25f0f473177d8515984ffbb9.
Reader SHA256 d9e0ef92cd6cec65fe8a93b74610b4d8e070f78c3e0e78d40ebb88465934af46.

Original binary, logs, session metadata and execution ID 112047927 are retained
locally in /home/ddanila/fun/dosravi/sessions/norma-vmd4-at29c512-20261107-read1/.
No anomalous binary is added to the firmware collection. One capture only.
The program's printed external-adapter wording differs from the actual onboard
normal PLCC32 socket used, as recorded in the original session notes.

## Retry after reseating

Owner tried fitting the chip better and authorized a second read on 2026-11-07.
Session: /home/ddanila/fun/dosravi/sessions/norma-vmd4-at29c512-20261107-read2/.
Read time 358985 ms; 65536 bytes; reader exit 0; VCC/VPP-off logged.
The new capture is FF at offset 0000 followed by 65535 BF bytes. Only the first
byte differs from read1 (02 became FF); the suspicious constant body remains.
CRC32 `7e2d3475`, SHA256
`d58d884ededd937eb904b994fb6efe3baf145785dd131564096b04201cea5635`.
Reseating has not produced a plausible image. Continue electrical/routing
checks rather than treating either capture as valid firmware. Both files
remain in local diagnostic sessions.

## Original-software investigation and reader correction

On 2026-11-07 the unmodified Willem 0.97ja application was run under Wine
with a synthetic IO.DLL, PCB3 mode and AT29C512 selected. Its DIP setting
matched the photographed switches (3,5,6,10,11 ON). One complete virtual read
visited 0000-FFFF; all 524288 data samples used raw LPT CONTROL=05h.
That holds DB25 pin17 HIGH. RD29V1 instead used 0Dh and held pin17 LOW.
The PCB5.0 schematic routes pin17 through DIP11 to chip pin31 /WE; /WE
must be high for reading. The reader therefore had a confirmed control-level
error, a likely cause of the BF captures. Those captures remain invalid.

Build `dosravi-at29c512-we-fix-v2` corrects startup/shutdown and has a
regression model that rejects the old startup. It was subsequently used for read3 below; contact or other hardware faults
are not ruled out.
No jumper change is indicated by the original-software comparison.

[Reader investigation and reproducible tools](https://github.com/ddanila/willem-v30/blob/main/docs/original-at29c512.md).
Private emulator evidence is in
`~/fun/dosravi/sessions/willem-original-at29c512-20261107/`.

## Corrected-reader physical attempt (read3)

Owner authorized one more read with the existing PLCC32/DIP634 setup.
`RD29V2.COM`, build `dosravi-at29c512-we-fix-v2`, SHA256
`937e232bd00ee32480c3ed29dd6378f3792888921b9ab7fb70fc7dd6901397e4`,
was uploaded and executed with `R29C512 VMD29R3.BIN 378
/PROFILE:conservative /FASTADDR`.

The initial upload timed out after 20992 acknowledged bytes, before any EXEC
request. DOSRAVI's exception incorrectly mentioned an EXEC timeout; the
transaction log shows PUT_DATA was the failing command. A new session resumed
the same upload at offset 20992 and completed it with CRC32 `593c23e7`.
There was only one physical read, execution ID `929376241`.

Read time 359370 ms; execution time 360525 ms; exit 0; explicit VCC-off and
VPP-off shutdown logged. Download size and CRC verified. Result:

- 64742 bytes FF, 732 bytes 04, 62 bytes 06.
- Every non-FF byte falls at offset 125, 126 or 127 within a 128-byte block.
- Distribution `(offset modulo 128, value)`: `(125,04)` 222,
  `(126,04)` 284, `(127,04)` 226, `(127,06)` 62.
- CRC32 `695c465d`; SHA256
  `68568fe682e451dc8166761c658522c527bd2187d14285c4c5bab0b249ea204c`.

The constant BF output is gone. This remains an unverified candidate data
capture, not evidence of a blank or defective chip. Subsequent EPROM analysis
found 128-byte flash read/write routines and deliberate page-end data storage;
the spacing alone does not establish a read-path fault. The inferred access-code
bytes are FF in this capture, so meaningful configuration is not yet confirmed.
See [firmware analysis](../analysis/README.md). No further read was started
automatically.

Raw capture and complete evidence remain locally in
`~/fun/dosravi/sessions/norma-vmd4-at29c512-20261107-read3-resume/`.
The incomplete-upload evidence is in the corresponding `...-read3/` session.
