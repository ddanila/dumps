# Nokia external modem — Am27S31DC PROM

Owner identifies this as the last chip on the last board of the same old Nokia
external modem previously supplying the [four MMI PROMs](../microcode-810237c-810240c/)
and [2764 EPROM](../controller-810244e/). Exact modem model,
board identity, socket position and sticker are unknown. No shared address
space or concatenation with those images is assumed.

## Acquisition — 2026-11-23

Device marking reported by owner: **Am27S31DC**. This is a 512 × 8 bipolar
fuse PROM in a 24-pin DIP, with three-state outputs. Two independent read-only
T48 captures using MiniPro's `82S141` custom profile, with ID probing skipped,
yielded identical nonblank 512-byte images (129 distinct byte values).
No programming or byte repairs were performed.

[Raw dump](nokia-modem-am27s31dc.bin)

- SHA-256: `312fa21f50203c7b84ec0a4b4aea62ca343b2a579c38687111342368b1f04d58`
- CRC32: `c2ad8429`
- Byte sum modulo 256: `B3`; no internal checksum scheme is established.

## Read-profile verification

The [AMD 1980 Bipolar Generic PROMs databook](https://ftpmirror.your.org/pub/misc/bitsavers/components/amd/_dataBooks/1980_AMD_Bipolar_Generic_PROMs.pdf),
printed page 65 (PDF page 70), specifies the pinout and read enable levels.
These agree with the local MiniPro type-7 implementation: VCC 24, GND 12;
A0–A8 on 8,7,6,5,4,3,2,1,23; D0–D7 on 9,10,11,13,14,15,16,17;
CS1/CS2 (21/20) low, CS3/CS4 (19/18) high. Pin 22 is unused.

The first 16 bytes are `00 31 5A 75 7F 75 5A 31 00 CF A6 8B 81 8B A6 CF`:
a pattern consistent with signed sine-wave samples. This is a preliminary data
observation, not an established role for the PROM or proof of modem operation.
A web search for the CRC32 found no public match; uniqueness is not established.

[Manifest](manifest.json) · [Read logs and acquisition metadata](evidence/)

[Subsequent investigation](../) identifies the case as Nokia Data Modem 2400/2400 and confirms that the first 16 bytes exactly match a
rounded signed sine table. Association with sticker 810241 on DSC3557 remains
provisional.
