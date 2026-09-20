# RF5 recheck, 2026-09-20

One read after the owner replugged the USB serial connection succeeded with
unchanged conservative RF5 reader settings. The 2048-byte capture is nonblank
and no longer contains the previous `00 06 04 06 ...` programmer-output echo.
CRC16-CCITT is `BC39`. At the time of the first capture it was unverified; the second read below
confirmed repeatability. Firmware identity remains unknown. No additional hardware reads were launched because the
owner requested retries only when instructed. VCC/VPP safe shutdown and zero
exit status were reported. Original evidence is retained in `evidence/`.

This result does not establish what caused the previous anomalous captures
or validate the earlier all-FF dumps. Full chip marking remains unavailable.

## Second read

A second explicitly requested read matched all 2048 bytes exactly. The
capture is now verified repeatable; firmware identity remains unknown.
The second command returned zero and reported safe VCC/VPP shutdown.
See `evidence/read2/` and `manifest.json` for its acquisition records.

[Offline strings and CPU survey](analysis/README.md) found no recognizable
text or convincing CPU identification; candidate disassemblies are retained.
