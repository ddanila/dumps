# AMI FA3 BIOS public comparison and removal

On 2026-11-27 the owner accepted the NM27C512Q capture as sufficiently represented
by the public Abit FA3 BIOS and requested removal. Its pending set record and
both local capture binaries were removed. Reader logs and result metadata remain
in `rom-programmers/sessions/nm27c512q-blank-check-20261127-070629`.

The closest public image is `ABITFA3.BIN` in
[abit-386dx-fa3.zip](https://theretroweb.com/motherboard/bios/abit-386dx-fa3-5ea4d7c538889909926304.zip),
linked from [The Retro Web’s Abit AB-FA3 page](https://theretroweb.com/motherboards/s/abit-ab-fa3).
It matches 65,532 of 65,536 bytes. At offsets `E13E`, `E13F`, `E145`, and
`E14B`, the capture has `00` and the public image has `04`, `0C`, `08`, and `11`.
These bytes lie in a zero-filled area following AMI’s copyright/address text.
The Sannata candidate also has zeros there, but differs elsewhere. Whether
these bytes are unused or the public copy is altered has not been established;
this is an owner-approved near-duplicate removal, not an exact-match claim.

[comparison.json](comparison.json) retains capture provenance, hashes, public
source URLs, all four candidate comparisons, and the small-difference listings.
The owner’s downloaded public archives were left intact.
