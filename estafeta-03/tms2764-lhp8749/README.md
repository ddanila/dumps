# Estafeta-03 — TMS2764 LHP8749 set

The owner reports two chips with identical markings: `TMS 2764-20JL LHP8749`.
They are labelled `01` and `02`; both have now been acquired. Static code and
string analysis strongly attribute this set to the **Estafeta-03 family**.
Exact source-board provenance, PCB positions, and firmware revision remain
unconfirmed. The two images form even/odd halves of 8086-compatible firmware;
see the evidence and limitations below.
Identical physical markings do not imply identical ROM contents.

## Label 01

- Image: `label01.bin`, exactly 8,192 bytes.
- Two independent full reads matched byte-for-byte, without a chip swap.
- CRC16-CCITT: `7557`; CRC32: `F4FFFEA1`.
- SHA-256: `82a53447a1832d5040bcb919c8cc45e54a8f59f1ba7991040965285d5f843c9c`.
- Non-uniform data: 244 distinct byte values and 21 distinct 256-byte pages.
  Not an all-zero/all-FF image or a single 256-byte page repeated throughout.
  Repeatability is not comparison against a trusted reference image.

## Label 02

- Image: `label02.bin`, exactly 8,192 bytes.
- Two independent full reads matched byte-for-byte, without a chip swap.
- CRC16-CCITT: `8845`; CRC32: `F404B705`.
- SHA-256: `4b1fcd3ec5b051ec9b189e6badc088d928d64f5eeceeaad87740543bd295b5fa`.
- Non-uniform data: 242 distinct byte values and 21 distinct 256-byte pages.
  Not an all-zero/all-FF image or a single repeated 256-byte page.
- The two chip images are distinct, differing at 4,582 of 8,192 byte offsets.
  Their exact board provenance remains unknown.

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

Whitespace is normalized in the table. The banner and ring-network diagnostics
support the Estafeta-03 attribution alongside the code and external hardware
description below. No firmware was executed during this analysis.

From the repository root, reproduce the checksum-verified extraction:

```sh
python3 estafeta-03/tms2764-lhp8749/analyze_strings.py
```

The script resolves its input images relative to itself. It reports both byte orders, checks the known
banner, and prints shift-delimited strings with offsets without writing files.
The table also includes readable fragments interrupted by dynamic fields, which
are not emitted by the script's stricter complete-shift-span matcher.

## 8086 code and system attribution

The owner suggested the [RetroPC Estafeta-03 collection entry](https://retropc.org/Stanciya_Lokal_noj_Svyazi_(SLS)_Estafeta-03_s_142.html).
The page describes a КР1810ВМ86 CPU, two D2764A UV EPROMs, КР537РУ10 static
RAM, and selectable communication speeds of 300–19200 baud. This is a close
architectural match to our paired 2764 images and communications strings.
Our chips are marked TMS2764, not the D2764A parts described on that specimen;
the page is supporting hardware evidence, not a reference dump or proof of
the originating board.

Disassembly with `ndisasm -b 16` establishes coherent executable paths in the
`01`-even / `02`-odd reconstruction, not merely isolated valid x86 opcodes:

1. At image offset `0x3FF0`, the bytes `BC 00 53 EA AF 08 00 00` decode as:

   ```asm
   mov sp, 0x5300
   jmp 0x0000:0x08AF
   ```

   If the 16 KiB ROM is mapped at physical `0xFC000–0xFFFFF`, this stub lands
   at the 8086 reset address `0xFFFF0`. The far jump and following absolute
   accesses imply a low-address ROM mapping/alias as well. This is a mapping
   inference; the board's address decoding has not been verified.

2. The target at `0x08AF` begins coherent initialization: register setup,
   writes to I/O ports `0x20`, `0x22`, and `0x12`, `CLI`, stack setup,
   loading `ES = 0x0C00`, and a loop at `0x08F3–0x08F9` clearing
   `0x5000–0x5FFF` in the data segment. Later initialization executes `STI`.

3. With the low mapping inferred above, vector slots 8, 9, and 10 contain
   `0000:0083`, `0000:0186`, and `0000:0255`. The decoded interrupt code
   includes register saves/restores and `IRET` returns.

4. Calls at `0x0936` and `0x0983` both target `0x1F3F`. That routine obtains
   the saved return address from the stack, reads successive inline bytes,
   and advances the saved address. Nonzero bytes are queued through `0x1FA5`;
   a zero terminator returns to the instruction after the string. Thus the
   banner following the call at `0x0983` is actual output data, not an
   accidental text match. Execution resumes at `0x0999` (`call 0x0F7B`).

Linear disassembly of the entire image incorrectly interprets embedded strings,
vector entries, and padding as instructions, sometimes displaying instructions
from newer x86 generations. Those are not evidence of a newer CPU. Conversely,
8086-compatible instructions alone cannot distinguish an 8086 from an 8088 or
other compatible processor; the two byte lanes and the external description
support the 8086 hardware interpretation.

Conclusion: very high confidence in **8086-compatible firmware**, with strong
**Estafeta-03 family attribution**. Exact revision and physical-board identity
remain unconfirmed without matching provenance or an independent reference ROM.
This justifies filing the set under `estafeta-03/`, while retaining that caveat.
It was previously archived at `unknown/tms2764-lhp8749/`; the move preserves
the original chip bytes, checksums, acquisition metadata, and read logs.

To reproduce selected disassembly without creating a combined ROM file, run
from the repository root (Python 3 and NASM's `ndisasm` required):

```sh
python3 - <<'PY'
import hashlib
from pathlib import Path
import subprocess

root = Path('estafeta-03/tms2764-lhp8749')
rom = bytearray(16384)
rom[0::2] = (root / 'label01.bin').read_bytes()
rom[1::2] = (root / 'label02.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest() == (
    'cdfa3999780ac80e96b7ca4e0d575c6cf3c9467cf66cc99dd88bb9f3268b7f0f')
for start, end in [(0x3FF0, 0x3FF8), (0x08AF, 0x0939),
                   (0x0983, 0x0986), (0x0999, 0x099C),
                   (0x1F3F, 0x1F59), (0x1FA5, 0x1FAE),
                   (0x1FB1, 0x1FCD)]:
    subprocess.run(['ndisasm', '-b', '16', '-o', str(start), '-'],
                   input=rom[start:end], check=True)
PY
```

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
