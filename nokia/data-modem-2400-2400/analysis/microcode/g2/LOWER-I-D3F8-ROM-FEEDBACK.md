# The D3F8 table byte feeds Q and the next lookup

The [preceding trace](LOWER-I-D3F8-LOOKUP-CHAIN.md) established that the
candidate upper-slice mapping makes `3F8` select a real Am27S31 byte at
`3F9`. The [follow-up](lower_i_d3f8_rom_feedback.py) checks what `3F9`
does with that byte on every one of 512 visits while an ADC code `59` is
held at `3F8`.

The actual `3F9` lower instruction is `15`: it writes Q's low nibble as
`(ROM_low + (~pre-RAM[A_low]_low & 0xF) + carry_in) & 0xF`. Its upper
instruction is `ED`: it writes RAM[B_high]'s high nibble as
`(~ROM_high & pre-RAM[A_high]_high) & 0xF`. The trace checker reconstructs
the pre-instruction RAM and confirms both equations, both destination
values and every fetched byte against the dumped PROM. Replaying the exact
512 fetched bytes at `3F9` reproduces the real-ROM trace digest.

Changing only bit 0 of the fetched byte on `3F9` visit 20 changes Q in
that instruction, then changes modeled RAM, the `3F7` ROM address and the
next `3F8` result. The PC path remains the same; 491 of 512 later D3F8
state boundaries and 492 `3F7` ROM addresses differ. Changing only bit 4
at the same visit changes no state in this fixture, because the upper `ED`
operation masks it with the then-zero high nibble of RAM[A]. The
[saved result](results/lower-i-d3f8-rom-feedback.json) includes exact
cycles, values, counts, trace digests and source hashes.

This establishes a conditional **ADC → table index → ROM byte → Q/state →
next table index** feedback path in the running microprogram. It does not
establish that the physical board uses this instruction wiring or ADC bus,
and Q is not yet a decoded dibit or a traced USART RxD output. The next
test should discriminate a receive decision or constrain an output route
using the observed table/Q feedback, rather than treating Q variation alone
as modem decoding.
