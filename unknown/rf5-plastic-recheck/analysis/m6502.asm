000: ff d5 9e  isb $9ed5, x
003: b4 21     ldy $21, x
005: 01 fb     ora ($fb, x)
007: c5 bc     cmp $bc
009: a4 56     ldy $56
00b: c3 30     dcp ($30, x)
00d: fb f8 12  isb $12f8, y
010: e1 26     sbc ($26, x)
012: 62        kil
013: 6f fa e4  rra $e4fa
016: 26 3a     rol $3a
018: 8c 0c 26  sty $260c
01b: 3a        nop
01c: ff ae 5f  isb $5fae, x
01f: b8        clv
020: 2e 12 c8  rol $c812
023: 17 80     slo $80, x
025: 2e 80 3f  rol $3f80
028: 90 44     bcc $006e
02a: f2        kil
02b: fb 52 fa  isb $fa52, y
02e: 44 06     nop $06
030: 1f 06 ac  slo $ac06, x
033: 3c a8 01  nop $01a8, x
036: f4 8a     nop $8a, x
038: df 5f 3c  dcp $3c5f, x
03b: 07 9a     slo $9a
03d: f0 fb     beq $003a
03f: 47 3a     sre $3a
041: 77 01     rra $01, x
043: 48        pha
044: eb bb     sbc #$bb
046: 83 05     sax ($05, x)
048: 85 fe     sta $fe
04a: 06 5e     asl $5e
04c: 95 bc     sta $bc, x
04e: 52        kil
04f: b3 57     lax ($57), y
051: 46 aa     lsr $aa
053: 72        kil
054: fa        nop
055: 80 01     nop #$01
057: 95 2e     sta $2e, x
059: 2e 77 4d  rol $4d77
05c: fc 77 ec  nop $ec77, x
05f: fa        nop
060: 56 aa     lsr $aa, x
062: 71 72     adc ($72), y
064: 7f b3 ef  rra $efb3, x
067: fe bc 53  inc $53bc, x
06a: d6 c3     dec $c3, x
06c: 36 74     rol $74, x
06e: 04 74     nop $74
070: fe bf ef  inc $efbf, x
073: 1f a4 07  slo $07a4, x
076: 77 bc     rra $bc, x
078: 34 07     nop $07, x
07a: 93 26     sha ($26), y
07c: f4 a4     nop $a4, x
07e: 87 95     sax $95
080: a4 14     ldy $14
082: 46 aa     lsr $aa
084: 1c fa 08  nop $08fa, x
087: bc 2f 07  ldy $072f, x
08a: 8f 95 f4  sax $f495
08d: c3 01     dcp ($01, x)
08f: fa        nop
090: 46 aa     lsr $aa
092: 8f bc 10  sax $10bc
095: 26 a4     rol $a4
097: 30 f4     bmi $008d
099: 96 15     stx $15, y
09b: cd 3f c5  cmp $c53f
09e: c9 3f     cmp #$3f
0a0: 96 ae     stx $ae, y
0a2: ff 96 6e  isb $6e96, x
0a5: 96 a6     stx $a6, y
0a7: 26 0c     rol $0c
0a9: e4 0f     cpx $0f
0ab: 03 f1     slo ($f1, x)
0ad: 56 d6     lsr $d6, x
0af: 86 84     stx $84
0b1: 0f b8 f1  slo $f1b8
0b4: 56 86     lsr $86, x
0b6: 02        kil
0b7: e9 96     sbc #$96
0b9: 08        php
0ba: bf 05 26  lax $2605, y
0bd: 33 26     rla ($26), y
0bf: b8        clv
0c0: 01 bc     ora ($bc, x)
0c2: b4 bc     ldy $bc, x
0c4: a0 2f     ldy #$2f
0c6: 8f 1d 11  sax $111d
0c9: 06 b8     asl $b8
0cb: f1 b0     sbc ($b0), y
0cd: 06 01     asl $01
0cf: e9 96     sbc #$96
0d1: 4a        lsr a
0d2: 02        kil
0d3: e4 21     cpx $21
0d5: 26 f1     rol $f1
0d7: 96 26     stx $26, y
0d9: bc a4 b4  ldy $b4a4, x
0dc: f8        sed
0dd: 0c cc a7  nop $a7cc
0e0: bc a4 b4  ldy $b4a4, x
0e3: 42        kil
0e4: 17 cc     slo $cc, x
0e6: d4 96     nop $96, x
0e8: 27 b8     rla $b8
0ea: a0 e9     ldy #$e9
0ec: d7 3f     dcp $3f, x
0ee: e8        inx
0ef: 26 01     rol $01
0f1: af e4 d5  lax $d5e4
0f4: ab 26     lxa #$26
0f6: 62        kil
0f7: 55 25     eor $25, x
0f9: fb eb ef  isb $efeb, y
0fc: fb fb fc  isb $fcfb, y
0ff: fc fb 43  nop $43fb, x
102: 17 86     slo $86, x
104: 43 26     sre ($26, x)
106: d1 bf     cmp ($bf), y
108: 05 a1     ora $a1
10a: 0e 27 11  asl $1127
10d: b8        clv
10e: ad af ae  lda $aeaf
111: e9 b3     sbc #$b3
113: a4 f1     ldy $f1
115: b1 11     lda ($11), y
117: 91 dd     sta ($dd), y
119: a4 96     ldy $96
11b: a4 11     ldy $11
11d: d1 11     cmp ($11), y
11f: 71 6e     adc ($6e), y
121: a4 a1     ldy $a1
123: a4 11     ldy $11
125: 11 11     ora ($11), y
127: 51 a1     eor ($a1), y
129: a4 a7     ldy $a7
12b: a4 11     ldy $11
12d: 31 11     and ($11), y
12f: ef 16 cd  isb $cd16
132: a4 af     ldy $af
134: f1 11     sbc ($11), y
136: 2d fd f1  and $f1fd
139: 11 ef     ora ($ef), y
13b: c3 cd     dcp ($cd, x)
13d: a4 38     ldy $38
13f: 43 26     sre ($26, x)
141: d1 21     cmp ($21), y
143: f1 0f     sbc ($0f), y
145: 86 07     stx $07
147: c8        iny
148: 11 93     ora ($93), y
14a: 71 43     adc ($43), y
14c: d8        cld
14d: 51 be     eor ($be), y
14f: aa        tax
150: f1 21     sbc ($21), y
152: bf ff dc  lax $dcff, y
155: aa        tax
156: 3f a8 f1  rla $f1a8, x
159: ef bf ff  isb $ffbf
15c: e9 53     sbc #$53
15e: 3f d6 0a  rla $0ad6, x
161: 6f f1 df  rra $dff1
164: c3 ff     dcp ($ff, x)
166: e4 c3     cpx $c3
168: 6f 07 86  rra $8607
16b: 51 26     eor ($26), y
16d: d1 21     cmp ($21), y
16f: ff a8 f1  isb $f1a8, x
172: ef 26 27  isb $2726
175: e9 5b     sbc #$5b
177: 06 bc     asl $bc
179: 94 3f     sty $3f, x
17b: 03 1d     slo ($1d, x)
17d: 26 b8     rol $b8
17f: f1 e9     sbc ($e9), y
181: 02        kil
182: 3e e9 26  rol $26e9, x
185: b8        clv
186: f1 26     sbc ($26), y
188: 06 3b     asl $3b
18a: e9 ff     sbc #$ff
18c: b8        clv
18d: f1 26     sbc ($26), y
18f: b8        clv
190: 00        brk
191: e9 15     sbc #$15
193: 07 f1     slo $f1
195: b8        clv
196: ff f1 0a  isb $0af1, x
199: c8        iny
19a: 0a        asl a
19b: ee a0 f1  inc $f1a0
19e: 06 a0     asl $a0
1a0: f1 06     sbc ($06), y
1a2: ac 96 0a  ldy $0a96
1a5: eb cf     sbc #$cf
1a7: ff a6 42  isb $42a6, x
1aa: c3 8c     dcp ($8c, x)
1ac: 96 17     stx $17, y
1ae: aa        tax
1af: ff 8a 0c  isb $0c8a, x
1b2: b8        clv
1b3: f1 7f     sbc ($7f), y
1b5: 37 05     rla $05, x
1b7: e9 11     sbc #$11
1b9: ba        tsx
1ba: bc f4 bc  ldy $bcf4, x
1bd: 07 32     slo $32
1bf: be 0f c5  ldx $c50f, y
1c2: 1f 28 12  slo $1228, x
1c5: be bc b8  ldx $b8bc, y
1c8: 20 ed 84  jsr $84ed
1cb: 9a        txs
1cc: 21 bd     and ($bd, x)
1ce: 3a        nop
1cf: 83 99     sax ($99, x)
1d1: 8c 9b 23  sty $239b
1d4: b9 bb bc  lda $bcbb, y
1d7: fc 21 ff  nop $ff21, x
1da: c4 da     cpy $da
1dc: e5 fd     sbc $fd
1de: 7a        nop
1df: c3 d9     dcp ($d9, x)
1e1: cc db 94  cpy $94db
1e4: f9 fb 3f  sbc $3ffb, y
1e7: 01 e8     ora ($e8, x)
1e9: 3f fa 56  rla $56fa, x
1ec: ff e1 f4  isb $f4e1, x
1ef: e0 c3     cpx #$c3
1f1: e1 f4     sbc ($f4, x)
1f3: 06 f1     asl $f1
1f5: fa        nop
1f6: 5e ce a6  lsr $a6ce, x
1f9: a0 1c     ldy #$1c
1fb: ed 17 18  sbc $1817
1fe: ea        nop
1ff: 26 06     rol $06
201: e4 05     cpx $05
203: 0c f1 d6  nop $d6f1
206: 93 41     sha ($41), y
208: 25 d6     and $d6
20a: 17 02     slo $02, x
20c: 11 93     ora ($93), y
20e: bc f4 37  ldy $37f4, x
211: 17 52     slo $52, x
213: 15 b2     ora $b2, x
215: b1 c1     lda ($c1), y
217: f1 03     sbc ($03), y
219: 06 25     asl $25
21b: 02        kil
21c: d6 93     dec $93, x
21e: bc f4 d6  ldy $d6f4, x
221: a4 c8     ldy $c8
223: 02        kil
224: 20 f1 bc  jsr $bcf1
227: f4 37     nop $37, x
229: 30 f7     bmi $0222
22b: b1 72     lda ($72), y
22d: d6 a4     dec $a4, x
22f: 17 bc     slo $bc, x
231: f4 92     nop $92, x
233: d6 02     dec $02, x
235: 37 3e     rla $3e, x
237: ef a4 f5  isb $f5a4
23a: d6 32     dec $32, x
23c: 91 11     sta ($11), y
23e: ad 56 53  lda $5356
241: 93 17     sha ($17), y
243: b1 a7     lda ($a7), y
245: 56 11     lsr $11, x
247: 71 df     adc ($df), y
249: bc da 05  ldy $05da, x
24c: 11 71     ora ($71), y
24e: bc b4 04  ldy $04b4, x
251: d9 05 93  cmp $9305, y
254: 41 bc     eor ($bc, x)
256: f4 64     nop $64, x
258: 26 33     rol $33
25a: 26 a4     rol $a4
25c: 08        php
25d: 5b 05 71  sre $7105, y
260: 20 01 c3  jsr $c301
263: 53 bc     sre ($bc), y
265: f4 6a     nop $6a, x
267: ac 41 11  ldy $1141
26a: 26 11     rol $11
26c: e4 bc     cpx $bc
26e: 02        kil
26f: b1 26     lda ($26), y
271: f1 af     sbc ($af), y
273: 0f 05 e4  slo $e405
276: 56 c3     lsr $c3, x
278: 95 07     sta $07, x
27a: e4 ab     cpx $ab
27c: 26 f1     rol $f1
27e: 07 b8     slo $b8
280: 07 e9     slo $e9
282: 93 ff     sha ($ff), y
284: f1 fb     sbc ($fb), y
286: 95 56     sta $56, x
288: 0f 06 b8  slo $b806
28b: f1 47     sbc ($47), y
28d: fd 07 e9  sbc $e907, x
290: ff 97 8b  isb $8b97, x
293: 8b b2     ane #$b2
295: 71 71     adc ($71), y
297: bc 27 72  ldy $7227, x
29a: b4 41     ldy $41, x
29c: f4 a0     nop $a0, x
29e: 0f d2 b4  slo $b4d2
2a1: 41 ff     eor ($ff, x)
2a3: 96 b4     stx $b4, y
2a5: d2        kil
2a6: a6 c3     ldx $c3
2a8: c0 03     cpy #$03
2aa: 04 e4     nop $e4
2ac: f1 d6     sbc ($d6), y
2ae: 93 b4     sha ($b4), y
2b0: ff 11 fd  isb $fd11, x
2b3: bc 27 b1  ldy $b127, x
2b6: 32        kil
2b7: 91 bb     sta ($bb), y
2b9: 12        kil
2ba: 91 71     sta ($71), y
2bc: fd c0 61  sbc $61c0, x
2bf: be f1 d6  ldx $d6f1, y
2c2: 93 b4     sha ($b4), y
2c4: 03 04     slo ($04, x)
2c6: ca        dex
2c7: ff 91 26  isb $2691, x
2ca: f1 d6     sbc ($d6), y
2cc: e0 06     cpx #$06
2ce: e4 05     cpx $05
2d0: c3 f1     dcp ($f1, x)
2d2: d6 93     dec $93, x
2d4: e4 03     cpx $03
2d6: 02        kil
2d7: e4 b4     cpx $b4
2d9: 71 27     adc ($27), y
2db: 06 ff     asl $ff
2dd: b6 b8     ldx $b8, y
2df: f1 e9     sbc ($e9), y
2e1: 06 e4     asl $e4
2e3: 07 26     slo $26
2e5: f1 56     sbc ($56), y
2e7: 06 ea     asl $ea
2e9: f1 f8     sbc ($f8), y
2eb: f9 b6 f3  sbc $f3b6, y
2ee: fa        nop
2ef: fb f2 e1  isb $e1f2, y
2f2: 81 61     sta ($61, x)
2f4: f2        kil
2f5: fa        nop
2f6: 0f 00 61  slo $6100
2f9: c1 61     cmp ($61, x)
2fb: e1 4e     sbc ($4e, x)
2fd: 4c 6b 25  jmp $256b
300: 26 d1     rol $d1
302: aa        tax
303: 38        sec
304: 02        kil
305: df be bd  dcp $bdbe, x
308: 05 9d     ora $9d
30a: 38        sec
30b: 2b d1     anc #$d1
30d: b8        clv
30e: bc be 06  ldy $06be, x
311: 24 07     bit $07
313: 2b b9     anc #$b9
315: bd bb 85  lda $85bb, x
318: f1 bc     sbc ($bc), y
31a: b4 21     ldy $21, x
31c: 71 27     adc ($27), y
31e: 82 ba     nop #$ba
320: 26 d1     rol $d1
322: aa        tax
323: 39 06 df  and $df06, y
326: be bd 05  ldx $05bd, y
329: 9d 38 01  sta $0138, x
32c: d1 bc     cmp ($bc), y
32e: bf f4 06  lax $06f4, y
331: 57 e3     sre $e3, x
333: 1c 08 a4  nop $a408, x
336: 3b f4 16  rla $16f4, y
339: 57 ef     sre $ef, x
33b: fb 00 a4  isb $a400, y
33e: 31 ba     and ($ba), y
340: 39 bd d1  and $d1bd, y
343: 26 ae     rol $ae
345: 05 b5     ora $b5
347: 06 d1     asl $d1
349: 96 06     stx $06, y
34b: df fd 26  dcp $26fd, x
34e: d1 aa     cmp ($aa), y
350: be bd d1  ldx $d1bd, y
353: b8        clv
354: 39 05 9d  and $9d05, y
357: 39 bc be  and $bebc, y
35a: b9 bd 2b  lda $2bbd, y
35d: 02        kil
35e: 22        kil
35f: 07 bb     slo $bb
361: 85 8c     sta $8c
363: 27 2b     rla $2b
365: f1 bc     sbc ($bc), y
367: b4 3e     ldy $3e, x
369: ba        tsx
36a: a6 26     ldx $26
36c: 21 ff     and ($ff, x)
36e: 96 05     stx $05, y
370: d1 aa     cmp ($aa), y
372: 39 01 df  and $df01, y
375: be bd d1  ldx $d1bd, y
378: 9d 39 2b  sta $2b39, x
37b: 02        kil
37c: b8        clv
37d: bc be b9  ldy $b9be, x
380: 20 07 2b  jsr $2b07
383: f1 bd     sbc ($bd), y
385: bb 85 71  las $7185, y
388: bc b4 21  ldy $21b4, x
38b: 27 27     rla $27
38d: 87 ba     sax $ba
38f: 17 d1     slo $d1, x
391: aa        tax
392: 39 05 df  and $df05, y
395: be bd d1  ldx $d1bd, y
398: 9d 3d 38  sta $383d, x
39b: 06 b8     asl $b8
39d: bc bd 97  ldy $97bd, x
3a0: d1 d1     cmp ($d1), y
3a2: d1 fb     cmp ($fb), y
3a4: a9 93     lda #$93
3a6: 93 ba     sha ($ba), y
3a8: 39 bd d1  and $d1bd, y
3ab: 27 ae     rla $ae
3ad: 05 b5     ora $b5
3af: 17 d1     slo $d1, x
3b1: 96 f1     stx $f1, y
3b3: 07 fd     slo $fd
3b5: 27 e4     rla $e4
3b7: b8        clv
3b8: 00        brk
3b9: e9 3f     sbc #$3f
3bb: 3d f1 be  and $bef1, x
3be: b9 d1 c2  lda $c2d1, y
3c1: 06 3d     asl $3d
3c3: 3d b9 b8  and $b8b9, x
3c6: bc bd 06  ldy $06bd, x
3c9: d1 e9     cmp ($e9), y
3cb: bc 97 a9  ldy $a997, x
3ce: c6 27     dec $27
3d0: f4 b4     nop $b4, x
3d2: db d6 d6  dcp $d6d6, y
3d5: c3 f4     dcp ($f4, x)
3d7: 0f c3 bc  slo $bcc3
3da: b4 96     ldy $96, x
3dc: db 27 00  dcp $0027, y
3df: 26 05     rol $05
3e1: e4 db     cpx $db
3e3: 3e f1 d2  rol $d2f1, x
3e6: be b9 3c  ldx $3cb9, y
3e9: c2 38     nop #$38
3eb: a4 d1     ldy $d1
3ed: bc 27 1c  ldy $1c27, x
3f0: bf f4 a4  lax $a4f4, y
3f3: ef 06 47  isb $4706
3f6: 1c f2 27  nop $27f2, x
3f9: cc 3a 34  cpy $343a
3fc: a4 b8     ldy $b8
3fe: f0 c8     beq $03c8
400: cc 34 17  cpy $1734
403: df f0 27  dcp $27f0, x
406: d1 ba     cmp ($ba), y
408: 39 bd d1  and $d1bd, y
40b: 96 ae     stx $ae, y
40d: 05 b5     ora $b5
40f: be 3e 3c  ldx $3c3e, y
412: c2 3c     nop #$3c
414: b9 d1 bc  lda $bcd1, y
417: f4 85     nop $85, x
419: 19 b8 bc  ora $bcb8, y
41c: c3 95     dcp ($95, x)
41e: 3e 2b be  rol $be2b, x
421: bd b3 ce  lda $ceb3, x
424: 06 06     asl $06
426: 28        plp
427: ce b9 bb  dec $bbb9
42a: 85 8c     sta $8c
42c: 2c 2b f1  bit $f12b
42f: 27 17     rla $17
431: df be bd  dcp $bdbe, x
434: d1 aa     cmp ($aa), y
436: 39 05 d1  and $d105, y
439: b8        clv
43a: bc be 9d  ldy $9dbe, x
43d: 39 2e 06  and $062e, y
440: b9 bd bb  lda $bbbd, y
443: 85 21     sta $21
445: 01 2e     ora ($2e, x)
447: f1 8c     sbc ($8c), y
449: 28        plp
44a: 01 56     ora ($56, x)
44c: bc bf f4  ldy $f4bf, x
44f: 0f c3 d6  slo $d6c3
452: 93 1c     sha ($1c), y
454: 53 0f     sre ($0f), y
456: 62        kil
457: ef 4d 28  isb $284d
45a: 01 0f     ora ($0f, x)
45c: bc bf b4  ldy $b4bf, x
45f: 1c ef 21  nop $21ef, x
462: 27 d1     rla $d1
464: 5d ba 17  eor $17ba, x
467: df aa 39  dcp $39aa, x
46a: 01 9d     ora ($9d, x)
46c: be bd d1  ldx $d1bd, y
46f: bc 3c 56  ldy $563c, x
472: a4 02     ldy $02
474: f4 f0     nop $f0, x
476: 26 d1     rol $d1
478: df be bd  dcp $bdbe, x
47b: d1 aa     cmp ($aa), y
47d: 38        sec
47e: 05 9d     ora $9d
480: b8        clv
481: bc bd 97  ldy $97bd, x
484: 3c 31 01  nop $0131, x
487: d1 a9     cmp ($a9), y
489: 93 ba     sha ($ba), y
48b: ae d1 fb  ldx $fbd1
48e: 38        sec
48f: bd 05 b5  lda $b505, x
492: 02        kil
493: fd d1 26  sbc $26d1, x
496: d1 26     cmp ($26), y
498: 05 df     ora $df
49a: be bd d1  ldx $d1bd, y
49d: aa        tax
49e: 39 01 d1  and $d101, y
4a1: bc bf 97  ldy $97bf, x
4a4: 9d 38 01  sta $0138, x
4a7: a7 1c     lax $1c
4a9: 16 57     asl $57, x
4ab: e3 f4     isb ($f4, x)
4ad: 00        brk
4ae: a4 b2     ldy $b2
4b0: ef fb 39  isb $39fb
4b3: bd a8 ba  lda $baa8, x
4b6: ae 01 d1  ldx $d101
4b9: 26 d1     rol $d1
4bb: be b5 05  ldx $05b5, y
4be: fd 3c b9  sbc $b93c, x
4c1: fe 27 e9  inc $e927, x
4c4: 0a        asl a
4c5: a8        tay
4c6: f1 ce     sbc ($ce), y
4c8: e9 71     sbc #$71
4ca: 26 f1     rol $f1
4cc: c2 da     nop #$da
4ce: 0e e4 07  asl $07e4
4d1: d8        cld
4d2: f1 ec     sbc ($ec), y
4d4: 93 ac     sha ($ac), y
4d6: f1 d1     sbc ($d1), y
4d8: b8        clv
4d9: f1 96     sbc ($96), y
4db: a6 0e     ldx $0e
4dd: e9 ff     sbc #$ff
4df: 96 26     stx $26, y
4e1: f1 17     sbc ($17), y
4e3: d6 06     dec $06, x
4e5: e4 af     cpx $af
4e7: 03 93     slo ($93, x)
4e9: 71 27     adc ($27), y
4eb: f0 ef     beq $04dc
4ed: da        nop
4ee: 81 ff     sta ($ff, x)
4f0: b8        clv
4f1: f1 96     sbc ($96), y
4f3: f1 06     sbc ($06), y
4f5: e9 53     sbc #$53
4f7: 11 d6     ora ($d6), y
4f9: f1 01     sbc ($01), y
4fb: e4 c3     cpx $c3
4fd: 26 f1     rol $f1
4ff: 07 c3     slo $c3
501: b8        clv
502: f1 96     sbc ($96), y
504: 07 01     slo $01
506: e9 f1     sbc #$f1
508: c8        iny
509: 27 b4     rla $b4
50b: 72        kil
50c: bc f4 10  ldy $10f4, x
50f: 12        kil
510: b4 11     ldy $11, x
512: 71 96     adc ($96), y
514: 08        php
515: bc 8b 11  ldy $118b, x
518: d6 23     dec $23, x
51a: 03 e4     slo ($e4, x)
51c: c3 26     dcp ($26, x)
51e: f1 07     sbc ($07), y
520: c3 b8     dcp ($b8, x)
522: f1 96     sbc ($96), y
524: 27 03     rla $03
526: e9 26     sbc #$26
528: 01 df     ora ($df, x)
52a: be bd d1  ldx $d1bd, y
52d: aa        tax
52e: 39 01 d1  and $d101, y
531: bc bf 97  ldy $97bf, x
534: 9d 38 01  sta $0138, x
537: a7 1c     lax $1c
539: 16 57     asl $57, x
53b: e3 f4     isb ($f4, x)
53d: 00        brk
53e: a4 42     ldy $42
540: ef fb 39  isb $39fb
543: bd 38 ba  lda $ba38, x
546: ae 01 d1  ldx $d101
549: 26 d1     rol $d1
54b: 26 b5     rol $b5
54d: 01 fd     ora ($fd, x)
54f: 48        pha
550: a1 bc     lda ($bc, x)
552: f4 82     nop $82, x
554: 22        kil
555: 02        kil
556: d2        kil
557: d6 40     dec $40, x
559: 27 e4     rla $e4
55b: 39 a4 f1  and $f1a4, y
55e: ba        tsx
55f: 12        kil
560: 66 3f     ror $3f
562: 39 06 ba  and $ba06, y
565: be bd d1  ldx $d1bd, y
568: 9d 39 56  sta $5639, x
56b: a4 bc     ldy $bc
56d: f4 0f     nop $0f, x
56f: b8        clv
570: 39 3c 06  and $063c, y
573: a4 bc     ldy $bc
575: bf f0 c8  lax $c8f0, y
578: cc 75 31  cpy $3175
57b: 3a        nop
57c: ef bc b4  isb $b4bc
57f: 1c b4 bc  nop $bcb4, x
582: f4 95     nop $95, x
584: 05 32     ora $32
586: 12        kil
587: b1 8e     lda ($8e), y
589: ce 31 ac  dec $ac31
58c: a1 bc     lda ($bc, x)
58e: f4 06     nop $06, x
590: fd f0 96  sbc $96f0, x
593: 03 a8     slo ($a8, x)
595: a4 f1     ldy $f1
597: d6 04     dec $04, x
599: 93 95     sha ($95), y
59b: c8        iny
59c: 85 9f     sta $9f
59e: f1 95     sbc ($95), y
5a0: bc f4 b3  ldy $b3f4, x
5a3: 07 35     slo $35
5a5: af bc 93  lax $93bc
5a8: ae f5 37  ldx $37f5
5ab: ce a1 a4  dec $a4a1
5ae: 12        kil
5af: b1 8e     lda ($8e), y
5b1: 31 a1     and ($a1), y
5b3: ff bc 14  isb $14bc, x
5b6: ce a6 96  dec $96a6
5b9: 31 a8     and ($a8), y
5bb: f4 bc     nop $bc, x
5bd: f4 ac     nop $ac, x
5bf: 2f 12 2f  rla $2f12
5c2: f0 ca     beq $058e
5c4: c7 46     dcp $46
5c6: a1 2f     lda ($2f, x)
5c8: 46 a0     lsr $a0
5ca: 03 06     slo ($06, x)
5cc: 0f f1 d6  slo $d6f1
5cf: 93 b8     sha ($b8), y
5d1: c8        iny
5d2: b4 cc     ldy $cc, x
5d4: f1 cc     sbc ($cc), y
5d6: fb b4 ff  isb $ffb4, y
5d9: 31 06     and ($06), y
5db: a8        tay
5dc: bc f4 fd  ldy $fdf4, x
5df: ac f4 bc  ldy $bcf4
5e2: f4 ed     nop $ed, x
5e4: af 35 12  lax $1235
5e7: ff 06 57  isb $5706, x
5ea: 96 47     stx $47, y
5ec: 0a        asl a
5ed: a0 ff     ldy #$ff
5ef: 06 0a     asl $0a
5f1: 47 96     sre $96
5f3: 02        kil
5f4: 57 a0     sre $a0, x
5f6: bc f4 56  ldy $56f4, x
5f9: a4 f1     ldy $f1
5fb: 46 9f     lsr $9f
5fd: 27 e4     rla $e4
5ff: 02        kil
600: ad 00 e9  lda $e900
603: 39 b8 f1  and $f1b8, y
606: be fd 12  ldx $12fd, y
609: be ba bd  ldx $bdba, y
60c: 09 3f     ora #$3f
60e: 3c 06 d1  nop $d106, x
611: 71 96     adc ($96), y
613: 39 b5 be  and $beb5, y
616: b8        clv
617: bc 2b 04  ldy $042b, x
61a: 27 06     rla $06
61c: be b9 bd  ldx $bdb9, y
61f: bb 2e f1  las $f12e, y
622: b8        clv
623: bc 85 8c  ldy $8c85, x
626: 3a        nop
627: 2c be b9  bit $b9be
62a: bd bb 04  lda $04bb, x
62d: 28        plp
62e: 02        kil
62f: 2a        rol a
630: 85 71     sta $71
632: 2e 0f f1  rol $f10f
635: bc b4 cc  ldy $ccb4, x
638: b4 bc     ldy $bc, x
63a: b8        clv
63b: f0 1f     beq $065c
63d: 27 32     rla $32
63f: bf 00 45  lax $4500, y
642: 2f a4 12  rla $12a4
645: bf ff 21  lax $21ff, y
648: ba        tsx
649: 01 df     ora ($df, x)
64b: be 26 d1  ldx $d126, y
64e: aa        tax
64f: 39 bd d1  and $d1bd, y
652: b8        clv
653: bc 01 9d  ldy $9d01, x
656: 39 2b be  and $be2b, y
659: b9 bd bb  lda $bbbd, y
65c: 04 26     nop $26
65e: 07 2b     slo $2b
660: 85 8c     sta $8c
662: 27 9e     rla $9e
664: f1 bc     sbc ($bc), y
666: b4 21     ldy $21, x
668: ba        tsx
669: 84 3a     sty $3a
66b: ff 83 84  isb $8483, x
66e: ff ff 39  isb $39ff, x
671: 84 3a     sty $3a
673: ff b9 8c  isb $8cb9, x
676: ff ff 39  isb $39ff, x
679: 29 9c     and #$9c
67b: 39 9c b5  and $b59c, y
67e: ff ab ff  isb $ffab, x
681: fa        nop
682: 6c bc e1  jmp ($e1bc)
685: 06 a8     asl $a8
687: 27 bf     rla $bf
689: f8        sed
68a: 17 c8     slo $c8, x
68c: 08        php
68d: a6 a4     ldx $a4
68f: cc ef 96  cpy $96ef
692: a6 f4     ldx $f4
694: 8a        txa
695: ff 96 16  isb $1696, x
698: 00        brk
699: a4 86     ldy $86
69b: f1 57     sbc ($57), y
69d: 1c fa e4  nop $e4fa, x
6a0: 06 57     asl $57
6a2: ac a4 00  ldy $00a4
6a5: 2e 2e ca  rol $ca2e
6a8: ce 9d f4  dec $f49d
6ab: 57 ed     sre $ed, x
6ad: 96 70     stx $70, y
6af: a4 18     ldy $18
6b1: ed 86 ac  sbc $ac86
6b4: 1c a9 fa  nop $faa9, x
6b7: f4 2e     nop $2e, x
6b9: 2e e9 ce  rol $cee9
6bc: a8        tay
6bd: f1 ca     sbc ($ca), y
6bf: ed b5 27  sbc $27b5
6c2: e4 32     cpx $32
6c4: 96 f1     stx $f1, y
6c6: 85 cc     sta $cc
6c8: 95 39     sta $39, x
6ca: cf 3f ba  dcp $ba3f
6cd: 12        kil
6ce: ba        tsx
6cf: bd 06 9d  lda $9d06, x
6d2: d3 f9     dcp ($f9), y
6d4: d1 b3     cmp ($b3), y
6d6: 96 a8     stx $a8, y
6d8: ac 06 d1  ldy $d106
6db: 96 bd     stx $bd, y
6dd: 97 a9     sax $a9, y
6df: ab e7     lxa #$e7
6e1: d1 59     cmp ($59), y
6e3: ec ad f2  cpx $f2ad
6e6: c3 27     dcp ($27, x)
6e8: 17 d6     slo $d6, x
6ea: f1 2b     sbc ($2b), y
6ec: ab 04     lxa #$04
6ee: 20 f1 20  jsr $20f1
6f1: 27 f1     rla $f1
6f3: a9 96     lda #$96
6f5: 17 e4     slo $e4, x
6f7: 26 80     rol $80
6f9: eb 96     sbc #$96
6fb: d1 e7     cmp ($e7), y
6fd: fc ab f2  nop $f2ab, x
700: d9 04 e9  cmp $e904, y
703: bc b8 f1  ldy $f1b8, x
706: 96 36     stx $36, y
708: f4 6f     nop $6f, x
70a: f1 12     sbc ($12), y
70c: 96 af     stx $af, y
70e: dc 0a 52  nop $520a, x
711: ff 3c 2f  isb $2f3c, x
714: 0a        asl a
715: 96 31     stx $31, y
717: 2a        rol a
718: 25 1e     and $1e
71a: 16 e1     asl $e1, x
71c: 20 17 0f  jsr $0f17
71f: fa        nop
720: 6d 12 96  adc $9612
723: 05 06     ora $06
725: a6 26     ldx $26
727: f1 e4     sbc ($e4), y
729: 00        brk
72a: b8        clv
72b: b0 06     bcs $0733
72d: 57 39     sre $39, x
72f: 00        brk
730: c8        iny
731: c8        iny
732: 31 bc     and ($bc), y
734: a0 b0     ldy #$b0
736: c8        iny
737: 1d 11 06  ora $0611, x
73a: 57 42     sre $42, x
73c: b0 06     bcs $0744
73e: 33 06     rla ($06), y
740: 50 a0     bvc $06e2
742: 39 2b 57  and $572b, y
745: b8        clv
746: bc be 04  ldy $04be, x
749: 27 07     rla $07
74b: 2b b9     anc #$b9
74d: bd bb 85  lda $85bb, x
750: f1 bc     sbc ($bc), y
752: b4 f1     ldy $f1, x
754: 8c 27 af  sty $af27
757: 03 d6     slo ($d6, x)
759: 93 bc     sha ($bc), y
75b: 11 06     ora ($06), y
75d: 61 1d     adc ($1d, x)
75f: b0 17     bcs $0778
761: f1 f1     sbc ($f1), y
763: d6 94     dec $94, x
765: c8        iny
766: 03 02     slo ($02, x)
768: 93 b8     sha ($b8), y
76a: 80 3f     nop #$3f
76c: 72        kil
76d: 2e 17 90  rol $9017
770: f1 21     sbc ($21), y
772: 19 56 c8  ora $c856, y
775: ba        tsx
776: f0 f0     beq $0768
778: b3 ee     lax ($ee), y
77a: 95 82     sta $82, x
77c: 82 7f     nop #$7f
77e: e1 c3     sbc ($c3, x)
780: 8c 47 ed  sty $ed47
783: e1 95     sbc ($95, x)
785: a4 88     ldy $88
787: a0 cc     ldy #$cc
789: f0 0f     beq $079a
78b: 97 19     sax $19, y
78d: 56 b3     lsr $b3, x
78f: ee 91 e1  inc $e191
792: c3 95     dcp ($95, x)
794: 95 97     sta $97, x
796: 9d a4 ed  sta $eda4, x
799: e1 cc     sbc ($cc, x)
79b: e1 99     sbc ($99, x)
79d: a0 c8     ldy #$c8
79f: 71 fb     adc ($fb), y
7a1: f4 a9     nop $a9, x
7a3: 0f ac 93  slo $93ac
7a6: b4 fb     ldy $fb, x
7a8: cb 93     sbx #$93
7aa: 27 f9     rla $f9
7ac: d9 a0 af  cmp $afa0, y
7af: d6 28     dec $28, x
7b1: b1 f9     lda ($f9), y
7b3: 29 93     and #$93
7b5: 1f d6 93  slo $93d6, x
7b8: ba        tsx
7b9: ff c6 ac  isb $acc6, x
7bc: 1f 93 f9  slo $f993, x
7bf: f4 06     nop $06, x
7c1: a4 a7     ldy $a7
7c3: fa        nop
7c4: 10 11     bpl $07d7
7c6: 93 96     sha ($96), y
7c8: bc b4 96  ldy $96b4, x
7cb: a6 36     ldx $36
7cd: ff ff 96  isb $96ff, x
7d0: f2        kil
7d1: d2        kil
7d2: e7 e7     isb $e7
7d4: fa        nop
7d5: fa        nop
7d6: 17 ac     slo $ac, x
7d8: 86 03     stx $03
7da: c3 f1     dcp ($f1, x)
7dc: f1 17     sbc ($17), y
7de: dc c8 96  nop $96c8, x
7e1: d0 b0     bne $0793
7e3: 1c f1 11  nop $11f1, x
7e6: a8        tay
7e7: 11 b0     ora ($b0), y
7e9: 68        pla
7ea: 28        plp
7eb: d0 47     bne $0834
7ed: 86 f1     stx $f1
7ef: f8        sed
7f0: 3f 1c 3f  rla $3f1c, x
7f3: 86 94     stx $94
7f5: 47 94     sre $94
7f7: 71 9d     adc ($9d), y
7f9: 26 3a     rol $3a
7fb: e8        inx
7fc: 94 4f     sty $4f, x
7fe: 01 ff     ora ($ff, x)
