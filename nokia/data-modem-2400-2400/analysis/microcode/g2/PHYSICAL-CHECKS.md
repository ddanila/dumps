# Decisive unpowered continuity checks for DSC 2847

This is a **measurement worksheet**, not a recovered netlist. The board's
[inventory](../board/inventory.json) identifies U9 as the N8X02 sequencer;
U5/U6/U29/U30 are LS374 registers; U10/U11/U17/U18 are MMI6381 control PROMs.
The existing [net ledger](../board/nets.json) contains no complete executable
pin-to-pin nets. Record a meter beep or resistance for each tested pair, and
also record explicit open results. Do not promote a visual trace or a shared
ground/power connection into a signal net.

Use the **unpowered board** with all connectors disconnected. Number the IC
pins from the package notch/dot, not from the orientation of the text. U9's
control pins are AC0=27, AC1=28, AC2=1, TEST=26 and CLK=25; its address outputs
A0=3 and A1=4. The LS374 clock is pin 11 and its eight Q pins are
2, 5, 6, 9, 12, 15, 16, 19. On each control PROM, A0=8, A1=7 and D0=9.

| Priority | Hold one meter lead on | Probe these pins | Question settled |
| --- | --- | --- | --- |
| 1 | U9.25 (CLK) | U5.11, U6.11, U29.11, U30.11 | Are sequencer and instruction registers clocked together? |
| 2 | U9.27 (AC0), then U9.28 (AC1), then U9.1 (AC2) | LS374 Q pins on U29/U30 first, then U5/U6 if no connection is found | Which stored PROM bits issue the sequencer command? Record every connected Q pin and any multiple connections. |
| 3 | U9.26 (TEST) | The same LS374 Q pins | Is the branch test driven by a stored microinstruction bit? |
| 4 | U9.3 (A0) | U10.8, U11.8, U17.8, U18.8 | Does sequencer address bit 0 reach the four PROMs without permutation? |
| 5 | U9.4 (A1) | U10.7, U11.7, U17.7, U18.7 | Does sequencer address bit 1 reach them without permutation? |
| 6 | U10.9, U11.9, U17.9, U18.9 (each PROM D0) | U5.3, U6.3, U29.3, U30.3 (each LS374 D0) | Confirm or reject the photo-inferred PROM/register pairings, beginning with bit 0. |

For each connected pair, record `source pin → destination pin`, resistance in
ohms, whether the ICs were installed, and any uncertainty about pin numbering.
A photo showing the meter probes against visible package notches helps resolve
orientation, but a clear pin-numbered text table is sufficient. If an entire
priority group is open, stop that group and report it; the next probes should
then target the visible trace/via rather than assume the listed pairings.

The first positive AC connection can map an 8X02 command bit to a particular
PROM lane and register bit. The A0/A1 checks constrain address permutation;
clock checks constrain the microcycle schedule. None alone proves the ROM
read-enable, DAC strobe, USART link or modem algorithm. Those remain separate
requirements in [PLAN-2](../PLAN-2.md).
