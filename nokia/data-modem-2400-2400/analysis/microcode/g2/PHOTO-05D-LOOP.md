# The photo-candidate 05D–063 ROM loop

The corrected cyclic-ROM screen lists 05E and 061 as D-fed register writes
under q1/q2. A diagnostic ROM gate that selects **both** sites has three raw
PROM-bit terms and activates 81 of the 1,024 words. This gate is one fitted
alternative, not a traced read-enable net.

[`photo_05d_loop.py`](photo_05d_loop.py) applies that gate to the q1
photo-constrained mapping and tests both Am27S31 banks. Starting at PC 000,
**none of the 256 initial Q values reaches 05D, 05E or 061** within 512
cycles under either bank. This is a reachability result for the declared
reset scenario, not a claim that the hardware never enters the routine. The
saved reset outcomes do include other recurring paths near 389–3FA for some
Q seeds; those are separate candidates to test with controller stimulus.

A separate **diagnostic local entry at 05D** tests what the code would do if
entered. All 256 Q values and both banks run cleanly for 128 instructions.
Q remains unchanged in every case; Q=0 reaches the modeled 084 terminal,
while the other 255 values keep repeating near 05F. Saved trace witnesses
for Q=0, 1, 127 and 255 show that both 05E and 061 repeatedly read the same
ROM address `bank + ((Q + 1) mod 256)` and produce the same ALU Y,
`(Q + ROM[address]) mod 256`, on every visit. For example, Q=127 reads
`080→21` and produces A0 in the lower bank, or `180→09` and produces 88 in
the upper bank (all values hexadecimal).

This is a stationary Q-indexed lookup in this local fixture, not a running
phase accumulator or line waveform. A caller could still update Q between
invocations; the caller and physical output route are not established. The
[report and full Q=127 witness](results/photo-05d-loop/) preserve the
mapping, scenario, gate, ROM bytes, trace and limitations.
