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
