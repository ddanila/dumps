# Upper I0 polarity opens ROM addresses, but no sustained byte motion

The [upper instruction sensitivity screen](UPPER-I-FIELD-SENSITIVITY.md)
found that inverting the candidate U8 I0 net makes a D4 pulse at `38E`
change three selected Am27S31 addresses. That is a useful clue, but its ROM
read count includes startup. A carrier requires the repeated loop to keep
changing a candidate output under a held input level. The
[execution screen](upper_i0_rom_liveness.py) checks that distinction with
the real four-PROM store and Am27S31 dump.

The screen applies the untraced upper-I0 inversion to the separated-slice,
upper-B candidate mapping. It runs **all 256 initial Q bytes** with D4 held
low and high at candidate input `38E`, 1,000 microcycles each. Of those, 32 Q
values reach `389` at least 20 times under both levels. It then traces those
64 eligible runs and tests all eight A8 bank choices at ROM-read PCs
`389/38A/38C` under both input levels at Q=`05`. The chosen D4 byte is held
across visits, so this is a sustained-input check rather than a new bit on
every loop iteration.

Every eligible run becomes constant after the first eight visits at each of
the ten repeated loop PCs. At each of the three ROM-read sites, the selected
address **and byte** are then fixed. For Q=`05`, the default-bank candidate
settles to these levels:

| Held D4 | `389` ROM address / Y | `38A` ROM address / Y | `38C` ROM address / Y | `39E` Y |
| ---: | --- | --- | --- | ---: |
| 0 | `104` / `D6` | `1D6` / `16` | `106` / `08` | `0B` |
| 1 | `124` / `56` | `156` / `46` | `106` / `28` | `0B` |

Addresses are three-digit hexadecimal. Over the *whole* 1,000-cycle run,
some cases select 19–25 ROM addresses, but these are startup/transient
reads; the recurring part selects one address per site. Independently
switching A8 at `389/38A/38C` changes selected ROM operands and sometimes
their ALU Y values, but **all 16 bank runs still settle to one Y and one ROM
address per repeated site**. Thus the ROM operand is not merely ignored in
this mapping; it contributes to a static held-input result. Neither the
ROM-address excursion nor those static levels form a sustained carrier in
this fixture. `39E` stays `0B` for all eligible Q values and both held bits.

The [result JSON](results/upper-i0-rom-liveness.json) records each eligible
Q, per-site tail values, bank alternatives, trace digests and source hashes.
The I0 inversion, upper B field, split-slice links, D38E input route and
ROM A8 drivers are hypotheses. A constant ALU Y is not a DAC measurement.
The next test should look for a clock or mapping that advances a retained
phase/ROM address under held symbols, or an independent repeated output path;
the absence of a physical pin trace is not a reason to stop.
