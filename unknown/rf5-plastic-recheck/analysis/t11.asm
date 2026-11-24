000: d5ff b49e 0121  BISB  #236,@000447
006: c5fb a4bc c356  BICB  #274,@-36252(R3)
00c: fb30            .WORD 175460
00e: 12f8 26e1       MOV   (R3),@23341(R0)
012: 6f62 e4fa       ADD   @-15406(R5),-(R2)
016: 3a26            BIT   @-(R0),-(SP)
018: 0c8c            ASR   (R4)
01a: 3a26            BIT   @-(R0),-(SP)
01c: aeff b85f 122e  CMPB  @-43641(R3),@011120
022: 17c8 2e80       MOV   @#027200,(R0)
026: 3f80 4490       BIT   @42220(SP),R0
02a: fbf2            .WORD 175762
02c: fa52            .WORD 175122
02e: 0644            BGT   000270
030: 061f            BGT   000160
032: 3cac 01a8       BIT   650(R2),@-(R4)
036: 8af4 5fdf       DECB  57737(R4)
03a: 073c            BLE   000264
03c: f09a            .WORD 170232
03e: 47fb 773a 4801  BIC   @#073472,@44001(R3)
044: bbeb            BITB  @-(PC),@-(R3)
046: 0583            BLT   177516
048: fe85            .WORD 177205
04a: 5e06 bc95       BIS   @-41553(R0),SP
04e: b352            BITB  (R5),(R2)+
050: 4657 72aa       BIC   @(R1)+,#071252
054: 80fa            BPL   000112
056: 9501            MOVB  (R4)+,R1
058: 2e2e 4d77       CMP   @46567(R0),@-(SP)
05c: 77fc faec       ASHC  @-2424(R4),PC
060: aa56            CMPB  @-(R1),(SP)+
062: 7271 b37f       DIV   -46201(R1),R1
066: feef            .WORD 177357
068: 53bc c3d6       BIS   (SP),@-36052(R4)
06c: 7436 7404       ASH   72004(SP),R0
070: bffe 1fef 07a4  BITB  @020143,@3644(SP)
076: bc77 0734 2693  BITB  3464(R1),023417
07c: a4f4 9587       CMPB  (R3)+,-65171(R4)
080: 14a4            MOV   (R2)+,-(R4)
082: aa46            CMPB  @-(R1),SP
084: fa1c            .WORD 175034
086: bc08 072f       BITB  3457(R0),(R0)
08a: 958f            MOVB  (SP)+,(PC)
08c: c3f4 fa01       BICB  (PC),-2777(R4)
090: aa46            CMPB  @-(R1),SP
092: bc8f 2610       BITB  23020(R2),(PC)
096: 30a4            BIT   R2,-(R4)
098: 96f4 cd15       MOVB  @(R3)+,-31353(R4)
09c: c53f 3fc9       BICB  (R4)+,@040151
0a0: ae96 96ff       CMPB  @-64401(R2),(SP)+
0a4: 966e            MOVB  @(R1)+,@-(SP)
0a6: 26a6            CMP   @(R2)+,-(SP)
0a8: e40c            SUB   (R0)+,(R4)
0aa: 030f            BEQ   000312
0ac: 56f1 86d6       BIS   @(R3)+,-74452(R1)
0b0: 0f84            .WORD 007604
0b2: f1b8            .WORD 170670
0b4: 8656            BCC   000542
0b6: e902            SUB   -(R4),R2
0b8: 0896            JSR   R2,(SP)+
0ba: 05bf            BLT   000072
0bc: 3326            BIT   (R4),-(SP)
0be: b826            BITB  -(R0),-(SP)
0c0: bc01 bcb4       BITB  -41514(R0),R1
0c4: 2fa0 1d8f       CMP   @16617(SP),-(R0)
0c8: 0611            BGT   000354
0ca: f1b8            .WORD 170670
0cc: 06b0            BGT   000056
0ce: e901            SUB   -(R4),R1
0d0: 4a96            BIC   @-(R2),(SP)+
0d2: e402            SUB   (R0)+,R2
0d4: 2621            CMP   @(R0)+,-(R1)
0d6: 96f1 bc26       MOVB  @(R3)+,-41732(R1)
0da: b4a4            BITB  (R2)+,-(R4)
0dc: 0cf8 a7cc       ASL   @-54064(R0)
0e0: a4bc 42b4       CMPB  (R2)+,@41264(R4)
0e4: cc17 96d4 b827  BICB  -64454(R0),#047
0ea: e9a0            SUB   -(SP),-(R0)
0ec: 3fd7 26e8 af01  BIT   @023730,#127401
0f2: d5e4 26ab       BISB  #253,-(R4)
0f6: 5562            BIS   (R5)+,-(R2)
0f8: fb25            .WORD 175445
0fa: efeb fbfb       SUB   @176371,@-(R3)
0fe: fcfc            .WORD 176374
100: 43fb 8617       BIC   (PC),@-74751(R3)
104: 2643            CMP   @(R1)+,R3
106: bfd1 a105       BITB  @121017,(R1)+
10a: 270e            CMP   @(R4)+,(SP)
10c: b811            BITB  -(R0),(R1)+
10e: afad e9ae       CMPB  @-13122(SP),@-(R5)
112: a4b3 b1f1       CMPB  (R2)+,-47017(R3)
116: 9111            MOVB  R4,(R1)+
118: a4dd            CMPB  (R3)+,@(R5)+
11a: a496            CMPB  (R2)+,(SP)+
11c: d111            BISB  R4,(R1)+
11e: 7111            MUL   (R1)+,R4
120: a46e            CMPB  (R1)+,@-(SP)
122: a4a1            CMPB  (R2)+,-(R1)
124: 1111            MOV   R4,(R1)+
126: 5111            BIS   R4,(R1)+
128: a4a1            CMPB  (R2)+,-(R1)
12a: a4a7            CMPB  (R2)+,-(PC)
12c: 3111            BIT   R4,(R1)+
12e: ef11 cd16       SUB   @-31352(R4),(R1)+
132: afa4 11f1       CMPB  @10761(SP),-(R4)
136: fd2d            .WORD 176455
138: 11f1 c3ef       MOV   PC,-36021(R1)
13c: a4cd            CMPB  (R3)+,(R5)
13e: 4338 d126       BIC   (R4),@-27332(R0)
142: f121            .WORD 170441
144: 860f            BCC   000544
146: c807            BICB  -(R0),PC
148: 9311            MOVB  (R4),(R1)+
14a: 4371 51d8       BIC   (R5),50730(R1)
14e: aabe 21f1       CMPB  @-(R2),@20761(SP)
152: ffbf            .WORD 177677
154: aadc            CMPB  @-(R3),@(R4)+
156: a83f eff1       CMPB  -(R0),@170513
15a: ffbf            .WORD 177677
15c: 53e9            BIS   (PC),@-(R1)
15e: d63f 6f0a       BISB  @(R0)+,@070154
162: dff1 ffc3 c3e4  BISB  @000451,-36034(R1)
168: 076f            BLE   001110
16a: 5186            BIS   SP,SP
16c: d126            BISB  R4,-(SP)
16e: ff21            .WORD 177441
170: f1a8            .WORD 170650
172: 26ef            CMP   @(R3)+,@-(PC)
174: e927            SUB   -(R4),-(PC)
176: 065b            BGT   001056
178: 94bc 033f       MOVB  (R2)+,@1477(R4)
17c: 261d            CMP   @(R0)+,@(R5)+
17e: f1b8            .WORD 170670
180: 02e9            BNE   000524
182: e93e b826       SUB   -(R4),@-43732(SP)
186: 26f1 3b06       CMP   @(R3)+,35406(R1)
18a: ffe9            .WORD 177751
18c: f1b8            .WORD 170670
18e: b826            BITB  -(R0),-(SP)
190: e900            SUB   -(R4),R0
192: 0715            BLE   000676
194: b8f1 f1ff       BITB  -(R3),-7001(R1)
198: c80a            BICB  -(R0),(R2)
19a: ee0a f1a0       SUB   @-7140(R0),(R2)
19e: a006            CMPB  R0,SP
1a0: 06f1            BGT   000604
1a2: 96ac            MOVB  @(R2)+,@-(R4)
1a4: eb0a            SUB   @-(R4),(R2)
1a6: ffcf            .WORD 177717
1a8: 42a6            BIC   (R2),-(SP)
1aa: 8cc3            ASLB  R3
1ac: 1796            MOV   @(SP)+,(SP)+
1ae: ffaa            .WORD 177652
1b0: 0c8a            ASR   (R2)
1b2: f1b8            .WORD 170670
1b4: 377f e905       BIT   @(R5)+,@165275
1b8: ba11            BITB  @-(R0),(R1)+
1ba: f4bc            .WORD 172274
1bc: 07bc            BLE   000466
1be: be32 c50f 281f  BITB  @-35361(R0),24037(R2)
1c4: be12 b8bc       BITB  @-43504(R0),(R2)+
1c8: ed20 9a84       SUB   -62574(R4),-(R0)
1cc: bd21 833a       BITB  -76306(R4),-(R1)
1d0: 8c99            ASRB  @(R1)+
1d2: 239b            CMP   (SP),@(R3)+
1d4: bbb9 fcbc       BITB  @-(SP),@-1504(R1)
1d8: ff21            .WORD 177441
1da: dac4            BISB  @-(R3),R4
1dc: fde5            .WORD 176745
1de: c37a ccd9       BICB  (R5),@-31447(R2)
1e2: 94db            MOVB  (R3)+,@(R3)+
1e4: fbf9            .WORD 175771
1e6: 013f            BR    001146
1e8: 3fe8 56fa       BIT   @054346,@-(R0)
1ec: e1ff e0f4       SUB   PC,@161344
1f0: e1c3            SUB   PC,R3
1f2: 06f4            BGT   000734
1f4: faf1            .WORD 175361
1f6: ce5e a0a6       BICB  @-57532(R1),@(SP)+
1fa: ed1c 1817       SUB   14027(R4),@(R4)+
1fe: 26ea            CMP   @(R3)+,@-(R2)
200: e406            SUB   (R0)+,SP
202: 0c05            ROR   R5
204: d6f1 4193       BISB  @(R3)+,40623(R1)
208: d625            BISB  @(R0)+,-(R5)
20a: 0217            BNE   001072
20c: 9311            MOVB  (R4),(R1)+
20e: f4bc            .WORD 172274
210: 1737 1552       MOV   @(R4)+,013546
214: b1b2 f1c1       BITB  SP,-7077(R2)
218: 0603            BGT   001040
21a: 0225            BNE   001146
21c: 93d6            MOVB  (PC),(SP)+
21e: f4bc            .WORD 172274
220: a4d6            CMPB  (R3)+,(SP)+
222: 02c8            BNE   000664
224: f120            .WORD 170440
226: f4bc            .WORD 172274
228: 3037 b1f7       BIT   R0,132043
22c: d672 17a4       BISB  @(R1)+,13644(R2)
230: f4bc            .WORD 172274
232: d692            BISB  @(R2)+,(R2)+
234: 3702            BIT   @(R4)+,R2
236: ef3e f5a4 32d6  SUB   @-5134(R4),@31326(SP)
23c: 1191            MOV   SP,(R1)+
23e: 56ad            BIS   @(R2)+,@-(R5)
240: 9353            MOVB  (R5),(R3)+
242: b117 56a7       BITB  R4,#247
246: 7111            MUL   (R1)+,R4
248: bcdf 05da 7111  BITB  2732(R3),@#070421
24e: b4bc d904       BITB  (R2)+,@-23374(R4)
252: 9305            MOVB  (R4),R5
254: bc41 64f4       BITB  62364(R1),R1
258: 3326            BIT   (R4),-(SP)
25a: a426            CMPB  (R0)+,-(SP)
25c: 5b08            BIS   @-(R4),(R0)
25e: 7105            MUL   R5,R4
260: 0120            BR    001242
262: 53c3            BIS   (PC),R3
264: f4bc            .WORD 172274
266: ac6a 1141       CMPB  10501(R1),@-(R2)
26a: 1126            MOV   R4,-(SP)
26c: bce4 b102       BITB  -47376(R3),-(R4)
270: f126            .WORD 170446
272: 0faf            .WORD 007657
274: e405            SUB   (R0)+,R5
276: c356            BICB  (R5),(SP)+
278: 0795            BLE   000644
27a: abe4            CMPB  @-(PC),-(R4)
27c: f126            .WORD 170446
27e: b807            BITB  -(R0),PC
280: e907            SUB   -(R4),PC
282: ff93            .WORD 177623
284: fbf1            .WORD 175761
286: 5695            BIS   @(R2)+,(R5)+
288: 060f            BGT   001250
28a: f1b8            .WORD 170670
28c: fd47            .WORD 176507
28e: e907            SUB   -(R4),PC
290: 97ff 8b8b 71b2  MOVB  @#105613,@072110
296: bc71 7227 41b4  BITB  71047(R1),40664(R1)
29c: a0f4 d20f       CMPB  R3,-26761(R4)
2a0: 41b4 96ff       BIC   SP,-64401(R4)
2a4: d2b4 c3a6       BISB  (R2),-36132(R4)
2a8: 03c0            BEQ   001052
2aa: e404            SUB   (R0)+,R4
2ac: d6f1 b493       BISB  @(R3)+,-45555(R1)
2b0: 11ff bcfd       MOV   PC,@137661
2b4: b127            BITB  R4,-(PC)
2b6: 9132 12bb       MOVB  R4,11273(R2)
2ba: 7191            MUL   (R1)+,SP
2bc: c0fd be61       BICB  R3,@-40637(R5)
2c0: d6f1 b493       BISB  @(R3)+,-45555(R1)
2c4: 0403            BGE   001314
2c6: ffca            .WORD 177712
2c8: 2691            CMP   @(R2)+,(R1)+
2ca: d6f1 06e0       BISB  @(R3)+,3340(R1)
2ce: 05e4            BLT   001230
2d0: f1c3            .WORD 170703
2d2: 93d6            MOVB  (PC),(SP)+
2d4: 03e4            BEQ   001236
2d6: e402            SUB   (R0)+,R2
2d8: 71b4 0627       MUL   3047(R4),SP
2dc: b6ff f1b8       BITB  @(R3)+,@172230
2e0: 06e9            BGT   001264
2e2: 07e4            BLE   001254
2e4: f126            .WORD 170446
2e6: 0656            BGT   001624
2e8: f1ea            .WORD 170752
2ea: f9f8            .WORD 174770
2ec: f3b6            .WORD 171666
2ee: fbfa            .WORD 175772
2f0: e1f2 6181       SUB   PC,60601(R2)
2f4: faf2            .WORD 175362
2f6: 000f            .WORD 000017
2f8: c161            BICB  R5,-(R1)
2fa: e161            SUB   R5,-(R1)
2fc: 4c4e 256b       BIC   22553(R1),(SP)
300: d126            BISB  R4,-(SP)
302: 38aa            BIT   -(R2),@-(R2)
304: df02 bdbe       BISB  @-41102(R4),R2
308: 9d05 2b38       MOVB  25470(R4),R5
30c: b8d1            BITB  -(R3),(R1)+
30e: bebc 2406 2b07  BITB  @22006(R2),@25407(R4)
314: bdb9 85bb bcf1  BITB  -75105(SP),@-41417(R1)
31a: 21b4 2771       CMP   SP,23561(R4)
31e: ba82            BITB  @-(R2),R2
320: d126            BISB  R4,-(SP)
322: 39aa            BIT   -(SP),@-(R2)
324: df06 bdbe       BISB  @-41102(R4),SP
328: 9d05 0138       MOVB  470(R4),R5
32c: bcd1 f4bf       BITB  -5501(R3),(R1)+
330: 5706            BIS   @(R4)+,SP
332: 1ce3 a408       MOV   -55770(R3),-(R3)
336: f43b            .WORD 172073
338: 5716            BIS   @(R4)+,(SP)+
33a: fbef            .WORD 175757
33c: a400            CMPB  (R0)+,R0
33e: ba31 bd39       BITB  @-(R0),-41307(R1)
342: 26d1            CMP   @(R3)+,(R1)+
344: 05ae            BLT   001242
346: 06b5            BGT   001262
348: 96d1            MOVB  @(R3)+,(R1)+
34a: df06 26fd       BISB  @23375(R4),SP
34e: aad1            CMPB  @-(R3),(R1)+
350: bdbe b8d1 0539  BITB  -43457(SP),@2471(SP)
356: 399d            BIT   -(SP),@(R5)+
358: bebc bdb9 022b  BITB  @-41107(R2),@1053(R4)
35e: 0722            BLE   001644
360: 85bb            BVS   001330
362: 278c            CMP   @(SP)+,(R4)
364: f12b            .WORD 170453
366: b4bc ba3e       BITB  (R2)+,@-42702(R4)
36a: 26a6            CMP   @(R2)+,-(SP)
36c: ff21            .WORD 177441
36e: 0596            BLT   001234
370: aad1            CMPB  @-(R3),(R1)+
372: 0139            BR    001746
374: bedf d1bd 399d  BITB  @-27103(R3),@#034635
37a: 022b            BNE   001722
37c: bcb8 b9be 0720  BITB  -43102(R2),@3440(R0)
382: f12b            .WORD 170453
384: bbbd 7185       BITB  @-(SP),@70605(R5)
388: b4bc 2721       BITB  (R2)+,@23441(R4)
38c: 8727            BCS   001734
38e: 17ba aad1       MOV   @(SP)+,@-52457(R2)
392: 0539            BLT   002006
394: bedf d1bd 3d9d  BITB  @-27103(R3),@#036635
39a: 0638            BGT   002014
39c: bcb8 97bd d1d1  BITB  -64103(R2),@-27057(R0)
3a2: fbd1            .WORD 175721
3a4: 93a9            MOVB  (SP),@-(R1)
3a6: ba93            BITB  @-(R2),(R3)+
3a8: bd39 27d1 05ae  BITB  23721(R4),@2656(R1)
3ae: 17b5 96d1       MOV   @(SP)+,-64457(R5)
3b2: 07f1            BLE   001626
3b4: 27fd b8e4 e900  CMP   @#134344,@-13400(R5)
3ba: 3d3f bef1 d1b9  BIT   -40417(R4),@152571
3c0: 06c2            BGT   001506
3c2: 3d3d b8b9 bdbc  BIT   -43507(R4),@-41104(R5)
3c8: d106            BISB  R4,SP
3ca: bce9 a997       BITB  -53151(R3),@-(R1)
3ce: 27c6 b4f4       CMP   @#132364,SP
3d2: d6db            BISB  @(R3)+,@(R3)+
3d4: c3d6            BICB  (PC),(SP)+
3d6: 0ff4            .WORD 007764
3d8: bcc3 96b4       BITB  -64514(R3),R3
3dc: 27db 2600       CMP   @#023000,@(R3)+
3e0: e405            SUB   (R0)+,R5
3e2: 3edb d2f1       BIT   @-26417(R3),@(R3)+
3e6: b9be c23c       BITB  -(SP),@-36704(SP)
3ea: a438 bcd1       CMPB  (R0)+,@-41457(R0)
3ee: 1c27 f4bf       MOV   -5501(R0),-(PC)
3f2: efa4 4706       SUB   @43406(SP),-(R4)
3f6: f21c            .WORD 171034
3f8: cc27 343a       BICB  32072(R0),-(PC)
3fc: b8a4            BITB  -(R2),-(R4)
3fe: c8f0 34cc       BICB  -(R3),32314(R0)
402: df17 27f0 bad1  BISB  @23760(R4),#321
408: bd39 96d1 05ae  BITB  -64457(R4),@2656(R1)
40e: beb5 3c3e 3cc2  BITB  @36076(R2),36302(R5)
414: d1b9 f4bc       BISB  SP,@-5504(R1)
418: 1985            MOV   -(SP),R5
41a: bcb8 95c3 2b3e  BITB  -65075(R2),@25476(R0)
420: bdbe ceb3 0606  BITB  -30515(SP),@3006(SP)
426: ce28 bbb9       BICB  @-42107(R0),@-(R0)
42a: 8c85            ASRB  R5
42c: 2b2c            CMP   @-(R4),@-(R4)
42e: 27f1 df17 bdbe  CMP   @#157427,-41102(R1)
434: aad1            CMPB  @-(R3),(R1)+
436: 0539            BLT   002252
438: b8d1            BITB  -(R3),(R1)+
43a: bebc 399d 062e  BITB  @34635(R2),@3056(R4)
440: bdb9 85bb 0121  BITB  -75105(SP),@441(R1)
446: f12e            .WORD 170456
448: 288c            CMP   -(R2),(R4)
44a: 5601            BIS   @(R0)+,R1
44c: bfbc 0ff4 d6c3  BITB  @7764(SP),@-24475(R4)
452: 1c93 0f53       MOV   7523(R2),(R3)+
456: ef62 284d       SUB   @24115(R5),-(R2)
45a: 0f01            .WORD 007401
45c: bfbc 1cb4 21ef  BITB  @16264(SP),@20757(R4)
462: d127            BISB  R4,-(PC)
464: ba5d            BITB  @-(R1),@(R5)+
466: df17 39aa 9d01  BISB  @34652(R4),#001
46c: bdbe bcd1 563c  BITB  -41457(SP),@53074(SP)
472: 02a4            BNE   001674
474: f0f4            .WORD 170364
476: d126            BISB  R4,-(SP)
478: bedf d1bd 38aa  BITB  @-27103(R3),@#034252
47e: 9d05 bcb8       MOVB  -41510(R4),R5
482: 97bd 313c       MOVB  @(SP)+,@30474(R5)
486: d101            BISB  R4,R1
488: 93a9            MOVB  (SP),@-(R1)
48a: aeba fbd1 bd38  CMPB  @-2057(R2),@-41310(R2)
490: b505            BITB  (R4)+,R5
492: fd02            .WORD 176402
494: 26d1            CMP   @(R3)+,(R1)+
496: 26d1            CMP   @(R3)+,(R1)+
498: df05 bdbe       BISB  @-41102(R4),R5
49c: aad1            CMPB  @-(R3),(R1)+
49e: 0139            BR    002422
4a0: bcd1 97bf       BITB  -64101(R3),(R1)+
4a4: 389d            BIT   -(R2),@(R5)+
4a6: a701            CMPB  @(R4)+,R1
4a8: 161c            MOV   @(R0)+,@(R4)+
4aa: e357 00f4       SUB   (R5),#000364
4ae: b2a4            BITB  (R2),-(R4)
4b0: fbef            .WORD 175757
4b2: bd39 baa8 01ae  BITB  -42530(R4),@656(R1)
4b8: 26d1            CMP   @(R3)+,(R1)+
4ba: bed1 05b5       BITB  @2665(R3),(R1)+
4be: 3cfd feb9 e927  BIT   -507(R3),@-13331(R5)
4c4: a80a            CMPB  -(R0),(R2)
4c6: cef1 71e9 f126  BICB  @70751(R3),-7332(R1)
4cc: dac2            BISB  @-(R3),R2
4ce: e40e            SUB   (R0)+,(SP)
4d0: d807            BISB  -(R0),PC
4d2: ecf1 ac93 d1f1  SUB   -51555(R3),-27017(R1)
4d8: f1b8            .WORD 170670
4da: a696            CMPB  @(R2)+,(SP)+
4dc: e90e            SUB   -(R4),(SP)
4de: 96ff f126       MOVB  @(R3)+,@173010
4e2: d617 e406       BISB  @(R0)+,#006
4e6: 03af            BEQ   002106
4e8: 7193            MUL   (R3)+,SP
4ea: f027            .WORD 170047
4ec: daef            BISB  @-(R3),@-(PC)
4ee: ff81            .WORD 177601
4f0: f1b8            .WORD 170670
4f2: f196            .WORD 170626
4f4: e906            SUB   -(R4),SP
4f6: 1153            MOV   R5,(R3)+
4f8: f1d6            .WORD 170726
4fa: e401            SUB   (R0)+,R1
4fc: 26c3            CMP   @(R3)+,R3
4fe: 07f1            BLE   002342
500: b8c3            BITB  -(R3),R3
502: 96f1 0107       MOVB  @(R3)+,407(R1)
506: f1e9            .WORD 170751
508: 27c8 72b4       CMP   @#071264,(R0)
50c: f4bc            .WORD 172274
50e: 1210            MOV   (R0),(R0)+
510: 11b4 9671       MOV   SP,-64617(R4)
514: bc08 118b       BITB  10613(R0),(R0)
518: 23d6            CMP   (PC),(SP)+
51a: e403            SUB   (R0)+,R3
51c: 26c3            CMP   @(R3)+,R3
51e: 07f1            BLE   002402
520: b8c3            BITB  -(R3),R3
522: 96f1 0327       MOVB  @(R3)+,1447(R1)
526: 26e9            CMP   @(R3)+,@-(R1)
528: df01 bdbe       BISB  @-41102(R4),R1
52c: aad1            CMPB  @-(R3),(R1)+
52e: 0139            BR    002642
530: bcd1 97bf       BITB  -64101(R3),(R1)+
534: 389d            BIT   -(R2),@(R5)+
536: a701            CMPB  @(R4)+,R1
538: 161c            MOV   @(R0)+,@(R4)+
53a: e357 00f4       SUB   (R5),#000364
53e: 42a4            BIC   (R2),-(R4)
540: fbef            .WORD 175757
542: bd39 ba38 01ae  BITB  -42710(R4),@656(R1)
548: 26d1            CMP   @(R3)+,(R1)+
54a: 26d1            CMP   @(R3)+,(R1)+
54c: 01b5            BR    002270
54e: 48fd bca1       BIC   -(R3),@-41537(R5)
552: 82f4            BHI   002474
554: 0222            BNE   002632
556: d6d2            BISB  @(R3)+,(R2)+
558: 2740            CMP   @(R5)+,R0
55a: 39e4            BIT   -(PC),-(R4)
55c: f1a4            .WORD 170644
55e: 12ba 3f66       MOV   (R2),@37546(R2)
562: 0639            BGT   002726
564: beba d1bd 399d  BITB  @-27103(R2),@34635(R2)
56a: a456            CMPB  (R1)+,(SP)+
56c: f4bc            .WORD 172274
56e: b80f            BITB  -(R0),(PC)
570: 3c39 a406 bfbc  BIT   -55772(R0),@-40104(R1)
576: c8f0 75cc       BICB  -(R3),72714(R0)
57a: 3a31 bcef       BIT   @-(R0),-41421(R1)
57e: 1cb4 bcb4 95f4  MOV   -41514(R2),-65014(R4)
584: 3205            BIT   (R0),R5
586: b112            BITB  R4,(R2)+
588: ce8e ac31       BICB  @-51717(R2),(SP)
58c: bca1 06f4       BITB  3364(R2),-(R1)
590: f0fd            .WORD 170375
592: 0396            BEQ   002300
594: a4a8            CMPB  (R2)+,@-(R0)
596: d6f1 9304       BISB  @(R3)+,-66374(R1)
59a: c895            BICB  -(R2),(R5)+
59c: 9f85 95f1       MOVB  @-65017(SP),R5
5a0: f4bc            .WORD 172274
5a2: 07b3            BLE   002412
5a4: af35 93bc f5ae  CMPB  @-66104(R4),-5122(R5)
5aa: ce37 a4a1 b112  BICB  @-55537(R0),133302
5b0: 318e            BIT   SP,(SP)
5b2: ffa1            .WORD 177641
5b4: 14bc a6ce       MOV   (R2)+,@-54462(R4)
5b8: 3196            BIT   SP,(SP)+
5ba: f4a8            .WORD 172250
5bc: f4bc            .WORD 172274
5be: 2fac 2f12       CMP   @27422(SP),@-(R4)
5c2: caf0 46c7       BICB  @-(R3),43307(R0)
5c6: 2fa1 a046       CMP   @-57672(SP),-(R1)
5ca: 0603            BGT   002722
5cc: f10f            .WORD 170417
5ce: 93d6            MOVB  (PC),(SP)+
5d0: c8b8 ccb4       BICB  -(R2),@-31514(R0)
5d4: ccf1 b4fb 31ff  BICB  -45405(R3),30777(R1)
5da: a806            CMPB  -(R0),SP
5dc: f4bc            .WORD 172274
5de: acfd bcf4 edf4  CMPB  -41414(R3),@-11014(R5)
5e4: 35af            BIT   (SP)+,@-(PC)
5e6: ff12            .WORD 177422
5e8: 5706            BIS   @(R4)+,SP
5ea: 4796            BIC   @(SP)+,(SP)+
5ec: a00a            CMPB  R0,(R2)
5ee: 06ff            BGT   002756
5f0: 470a            BIC   @(R4)+,(R2)
5f2: 0296            BNE   002440
5f4: a057 f4bc       CMPB  R1,#274
5f8: a456            CMPB  (R1)+,(SP)+
5fa: 46f1 279f       BIC   @(R3)+,23637(R1)
5fe: 02e4            BNE   002710
600: 00ad            Ccc   #15
602: 39e9            BIT   -(PC),@-(R1)
604: f1b8            .WORD 170670
606: fdbe            .WORD 176676
608: be12 bdba       BITB  @-41106(R0),(R2)+
60c: 3f09 063c       BIT   @3074(R4),(R1)
610: 71d1            MUL   (R1)+,PC
612: 3996            BIT   -(SP),(SP)+
614: beb5 bcb8 042b  BITB  @-41510(R2),2053(R5)
61a: 0627            BGT   003152
61c: b9be bbbd       BITB  -(SP),@-42103(SP)
620: f12e            .WORD 170456
622: bcb8 8c85 2c3a  BITB  -71573(R2),@26072(R0)
628: b9be bbbd       BITB  -(SP),@-42103(SP)
62c: 2804            CMP   -(R0),R4
62e: 2a02            CMP   @-(R0),R2
630: 7185            MUL   R5,SP
632: 0f2e            .WORD 007456
634: bcf1 ccb4 bcb4  BITB  -31514(R3),-41514(R1)
63a: f0b8            .WORD 170270
63c: 271f bf32       CMP   @(R4)+,@#137462
640: 4500            BIC   (R4)+,R0
642: a42f            CMPB  (R0)+,@-(PC)
644: bf12 21ff       BITB  @20777(R4),(R2)+
648: 01ba            BR    002676
64a: bedf d126 39aa  BITB  @-27332(R3),@#034652
650: d1bd bcb8       BISB  SP,@-41510(R5)
654: 9d01 2b39       MOVB  25471(R4),R1
658: b9be bbbd       BITB  -(SP),@-42103(SP)
65c: 2604            CMP   @(R0)+,R4
65e: 2b07            CMP   @-(R4),PC
660: 8c85            ASRB  R5
662: 9e27 bcf1       MOVB  @-41417(R0),-(PC)
666: 21b4 84ba       CMP   SP,-75506(R4)
66a: ff3a            .WORD 177472
66c: 8483            BVC   002564
66e: ffff            .WORD 177777
670: 8439            BVC   003344
672: ff3a            .WORD 177472
674: 8cb9 ffff       ASRB  @-1(R1)
678: 2939 399c       CMP   -(R4),@34634(R1)
67c: b59c            BITB  (SP)+,@(R4)+
67e: abff faff       CMPB  @-(PC),@000601
682: bc6c 06e1       BITB  3341(R1),@-(R4)
686: 27a8            CMP   @(SP)+,@-(R0)
688: f8bf            .WORD 174277
68a: c817 a608       BICB  -(R0),#010
68e: cca4 96ef       BICB  -64421(R2),-(R4)
692: f4a6            .WORD 172246
694: ff8a            .WORD 177612
696: 1696            MOV   @(R2)+,(SP)+
698: a400            CMPB  (R0)+,R0
69a: f186            .WORD 170606
69c: 1c57 e4fa 5706  MOV   -15406(R1),#053406
6a2: a4ac            CMPB  (R2)+,@-(R4)
6a4: 2e00 ca2e       CMP   @-32722(R0),R0
6a8: 9dce 57f4       MOVB  057240,(SP)
6ac: 96ed            MOVB  @(R3)+,@-(R5)
6ae: a470 ed18       CMPB  (R1)+,-11350(R0)
6b2: ac86 a91c       CMPB  -53344(R2),SP
6b6: f4fa            .WORD 172372
6b8: 2e2e cee9       CMP   @-30427(R0),@-(SP)
6bc: f1a8            .WORD 170650
6be: edca 27b5       SUB   027167,(R2)
6c2: 32e4            BIT   (R3),-(R4)
6c4: f196            .WORD 170626
6c6: cc85 3995       BICB  34625(R2),R5
6ca: 3fcf 12ba       BIT   @014610,(PC)
6ce: bdba 9d06 f9d3  BITB  -61372(SP),@-3055(R2)
6d4: b3d1            BITB  (PC),(R1)+
6d6: a896            CMPB  -(R2),(SP)+
6d8: 06ac            BGT   003062
6da: 96d1            MOVB  @(R3)+,(R1)+
6dc: 97bd aba9       MOVB  @(SP)+,@-52127(R5)
6e0: d1e7            BISB  PC,-(PC)
6e2: ec59 f2ad       SUB   -6523(R1),@(R1)+
6e6: 27c3 d617       CMP   @#153027,R3
6ea: 2bf1 04ab       CMP   @-(PC),2253(R1)
6ee: f120            .WORD 170440
6f0: 2720            CMP   @(R4)+,-(R0)
6f2: a9f1 1796       CMPB  -(PC),13626(R1)
6f6: 26e4            CMP   @(R3)+,-(R4)
6f8: eb80            SUB   @-(SP),R0
6fa: d196            BISB  SP,(SP)+
6fc: fce7            .WORD 176347
6fe: f2ab            .WORD 171253
700: 04d9            BGE   003264
702: bce9 f1b8       BITB  -7110(R3),@-(R1)
706: 3696            BIT   @(R2)+,(SP)+
708: 6ff4 12f1 af96  ADD   @014775,-50152(R4)
70e: 0adc            DEC   @(R4)+
710: ff52            .WORD 177522
712: 2f3c 960a 2a31  CMP   @-64766(R4),@25061(R4)
718: 1e25 e116       MOV   @-17352(R0),-(R5)
71c: 1720            MOV   @(R4)+,-(R0)
71e: fa0f            .WORD 175017
720: 126d            MOV   (R1),@-(R5)
722: 0596            BLT   003120
724: a606            CMPB  @(R0)+,SP
726: f126            .WORD 170446
728: 00e4            SWAB  -(R4)
72a: b0b8 5706       BITB  R2,@53406(R0)
72e: 0039            .WORD 000071
730: c8c8            BICB  -(R3),(R0)
732: bc31 b0a0 1dc8  BITB  -47540(R0),16710(R1)
738: 0611            BGT   003534
73a: 4257 06b0       BIC   (R1),#003260
73e: 0633            BGT   003646
740: a050            CMPB  R1,(R0)+
742: 2b39 b857       CMP   @-(R4),@-43651(R1)
746: bebc 2704 2b07  BITB  @23404(R2),@25407(R4)
74c: bdb9 85bb bcf1  BITB  -75105(SP),@-41417(R1)
752: f1b4            .WORD 170664
754: 278c            CMP   @(SP)+,(R4)
756: 03af            BEQ   003266
758: 93d6            MOVB  (PC),(SP)+
75a: 11bc 6106       MOV   SP,@60406(R4)
75e: b01d            BITB  R0,@(R5)+
760: f117            .WORD 170427
762: d6f1 c894       BISB  @(R3)+,-33554(R1)
766: 0203            BNE   003556
768: b893            BITB  -(R2),(R3)+
76a: 3f80 2e72       BIT   @27162(SP),R0
76e: 9017 21f1       MOVB  R0,#361
772: 5619            BIS   @(R0)+,@(R1)+
774: bac8            BITB  @-(R3),(R0)
776: f0f0            .WORD 170360
778: eeb3 8295 7f82  SUB   @-76553(R2),77602(R3)
77e: c3e1            BICB  (PC),-(R1)
780: 478c            BIC   @(SP)+,(R4)
782: e1ed            SUB   PC,@-(R5)
784: a495            CMPB  (R2)+,(R5)+
786: a088            CMPB  R2,(R0)
788: f0cc            .WORD 170314
78a: 970f            MOVB  @(R4)+,(PC)
78c: 5619            BIS   @(R0)+,@(R1)+
78e: eeb3 e191 95c3  SUB   @-17157(R2),-65075(R3)
794: 9795            MOVB  @(SP)+,(R5)+
796: a49d            CMPB  (R2)+,@(R5)+
798: e1ed            SUB   PC,@-(R5)
79a: e1cc            SUB   PC,(R4)
79c: a099            CMPB  R2,@(R1)+
79e: 71c8            MUL   (R0),PC
7a0: f4fb            .WORD 172373
7a2: 0fa9            .WORD 007651
7a4: 93ac            MOVB  (SP),@-(R4)
7a6: fbb4            .WORD 175664
7a8: 93cb            MOVB  (PC),(R3)
7aa: f927            .WORD 174447
7ac: a0d9            CMPB  R3,@(R1)+
7ae: d6af            BISB  @(R2)+,@-(PC)
7b0: b128            BITB  R4,@-(R0)
7b2: 29f9 1f93       CMP   -(PC),@17623(R1)
7b6: 93d6            MOVB  (PC),(SP)+
7b8: ffba            .WORD 177672
7ba: acc6 931f       CMPB  -66341(R3),SP
7be: f4f9            .WORD 172371
7c0: a406            CMPB  (R0)+,SP
7c2: faa7            .WORD 175247
7c4: 1110            MOV   R4,(R0)+
7c6: 9693            MOVB  @(R2)+,(R3)+
7c8: b4bc a696       BITB  (R2)+,@-54552(R4)
7cc: ff36            .WORD 177466
7ce: 96ff d2f2       MOVB  @(R3)+,@155304
7d2: e7e7 fafa       SUB   @#175372,-(PC)
7d6: ac17 0386 f1c3  CMPB  1606(R0),#303
7dc: 17f1 c8dc d096  MOV   @#144334,-27552(R1)
7e2: 1cb0 11f1 11a8  MOV   10761(R2),10650(R0)
7e8: 68b0 d028       ADD   -(R2),-27730(R0)
7ec: 8647            BCC   004174
7ee: f8f1            .WORD 174361
7f0: 1c3f 863f 4794  MOV   -74701(R0),@047612
7f6: 7194            MUL   (R4)+,SP
7f8: 269d            CMP   @(R2)+,@(R5)+
7fa: e83a 4f94       SUB   -(R0),@47624(R2)
7fe: ff01            .WORD 177401
