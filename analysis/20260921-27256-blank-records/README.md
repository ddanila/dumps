# Corrected-reader blank 27256 records

Physical chips 02, 04, 05, and 06 each returned 32768 bytes of FF using
`RD256V2.COM` and conservative timing. Each record describes one successful
read, consistent with a blank chip; repeatability and known-programmed 27256
control validation remain absent. Chip 03 instead produced the separately
preserved FF/F7-only capture. Chip 01 has not been reread with the corrected
reader.

No all-FF binaries are included. The JSON files preserve local session
identities, checksums, exit status, and safe-shutdown observations. Original
captures and transport evidence remain in DOSRAVI sessions. Dates use the
host clock, not the Pocket8086 clock.
