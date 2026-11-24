# Actual sine-ROM bytes reach arithmetic under a selected-read hypothesis

*Runs under the [shared assumptions](ASSUMPTIONS.md).*

The earlier [global ROM-feedback experiment](ALU-FEEDBACK.md) replaced every
external read, including handshake replies, and reached only zero operands in
its sampled arithmetic calls. The [independent component path](PAIRED-COMPONENTS.md)
now provides a concrete place to test a qualified ROM read while retaining the
other input assumptions. This experiment feeds actual dump bytes into that
path; it does not recover the physical ROM enable or address latch.

## Scenario contract

The integrated runner now permits `io.read.mode: pc_sequence` together with an
`address` policy containing a nonempty `pcs` list. Only those instruction
addresses sample the Am27S31 dump; other instructions retain their independent
external sequences or default input byte. For this experiment:

```json
{
  "source": "previous_y",
  "bank": 256,
  "initial_y": 0,
  "pcs": [791],
  "status": "hypothesis",
  "evidence": "Diagnostic ROM read at 317; physical read qualification unknown"
}
```

791 is hexadecimal 317. Address is bank plus the preceding instruction's Y.
The existing unconditional previous-Y update policy is retained, even outside
ROM-read sites. The read object also requires the expected dump SHA-256:
`312fa21f50203c7b84ec0a4b4aea62ca343b2a579c38687111342368b1f04d58`.
Duplicate/out-of-range sites, overlapping per-PC byte sequences, missing
provenance and bad ROM hashes are rejected. The old global `am27s31` mode and
ordinary PC-keyed reads retain their execution behavior.

Each actual ROM read logs address, byte and whether the ALU selects D. Summary
counts include only those qualified ROM reads, separately from sequence visits.
A physical read strobe is not inferred from the choice of an instruction PC.
The scenario still models ROM-backed dispatch independently; it is not a
reconstruction of a shared physical bus or its arbitration.

## A complete reset-to-result path

The q3 scenario retains Q=5, Q-based handler-5 dispatch, captured V=0001,
previous flags, early handshake replies, and the later zero reply at 36D.
At 316, supply `(phase-5)&FF`. Its D+Q calculation exposes the phase on Y.
At 317, the selected ROM read supplies `S = ROM[100 + phase]`, so R4 becomes
`U = S+5`. The wrapper copies U to R8/R9 and calls entry 0 of paired arithmetic.
All addresses in this paragraph are hexadecimal except the phase and byte
values used in the formulas.

For phases 0–64, actual ROM bytes equal
`round(127*sin(pi*phase/128))`. The first output word is `2*(S+5)` and the
second is 0002. Every phase reaches 084. Representative byte and output values:

| Phase (decimal) | ROM address (hex) | ROM byte (decimal) | First output word (hex) | Second word (hex) |
| --- | --- | --- | --- | --- |
| 0 | 100 | 0 | 000A | 0002 |
| 32 | 120 | 90 | 00BE | 0002 |
| 64 | 140 | 127 | 0108 | 0002 |

Zero-based microinstruction timing is stable across all phases: 316 exposes
the address at cycle 44, 317 reads the ROM at 45, the first arithmetic output
byte appears at 55, and the terminal loop begins at 110. This is ten modeled
microinstructions from read to first result, not a time in seconds or a
recovered sample rate. Each phase is a separate reset scenario; the experiment
does not demonstrate autonomous phase advancement or continuous waveform
output. No DAC write is identified.

The ROM is read exactly once per run. In all q3 cases it is selected as an ALU
operand, and its effect survives in R8/R9 through termination. At phases
0/32/64, replacing only the 317 ROM read with a zero external byte preserves
the prefix through the address setup and changes the first output to 000A.
The output difference is exactly twice the real ROM byte. Thus this is an
operative input, not merely a sampled-but-unused lookup.

Under matched q1 inputs at phases 0/32/64, 316 does not expose the requested
phase: it exposes zero. 317 samples ROM[100]=0 but does not select D. Its first
output stays zero. These controls distinguish mapping hypotheses; they do not
prove the q3 mapping or the site-qualified ROM policy is physically correct.

## Evidence and limits

[Configuration](sine-operand-study.json), [runner](sine_operand_study.py), and
[report](results/sine-operand-study/report.json) retain all assumptions, source
hashes and outcomes. There are 65 q3 phase runs, three q1 controls and three
zero-input counterfactuals, all clean for 160 instructions. Nine full witness
directories retain the three phase boundaries, both profiles and the zero
controls. The full experiment reproduces byte for byte.

The 93-test suite checks interleaving sequence and ROM inputs, address feedback,
read accounting, invalid site lists/hash rejection, and this nonzero reset
path. The existing global-ROM million-cycle trace digest is also rechecked.
This supplies an explicit assumed connection between the sine dump and live
microcode arithmetic. Physical read qualification, DAC writes, sample clock,
controller exchange and the purpose of the gain/offset remain unresolved.
Annotation coverage stays at 362 distinct words.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/assumed/sine_operand_study.py --out /tmp/nokia-sine-operand
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode -p 'test_*.py'
```
