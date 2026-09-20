000: ff d5 9e     STU    $D59E
003: b4 21 01     ANDA   $2101
006: fb c5 bc     ADDB   $C5BC
009: a4 56        ANDA   -$A,U
00b: c3 30 fb     ADDD   #$30FB
00e: f8 12 e1     EORB   $12E1
011: 26 62        BNE    $0075
013: 6f fa        CLR    [F,S]
015: e4 26        ANDB   $6,Y
017: 3a           ABX
018: 8c 0c 26     CMPX   #$0C26
01b: 3a           ABX
01c: ff ae 5f     STU    $AE5F
01f: b8 2e 12     EORA   $2E12
022: c8 17        EORB   #$17
024: 80 2e        SUBA   #$2E
026: 80 3f        SUBA   #$3F
028: 90 44        SUBA   <$44
02a: f2 fb 52     SBCB   $FB52
02d: fa 44 06     ORB    $4406
030: 1f 06        TFR    D,inv
032: ac 3c        CMPX   -$4,Y
034: a8 01        EORA   $1,X
036: f4 8a df     ANDB   $8ADF
039: 5f           CLRB
03a: 3c 07        CWAI   #$07
03c: 9a f0        ORA    <$F0
03e: fb 47 3a     ADDB   $473A
041: 77 01 48     ASR    $0148
044: eb bb        ADDB   [D,Y]
046: 83 05 85     SUBD   #$0585
049: fe 06 5e     LDU    $065E
04c: 95 bc        BITA   <$BC
04e: 52           XNCB
04f: b3 57 46     SUBD   $5746
052: aa 72        ORA    -$E,S
054: fa 80 01     ORB    $8001
057: 95 2e        BITA   <$2E
059: 2e 77        BGT    $00D2
05b: 4d           TSTA
05c: fc 77 ec     LDD    $77EC
05f: fa 56 aa     ORB    $56AA
062: 71 72 7f     NEG    $727F
065: b3 ef fe     SUBD   $EFFE
068: bc 53 d6     CMPX   $53D6
06b: c3 36 74     ADDD   #$3674
06e: 04 74        LSR    <$74
070: fe bf ef     LDU    $BFEF
073: 1f a4        TFR    CC,S
075: 07 77        ASR    <$77
077: bc 34 07     CMPX   $3407
07a: 93 26        SUBD   <$26
07c: f4 a4 87     ANDB   $A487
07f: 95 a4        BITA   <$A4
081: 14           XHCF
082: 46           RORA
083: aa 1c        ORA    -$4,X
085: fa 08 bc     ORB    $08BC
088: 2f 07        BLE    $0091
08a: 8f 95 f4     XSTX   #$95F4
08d: c3 01 fa     ADDD   #$01FA
090: 46           RORA
091: aa 8f        ORA    ,W
093: bc 10 26     CMPX   $1026
096: a4 30        ANDA   -$10,Y
098: f4 96 15     ANDB   $9615
09b: cd           XHCF
09c: 3f           SWI
09d: c5 c9        BITB   #$C9
09f: 3f           SWI
0a0: 96 ae        LDA    <$AE
0a2: ff 96 6e     STU    $966E
0a5: 96 a6        LDA    <$A6
0a7: 26 0c        BNE    $00B5
0a9: e4 0f        ANDB   $F,X
0ab: 03 f1        COM    <$F1
0ad: 56           RORB
0ae: d6 86        LDB    <$86
0b0: 84 0f        ANDA   #$0F
0b2: b8 f1 56     EORA   $F156
0b5: 86 02        LDA    #$02
0b7: e9 96        ADCB   [A,X]
0b9: 08 bf        ASL    <$BF
0bb: 05 26        LSR    <$26
0bd: 33 26        LEAU   $6,Y
0bf: b8 01 bc     EORA   $01BC
0c2: b4 bc a0     ANDA   $BCA0
0c5: 2f 8f        BLE    $0056
0c7: 1d           SEX
0c8: 11 06 b8     ROR    <$B8
0cb: f1 b0 06     CMPB   $B006
0ce: 01 e9        NEG    <$E9
0d0: 96 4a        LDA    <$4A
0d2: 02 e4        XNC    <$E4
0d4: 21 26        BRN    $00FC
0d6: f1 96 26     CMPB   $9626
0d9: bc a4 b4     CMPX   $A4B4
0dc: f8 0c cc     EORB   $0CCC
0df: a7 bc a4     STA    [$0086,PCR]
0e2: b4 42 17     ANDA   $4217
0e5: cc d4 96     LDD    #$D496
0e8: 27 b8        BEQ    $00A2
0ea: a0 e9 d7 3f  SUBA   -$28C1,S
0ee: e8 26        EORB   $6,Y
0f0: 01 af        NEG    <$AF
0f2: e4 d5        ANDB   [B,U]
0f4: ab 26        ADDA   $6,Y
0f6: 62 55        XNC    -$B,U
0f8: 25 fb        BCS    $00F5
0fa: eb ef        ADDB   ,--W
0fc: fb fb fc     ADDB   $FBFC
0ff: fc fb 43     LDD    $FB43
102: 17 86 43     LBSR   $8748
105: 26 d1        BNE    $00D8
107: bf 05 a1     STX    $05A1
10a: 0e 27        JMP    <$27
10c: 11 b8 ad af  EORA   $ADAF
110: ae e9 b3 a4  LDX    -$4C5C,S
114: f1 b1 11     CMPB   $B111
117: 91 dd        CMPA   <$DD
119: a4 96        ANDA   [A,X]
11b: a4 11        ANDA   -$F,X
11d: d1 11        CMPB   <$11
11f: 71 6e a4     NEG    $6EA4
122: a1 a4        CMPA   ,Y
124: 11           FCB    $11
125: 11           FCB    $11
126: 11 51        NEGB
128: a1 a4        CMPA   ,Y
12a: a7 a4        STA    ,Y
12c: 11 31 11     LEAY   -$F,X
12f: ef 16        STU    -$A,X
131: cd           XHCF
132: a4 af f1 11  ANDA   -$0EEF,W
136: 2d fd        BLT    $0135
138: f1 11 ef     CMPB   $11EF
13b: c3 cd a4     ADDD   #$CDA4
13e: 38 43        XANDCC #$43
140: 26 d1        BNE    $0113
142: 21 f1        BRN    $0135
144: 0f 86        CLR    <$86
146: 07 c8        ASR    <$C8
148: 11 93 71     CMPU   <$71
14b: 43           COMA
14c: d8 51        EORB   <$51
14e: be aa f1     LDX    $AAF1
151: 21 bf        BRN    $0112
153: ff dc aa     STU    $DCAA
156: 3f           SWI
157: a8 f1        EORA   [,S++]
159: ef bf ff e9  STU    [$FFE9]
15d: 53           COMB
15e: 3f           SWI
15f: d6 0a        LDB    <$0A
161: 6f f1        CLR    [,S++]
163: df c3        STU    <$C3
165: ff e4 c3     STU    $E4C3
168: 6f 07        CLR    $7,X
16a: 86 51        LDA    #$51
16c: 26 d1        BNE    $013F
16e: 21 ff        BRN    $016F
170: a8 f1        EORA   [,S++]
172: ef 26        STU    $6,Y
174: 27 e9        BEQ    $015F
176: 5b           XDECB
177: 06 bc        ROR    <$BC
179: 94 3f        ANDA   <$3F
17b: 03 1d        COM    <$1D
17d: 26 b8        BNE    $0137
17f: f1 e9 02     CMPB   $E902
182: 3e           XRES
183: e9 26        ADCB   $6,Y
185: b8 f1 26     EORA   $F126
188: 06 3b        ROR    <$3B
18a: e9 ff b8 f1  ADCB   [$B8F1]
18e: 26 b8        BNE    $0148
190: 00 e9        NEG    <$E9
192: 15           XHCF
193: 07 f1        ASR    <$F1
195: b8 ff f1     EORA   $FFF1
198: 0a c8        DEC    <$C8
19a: 0a ee        DEC    <$EE
19c: a0 f1        SUBA   [,S++]
19e: 06 a0        ROR    <$A0
1a0: f1 06 ac     CMPB   $06AC
1a3: 96 0a        LDA    <$0A
1a5: eb cf        ADDB   ,W++
1a7: ff a6 42     STU    $A642
1aa: c3 8c 96     ADDD   #$8C96
1ad: 17 aa ff     LBSR   $ACAF
1b0: 8a 0c        ORA    #$0C
1b2: b8 f1 7f     EORA   $F17F
1b5: 37 05        PULU   CC,B
1b7: e9 11        ADCB   -$F,X
1b9: ba bc f4     ORA    $BCF4
1bc: bc 07 32     CMPX   $0732
1bf: be 0f c5     LDX    $0FC5
1c2: 1f 28        TFR    Y,A
1c4: 12           NOP
1c5: be bc b8     LDX    $BCB8
1c8: 20 ed        BRA    $01B7
1ca: 84 9a        ANDA   #$9A
1cc: 21 bd        BRN    $018B
1ce: 3a           ABX
1cf: 83 99 8c     SUBD   #$998C
1d2: 9b 23        ADDA   <$23
1d4: b9 bb bc     ADCA   $BBBC
1d7: fc 21 ff     LDD    $21FF
1da: c4 da        ANDB   #$DA
1dc: e5 fd 7a c3  BITB   [$7CA3,PCR]
1e0: d9 cc        ADCB   <$CC
1e2: db 94        ADDB   <$94
1e4: f9 fb 3f     ADCB   $FB3F
1e7: 01 e8        NEG    <$E8
1e9: 3f           SWI
1ea: fa 56 ff     ORB    $56FF
1ed: e1 f4        CMPB   [,S]
1ef: e0 c3        SUBB   ,--U
1f1: e1 f4        CMPB   [,S]
1f3: 06 f1        ROR    <$F1
1f5: fa 5e ce     ORB    $5ECE
1f8: a6 a0        LDA    ,Y+
1fa: 1c ed        ANDCC  #$ED
1fc: 17 18 ea     LBSR   $1AE9
1ff: 26 06        BNE    $0207
201: e4 05        ANDB   $5,X
203: 0c f1        INC    <$F1
205: d6 93        LDB    <$93
207: 41           NEGA
208: 25 d6        BCS    $01E0
20a: 17 02 11     LBSR   $041E
20d: 93 bc        SUBD   <$BC
20f: f4 37 17     ANDB   $3717
212: 52           XNCB
213: 15           XHCF
214: b2 b1 c1     SBCA   $B1C1
217: f1 03 06     CMPB   $0306
21a: 25 02        BCS    $021E
21c: d6 93        LDB    <$93
21e: bc f4 d6     CMPX   $F4D6
221: a4 c8 02     ANDA   $02,U
224: 20 f1        BRA    $0217
226: bc f4 37     CMPX   $F437
229: 30 f7        LEAX   [E,S]
22b: b1 72 d6     CMPA   $72D6
22e: a4 17        ANDA   -$9,X
230: bc f4 92     CMPX   $F492
233: d6 02        LDB    <$02
235: 37 3e        PULU   D,DP,X,Y
237: ef a4        STU    ,Y
239: f5 d6 32     BITB   $D632
23c: 91 11        CMPA   <$11
23e: ad 56        JSR    -$A,U
240: 53           COMB
241: 93 17        SUBD   <$17
243: b1 a7 56     CMPA   $A756
246: 11 71 df bc  NEG    $DFBC
24a: da 05        ORB    <$05
24c: 11 71 bc b4  NEG    $BCB4
250: 04 d9        LSR    <$D9
252: 05 93        LSR    <$93
254: 41           NEGA
255: bc f4 64     CMPX   $F464
258: 26 33        BNE    $028D
25a: 26 a4        BNE    $0200
25c: 08 5b        ASL    <$5B
25e: 05 71        LSR    <$71
260: 20 01        BRA    $0263
262: c3 53 bc     ADDD   #$53BC
265: f4 6a ac     ANDB   $6AAC
268: 41           NEGA
269: 11 26 11     BNE    $027D
26c: e4 bc 02     ANDB   [$0271,PCR]
26f: b1 26 f1     CMPA   $26F1
272: af 0f        STX    $F,X
274: 05 e4        LSR    <$E4
276: 56           RORB
277: c3 95 07     ADDD   #$9507
27a: e4 ab        ANDB   D,Y
27c: 26 f1        BNE    $026F
27e: 07 b8        ASR    <$B8
280: 07 e9        ASR    <$E9
282: 93 ff        SUBD   <$FF
284: f1 fb 95     CMPB   $FB95
287: 56           RORB
288: 0f 06        CLR    <$06
28a: b8 f1 47     EORA   $F147
28d: fd 07 e9     STD    $07E9
290: ff 97 8b     STU    $978B
293: 8b b2        ADDA   #$B2
295: 71 71 bc     NEG    $71BC
298: 27 72        BEQ    $030C
29a: b4 41 f4     ANDA   $41F4
29d: a0 0f        SUBA   $F,X
29f: d2 b4        SBCB   <$B4
2a1: 41           NEGA
2a2: ff 96 b4     STU    $96B4
2a5: d2 a6        SBCB   <$A6
2a7: c3 c0 03     ADDD   #$C003
2aa: 04 e4        LSR    <$E4
2ac: f1 d6 93     CMPB   $D693
2af: b4 ff 11     ANDA   $FF11
2b2: fd bc 27     STD    $BC27
2b5: b1 32 91     CMPA   $3291
2b8: bb 12 91     ADDA   $1291
2bb: 71 fd c0     NEG    $FDC0
2be: 61 be        NEG    [W,Y]
2c0: f1 d6 93     CMPB   $D693
2c3: b4 03 04     ANDA   $0304
2c6: ca ff        ORB    #$FF
2c8: 91 26        CMPA   <$26
2ca: f1 d6 e0     CMPB   $D6E0
2cd: 06 e4        ROR    <$E4
2cf: 05 c3        LSR    <$C3
2d1: f1 d6 93     CMPB   $D693
2d4: e4 03        ANDB   $3,X
2d6: 02 e4        XNC    <$E4
2d8: b4 71 27     ANDA   $7127
2db: 06 ff        ROR    <$FF
2dd: b6 b8 f1     LDA    $B8F1
2e0: e9 06        ADCB   $6,X
2e2: e4 07        ANDB   $7,X
2e4: 26 f1        BNE    $02D7
2e6: 56           RORB
2e7: 06 ea        ROR    <$EA
2e9: f1 f8 f9     CMPB   $F8F9
2ec: b6 f3 fa     LDA    $F3FA
2ef: fb f2 e1     ADDB   $F2E1
2f2: 81 61        CMPA   #$61
2f4: f2 fa 0f     SBCB   $FA0F
2f7: 00 61        NEG    <$61
2f9: c1 61        CMPB   #$61
2fb: e1 4e        CMPB   $E,U
2fd: 4c           INCA
2fe: 6b 25        XDEC   $5,Y
300: 26 d1        BNE    $02D3
302: aa 38        ORA    -$8,Y
304: 02 df        XNC    <$DF
306: be bd 05     LDX    $BD05
309: 9d 38        JSR    <$38
30b: 2b d1        BMI    $02DE
30d: b8 bc be     EORA   $BCBE
310: 06 24        ROR    <$24
312: 07 2b        ASR    <$2B
314: b9 bd bb     ADCA   $BDBB
317: 85 f1        BITA   #$F1
319: bc b4 21     CMPX   $B421
31c: 71 27 82     NEG    $2782
31f: ba 26 d1     ORA    $26D1
322: aa 39        ORA    -$7,Y
324: 06 df        ROR    <$DF
326: be bd 05     LDX    $BD05
329: 9d 38        JSR    <$38
32b: 01 d1        NEG    <$D1
32d: bc bf f4     CMPX   $BFF4
330: 06 57        ROR    <$57
332: e3 1c        ADDD   -$4,X
334: 08 a4        ASL    <$A4
336: 3b           RTI
337: f4 16 57     ANDB   $1657
33a: ef fb        STU    [D,S]
33c: 00 a4        NEG    <$A4
33e: 31 ba        LEAY   [F,Y]
340: 39           RTS
341: bd d1 26     JSR    $D126
344: ae 05        LDX    $5,X
346: b5 06 d1     BITA   $06D1
349: 96 06        LDA    <$06
34b: df fd        STU    <$FD
34d: 26 d1        BNE    $0320
34f: aa be        ORA    [W,Y]
351: bd d1 b8     JSR    $D1B8
354: 39           RTS
355: 05 9d        LSR    <$9D
357: 39           RTS
358: bc be b9     CMPX   $BEB9
35b: bd 2b 02     JSR    $2B02
35e: 22 07        BHI    $0367
360: bb 85 8c     ADDA   $858C
363: 27 2b        BEQ    $0390
365: f1 bc b4     CMPB   $BCB4
368: 3e           XRES
369: ba a6 26     ORA    $A626
36c: 21 ff        BRN    $036D
36e: 96 05        LDA    <$05
370: d1 aa        CMPB   <$AA
372: 39           RTS
373: 01 df        NEG    <$DF
375: be bd d1     LDX    $BDD1
378: 9d 39        JSR    <$39
37a: 2b 02        BMI    $037E
37c: b8 bc be     EORA   $BCBE
37f: b9 20 07     ADCA   $2007
382: 2b f1        BMI    $0375
384: bd bb 85     JSR    $BB85
387: 71 bc b4     NEG    $BCB4
38a: 21 27        BRN    $03B3
38c: 27 87        BEQ    $0315
38e: ba 17 d1     ORA    $17D1
391: aa 39        ORA    -$7,Y
393: 05 df        LSR    <$DF
395: be bd d1     LDX    $BDD1
398: 9d 3d        JSR    <$3D
39a: 38 06        XANDCC #$06
39c: b8 bc bd     EORA   $BCBD
39f: 97 d1        STA    <$D1
3a1: d1 d1        CMPB   <$D1
3a3: fb a9 93     ADDB   $A993
3a6: 93 ba        SUBD   <$BA
3a8: 39           RTS
3a9: bd d1 27     JSR    $D127
3ac: ae 05        LDX    $5,X
3ae: b5 17 d1     BITA   $17D1
3b1: 96 f1        LDA    <$F1
3b3: 07 fd        ASR    <$FD
3b5: 27 e4        BEQ    $039B
3b7: b8 00 e9     EORA   >$00E9
3ba: 3f           SWI
3bb: 3d           MUL
3bc: f1 be b9     CMPB   $BEB9
3bf: d1 c2        CMPB   <$C2
3c1: 06 3d        ROR    <$3D
3c3: 3d           MUL
3c4: b9 b8 bc     ADCA   $B8BC
3c7: bd 06 d1     JSR    $06D1
3ca: e9 bc 97     ADCB   [$0364,PCR]
3cd: a9 c6        ADCA   A,U
3cf: 27 f4        BEQ    $03C5
3d1: b4 db d6     ANDA   $DBD6
3d4: d6 c3        LDB    <$C3
3d6: f4 0f c3     ANDB   $0FC3
3d9: bc b4 96     CMPX   $B496
3dc: db 27        ADDB   <$27
3de: 00 26        NEG    <$26
3e0: 05 e4        LSR    <$E4
3e2: db 3e        ADDB   <$3E
3e4: f1 d2 be     CMPB   $D2BE
3e7: b9 3c c2     ADCA   $3CC2
3ea: 38 a4        XANDCC #$A4
3ec: d1 bc        CMPB   <$BC
3ee: 27 1c        BEQ    $040C
3f0: bf f4 a4     STX    $F4A4
3f3: ef 06        STU    $6,X
3f5: 47           ASRA
3f6: 1c f2        ANDCC  #$F2
3f8: 27 cc        BEQ    $03C6
3fa: 3a           ABX
3fb: 34 a4        PSHS   PC,Y,B
3fd: b8 f0 c8     EORA   $F0C8
400: cc 34 17     LDD    #$3417
403: df f0        STU    <$F0
405: 27 d1        BEQ    $03D8
407: ba 39 bd     ORA    $39BD
40a: d1 96        CMPB   <$96
40c: ae 05        LDX    $5,X
40e: b5 be 3e     BITA   $BE3E
411: 3c c2        CWAI   #$C2
413: 3c b9        CWAI   #$B9
415: d1 bc        CMPB   <$BC
417: f4 85 19     ANDB   $8519
41a: b8 bc c3     EORA   $BCC3
41d: 95 3e        BITA   <$3E
41f: 2b be        BMI    $03DF
421: bd b3 ce     JSR    $B3CE
424: 06 06        ROR    <$06
426: 28 ce        BVC    $03F6
428: b9 bb 85     ADCA   $BB85
42b: 8c 2c 2b     CMPX   #$2C2B
42e: f1 27 17     CMPB   $2717
431: df be        STU    <$BE
433: bd d1 aa     JSR    $D1AA
436: 39           RTS
437: 05 d1        LSR    <$D1
439: b8 bc be     EORA   $BCBE
43c: 9d 39        JSR    <$39
43e: 2e 06        BGT    $0446
440: b9 bd bb     ADCA   $BDBB
443: 85 21        BITA   #$21
445: 01 2e        NEG    <$2E
447: f1 8c 28     CMPB   $8C28
44a: 01 56        NEG    <$56
44c: bc bf f4     CMPX   $BFF4
44f: 0f c3        CLR    <$C3
451: d6 93        LDB    <$93
453: 1c 53        ANDCC  #$53
455: 0f 62        CLR    <$62
457: ef 4d        STU    $D,U
459: 28 01        BVC    $045C
45b: 0f bc        CLR    <$BC
45d: bf b4 1c     STX    $B41C
460: ef 21        STU    $1,Y
462: 27 d1        BEQ    $0435
464: 5d           TSTB
465: ba 17 df     ORA    $17DF
468: aa 39        ORA    -$7,Y
46a: 01 9d        NEG    <$9D
46c: be bd d1     LDX    $BDD1
46f: bc 3c 56     CMPX   $3C56
472: a4 02        ANDA   $2,X
474: f4 f0 26     ANDB   $F026
477: d1 df        CMPB   <$DF
479: be bd d1     LDX    $BDD1
47c: aa 38        ORA    -$8,Y
47e: 05 9d        LSR    <$9D
480: b8 bc bd     EORA   $BCBD
483: 97 3c        STA    <$3C
485: 31 01        LEAY   $1,X
487: d1 a9        CMPB   <$A9
489: 93 ba        SUBD   <$BA
48b: ae d1        LDX    [,U++]
48d: fb 38 bd     ADDB   $38BD
490: 05 b5        LSR    <$B5
492: 02 fd        XNC    <$FD
494: d1 26        CMPB   <$26
496: d1 26        CMPB   <$26
498: 05 df        LSR    <$DF
49a: be bd d1     LDX    $BDD1
49d: aa 39        ORA    -$7,Y
49f: 01 d1        NEG    <$D1
4a1: bc bf 97     CMPX   $BF97
4a4: 9d 38        JSR    <$38
4a6: 01 a7        NEG    <$A7
4a8: 1c 16        ANDCC  #$16
4aa: 57           ASRB
4ab: e3 f4        ADDD   [,S]
4ad: 00 a4        NEG    <$A4
4af: b2 ef fb     SBCA   $EFFB
4b2: 39           RTS
4b3: bd a8 ba     JSR    $A8BA
4b6: ae 01        LDX    $1,X
4b8: d1 26        CMPB   <$26
4ba: d1 be        CMPB   <$BE
4bc: b5 05 fd     BITA   $05FD
4bf: 3c b9        CWAI   #$B9
4c1: fe 27 e9     LDU    $27E9
4c4: 0a a8        DEC    <$A8
4c6: f1 ce e9     CMPB   $CEE9
4c9: 71 26 f1     NEG    $26F1
4cc: c2 da        SBCB   #$DA
4ce: 0e e4        JMP    <$E4
4d0: 07 d8        ASR    <$D8
4d2: f1 ec 93     CMPB   $EC93
4d5: ac f1        CMPX   [,S++]
4d7: d1 b8        CMPB   <$B8
4d9: f1 96 a6     CMPB   $96A6
4dc: 0e e9        JMP    <$E9
4de: ff 96 26     STU    $9626
4e1: f1 17 d6     CMPB   $17D6
4e4: 06 e4        ROR    <$E4
4e6: af 03        STX    $3,X
4e8: 93 71        SUBD   <$71
4ea: 27 f0        BEQ    $04DC
4ec: ef da        STU    [F,U]
4ee: 81 ff        CMPA   #$FF
4f0: b8 f1 96     EORA   $F196
4f3: f1 06 e9     CMPB   $06E9
4f6: 53           COMB
4f7: 11 d6 f1     LDB    <$F1
4fa: 01 e4        NEG    <$E4
4fc: c3 26 f1     ADDD   #$26F1
4ff: 07 c3        ASR    <$C3
501: b8 f1 96     EORA   $F196
504: 07 01        ASR    <$01
506: e9 f1        ADCB   [,S++]
508: c8 27        EORB   #$27
50a: b4 72 bc     ANDA   $72BC
50d: f4 10 12     ANDB   $1012
510: b4 11 71     ANDA   $1171
513: 96 08        LDA    <$08
515: bc 8b 11     CMPX   $8B11
518: d6 23        LDB    <$23
51a: 03 e4        COM    <$E4
51c: c3 26 f1     ADDD   #$26F1
51f: 07 c3        ASR    <$C3
521: b8 f1 96     EORA   $F196
524: 27 03        BEQ    $0529
526: e9 26        ADCB   $6,Y
528: 01 df        NEG    <$DF
52a: be bd d1     LDX    $BDD1
52d: aa 39        ORA    -$7,Y
52f: 01 d1        NEG    <$D1
531: bc bf 97     CMPX   $BF97
534: 9d 38        JSR    <$38
536: 01 a7        NEG    <$A7
538: 1c 16        ANDCC  #$16
53a: 57           ASRB
53b: e3 f4        ADDD   [,S]
53d: 00 a4        NEG    <$A4
53f: 42           XNCA
540: ef fb        STU    [D,S]
542: 39           RTS
543: bd 38 ba     JSR    $38BA
546: ae 01        LDX    $1,X
548: d1 26        CMPB   <$26
54a: d1 26        CMPB   <$26
54c: b5 01 fd     BITA   $01FD
54f: 48           ASLA
550: a1 bc f4     CMPA   [$0547,PCR]
553: 82 22        SBCA   #$22
555: 02 d2        XNC    <$D2
557: d6 40        LDB    <$40
559: 27 e4        BEQ    $053F
55b: 39           RTS
55c: a4 f1        ANDA   [,S++]
55e: ba 12 66     ORA    $1266
561: 3f           SWI
562: 39           RTS
563: 06 ba        ROR    <$BA
565: be bd d1     LDX    $BDD1
568: 9d 39        JSR    <$39
56a: 56           RORB
56b: a4 bc f4     ANDA   [$0562,PCR]
56e: 0f b8        CLR    <$B8
570: 39           RTS
571: 3c 06        CWAI   #$06
573: a4 bc bf     ANDA   [$0535,PCR]
576: f0 c8 cc     SUBB   $C8CC
579: 75 31 3a     LSR    $313A
57c: ef bc b4     STU    [$0533,PCR]
57f: 1c b4        ANDCC  #$B4
581: bc f4 95     CMPX   $F495
584: 05 32        LSR    <$32
586: 12           NOP
587: b1 8e ce     CMPA   $8ECE
58a: 31 ac a1     LEAY   $052E,PCR
58d: bc f4 06     CMPX   $F406
590: fd f0 96     STD    $F096
593: 03 a8        COM    <$A8
595: a4 f1        ANDA   [,S++]
597: d6 04        LDB    <$04
599: 93 95        SUBD   <$95
59b: c8 85        EORB   #$85
59d: 9f f1        STX    <$F1
59f: 95 bc        BITA   <$BC
5a1: f4 b3 07     ANDB   $B307
5a4: 35 af        PULS   CC,D,DP,Y,PC
5a6: bc 93 ae     CMPX   $93AE
5a9: f5 37 ce     BITB   $37CE
5ac: a1 a4        CMPA   ,Y
5ae: 12           NOP
5af: b1 8e 31     CMPA   $8E31
5b2: a1 ff bc 14  CMPA   [$BC14]
5b6: ce a6 96     LDU    #$A696
5b9: 31 a8 f4     LEAY   -$0C,Y
5bc: bc f4 ac     CMPX   $F4AC
5bf: 2f 12        BLE    $05D3
5c1: 2f f0        BLE    $05B3
5c3: ca c7        ORB    #$C7
5c5: 46           RORA
5c6: a1 2f        CMPA   $F,Y
5c8: 46           RORA
5c9: a0 03        SUBA   $3,X
5cb: 06 0f        ROR    <$0F
5cd: f1 d6 93     CMPB   $D693
5d0: b8 c8 b4     EORA   $C8B4
5d3: cc f1 cc     LDD    #$F1CC
5d6: fb b4 ff     ADDB   $B4FF
5d9: 31 06        LEAY   $6,X
5db: a8 bc f4     EORA   [$05D2,PCR]
5de: fd ac f4     STD    $ACF4
5e1: bc f4 ed     CMPX   $F4ED
5e4: af 35        STX    -$B,Y
5e6: 12           NOP
5e7: ff 06 57     STU    $0657
5ea: 96 47        LDA    <$47
5ec: 0a a0        DEC    <$A0
5ee: ff 06 0a     STU    $060A
5f1: 47           ASRA
5f2: 96 02        LDA    <$02
5f4: 57           ASRB
5f5: a0 bc f4     SUBA   [$05EC,PCR]
5f8: 56           RORB
5f9: a4 f1        ANDA   [,S++]
5fb: 46           RORA
5fc: 9f 27        STX    <$27
5fe: e4 02        ANDB   $2,X
600: ad 00        JSR    $0,X
602: e9 39        ADCB   -$7,Y
604: b8 f1 be     EORA   $F1BE
607: fd 12 be     STD    $12BE
60a: ba bd 09     ORA    $BD09
60d: 3f           SWI
60e: 3c 06        CWAI   #$06
610: d1 71        CMPB   <$71
612: 96 39        LDA    <$39
614: b5 be b8     BITA   $BEB8
617: bc 2b 04     CMPX   $2B04
61a: 27 06        BEQ    $0622
61c: be b9 bd     LDX    $B9BD
61f: bb 2e f1     ADDA   $2EF1
622: b8 bc 85     EORA   $BC85
625: 8c 3a 2c     CMPX   #$3A2C
628: be b9 bd     LDX    $B9BD
62b: bb 04 28     ADDA   $0428
62e: 02 2a        XNC    <$2A
630: 85 71        BITA   #$71
632: 2e 0f        BGT    $0643
634: f1 bc b4     CMPB   $BCB4
637: cc b4 bc     LDD    #$B4BC
63a: b8 f0 1f     EORA   $F01F
63d: 27 32        BEQ    $0671
63f: bf 00 45     STX    >$0045
642: 2f a4        BLE    $05E8
644: 12           NOP
645: bf ff 21     STX    $FF21
648: ba 01 df     ORA    $01DF
64b: be 26 d1     LDX    $26D1
64e: aa 39        ORA    -$7,Y
650: bd d1 b8     JSR    $D1B8
653: bc 01 9d     CMPX   $019D
656: 39           RTS
657: 2b be        BMI    $0617
659: b9 bd bb     ADCA   $BDBB
65c: 04 26        LSR    <$26
65e: 07 2b        ASR    <$2B
660: 85 8c        BITA   #$8C
662: 27 9e        BEQ    $0602
664: f1 bc b4     CMPB   $BCB4
667: 21 ba        BRN    $0623
669: 84 3a        ANDA   #$3A
66b: ff 83 84     STU    $8384
66e: ff ff 39     STU    $FF39
671: 84 3a        ANDA   #$3A
673: ff b9 8c     STU    $B98C
676: ff ff 39     STU    $FF39
679: 29 9c        BVS    $0617
67b: 39           RTS
67c: 9c b5        CMPX   <$B5
67e: ff ab ff     STU    $ABFF
681: fa 6c bc     ORB    $6CBC
684: e1 06        CMPB   $6,X
686: a8 27        EORA   $7,Y
688: bf f8 17     STX    $F817
68b: c8 08        EORB   #$08
68d: a6 a4        LDA    ,Y
68f: cc ef 96     LDD    #$EF96
692: a6 f4        LDA    [,S]
694: 8a ff        ORA    #$FF
696: 96 16        LDA    <$16
698: 00 a4        NEG    <$A4
69a: 86 f1        LDA    #$F1
69c: 57           ASRB
69d: 1c fa        ANDCC  #$FA
69f: e4 06        ANDB   $6,X
6a1: 57           ASRB
6a2: ac a4        CMPX   ,Y
6a4: 00 2e        NEG    <$2E
6a6: 2e ca        BGT    $0672
6a8: ce 9d f4     LDU    #$9DF4
6ab: 57           ASRB
6ac: ed 96        STD    [A,X]
6ae: 70 a4 18     NEG    $A418
6b1: ed 86        STD    A,X
6b3: ac 1c        CMPX   -$4,X
6b5: a9 fa        ADCA   [F,S]
6b7: f4 2e 2e     ANDB   $2E2E
6ba: e9 ce        ADCB   W,U
6bc: a8 f1        EORA   [,S++]
6be: ca ed        ORB    #$ED
6c0: b5 27 e4     BITA   $27E4
6c3: 32 96        LEAS   [A,X]
6c5: f1 85 cc     CMPB   $85CC
6c8: 95 39        BITA   <$39
6ca: cf 3f ba     XSTU   #$3FBA
6cd: 12           NOP
6ce: ba bd 06     ORA    $BD06
6d1: 9d d3        JSR    <$D3
6d3: f9 d1 b3     ADCB   $D1B3
6d6: 96 a8        LDA    <$A8
6d8: ac 06        CMPX   $6,X
6da: d1 96        CMPB   <$96
6dc: bd 97 a9     JSR    $97A9
6df: ab e7        ADDA   E,S
6e1: d1 59        CMPB   <$59
6e3: ec ad f2 c3  LDD    $F9AA,PCR
6e7: 27 17        BEQ    $0700
6e9: d6 f1        LDB    <$F1
6eb: 2b ab        BMI    $0698
6ed: 04 20        LSR    <$20
6ef: f1 20 27     CMPB   $2027
6f2: f1 a9 96     CMPB   $A996
6f5: 17 e4 26     LBSR   $EB1E
6f8: 80 eb        SUBA   #$EB
6fa: 96 d1        LDA    <$D1
6fc: e7 fc ab     STB    [$06AA,PCR]
6ff: f2 d9 04     SBCB   $D904
702: e9 bc b8     ADCB   [$06BD,PCR]
705: f1 96 36     CMPB   $9636
708: f4 6f f1     ANDB   $6FF1
70b: 12           NOP
70c: 96 af        LDA    <$AF
70e: dc 0a        LDD    <$0A
710: 52           XNCB
711: ff 3c 2f     STU    $3C2F
714: 0a 96        DEC    <$96
716: 31 2a        LEAY   $A,Y
718: 25 1e        BCS    $0738
71a: 16 e1 20     LBRA   $E83D
71d: 17 0f fa     LBSR   $171A
720: 6d 12        TST    -$E,X
722: 96 05        LDA    <$05
724: 06 a6        ROR    <$A6
726: 26 f1        BNE    $0719
728: e4 00        ANDB   $0,X
72a: b8 b0 06     EORA   $B006
72d: 57           ASRB
72e: 39           RTS
72f: 00 c8        NEG    <$C8
731: c8 31        EORB   #$31
733: bc a0 b0     CMPX   $A0B0
736: c8 1d        EORB   #$1D
738: 11 06 57     ROR    <$57
73b: 42           XNCA
73c: b0 06 33     SUBA   $0633
73f: 06 50        ROR    <$50
741: a0 39        SUBA   -$7,Y
743: 2b 57        BMI    $079C
745: b8 bc be     EORA   $BCBE
748: 04 27        LSR    <$27
74a: 07 2b        ASR    <$2B
74c: b9 bd bb     ADCA   $BDBB
74f: 85 f1        BITA   #$F1
751: bc b4 f1     CMPX   $B4F1
754: 8c 27 af     CMPX   #$27AF
757: 03 d6        COM    <$D6
759: 93 bc        SUBD   <$BC
75b: 11 06 61     ROR    <$61
75e: 1d           SEX
75f: b0 17 f1     SUBA   $17F1
762: f1 d6 94     CMPB   $D694
765: c8 03        EORB   #$03
767: 02 93        XNC    <$93
769: b8 80 3f     EORA   $803F
76c: 72 2e 17     XNC    $2E17
76f: 90 f1        SUBA   <$F1
771: 21 19        BRN    $078C
773: 56           RORB
774: c8 ba        EORB   #$BA
776: f0 f0 b3     SUBB   $F0B3
779: ee 95        LDU    [B,X]
77b: 82 82        SBCA   #$82
77d: 7f e1 c3     CLR    $E1C3
780: 8c 47 ed     CMPX   #$47ED
783: e1 95        CMPB   [B,X]
785: a4 88 a0     ANDA   -$60,X
788: cc f0 0f     LDD    #$F00F
78b: 97 19        STA    <$19
78d: 56           RORB
78e: b3 ee 91     SUBD   $EE91
791: e1 c3        CMPB   ,--U
793: 95 95        BITA   <$95
795: 97 9d        STA    <$9D
797: a4 ed e1 cc  ANDA   $E967,PCR
79b: e1 99 a0 c8  CMPB   [-$5F38,X]
79f: 71 fb f4     NEG    $FBF4
7a2: a9 0f        ADCA   $F,X
7a4: ac 93        CMPX   [,--X]
7a6: b4 fb cb     ANDA   $FBCB
7a9: 93 27        SUBD   <$27
7ab: f9 d9 a0     ADCB   $D9A0
7ae: af d6        STX    [A,U]
7b0: 28 b1        BVC    $0763
7b2: f9 29 93     ADCB   $2993
7b5: 1f d6        TFR    inv,inv
7b7: 93 ba        SUBD   <$BA
7b9: ff c6 ac     STU    $C6AC
7bc: 1f 93        TFR    B,U
7be: f9 f4 06     ADCB   $F406
7c1: a4 a7        ANDA   E,Y
7c3: fa 10 11     ORB    $1011
7c6: 93 96        SUBD   <$96
7c8: bc b4 96     CMPX   $B496
7cb: a6 36        LDA    -$A,Y
7cd: ff ff 96     STU    $FF96
7d0: f2 d2 e7     SBCB   $D2E7
7d3: e7 fa        STB    [F,S]
7d5: fa 17 ac     ORB    $17AC
7d8: 86 03        LDA    #$03
7da: c3 f1 f1     ADDD   #$F1F1
7dd: 17 dc c8     LBSR   $E4A8
7e0: 96 d0        LDA    <$D0
7e2: b0 1c f1     SUBA   $1CF1
7e5: 11 a8 11     EORA   -$F,X
7e8: b0 68 28     SUBA   $6828
7eb: d0 47        SUBB   <$47
7ed: 86 f1        LDA    #$F1
7ef: f8 3f 1c     EORB   $3F1C
7f2: 3f           SWI
7f3: 86 94        LDA    #$94
7f5: 47           ASRA
7f6: 94 71        ANDA   <$71
7f8: 9d 26        JSR    <$26
7fa: 3a           ABX
7fb: e8 94        EORB   [,X]
7fd: 4f           CLRA
7fe: 01 ff        NEG    <$FF
