# Unidentified TMS2764 LHP8749 set

The owner reports two chips with identical markings: `TMS 2764-20JL LHP8749`.
They are labelled `01` and `02`; both have now been acquired. The original
system and PCB positions remain unknown. String analysis strongly supports
an even/odd interleaving of the two images; see the findings below.
Identical physical markings do not imply identical ROM contents.

## Label 01

- Image: `label01.bin`, exactly 8,192 bytes.
- Two independent full reads matched byte-for-byte, without a chip swap.
- CRC16-CCITT: `7557`; CRC32: `F4FFFEA1`.
- SHA-256: `82a53447a1832d5040bcb919c8cc45e54a8f59f1ba7991040965285d5f843c9c`.
- Non-uniform data: 244 distinct byte values and 21 distinct 256-byte pages.
  Not an all-zero/all-FF image or a single 256-byte page repeated throughout.
  No original system identity is claimed; repeatability is not comparison
  against a trusted reference image.

## Label 02

- Image: `label02.bin`, exactly 8,192 bytes.
- Two independent full reads matched byte-for-byte, without a chip swap.
- CRC16-CCITT: `8845`; CRC32: `F404B705`.
- SHA-256: `4b1fcd3ec5b051ec9b189e6badc088d928d64f5eeceeaad87740543bd295b5fa`.
- Non-uniform data: 242 distinct byte values and 21 distinct 256-byte pages.
  Not an all-zero/all-FF image or a single repeated 256-byte page.
- The two chip images are distinct, differing at 4,582 of 8,192 byte offsets.
  Their exact system identity remains unknown.

## String findings

Label `01` supplies even-offset bytes and label `02` odd-offset bytes of a
16 KiB reconstructed image:

```text
combined[2*i] = label01[i]
combined[2*i + 1] = label02[i]
```

Separate-chip ASCII scans show fragments such as `weiekd` and `wdt o:`.
This interleaving reconstructs `wwedite kod:`. Reversing the even/odd order
scrambles the text; simple concatenation leaves the fragments uncombined.
Offsets below refer to the reconstructed image, not an established CPU address.
The original chip dumps remain unchanged; no combined image replaces them.

The readable strings use KOI-7-style Russian with explicit `0Eh` / `0Fh`
shift delimiters. Bytes `60h..7Eh` map to uppercase Cyrillic (equivalent to
setting bit 7 and decoding those bytes as KOI8-R). Other printable bytes are
preserved. The banner's exact byte sequence is:

```text
0x0988: 0E 7C 73 74 61 66 65 74 61 0F 20 2D 20 49 49 49 00
             |  s  t  a  f  e  t  a       -     I  I  I
decoded: ЭСТАФЕТА - III
```

| Offset | Decoded text | Meaning |
|---|---|---|
| `093C` | ВВЕДИТЕ КОД: | Enter code |
| `0989` | ЭСТАФЕТА - III | Apparent system/firmware banner |
| `09F0` | ВЫЗОВ: | Call |
| `0A8D` | КОМАНДА: | Command |
| `129C` | РАЗРЫВ ( | Break/disconnection |
| `1395` | РАЗ"ЕДИНЕН | Disconnected (literal spelling in ROM) |
| `1974` | ОШИБКА | Error |
| `1981` | ЗАНЯТО | Busy |
| `198C` | МЕЖСЕТЕВОЙ | Internetwork |
| `1F22` | СОЕДИНЕН | Connected |
| `2327` | РАЗРЫВ КОЛЬЦА | Ring break |
| `2337` | УСТРАНЕН | Cleared/resolved |
| `2347` | ТЕСТ ОЗУ | RAM test |
| `2355` | ТЕСТ ПЗУ | ROM test |
| `2363` | ТЕСТ КОЛЬЦА | Ring test |
| `2374` | ОЗУ ИСПРАВНО | RAM operational |
| `2387` | ПЗУ ИСПРАВНО | ROM operational |
| `239A` | КОЛЬЦО ИСПРАВНО | Ring operational |
| `23AE` | ПРОЧИТАНО: | Read |
| `23BF` | ЗАПИСАНО: | Written |
| `23D0` | АДРЕС: | Address |
| `23E1` | КОНТР.СУММА: | Checksum |
| `23F2` | ЭТАЛОН: | Reference value |
| `2404` | ПЕРЕДАНО: | Transmitted |
| `2413` | ПРИНЯТО: | Received |

Whitespace is normalized in the table. These strings suggest firmware for a
ring-network controller or diagnostic device associated with "Эстафета-III".
This is a hypothesis from the dump contents, not a confirmed historical product,
board identification, CPU identification, or attribution to a manufacturer.
The banner and the diagnostics are directly observed; the device interpretation
remains provisional. No firmware was executed during this analysis.

From the repository root, reproduce the checksum-verified extraction:

```sh
python3 unknown/tms2764-lhp8749/analyze_strings.py
```

The script resolves its input images relative to itself. It reports both byte orders, checks the known
banner, and prints shift-delimited strings with offsets without writing files.
The table also includes readable fragments interrupted by dynamic fields, which
are not emitted by the script's stricter complete-shift-span matcher.

## Acquisition

Host acquisition date: 2026-09-06 (UTC). The DOS clock in the retained logs
shows 1980 and must not be used as the acquisition date.

The existing Pocket8086 / Willem PCB5.0E setup was accessed through DOSRAVI
0.1.1 at 57,600 baud using the CP2102 serial connection. The owner confirmed
each chip ready after the normal 2764 read-setup and unpowered-swap instructions. Expected
configuration: 5 V VCC, normal 28-pin routing, DIP ON 1/2/4/6/9, PCB3B selector
J9/J10 toward DB25, chip at the ZIF end opposite the lever with two empty rows
at the notch/lever end. Physical voltages were not remeasured in this session.
The [TI datasheet](https://www.bulcomp-eng.com/datasheet/Texas%20Instruments%202764JLT-25%20-%20Datasheet.pdf)
specifies 5 V read operation, with VPP at VCC.

Only `R2764` commands were issued, using the conservative timing profile.
Each read reported `read_ms=112035`, exit status zero, and safe shutdown with
VCC/VPP off. No programming, erase, or electronic-ID operation was issued.
The first upload and some downloads required serial retries; the transfer
protocol verified the artifacts, and the independent ROM dumps match.

The reader was the existing `willem-v30` build, uploaded under `RD2764.COM`:
SHA-256 `3909c219d41f6db463817ee45543cc063e024917b2adc4646a4019f9eb1ebe03`.
It reports build ID `dosravi-m2764a-write-v1`; that build name does not describe
this operation, which was strictly read-only.

Per-read output is retained in `evidence/`. Full transport sessions remain
locally under the sibling `dosravi/sessions/tms2764-lhp8749-label01-read1`,
`tms2764-lhp8749-label01-read2`, `tms2764-lhp8749-label02-read1`, and
`tms2764-lhp8749-label02-read2` directories. See `manifest.json` for execution
identities and `SHA256SUMS` for image verification.
