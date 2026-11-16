# Probable Nokia MAC4 family — MAC 3.04

Owner-reported M27C2001, read on 2026-11-16 using the T48 with
`M27C2001@DIP32`, ID test disabled. A subsequent owner-supplied
[photo](photos/PXL_20261116_173434247.jpg) confirms the 32-pin ST EPROM marked
`M27C2001 -15F1`, `V88AB`, `9348C`, `SINGAPORE`. The sticker reads
`MAC4` and `V:3.04`; its worn lower identifier is not reliably transcribed.
The source board remains unknown.
Both read commands exited zero and produced identical 262144-byte (256 KiB)
images. CRC32: `8012F03B`. SHA-256 is recorded in `SHA256SUMS`.
No repeated whole-image period of 256, 1024, 8192, 32768, 65536 or 131072
bytes was found. Repeatability does not independently validate every stored bit.
No firmware-specific checksum has been identified or validated.

## Identification and investigation

The embedded string at file offset `0x63E6` is
`FRONT:xxx   MAC:3.04  93-10-13`. Menu content strongly suggests an analog
satellite receiver with MAC decoding and subscription-card facilities;
manufacturer, receiver model and exact MAC standard remain unconfirmed.

Observed strings include service and receiver setup menus, channel scanning,
LNB standby, dual-band input, PAL/MAC baseband video gain, TV format,
smart-card selection, subscription information, pay-per-view locks, parental
control, and PIN changes. These are evidence of menu content, not proof that
all corresponding hardware features are enabled. Ten language choices are
listed: English, Swedish, Danish, Norwegian, Finnish, Dutch, German, French,
Italian and Spanish. Some accented letters use custom character codes.
All 708 printable runs of at least eight bytes are in `strings.txt`, with file
offsets; some runs may be incidental machine-code bytes.

The first bytes `02 00 2E` decode as 8051 `LJMP 002Eh`. At `002Eh`,
`C2 B1 C2 D3 C2 D4` clear bits, followed by `90 60 00` (MOV DPTR,#6000h),
`74 FF` (MOV A,#FFh), `F0` (MOVX @DPTR,A), and an external-memory fill loop.
Further startup instructions clear internal RAM and initialize PSW and SP.
This coherent startup supports an 8051-family interpretation. The subsequent [firmware investigation](analysis/README.md) recovered the
banking and menu structures and executed original instructions with synthetic
peripherals. Exact CPU marking and receiver model remain unconfirmed.

The investigation includes a [searchable multilingual catalog](analysis/menus/out/catalog.html),
service-menu analysis, code references and a reproducible emulator harness.

## Preservation and availability

No exact local repository match. Bounded web searches on 2026-11-16 for
CRC32 `8012f03b`, SHA-1 `d7b1867eebdf6529ac0484509414e05667ca7f49`,
`MAC:3.04`, `93-10-13`, and `FRONT:xxx` did not locate an exact public dump.
No candidate binary was found to compare. This is not proof of uniqueness.

Raw logs, acquisition metadata and analysis are in `evidence/`. Full local
session: `/home/ddanila/fun/dosravi/sessions/orphan-m27c2001-t48-20261116-192729/`.
Only read operations were performed, with no programming, erasing or ID test.
Minipro warns of incomplete T48 support and outdated programmer firmware.
Reported USB supply voltage is not an independent chip-pin measurement.
