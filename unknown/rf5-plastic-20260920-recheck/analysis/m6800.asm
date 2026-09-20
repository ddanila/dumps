000: ff d5 9e  stx  $D59E
003: b4 21 01  anda $2101
006: fb c5 bc  addb $C5BC
009: a4 56     anda $56,x
00b: c3        illegal
00c: 30        tsx  
00d: fb f8 12  addb $F812
010: e1 26     cmpb $26,x
012: 62        illegal
013: 6f fa     clr  $FA,x
015: e4 26     andb $26,x
017: 3a        illegal
018: 8c 0c 26  cmpx #$0C26
01b: 3a        illegal
01c: ff ae 5f  stx  $AE5F
01f: b8 2e 12  eora $2E12
022: c8 17     eorb #$17
024: 80 2e     suba #$2E
026: 80 3f     suba #$3F
028: 90 44     suba $44
02a: f2 fb 52  sbcb $FB52
02d: fa 44 06  orb  $4406
030: 1f        illegal
031: 06        tap  
032: ac 3c     cmpx $3C,x
034: a8 01     eora $01,x
036: f4 8a df  andb $8ADF
039: 5f        clrb 
03a: 3c        illegal
03b: 07        tpa  
03c: 9a f0     ora  $F0
03e: fb 47 3a  addb $473A
041: 77 01 48  asr  $0148
044: eb bb     addb $BB,x
046: 83        illegal
047: 05        illegal
048: 85 fe     bita #$FE
04a: 06        tap  
04b: 5e        illegal
04c: 95 bc     bita $BC
04e: 52        illegal
04f: b3        illegal
050: 57        asrb 
051: 46        rora 
052: aa 72     ora  $72,x
054: fa 80 01  orb  $8001
057: 95 2e     bita $2E
059: 2e 77     bgt  $00D2
05b: 4d        tsta 
05c: fc        illegal
05d: 77 ec fa  asr  $ECFA
060: 56        rorb 
061: aa 71     ora  $71,x
063: 72        illegal
064: 7f b3 ef  clr  $B3EF
067: fe bc 53  ldx  $BC53
06a: d6 c3     ldb  $C3
06c: 36        psha 
06d: 74 04 74  lsr  $0474
070: fe bf ef  ldx  $BFEF
073: 1f        illegal
074: a4 07     anda $07,x
076: 77 bc 34  asr  $BC34
079: 07        tpa  
07a: 93        illegal
07b: 26 f4     bne  $0071
07d: a4 87     anda $87,x
07f: 95 a4     bita $A4
081: 14        illegal
082: 46        rora 
083: aa 1c     ora  $1C,x
085: fa 08 bc  orb  $08BC
088: 2f 07     ble  $0091
08a: 8f 95 f4  sts  #$95F4
08d: c3        illegal
08e: 01        nop  
08f: fa 46 aa  orb  $46AA
092: 8f bc 10  sts  #$BC10
095: 26 a4     bne  $003B
097: 30        tsx  
098: f4 96 15  andb $9615
09b: cd        illegal
09c: 3f        swi  
09d: c5 c9     bitb #$C9
09f: 3f        swi  
0a0: 96 ae     lda  $AE
0a2: ff 96 6e  stx  $966E
0a5: 96 a6     lda  $A6
0a7: 26 0c     bne  $00B5
0a9: e4 0f     andb $0F,x
0ab: 03        illegal
0ac: f1 56 d6  cmpb $56D6
0af: 86 84     lda  #$84
0b1: 0f        sei  
0b2: b8 f1 56  eora $F156
0b5: 86 02     lda  #$02
0b7: e9 96     adcb $96,x
0b9: 08        inx  
0ba: bf 05 26  sts  $0526
0bd: 33        pulb 
0be: 26 b8     bne  $0078
0c0: 01        nop  
0c1: bc b4 bc  cmpx $B4BC
0c4: a0 2f     suba $2F,x
0c6: 8f 1d 11  sts  #$1D11
0c9: 06        tap  
0ca: b8 f1 b0  eora $F1B0
0cd: 06        tap  
0ce: 01        nop  
0cf: e9 96     adcb $96,x
0d1: 4a        deca 
0d2: 02        illegal
0d3: e4 21     andb $21,x
0d5: 26 f1     bne  $00C8
0d7: 96 26     lda  $26
0d9: bc a4 b4  cmpx $A4B4
0dc: f8 0c cc  eorb $0CCC
0df: a7 bc     sta  $BC,x
0e1: a4 b4     anda $B4,x
0e3: 42        illegal
0e4: 17        tba  
0e5: cc        illegal
0e6: d4 96     andb $96
0e8: 27 b8     beq  $00A2
0ea: a0 e9     suba $E9,x
0ec: d7 3f     stb  $3F
0ee: e8 26     eorb $26,x
0f0: 01        nop  
0f1: af e4     sts  $E4,x
0f3: d5 ab     bitb $AB
0f5: 26 62     bne  $0159
0f7: 55        illegal
0f8: 25 fb     bcs  $00F5
0fa: eb ef     addb $EF,x
0fc: fb fb fc  addb $FBFC
0ff: fc        illegal
100: fb 43 17  addb $4317
103: 86 43     lda  #$43
105: 26 d1     bne  $00D8
107: bf 05 a1  sts  $05A1
10a: 0e        cli  
10b: 27 11     beq  $011E
10d: b8 ad af  eora $ADAF
110: ae e9     lds  $E9,x
112: b3        illegal
113: a4 f1     anda $F1,x
115: b1 11 91  cmpa $1191
118: dd        illegal
119: a4 96     anda $96,x
11b: a4 11     anda $11,x
11d: d1 11     cmpb $11
11f: 71        illegal
120: 6e a4     jmp  $A4,x
122: a1 a4     cmpa $A4,x
124: 11        cba  
125: 11        cba  
126: 11        cba  
127: 51        illegal
128: a1 a4     cmpa $A4,x
12a: a7 a4     sta  $A4,x
12c: 11        cba  
12d: 31        ins  
12e: 11        cba  
12f: ef 16     stx  $16,x
131: cd        illegal
132: a4 af     anda $AF,x
134: f1 11 2d  cmpb $112D
137: fd        illegal
138: f1 11 ef  cmpb $11EF
13b: c3        illegal
13c: cd        illegal
13d: a4 38     anda $38,x
13f: 43        coma 
140: 26 d1     bne  $0113
142: 21 f1     brn  $0135
144: 0f        sei  
145: 86 07     lda  #$07
147: c8 11     eorb #$11
149: 93        illegal
14a: 71        illegal
14b: 43        coma 
14c: d8 51     eorb $51
14e: be aa f1  lds  $AAF1
151: 21 bf     brn  $0112
153: ff dc aa  stx  $DCAA
156: 3f        swi  
157: a8 f1     eora $F1,x
159: ef bf     stx  $BF,x
15b: ff e9 53  stx  $E953
15e: 3f        swi  
15f: d6 0a     ldb  $0A
161: 6f f1     clr  $F1,x
163: df c3     stx  $C3
165: ff e4 c3  stx  $E4C3
168: 6f 07     clr  $07,x
16a: 86 51     lda  #$51
16c: 26 d1     bne  $013F
16e: 21 ff     brn  $016F
170: a8 f1     eora $F1,x
172: ef 26     stx  $26,x
174: 27 e9     beq  $015F
176: 5b        illegal
177: 06        tap  
178: bc 94 3f  cmpx $943F
17b: 03        illegal
17c: 1d        illegal
17d: 26 b8     bne  $0137
17f: f1 e9 02  cmpb $E902
182: 3e        wai  
183: e9 26     adcb $26,x
185: b8 f1 26  eora $F126
188: 06        tap  
189: 3b        rti  
18a: e9 ff     adcb $FF,x
18c: b8 f1 26  eora $F126
18f: b8 00 e9  eora $00E9
192: 15        illegal
193: 07        tpa  
194: f1 b8 ff  cmpb $B8FF
197: f1 0a c8  cmpb $0AC8
19a: 0a        clv  
19b: ee a0     ldx  $A0,x
19d: f1 06 a0  cmpb $06A0
1a0: f1 06 ac  cmpb $06AC
1a3: 96 0a     lda  $0A
1a5: eb cf     addb $CF,x
1a7: ff a6 42  stx  $A642
1aa: c3        illegal
1ab: 8c 96 17  cmpx #$9617
1ae: aa ff     ora  $FF,x
1b0: 8a 0c     ora  #$0C
1b2: b8 f1 7f  eora $F17F
1b5: 37        pshb 
1b6: 05        illegal
1b7: e9 11     adcb $11,x
1b9: ba bc f4  ora  $BCF4
1bc: bc 07 32  cmpx $0732
1bf: be 0f c5  lds  $0FC5
1c2: 1f        illegal
1c3: 28 12     bvc  $01D7
1c5: be bc b8  lds  $BCB8
1c8: 20 ed     bra  $01B7
1ca: 84 9a     anda #$9A
1cc: 21 bd     brn  $018B
1ce: 3a        illegal
1cf: 83        illegal
1d0: 99 8c     adca $8C
1d2: 9b 23     adda $23
1d4: b9 bb bc  adca $BBBC
1d7: fc        illegal
1d8: 21 ff     brn  $01D9
1da: c4 da     andb #$DA
1dc: e5 fd     bitb $FD,x
1de: 7a c3 d9  dec  $C3D9
1e1: cc        illegal
1e2: db 94     addb $94
1e4: f9 fb 3f  adcb $FB3F
1e7: 01        nop  
1e8: e8 3f     eorb $3F,x
1ea: fa 56 ff  orb  $56FF
1ed: e1 f4     cmpb $F4,x
1ef: e0 c3     subb $C3,x
1f1: e1 f4     cmpb $F4,x
1f3: 06        tap  
1f4: f1 fa 5e  cmpb $FA5E
1f7: ce a6 a0  ldx  #$A6A0
1fa: 1c        illegal
1fb: ed        illegal
1fc: 17        tba  
1fd: 18        illegal
1fe: ea 26     orb  $26,x
200: 06        tap  
201: e4 05     andb $05,x
203: 0c        clc  
204: f1 d6 93  cmpb $D693
207: 41        illegal
208: 25 d6     bcs  $01E0
20a: 17        tba  
20b: 02        illegal
20c: 11        cba  
20d: 93        illegal
20e: bc f4 37  cmpx $F437
211: 17        tba  
212: 52        illegal
213: 15        illegal
214: b2 b1 c1  sbca $B1C1
217: f1 03 06  cmpb $0306
21a: 25 02     bcs  $021E
21c: d6 93     ldb  $93
21e: bc f4 d6  cmpx $F4D6
221: a4 c8     anda $C8,x
223: 02        illegal
224: 20 f1     bra  $0217
226: bc f4 37  cmpx $F437
229: 30        tsx  
22a: f7 b1 72  stb  $B172
22d: d6 a4     ldb  $A4
22f: 17        tba  
230: bc f4 92  cmpx $F492
233: d6 02     ldb  $02
235: 37        pshb 
236: 3e        wai  
237: ef a4     stx  $A4,x
239: f5 d6 32  bitb $D632
23c: 91 11     cmpa $11
23e: ad 56     jsr  $56,x
240: 53        comb 
241: 93        illegal
242: 17        tba  
243: b1 a7 56  cmpa $A756
246: 11        cba  
247: 71        illegal
248: df bc     stx  $BC
24a: da 05     orb  $05
24c: 11        cba  
24d: 71        illegal
24e: bc b4 04  cmpx $B404
251: d9 05     adcb $05
253: 93        illegal
254: 41        illegal
255: bc f4 64  cmpx $F464
258: 26 33     bne  $028D
25a: 26 a4     bne  $0200
25c: 08        inx  
25d: 5b        illegal
25e: 05        illegal
25f: 71        illegal
260: 20 01     bra  $0263
262: c3        illegal
263: 53        comb 
264: bc f4 6a  cmpx $F46A
267: ac 41     cmpx $41,x
269: 11        cba  
26a: 26 11     bne  $027D
26c: e4 bc     andb $BC,x
26e: 02        illegal
26f: b1 26 f1  cmpa $26F1
272: af 0f     sts  $0F,x
274: 05        illegal
275: e4 56     andb $56,x
277: c3        illegal
278: 95 07     bita $07
27a: e4 ab     andb $AB,x
27c: 26 f1     bne  $026F
27e: 07        tpa  
27f: b8 07 e9  eora $07E9
282: 93        illegal
283: ff f1 fb  stx  $F1FB
286: 95 56     bita $56
288: 0f        sei  
289: 06        tap  
28a: b8 f1 47  eora $F147
28d: fd        illegal
28e: 07        tpa  
28f: e9 ff     adcb $FF,x
291: 97 8b     sta  $8B
293: 8b b2     adda #$B2
295: 71        illegal
296: 71        illegal
297: bc 27 72  cmpx $2772
29a: b4 41 f4  anda $41F4
29d: a0 0f     suba $0F,x
29f: d2 b4     sbcb $B4
2a1: 41        illegal
2a2: ff 96 b4  stx  $96B4
2a5: d2 a6     sbcb $A6
2a7: c3        illegal
2a8: c0 03     subb #$03
2aa: 04        illegal
2ab: e4 f1     andb $F1,x
2ad: d6 93     ldb  $93
2af: b4 ff 11  anda $FF11
2b2: fd        illegal
2b3: bc 27 b1  cmpx $27B1
2b6: 32        pula 
2b7: 91 bb     cmpa $BB
2b9: 12        illegal
2ba: 91 71     cmpa $71
2bc: fd        illegal
2bd: c0 61     subb #$61
2bf: be f1 d6  lds  $F1D6
2c2: 93        illegal
2c3: b4 03 04  anda $0304
2c6: ca ff     orb  #$FF
2c8: 91 26     cmpa $26
2ca: f1 d6 e0  cmpb $D6E0
2cd: 06        tap  
2ce: e4 05     andb $05,x
2d0: c3        illegal
2d1: f1 d6 93  cmpb $D693
2d4: e4 03     andb $03,x
2d6: 02        illegal
2d7: e4 b4     andb $B4,x
2d9: 71        illegal
2da: 27 06     beq  $02E2
2dc: ff b6 b8  stx  $B6B8
2df: f1 e9 06  cmpb $E906
2e2: e4 07     andb $07,x
2e4: 26 f1     bne  $02D7
2e6: 56        rorb 
2e7: 06        tap  
2e8: ea f1     orb  $F1,x
2ea: f8 f9 b6  eorb $F9B6
2ed: f3        illegal
2ee: fa fb f2  orb  $FBF2
2f1: e1 81     cmpb $81,x
2f3: 61        illegal
2f4: f2 fa 0f  sbcb $FA0F
2f7: 00        illegal
2f8: 61        illegal
2f9: c1 61     cmpb #$61
2fb: e1 4e     cmpb $4E,x
2fd: 4c        inca 
2fe: 6b        illegal
2ff: 25 26     bcs  $0327
301: d1 aa     cmpb $AA
303: 38        illegal
304: 02        illegal
305: df be     stx  $BE
307: bd 05 9d  jsr  $059D
30a: 38        illegal
30b: 2b d1     bmi  $02DE
30d: b8 bc be  eora $BCBE
310: 06        tap  
311: 24 07     bcc  $031A
313: 2b b9     bmi  $02CE
315: bd bb 85  jsr  $BB85
318: f1 bc b4  cmpb $BCB4
31b: 21 71     brn  $038E
31d: 27 82     beq  $02A1
31f: ba 26 d1  ora  $26D1
322: aa 39     ora  $39,x
324: 06        tap  
325: df be     stx  $BE
327: bd 05 9d  jsr  $059D
32a: 38        illegal
32b: 01        nop  
32c: d1 bc     cmpb $BC
32e: bf f4 06  sts  $F406
331: 57        asrb 
332: e3        illegal
333: 1c        illegal
334: 08        inx  
335: a4 3b     anda $3B,x
337: f4 16 57  andb $1657
33a: ef fb     stx  $FB,x
33c: 00        illegal
33d: a4 31     anda $31,x
33f: ba 39 bd  ora  $39BD
342: d1 26     cmpb $26
344: ae 05     lds  $05,x
346: b5 06 d1  bita $06D1
349: 96 06     lda  $06
34b: df fd     stx  $FD
34d: 26 d1     bne  $0320
34f: aa be     ora  $BE,x
351: bd d1 b8  jsr  $D1B8
354: 39        rts  
355: 05        illegal
356: 9d 39     jsr  $39
358: bc be b9  cmpx $BEB9
35b: bd 2b 02  jsr  $2B02
35e: 22 07     bhi  $0367
360: bb 85 8c  adda $858C
363: 27 2b     beq  $0390
365: f1 bc b4  cmpb $BCB4
368: 3e        wai  
369: ba a6 26  ora  $A626
36c: 21 ff     brn  $036D
36e: 96 05     lda  $05
370: d1 aa     cmpb $AA
372: 39        rts  
373: 01        nop  
374: df be     stx  $BE
376: bd d1 9d  jsr  $D19D
379: 39        rts  
37a: 2b 02     bmi  $037E
37c: b8 bc be  eora $BCBE
37f: b9 20 07  adca $2007
382: 2b f1     bmi  $0375
384: bd bb 85  jsr  $BB85
387: 71        illegal
388: bc b4 21  cmpx $B421
38b: 27 27     beq  $03B4
38d: 87 ba     sta  #$BA
38f: 17        tba  
390: d1 aa     cmpb $AA
392: 39        rts  
393: 05        illegal
394: df be     stx  $BE
396: bd d1 9d  jsr  $D19D
399: 3d        illegal
39a: 38        illegal
39b: 06        tap  
39c: b8 bc bd  eora $BCBD
39f: 97 d1     sta  $D1
3a1: d1 d1     cmpb $D1
3a3: fb a9 93  addb $A993
3a6: 93        illegal
3a7: ba 39 bd  ora  $39BD
3aa: d1 27     cmpb $27
3ac: ae 05     lds  $05,x
3ae: b5 17 d1  bita $17D1
3b1: 96 f1     lda  $F1
3b3: 07        tpa  
3b4: fd        illegal
3b5: 27 e4     beq  $039B
3b7: b8 00 e9  eora $00E9
3ba: 3f        swi  
3bb: 3d        illegal
3bc: f1 be b9  cmpb $BEB9
3bf: d1 c2     cmpb $C2
3c1: 06        tap  
3c2: 3d        illegal
3c3: 3d        illegal
3c4: b9 b8 bc  adca $B8BC
3c7: bd 06 d1  jsr  $06D1
3ca: e9 bc     adcb $BC,x
3cc: 97 a9     sta  $A9
3ce: c6 27     ldb  #$27
3d0: f4 b4 db  andb $B4DB
3d3: d6 d6     ldb  $D6
3d5: c3        illegal
3d6: f4 0f c3  andb $0FC3
3d9: bc b4 96  cmpx $B496
3dc: db 27     addb $27
3de: 00        illegal
3df: 26 05     bne  $03E6
3e1: e4 db     andb $DB,x
3e3: 3e        wai  
3e4: f1 d2 be  cmpb $D2BE
3e7: b9 3c c2  adca $3CC2
3ea: 38        illegal
3eb: a4 d1     anda $D1,x
3ed: bc 27 1c  cmpx $271C
3f0: bf f4 a4  sts  $F4A4
3f3: ef 06     stx  $06,x
3f5: 47        asra 
3f6: 1c        illegal
3f7: f2 27 cc  sbcb $27CC
3fa: 3a        illegal
3fb: 34        des  
3fc: a4 b8     anda $B8,x
3fe: f0 c8 cc  subb $C8CC
401: 34        des  
402: 17        tba  
403: df f0     stx  $F0
405: 27 d1     beq  $03D8
407: ba 39 bd  ora  $39BD
40a: d1 96     cmpb $96
40c: ae 05     lds  $05,x
40e: b5 be 3e  bita $BE3E
411: 3c        illegal
412: c2 3c     sbcb #$3C
414: b9 d1 bc  adca $D1BC
417: f4 85 19  andb $8519
41a: b8 bc c3  eora $BCC3
41d: 95 3e     bita $3E
41f: 2b be     bmi  $03DF
421: bd b3 ce  jsr  $B3CE
424: 06        tap  
425: 06        tap  
426: 28 ce     bvc  $03F6
428: b9 bb 85  adca $BB85
42b: 8c 2c 2b  cmpx #$2C2B
42e: f1 27 17  cmpb $2717
431: df be     stx  $BE
433: bd d1 aa  jsr  $D1AA
436: 39        rts  
437: 05        illegal
438: d1 b8     cmpb $B8
43a: bc be 9d  cmpx $BE9D
43d: 39        rts  
43e: 2e 06     bgt  $0446
440: b9 bd bb  adca $BDBB
443: 85 21     bita #$21
445: 01        nop  
446: 2e f1     bgt  $0439
448: 8c 28 01  cmpx #$2801
44b: 56        rorb 
44c: bc bf f4  cmpx $BFF4
44f: 0f        sei  
450: c3        illegal
451: d6 93     ldb  $93
453: 1c        illegal
454: 53        comb 
455: 0f        sei  
456: 62        illegal
457: ef 4d     stx  $4D,x
459: 28 01     bvc  $045C
45b: 0f        sei  
45c: bc bf b4  cmpx $BFB4
45f: 1c        illegal
460: ef 21     stx  $21,x
462: 27 d1     beq  $0435
464: 5d        tstb 
465: ba 17 df  ora  $17DF
468: aa 39     ora  $39,x
46a: 01        nop  
46b: 9d be     jsr  $BE
46d: bd d1 bc  jsr  $D1BC
470: 3c        illegal
471: 56        rorb 
472: a4 02     anda $02,x
474: f4 f0 26  andb $F026
477: d1 df     cmpb $DF
479: be bd d1  lds  $BDD1
47c: aa 38     ora  $38,x
47e: 05        illegal
47f: 9d b8     jsr  $B8
481: bc bd 97  cmpx $BD97
484: 3c        illegal
485: 31        ins  
486: 01        nop  
487: d1 a9     cmpb $A9
489: 93        illegal
48a: ba ae d1  ora  $AED1
48d: fb 38 bd  addb $38BD
490: 05        illegal
491: b5 02 fd  bita $02FD
494: d1 26     cmpb $26
496: d1 26     cmpb $26
498: 05        illegal
499: df be     stx  $BE
49b: bd d1 aa  jsr  $D1AA
49e: 39        rts  
49f: 01        nop  
4a0: d1 bc     cmpb $BC
4a2: bf 97 9d  sts  $979D
4a5: 38        illegal
4a6: 01        nop  
4a7: a7 1c     sta  $1C,x
4a9: 16        tab  
4aa: 57        asrb 
4ab: e3        illegal
4ac: f4 00 a4  andb $00A4
4af: b2 ef fb  sbca $EFFB
4b2: 39        rts  
4b3: bd a8 ba  jsr  $A8BA
4b6: ae 01     lds  $01,x
4b8: d1 26     cmpb $26
4ba: d1 be     cmpb $BE
4bc: b5 05 fd  bita $05FD
4bf: 3c        illegal
4c0: b9 fe 27  adca $FE27
4c3: e9 0a     adcb $0A,x
4c5: a8 f1     eora $F1,x
4c7: ce e9 71  ldx  #$E971
4ca: 26 f1     bne  $04BD
4cc: c2 da     sbcb #$DA
4ce: 0e        cli  
4cf: e4 07     andb $07,x
4d1: d8 f1     eorb $F1
4d3: ec        illegal
4d4: 93        illegal
4d5: ac f1     cmpx $F1,x
4d7: d1 b8     cmpb $B8
4d9: f1 96 a6  cmpb $96A6
4dc: 0e        cli  
4dd: e9 ff     adcb $FF,x
4df: 96 26     lda  $26
4e1: f1 17 d6  cmpb $17D6
4e4: 06        tap  
4e5: e4 af     andb $AF,x
4e7: 03        illegal
4e8: 93        illegal
4e9: 71        illegal
4ea: 27 f0     beq  $04DC
4ec: ef da     stx  $DA,x
4ee: 81 ff     cmpa #$FF
4f0: b8 f1 96  eora $F196
4f3: f1 06 e9  cmpb $06E9
4f6: 53        comb 
4f7: 11        cba  
4f8: d6 f1     ldb  $F1
4fa: 01        nop  
4fb: e4 c3     andb $C3,x
4fd: 26 f1     bne  $04F0
4ff: 07        tpa  
500: c3        illegal
501: b8 f1 96  eora $F196
504: 07        tpa  
505: 01        nop  
506: e9 f1     adcb $F1,x
508: c8 27     eorb #$27
50a: b4 72 bc  anda $72BC
50d: f4 10 12  andb $1012
510: b4 11 71  anda $1171
513: 96 08     lda  $08
515: bc 8b 11  cmpx $8B11
518: d6 23     ldb  $23
51a: 03        illegal
51b: e4 c3     andb $C3,x
51d: 26 f1     bne  $0510
51f: 07        tpa  
520: c3        illegal
521: b8 f1 96  eora $F196
524: 27 03     beq  $0529
526: e9 26     adcb $26,x
528: 01        nop  
529: df be     stx  $BE
52b: bd d1 aa  jsr  $D1AA
52e: 39        rts  
52f: 01        nop  
530: d1 bc     cmpb $BC
532: bf 97 9d  sts  $979D
535: 38        illegal
536: 01        nop  
537: a7 1c     sta  $1C,x
539: 16        tab  
53a: 57        asrb 
53b: e3        illegal
53c: f4 00 a4  andb $00A4
53f: 42        illegal
540: ef fb     stx  $FB,x
542: 39        rts  
543: bd 38 ba  jsr  $38BA
546: ae 01     lds  $01,x
548: d1 26     cmpb $26
54a: d1 26     cmpb $26
54c: b5 01 fd  bita $01FD
54f: 48        asla 
550: a1 bc     cmpa $BC,x
552: f4 82 22  andb $8222
555: 02        illegal
556: d2 d6     sbcb $D6
558: 40        nega 
559: 27 e4     beq  $053F
55b: 39        rts  
55c: a4 f1     anda $F1,x
55e: ba 12 66  ora  $1266
561: 3f        swi  
562: 39        rts  
563: 06        tap  
564: ba be bd  ora  $BEBD
567: d1 9d     cmpb $9D
569: 39        rts  
56a: 56        rorb 
56b: a4 bc     anda $BC,x
56d: f4 0f b8  andb $0FB8
570: 39        rts  
571: 3c        illegal
572: 06        tap  
573: a4 bc     anda $BC,x
575: bf f0 c8  sts  $F0C8
578: cc        illegal
579: 75        illegal
57a: 31        ins  
57b: 3a        illegal
57c: ef bc     stx  $BC,x
57e: b4 1c b4  anda $1CB4
581: bc f4 95  cmpx $F495
584: 05        illegal
585: 32        pula 
586: 12        illegal
587: b1 8e ce  cmpa $8ECE
58a: 31        ins  
58b: ac a1     cmpx $A1,x
58d: bc f4 06  cmpx $F406
590: fd        illegal
591: f0 96 03  subb $9603
594: a8 a4     eora $A4,x
596: f1 d6 04  cmpb $D604
599: 93        illegal
59a: 95 c8     bita $C8
59c: 85 9f     bita #$9F
59e: f1 95 bc  cmpb $95BC
5a1: f4 b3 07  andb $B307
5a4: 35        txs  
5a5: af bc     sts  $BC,x
5a7: 93        illegal
5a8: ae f5     lds  $F5,x
5aa: 37        pshb 
5ab: ce a1 a4  ldx  #$A1A4
5ae: 12        illegal
5af: b1 8e 31  cmpa $8E31
5b2: a1 ff     cmpa $FF,x
5b4: bc 14 ce  cmpx $14CE
5b7: a6 96     lda  $96,x
5b9: 31        ins  
5ba: a8 f4     eora $F4,x
5bc: bc f4 ac  cmpx $F4AC
5bf: 2f 12     ble  $05D3
5c1: 2f f0     ble  $05B3
5c3: ca c7     orb  #$C7
5c5: 46        rora 
5c6: a1 2f     cmpa $2F,x
5c8: 46        rora 
5c9: a0 03     suba $03,x
5cb: 06        tap  
5cc: 0f        sei  
5cd: f1 d6 93  cmpb $D693
5d0: b8 c8 b4  eora $C8B4
5d3: cc        illegal
5d4: f1 cc fb  cmpb $CCFB
5d7: b4 ff 31  anda $FF31
5da: 06        tap  
5db: a8 bc     eora $BC,x
5dd: f4 fd ac  andb $FDAC
5e0: f4 bc f4  andb $BCF4
5e3: ed        illegal
5e4: af 35     sts  $35,x
5e6: 12        illegal
5e7: ff 06 57  stx  $0657
5ea: 96 47     lda  $47
5ec: 0a        clv  
5ed: a0 ff     suba $FF,x
5ef: 06        tap  
5f0: 0a        clv  
5f1: 47        asra 
5f2: 96 02     lda  $02
5f4: 57        asrb 
5f5: a0 bc     suba $BC,x
5f7: f4 56 a4  andb $56A4
5fa: f1 46 9f  cmpb $469F
5fd: 27 e4     beq  $05E3
5ff: 02        illegal
600: ad 00     jsr  $00,x
602: e9 39     adcb $39,x
604: b8 f1 be  eora $F1BE
607: fd        illegal
608: 12        illegal
609: be ba bd  lds  $BABD
60c: 09        dex  
60d: 3f        swi  
60e: 3c        illegal
60f: 06        tap  
610: d1 71     cmpb $71
612: 96 39     lda  $39
614: b5 be b8  bita $BEB8
617: bc 2b 04  cmpx $2B04
61a: 27 06     beq  $0622
61c: be b9 bd  lds  $B9BD
61f: bb 2e f1  adda $2EF1
622: b8 bc 85  eora $BC85
625: 8c 3a 2c  cmpx #$3A2C
628: be b9 bd  lds  $B9BD
62b: bb 04 28  adda $0428
62e: 02        illegal
62f: 2a 85     bpl  $05B6
631: 71        illegal
632: 2e 0f     bgt  $0643
634: f1 bc b4  cmpb $BCB4
637: cc        illegal
638: b4 bc b8  anda $BCB8
63b: f0 1f 27  subb $1F27
63e: 32        pula 
63f: bf 00 45  sts  $0045
642: 2f a4     ble  $05E8
644: 12        illegal
645: bf ff 21  sts  $FF21
648: ba 01 df  ora  $01DF
64b: be 26 d1  lds  $26D1
64e: aa 39     ora  $39,x
650: bd d1 b8  jsr  $D1B8
653: bc 01 9d  cmpx $019D
656: 39        rts  
657: 2b be     bmi  $0617
659: b9 bd bb  adca $BDBB
65c: 04        illegal
65d: 26 07     bne  $0666
65f: 2b 85     bmi  $05E6
661: 8c 27 9e  cmpx #$279E
664: f1 bc b4  cmpb $BCB4
667: 21 ba     brn  $0623
669: 84 3a     anda #$3A
66b: ff 83 84  stx  $8384
66e: ff ff 39  stx  $FF39
671: 84 3a     anda #$3A
673: ff b9 8c  stx  $B98C
676: ff ff 39  stx  $FF39
679: 29 9c     bvs  $0617
67b: 39        rts  
67c: 9c b5     cmpx $B5
67e: ff ab ff  stx  $ABFF
681: fa 6c bc  orb  $6CBC
684: e1 06     cmpb $06,x
686: a8 27     eora $27,x
688: bf f8 17  sts  $F817
68b: c8 08     eorb #$08
68d: a6 a4     lda  $A4,x
68f: cc        illegal
690: ef 96     stx  $96,x
692: a6 f4     lda  $F4,x
694: 8a ff     ora  #$FF
696: 96 16     lda  $16
698: 00        illegal
699: a4 86     anda $86,x
69b: f1 57 1c  cmpb $571C
69e: fa e4 06  orb  $E406
6a1: 57        asrb 
6a2: ac a4     cmpx $A4,x
6a4: 00        illegal
6a5: 2e 2e     bgt  $06D5
6a7: ca ce     orb  #$CE
6a9: 9d f4     jsr  $F4
6ab: 57        asrb 
6ac: ed        illegal
6ad: 96 70     lda  $70
6af: a4 18     anda $18,x
6b1: ed        illegal
6b2: 86 ac     lda  #$AC
6b4: 1c        illegal
6b5: a9 fa     adca $FA,x
6b7: f4 2e 2e  andb $2E2E
6ba: e9 ce     adcb $CE,x
6bc: a8 f1     eora $F1,x
6be: ca ed     orb  #$ED
6c0: b5 27 e4  bita $27E4
6c3: 32        pula 
6c4: 96 f1     lda  $F1
6c6: 85 cc     bita #$CC
6c8: 95 39     bita $39
6ca: cf 3f ba  stx  #$3FBA
6cd: 12        illegal
6ce: ba bd 06  ora  $BD06
6d1: 9d d3     jsr  $D3
6d3: f9 d1 b3  adcb $D1B3
6d6: 96 a8     lda  $A8
6d8: ac 06     cmpx $06,x
6da: d1 96     cmpb $96
6dc: bd 97 a9  jsr  $97A9
6df: ab e7     adda $E7,x
6e1: d1 59     cmpb $59
6e3: ec        illegal
6e4: ad f2     jsr  $F2,x
6e6: c3        illegal
6e7: 27 17     beq  $0700
6e9: d6 f1     ldb  $F1
6eb: 2b ab     bmi  $0698
6ed: 04        illegal
6ee: 20 f1     bra  $06E1
6f0: 20 27     bra  $0719
6f2: f1 a9 96  cmpb $A996
6f5: 17        tba  
6f6: e4 26     andb $26,x
6f8: 80 eb     suba #$EB
6fa: 96 d1     lda  $D1
6fc: e7 fc     stb  $FC,x
6fe: ab f2     adda $F2,x
700: d9 04     adcb $04
702: e9 bc     adcb $BC,x
704: b8 f1 96  eora $F196
707: 36        psha 
708: f4 6f f1  andb $6FF1
70b: 12        illegal
70c: 96 af     lda  $AF
70e: dc        illegal
70f: 0a        clv  
710: 52        illegal
711: ff 3c 2f  stx  $3C2F
714: 0a        clv  
715: 96 31     lda  $31
717: 2a 25     bpl  $073E
719: 1e        illegal
71a: 16        tab  
71b: e1 20     cmpb $20,x
71d: 17        tba  
71e: 0f        sei  
71f: fa 6d 12  orb  $6D12
722: 96 05     lda  $05
724: 06        tap  
725: a6 26     lda  $26,x
727: f1 e4 00  cmpb $E400
72a: b8 b0 06  eora $B006
72d: 57        asrb 
72e: 39        rts  
72f: 00        illegal
730: c8 c8     eorb #$C8
732: 31        ins  
733: bc a0 b0  cmpx $A0B0
736: c8 1d     eorb #$1D
738: 11        cba  
739: 06        tap  
73a: 57        asrb 
73b: 42        illegal
73c: b0 06 33  suba $0633
73f: 06        tap  
740: 50        negb 
741: a0 39     suba $39,x
743: 2b 57     bmi  $079C
745: b8 bc be  eora $BCBE
748: 04        illegal
749: 27 07     beq  $0752
74b: 2b b9     bmi  $0706
74d: bd bb 85  jsr  $BB85
750: f1 bc b4  cmpb $BCB4
753: f1 8c 27  cmpb $8C27
756: af 03     sts  $03,x
758: d6 93     ldb  $93
75a: bc 11 06  cmpx $1106
75d: 61        illegal
75e: 1d        illegal
75f: b0 17 f1  suba $17F1
762: f1 d6 94  cmpb $D694
765: c8 03     eorb #$03
767: 02        illegal
768: 93        illegal
769: b8 80 3f  eora $803F
76c: 72        illegal
76d: 2e 17     bgt  $0786
76f: 90 f1     suba $F1
771: 21 19     brn  $078C
773: 56        rorb 
774: c8 ba     eorb #$BA
776: f0 f0 b3  subb $F0B3
779: ee 95     ldx  $95,x
77b: 82 82     sbca #$82
77d: 7f e1 c3  clr  $E1C3
780: 8c 47 ed  cmpx #$47ED
783: e1 95     cmpb $95,x
785: a4 88     anda $88,x
787: a0 cc     suba $CC,x
789: f0 0f 97  subb $0F97
78c: 19        daa  
78d: 56        rorb 
78e: b3        illegal
78f: ee 91     ldx  $91,x
791: e1 c3     cmpb $C3,x
793: 95 95     bita $95
795: 97 9d     sta  $9D
797: a4 ed     anda $ED,x
799: e1 cc     cmpb $CC,x
79b: e1 99     cmpb $99,x
79d: a0 c8     suba $C8,x
79f: 71        illegal
7a0: fb f4 a9  addb $F4A9
7a3: 0f        sei  
7a4: ac 93     cmpx $93,x
7a6: b4 fb cb  anda $FBCB
7a9: 93        illegal
7aa: 27 f9     beq  $07A5
7ac: d9 a0     adcb $A0
7ae: af d6     sts  $D6,x
7b0: 28 b1     bvc  $0763
7b2: f9 29 93  adcb $2993
7b5: 1f        illegal
7b6: d6 93     ldb  $93
7b8: ba ff c6  ora  $FFC6
7bb: ac 1f     cmpx $1F,x
7bd: 93        illegal
7be: f9 f4 06  adcb $F406
7c1: a4 a7     anda $A7,x
7c3: fa 10 11  orb  $1011
7c6: 93        illegal
7c7: 96 bc     lda  $BC
7c9: b4 96 a6  anda $96A6
7cc: 36        psha 
7cd: ff ff 96  stx  $FF96
7d0: f2 d2 e7  sbcb $D2E7
7d3: e7 fa     stb  $FA,x
7d5: fa 17 ac  orb  $17AC
7d8: 86 03     lda  #$03
7da: c3        illegal
7db: f1 f1 17  cmpb $F117
7de: dc        illegal
7df: c8 96     eorb #$96
7e1: d0 b0     subb $B0
7e3: 1c        illegal
7e4: f1 11 a8  cmpb $11A8
7e7: 11        cba  
7e8: b0 68 28  suba $6828
7eb: d0 47     subb $47
7ed: 86 f1     lda  #$F1
7ef: f8 3f 1c  eorb $3F1C
7f2: 3f        swi  
7f3: 86 94     lda  #$94
7f5: 47        asra 
7f6: 94 71     anda $71
7f8: 9d 26     jsr  $26
7fa: 3a        illegal
7fb: e8 94     eorb $94,x
7fd: 4f        clra 
7fe: 01        nop  
7ff: ff ff d5  stx  $0000
