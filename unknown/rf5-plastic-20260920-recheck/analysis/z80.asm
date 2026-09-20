000: ff        rst  $38
001: d5        push de
002: 9e        sbc  a,(hl)
003: b4        or   h
004: 21 01 fb  ld   hl,$FB01
007: c5        push bc
008: bc        cp   h
009: a4        and  h
00a: 56        ld   d,(hl)
00b: c3 30 fb  jp   $FB30
00e: f8        ret  m
00f: 12        ld   (de),a
010: e1        pop  hl
011: 26 62     ld   h,$62
013: 6f        ld   l,a
014: fa e4 26  jp   m,$26E4
017: 3a 8c 0c  ld   a,($0C8C)
01a: 26 3a     ld   h,$3A
01c: ff        rst  $38
01d: ae        xor  (hl)
01e: 5f        ld   e,a
01f: b8        cp   b
020: 2e 12     ld   l,$12
022: c8        ret  z
023: 17        rla
024: 80        add  a,b
025: 2e 80     ld   l,$80
027: 3f        ccf
028: 90        sub  b
029: 44        ld   b,h
02a: f2 fb 52  jp   p,$52FB
02d: fa 44 06  jp   m,$0644
030: 1f        rra
031: 06 ac     ld   b,$AC
033: 3c        inc  a
034: a8        xor  b
035: 01 f4 8a  ld   bc,$8AF4
038: df        rst  $18
039: 5f        ld   e,a
03a: 3c        inc  a
03b: 07        rlca
03c: 9a        sbc  a,d
03d: f0        ret  p
03e: fb        ei
03f: 47        ld   b,a
040: 3a 77 01  ld   a,($0177)
043: 48        ld   c,b
044: eb        ex   de,hl
045: bb        cp   e
046: 83        add  a,e
047: 05        dec  b
048: 85        add  a,l
049: fe 06     cp   $06
04b: 5e        ld   e,(hl)
04c: 95        sub  l
04d: bc        cp   h
04e: 52        ld   d,d
04f: b3        or   e
050: 57        ld   d,a
051: 46        ld   b,(hl)
052: aa        xor  d
053: 72        ld   (hl),d
054: fa 80 01  jp   m,$0180
057: 95        sub  l
058: 2e 2e     ld   l,$2E
05a: 77        ld   (hl),a
05b: 4d        ld   c,l
05c: fc 77 ec  call m,$EC77
05f: fa 56 aa  jp   m,$AA56
062: 71        ld   (hl),c
063: 72        ld   (hl),d
064: 7f        ld   a,a
065: b3        or   e
066: ef        rst  $28
067: fe bc     cp   $BC
069: 53        ld   d,e
06a: d6 c3     sub  $C3
06c: 36 74     ld   (hl),$74
06e: 04        inc  b
06f: 74        ld   (hl),h
070: fe bf     cp   $BF
072: ef        rst  $28
073: 1f        rra
074: a4        and  h
075: 07        rlca
076: 77        ld   (hl),a
077: bc        cp   h
078: 34        inc  (hl)
079: 07        rlca
07a: 93        sub  e
07b: 26 f4     ld   h,$F4
07d: a4        and  h
07e: 87        add  a,a
07f: 95        sub  l
080: a4        and  h
081: 14        inc  d
082: 46        ld   b,(hl)
083: aa        xor  d
084: 1c        inc  e
085: fa 08 bc  jp   m,$BC08
088: 2f        cpl
089: 07        rlca
08a: 8f        adc  a,a
08b: 95        sub  l
08c: f4 c3 01  call p,$01C3
08f: fa 46 aa  jp   m,$AA46
092: 8f        adc  a,a
093: bc        cp   h
094: 10 26     djnz $00BC
096: a4        and  h
097: 30 f4     jr   nc,$008D
099: 96        sub  (hl)
09a: 15        dec  d
09b: cd 3f c5  call $C53F
09e: c9        ret
09f: 3f        ccf
0a0: 96        sub  (hl)
0a1: ae        xor  (hl)
0a2: ff        rst  $38
0a3: 96        sub  (hl)
0a4: 6e        ld   l,(hl)
0a5: 96        sub  (hl)
0a6: a6        and  (hl)
0a7: 26 0c     ld   h,$0C
0a9: e4 0f 03  call po,$030F
0ac: f1        pop  af
0ad: 56        ld   d,(hl)
0ae: d6 86     sub  $86
0b0: 84        add  a,h
0b1: 0f        rrca
0b2: b8        cp   b
0b3: f1        pop  af
0b4: 56        ld   d,(hl)
0b5: 86        add  a,(hl)
0b6: 02        ld   (bc),a
0b7: e9        jp   (hl)
0b8: 96        sub  (hl)
0b9: 08        ex   af,af'
0ba: bf        cp   a
0bb: 05        dec  b
0bc: 26 33     ld   h,$33
0be: 26 b8     ld   h,$B8
0c0: 01 bc b4  ld   bc,$B4BC
0c3: bc        cp   h
0c4: a0        and  b
0c5: 2f        cpl
0c6: 8f        adc  a,a
0c7: 1d        dec  e
0c8: 11 06 b8  ld   de,$B806
0cb: f1        pop  af
0cc: b0        or   b
0cd: 06 01     ld   b,$01
0cf: e9        jp   (hl)
0d0: 96        sub  (hl)
0d1: 4a        ld   c,d
0d2: 02        ld   (bc),a
0d3: e4 21 26  call po,$2621
0d6: f1        pop  af
0d7: 96        sub  (hl)
0d8: 26 bc     ld   h,$BC
0da: a4        and  h
0db: b4        or   h
0dc: f8        ret  m
0dd: 0c        inc  c
0de: cc a7 bc  call z,$BCA7
0e1: a4        and  h
0e2: b4        or   h
0e3: 42        ld   b,d
0e4: 17        rla
0e5: cc d4 96  call z,$96D4
0e8: 27        daa
0e9: b8        cp   b
0ea: a0        and  b
0eb: e9        jp   (hl)
0ec: d7        rst  $10
0ed: 3f        ccf
0ee: e8        ret  pe
0ef: 26 01     ld   h,$01
0f1: af        xor  a
0f2: e4 d5 ab  call po,$ABD5
0f5: 26 62     ld   h,$62
0f7: 55        ld   d,l
0f8: 25        dec  h
0f9: fb        ei
0fa: eb        ex   de,hl
0fb: ef        rst  $28
0fc: fb        ei
0fd: fb        ei
0fe: fc fc fb  call m,$FBFC
101: 43        ld   b,e
102: 17        rla
103: 86        add  a,(hl)
104: 43        ld   b,e
105: 26 d1     ld   h,$D1
107: bf        cp   a
108: 05        dec  b
109: a1        and  c
10a: 0e 27     ld   c,$27
10c: 11 b8 ad  ld   de,$ADB8
10f: af        xor  a
110: ae        xor  (hl)
111: e9        jp   (hl)
112: b3        or   e
113: a4        and  h
114: f1        pop  af
115: b1        or   c
116: 11 91 dd  ld   de,$DD91
119: a4        and  h
11a: 96        sub  (hl)
11b: a4        and  h
11c: 11 d1 11  ld   de,$11D1
11f: 71        ld   (hl),c
120: 6e        ld   l,(hl)
121: a4        and  h
122: a1        and  c
123: a4        and  h
124: 11 11 11  ld   de,$1111
127: 51        ld   d,c
128: a1        and  c
129: a4        and  h
12a: a7        and  a
12b: a4        and  h
12c: 11 31 11  ld   de,$1131
12f: ef        rst  $28
130: 16 cd     ld   d,$CD
132: a4        and  h
133: af        xor  a
134: f1        pop  af
135: 11 2d fd  ld   de,$FD2D
138: f1        pop  af
139: 11 ef c3  ld   de,$C3EF
13c: cd a4 38  call $38A4
13f: 43        ld   b,e
140: 26 d1     ld   h,$D1
142: 21 f1 0f  ld   hl,$0FF1
145: 86        add  a,(hl)
146: 07        rlca
147: c8        ret  z
148: 11 93 71  ld   de,$7193
14b: 43        ld   b,e
14c: d8        ret  c
14d: 51        ld   d,c
14e: be        cp   (hl)
14f: aa        xor  d
150: f1        pop  af
151: 21 bf ff  ld   hl,$FFBF
154: dc aa 3f  call c,$3FAA
157: a8        xor  b
158: f1        pop  af
159: ef        rst  $28
15a: bf        cp   a
15b: ff        rst  $38
15c: e9        jp   (hl)
15d: 53        ld   d,e
15e: 3f        ccf
15f: d6 0a     sub  $0A
161: 6f        ld   l,a
162: f1        pop  af
163: df        rst  $18
164: c3 ff e4  jp   $E4FF
167: c3 6f 07  jp   $076F
16a: 86        add  a,(hl)
16b: 51        ld   d,c
16c: 26 d1     ld   h,$D1
16e: 21 ff a8  ld   hl,$A8FF
171: f1        pop  af
172: ef        rst  $28
173: 26 27     ld   h,$27
175: e9        jp   (hl)
176: 5b        ld   e,e
177: 06 bc     ld   b,$BC
179: 94        sub  h
17a: 3f        ccf
17b: 03        inc  bc
17c: 1d        dec  e
17d: 26 b8     ld   h,$B8
17f: f1        pop  af
180: e9        jp   (hl)
181: 02        ld   (bc),a
182: 3e e9     ld   a,$E9
184: 26 b8     ld   h,$B8
186: f1        pop  af
187: 26 06     ld   h,$06
189: 3b        dec  sp
18a: e9        jp   (hl)
18b: ff        rst  $38
18c: b8        cp   b
18d: f1        pop  af
18e: 26 b8     ld   h,$B8
190: 00        nop
191: e9        jp   (hl)
192: 15        dec  d
193: 07        rlca
194: f1        pop  af
195: b8        cp   b
196: ff        rst  $38
197: f1        pop  af
198: 0a        ld   a,(bc)
199: c8        ret  z
19a: 0a        ld   a,(bc)
19b: ee a0     xor  $A0
19d: f1        pop  af
19e: 06 a0     ld   b,$A0
1a0: f1        pop  af
1a1: 06 ac     ld   b,$AC
1a3: 96        sub  (hl)
1a4: 0a        ld   a,(bc)
1a5: eb        ex   de,hl
1a6: cf        rst  $08
1a7: ff        rst  $38
1a8: a6        and  (hl)
1a9: 42        ld   b,d
1aa: c3 8c 96  jp   $968C
1ad: 17        rla
1ae: aa        xor  d
1af: ff        rst  $38
1b0: 8a        adc  a,d
1b1: 0c        inc  c
1b2: b8        cp   b
1b3: f1        pop  af
1b4: 7f        ld   a,a
1b5: 37        scf
1b6: 05        dec  b
1b7: e9        jp   (hl)
1b8: 11 ba bc  ld   de,$BCBA
1bb: f4 bc 07  call p,$07BC
1be: 32 be 0f  ld   ($0FBE),a
1c1: c5        push bc
1c2: 1f        rra
1c3: 28 12     jr   z,$01D7
1c5: be        cp   (hl)
1c6: bc        cp   h
1c7: b8        cp   b
1c8: 20 ed     jr   nz,$01B7
1ca: 84        add  a,h
1cb: 9a        sbc  a,d
1cc: 21 bd 3a  ld   hl,$3ABD
1cf: 83        add  a,e
1d0: 99        sbc  a,c
1d1: 8c        adc  a,h
1d2: 9b        sbc  a,e
1d3: 23        inc  hl
1d4: b9        cp   c
1d5: bb        cp   e
1d6: bc        cp   h
1d7: fc 21 ff  call m,$FF21
1da: c4 da e5  call nz,$E5DA
1dd: fd        db   $fd
1de: 7a        ld   a,d
1df: c3 d9 cc  jp   $CCD9
1e2: db 94     in   a,($94)
1e4: f9        ld   sp,hl
1e5: fb        ei
1e6: 3f        ccf
1e7: 01 e8 3f  ld   bc,$3FE8
1ea: fa 56 ff  jp   m,$FF56
1ed: e1        pop  hl
1ee: f4 e0 c3  call p,$C3E0
1f1: e1        pop  hl
1f2: f4 06 f1  call p,$F106
1f5: fa 5e ce  jp   m,$CE5E
1f8: a6        and  (hl)
1f9: a0        and  b
1fa: 1c        inc  e
1fb: ed        db   $ed
1fc: 17        rla
1fd: 18 ea     jr   $01E9
1ff: 26 06     ld   h,$06
201: e4 05 0c  call po,$0C05
204: f1        pop  af
205: d6 93     sub  $93
207: 41        ld   b,c
208: 25        dec  h
209: d6 17     sub  $17
20b: 02        ld   (bc),a
20c: 11 93 bc  ld   de,$BC93
20f: f4 37 17  call p,$1737
212: 52        ld   d,d
213: 15        dec  d
214: b2        or   d
215: b1        or   c
216: c1        pop  bc
217: f1        pop  af
218: 03        inc  bc
219: 06 25     ld   b,$25
21b: 02        ld   (bc),a
21c: d6 93     sub  $93
21e: bc        cp   h
21f: f4 d6 a4  call p,$A4D6
222: c8        ret  z
223: 02        ld   (bc),a
224: 20 f1     jr   nz,$0217
226: bc        cp   h
227: f4 37 30  call p,$3037
22a: f7        rst  $30
22b: b1        or   c
22c: 72        ld   (hl),d
22d: d6 a4     sub  $A4
22f: 17        rla
230: bc        cp   h
231: f4 92 d6  call p,$D692
234: 02        ld   (bc),a
235: 37        scf
236: 3e ef     ld   a,$EF
238: a4        and  h
239: f5        push af
23a: d6 32     sub  $32
23c: 91        sub  c
23d: 11 ad 56  ld   de,$56AD
240: 53        ld   d,e
241: 93        sub  e
242: 17        rla
243: b1        or   c
244: a7        and  a
245: 56        ld   d,(hl)
246: 11 71 df  ld   de,$DF71
249: bc        cp   h
24a: da 05 11  jp   c,$1105
24d: 71        ld   (hl),c
24e: bc        cp   h
24f: b4        or   h
250: 04        inc  b
251: d9        exx
252: 05        dec  b
253: 93        sub  e
254: 41        ld   b,c
255: bc        cp   h
256: f4 64 26  call p,$2664
259: 33        inc  sp
25a: 26 a4     ld   h,$A4
25c: 08        ex   af,af'
25d: 5b        ld   e,e
25e: 05        dec  b
25f: 71        ld   (hl),c
260: 20 01     jr   nz,$0263
262: c3 53 bc  jp   $BC53
265: f4 6a ac  call p,$AC6A
268: 41        ld   b,c
269: 11 26 11  ld   de,$1126
26c: e4 bc 02  call po,$02BC
26f: b1        or   c
270: 26 f1     ld   h,$F1
272: af        xor  a
273: 0f        rrca
274: 05        dec  b
275: e4 56 c3  call po,$C356
278: 95        sub  l
279: 07        rlca
27a: e4 ab 26  call po,$26AB
27d: f1        pop  af
27e: 07        rlca
27f: b8        cp   b
280: 07        rlca
281: e9        jp   (hl)
282: 93        sub  e
283: ff        rst  $38
284: f1        pop  af
285: fb        ei
286: 95        sub  l
287: 56        ld   d,(hl)
288: 0f        rrca
289: 06 b8     ld   b,$B8
28b: f1        pop  af
28c: 47        ld   b,a
28d: fd        db   $fd
28e: 07        rlca
28f: e9        jp   (hl)
290: ff        rst  $38
291: 97        sub  a
292: 8b        adc  a,e
293: 8b        adc  a,e
294: b2        or   d
295: 71        ld   (hl),c
296: 71        ld   (hl),c
297: bc        cp   h
298: 27        daa
299: 72        ld   (hl),d
29a: b4        or   h
29b: 41        ld   b,c
29c: f4 a0 0f  call p,$0FA0
29f: d2 b4 41  jp   nc,$41B4
2a2: ff        rst  $38
2a3: 96        sub  (hl)
2a4: b4        or   h
2a5: d2 a6 c3  jp   nc,$C3A6
2a8: c0        ret  nz
2a9: 03        inc  bc
2aa: 04        inc  b
2ab: e4 f1 d6  call po,$D6F1
2ae: 93        sub  e
2af: b4        or   h
2b0: ff        rst  $38
2b1: 11 fd bc  ld   de,$BCFD
2b4: 27        daa
2b5: b1        or   c
2b6: 32 91 bb  ld   ($BB91),a
2b9: 12        ld   (de),a
2ba: 91        sub  c
2bb: 71        ld   (hl),c
2bc: fd        db   $fd
2bd: c0        ret  nz
2be: 61        ld   h,c
2bf: be        cp   (hl)
2c0: f1        pop  af
2c1: d6 93     sub  $93
2c3: b4        or   h
2c4: 03        inc  bc
2c5: 04        inc  b
2c6: ca ff 91  jp   z,$91FF
2c9: 26 f1     ld   h,$F1
2cb: d6 e0     sub  $E0
2cd: 06 e4     ld   b,$E4
2cf: 05        dec  b
2d0: c3 f1 d6  jp   $D6F1
2d3: 93        sub  e
2d4: e4 03 02  call po,$0203
2d7: e4 b4 71  call po,$71B4
2da: 27        daa
2db: 06 ff     ld   b,$FF
2dd: b6        or   (hl)
2de: b8        cp   b
2df: f1        pop  af
2e0: e9        jp   (hl)
2e1: 06 e4     ld   b,$E4
2e3: 07        rlca
2e4: 26 f1     ld   h,$F1
2e6: 56        ld   d,(hl)
2e7: 06 ea     ld   b,$EA
2e9: f1        pop  af
2ea: f8        ret  m
2eb: f9        ld   sp,hl
2ec: b6        or   (hl)
2ed: f3        di
2ee: fa fb f2  jp   m,$F2FB
2f1: e1        pop  hl
2f2: 81        add  a,c
2f3: 61        ld   h,c
2f4: f2 fa 0f  jp   p,$0FFA
2f7: 00        nop
2f8: 61        ld   h,c
2f9: c1        pop  bc
2fa: 61        ld   h,c
2fb: e1        pop  hl
2fc: 4e        ld   c,(hl)
2fd: 4c        ld   c,h
2fe: 6b        ld   l,e
2ff: 25        dec  h
300: 26 d1     ld   h,$D1
302: aa        xor  d
303: 38 02     jr   c,$0307
305: df        rst  $18
306: be        cp   (hl)
307: bd        cp   l
308: 05        dec  b
309: 9d        sbc  a,l
30a: 38 2b     jr   c,$0337
30c: d1        pop  de
30d: b8        cp   b
30e: bc        cp   h
30f: be        cp   (hl)
310: 06 24     ld   b,$24
312: 07        rlca
313: 2b        dec  hl
314: b9        cp   c
315: bd        cp   l
316: bb        cp   e
317: 85        add  a,l
318: f1        pop  af
319: bc        cp   h
31a: b4        or   h
31b: 21 71 27  ld   hl,$2771
31e: 82        add  a,d
31f: ba        cp   d
320: 26 d1     ld   h,$D1
322: aa        xor  d
323: 39        add  hl,sp
324: 06 df     ld   b,$DF
326: be        cp   (hl)
327: bd        cp   l
328: 05        dec  b
329: 9d        sbc  a,l
32a: 38 01     jr   c,$032D
32c: d1        pop  de
32d: bc        cp   h
32e: bf        cp   a
32f: f4 06 57  call p,$5706
332: e3        ex   (sp),hl
333: 1c        inc  e
334: 08        ex   af,af'
335: a4        and  h
336: 3b        dec  sp
337: f4 16 57  call p,$5716
33a: ef        rst  $28
33b: fb        ei
33c: 00        nop
33d: a4        and  h
33e: 31 ba 39  ld   sp,$39BA
341: bd        cp   l
342: d1        pop  de
343: 26 ae     ld   h,$AE
345: 05        dec  b
346: b5        or   l
347: 06 d1     ld   b,$D1
349: 96        sub  (hl)
34a: 06 df     ld   b,$DF
34c: fd 26 d1  ld   iyh,$D1
34f: aa        xor  d
350: be        cp   (hl)
351: bd        cp   l
352: d1        pop  de
353: b8        cp   b
354: 39        add  hl,sp
355: 05        dec  b
356: 9d        sbc  a,l
357: 39        add  hl,sp
358: bc        cp   h
359: be        cp   (hl)
35a: b9        cp   c
35b: bd        cp   l
35c: 2b        dec  hl
35d: 02        ld   (bc),a
35e: 22 07 bb  ld   ($BB07),hl
361: 85        add  a,l
362: 8c        adc  a,h
363: 27        daa
364: 2b        dec  hl
365: f1        pop  af
366: bc        cp   h
367: b4        or   h
368: 3e ba     ld   a,$BA
36a: a6        and  (hl)
36b: 26 21     ld   h,$21
36d: ff        rst  $38
36e: 96        sub  (hl)
36f: 05        dec  b
370: d1        pop  de
371: aa        xor  d
372: 39        add  hl,sp
373: 01 df be  ld   bc,$BEDF
376: bd        cp   l
377: d1        pop  de
378: 9d        sbc  a,l
379: 39        add  hl,sp
37a: 2b        dec  hl
37b: 02        ld   (bc),a
37c: b8        cp   b
37d: bc        cp   h
37e: be        cp   (hl)
37f: b9        cp   c
380: 20 07     jr   nz,$0389
382: 2b        dec  hl
383: f1        pop  af
384: bd        cp   l
385: bb        cp   e
386: 85        add  a,l
387: 71        ld   (hl),c
388: bc        cp   h
389: b4        or   h
38a: 21 27 27  ld   hl,$2727
38d: 87        add  a,a
38e: ba        cp   d
38f: 17        rla
390: d1        pop  de
391: aa        xor  d
392: 39        add  hl,sp
393: 05        dec  b
394: df        rst  $18
395: be        cp   (hl)
396: bd        cp   l
397: d1        pop  de
398: 9d        sbc  a,l
399: 3d        dec  a
39a: 38 06     jr   c,$03A2
39c: b8        cp   b
39d: bc        cp   h
39e: bd        cp   l
39f: 97        sub  a
3a0: d1        pop  de
3a1: d1        pop  de
3a2: d1        pop  de
3a3: fb        ei
3a4: a9        xor  c
3a5: 93        sub  e
3a6: 93        sub  e
3a7: ba        cp   d
3a8: 39        add  hl,sp
3a9: bd        cp   l
3aa: d1        pop  de
3ab: 27        daa
3ac: ae        xor  (hl)
3ad: 05        dec  b
3ae: b5        or   l
3af: 17        rla
3b0: d1        pop  de
3b1: 96        sub  (hl)
3b2: f1        pop  af
3b3: 07        rlca
3b4: fd        db   $fd
3b5: 27        daa
3b6: e4 b8 00  call po,$00B8
3b9: e9        jp   (hl)
3ba: 3f        ccf
3bb: 3d        dec  a
3bc: f1        pop  af
3bd: be        cp   (hl)
3be: b9        cp   c
3bf: d1        pop  de
3c0: c2 06 3d  jp   nz,$3D06
3c3: 3d        dec  a
3c4: b9        cp   c
3c5: b8        cp   b
3c6: bc        cp   h
3c7: bd        cp   l
3c8: 06 d1     ld   b,$D1
3ca: e9        jp   (hl)
3cb: bc        cp   h
3cc: 97        sub  a
3cd: a9        xor  c
3ce: c6 27     add  a,$27
3d0: f4 b4 db  call p,$DBB4
3d3: d6 d6     sub  $D6
3d5: c3 f4 0f  jp   $0FF4
3d8: c3 bc b4  jp   $B4BC
3db: 96        sub  (hl)
3dc: db 27     in   a,($27)
3de: 00        nop
3df: 26 05     ld   h,$05
3e1: e4 db 3e  call po,$3EDB
3e4: f1        pop  af
3e5: d2 be b9  jp   nc,$B9BE
3e8: 3c        inc  a
3e9: c2 38 a4  jp   nz,$A438
3ec: d1        pop  de
3ed: bc        cp   h
3ee: 27        daa
3ef: 1c        inc  e
3f0: bf        cp   a
3f1: f4 a4 ef  call p,$EFA4
3f4: 06 47     ld   b,$47
3f6: 1c        inc  e
3f7: f2 27 cc  jp   p,$CC27
3fa: 3a 34 a4  ld   a,($A434)
3fd: b8        cp   b
3fe: f0        ret  p
3ff: c8        ret  z
400: cc 34 17  call z,$1734
403: df        rst  $18
404: f0        ret  p
405: 27        daa
406: d1        pop  de
407: ba        cp   d
408: 39        add  hl,sp
409: bd        cp   l
40a: d1        pop  de
40b: 96        sub  (hl)
40c: ae        xor  (hl)
40d: 05        dec  b
40e: b5        or   l
40f: be        cp   (hl)
410: 3e 3c     ld   a,$3C
412: c2 3c b9  jp   nz,$B93C
415: d1        pop  de
416: bc        cp   h
417: f4 85 19  call p,$1985
41a: b8        cp   b
41b: bc        cp   h
41c: c3 95 3e  jp   $3E95
41f: 2b        dec  hl
420: be        cp   (hl)
421: bd        cp   l
422: b3        or   e
423: ce 06     adc  a,$06
425: 06 28     ld   b,$28
427: ce b9     adc  a,$B9
429: bb        cp   e
42a: 85        add  a,l
42b: 8c        adc  a,h
42c: 2c        inc  l
42d: 2b        dec  hl
42e: f1        pop  af
42f: 27        daa
430: 17        rla
431: df        rst  $18
432: be        cp   (hl)
433: bd        cp   l
434: d1        pop  de
435: aa        xor  d
436: 39        add  hl,sp
437: 05        dec  b
438: d1        pop  de
439: b8        cp   b
43a: bc        cp   h
43b: be        cp   (hl)
43c: 9d        sbc  a,l
43d: 39        add  hl,sp
43e: 2e 06     ld   l,$06
440: b9        cp   c
441: bd        cp   l
442: bb        cp   e
443: 85        add  a,l
444: 21 01 2e  ld   hl,$2E01
447: f1        pop  af
448: 8c        adc  a,h
449: 28 01     jr   z,$044C
44b: 56        ld   d,(hl)
44c: bc        cp   h
44d: bf        cp   a
44e: f4 0f c3  call p,$C30F
451: d6 93     sub  $93
453: 1c        inc  e
454: 53        ld   d,e
455: 0f        rrca
456: 62        ld   h,d
457: ef        rst  $28
458: 4d        ld   c,l
459: 28 01     jr   z,$045C
45b: 0f        rrca
45c: bc        cp   h
45d: bf        cp   a
45e: b4        or   h
45f: 1c        inc  e
460: ef        rst  $28
461: 21 27 d1  ld   hl,$D127
464: 5d        ld   e,l
465: ba        cp   d
466: 17        rla
467: df        rst  $18
468: aa        xor  d
469: 39        add  hl,sp
46a: 01 9d be  ld   bc,$BE9D
46d: bd        cp   l
46e: d1        pop  de
46f: bc        cp   h
470: 3c        inc  a
471: 56        ld   d,(hl)
472: a4        and  h
473: 02        ld   (bc),a
474: f4 f0 26  call p,$26F0
477: d1        pop  de
478: df        rst  $18
479: be        cp   (hl)
47a: bd        cp   l
47b: d1        pop  de
47c: aa        xor  d
47d: 38 05     jr   c,$0484
47f: 9d        sbc  a,l
480: b8        cp   b
481: bc        cp   h
482: bd        cp   l
483: 97        sub  a
484: 3c        inc  a
485: 31 01 d1  ld   sp,$D101
488: a9        xor  c
489: 93        sub  e
48a: ba        cp   d
48b: ae        xor  (hl)
48c: d1        pop  de
48d: fb        ei
48e: 38 bd     jr   c,$044D
490: 05        dec  b
491: b5        or   l
492: 02        ld   (bc),a
493: fd        db   $fd
494: d1        pop  de
495: 26 d1     ld   h,$D1
497: 26 05     ld   h,$05
499: df        rst  $18
49a: be        cp   (hl)
49b: bd        cp   l
49c: d1        pop  de
49d: aa        xor  d
49e: 39        add  hl,sp
49f: 01 d1 bc  ld   bc,$BCD1
4a2: bf        cp   a
4a3: 97        sub  a
4a4: 9d        sbc  a,l
4a5: 38 01     jr   c,$04A8
4a7: a7        and  a
4a8: 1c        inc  e
4a9: 16 57     ld   d,$57
4ab: e3        ex   (sp),hl
4ac: f4 00 a4  call p,$A400
4af: b2        or   d
4b0: ef        rst  $28
4b1: fb        ei
4b2: 39        add  hl,sp
4b3: bd        cp   l
4b4: a8        xor  b
4b5: ba        cp   d
4b6: ae        xor  (hl)
4b7: 01 d1 26  ld   bc,$26D1
4ba: d1        pop  de
4bb: be        cp   (hl)
4bc: b5        or   l
4bd: 05        dec  b
4be: fd        db   $fd
4bf: 3c        inc  a
4c0: b9        cp   c
4c1: fe 27     cp   $27
4c3: e9        jp   (hl)
4c4: 0a        ld   a,(bc)
4c5: a8        xor  b
4c6: f1        pop  af
4c7: ce e9     adc  a,$E9
4c9: 71        ld   (hl),c
4ca: 26 f1     ld   h,$F1
4cc: c2 da 0e  jp   nz,$0EDA
4cf: e4 07 d8  call po,$D807
4d2: f1        pop  af
4d3: ec 93 ac  call pe,$AC93
4d6: f1        pop  af
4d7: d1        pop  de
4d8: b8        cp   b
4d9: f1        pop  af
4da: 96        sub  (hl)
4db: a6        and  (hl)
4dc: 0e e9     ld   c,$E9
4de: ff        rst  $38
4df: 96        sub  (hl)
4e0: 26 f1     ld   h,$F1
4e2: 17        rla
4e3: d6 06     sub  $06
4e5: e4 af 03  call po,$03AF
4e8: 93        sub  e
4e9: 71        ld   (hl),c
4ea: 27        daa
4eb: f0        ret  p
4ec: ef        rst  $28
4ed: da 81 ff  jp   c,$FF81
4f0: b8        cp   b
4f1: f1        pop  af
4f2: 96        sub  (hl)
4f3: f1        pop  af
4f4: 06 e9     ld   b,$E9
4f6: 53        ld   d,e
4f7: 11 d6 f1  ld   de,$F1D6
4fa: 01 e4 c3  ld   bc,$C3E4
4fd: 26 f1     ld   h,$F1
4ff: 07        rlca
500: c3 b8 f1  jp   $F1B8
503: 96        sub  (hl)
504: 07        rlca
505: 01 e9 f1  ld   bc,$F1E9
508: c8        ret  z
509: 27        daa
50a: b4        or   h
50b: 72        ld   (hl),d
50c: bc        cp   h
50d: f4 10 12  call p,$1210
510: b4        or   h
511: 11 71 96  ld   de,$9671
514: 08        ex   af,af'
515: bc        cp   h
516: 8b        adc  a,e
517: 11 d6 23  ld   de,$23D6
51a: 03        inc  bc
51b: e4 c3 26  call po,$26C3
51e: f1        pop  af
51f: 07        rlca
520: c3 b8 f1  jp   $F1B8
523: 96        sub  (hl)
524: 27        daa
525: 03        inc  bc
526: e9        jp   (hl)
527: 26 01     ld   h,$01
529: df        rst  $18
52a: be        cp   (hl)
52b: bd        cp   l
52c: d1        pop  de
52d: aa        xor  d
52e: 39        add  hl,sp
52f: 01 d1 bc  ld   bc,$BCD1
532: bf        cp   a
533: 97        sub  a
534: 9d        sbc  a,l
535: 38 01     jr   c,$0538
537: a7        and  a
538: 1c        inc  e
539: 16 57     ld   d,$57
53b: e3        ex   (sp),hl
53c: f4 00 a4  call p,$A400
53f: 42        ld   b,d
540: ef        rst  $28
541: fb        ei
542: 39        add  hl,sp
543: bd        cp   l
544: 38 ba     jr   c,$0500
546: ae        xor  (hl)
547: 01 d1 26  ld   bc,$26D1
54a: d1        pop  de
54b: 26 b5     ld   h,$B5
54d: 01 fd 48  ld   bc,$48FD
550: a1        and  c
551: bc        cp   h
552: f4 82 22  call p,$2282
555: 02        ld   (bc),a
556: d2 d6 40  jp   nc,$40D6
559: 27        daa
55a: e4 39 a4  call po,$A439
55d: f1        pop  af
55e: ba        cp   d
55f: 12        ld   (de),a
560: 66        ld   h,(hl)
561: 3f        ccf
562: 39        add  hl,sp
563: 06 ba     ld   b,$BA
565: be        cp   (hl)
566: bd        cp   l
567: d1        pop  de
568: 9d        sbc  a,l
569: 39        add  hl,sp
56a: 56        ld   d,(hl)
56b: a4        and  h
56c: bc        cp   h
56d: f4 0f b8  call p,$B80F
570: 39        add  hl,sp
571: 3c        inc  a
572: 06 a4     ld   b,$A4
574: bc        cp   h
575: bf        cp   a
576: f0        ret  p
577: c8        ret  z
578: cc 75 31  call z,$3175
57b: 3a ef bc  ld   a,($BCEF)
57e: b4        or   h
57f: 1c        inc  e
580: b4        or   h
581: bc        cp   h
582: f4 95 05  call p,$0595
585: 32 12 b1  ld   ($B112),a
588: 8e        adc  a,(hl)
589: ce 31     adc  a,$31
58b: ac        xor  h
58c: a1        and  c
58d: bc        cp   h
58e: f4 06 fd  call p,$FD06
591: f0        ret  p
592: 96        sub  (hl)
593: 03        inc  bc
594: a8        xor  b
595: a4        and  h
596: f1        pop  af
597: d6 04     sub  $04
599: 93        sub  e
59a: 95        sub  l
59b: c8        ret  z
59c: 85        add  a,l
59d: 9f        sbc  a,a
59e: f1        pop  af
59f: 95        sub  l
5a0: bc        cp   h
5a1: f4 b3 07  call p,$07B3
5a4: 35        dec  (hl)
5a5: af        xor  a
5a6: bc        cp   h
5a7: 93        sub  e
5a8: ae        xor  (hl)
5a9: f5        push af
5aa: 37        scf
5ab: ce a1     adc  a,$A1
5ad: a4        and  h
5ae: 12        ld   (de),a
5af: b1        or   c
5b0: 8e        adc  a,(hl)
5b1: 31 a1 ff  ld   sp,$FFA1
5b4: bc        cp   h
5b5: 14        inc  d
5b6: ce a6     adc  a,$A6
5b8: 96        sub  (hl)
5b9: 31 a8 f4  ld   sp,$F4A8
5bc: bc        cp   h
5bd: f4 ac 2f  call p,$2FAC
5c0: 12        ld   (de),a
5c1: 2f        cpl
5c2: f0        ret  p
5c3: ca c7 46  jp   z,$46C7
5c6: a1        and  c
5c7: 2f        cpl
5c8: 46        ld   b,(hl)
5c9: a0        and  b
5ca: 03        inc  bc
5cb: 06 0f     ld   b,$0F
5cd: f1        pop  af
5ce: d6 93     sub  $93
5d0: b8        cp   b
5d1: c8        ret  z
5d2: b4        or   h
5d3: cc f1 cc  call z,$CCF1
5d6: fb        ei
5d7: b4        or   h
5d8: ff        rst  $38
5d9: 31 06 a8  ld   sp,$A806
5dc: bc        cp   h
5dd: f4 fd ac  call p,$ACFD
5e0: f4 bc f4  call p,$F4BC
5e3: ed        db   $ed
5e4: af        xor  a
5e5: 35        dec  (hl)
5e6: 12        ld   (de),a
5e7: ff        rst  $38
5e8: 06 57     ld   b,$57
5ea: 96        sub  (hl)
5eb: 47        ld   b,a
5ec: 0a        ld   a,(bc)
5ed: a0        and  b
5ee: ff        rst  $38
5ef: 06 0a     ld   b,$0A
5f1: 47        ld   b,a
5f2: 96        sub  (hl)
5f3: 02        ld   (bc),a
5f4: 57        ld   d,a
5f5: a0        and  b
5f6: bc        cp   h
5f7: f4 56 a4  call p,$A456
5fa: f1        pop  af
5fb: 46        ld   b,(hl)
5fc: 9f        sbc  a,a
5fd: 27        daa
5fe: e4 02 ad  call po,$AD02
601: 00        nop
602: e9        jp   (hl)
603: 39        add  hl,sp
604: b8        cp   b
605: f1        pop  af
606: be        cp   (hl)
607: fd        db   $fd
608: 12        ld   (de),a
609: be        cp   (hl)
60a: ba        cp   d
60b: bd        cp   l
60c: 09        add  hl,bc
60d: 3f        ccf
60e: 3c        inc  a
60f: 06 d1     ld   b,$D1
611: 71        ld   (hl),c
612: 96        sub  (hl)
613: 39        add  hl,sp
614: b5        or   l
615: be        cp   (hl)
616: b8        cp   b
617: bc        cp   h
618: 2b        dec  hl
619: 04        inc  b
61a: 27        daa
61b: 06 be     ld   b,$BE
61d: b9        cp   c
61e: bd        cp   l
61f: bb        cp   e
620: 2e f1     ld   l,$F1
622: b8        cp   b
623: bc        cp   h
624: 85        add  a,l
625: 8c        adc  a,h
626: 3a 2c be  ld   a,($BE2C)
629: b9        cp   c
62a: bd        cp   l
62b: bb        cp   e
62c: 04        inc  b
62d: 28 02     jr   z,$0631
62f: 2a 85 71  ld   hl,($7185)
632: 2e 0f     ld   l,$0F
634: f1        pop  af
635: bc        cp   h
636: b4        or   h
637: cc b4 bc  call z,$BCB4
63a: b8        cp   b
63b: f0        ret  p
63c: 1f        rra
63d: 27        daa
63e: 32 bf 00  ld   ($00BF),a
641: 45        ld   b,l
642: 2f        cpl
643: a4        and  h
644: 12        ld   (de),a
645: bf        cp   a
646: ff        rst  $38
647: 21 ba 01  ld   hl,$01BA
64a: df        rst  $18
64b: be        cp   (hl)
64c: 26 d1     ld   h,$D1
64e: aa        xor  d
64f: 39        add  hl,sp
650: bd        cp   l
651: d1        pop  de
652: b8        cp   b
653: bc        cp   h
654: 01 9d 39  ld   bc,$399D
657: 2b        dec  hl
658: be        cp   (hl)
659: b9        cp   c
65a: bd        cp   l
65b: bb        cp   e
65c: 04        inc  b
65d: 26 07     ld   h,$07
65f: 2b        dec  hl
660: 85        add  a,l
661: 8c        adc  a,h
662: 27        daa
663: 9e        sbc  a,(hl)
664: f1        pop  af
665: bc        cp   h
666: b4        or   h
667: 21 ba 84  ld   hl,$84BA
66a: 3a ff 83  ld   a,($83FF)
66d: 84        add  a,h
66e: ff        rst  $38
66f: ff        rst  $38
670: 39        add  hl,sp
671: 84        add  a,h
672: 3a ff b9  ld   a,($B9FF)
675: 8c        adc  a,h
676: ff        rst  $38
677: ff        rst  $38
678: 39        add  hl,sp
679: 29        add  hl,hl
67a: 9c        sbc  a,h
67b: 39        add  hl,sp
67c: 9c        sbc  a,h
67d: b5        or   l
67e: ff        rst  $38
67f: ab        xor  e
680: ff        rst  $38
681: fa 6c bc  jp   m,$BC6C
684: e1        pop  hl
685: 06 a8     ld   b,$A8
687: 27        daa
688: bf        cp   a
689: f8        ret  m
68a: 17        rla
68b: c8        ret  z
68c: 08        ex   af,af'
68d: a6        and  (hl)
68e: a4        and  h
68f: cc ef 96  call z,$96EF
692: a6        and  (hl)
693: f4 8a ff  call p,$FF8A
696: 96        sub  (hl)
697: 16 00     ld   d,$00
699: a4        and  h
69a: 86        add  a,(hl)
69b: f1        pop  af
69c: 57        ld   d,a
69d: 1c        inc  e
69e: fa e4 06  jp   m,$06E4
6a1: 57        ld   d,a
6a2: ac        xor  h
6a3: a4        and  h
6a4: 00        nop
6a5: 2e 2e     ld   l,$2E
6a7: ca ce 9d  jp   z,$9DCE
6aa: f4 57 ed  call p,$ED57
6ad: 96        sub  (hl)
6ae: 70        ld   (hl),b
6af: a4        and  h
6b0: 18 ed     jr   $069F
6b2: 86        add  a,(hl)
6b3: ac        xor  h
6b4: 1c        inc  e
6b5: a9        xor  c
6b6: fa f4 2e  jp   m,$2EF4
6b9: 2e e9     ld   l,$E9
6bb: ce a8     adc  a,$A8
6bd: f1        pop  af
6be: ca ed b5  jp   z,$B5ED
6c1: 27        daa
6c2: e4 32 96  call po,$9632
6c5: f1        pop  af
6c6: 85        add  a,l
6c7: cc 95 39  call z,$3995
6ca: cf        rst  $08
6cb: 3f        ccf
6cc: ba        cp   d
6cd: 12        ld   (de),a
6ce: ba        cp   d
6cf: bd        cp   l
6d0: 06 9d     ld   b,$9D
6d2: d3 f9     out  ($F9),a
6d4: d1        pop  de
6d5: b3        or   e
6d6: 96        sub  (hl)
6d7: a8        xor  b
6d8: ac        xor  h
6d9: 06 d1     ld   b,$D1
6db: 96        sub  (hl)
6dc: bd        cp   l
6dd: 97        sub  a
6de: a9        xor  c
6df: ab        xor  e
6e0: e7        rst  $20
6e1: d1        pop  de
6e2: 59        ld   e,c
6e3: ec ad f2  call pe,$F2AD
6e6: c3 27 17  jp   $1727
6e9: d6 f1     sub  $F1
6eb: 2b        dec  hl
6ec: ab        xor  e
6ed: 04        inc  b
6ee: 20 f1     jr   nz,$06E1
6f0: 20 27     jr   nz,$0719
6f2: f1        pop  af
6f3: a9        xor  c
6f4: 96        sub  (hl)
6f5: 17        rla
6f6: e4 26 80  call po,$8026
6f9: eb        ex   de,hl
6fa: 96        sub  (hl)
6fb: d1        pop  de
6fc: e7        rst  $20
6fd: fc ab f2  call m,$F2AB
700: d9        exx
701: 04        inc  b
702: e9        jp   (hl)
703: bc        cp   h
704: b8        cp   b
705: f1        pop  af
706: 96        sub  (hl)
707: 36 f4     ld   (hl),$F4
709: 6f        ld   l,a
70a: f1        pop  af
70b: 12        ld   (de),a
70c: 96        sub  (hl)
70d: af        xor  a
70e: dc 0a 52  call c,$520A
711: ff        rst  $38
712: 3c        inc  a
713: 2f        cpl
714: 0a        ld   a,(bc)
715: 96        sub  (hl)
716: 31 2a 25  ld   sp,$252A
719: 1e 16     ld   e,$16
71b: e1        pop  hl
71c: 20 17     jr   nz,$0735
71e: 0f        rrca
71f: fa 6d 12  jp   m,$126D
722: 96        sub  (hl)
723: 05        dec  b
724: 06 a6     ld   b,$A6
726: 26 f1     ld   h,$F1
728: e4 00 b8  call po,$B800
72b: b0        or   b
72c: 06 57     ld   b,$57
72e: 39        add  hl,sp
72f: 00        nop
730: c8        ret  z
731: c8        ret  z
732: 31 bc a0  ld   sp,$A0BC
735: b0        or   b
736: c8        ret  z
737: 1d        dec  e
738: 11 06 57  ld   de,$5706
73b: 42        ld   b,d
73c: b0        or   b
73d: 06 33     ld   b,$33
73f: 06 50     ld   b,$50
741: a0        and  b
742: 39        add  hl,sp
743: 2b        dec  hl
744: 57        ld   d,a
745: b8        cp   b
746: bc        cp   h
747: be        cp   (hl)
748: 04        inc  b
749: 27        daa
74a: 07        rlca
74b: 2b        dec  hl
74c: b9        cp   c
74d: bd        cp   l
74e: bb        cp   e
74f: 85        add  a,l
750: f1        pop  af
751: bc        cp   h
752: b4        or   h
753: f1        pop  af
754: 8c        adc  a,h
755: 27        daa
756: af        xor  a
757: 03        inc  bc
758: d6 93     sub  $93
75a: bc        cp   h
75b: 11 06 61  ld   de,$6106
75e: 1d        dec  e
75f: b0        or   b
760: 17        rla
761: f1        pop  af
762: f1        pop  af
763: d6 94     sub  $94
765: c8        ret  z
766: 03        inc  bc
767: 02        ld   (bc),a
768: 93        sub  e
769: b8        cp   b
76a: 80        add  a,b
76b: 3f        ccf
76c: 72        ld   (hl),d
76d: 2e 17     ld   l,$17
76f: 90        sub  b
770: f1        pop  af
771: 21 19 56  ld   hl,$5619
774: c8        ret  z
775: ba        cp   d
776: f0        ret  p
777: f0        ret  p
778: b3        or   e
779: ee 95     xor  $95
77b: 82        add  a,d
77c: 82        add  a,d
77d: 7f        ld   a,a
77e: e1        pop  hl
77f: c3 8c 47  jp   $478C
782: ed        db   $ed
783: e1        pop  hl
784: 95        sub  l
785: a4        and  h
786: 88        adc  a,b
787: a0        and  b
788: cc f0 0f  call z,$0FF0
78b: 97        sub  a
78c: 19        add  hl,de
78d: 56        ld   d,(hl)
78e: b3        or   e
78f: ee 91     xor  $91
791: e1        pop  hl
792: c3 95 95  jp   $9595
795: 97        sub  a
796: 9d        sbc  a,l
797: a4        and  h
798: ed        db   $ed
799: e1        pop  hl
79a: cc e1 99  call z,$99E1
79d: a0        and  b
79e: c8        ret  z
79f: 71        ld   (hl),c
7a0: fb        ei
7a1: f4 a9 0f  call p,$0FA9
7a4: ac        xor  h
7a5: 93        sub  e
7a6: b4        or   h
7a7: fb        ei
7a8: cb 93     res  2,e
7aa: 27        daa
7ab: f9        ld   sp,hl
7ac: d9        exx
7ad: a0        and  b
7ae: af        xor  a
7af: d6 28     sub  $28
7b1: b1        or   c
7b2: f9        ld   sp,hl
7b3: 29        add  hl,hl
7b4: 93        sub  e
7b5: 1f        rra
7b6: d6 93     sub  $93
7b8: ba        cp   d
7b9: ff        rst  $38
7ba: c6 ac     add  a,$AC
7bc: 1f        rra
7bd: 93        sub  e
7be: f9        ld   sp,hl
7bf: f4 06 a4  call p,$A406
7c2: a7        and  a
7c3: fa 10 11  jp   m,$1110
7c6: 93        sub  e
7c7: 96        sub  (hl)
7c8: bc        cp   h
7c9: b4        or   h
7ca: 96        sub  (hl)
7cb: a6        and  (hl)
7cc: 36 ff     ld   (hl),$FF
7ce: ff        rst  $38
7cf: 96        sub  (hl)
7d0: f2 d2 e7  jp   p,$E7D2
7d3: e7        rst  $20
7d4: fa fa 17  jp   m,$17FA
7d7: ac        xor  h
7d8: 86        add  a,(hl)
7d9: 03        inc  bc
7da: c3 f1 f1  jp   $F1F1
7dd: 17        rla
7de: dc c8 96  call c,$96C8
7e1: d0        ret  nc
7e2: b0        or   b
7e3: 1c        inc  e
7e4: f1        pop  af
7e5: 11 a8 11  ld   de,$11A8
7e8: b0        or   b
7e9: 68        ld   l,b
7ea: 28 d0     jr   z,$07BC
7ec: 47        ld   b,a
7ed: 86        add  a,(hl)
7ee: f1        pop  af
7ef: f8        ret  m
7f0: 3f        ccf
7f1: 1c        inc  e
7f2: 3f        ccf
7f3: 86        add  a,(hl)
7f4: 94        sub  h
7f5: 47        ld   b,a
7f6: 94        sub  h
7f7: 71        ld   (hl),c
7f8: 9d        sbc  a,l
7f9: 26 3a     ld   h,$3A
7fb: e8        ret  pe
7fc: 94        sub  h
7fd: 4f        ld   c,a
7fe: 01 ff ff  ld   bc,$00FF
