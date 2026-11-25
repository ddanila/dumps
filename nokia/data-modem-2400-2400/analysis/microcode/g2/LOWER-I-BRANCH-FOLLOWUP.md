# Alternate lower-instruction paths separate bit relay from ROM cycling

The [single-pin retention screen](LOWER-I-ADC-RETENTION-SCREEN.md) left 30
mappings outside its D3A1 comparison window. These are clean executions, not
model errors: a saved 512-cycle audit finds zero D3A1 visits in all 30;
16 still visit D38E and 14 do not. A
[follow-up run](lower_i_branch_followup.py) takes three representative
photo-compatible U11-to-U2 substitutions and executes 1,580
real-PROM microinstructions with Q=5 and zero initial RAM. The 128-bit 8031
scrambler fixture is offered at D38E, with all-zero and all-one controls.

| Lower instruction pin | Repeated path | Executed result after startup |
| --- | --- | --- |
| U2 I3←U11.1 | `38D/38E → 396–399` | `396`: previous D38E bit 0→`11`, 1→`31`; `398`: 0→`E5`, 1→`C5`. The other two ALU sites are bit-independent. |
| U2 I4←U11.0 | `38D/38E → 39A–39D` | `39A`: previous bit 0→`11`, 1→`31`; `39C`: 0→`E6`, 1→`C6`. The other two sites are bit-independent. |
| U2 I6←U11.0 | `3ED–3FA` | D38E is never reached. After startup, selected Am27S31 reads at `3F7` repeat addresses `11B, 101, 117, 11D, 113, 119, 11F, 105`. |

Each bit-dependent site changes on visits 1–127 between the all-zero and
all-one controller controls. The actual scrambler run follows the same
one-visit rule. These ALU values are still only a bit relay, not changing
carrier samples; the ROM addresses in the first two paths do not change with
the offered bit. The third path does traverse eight values of the photographed
ROM's quarter-sine region, but without controller input at D38E or a traced
DAC-bound output it does not establish a transmitter.

An `FF` impulse at the other selected input, D38D in the first two paths or
D3F8 in the third, changes modeled state at boundary 20 only. The next and
later observed boundaries, selected ROM addresses and reached `392–39F` ALU
events match the zero-byte control. The [report](results/lower-i-branch-followup.json)
records visit counts, exact bit rules, ROM sequence, differences and source
hashes. All substituted nets, input routes, clock and output latch remain
untraced hypotheses.

The quarter-sine address loop is a useful independent lead: test which
photo-compatible input or latch phase can couple its table values to a
controller-driven state and then to the DAC08 path. An ambiguous net does not
block that experiment.
The [3F7 dataflow check](LOWER-I-ROM-DATAFLOW.md) finds that the selected ROM
bytes do update R10, but no other RAM location, ALU Y or control path in the
tested loop; an isolated byte change is overwritten at the next `3F7` visit.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_branch_followup.py
```
