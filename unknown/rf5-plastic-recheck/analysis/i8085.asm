000: ff        rst  7
001: d5        push d
002: 9e        sbb  m
003: b4        ora  h
004: 21 01 fb  lxi  h,$fb01
007: c5        push b
008: bc        cmp  h
009: a4        ana  h
00a: 56        mov  d,m
00b: c3 30 fb  jmp  $fb30
00e: f8        rm
00f: 12        stax d
010: e1        pop  h
011: 26 62     mvi  h,$62
013: 6f        mov  l,a
014: fa e4 26  jm   $26e4
017: 3a 8c 0c  lda  $0c8c
01a: 26 3a     mvi  h,$3a
01c: ff        rst  7
01d: ae        xra  m
01e: 5f        mov  e,a
01f: b8        cmp  b
020: 2e 12     mvi  l,$12
022: c8        rz
023: 17        ral
024: 80        add  b
025: 2e 80     mvi  l,$80
027: 3f        cmc
028: 90        sub  b
029: 44        mov  b,h
02a: f2 fb 52  jp   $52fb
02d: fa 44 06  jm   $0644
030: 1f        rar
031: 06 ac     mvi  b,$ac
033: 3c        inr  a
034: a8        xra  b
035: 01 f4 8a  lxi  b,$8af4
038: df        rst  3
039: 5f        mov  e,a
03a: 3c        inr  a
03b: 07        rlc
03c: 9a        sbb  d
03d: f0        rp
03e: fb        ei
03f: 47        mov  b,a
040: 3a 77 01  lda  $0177
043: 48        mov  c,b
044: eb        xchg
045: bb        cmp  e
046: 83        add  e
047: 05        dcr  b
048: 85        add  l
049: fe 06     cpi  $06
04b: 5e        mov  e,m
04c: 95        sub  l
04d: bc        cmp  h
04e: 52        mov  d,d
04f: b3        ora  e
050: 57        mov  d,a
051: 46        mov  b,m
052: aa        xra  d
053: 72        mov  m,d
054: fa 80 01  jm   $0180
057: 95        sub  l
058: 2e 2e     mvi  l,$2e
05a: 77        mov  m,a
05b: 4d        mov  c,l
05c: fc 77 ec  cm   $ec77
05f: fa 56 aa  jm   $aa56
062: 71        mov  m,c
063: 72        mov  m,d
064: 7f        mov  a,a
065: b3        ora  e
066: ef        rst  5
067: fe bc     cpi  $bc
069: 53        mov  d,e
06a: d6 c3     sui  $c3
06c: 36 74     mvi  m,$74
06e: 04        inr  b
06f: 74        mov  m,h
070: fe bf     cpi  $bf
072: ef        rst  5
073: 1f        rar
074: a4        ana  h
075: 07        rlc
076: 77        mov  m,a
077: bc        cmp  h
078: 34        inr  m
079: 07        rlc
07a: 93        sub  e
07b: 26 f4     mvi  h,$f4
07d: a4        ana  h
07e: 87        add  a
07f: 95        sub  l
080: a4        ana  h
081: 14        inr  d
082: 46        mov  b,m
083: aa        xra  d
084: 1c        inr  e
085: fa 08 bc  jm   $bc08
088: 2f        cma
089: 07        rlc
08a: 8f        adc  a
08b: 95        sub  l
08c: f4 c3 01  cp   $01c3
08f: fa 46 aa  jm   $aa46
092: 8f        adc  a
093: bc        cmp  h
094: 10        arhl (*)
095: 26 a4     mvi  h,$a4
097: 30        sim
098: f4 96 15  cp   $1596
09b: cd 3f c5  call $c53f
09e: c9        ret
09f: 3f        cmc
0a0: 96        sub  m
0a1: ae        xra  m
0a2: ff        rst  7
0a3: 96        sub  m
0a4: 6e        mov  l,m
0a5: 96        sub  m
0a6: a6        ana  m
0a7: 26 0c     mvi  h,$0c
0a9: e4 0f 03  cpo  $030f
0ac: f1        pop  psw
0ad: 56        mov  d,m
0ae: d6 86     sui  $86
0b0: 84        add  h
0b1: 0f        rrc
0b2: b8        cmp  b
0b3: f1        pop  psw
0b4: 56        mov  d,m
0b5: 86        add  m
0b6: 02        stax b
0b7: e9        pchl
0b8: 96        sub  m
0b9: 08        dsub (*)
0ba: bf        cmp  a
0bb: 05        dcr  b
0bc: 26 33     mvi  h,$33
0be: 26 b8     mvi  h,$b8
0c0: 01 bc b4  lxi  b,$b4bc
0c3: bc        cmp  h
0c4: a0        ana  b
0c5: 2f        cma
0c6: 8f        adc  a
0c7: 1d        dcr  e
0c8: 11 06 b8  lxi  d,$b806
0cb: f1        pop  psw
0cc: b0        ora  b
0cd: 06 01     mvi  b,$01
0cf: e9        pchl
0d0: 96        sub  m
0d1: 4a        mov  c,d
0d2: 02        stax b
0d3: e4 21 26  cpo  $2621
0d6: f1        pop  psw
0d7: 96        sub  m
0d8: 26 bc     mvi  h,$bc
0da: a4        ana  h
0db: b4        ora  h
0dc: f8        rm
0dd: 0c        inr  c
0de: cc a7 bc  cz   $bca7
0e1: a4        ana  h
0e2: b4        ora  h
0e3: 42        mov  b,d
0e4: 17        ral
0e5: cc d4 96  cz   $96d4
0e8: 27        daa
0e9: b8        cmp  b
0ea: a0        ana  b
0eb: e9        pchl
0ec: d7        rst  2
0ed: 3f        cmc
0ee: e8        rpe
0ef: 26 01     mvi  h,$01
0f1: af        xra  a
0f2: e4 d5 ab  cpo  $abd5
0f5: 26 62     mvi  h,$62
0f7: 55        mov  d,l
0f8: 25        dcr  h
0f9: fb        ei
0fa: eb        xchg
0fb: ef        rst  5
0fc: fb        ei
0fd: fb        ei
0fe: fc fc fb  cm   $fbfc
101: 43        mov  b,e
102: 17        ral
103: 86        add  m
104: 43        mov  b,e
105: 26 d1     mvi  h,$d1
107: bf        cmp  a
108: 05        dcr  b
109: a1        ana  c
10a: 0e 27     mvi  c,$27
10c: 11 b8 ad  lxi  d,$adb8
10f: af        xra  a
110: ae        xra  m
111: e9        pchl
112: b3        ora  e
113: a4        ana  h
114: f1        pop  psw
115: b1        ora  c
116: 11 91 dd  lxi  d,$dd91
119: a4        ana  h
11a: 96        sub  m
11b: a4        ana  h
11c: 11 d1 11  lxi  d,$11d1
11f: 71        mov  m,c
120: 6e        mov  l,m
121: a4        ana  h
122: a1        ana  c
123: a4        ana  h
124: 11 11 11  lxi  d,$1111
127: 51        mov  d,c
128: a1        ana  c
129: a4        ana  h
12a: a7        ana  a
12b: a4        ana  h
12c: 11 31 11  lxi  d,$1131
12f: ef        rst  5
130: 16 cd     mvi  d,$cd
132: a4        ana  h
133: af        xra  a
134: f1        pop  psw
135: 11 2d fd  lxi  d,$fd2d
138: f1        pop  psw
139: 11 ef c3  lxi  d,$c3ef
13c: cd a4 38  call $38a4
13f: 43        mov  b,e
140: 26 d1     mvi  h,$d1
142: 21 f1 0f  lxi  h,$0ff1
145: 86        add  m
146: 07        rlc
147: c8        rz
148: 11 93 71  lxi  d,$7193
14b: 43        mov  b,e
14c: d8        rc
14d: 51        mov  d,c
14e: be        cmp  m
14f: aa        xra  d
150: f1        pop  psw
151: 21 bf ff  lxi  h,$ffbf
154: dc aa 3f  cc   $3faa
157: a8        xra  b
158: f1        pop  psw
159: ef        rst  5
15a: bf        cmp  a
15b: ff        rst  7
15c: e9        pchl
15d: 53        mov  d,e
15e: 3f        cmc
15f: d6 0a     sui  $0a
161: 6f        mov  l,a
162: f1        pop  psw
163: df        rst  3
164: c3 ff e4  jmp  $e4ff
167: c3 6f 07  jmp  $076f
16a: 86        add  m
16b: 51        mov  d,c
16c: 26 d1     mvi  h,$d1
16e: 21 ff a8  lxi  h,$a8ff
171: f1        pop  psw
172: ef        rst  5
173: 26 27     mvi  h,$27
175: e9        pchl
176: 5b        mov  e,e
177: 06 bc     mvi  b,$bc
179: 94        sub  h
17a: 3f        cmc
17b: 03        inx  b
17c: 1d        dcr  e
17d: 26 b8     mvi  h,$b8
17f: f1        pop  psw
180: e9        pchl
181: 02        stax b
182: 3e e9     mvi  a,$e9
184: 26 b8     mvi  h,$b8
186: f1        pop  psw
187: 26 06     mvi  h,$06
189: 3b        dcx  sp
18a: e9        pchl
18b: ff        rst  7
18c: b8        cmp  b
18d: f1        pop  psw
18e: 26 b8     mvi  h,$b8
190: 00        nop
191: e9        pchl
192: 15        dcr  d
193: 07        rlc
194: f1        pop  psw
195: b8        cmp  b
196: ff        rst  7
197: f1        pop  psw
198: 0a        ldax b
199: c8        rz
19a: 0a        ldax b
19b: ee a0     xri  $a0
19d: f1        pop  psw
19e: 06 a0     mvi  b,$a0
1a0: f1        pop  psw
1a1: 06 ac     mvi  b,$ac
1a3: 96        sub  m
1a4: 0a        ldax b
1a5: eb        xchg
1a6: cf        rst  1
1a7: ff        rst  7
1a8: a6        ana  m
1a9: 42        mov  b,d
1aa: c3 8c 96  jmp  $968c
1ad: 17        ral
1ae: aa        xra  d
1af: ff        rst  7
1b0: 8a        adc  d
1b1: 0c        inr  c
1b2: b8        cmp  b
1b3: f1        pop  psw
1b4: 7f        mov  a,a
1b5: 37        stc
1b6: 05        dcr  b
1b7: e9        pchl
1b8: 11 ba bc  lxi  d,$bcba
1bb: f4 bc 07  cp   $07bc
1be: 32 be 0f  sta  $0fbe
1c1: c5        push b
1c2: 1f        rar
1c3: 28 12     ldhi $12 (*)
1c5: be        cmp  m
1c6: bc        cmp  h
1c7: b8        cmp  b
1c8: 20        rim
1c9: ed        lhlx d (*)
1ca: 84        add  h
1cb: 9a        sbb  d
1cc: 21 bd 3a  lxi  h,$3abd
1cf: 83        add  e
1d0: 99        sbb  c
1d1: 8c        adc  h
1d2: 9b        sbb  e
1d3: 23        inx  h
1d4: b9        cmp  c
1d5: bb        cmp  e
1d6: bc        cmp  h
1d7: fc 21 ff  cm   $ff21
1da: c4 da e5  cnz  $e5da
1dd: fd 7a c3  jx5  $c37a (*)
1e0: d9        shlx d (*)
1e1: cc db 94  cz   $94db
1e4: f9        sphl
1e5: fb        ei
1e6: 3f        cmc
1e7: 01 e8 3f  lxi  b,$3fe8
1ea: fa 56 ff  jm   $ff56
1ed: e1        pop  h
1ee: f4 e0 c3  cp   $c3e0
1f1: e1        pop  h
1f2: f4 06 f1  cp   $f106
1f5: fa 5e ce  jm   $ce5e
1f8: a6        ana  m
1f9: a0        ana  b
1fa: 1c        inr  e
1fb: ed        lhlx d (*)
1fc: 17        ral
1fd: 18        rdel (*)
1fe: ea 26 06  jpe  $0626
201: e4 05 0c  cpo  $0c05
204: f1        pop  psw
205: d6 93     sui  $93
207: 41        mov  b,c
208: 25        dcr  h
209: d6 17     sui  $17
20b: 02        stax b
20c: 11 93 bc  lxi  d,$bc93
20f: f4 37 17  cp   $1737
212: 52        mov  d,d
213: 15        dcr  d
214: b2        ora  d
215: b1        ora  c
216: c1        pop  b
217: f1        pop  psw
218: 03        inx  b
219: 06 25     mvi  b,$25
21b: 02        stax b
21c: d6 93     sui  $93
21e: bc        cmp  h
21f: f4 d6 a4  cp   $a4d6
222: c8        rz
223: 02        stax b
224: 20        rim
225: f1        pop  psw
226: bc        cmp  h
227: f4 37 30  cp   $3037
22a: f7        rst  6
22b: b1        ora  c
22c: 72        mov  m,d
22d: d6 a4     sui  $a4
22f: 17        ral
230: bc        cmp  h
231: f4 92 d6  cp   $d692
234: 02        stax b
235: 37        stc
236: 3e ef     mvi  a,$ef
238: a4        ana  h
239: f5        push psw
23a: d6 32     sui  $32
23c: 91        sub  c
23d: 11 ad 56  lxi  d,$56ad
240: 53        mov  d,e
241: 93        sub  e
242: 17        ral
243: b1        ora  c
244: a7        ana  a
245: 56        mov  d,m
246: 11 71 df  lxi  d,$df71
249: bc        cmp  h
24a: da 05 11  jc   $1105
24d: 71        mov  m,c
24e: bc        cmp  h
24f: b4        ora  h
250: 04        inr  b
251: d9        shlx d (*)
252: 05        dcr  b
253: 93        sub  e
254: 41        mov  b,c
255: bc        cmp  h
256: f4 64 26  cp   $2664
259: 33        inx  sp
25a: 26 a4     mvi  h,$a4
25c: 08        dsub (*)
25d: 5b        mov  e,e
25e: 05        dcr  b
25f: 71        mov  m,c
260: 20        rim
261: 01 c3 53  lxi  b,$53c3
264: bc        cmp  h
265: f4 6a ac  cp   $ac6a
268: 41        mov  b,c
269: 11 26 11  lxi  d,$1126
26c: e4 bc 02  cpo  $02bc
26f: b1        ora  c
270: 26 f1     mvi  h,$f1
272: af        xra  a
273: 0f        rrc
274: 05        dcr  b
275: e4 56 c3  cpo  $c356
278: 95        sub  l
279: 07        rlc
27a: e4 ab 26  cpo  $26ab
27d: f1        pop  psw
27e: 07        rlc
27f: b8        cmp  b
280: 07        rlc
281: e9        pchl
282: 93        sub  e
283: ff        rst  7
284: f1        pop  psw
285: fb        ei
286: 95        sub  l
287: 56        mov  d,m
288: 0f        rrc
289: 06 b8     mvi  b,$b8
28b: f1        pop  psw
28c: 47        mov  b,a
28d: fd 07 e9  jx5  $e907 (*)
290: ff        rst  7
291: 97        sub  a
292: 8b        adc  e
293: 8b        adc  e
294: b2        ora  d
295: 71        mov  m,c
296: 71        mov  m,c
297: bc        cmp  h
298: 27        daa
299: 72        mov  m,d
29a: b4        ora  h
29b: 41        mov  b,c
29c: f4 a0 0f  cp   $0fa0
29f: d2 b4 41  jnc  $41b4
2a2: ff        rst  7
2a3: 96        sub  m
2a4: b4        ora  h
2a5: d2 a6 c3  jnc  $c3a6
2a8: c0        rnz
2a9: 03        inx  b
2aa: 04        inr  b
2ab: e4 f1 d6  cpo  $d6f1
2ae: 93        sub  e
2af: b4        ora  h
2b0: ff        rst  7
2b1: 11 fd bc  lxi  d,$bcfd
2b4: 27        daa
2b5: b1        ora  c
2b6: 32 91 bb  sta  $bb91
2b9: 12        stax d
2ba: 91        sub  c
2bb: 71        mov  m,c
2bc: fd c0 61  jx5  $61c0 (*)
2bf: be        cmp  m
2c0: f1        pop  psw
2c1: d6 93     sui  $93
2c3: b4        ora  h
2c4: 03        inx  b
2c5: 04        inr  b
2c6: ca ff 91  jz   $91ff
2c9: 26 f1     mvi  h,$f1
2cb: d6 e0     sui  $e0
2cd: 06 e4     mvi  b,$e4
2cf: 05        dcr  b
2d0: c3 f1 d6  jmp  $d6f1
2d3: 93        sub  e
2d4: e4 03 02  cpo  $0203
2d7: e4 b4 71  cpo  $71b4
2da: 27        daa
2db: 06 ff     mvi  b,$ff
2dd: b6        ora  m
2de: b8        cmp  b
2df: f1        pop  psw
2e0: e9        pchl
2e1: 06 e4     mvi  b,$e4
2e3: 07        rlc
2e4: 26 f1     mvi  h,$f1
2e6: 56        mov  d,m
2e7: 06 ea     mvi  b,$ea
2e9: f1        pop  psw
2ea: f8        rm
2eb: f9        sphl
2ec: b6        ora  m
2ed: f3        di
2ee: fa fb f2  jm   $f2fb
2f1: e1        pop  h
2f2: 81        add  c
2f3: 61        mov  h,c
2f4: f2 fa 0f  jp   $0ffa
2f7: 00        nop
2f8: 61        mov  h,c
2f9: c1        pop  b
2fa: 61        mov  h,c
2fb: e1        pop  h
2fc: 4e        mov  c,m
2fd: 4c        mov  c,h
2fe: 6b        mov  l,e
2ff: 25        dcr  h
300: 26 d1     mvi  h,$d1
302: aa        xra  d
303: 38 02     ldsi $02 (*)
305: df        rst  3
306: be        cmp  m
307: bd        cmp  l
308: 05        dcr  b
309: 9d        sbb  l
30a: 38 2b     ldsi $2b (*)
30c: d1        pop  d
30d: b8        cmp  b
30e: bc        cmp  h
30f: be        cmp  m
310: 06 24     mvi  b,$24
312: 07        rlc
313: 2b        dcx  h
314: b9        cmp  c
315: bd        cmp  l
316: bb        cmp  e
317: 85        add  l
318: f1        pop  psw
319: bc        cmp  h
31a: b4        ora  h
31b: 21 71 27  lxi  h,$2771
31e: 82        add  d
31f: ba        cmp  d
320: 26 d1     mvi  h,$d1
322: aa        xra  d
323: 39        dad  sp
324: 06 df     mvi  b,$df
326: be        cmp  m
327: bd        cmp  l
328: 05        dcr  b
329: 9d        sbb  l
32a: 38 01     ldsi $01 (*)
32c: d1        pop  d
32d: bc        cmp  h
32e: bf        cmp  a
32f: f4 06 57  cp   $5706
332: e3        xthl
333: 1c        inr  e
334: 08        dsub (*)
335: a4        ana  h
336: 3b        dcx  sp
337: f4 16 57  cp   $5716
33a: ef        rst  5
33b: fb        ei
33c: 00        nop
33d: a4        ana  h
33e: 31 ba 39  lxi  sp,$39ba
341: bd        cmp  l
342: d1        pop  d
343: 26 ae     mvi  h,$ae
345: 05        dcr  b
346: b5        ora  l
347: 06 d1     mvi  b,$d1
349: 96        sub  m
34a: 06 df     mvi  b,$df
34c: fd 26 d1  jx5  $d126 (*)
34f: aa        xra  d
350: be        cmp  m
351: bd        cmp  l
352: d1        pop  d
353: b8        cmp  b
354: 39        dad  sp
355: 05        dcr  b
356: 9d        sbb  l
357: 39        dad  sp
358: bc        cmp  h
359: be        cmp  m
35a: b9        cmp  c
35b: bd        cmp  l
35c: 2b        dcx  h
35d: 02        stax b
35e: 22 07 bb  shld $bb07
361: 85        add  l
362: 8c        adc  h
363: 27        daa
364: 2b        dcx  h
365: f1        pop  psw
366: bc        cmp  h
367: b4        ora  h
368: 3e ba     mvi  a,$ba
36a: a6        ana  m
36b: 26 21     mvi  h,$21
36d: ff        rst  7
36e: 96        sub  m
36f: 05        dcr  b
370: d1        pop  d
371: aa        xra  d
372: 39        dad  sp
373: 01 df be  lxi  b,$bedf
376: bd        cmp  l
377: d1        pop  d
378: 9d        sbb  l
379: 39        dad  sp
37a: 2b        dcx  h
37b: 02        stax b
37c: b8        cmp  b
37d: bc        cmp  h
37e: be        cmp  m
37f: b9        cmp  c
380: 20        rim
381: 07        rlc
382: 2b        dcx  h
383: f1        pop  psw
384: bd        cmp  l
385: bb        cmp  e
386: 85        add  l
387: 71        mov  m,c
388: bc        cmp  h
389: b4        ora  h
38a: 21 27 27  lxi  h,$2727
38d: 87        add  a
38e: ba        cmp  d
38f: 17        ral
390: d1        pop  d
391: aa        xra  d
392: 39        dad  sp
393: 05        dcr  b
394: df        rst  3
395: be        cmp  m
396: bd        cmp  l
397: d1        pop  d
398: 9d        sbb  l
399: 3d        dcr  a
39a: 38 06     ldsi $06 (*)
39c: b8        cmp  b
39d: bc        cmp  h
39e: bd        cmp  l
39f: 97        sub  a
3a0: d1        pop  d
3a1: d1        pop  d
3a2: d1        pop  d
3a3: fb        ei
3a4: a9        xra  c
3a5: 93        sub  e
3a6: 93        sub  e
3a7: ba        cmp  d
3a8: 39        dad  sp
3a9: bd        cmp  l
3aa: d1        pop  d
3ab: 27        daa
3ac: ae        xra  m
3ad: 05        dcr  b
3ae: b5        ora  l
3af: 17        ral
3b0: d1        pop  d
3b1: 96        sub  m
3b2: f1        pop  psw
3b3: 07        rlc
3b4: fd 27 e4  jx5  $e427 (*)
3b7: b8        cmp  b
3b8: 00        nop
3b9: e9        pchl
3ba: 3f        cmc
3bb: 3d        dcr  a
3bc: f1        pop  psw
3bd: be        cmp  m
3be: b9        cmp  c
3bf: d1        pop  d
3c0: c2 06 3d  jnz  $3d06
3c3: 3d        dcr  a
3c4: b9        cmp  c
3c5: b8        cmp  b
3c6: bc        cmp  h
3c7: bd        cmp  l
3c8: 06 d1     mvi  b,$d1
3ca: e9        pchl
3cb: bc        cmp  h
3cc: 97        sub  a
3cd: a9        xra  c
3ce: c6 27     adi  $27
3d0: f4 b4 db  cp   $dbb4
3d3: d6 d6     sui  $d6
3d5: c3 f4 0f  jmp  $0ff4
3d8: c3 bc b4  jmp  $b4bc
3db: 96        sub  m
3dc: db 27     in   $27
3de: 00        nop
3df: 26 05     mvi  h,$05
3e1: e4 db 3e  cpo  $3edb
3e4: f1        pop  psw
3e5: d2 be b9  jnc  $b9be
3e8: 3c        inr  a
3e9: c2 38 a4  jnz  $a438
3ec: d1        pop  d
3ed: bc        cmp  h
3ee: 27        daa
3ef: 1c        inr  e
3f0: bf        cmp  a
3f1: f4 a4 ef  cp   $efa4
3f4: 06 47     mvi  b,$47
3f6: 1c        inr  e
3f7: f2 27 cc  jp   $cc27
3fa: 3a 34 a4  lda  $a434
3fd: b8        cmp  b
3fe: f0        rp
3ff: c8        rz
400: cc 34 17  cz   $1734
403: df        rst  3
404: f0        rp
405: 27        daa
406: d1        pop  d
407: ba        cmp  d
408: 39        dad  sp
409: bd        cmp  l
40a: d1        pop  d
40b: 96        sub  m
40c: ae        xra  m
40d: 05        dcr  b
40e: b5        ora  l
40f: be        cmp  m
410: 3e 3c     mvi  a,$3c
412: c2 3c b9  jnz  $b93c
415: d1        pop  d
416: bc        cmp  h
417: f4 85 19  cp   $1985
41a: b8        cmp  b
41b: bc        cmp  h
41c: c3 95 3e  jmp  $3e95
41f: 2b        dcx  h
420: be        cmp  m
421: bd        cmp  l
422: b3        ora  e
423: ce 06     aci  $06
425: 06 28     mvi  b,$28
427: ce b9     aci  $b9
429: bb        cmp  e
42a: 85        add  l
42b: 8c        adc  h
42c: 2c        inr  l
42d: 2b        dcx  h
42e: f1        pop  psw
42f: 27        daa
430: 17        ral
431: df        rst  3
432: be        cmp  m
433: bd        cmp  l
434: d1        pop  d
435: aa        xra  d
436: 39        dad  sp
437: 05        dcr  b
438: d1        pop  d
439: b8        cmp  b
43a: bc        cmp  h
43b: be        cmp  m
43c: 9d        sbb  l
43d: 39        dad  sp
43e: 2e 06     mvi  l,$06
440: b9        cmp  c
441: bd        cmp  l
442: bb        cmp  e
443: 85        add  l
444: 21 01 2e  lxi  h,$2e01
447: f1        pop  psw
448: 8c        adc  h
449: 28 01     ldhi $01 (*)
44b: 56        mov  d,m
44c: bc        cmp  h
44d: bf        cmp  a
44e: f4 0f c3  cp   $c30f
451: d6 93     sui  $93
453: 1c        inr  e
454: 53        mov  d,e
455: 0f        rrc
456: 62        mov  h,d
457: ef        rst  5
458: 4d        mov  c,l
459: 28 01     ldhi $01 (*)
45b: 0f        rrc
45c: bc        cmp  h
45d: bf        cmp  a
45e: b4        ora  h
45f: 1c        inr  e
460: ef        rst  5
461: 21 27 d1  lxi  h,$d127
464: 5d        mov  e,l
465: ba        cmp  d
466: 17        ral
467: df        rst  3
468: aa        xra  d
469: 39        dad  sp
46a: 01 9d be  lxi  b,$be9d
46d: bd        cmp  l
46e: d1        pop  d
46f: bc        cmp  h
470: 3c        inr  a
471: 56        mov  d,m
472: a4        ana  h
473: 02        stax b
474: f4 f0 26  cp   $26f0
477: d1        pop  d
478: df        rst  3
479: be        cmp  m
47a: bd        cmp  l
47b: d1        pop  d
47c: aa        xra  d
47d: 38 05     ldsi $05 (*)
47f: 9d        sbb  l
480: b8        cmp  b
481: bc        cmp  h
482: bd        cmp  l
483: 97        sub  a
484: 3c        inr  a
485: 31 01 d1  lxi  sp,$d101
488: a9        xra  c
489: 93        sub  e
48a: ba        cmp  d
48b: ae        xra  m
48c: d1        pop  d
48d: fb        ei
48e: 38 bd     ldsi $bd (*)
490: 05        dcr  b
491: b5        ora  l
492: 02        stax b
493: fd d1 26  jx5  $26d1 (*)
496: d1        pop  d
497: 26 05     mvi  h,$05
499: df        rst  3
49a: be        cmp  m
49b: bd        cmp  l
49c: d1        pop  d
49d: aa        xra  d
49e: 39        dad  sp
49f: 01 d1 bc  lxi  b,$bcd1
4a2: bf        cmp  a
4a3: 97        sub  a
4a4: 9d        sbb  l
4a5: 38 01     ldsi $01 (*)
4a7: a7        ana  a
4a8: 1c        inr  e
4a9: 16 57     mvi  d,$57
4ab: e3        xthl
4ac: f4 00 a4  cp   $a400
4af: b2        ora  d
4b0: ef        rst  5
4b1: fb        ei
4b2: 39        dad  sp
4b3: bd        cmp  l
4b4: a8        xra  b
4b5: ba        cmp  d
4b6: ae        xra  m
4b7: 01 d1 26  lxi  b,$26d1
4ba: d1        pop  d
4bb: be        cmp  m
4bc: b5        ora  l
4bd: 05        dcr  b
4be: fd 3c b9  jx5  $b93c (*)
4c1: fe 27     cpi  $27
4c3: e9        pchl
4c4: 0a        ldax b
4c5: a8        xra  b
4c6: f1        pop  psw
4c7: ce e9     aci  $e9
4c9: 71        mov  m,c
4ca: 26 f1     mvi  h,$f1
4cc: c2 da 0e  jnz  $0eda
4cf: e4 07 d8  cpo  $d807
4d2: f1        pop  psw
4d3: ec 93 ac  cpe  $ac93
4d6: f1        pop  psw
4d7: d1        pop  d
4d8: b8        cmp  b
4d9: f1        pop  psw
4da: 96        sub  m
4db: a6        ana  m
4dc: 0e e9     mvi  c,$e9
4de: ff        rst  7
4df: 96        sub  m
4e0: 26 f1     mvi  h,$f1
4e2: 17        ral
4e3: d6 06     sui  $06
4e5: e4 af 03  cpo  $03af
4e8: 93        sub  e
4e9: 71        mov  m,c
4ea: 27        daa
4eb: f0        rp
4ec: ef        rst  5
4ed: da 81 ff  jc   $ff81
4f0: b8        cmp  b
4f1: f1        pop  psw
4f2: 96        sub  m
4f3: f1        pop  psw
4f4: 06 e9     mvi  b,$e9
4f6: 53        mov  d,e
4f7: 11 d6 f1  lxi  d,$f1d6
4fa: 01 e4 c3  lxi  b,$c3e4
4fd: 26 f1     mvi  h,$f1
4ff: 07        rlc
500: c3 b8 f1  jmp  $f1b8
503: 96        sub  m
504: 07        rlc
505: 01 e9 f1  lxi  b,$f1e9
508: c8        rz
509: 27        daa
50a: b4        ora  h
50b: 72        mov  m,d
50c: bc        cmp  h
50d: f4 10 12  cp   $1210
510: b4        ora  h
511: 11 71 96  lxi  d,$9671
514: 08        dsub (*)
515: bc        cmp  h
516: 8b        adc  e
517: 11 d6 23  lxi  d,$23d6
51a: 03        inx  b
51b: e4 c3 26  cpo  $26c3
51e: f1        pop  psw
51f: 07        rlc
520: c3 b8 f1  jmp  $f1b8
523: 96        sub  m
524: 27        daa
525: 03        inx  b
526: e9        pchl
527: 26 01     mvi  h,$01
529: df        rst  3
52a: be        cmp  m
52b: bd        cmp  l
52c: d1        pop  d
52d: aa        xra  d
52e: 39        dad  sp
52f: 01 d1 bc  lxi  b,$bcd1
532: bf        cmp  a
533: 97        sub  a
534: 9d        sbb  l
535: 38 01     ldsi $01 (*)
537: a7        ana  a
538: 1c        inr  e
539: 16 57     mvi  d,$57
53b: e3        xthl
53c: f4 00 a4  cp   $a400
53f: 42        mov  b,d
540: ef        rst  5
541: fb        ei
542: 39        dad  sp
543: bd        cmp  l
544: 38 ba     ldsi $ba (*)
546: ae        xra  m
547: 01 d1 26  lxi  b,$26d1
54a: d1        pop  d
54b: 26 b5     mvi  h,$b5
54d: 01 fd 48  lxi  b,$48fd
550: a1        ana  c
551: bc        cmp  h
552: f4 82 22  cp   $2282
555: 02        stax b
556: d2 d6 40  jnc  $40d6
559: 27        daa
55a: e4 39 a4  cpo  $a439
55d: f1        pop  psw
55e: ba        cmp  d
55f: 12        stax d
560: 66        mov  h,m
561: 3f        cmc
562: 39        dad  sp
563: 06 ba     mvi  b,$ba
565: be        cmp  m
566: bd        cmp  l
567: d1        pop  d
568: 9d        sbb  l
569: 39        dad  sp
56a: 56        mov  d,m
56b: a4        ana  h
56c: bc        cmp  h
56d: f4 0f b8  cp   $b80f
570: 39        dad  sp
571: 3c        inr  a
572: 06 a4     mvi  b,$a4
574: bc        cmp  h
575: bf        cmp  a
576: f0        rp
577: c8        rz
578: cc 75 31  cz   $3175
57b: 3a ef bc  lda  $bcef
57e: b4        ora  h
57f: 1c        inr  e
580: b4        ora  h
581: bc        cmp  h
582: f4 95 05  cp   $0595
585: 32 12 b1  sta  $b112
588: 8e        adc  m
589: ce 31     aci  $31
58b: ac        xra  h
58c: a1        ana  c
58d: bc        cmp  h
58e: f4 06 fd  cp   $fd06
591: f0        rp
592: 96        sub  m
593: 03        inx  b
594: a8        xra  b
595: a4        ana  h
596: f1        pop  psw
597: d6 04     sui  $04
599: 93        sub  e
59a: 95        sub  l
59b: c8        rz
59c: 85        add  l
59d: 9f        sbb  a
59e: f1        pop  psw
59f: 95        sub  l
5a0: bc        cmp  h
5a1: f4 b3 07  cp   $07b3
5a4: 35        dcr  m
5a5: af        xra  a
5a6: bc        cmp  h
5a7: 93        sub  e
5a8: ae        xra  m
5a9: f5        push psw
5aa: 37        stc
5ab: ce a1     aci  $a1
5ad: a4        ana  h
5ae: 12        stax d
5af: b1        ora  c
5b0: 8e        adc  m
5b1: 31 a1 ff  lxi  sp,$ffa1
5b4: bc        cmp  h
5b5: 14        inr  d
5b6: ce a6     aci  $a6
5b8: 96        sub  m
5b9: 31 a8 f4  lxi  sp,$f4a8
5bc: bc        cmp  h
5bd: f4 ac 2f  cp   $2fac
5c0: 12        stax d
5c1: 2f        cma
5c2: f0        rp
5c3: ca c7 46  jz   $46c7
5c6: a1        ana  c
5c7: 2f        cma
5c8: 46        mov  b,m
5c9: a0        ana  b
5ca: 03        inx  b
5cb: 06 0f     mvi  b,$0f
5cd: f1        pop  psw
5ce: d6 93     sui  $93
5d0: b8        cmp  b
5d1: c8        rz
5d2: b4        ora  h
5d3: cc f1 cc  cz   $ccf1
5d6: fb        ei
5d7: b4        ora  h
5d8: ff        rst  7
5d9: 31 06 a8  lxi  sp,$a806
5dc: bc        cmp  h
5dd: f4 fd ac  cp   $acfd
5e0: f4 bc f4  cp   $f4bc
5e3: ed        lhlx d (*)
5e4: af        xra  a
5e5: 35        dcr  m
5e6: 12        stax d
5e7: ff        rst  7
5e8: 06 57     mvi  b,$57
5ea: 96        sub  m
5eb: 47        mov  b,a
5ec: 0a        ldax b
5ed: a0        ana  b
5ee: ff        rst  7
5ef: 06 0a     mvi  b,$0a
5f1: 47        mov  b,a
5f2: 96        sub  m
5f3: 02        stax b
5f4: 57        mov  d,a
5f5: a0        ana  b
5f6: bc        cmp  h
5f7: f4 56 a4  cp   $a456
5fa: f1        pop  psw
5fb: 46        mov  b,m
5fc: 9f        sbb  a
5fd: 27        daa
5fe: e4 02 ad  cpo  $ad02
601: 00        nop
602: e9        pchl
603: 39        dad  sp
604: b8        cmp  b
605: f1        pop  psw
606: be        cmp  m
607: fd 12 be  jx5  $be12 (*)
60a: ba        cmp  d
60b: bd        cmp  l
60c: 09        dad  b
60d: 3f        cmc
60e: 3c        inr  a
60f: 06 d1     mvi  b,$d1
611: 71        mov  m,c
612: 96        sub  m
613: 39        dad  sp
614: b5        ora  l
615: be        cmp  m
616: b8        cmp  b
617: bc        cmp  h
618: 2b        dcx  h
619: 04        inr  b
61a: 27        daa
61b: 06 be     mvi  b,$be
61d: b9        cmp  c
61e: bd        cmp  l
61f: bb        cmp  e
620: 2e f1     mvi  l,$f1
622: b8        cmp  b
623: bc        cmp  h
624: 85        add  l
625: 8c        adc  h
626: 3a 2c be  lda  $be2c
629: b9        cmp  c
62a: bd        cmp  l
62b: bb        cmp  e
62c: 04        inr  b
62d: 28 02     ldhi $02 (*)
62f: 2a 85 71  lhld $7185
632: 2e 0f     mvi  l,$0f
634: f1        pop  psw
635: bc        cmp  h
636: b4        ora  h
637: cc b4 bc  cz   $bcb4
63a: b8        cmp  b
63b: f0        rp
63c: 1f        rar
63d: 27        daa
63e: 32 bf 00  sta  $00bf
641: 45        mov  b,l
642: 2f        cma
643: a4        ana  h
644: 12        stax d
645: bf        cmp  a
646: ff        rst  7
647: 21 ba 01  lxi  h,$01ba
64a: df        rst  3
64b: be        cmp  m
64c: 26 d1     mvi  h,$d1
64e: aa        xra  d
64f: 39        dad  sp
650: bd        cmp  l
651: d1        pop  d
652: b8        cmp  b
653: bc        cmp  h
654: 01 9d 39  lxi  b,$399d
657: 2b        dcx  h
658: be        cmp  m
659: b9        cmp  c
65a: bd        cmp  l
65b: bb        cmp  e
65c: 04        inr  b
65d: 26 07     mvi  h,$07
65f: 2b        dcx  h
660: 85        add  l
661: 8c        adc  h
662: 27        daa
663: 9e        sbb  m
664: f1        pop  psw
665: bc        cmp  h
666: b4        ora  h
667: 21 ba 84  lxi  h,$84ba
66a: 3a ff 83  lda  $83ff
66d: 84        add  h
66e: ff        rst  7
66f: ff        rst  7
670: 39        dad  sp
671: 84        add  h
672: 3a ff b9  lda  $b9ff
675: 8c        adc  h
676: ff        rst  7
677: ff        rst  7
678: 39        dad  sp
679: 29        dad  h
67a: 9c        sbb  h
67b: 39        dad  sp
67c: 9c        sbb  h
67d: b5        ora  l
67e: ff        rst  7
67f: ab        xra  e
680: ff        rst  7
681: fa 6c bc  jm   $bc6c
684: e1        pop  h
685: 06 a8     mvi  b,$a8
687: 27        daa
688: bf        cmp  a
689: f8        rm
68a: 17        ral
68b: c8        rz
68c: 08        dsub (*)
68d: a6        ana  m
68e: a4        ana  h
68f: cc ef 96  cz   $96ef
692: a6        ana  m
693: f4 8a ff  cp   $ff8a
696: 96        sub  m
697: 16 00     mvi  d,$00
699: a4        ana  h
69a: 86        add  m
69b: f1        pop  psw
69c: 57        mov  d,a
69d: 1c        inr  e
69e: fa e4 06  jm   $06e4
6a1: 57        mov  d,a
6a2: ac        xra  h
6a3: a4        ana  h
6a4: 00        nop
6a5: 2e 2e     mvi  l,$2e
6a7: ca ce 9d  jz   $9dce
6aa: f4 57 ed  cp   $ed57
6ad: 96        sub  m
6ae: 70        mov  m,b
6af: a4        ana  h
6b0: 18        rdel (*)
6b1: ed        lhlx d (*)
6b2: 86        add  m
6b3: ac        xra  h
6b4: 1c        inr  e
6b5: a9        xra  c
6b6: fa f4 2e  jm   $2ef4
6b9: 2e e9     mvi  l,$e9
6bb: ce a8     aci  $a8
6bd: f1        pop  psw
6be: ca ed b5  jz   $b5ed
6c1: 27        daa
6c2: e4 32 96  cpo  $9632
6c5: f1        pop  psw
6c6: 85        add  l
6c7: cc 95 39  cz   $3995
6ca: cf        rst  1
6cb: 3f        cmc
6cc: ba        cmp  d
6cd: 12        stax d
6ce: ba        cmp  d
6cf: bd        cmp  l
6d0: 06 9d     mvi  b,$9d
6d2: d3 f9     out  $f9
6d4: d1        pop  d
6d5: b3        ora  e
6d6: 96        sub  m
6d7: a8        xra  b
6d8: ac        xra  h
6d9: 06 d1     mvi  b,$d1
6db: 96        sub  m
6dc: bd        cmp  l
6dd: 97        sub  a
6de: a9        xra  c
6df: ab        xra  e
6e0: e7        rst  4
6e1: d1        pop  d
6e2: 59        mov  e,c
6e3: ec ad f2  cpe  $f2ad
6e6: c3 27 17  jmp  $1727
6e9: d6 f1     sui  $f1
6eb: 2b        dcx  h
6ec: ab        xra  e
6ed: 04        inr  b
6ee: 20        rim
6ef: f1        pop  psw
6f0: 20        rim
6f1: 27        daa
6f2: f1        pop  psw
6f3: a9        xra  c
6f4: 96        sub  m
6f5: 17        ral
6f6: e4 26 80  cpo  $8026
6f9: eb        xchg
6fa: 96        sub  m
6fb: d1        pop  d
6fc: e7        rst  4
6fd: fc ab f2  cm   $f2ab
700: d9        shlx d (*)
701: 04        inr  b
702: e9        pchl
703: bc        cmp  h
704: b8        cmp  b
705: f1        pop  psw
706: 96        sub  m
707: 36 f4     mvi  m,$f4
709: 6f        mov  l,a
70a: f1        pop  psw
70b: 12        stax d
70c: 96        sub  m
70d: af        xra  a
70e: dc 0a 52  cc   $520a
711: ff        rst  7
712: 3c        inr  a
713: 2f        cma
714: 0a        ldax b
715: 96        sub  m
716: 31 2a 25  lxi  sp,$252a
719: 1e 16     mvi  e,$16
71b: e1        pop  h
71c: 20        rim
71d: 17        ral
71e: 0f        rrc
71f: fa 6d 12  jm   $126d
722: 96        sub  m
723: 05        dcr  b
724: 06 a6     mvi  b,$a6
726: 26 f1     mvi  h,$f1
728: e4 00 b8  cpo  $b800
72b: b0        ora  b
72c: 06 57     mvi  b,$57
72e: 39        dad  sp
72f: 00        nop
730: c8        rz
731: c8        rz
732: 31 bc a0  lxi  sp,$a0bc
735: b0        ora  b
736: c8        rz
737: 1d        dcr  e
738: 11 06 57  lxi  d,$5706
73b: 42        mov  b,d
73c: b0        ora  b
73d: 06 33     mvi  b,$33
73f: 06 50     mvi  b,$50
741: a0        ana  b
742: 39        dad  sp
743: 2b        dcx  h
744: 57        mov  d,a
745: b8        cmp  b
746: bc        cmp  h
747: be        cmp  m
748: 04        inr  b
749: 27        daa
74a: 07        rlc
74b: 2b        dcx  h
74c: b9        cmp  c
74d: bd        cmp  l
74e: bb        cmp  e
74f: 85        add  l
750: f1        pop  psw
751: bc        cmp  h
752: b4        ora  h
753: f1        pop  psw
754: 8c        adc  h
755: 27        daa
756: af        xra  a
757: 03        inx  b
758: d6 93     sui  $93
75a: bc        cmp  h
75b: 11 06 61  lxi  d,$6106
75e: 1d        dcr  e
75f: b0        ora  b
760: 17        ral
761: f1        pop  psw
762: f1        pop  psw
763: d6 94     sui  $94
765: c8        rz
766: 03        inx  b
767: 02        stax b
768: 93        sub  e
769: b8        cmp  b
76a: 80        add  b
76b: 3f        cmc
76c: 72        mov  m,d
76d: 2e 17     mvi  l,$17
76f: 90        sub  b
770: f1        pop  psw
771: 21 19 56  lxi  h,$5619
774: c8        rz
775: ba        cmp  d
776: f0        rp
777: f0        rp
778: b3        ora  e
779: ee 95     xri  $95
77b: 82        add  d
77c: 82        add  d
77d: 7f        mov  a,a
77e: e1        pop  h
77f: c3 8c 47  jmp  $478c
782: ed        lhlx d (*)
783: e1        pop  h
784: 95        sub  l
785: a4        ana  h
786: 88        adc  b
787: a0        ana  b
788: cc f0 0f  cz   $0ff0
78b: 97        sub  a
78c: 19        dad  d
78d: 56        mov  d,m
78e: b3        ora  e
78f: ee 91     xri  $91
791: e1        pop  h
792: c3 95 95  jmp  $9595
795: 97        sub  a
796: 9d        sbb  l
797: a4        ana  h
798: ed        lhlx d (*)
799: e1        pop  h
79a: cc e1 99  cz   $99e1
79d: a0        ana  b
79e: c8        rz
79f: 71        mov  m,c
7a0: fb        ei
7a1: f4 a9 0f  cp   $0fa9
7a4: ac        xra  h
7a5: 93        sub  e
7a6: b4        ora  h
7a7: fb        ei
7a8: cb        rstv 8 (*)
7a9: 93        sub  e
7aa: 27        daa
7ab: f9        sphl
7ac: d9        shlx d (*)
7ad: a0        ana  b
7ae: af        xra  a
7af: d6 28     sui  $28
7b1: b1        ora  c
7b2: f9        sphl
7b3: 29        dad  h
7b4: 93        sub  e
7b5: 1f        rar
7b6: d6 93     sui  $93
7b8: ba        cmp  d
7b9: ff        rst  7
7ba: c6 ac     adi  $ac
7bc: 1f        rar
7bd: 93        sub  e
7be: f9        sphl
7bf: f4 06 a4  cp   $a406
7c2: a7        ana  a
7c3: fa 10 11  jm   $1110
7c6: 93        sub  e
7c7: 96        sub  m
7c8: bc        cmp  h
7c9: b4        ora  h
7ca: 96        sub  m
7cb: a6        ana  m
7cc: 36 ff     mvi  m,$ff
7ce: ff        rst  7
7cf: 96        sub  m
7d0: f2 d2 e7  jp   $e7d2
7d3: e7        rst  4
7d4: fa fa 17  jm   $17fa
7d7: ac        xra  h
7d8: 86        add  m
7d9: 03        inx  b
7da: c3 f1 f1  jmp  $f1f1
7dd: 17        ral
7de: dc c8 96  cc   $96c8
7e1: d0        rnc
7e2: b0        ora  b
7e3: 1c        inr  e
7e4: f1        pop  psw
7e5: 11 a8 11  lxi  d,$11a8
7e8: b0        ora  b
7e9: 68        mov  l,b
7ea: 28 d0     ldhi $d0 (*)
7ec: 47        mov  b,a
7ed: 86        add  m
7ee: f1        pop  psw
7ef: f8        rm
7f0: 3f        cmc
7f1: 1c        inr  e
7f2: 3f        cmc
7f3: 86        add  m
7f4: 94        sub  h
7f5: 47        mov  b,a
7f6: 94        sub  h
7f7: 71        mov  m,c
7f8: 9d        sbb  l
7f9: 26 3a     mvi  h,$3a
7fb: e8        rpe
7fc: 94        sub  h
7fd: 4f        mov  c,a
7fe: 01 ff ff  lxi  b,$00ff
