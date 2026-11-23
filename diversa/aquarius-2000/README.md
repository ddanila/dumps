# Aquarius 2000 Q-meter

Owner identifies the source as an Aquarius 2000 Q-meter and the EPROM as a
27256. The image contains `Diversa Ltd.` at 0x126B and
`AQ 2000   S/N:Unknow` at 0x35BB. Board position, chip markings and firmware
revision have not been recorded.

## Acquisition — 2026-11-23

Two independent read-only T48 captures using minipro 0.7.4 and
`minipro -p M27256@DIP28 -x -r OUTPUT.bin` exited successfully and matched
byte for byte. Chip-ID probing was skipped. No programming or repairs were
performed. The tool reports T48 firmware 00.1.03 and warns that T48 support is
incomplete and firmware is older than expected; both acquisition logs are retained.

[Raw 32 KiB dump](aquarius-2000-27256.bin)

- Size: 32,768 bytes, nonblank, 255 distinct byte values.
- SHA-256: `958d3c99aa6b8bf7274a59d6742e516b068e7b2c5fb13c26d64f709a55965a57`
- CRC32: `054481d8`

Strings include supply/return calibration, clock setup, RAM test, sensor
errors, and hourly/daily/monthly history menus. No internal checksum has
been established.

No full-image contiguous match was found in the existing repository ROMs
checked (see manifest). Web searches for the model with firmware, Diversa
with AQ 2000, and the CRC32 found no relevant public firmware candidate.
This limited search does not establish uniqueness.

[Manifest and string offsets](manifest.json) · [Acquisition evidence](evidence/)

Both raw reads remain in the local programmer session
`aquarius-2000-27256-20261123-175119`; the identical image is stored once here.
