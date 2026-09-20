# Plastic-package РФ5: anomalous read, 2026-09-19

Chip 10 in the loose-chip checks. The owner identifies it as an РФ5 in a
plastic case, the last chip from the second batch. Full markings and batch
code were not provided. Read with the existing standard 2716-compatible setup.

Two independent 2,048-byte captures match exactly, with this pattern:

- Address `0000`: `00`.
- Every odd address: `06` (1,024 bytes).
- Remaining even addresses: `04` (1,023 bytes).

This is **not an all-FF capture**, but it is not established as valid firmware
or trustworthy programmed contents. Apart from the first byte, the output
varies only with the lowest address bit. A programmed test pattern, contact
problem, read-path problem, or chip fault remain possible. A powered-off
reseat and a known-programmed control chip are useful next checks. The nine
preceding chips all read FF, and no known-programmed control has been tested
with today's setup.

The raw capture is retained as evidence, not identified as executable code.
Both reads returned zero and reported VCC/VPP safely off. No programming or
erasure was performed. Checksums and execution identities are in the manifest.
The host date is used; DOS clock timestamps are not acquisition dates.
Evidence includes per-run stdout and original cumulative WILLEM.LOG files;
earlier chip operations can precede the relevant final run in each log.

A subsequent [27256 capture](../27256-20260919-chip01/README.md) returned the
same pattern across 32 KiB, with its first 2 KiB identical to this image.
This points toward a shared read-path problem; this РФ5 has not been
established as faulty. The owner deferred further investigation of the chip.

A later [known EktaSoft AT28C64 control](../../juku/ekta37-low-control-20260919/)
passed two exact 8 KiB comparisons after changing to its DIP12B setup.
That validates the later AT28C64 configuration, but does not resolve this
capture or prove this chip faulty.

[Offline protocol analysis](../../analysis/20260919-programmer-echo/README.md)
reproduces every byte with a programmer-output echo model, including the
initial `00`. The exact physical cause remains unconfirmed.
