000: ff        mov   r7,a
001: d5 9e b4  djnz  $9E,$FFFFFFB8
004: 21 01     ajmp  $0101
006: fb        mov   r3,a
007: c5 bc     xch   a,$BC
009: a4        mul   ab
00a: 56        anl   a,@r0
00b: c3        clr   c
00c: 30 fb f8  jnb   $F8.3,$0007
00f: 12 e1 26  lcall $E126
012: 62 6f     xrl   $6F,a
014: fa        mov   r2,a
015: e4        clr   a
016: 26        add   a,@r0
017: 3a        addc  a,r2
018: 8c 0c     mov   rb1r4,r4
01a: 26        add   a,@r0
01b: 3a        addc  a,r2
01c: ff        mov   r7,a
01d: ae 5f     mov   r6,$5F
01f: b8 2e 12  cjne  r0,#$2E,$0034
022: c8        xch   a,r0
023: 17        dec   @r1
024: 80 2e     sjmp  $0054
026: 80 3f     sjmp  $0067
028: 90 44 f2  mov   dptr,#$44F2
02b: fb        mov   r3,a
02c: 52 fa     anl   $FA,a
02e: 44 06     orl   a,#$06
030: 1f        dec   r7
031: 06        inc   @r0
032: ac 3c     mov   r4,$3C
034: a8 01     mov   r0,rb0r1
036: f4        cpl   a
037: 8a df     mov   $DF,r2
039: 5f        anl   a,r7
03a: 3c        addc  a,r4
03b: 07        inc   @r1
03c: 9a        subb  a,r2
03d: f0        movx  @dptr,a
03e: fb        mov   r3,a
03f: 47        orl   a,@r1
040: 3a        addc  a,r2
041: 77 01     mov   @r1,#$01
043: 48        orl   a,r0
044: eb        mov   a,r3
045: bb 83 05  cjne  r3,#$83,$004D
048: 85 fe 06  mov   rb0r6,$FE
04b: 5e        anl   a,r6
04c: 95 bc     subb  a,$BC
04e: 52 b3     anl   $B3,a
050: 57        anl   a,@r1
051: 46        orl   a,@r0
052: aa 72     mov   r2,$72
054: fa        mov   r2,a
055: 80 01     sjmp  $0058
057: 95 2e     subb  a,$2E
059: 2e        add   a,r6
05a: 77 4d     mov   @r1,#$4D
05c: fc        mov   r4,a
05d: 77 ec     mov   @r1,#$EC
05f: fa        mov   r2,a
060: 56        anl   a,@r0
061: aa 71     mov   r2,$71
063: 72 7f     orl   c,$2F.7
065: b3        cpl   c
066: ef        mov   a,r7
067: fe        mov   r6,a
068: bc 53 d6  cjne  r4,#$53,$0041
06b: c3        clr   c
06c: 36        addc  a,@r0
06d: 74 04     mov   a,#$04
06f: 74 fe     mov   a,#$FE
071: bf ef 1f  cjne  r7,#$EF,$0093
074: a4        mul   ab
075: 07        inc   @r1
076: 77 bc     mov   @r1,#$BC
078: 34 07     addc  a,#$07
07a: 93        movc  a,@a+dptr
07b: 26        add   a,@r0
07c: f4        cpl   a
07d: a4        mul   ab
07e: 87 95     mov   $95,@r1
080: a4        mul   ab
081: 14        dec   a
082: 46        orl   a,@r0
083: aa 1c     mov   r2,rb3r4
085: fa        mov   r2,a
086: 08        inc   r0
087: bc 2f 07  cjne  r4,#$2F,$0091
08a: 8f 95     mov   $95,r7
08c: f4        cpl   a
08d: c3        clr   c
08e: 01 fa     ajmp  $00FA
090: 46        orl   a,@r0
091: aa 8f     mov   r2,$8F
093: bc 10 26  cjne  r4,#$10,$00BC
096: a4        mul   ab
097: 30 f4 96  jnb   b.4,$0030
09a: 15 cd     dec   $CD
09c: 3f        addc  a,r7
09d: c5 c9     xch   a,$C9
09f: 3f        addc  a,r7
0a0: 96        subb  a,@r0
0a1: ae ff     mov   r6,$FF
0a3: 96        subb  a,@r0
0a4: 6e        xrl   a,r6
0a5: 96        subb  a,@r0
0a6: a6 26     mov   @r0,$26
0a8: 0c        inc   r4
0a9: e4        clr   a
0aa: 0f        inc   r7
0ab: 03        rr    a
0ac: f1 56     acall $0756
0ae: d6        xchd  a,@r0
0af: 86 84     mov   $84,@r0
0b1: 0f        inc   r7
0b2: b8 f1 56  cjne  r0,#$F1,$010B
0b5: 86 02     mov   rb0r2,@r0
0b7: e9        mov   a,r1
0b8: 96        subb  a,@r0
0b9: 08        inc   r0
0ba: bf 05 26  cjne  r7,#$05,$00E3
0bd: 33        rlc   a
0be: 26        add   a,@r0
0bf: b8 01 bc  cjne  r0,#$01,$007E
0c2: b4 bc a0  cjne  a,#$BC,$0065
0c5: 2f        add   a,r7
0c6: 8f 1d     mov   rb3r5,r7
0c8: 11 06     acall $0006
0ca: b8 f1 b0  cjne  r0,#$F1,$007D
0cd: 06        inc   @r0
0ce: 01 e9     ajmp  $00E9
0d0: 96        subb  a,@r0
0d1: 4a        orl   a,r2
0d2: 02 e4 21  ljmp  $E421
0d5: 26        add   a,@r0
0d6: f1 96     acall $0796
0d8: 26        add   a,@r0
0d9: bc a4 b4  cjne  r4,#$A4,$0090
0dc: f8        mov   r0,a
0dd: 0c        inc   r4
0de: cc        xch   a,r4
0df: a7 bc     mov   @r1,$BC
0e1: a4        mul   ab
0e2: b4 42 17  cjne  a,#$42,$00FC
0e5: cc        xch   a,r4
0e6: d4        da    a
0e7: 96        subb  a,@r0
0e8: 27        add   a,@r1
0e9: b8 a0 e9  cjne  r0,#$A0,$00D5
0ec: d7        xchd  a,@r1
0ed: 3f        addc  a,r7
0ee: e8        mov   a,r0
0ef: 26        add   a,@r0
0f0: 01 af     ajmp  $00AF
0f2: e4        clr   a
0f3: d5 ab 26  djnz  $AB,$011C
0f6: 62 55     xrl   $55,a
0f8: 25 fb     add   a,$FB
0fa: eb        mov   a,r3
0fb: ef        mov   a,r7
0fc: fb        mov   r3,a
0fd: fb        mov   r3,a
0fe: fc        mov   r4,a
0ff: fc        mov   r4,a
100: fb        mov   r3,a
101: 43 17 86  orl   rb2r7,#$86
104: 43 26 d1  orl   $26,#$D1
107: bf 05 a1  cjne  r7,#$05,$00AB
10a: 0e        inc   r6
10b: 27        add   a,@r1
10c: 11 b8     acall $00B8
10e: ad af     mov   r5,$AF
110: ae e9     mov   r6,$E9
112: b3        cpl   c
113: a4        mul   ab
114: f1 b1     acall $07B1
116: 11 91     acall $0091
118: dd a4     djnz  r5,$00BE
11a: 96        subb  a,@r0
11b: a4        mul   ab
11c: 11 d1     acall $00D1
11e: 11 71     acall $0071
120: 6e        xrl   a,r6
121: a4        mul   ab
122: a1 a4     ajmp  $05A4
124: 11 11     acall $0011
126: 11 51     acall $0051
128: a1 a4     ajmp  $05A4
12a: a7 a4     mov   @r1,$A4
12c: 11 31     acall $0031
12e: 11 ef     acall $00EF
130: 16        dec   @r0
131: cd        xch   a,r5
132: a4        mul   ab
133: af f1     mov   r7,$F1
135: 11 2d     acall $002D
137: fd        mov   r5,a
138: f1 11     acall $0711
13a: ef        mov   a,r7
13b: c3        clr   c
13c: cd        xch   a,r5
13d: a4        mul   ab
13e: 38        addc  a,r0
13f: 43 26 d1  orl   $26,#$D1
142: 21 f1     ajmp  $01F1
144: 0f        inc   r7
145: 86 07     mov   rb0r7,@r0
147: c8        xch   a,r0
148: 11 93     acall $0093
14a: 71 43     acall $0343
14c: d8 51     djnz  r0,$019F
14e: be aa f1  cjne  r6,#$AA,$0142
151: 21 bf     ajmp  $01BF
153: ff        mov   r7,a
154: dc aa     djnz  r4,$0100
156: 3f        addc  a,r7
157: a8 f1     mov   r0,$F1
159: ef        mov   a,r7
15a: bf ff e9  cjne  r7,#$FF,$0146
15d: 53 3f d6  anl   $3F,#$D6
160: 0a        inc   r2
161: 6f        xrl   a,r7
162: f1 df     acall $07DF
164: c3        clr   c
165: ff        mov   r7,a
166: e4        clr   a
167: c3        clr   c
168: 6f        xrl   a,r7
169: 07        inc   @r1
16a: 86 51     mov   $51,@r0
16c: 26        add   a,@r0
16d: d1 21     acall $0621
16f: ff        mov   r7,a
170: a8 f1     mov   r0,$F1
172: ef        mov   a,r7
173: 26        add   a,@r0
174: 27        add   a,@r1
175: e9        mov   a,r1
176: 5b        anl   a,r3
177: 06        inc   @r0
178: bc 94 3f  cjne  r4,#$94,$01BA
17b: 03        rr    a
17c: 1d        dec   r5
17d: 26        add   a,@r0
17e: b8 f1 e9  cjne  r0,#$F1,$016A
181: 02 3e e9  ljmp  $3EE9
184: 26        add   a,@r0
185: b8 f1 26  cjne  r0,#$F1,$01AE
188: 06        inc   @r0
189: 3b        addc  a,r3
18a: e9        mov   a,r1
18b: ff        mov   r7,a
18c: b8 f1 26  cjne  r0,#$F1,$01B5
18f: b8 00 e9  cjne  r0,#$00,$017B
192: 15 07     dec   rb0r7
194: f1 b8     acall $07B8
196: ff        mov   r7,a
197: f1 0a     acall $070A
199: c8        xch   a,r0
19a: 0a        inc   r2
19b: ee        mov   a,r6
19c: a0 f1     orl   c,/b.1
19e: 06        inc   @r0
19f: a0 f1     orl   c,/b.1
1a1: 06        inc   @r0
1a2: ac 96     mov   r4,$96
1a4: 0a        inc   r2
1a5: eb        mov   a,r3
1a6: cf        xch   a,r7
1a7: ff        mov   r7,a
1a8: a6 42     mov   @r0,$42
1aa: c3        clr   c
1ab: 8c 96     mov   $96,r4
1ad: 17        dec   @r1
1ae: aa ff     mov   r2,$FF
1b0: 8a 0c     mov   rb1r4,r2
1b2: b8 f1 7f  cjne  r0,#$F1,$0234
1b5: 37        addc  a,@r1
1b6: 05 e9     inc   $E9
1b8: 11 ba     acall $00BA
1ba: bc f4 bc  cjne  r4,#$F4,$0179
1bd: 07        inc   @r1
1be: 32        reti
1bf: be 0f c5  cjne  r6,#$0F,$0187
1c2: 1f        dec   r7
1c3: 28        add   a,r0
1c4: 12 be bc  lcall $BEBC
1c7: b8 20 ed  cjne  r0,#$20,$01B7
1ca: 84        div   ab
1cb: 9a        subb  a,r2
1cc: 21 bd     ajmp  $01BD
1ce: 3a        addc  a,r2
1cf: 83        movc  a,@a+pc
1d0: 99        subb  a,r1
1d1: 8c 9b     mov   $9B,r4
1d3: 23        rl    a
1d4: b9 bb bc  cjne  r1,#$BB,$0193
1d7: fc        mov   r4,a
1d8: 21 ff     ajmp  $01FF
1da: c4        swap  a
1db: da e5     djnz  r2,$01C2
1dd: fd        mov   r5,a
1de: 7a c3     mov   r2,#$C3
1e0: d9 cc     djnz  r1,$01AE
1e2: db 94     djnz  r3,$0178
1e4: f9        mov   r1,a
1e5: fb        mov   r3,a
1e6: 3f        addc  a,r7
1e7: 01 e8     ajmp  $00E8
1e9: 3f        addc  a,r7
1ea: fa        mov   r2,a
1eb: 56        anl   a,@r0
1ec: ff        mov   r7,a
1ed: e1 f4     ajmp  $07F4
1ef: e0        movx  a,@dptr
1f0: c3        clr   c
1f1: e1 f4     ajmp  $07F4
1f3: 06        inc   @r0
1f4: f1 fa     acall $07FA
1f6: 5e        anl   a,r6
1f7: ce        xch   a,r6
1f8: a6 a0     mov   @r0,p2
1fa: 1c        dec   r4
1fb: ed        mov   a,r5
1fc: 17        dec   @r1
1fd: 18        dec   r0
1fe: ea        mov   a,r2
1ff: 26        add   a,@r0
200: 06        inc   @r0
201: e4        clr   a
202: 05 0c     inc   rb1r4
204: f1 d6     acall $07D6
206: 93        movc  a,@a+dptr
207: 41 25     ajmp  $0225
209: d6        xchd  a,@r0
20a: 17        dec   @r1
20b: 02 11 93  ljmp  $1193
20e: bc f4 37  cjne  r4,#$F4,$0248
211: 17        dec   @r1
212: 52 15     anl   rb2r5,a
214: b2 b1     cpl   txd
216: c1 f1     ajmp  $06F1
218: 03        rr    a
219: 06        inc   @r0
21a: 25 02     add   a,rb0r2
21c: d6        xchd  a,@r0
21d: 93        movc  a,@a+dptr
21e: bc f4 d6  cjne  r4,#$F4,$01F7
221: a4        mul   ab
222: c8        xch   a,r0
223: 02 20 f1  ljmp  $20F1
226: bc f4 37  cjne  r4,#$F4,$0260
229: 30 f7 b1  jnb   b.7,$01DD
22c: 72 d6     orl   c,ac
22e: a4        mul   ab
22f: 17        dec   @r1
230: bc f4 92  cjne  r4,#$F4,$01C5
233: d6        xchd  a,@r0
234: 02 37 3e  ljmp  $373E
237: ef        mov   a,r7
238: a4        mul   ab
239: f5 d6     mov   $D6,a
23b: 32        reti
23c: 91 11     acall $0411
23e: ad 56     mov   r5,$56
240: 53 93 17  anl   $93,#$17
243: b1 a7     acall $05A7
245: 56        anl   a,@r0
246: 11 71     acall $0071
248: df bc     djnz  r7,$0206
24a: da 05     djnz  r2,$0251
24c: 11 71     acall $0071
24e: bc b4 04  cjne  r4,#$B4,$0255
251: d9 05     djnz  r1,$0258
253: 93        movc  a,@a+dptr
254: 41 bc     ajmp  $02BC
256: f4        cpl   a
257: 64 26     xrl   a,#$26
259: 33        rlc   a
25a: 26        add   a,@r0
25b: a4        mul   ab
25c: 08        inc   r0
25d: 5b        anl   a,r3
25e: 05 71     inc   $71
260: 20 01 c3  jb    $20.1,$0226
263: 53 bc f4  anl   $BC,#$F4
266: 6a        xrl   a,r2
267: ac 41     mov   r4,$41
269: 11 26     acall $0026
26b: 11 e4     acall $00E4
26d: bc 02 b1  cjne  r4,#$02,$0221
270: 26        add   a,@r0
271: f1 af     acall $07AF
273: 0f        inc   r7
274: 05 e4     inc   $E4
276: 56        anl   a,@r0
277: c3        clr   c
278: 95 07     subb  a,rb0r7
27a: e4        clr   a
27b: ab 26     mov   r3,$26
27d: f1 07     acall $0707
27f: b8 07 e9  cjne  r0,#$07,$026B
282: 93        movc  a,@a+dptr
283: ff        mov   r7,a
284: f1 fb     acall $07FB
286: 95 56     subb  a,$56
288: 0f        inc   r7
289: 06        inc   @r0
28a: b8 f1 47  cjne  r0,#$F1,$02D4
28d: fd        mov   r5,a
28e: 07        inc   @r1
28f: e9        mov   a,r1
290: ff        mov   r7,a
291: 97        subb  a,@r1
292: 8b 8b     mov   tl1,r3
294: b2 71     cpl   $2E.1
296: 71 bc     acall $03BC
298: 27        add   a,@r1
299: 72 b4     orl   c,t0
29b: 41 f4     ajmp  $02F4
29d: a0 0f     orl   c,/$21.7
29f: d2 b4     setb  t0
2a1: 41 ff     ajmp  $02FF
2a3: 96        subb  a,@r0
2a4: b4 d2 a6  cjne  a,#$D2,$024D
2a7: c3        clr   c
2a8: c0 03     push  rb0r3
2aa: 04        inc   a
2ab: e4        clr   a
2ac: f1 d6     acall $07D6
2ae: 93        movc  a,@a+dptr
2af: b4 ff 11  cjne  a,#$FF,$02C3
2b2: fd        mov   r5,a
2b3: bc 27 b1  cjne  r4,#$27,$0267
2b6: 32        reti
2b7: 91 bb     acall $04BB
2b9: 12 91 71  lcall $9171
2bc: fd        mov   r5,a
2bd: c0 61     push  $61
2bf: be f1 d6  cjne  r6,#$F1,$0298
2c2: 93        movc  a,@a+dptr
2c3: b4 03 04  cjne  a,#$03,$02CA
2c6: ca        xch   a,r2
2c7: ff        mov   r7,a
2c8: 91 26     acall $0426
2ca: f1 d6     acall $07D6
2cc: e0        movx  a,@dptr
2cd: 06        inc   @r0
2ce: e4        clr   a
2cf: 05 c3     inc   $C3
2d1: f1 d6     acall $07D6
2d3: 93        movc  a,@a+dptr
2d4: e4        clr   a
2d5: 03        rr    a
2d6: 02 e4 b4  ljmp  $E4B4
2d9: 71 27     acall $0327
2db: 06        inc   @r0
2dc: ff        mov   r7,a
2dd: b6 b8 f1  cjne  @r0,#$B8,$02D1
2e0: e9        mov   a,r1
2e1: 06        inc   @r0
2e2: e4        clr   a
2e3: 07        inc   @r1
2e4: 26        add   a,@r0
2e5: f1 56     acall $0756
2e7: 06        inc   @r0
2e8: ea        mov   a,r2
2e9: f1 f8     acall $07F8
2eb: f9        mov   r1,a
2ec: b6 f3 fa  cjne  @r0,#$F3,$02E9
2ef: fb        mov   r3,a
2f0: f2        movx  @r0,a
2f1: e1 81     ajmp  $0781
2f3: 61 f2     ajmp  $03F2
2f5: fa        mov   r2,a
2f6: 0f        inc   r7
2f7: 00        nop
2f8: 61 c1     ajmp  $03C1
2fa: 61 e1     ajmp  $03E1
2fc: 4e        orl   a,r6
2fd: 4c        orl   a,r4
2fe: 6b        xrl   a,r3
2ff: 25 26     add   a,$26
301: d1 aa     acall $06AA
303: 38        addc  a,r0
304: 02 df be  ljmp  $DFBE
307: bd 05 9d  cjne  r5,#$05,$02A7
30a: 38        addc  a,r0
30b: 2b        add   a,r3
30c: d1 b8     acall $06B8
30e: bc be 06  cjne  r4,#$BE,$0317
311: 24 07     add   a,#$07
313: 2b        add   a,r3
314: b9 bd bb  cjne  r1,#$BD,$02D2
317: 85 f1 bc  mov   $BC,$F1
31a: b4 21 71  cjne  a,#$21,$038E
31d: 27        add   a,@r1
31e: 82 ba     anl   c,px1
320: 26        add   a,@r0
321: d1 aa     acall $06AA
323: 39        addc  a,r1
324: 06        inc   @r0
325: df be     djnz  r7,$02E5
327: bd 05 9d  cjne  r5,#$05,$02C7
32a: 38        addc  a,r0
32b: 01 d1     ajmp  $00D1
32d: bc bf f4  cjne  r4,#$BF,$0324
330: 06        inc   @r0
331: 57        anl   a,@r1
332: e3        movx  a,@r1
333: 1c        dec   r4
334: 08        inc   r0
335: a4        mul   ab
336: 3b        addc  a,r3
337: f4        cpl   a
338: 16        dec   @r0
339: 57        anl   a,@r1
33a: ef        mov   a,r7
33b: fb        mov   r3,a
33c: 00        nop
33d: a4        mul   ab
33e: 31 ba     acall $01BA
340: 39        addc  a,r1
341: bd d1 26  cjne  r5,#$D1,$036A
344: ae 05     mov   r6,rb0r5
346: b5 06 d1  cjne  a,rb0r6,$031A
349: 96        subb  a,@r0
34a: 06        inc   @r0
34b: df fd     djnz  r7,$034A
34d: 26        add   a,@r0
34e: d1 aa     acall $06AA
350: be bd d1  cjne  r6,#$BD,$0324
353: b8 39 05  cjne  r0,#$39,$035B
356: 9d        subb  a,r5
357: 39        addc  a,r1
358: bc be b9  cjne  r4,#$BE,$0314
35b: bd 2b 02  cjne  r5,#$2B,$0360
35e: 22        ret
35f: 07        inc   @r1
360: bb 85 8c  cjne  r3,#$85,$02EF
363: 27        add   a,@r1
364: 2b        add   a,r3
365: f1 bc     acall $07BC
367: b4 3e ba  cjne  a,#$3E,$0324
36a: a6 26     mov   @r0,$26
36c: 21 ff     ajmp  $01FF
36e: 96        subb  a,@r0
36f: 05 d1     inc   $D1
371: aa 39     mov   r2,$39
373: 01 df     ajmp  $00DF
375: be bd d1  cjne  r6,#$BD,$0349
378: 9d        subb  a,r5
379: 39        addc  a,r1
37a: 2b        add   a,r3
37b: 02 b8 bc  ljmp  $B8BC
37e: be b9 20  cjne  r6,#$B9,$03A1
381: 07        inc   @r1
382: 2b        add   a,r3
383: f1 bd     acall $07BD
385: bb 85 71  cjne  r3,#$85,$03F9
388: bc b4 21  cjne  r4,#$B4,$03AC
38b: 27        add   a,@r1
38c: 27        add   a,@r1
38d: 87 ba     mov   $BA,@r1
38f: 17        dec   @r1
390: d1 aa     acall $06AA
392: 39        addc  a,r1
393: 05 df     inc   $DF
395: be bd d1  cjne  r6,#$BD,$0369
398: 9d        subb  a,r5
399: 3d        addc  a,r5
39a: 38        addc  a,r0
39b: 06        inc   @r0
39c: b8 bc bd  cjne  r0,#$BC,$035C
39f: 97        subb  a,@r1
3a0: d1 d1     acall $06D1
3a2: d1 fb     acall $06FB
3a4: a9 93     mov   r1,$93
3a6: 93        movc  a,@a+dptr
3a7: ba 39 bd  cjne  r2,#$39,$0367
3aa: d1 27     acall $0627
3ac: ae 05     mov   r6,rb0r5
3ae: b5 17 d1  cjne  a,rb2r7,$0382
3b1: 96        subb  a,@r0
3b2: f1 07     acall $0707
3b4: fd        mov   r5,a
3b5: 27        add   a,@r1
3b6: e4        clr   a
3b7: b8 00 e9  cjne  r0,#$00,$03A3
3ba: 3f        addc  a,r7
3bb: 3d        addc  a,r5
3bc: f1 be     acall $07BE
3be: b9 d1 c2  cjne  r1,#$D1,$0383
3c1: 06        inc   @r0
3c2: 3d        addc  a,r5
3c3: 3d        addc  a,r5
3c4: b9 b8 bc  cjne  r1,#$B8,$0383
3c7: bd 06 d1  cjne  r5,#$06,$039B
3ca: e9        mov   a,r1
3cb: bc 97 a9  cjne  r4,#$97,$0377
3ce: c6        xch   a,@r0
3cf: 27        add   a,@r1
3d0: f4        cpl   a
3d1: b4 db d6  cjne  a,#$DB,$03AA
3d4: d6        xchd  a,@r0
3d5: c3        clr   c
3d6: f4        cpl   a
3d7: 0f        inc   r7
3d8: c3        clr   c
3d9: bc b4 96  cjne  r4,#$B4,$0372
3dc: db 27     djnz  r3,$0405
3de: 00        nop
3df: 26        add   a,@r0
3e0: 05 e4     inc   $E4
3e2: db 3e     djnz  r3,$0422
3e4: f1 d2     acall $07D2
3e6: be b9 3c  cjne  r6,#$B9,$0425
3e9: c2 38     clr   $27.0
3eb: a4        mul   ab
3ec: d1 bc     acall $06BC
3ee: 27        add   a,@r1
3ef: 1c        dec   r4
3f0: bf f4 a4  cjne  r7,#$F4,$0397
3f3: ef        mov   a,r7
3f4: 06        inc   @r0
3f5: 47        orl   a,@r1
3f6: 1c        dec   r4
3f7: f2        movx  @r0,a
3f8: 27        add   a,@r1
3f9: cc        xch   a,r4
3fa: 3a        addc  a,r2
3fb: 34 a4     addc  a,#$A4
3fd: b8 f0 c8  cjne  r0,#$F0,$03C8
400: cc        xch   a,r4
401: 34 17     addc  a,#$17
403: df f0     djnz  r7,$03F5
405: 27        add   a,@r1
406: d1 ba     acall $06BA
408: 39        addc  a,r1
409: bd d1 96  cjne  r5,#$D1,$03A2
40c: ae 05     mov   r6,rb0r5
40e: b5 be 3e  cjne  a,$BE,$044F
411: 3c        addc  a,r4
412: c2 3c     clr   $27.4
414: b9 d1 bc  cjne  r1,#$D1,$03D3
417: f4        cpl   a
418: 85 19 b8  mov   ip,rb3r1
41b: bc c3 95  cjne  r4,#$C3,$03B3
41e: 3e        addc  a,r6
41f: 2b        add   a,r3
420: be bd b3  cjne  r6,#$BD,$03D6
423: ce        xch   a,r6
424: 06        inc   @r0
425: 06        inc   @r0
426: 28        add   a,r0
427: ce        xch   a,r6
428: b9 bb 85  cjne  r1,#$BB,$03B0
42b: 8c 2c     mov   $2C,r4
42d: 2b        add   a,r3
42e: f1 27     acall $0727
430: 17        dec   @r1
431: df be     djnz  r7,$03F1
433: bd d1 aa  cjne  r5,#$D1,$03E0
436: 39        addc  a,r1
437: 05 d1     inc   $D1
439: b8 bc be  cjne  r0,#$BC,$03FA
43c: 9d        subb  a,r5
43d: 39        addc  a,r1
43e: 2e        add   a,r6
43f: 06        inc   @r0
440: b9 bd bb  cjne  r1,#$BD,$03FE
443: 85 21 01  mov   rb0r1,$21
446: 2e        add   a,r6
447: f1 8c     acall $078C
449: 28        add   a,r0
44a: 01 56     ajmp  $0056
44c: bc bf f4  cjne  r4,#$BF,$0443
44f: 0f        inc   r7
450: c3        clr   c
451: d6        xchd  a,@r0
452: 93        movc  a,@a+dptr
453: 1c        dec   r4
454: 53 0f 62  anl   rb1r7,#$62
457: ef        mov   a,r7
458: 4d        orl   a,r5
459: 28        add   a,r0
45a: 01 0f     ajmp  $000F
45c: bc bf b4  cjne  r4,#$BF,$0413
45f: 1c        dec   r4
460: ef        mov   a,r7
461: 21 27     ajmp  $0127
463: d1 5d     acall $065D
465: ba 17 df  cjne  r2,#$17,$0447
468: aa 39     mov   r2,$39
46a: 01 9d     ajmp  $009D
46c: be bd d1  cjne  r6,#$BD,$0440
46f: bc 3c 56  cjne  r4,#$3C,$04C8
472: a4        mul   ab
473: 02 f4 f0  ljmp  $F4F0
476: 26        add   a,@r0
477: d1 df     acall $06DF
479: be bd d1  cjne  r6,#$BD,$044D
47c: aa 38     mov   r2,$38
47e: 05 9d     inc   $9D
480: b8 bc bd  cjne  r0,#$BC,$0440
483: 97        subb  a,@r1
484: 3c        addc  a,r4
485: 31 01     acall $0101
487: d1 a9     acall $06A9
489: 93        movc  a,@a+dptr
48a: ba ae d1  cjne  r2,#$AE,$045E
48d: fb        mov   r3,a
48e: 38        addc  a,r0
48f: bd 05 b5  cjne  r5,#$05,$0447
492: 02 fd d1  ljmp  $FDD1
495: 26        add   a,@r0
496: d1 26     acall $0626
498: 05 df     inc   $DF
49a: be bd d1  cjne  r6,#$BD,$046E
49d: aa 39     mov   r2,$39
49f: 01 d1     ajmp  $00D1
4a1: bc bf 97  cjne  r4,#$BF,$043B
4a4: 9d        subb  a,r5
4a5: 38        addc  a,r0
4a6: 01 a7     ajmp  $00A7
4a8: 1c        dec   r4
4a9: 16        dec   @r0
4aa: 57        anl   a,@r1
4ab: e3        movx  a,@r1
4ac: f4        cpl   a
4ad: 00        nop
4ae: a4        mul   ab
4af: b2 ef     cpl   $E8.7
4b1: fb        mov   r3,a
4b2: 39        addc  a,r1
4b3: bd a8 ba  cjne  r5,#$A8,$0470
4b6: ae 01     mov   r6,rb0r1
4b8: d1 26     acall $0626
4ba: d1 be     acall $06BE
4bc: b5 05 fd  cjne  a,rb0r5,$04BC
4bf: 3c        addc  a,r4
4c0: b9 fe 27  cjne  r1,#$FE,$04EA
4c3: e9        mov   a,r1
4c4: 0a        inc   r2
4c5: a8 f1     mov   r0,$F1
4c7: ce        xch   a,r6
4c8: e9        mov   a,r1
4c9: 71 26     acall $0326
4cb: f1 c2     acall $07C2
4cd: da 0e     djnz  r2,$04DD
4cf: e4        clr   a
4d0: 07        inc   @r1
4d1: d8 f1     djnz  r0,$04C4
4d3: ec        mov   a,r4
4d4: 93        movc  a,@a+dptr
4d5: ac f1     mov   r4,$F1
4d7: d1 b8     acall $06B8
4d9: f1 96     acall $0796
4db: a6 0e     mov   @r0,rb1r6
4dd: e9        mov   a,r1
4de: ff        mov   r7,a
4df: 96        subb  a,@r0
4e0: 26        add   a,@r0
4e1: f1 17     acall $0717
4e3: d6        xchd  a,@r0
4e4: 06        inc   @r0
4e5: e4        clr   a
4e6: af 03     mov   r7,rb0r3
4e8: 93        movc  a,@a+dptr
4e9: 71 27     acall $0327
4eb: f0        movx  @dptr,a
4ec: ef        mov   a,r7
4ed: da 81     djnz  r2,$0470
4ef: ff        mov   r7,a
4f0: b8 f1 96  cjne  r0,#$F1,$0489
4f3: f1 06     acall $0706
4f5: e9        mov   a,r1
4f6: 53 11 d6  anl   rb2r1,#$D6
4f9: f1 01     acall $0701
4fb: e4        clr   a
4fc: c3        clr   c
4fd: 26        add   a,@r0
4fe: f1 07     acall $0707
500: c3        clr   c
501: b8 f1 96  cjne  r0,#$F1,$049A
504: 07        inc   @r1
505: 01 e9     ajmp  $00E9
507: f1 c8     acall $07C8
509: 27        add   a,@r1
50a: b4 72 bc  cjne  a,#$72,$04C9
50d: f4        cpl   a
50e: 10 12 b4  jbc   $22.2,$04C5
511: 11 71     acall $0071
513: 96        subb  a,@r0
514: 08        inc   r0
515: bc 8b 11  cjne  r4,#$8B,$0529
518: d6        xchd  a,@r0
519: 23        rl    a
51a: 03        rr    a
51b: e4        clr   a
51c: c3        clr   c
51d: 26        add   a,@r0
51e: f1 07     acall $0707
520: c3        clr   c
521: b8 f1 96  cjne  r0,#$F1,$04BA
524: 27        add   a,@r1
525: 03        rr    a
526: e9        mov   a,r1
527: 26        add   a,@r0
528: 01 df     ajmp  $00DF
52a: be bd d1  cjne  r6,#$BD,$04FE
52d: aa 39     mov   r2,$39
52f: 01 d1     ajmp  $00D1
531: bc bf 97  cjne  r4,#$BF,$04CB
534: 9d        subb  a,r5
535: 38        addc  a,r0
536: 01 a7     ajmp  $00A7
538: 1c        dec   r4
539: 16        dec   @r0
53a: 57        anl   a,@r1
53b: e3        movx  a,@r1
53c: f4        cpl   a
53d: 00        nop
53e: a4        mul   ab
53f: 42 ef     orl   $EF,a
541: fb        mov   r3,a
542: 39        addc  a,r1
543: bd 38 ba  cjne  r5,#$38,$0500
546: ae 01     mov   r6,rb0r1
548: d1 26     acall $0626
54a: d1 26     acall $0626
54c: b5 01 fd  cjne  a,rb0r1,$054C
54f: 48        orl   a,r0
550: a1 bc     ajmp  $05BC
552: f4        cpl   a
553: 82 22     anl   c,$24.2
555: 02 d2 d6  ljmp  $D2D6
558: 40 27     jc    $0581
55a: e4        clr   a
55b: 39        addc  a,r1
55c: a4        mul   ab
55d: f1 ba     acall $07BA
55f: 12 66 3f  lcall $663F
562: 39        addc  a,r1
563: 06        inc   @r0
564: ba be bd  cjne  r2,#$BE,$0524
567: d1 9d     acall $069D
569: 39        addc  a,r1
56a: 56        anl   a,@r0
56b: a4        mul   ab
56c: bc f4 0f  cjne  r4,#$F4,$057E
56f: b8 39 3c  cjne  r0,#$39,$05AE
572: 06        inc   @r0
573: a4        mul   ab
574: bc bf f0  cjne  r4,#$BF,$0567
577: c8        xch   a,r0
578: cc        xch   a,r4
579: 75 31 3a  mov   $31,#$3A
57c: ef        mov   a,r7
57d: bc b4 1c  cjne  r4,#$B4,$059C
580: b4 bc f4  cjne  a,#$BC,$0577
583: 95 05     subb  a,rb0r5
585: 32        reti
586: 12 b1 8e  lcall $B18E
589: ce        xch   a,r6
58a: 31 ac     acall $01AC
58c: a1 bc     ajmp  $05BC
58e: f4        cpl   a
58f: 06        inc   @r0
590: fd        mov   r5,a
591: f0        movx  @dptr,a
592: 96        subb  a,@r0
593: 03        rr    a
594: a8 a4     mov   r0,$A4
596: f1 d6     acall $07D6
598: 04        inc   a
599: 93        movc  a,@a+dptr
59a: 95 c8     subb  a,$C8
59c: 85 9f f1  mov   $F1,$9F
59f: 95 bc     subb  a,$BC
5a1: f4        cpl   a
5a2: b3        cpl   c
5a3: 07        inc   @r1
5a4: 35 af     addc  a,$AF
5a6: bc 93 ae  cjne  r4,#$93,$0557
5a9: f5 37     mov   $37,a
5ab: ce        xch   a,r6
5ac: a1 a4     ajmp  $05A4
5ae: 12 b1 8e  lcall $B18E
5b1: 31 a1     acall $01A1
5b3: ff        mov   r7,a
5b4: bc 14 ce  cjne  r4,#$14,$0585
5b7: a6 96     mov   @r0,$96
5b9: 31 a8     acall $01A8
5bb: f4        cpl   a
5bc: bc f4 ac  cjne  r4,#$F4,$056B
5bf: 2f        add   a,r7
5c0: 12 2f f0  lcall $2FF0
5c3: ca        xch   a,r2
5c4: c7        xch   a,@r1
5c5: 46        orl   a,@r0
5c6: a1 2f     ajmp  $052F
5c8: 46        orl   a,@r0
5c9: a0 03     orl   c,/$20.3
5cb: 06        inc   @r0
5cc: 0f        inc   r7
5cd: f1 d6     acall $07D6
5cf: 93        movc  a,@a+dptr
5d0: b8 c8 b4  cjne  r0,#$C8,$0587
5d3: cc        xch   a,r4
5d4: f1 cc     acall $07CC
5d6: fb        mov   r3,a
5d7: b4 ff 31  cjne  a,#$FF,$060B
5da: 06        inc   @r0
5db: a8 bc     mov   r0,$BC
5dd: f4        cpl   a
5de: fd        mov   r5,a
5df: ac f4     mov   r4,$F4
5e1: bc f4 ed  cjne  r4,#$F4,$05D1
5e4: af 35     mov   r7,$35
5e6: 12 ff 06  lcall $FF06
5e9: 57        anl   a,@r1
5ea: 96        subb  a,@r0
5eb: 47        orl   a,@r1
5ec: 0a        inc   r2
5ed: a0 ff     orl   c,/$F8.7
5ef: 06        inc   @r0
5f0: 0a        inc   r2
5f1: 47        orl   a,@r1
5f2: 96        subb  a,@r0
5f3: 02 57 a0  ljmp  $57A0
5f6: bc f4 56  cjne  r4,#$F4,$064F
5f9: a4        mul   ab
5fa: f1 46     acall $0746
5fc: 9f        subb  a,r7
5fd: 27        add   a,@r1
5fe: e4        clr   a
5ff: 02 ad 00  ljmp  $AD00
602: e9        mov   a,r1
603: 39        addc  a,r1
604: b8 f1 be  cjne  r0,#$F1,$05C5
607: fd        mov   r5,a
608: 12 be ba  lcall $BEBA
60b: bd 09 3f  cjne  r5,#$09,$064D
60e: 3c        addc  a,r4
60f: 06        inc   @r0
610: d1 71     acall $0671
612: 96        subb  a,@r0
613: 39        addc  a,r1
614: b5 be b8  cjne  a,$BE,$05CF
617: bc 2b 04  cjne  r4,#$2B,$061E
61a: 27        add   a,@r1
61b: 06        inc   @r0
61c: be b9 bd  cjne  r6,#$B9,$05DC
61f: bb 2e f1  cjne  r3,#$2E,$0613
622: b8 bc 85  cjne  r0,#$BC,$05AA
625: 8c 3a     mov   $3A,r4
627: 2c        add   a,r4
628: be b9 bd  cjne  r6,#$B9,$05E8
62b: bb 04 28  cjne  r3,#$04,$0656
62e: 02 2a 85  ljmp  $2A85
631: 71 2e     acall $032E
633: 0f        inc   r7
634: f1 bc     acall $07BC
636: b4 cc b4  cjne  a,#$CC,$05ED
639: bc b8 f0  cjne  r4,#$B8,$062C
63c: 1f        dec   r7
63d: 27        add   a,@r1
63e: 32        reti
63f: bf 00 45  cjne  r7,#$00,$0687
642: 2f        add   a,r7
643: a4        mul   ab
644: 12 bf ff  lcall $BFFF
647: 21 ba     ajmp  $01BA
649: 01 df     ajmp  $00DF
64b: be 26 d1  cjne  r6,#$26,$061F
64e: aa 39     mov   r2,$39
650: bd d1 b8  cjne  r5,#$D1,$060B
653: bc 01 9d  cjne  r4,#$01,$05F3
656: 39        addc  a,r1
657: 2b        add   a,r3
658: be b9 bd  cjne  r6,#$B9,$0618
65b: bb 04 26  cjne  r3,#$04,$0684
65e: 07        inc   @r1
65f: 2b        add   a,r3
660: 85 8c 27  mov   $27,th0
663: 9e        subb  a,r6
664: f1 bc     acall $07BC
666: b4 21 ba  cjne  a,#$21,$0623
669: 84        div   ab
66a: 3a        addc  a,r2
66b: ff        mov   r7,a
66c: 83        movc  a,@a+pc
66d: 84        div   ab
66e: ff        mov   r7,a
66f: ff        mov   r7,a
670: 39        addc  a,r1
671: 84        div   ab
672: 3a        addc  a,r2
673: ff        mov   r7,a
674: b9 8c ff  cjne  r1,#$8C,$0676
677: ff        mov   r7,a
678: 39        addc  a,r1
679: 29        add   a,r1
67a: 9c        subb  a,r4
67b: 39        addc  a,r1
67c: 9c        subb  a,r4
67d: b5 ff ab  cjne  a,$FF,$062B
680: ff        mov   r7,a
681: fa        mov   r2,a
682: 6c        xrl   a,r4
683: bc e1 06  cjne  r4,#$E1,$068C
686: a8 27     mov   r0,$27
688: bf f8 17  cjne  r7,#$F8,$06A2
68b: c8        xch   a,r0
68c: 08        inc   r0
68d: a6 a4     mov   @r0,$A4
68f: cc        xch   a,r4
690: ef        mov   a,r7
691: 96        subb  a,@r0
692: a6 f4     mov   @r0,$F4
694: 8a ff     mov   $FF,r2
696: 96        subb  a,@r0
697: 16        dec   @r0
698: 00        nop
699: a4        mul   ab
69a: 86 f1     mov   $F1,@r0
69c: 57        anl   a,@r1
69d: 1c        dec   r4
69e: fa        mov   r2,a
69f: e4        clr   a
6a0: 06        inc   @r0
6a1: 57        anl   a,@r1
6a2: ac a4     mov   r4,$A4
6a4: 00        nop
6a5: 2e        add   a,r6
6a6: 2e        add   a,r6
6a7: ca        xch   a,r2
6a8: ce        xch   a,r6
6a9: 9d        subb  a,r5
6aa: f4        cpl   a
6ab: 57        anl   a,@r1
6ac: ed        mov   a,r5
6ad: 96        subb  a,@r0
6ae: 70 a4     jnz   $0654
6b0: 18        dec   r0
6b1: ed        mov   a,r5
6b2: 86 ac     mov   $AC,@r0
6b4: 1c        dec   r4
6b5: a9 fa     mov   r1,$FA
6b7: f4        cpl   a
6b8: 2e        add   a,r6
6b9: 2e        add   a,r6
6ba: e9        mov   a,r1
6bb: ce        xch   a,r6
6bc: a8 f1     mov   r0,$F1
6be: ca        xch   a,r2
6bf: ed        mov   a,r5
6c0: b5 27 e4  cjne  a,$27,$06A7
6c3: 32        reti
6c4: 96        subb  a,@r0
6c5: f1 85     acall $0785
6c7: cc        xch   a,r4
6c8: 95 39     subb  a,$39
6ca: cf        xch   a,r7
6cb: 3f        addc  a,r7
6cc: ba 12 ba  cjne  r2,#$12,$0689
6cf: bd 06 9d  cjne  r5,#$06,$066F
6d2: d3        setb  c
6d3: f9        mov   r1,a
6d4: d1 b3     acall $06B3
6d6: 96        subb  a,@r0
6d7: a8 ac     mov   r0,$AC
6d9: 06        inc   @r0
6da: d1 96     acall $0696
6dc: bd 97 a9  cjne  r5,#$97,$0688
6df: ab e7     mov   r3,$E7
6e1: d1 59     acall $0659
6e3: ec        mov   a,r4
6e4: ad f2     mov   r5,$F2
6e6: c3        clr   c
6e7: 27        add   a,@r1
6e8: 17        dec   @r1
6e9: d6        xchd  a,@r0
6ea: f1 2b     acall $072B
6ec: ab 04     mov   r3,rb0r4
6ee: 20 f1 20  jb    b.1,$0711
6f1: 27        add   a,@r1
6f2: f1 a9     acall $07A9
6f4: 96        subb  a,@r0
6f5: 17        dec   @r1
6f6: e4        clr   a
6f7: 26        add   a,@r0
6f8: 80 eb     sjmp  $06E5
6fa: 96        subb  a,@r0
6fb: d1 e7     acall $06E7
6fd: fc        mov   r4,a
6fe: ab f2     mov   r3,$F2
700: d9 04     djnz  r1,$0706
702: e9        mov   a,r1
703: bc b8 f1  cjne  r4,#$B8,$06F7
706: 96        subb  a,@r0
707: 36        addc  a,@r0
708: f4        cpl   a
709: 6f        xrl   a,r7
70a: f1 12     acall $0712
70c: 96        subb  a,@r0
70d: af dc     mov   r7,$DC
70f: 0a        inc   r2
710: 52 ff     anl   $FF,a
712: 3c        addc  a,r4
713: 2f        add   a,r7
714: 0a        inc   r2
715: 96        subb  a,@r0
716: 31 2a     acall $012A
718: 25 1e     add   a,rb3r6
71a: 16        dec   @r0
71b: e1 20     ajmp  $0720
71d: 17        dec   @r1
71e: 0f        inc   r7
71f: fa        mov   r2,a
720: 6d        xrl   a,r5
721: 12 96 05  lcall $9605
724: 06        inc   @r0
725: a6 26     mov   @r0,$26
727: f1 e4     acall $07E4
729: 00        nop
72a: b8 b0 06  cjne  r0,#$B0,$0733
72d: 57        anl   a,@r1
72e: 39        addc  a,r1
72f: 00        nop
730: c8        xch   a,r0
731: c8        xch   a,r0
732: 31 bc     acall $01BC
734: a0 b0     orl   c,/rxd
736: c8        xch   a,r0
737: 1d        dec   r5
738: 11 06     acall $0006
73a: 57        anl   a,@r1
73b: 42 b0     orl   p3,a
73d: 06        inc   @r0
73e: 33        rlc   a
73f: 06        inc   @r0
740: 50 a0     jnc   $06E2
742: 39        addc  a,r1
743: 2b        add   a,r3
744: 57        anl   a,@r1
745: b8 bc be  cjne  r0,#$BC,$0706
748: 04        inc   a
749: 27        add   a,@r1
74a: 07        inc   @r1
74b: 2b        add   a,r3
74c: b9 bd bb  cjne  r1,#$BD,$070A
74f: 85 f1 bc  mov   $BC,$F1
752: b4 f1 8c  cjne  a,#$F1,$06E1
755: 27        add   a,@r1
756: af 03     mov   r7,rb0r3
758: d6        xchd  a,@r0
759: 93        movc  a,@a+dptr
75a: bc 11 06  cjne  r4,#$11,$0763
75d: 61 1d     ajmp  $031D
75f: b0 17     anl   c,/$22.7
761: f1 f1     acall $07F1
763: d6        xchd  a,@r0
764: 94 c8     subb  a,#$C8
766: 03        rr    a
767: 02 93 b8  ljmp  $93B8
76a: 80 3f     sjmp  $07AB
76c: 72 2e     orl   c,$25.6
76e: 17        dec   @r1
76f: 90 f1 21  mov   dptr,#$F121
772: 19        dec   r1
773: 56        anl   a,@r0
774: c8        xch   a,r0
775: ba f0 f0  cjne  r2,#$F0,$0768
778: b3        cpl   c
779: ee        mov   a,r6
77a: 95 82     subb  a,dpl
77c: 82 7f     anl   c,$2F.7
77e: e1 c3     ajmp  $07C3
780: 8c 47     mov   $47,r4
782: ed        mov   a,r5
783: e1 95     ajmp  $0795
785: a4        mul   ab
786: 88 a0     mov   p2,r0
788: cc        xch   a,r4
789: f0        movx  @dptr,a
78a: 0f        inc   r7
78b: 97        subb  a,@r1
78c: 19        dec   r1
78d: 56        anl   a,@r0
78e: b3        cpl   c
78f: ee        mov   a,r6
790: 91 e1     acall $04E1
792: c3        clr   c
793: 95 95     subb  a,$95
795: 97        subb  a,@r1
796: 9d        subb  a,r5
797: a4        mul   ab
798: ed        mov   a,r5
799: e1 cc     ajmp  $07CC
79b: e1 99     ajmp  $0799
79d: a0 c8     orl   c,/$C8.0
79f: 71 fb     acall $03FB
7a1: f4        cpl   a
7a2: a9 0f     mov   r1,rb1r7
7a4: ac 93     mov   r4,$93
7a6: b4 fb cb  cjne  a,#$FB,$0774
7a9: 93        movc  a,@a+dptr
7aa: 27        add   a,@r1
7ab: f9        mov   r1,a
7ac: d9 a0     djnz  r1,$074E
7ae: af d6     mov   r7,$D6
7b0: 28        add   a,r0
7b1: b1 f9     acall $05F9
7b3: 29        add   a,r1
7b4: 93        movc  a,@a+dptr
7b5: 1f        dec   r7
7b6: d6        xchd  a,@r0
7b7: 93        movc  a,@a+dptr
7b8: ba ff c6  cjne  r2,#$FF,$0781
7bb: ac 1f     mov   r4,rb3r7
7bd: 93        movc  a,@a+dptr
7be: f9        mov   r1,a
7bf: f4        cpl   a
7c0: 06        inc   @r0
7c1: a4        mul   ab
7c2: a7 fa     mov   @r1,$FA
7c4: 10 11 93  jbc   $22.1,$075A
7c7: 96        subb  a,@r0
7c8: bc b4 96  cjne  r4,#$B4,$0761
7cb: a6 36     mov   @r0,$36
7cd: ff        mov   r7,a
7ce: ff        mov   r7,a
7cf: 96        subb  a,@r0
7d0: f2        movx  @r0,a
7d1: d2 e7     setb  acc.7
7d3: e7        mov   a,@r1
7d4: fa        mov   r2,a
7d5: fa        mov   r2,a
7d6: 17        dec   @r1
7d7: ac 86     mov   r4,$86
7d9: 03        rr    a
7da: c3        clr   c
7db: f1 f1     acall $07F1
7dd: 17        dec   @r1
7de: dc c8     djnz  r4,$07A8
7e0: 96        subb  a,@r0
7e1: d0 b0     pop   p3
7e3: 1c        dec   r4
7e4: f1 11     acall $0711
7e6: a8 11     mov   r0,rb2r1
7e8: b0 68     anl   c,/$2D.0
7ea: 28        add   a,r0
7eb: d0 47     pop   $47
7ed: 86 f1     mov   $F1,@r0
7ef: f8        mov   r0,a
7f0: 3f        addc  a,r7
7f1: 1c        dec   r4
7f2: 3f        addc  a,r7
7f3: 86 94     mov   $94,@r0
7f5: 47        orl   a,@r1
7f6: 94 71     subb  a,#$71
7f8: 9d        subb  a,r5
7f9: 26        add   a,@r0
7fa: 3a        addc  a,r2
7fb: e8        mov   a,r0
7fc: 94 4f     subb  a,#$4F
7fe: 01 ff     ajmp  $08FF
