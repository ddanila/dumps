# Known-ROM search, 2026-09-24

Searched exact SHA256 9789107c12b6630e8d48b6a65411e80f2ededcee6ab05c23093bbb864fc01e7b,
SHA1 0bcfaf89ae59f5857e9334f27fc3bd8379603835, CRC32 b134c0a6, PRU_AC with date
and firmware/ROM terms, Landis Unigyr PRU EPROM dump. No matching public ROM
located. Also searched local MAME src/ and hash/ for the hashes and distinctive
Landis/PRU_AC strings: no matches. This does not establish Internet uniqueness.

The manufacturer service manual CM2B8205E (January 1998), hosted at
https://files.elektroda.pl/388561%2Cb8205e.html identifies PRU process units and
page 247 device functions AC (air conditioning), HT (heating), HA, RMC, V1, WILO.
Those abbreviations also occur together in this capture, supporting a PRU-family
HVAC firmware attribution. Exact PCB model and CPU remain unconfirmed.

Chip 6: also searched exact SHA256
38c3e5063a880da016f630b11faba7d5e9292268ab0e90f475df86641ef7c749,
SHA1 036ab6f66ec37d77fb4302682952af32a10d4b3f and CRC32 a0a09b07:
no web results; no hash matches in local MAME src/ or hash/. No identifying
ASCII banner available; same-board family searches above also apply.

Chip 1: searched exact SHA256
b60273ce5c952e11f6fcc5080c1539999e8f70c5ba6887e24c669802a72445ad,
SHA1 c7a4d6d73cde9d292c2e9c1400bf1177e0cdd658 and CRC32 8ab497de:
no web results or local MAME hash matches. No identifying ASCII banner.
This limited search does not establish Internet uniqueness.

Chip 2: searched exact SHA256
3474e719859a4509cd201c3397ef4295791459fcd4c837efd93df02b6fe29054,
SHA1 f195acec1a0bf4f0de10691216956fd62c2365b1 and CRC32 3ee0f6fd:
no web results or local MAME hash matches. No identifying ASCII banner.
Capture has a 128-byte repetition period; stored-data/address validity unresolved.

Chip 3: searched exact SHA256
78f4dddd7deeb1fe4ae552d9deeaac8fed70661e3bdce46be8650624d1775854,
SHA1 8d61c6561a7a7d86122e2210d390e782747eb38b, CRC32 c18f8919 and
SJ.SM4:PULSSI_LASKURI: no web results or local MAME hash matches.
This limited search does not establish Internet uniqueness.

Chip 4 (2026-09-25 Europe/Tallinn): searched exact SHA256
43d4d3f61605718d4945fbefe630c49e337db96fa7e0274f4d61a1d605fa92b5,
SHA1 9c34eda70f1a8a97ee52dfd60d28b6065183f923, CRC32 d0fe2145 and
SM.SM1:PULSSI_LASKURI: no web results or local MAME hash matches.
This limited search does not establish Internet uniqueness.

Update, 2026-09-25: subsequent disassembly identifies the executable ISA as
Motorola 68HC11. Manufacturer PAA1 documentation strongly supports a PRU1
program-card attribution; exact board and CPU variant remain unresolved.
See `../analysis/README.md` for sources, alternative-CPU comparisons and the
passing original firmware checksum. The initial acquisition notes above
record the identification state at the time of each read.
