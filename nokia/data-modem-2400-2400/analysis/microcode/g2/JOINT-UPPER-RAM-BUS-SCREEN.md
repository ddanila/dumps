# The fixed receive loop has no direct RAM address or active-low write pulse

The [echo washout](JOINT-UPPER-ECHO-WASHOUT.md) found that the modeled
Am2901 state loses its own-echo history within three ADC visits. The
[DSC 3557 front photograph](../../../photos/PXL_20261123_114811760.jpg)
shows four `MCM93422PC` RAMs in a cluster, with a visible `74LS163`
counter and `74LS157` multiplexer nearby. The RAMs have 256×4 bits each;
the [93422 family data](https://bitsavers.trailing-edge.com/components/motorola/_dataBooks/1989_Motorola_Memory_Data.pdf)
describes separate data input/output and active-low write and output
enables. TI identifies the [74LS163](https://www.ti.com/product/SN74LS163A)
as a four-bit binary counter and the [74LS157](https://www.ti.com/product/SN74LS157)
as a four-channel, two-input selector. These are component identities
and capacities, not traced connections or an established tap-memory
organization.

This [PROM screen](joint_upper_ram_bus_screen.py) executes the joint
upper-source mask-`08` receive loop twice for 2,048 selected `3F8` ADC
visits each: once with constant code `127`, once with deterministic
varying codes `80…176`. It examines the eight reached words `3EA`,
`3EB`, `3EC`, `3F7–3FA`, `3ED` and their four raw PROM bytes.

Only three of the 32 bare PROM bits assert at **exactly one** of those
eight words, identically in both runs:

| Raw bit | Sole high word |
| --- | --- |
| U18 D2 | `3EC` |
| U18 D4 | `3EC` |
| U18 D7 | `3EA` |

No raw bit goes **low** at just one word, so the active-low RAM write
enable cannot be a bare single-word low PROM output in this loop.
An inversion, gate or decoded address can still make a write pulse.
In the changing-ADC run, `3F8` Y takes 111 distinct values, `3F9`
63 and `3FA` 18, but their consecutive +1 modulo-256 counts are only
21, 87 and 159 of 2,047 transitions. The other five sites are
constant or nearly so. There is no simple per-visit 8-bit address
counter on a reached Am2901 Y byte under this fixture.

The cluster therefore offers a concrete next candidate to test: an
external address counter/mux driving the MCM93422 address pins, with a
decoded or inverted write strobe and a separate data latch. The
photograph does not show which pins or clock edges implement it, and
one four-bit 74LS163 by itself cannot supply all eight address bits.
The data returned from RAM to the DSC, any train/freeze control and
the line residual remain unidentified; C4 stays open.

The [machine report](results/joint-upper-ram-bus-screen.json) records
both trace digests, the raw words, per-site Y statistics and source/
photo hashes. Reproduce from the microcode directory with
`python3 g2/joint_upper_ram_bus_screen.py`.
