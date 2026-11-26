; 8085, origin 0000h. Recursive direct-flow disassembly; DB = unclassified/data.
; No claim that all executable paths were discovered. See analyze.py for seeds.
; reset_vector
0000: f3          DI
0001: c3 e8 01    JMP  $01E8
0004: 00 00 00 00                                     DB $00,$00,$00,$00
0008: f3          DI
0009: e5          PUSH H
000A: 2a 10 5c    LHLD $5C10
000D: e3          XTHL
000E: c9          RET
000F: 00                                              DB $00
0010: fb          EI
0011: c9          RET
0012: 00 00 00 00 00 00                               DB $00,$00,$00,$00,$00,$00
0018: fb          EI
0019: c9          RET
001A: 00 00 00 00 00 00                               DB $00,$00,$00,$00,$00,$00
0020: f3          DI
0021: c3 8a 02    JMP  $028A
0024: c3 e5 03    JMP  $03E5
0027: 00                                              DB $00
0028: f3          DI
0029: c3 8a 02    JMP  $028A
002C: f3          DI
002D: c3 23 04    JMP  $0423
0030: f3          DI
0031: c3 93 04    JMP  $0493
0034: f3          DI
0035: c3 1d 04    JMP  $041D
0038: fb          EI
0039: c9          RET
003A: 00 00                                           DB $00,$00
003C: f3          DI
003D: c3 34 05    JMP  $0534
0040: c3 4e 13    JMP  $134E
0043: c3 53 13    JMP  $1353
0046: c3 5b 13    JMP  $135B
0049: c3 60 13    JMP  $1360
004C: c3 fd 0c    JMP  $0CFD
004F: c3 0a 0d    JMP  $0D0A
0052: c3 1e 0d    JMP  $0D1E
0055: c3 2d 0d    JMP  $0D2D
0058: c3 3a 0d    JMP  $0D3A
005B: c3 40 0d    JMP  $0D40
005E: c3 46 0d    JMP  $0D46
0061: c3 4c 0d    JMP  $0D4C
0064: c3 e6 0c    JMP  $0CE6
0067: c3 76 11    JMP  $1176
006A: c3 7f 11    JMP  $117F
006D: c3 87 11    JMP  $1187
0070: c3 8e 11    JMP  $118E
0073: c3 a7 11    JMP  $11A7
0076: c3 b7 11    JMP  $11B7
0079: c3 c2 11    JMP  $11C2
007C: c3 c9 11    JMP  $11C9
007F: c3 d7 11    JMP  $11D7
0082: c3 e5 11    JMP  $11E5
0085: c3 03 12    JMP  $1203
0088: c3 f5 11    JMP  $11F5
008B: c3 30 12    JMP  $1230
008E: c3 23 12    JMP  $1223
0091: c3 4d 12    JMP  $124D
0094: c3 51 12    JMP  $1251
0097: c3 55 12    JMP  $1255
009A: c3 28 14    JMP  $1428
009D: c3 da 13    JMP  $13DA
00A0: c3 bd 13    JMP  $13BD
00A3: c3 89 13    JMP  $1389
00A6: c3 a3 13    JMP  $13A3
00A9: c3 94 14    JMP  $1494
00AC: c3 e8 14    JMP  $14E8
00AF: c3 78 14    JMP  $1478
00B2: c3 52 0d    JMP  $0D52
00B5: c3 79 0d    JMP  $0D79
00B8: c3 8f 0d    JMP  $0D8F
00BB: c3 d0 0c    JMP  $0CD0
00BE: c3 6f 0c    JMP  $0C6F
00C1: c3 c2 0c    JMP  $0CC2
00C4: c3 42 0c    JMP  $0C42
00C7: c3 a8 0c    JMP  $0CA8
00CA: c3 ff 0b    JMP  $0BFF
00CD: c3 d9 0b    JMP  $0BD9
00D0: c3 fd 0d    JMP  $0DFD
00D3: c3 db 0d    JMP  $0DDB
00D6: c3 3f 0e    JMP  $0E3F
00D9: c3 57 0e    JMP  $0E57
00DC: c3 85 0e    JMP  $0E85
00DF: c3 a5 0b    JMP  $0BA5
00E2: c3 59 12    JMP  $1259
00E5: c3 91 12    JMP  $1291
00E8: c3 75 12    JMP  $1275
00EB: c3 97 12    JMP  $1297
00EE: c3 e9 12    JMP  $12E9
00F1: c3 9d 12    JMP  $129D
00F4: c3 f3 12    JMP  $12F3
00F7: c3 b5 12    JMP  $12B5
00FA: c3 01 13    JMP  $1301
00FD: c3 c3 12    JMP  $12C3
0100: c3 14 13    JMP  $1314
0103: c3 db 12    JMP  $12DB
0106: c3 01 15    JMP  $1501
0109: c3 12 15    JMP  $1512
010C: c3 44 15    JMP  $1544
010F: c3 c8 15    JMP  $15C8
0112: c3 bf 18    JMP  $18BF
0115: c3 2f 17    JMP  $172F
0118: c3 72 17    JMP  $1772
011B: c3 a2 17    JMP  $17A2
011E: c3 b6 17    JMP  $17B6
0121: c3 1c 10    JMP  $101C
0124: c3 50 10    JMP  $1050
0127: c3 a8 09    JMP  $09A8
012A: c3 05 16    JMP  $1605
012D: c3 11 12    JMP  $1211
0130: c3 3b 12    JMP  $123B
0133: c3 9f 0d    JMP  $0D9F
0136: c3 b2 0d    JMP  $0DB2
0139: c3 b5 09    JMP  $09B5
013C: c3 d3 0a    JMP  $0AD3
013F: c3 5d 0b    JMP  $0B5D
0142: c3 72 14    JMP  $1472
0145: c3 8d 14    JMP  $148D
0148: c3 b7 13    JMP  $13B7
014B: c3 d4 13    JMP  $13D4
014E: c3 14 14    JMP  $1414
0151: c3 d5 14    JMP  $14D5
0154: c3 ff 1d    JMP  $1DFF
0157: c3 57 0b    JMP  $0B57
015A: c3 d9 10    JMP  $10D9
015D: c3 2a 11    JMP  $112A
0160: c3 0a 19    JMP  $190A
0163: c3 35 1b    JMP  $1B35
0166: c3 e0 1c    JMP  $1CE0
0169: c3 25 1d    JMP  $1D25
016C: c3 aa 0b    JMP  $0BAA
016F: c3 de 0b    JMP  $0BDE
0172: c3 02 0e    JMP  $0E02
0175: c3 e0 0d    JMP  $0DE0
0178: c3 8a 0e    JMP  $0E8A
017B: c3 a8 20    JMP  $20A8
017E: c3 ba 20    JMP  $20BA
0181: c3 68 13    JMP  $1368
0184: c3 e4 01    JMP  $01E4
0187: c3 e4 01    JMP  $01E4
018A: c3 e4 01    JMP  $01E4
018D: c3 ef 0e    JMP  $0EEF
0190: c3 2a 18    JMP  $182A
0193: c3 4d 18    JMP  $184D
0196: c3 70 18    JMP  $1870
0199: c3 94 18    JMP  $1894
019C: c3 b2 16    JMP  $16B2
019F: c3 cd 16    JMP  $16CD
01A2: c3 12 1e    JMP  $1E12
01A5: c3 a4 1d    JMP  $1DA4
01A8: c3 36 16    JMP  $1636
01AB: c3 78 16    JMP  $1678
01AE: c3 e5 16    JMP  $16E5
01B1: c3 82 1e    JMP  $1E82
01B4: c3 9a 1e    JMP  $1E9A
01B7: c3 0e 17    JMP  $170E
01BA: c3 35 1f    JMP  $1F35
01BD: c3 5b 1f    JMP  $1F5B
01C0: c3 9c 1f    JMP  $1F9C
01C3: c3 80 1f    JMP  $1F80
01C6: c3 1c 1f    JMP  $1F1C
01C9: c3 ca 1f    JMP  $1FCA
01CC: c3 d0 1f    JMP  $1FD0
01CF: c3 d6 1f    JMP  $1FD6
01D2: c3 9b 06    JMP  $069B
01D5: c3 dc 06    JMP  $06DC
01D8: c3 77 07    JMP  $0777
01DB: c3 d5 07    JMP  $07D5
01DE: c3 91 08    JMP  $0891
01E1: c3 c0 06    JMP  $06C0
01E4: 37          STC
01E5: 3f          CMC
01E6: c9          RET
01E7: 00                                              DB $00
; reset
01E8: f3          DI
01E9: 3e 08       MVI  A,$08
01EB: d3 50       OUT  $50
01ED: 3e df       MVI  A,$DF
01EF: d3 60       OUT  $60
01F1: d3 3e       OUT  $3E
01F3: d3 3a       OUT  $3A
01F5: 3e 71       MVI  A,$71
01F7: d3 30       OUT  $30
01F9: 3e 7f       MVI  A,$7F
01FB: d3 31       OUT  $31
01FD: 3e 6d       MVI  A,$6D
01FF: d3 32       OUT  $32
0201: 3e 18       MVI  A,$18
0203: d3 33       OUT  $33
0205: 3e 51       MVI  A,$51
0207: d3 34       OUT  $34
0209: 3e 28       MVI  A,$28
020B: d3 35       OUT  $35
020D: 3e 18       MVI  A,$18
020F: d3 36       OUT  $36
0211: 97          SUB  A
0212: d3 3c       OUT  $3C
0214: d3 3d       OUT  $3D
0216: d3 3e       OUT  $3E
0218: 31 ff 5f    LXI  SP,$5FFF
021B: 21 00 80    LXI  H,$8000
021E: 7e          MOV  A,M
021F: 23          INX  H
0220: 86          ADD  M
0221: c2 2d 02    JNZ  $022D
0224: d2 2d 02    JNC  $022D
0227: cd 07 09    CALL $0907
022A: c3 02 80    JMP  $8002
022D: 2a 0c 5e    LHLD $5E0C
0230: 7c          MOV  A,H
0231: 85          ADD  L
0232: 3f          CMC
0233: c2 39 02    JNZ  $0239
0236: d2 3c 02    JNC  $023C
0239: cd 5f 06    CALL $065F
023C: cd 07 09    CALL $0907
023F: f5          PUSH PSW
0240: d2 56 02    JNC  $0256
0243: 21 7f 02    LXI  H,$027F
0246: cd e8 14    CALL $14E8
0249: f1          POP  PSW
024A: f5          PUSH PSW
024B: cd 5b 1f    CALL $1F5B
024E: 3e 18       MVI  A,$18
0250: cd e6 0c    CALL $0CE6
0253: da 4e 02    JC   $024E
0256: 21 80 80    LXI  H,$8080
0259: 22 0c 5e    SHLD $5E0C
025C: 21 00 21    LXI  H,$2100
025F: cd 71 02    CALL $0271
0262: 21 00 c0    LXI  H,$C000
0265: cd 71 02    CALL $0271
0268: 21 7b 02    LXI  H,$027B
026B: cd e8 14    CALL $14E8
026E: c3 6e 02    JMP  $026E
; probe_module_signature_and_enter
0271: 7e          MOV  A,M
0272: 23          INX  H
0273: 86          ADD  M
0274: c0          RNZ
0275: d0          RNC
0276: 23          INX  H
0277: d1          POP  D
0278: f1          POP  PSW
0279: fb          EI
027A: e9          PCHL
027B: 3f 3f 3f 00 45 52 52 4f 52 20 4e 4f 2e 3a 00    DB $3F,$3F,$3F,$00,$45,$52,$52,$4F,$52,$20,$4E,$4F,$2E,$3A,$00
; interrupt_dispatch
028A: e5          PUSH H
028B: 21 21 5e    LXI  H,$5E21
028E: 74          MOV  M,H
028F: 2a 14 5c    LHLD $5C14
0292: e3          XTHL
0293: c9          RET
0294: f5          PUSH PSW
0295: c5          PUSH B
0296: e5          PUSH H
0297: 97          SUB  A
0298: d3 01       OUT  $01
029A: db 01       IN   $01
029C: 47          MOV  B,A
029D: e6 02       ANI  $02
029F: ca cc 02    JZ   $02CC
02A2: 3e 02       MVI  A,$02
02A4: d3 03       OUT  $03
02A6: db 03       IN   $03
02A8: e6 0e       ANI  $0E
02AA: fe 0c       CPI  $0C
02AC: ca d5 02    JZ   $02D5
02AF: fe 08       CPI  $08
02B1: ca 3f 03    JZ   $033F
02B4: fe 0e       CPI  $0E
02B6: ca 95 03    JZ   $0395
02B9: fe 04       CPI  $04
02BB: ca 27 03    JZ   $0327
02BE: a7          ANA  A
02BF: ca 7f 03    JZ   $037F
02C2: fe 06       CPI  $06
02C4: ca aa 03    JZ   $03AA
02C7: fe 0a       CPI  $0A
02C9: ca bf 03    JZ   $03BF
02CC: 3e 38       MVI  A,$38
02CE: d3 01       OUT  $01
02D0: e1          POP  H
02D1: c1          POP  B
02D2: f1          POP  PSW
02D3: fb          EI
02D4: c9          RET
02D5: db 00       IN   $00
02D7: 47          MOV  B,A
02D8: 3a 1b 5e    LDA  $5E1B
02DB: a0          ANA  B
02DC: 2a 1e 5c    LHLD $5C1E
02DF: a7          ANA  A
02E0: cd e4 03    CALL $03E4
02E3: da 97 02    JC   $0297
02E6: 47          MOV  B,A
02E7: 3a 13 5f    LDA  $5F13
02EA: a7          ANA  A
02EB: ca 12 03    JZ   $0312
02EE: 3a 1d 5e    LDA  $5E1D
02F1: a7          ANA  A
02F2: c2 12 03    JNZ  $0312
02F5: 3a 2e 5d    LDA  $5D2E
02F8: 21 3c 5e    LXI  H,$5E3C
02FB: be          CMP  M
02FC: da 12 03    JC   $0312
02FF: 3e 13       MVI  A,$13
0301: cd da 03    CALL $03DA
0304: da 0d 03    JC   $030D
0307: cd de 0b    CALL $0BDE
030A: da 12 03    JC   $0312
030D: 3e 01       MVI  A,$01
030F: 32 1d 5e    STA  $5E1D
0312: 78          MOV  A,B
0313: cd 34 0f    CALL $0F34
0316: da 1c 03    JC   $031C
0319: c3 97 02    JMP  $0297
031C: 2a 26 5c    LHLD $5C26
031F: 3e 80       MVI  A,$80
0321: cd e4 03    CALL $03E4
0324: c3 97 02    JMP  $0297
0327: db 02       IN   $02
0329: 47          MOV  B,A
032A: 3a 1c 5e    LDA  $5E1C
032D: a0          ANA  B
032E: cd 61 0f    CALL $0F61
0331: da 37 03    JC   $0337
0334: c3 97 02    JMP  $0297
0337: 2a 28 5c    LHLD $5C28
033A: 3e 80       MVI  A,$80
033C: c3 21 03    JMP  $0321
033F: 3a fb 5e    LDA  $5EFB
0342: a7          ANA  A
0343: ca 52 03    JZ   $0352
0346: 3a 24 5e    LDA  $5E24
0349: d3 00       OUT  $00
034B: 97          SUB  A
034C: 32 fb 5e    STA  $5EFB
034F: c3 97 02    JMP  $0297
0352: 3a 51 5d    LDA  $5D51
0355: fe 01       CPI  $01
0357: c2 78 03    JNZ  $0378
035A: 3a 52 5d    LDA  $5D52
035D: a7          ANA  A
035E: ca 69 03    JZ   $0369
0361: 3e 02       MVI  A,$02
0363: 32 51 5d    STA  $5D51
0366: c3 78 03    JMP  $0378
0369: cd 12 0f    CALL $0F12
036C: da 74 03    JC   $0374
036F: d3 00       OUT  $00
0371: c3 97 02    JMP  $0297
0374: 97          SUB  A
0375: 32 51 5d    STA  $5D51
0378: 3e 28       MVI  A,$28
037A: d3 01       OUT  $01
037C: c3 97 02    JMP  $0297
037F: cd 29 0f    CALL $0F29
0382: da 8a 03    JC   $038A
0385: d3 02       OUT  $02
0387: c3 97 02    JMP  $0297
038A: 3e 28       MVI  A,$28
038C: d3 03       OUT  $03
038E: 97          SUB  A
038F: 32 99 5d    STA  $5D99
0392: c3 97 02    JMP  $0297
0395: 3e 01       MVI  A,$01
0397: d3 01       OUT  $01
0399: db 01       IN   $01
039B: e6 70       ANI  $70
039D: 2a 26 5c    LHLD $5C26
03A0: cd e4 03    CALL $03E4
03A3: 3e 30       MVI  A,$30
03A5: d3 01       OUT  $01
03A7: c3 97 02    JMP  $0297
03AA: 3e 01       MVI  A,$01
03AC: d3 03       OUT  $03
03AE: db 03       IN   $03
03B0: e6 70       ANI  $70
03B2: 2a 28 5c    LHLD $5C28
03B5: cd e4 03    CALL $03E4
03B8: 3e 30       MVI  A,$30
03BA: d3 03       OUT  $03
03BC: c3 97 02    JMP  $0297
03BF: 78          MOV  A,B
03C0: e6 28       ANI  $28
03C2: 47          MOV  B,A
03C3: 3a f7 5d    LDA  $5DF7
03C6: e6 03       ANI  $03
03C8: b0          ORA  B
03C9: 32 f7 5d    STA  $5DF7
03CC: cd d6 03    CALL $03D6
03CF: 3e 10       MVI  A,$10
03D1: d3 01       OUT  $01
03D3: c3 97 02    JMP  $0297
03D6: 2a 22 5c    LHLD $5C22
03D9: e9          PCHL
03DA: e5          PUSH H
03DB: a7          ANA  A
03DC: 2a 24 5c    LHLD $5C24
03DF: cd e4 03    CALL $03E4
03E2: e1          POP  H
03E3: c9          RET
03E4: e9          PCHL
03E5: e5          PUSH H
03E6: f5          PUSH PSW
03E7: 2a 0c 5e    LHLD $5E0C
03EA: 7c          MOV  A,H
03EB: fe 80       CPI  $80
03ED: c2 09 04    JNZ  $0409
03F0: 85          ADD  L
03F1: c2 09 04    JNZ  $0409
03F4: 3a 20 5e    LDA  $5E20
03F7: a7          ANA  A
03F8: ca 03 04    JZ   $0403
03FB: 3e 02       MVI  A,$02
03FD: 32 20 5e    STA  $5E20
0400: f1          POP  PSW
0401: e1          POP  H
0402: c9          RET
0403: 2a 12 5c    LHLD $5C12
0406: cd 1c 04    CALL $041C
0409: 20          RIM
040A: e6 08       ANI  $08
040C: ca 10 04    JZ   $0410
040F: fb          EI
0410: f1          POP  PSW
0411: e1          POP  H
0412: c9          RET
0413: c5          PUSH B
0414: 01 08 d6    LXI  B,$D608
0417: cd 12 1f    CALL $1F12
041A: c1          POP  B
041B: c9          RET
041C: e9          PCHL
041D: e5          PUSH H
041E: 2a 1c 5c    LHLD $5C1C
0421: e3          XTHL
0422: c9          RET
0423: e5          PUSH H
0424: 21 21 5e    LXI  H,$5E21
0427: 74          MOV  M,H
0428: 2a 16 5c    LHLD $5C16
042B: e3          XTHL
042C: c9          RET
042D: f5          PUSH PSW
042E: e5          PUSH H
042F: db 10       IN   $10
0431: f5          PUSH PSW
0432: e6 70       ANI  $70
0434: c4 61 04    CNZ  $0461
0437: f1          POP  PSW
0438: e6 01       ANI  $01
043A: ca 5d 04    JZ   $045D
043D: db 11       IN   $11
043F: 67          MOV  H,A
0440: e6 fc       ANI  $FC
0442: fe dc       CPI  $DC
0444: ca 65 04    JZ   $0465
0447: 7c          MOV  A,H
0448: 2a 20 5c    LHLD $5C20
044B: a7          ANA  A
044C: cd 64 04    CALL $0464
044F: da 5d 04    JC   $045D
0452: cd ef 0e    CALL $0EEF
0455: d2 5d 04    JNC  $045D
0458: 3e 80       MVI  A,$80
045A: cd 61 04    CALL $0461
045D: e1          POP  H
045E: f1          POP  PSW
045F: fb          EI
0460: c9          RET
0461: 2a 2a 5c    LHLD $5C2A
0464: e9          PCHL
0465: 7c          MOV  A,H
0466: e6 01       ANI  $01
0468: 32 0b 5e    STA  $5E0B
046B: 7c          MOV  A,H
046C: e6 02       ANI  $02
046E: ca 5d 04    JZ   $045D
0471: 3a 0e 5e    LDA  $5E0E
0474: f6 08       ORI  $08
0476: d3 60       OUT  $60
0478: 3a 10 5e    LDA  $5E10
047B: e6 bb       ANI  $BB
047D: d3 50       OUT  $50
047F: db 10       IN   $10
0481: e6 01       ANI  $01
0483: ca 71 04    JZ   $0471
0486: db 11       IN   $11
0488: 67          MOV  H,A
0489: e6 fc       ANI  $FC
048B: fe dc       CPI  $DC
048D: c2 71 04    JNZ  $0471
0490: c3 65 04    JMP  $0465
0493: e5          PUSH H
0494: 2a 18 5c    LHLD $5C18
0497: e3          XTHL
0498: c9          RET
0499: f5          PUSH PSW
049A: c5          PUSH B
049B: db 18       IN   $18
049D: 47          MOV  B,A
049E: e6 02       ANI  $02
04A0: c4 ba 04    CNZ  $04BA
04A3: 3a 17 5f    LDA  $5F17
04A6: a7          ANA  A
04A7: ca b6 04    JZ   $04B6
04AA: 78          MOV  A,B
04AB: e6 01       ANI  $01
04AD: c4 f6 04    CNZ  $04F6
04B0: 78          MOV  A,B
04B1: e6 70       ANI  $70
04B3: c4 23 05    CNZ  $0523
04B6: c1          POP  B
04B7: f1          POP  PSW
04B8: fb          EI
04B9: c9          RET
04BA: 0e 80       MVI  C,$80
04BC: 3a 09 5f    LDA  $5F09
04BF: a7          ANA  A
04C0: c2 c5 04    JNZ  $04C5
04C3: 0e 00       MVI  C,$00
04C5: 3a e0 5d    LDA  $5DE0
04C8: fe 01       CPI  $01
04CA: da 2c 05    JC   $052C
04CD: 0e 00       MVI  C,$00
04CF: c0          RNZ
04D0: 3a 17 5f    LDA  $5F17
04D3: a7          ANA  A
04D4: c2 e8 04    JNZ  $04E8
04D7: cd 8f 0d    CALL $0D8F
04DA: d2 e8 04    JNC  $04E8
04DD: e5          PUSH H
04DE: 21 68 10    LXI  H,$1068
04E1: 22 29 5e    SHLD $5E29
04E4: e1          POP  H
04E5: c3 2c 05    JMP  $052C
04E8: cd e3 0f    CALL $0FE3
04EB: da f1 04    JC   $04F1
04EE: d3 19       OUT  $19
04F0: c9          RET
04F1: 97          SUB  A
04F2: 32 e0 5d    STA  $5DE0
04F5: c9          RET
04F6: 3a 09 5f    LDA  $5F09
04F9: a7          ANA  A
04FA: db 19       IN   $19
04FC: ca 1d 05    JZ   $051D
04FF: fe 13       CPI  $13
0501: c2 0e 05    JNZ  $050E
0504: 0e 80       MVI  C,$80
0506: cd 2c 05    CALL $052C
0509: 3e 02       MVI  A,$02
050B: c3 f2 04    JMP  $04F2
050E: fe 11       CPI  $11
0510: c2 1d 05    JNZ  $051D
0513: 0e a0       MVI  C,$A0
0515: cd 2c 05    CALL $052C
0518: 3e 01       MVI  A,$01
051A: c3 f2 04    JMP  $04F2
051D: cd 78 0f    CALL $0F78
0520: d0          RNC
0521: 3e 80       MVI  A,$80
0523: e5          PUSH H
0524: 2a 2c 5c    LHLD $5C2C
0527: cd 33 05    CALL $0533
052A: e1          POP  H
052B: c9          RET
052C: 3a 11 5e    LDA  $5E11
052F: b1          ORA  C
0530: d3 18       OUT  $18
0532: c9          RET
0533: e9          PCHL
; timer_interrupt
0534: e5          PUSH H
0535: f5          PUSH PSW
0536: c5          PUSH B
0537: d5          PUSH D
0538: 3e 01       MVI  A,$01
053A: 32 f5 5d    STA  $5DF5
053D: db 60       IN   $60
053F: e6 0c       ANI  $0C
0541: 0f          RRC
0542: 0f          RRC
0543: 67          MOV  H,A
0544: 3a f7 5d    LDA  $5DF7
0547: e6 03       ANI  $03
0549: bc          CMP  H
054A: ca 59 05    JZ   $0559
054D: 3a f7 5d    LDA  $5DF7
0550: e6 28       ANI  $28
0552: b4          ORA  H
0553: 32 f7 5d    STA  $5DF7
0556: cd 5b 06    CALL $065B
0559: 3a 1a 5e    LDA  $5E1A
055C: d3 36       OUT  $36
055E: 2a 16 5e    LHLD $5E16
0561: 84          ADD  H
0562: fe 19       CPI  $19
0564: da 69 05    JC   $0569
0567: d6 19       SUI  $19
0569: d3 3d       OUT  $3D
056B: 7d          MOV  A,L
056C: 3d          DCR  A
056D: d3 3c       OUT  $3C
056F: 3a 0f 5e    LDA  $5E0F
0572: a7          ANA  A
0573: c2 ec 05    JNZ  $05EC
0576: 3a 19 5e    LDA  $5E19
0579: a7          ANA  A
057A: 3a 0e 5e    LDA  $5E0E
057D: ca 85 05    JZ   $0585
0580: f6 08       ORI  $08
0582: c3 87 05    JMP  $0587
0585: e6 f7       ANI  $F7
0587: 4f          MOV  C,A
0588: 3a f9 5d    LDA  $5DF9
058B: 07          RLC
058C: e6 06       ANI  $06
058E: 32 f9 5d    STA  $5DF9
0591: fe 02       CPI  $02
0593: ca a7 05    JZ   $05A7
0596: a7          ANA  A
0597: c2 ab 05    JNZ  $05AB
059A: 3a 18 5e    LDA  $5E18
059D: a7          ANA  A
059E: c2 a7 05    JNZ  $05A7
05A1: 79          MOV  A,C
05A2: f6 10       ORI  $10
05A4: c3 aa 05    JMP  $05AA
05A7: 79          MOV  A,C
05A8: e6 ef       ANI  $EF
05AA: 4f          MOV  C,A
05AB: 3a 21 5e    LDA  $5E21
05AE: a7          ANA  A
05AF: c2 d9 05    JNZ  $05D9
05B2: 3a 0d 5f    LDA  $5F0D
05B5: a7          ANA  A
05B6: c2 e6 05    JNZ  $05E6
05B9: 2a 22 5e    LHLD $5E22
05BC: 2b          DCX  H
05BD: 22 22 5e    SHLD $5E22
05C0: 7c          MOV  A,H
05C1: b5          ORA  L
05C2: c2 e6 05    JNZ  $05E6
05C5: 79          MOV  A,C
05C6: f6 08       ORI  $08
05C8: 4f          MOV  C,A
05C9: 3a 10 5e    LDA  $5E10
05CC: e6 bb       ANI  $BB
05CE: d3 50       OUT  $50
05D0: 21 01 00    LXI  H,$0001
05D3: 22 22 5e    SHLD $5E22
05D6: c3 e6 05    JMP  $05E6
05D9: 21 21 a4    LXI  H,$A421
05DC: 22 22 5e    SHLD $5E22
05DF: 3a 10 5e    LDA  $5E10
05E2: e6 fb       ANI  $FB
05E4: d3 50       OUT  $50
05E6: 79          MOV  A,C
05E7: 32 0e 5e    STA  $5E0E
05EA: d3 60       OUT  $60
05EC: 97          SUB  A
05ED: 32 21 5e    STA  $5E21
05F0: 2a 29 5e    LHLD $5E29
05F3: cd 52 06    CALL $0652
05F6: 22 29 5e    SHLD $5E29
05F9: da 0f 06    JC   $060F
05FC: ca 1d 06    JZ   $061D
05FF: cd 8f 0d    CALL $0D8F
0602: da 1d 06    JC   $061D
0605: 3a 11 5e    LDA  $5E11
0608: f6 20       ORI  $20
060A: d3 18       OUT  $18
060C: c3 17 06    JMP  $0617
060F: 3e 08       MVI  A,$08
0611: cd 23 05    CALL $0523
0614: cd df 0a    CALL $0ADF
0617: 21 00 00    LXI  H,$0000
061A: 22 29 5e    SHLD $5E29
061D: 2a 00 5c    LHLD $5C00
0620: cd 52 06    CALL $0652
0623: 22 00 5c    SHLD $5C00
0626: 2a 02 5c    LHLD $5C02
0629: dc 5e 06    CC   $065E
062C: 2a 04 5c    LHLD $5C04
062F: cd 52 06    CALL $0652
0632: 22 04 5c    SHLD $5C04
0635: 2a 06 5c    LHLD $5C06
0638: dc 5e 06    CC   $065E
063B: 2a 08 5c    LHLD $5C08
063E: cd 52 06    CALL $0652
0641: 22 08 5c    SHLD $5C08
0644: 2a 0a 5c    LHLD $5C0A
0647: dc 5e 06    CC   $065E
064A: d1          POP  D
064B: c1          POP  B
064C: f1          POP  PSW
064D: 2a 1a 5c    LHLD $5C1A
0650: e3          XTHL
0651: c9          RET
; decrement_timer
0652: 7c          MOV  A,H
0653: b5          ORA  L
0654: c8          RZ
0655: 2b          DCX  H
0656: 7c          MOV  A,H
0657: b5          ORA  L
0658: c0          RNZ
0659: 37          STC
065A: c9          RET
065B: 2a 22 5c    LHLD $5C22
065E: e9          PCHL
; cold_selftests
065F: 21 00 58    LXI  H,$5800
0662: 11 f0 5f    LXI  D,$5FF0
0665: cd 02 07    CALL $0702
0668: 3e 08       MVI  A,$08
066A: cd 07 09    CALL $0907
066D: d4 77 07    CNC  $0777
0670: f5          PUSH PSW
0671: 3a 07 5f    LDA  $5F07
0674: 32 03 5f    STA  $5F03
0677: af          XRA  A
0678: 32 13 5f    STA  $5F13
067B: cd b5 09    CALL $09B5
067E: f1          POP  PSW
067F: d4 d5 07    CNC  $07D5
0682: d4 91 08    CNC  $0891
0685: d4 dc 06    CNC  $06DC
0688: d4 9b 06    CNC  $069B
068B: c9          RET
068C: f1          POP  PSW
068D: e1          POP  H
068E: d1          POP  D
068F: c1          POP  B
0690: 37          STC
0691: 3f          CMC
0692: c9          RET
0693: 47          MOV  B,A
0694: f1          POP  PSW
0695: 78          MOV  A,B
0696: e1          POP  H
0697: d1          POP  D
0698: c1          POP  B
0699: 37          STC
069A: c9          RET
; rom_checksum_test
069B: c5          PUSH B
069C: d5          PUSH D
069D: e5          PUSH H
069E: f5          PUSH PSW
069F: 97          SUB  A
06A0: 32 01 5e    STA  $5E01
06A3: 06 50       MVI  B,$50
06A5: cd 51 07    CALL $0751
06A8: da b3 06    JC   $06B3
06AB: fe 80       CPI  $80
06AD: cc c0 06    CZ   $06C0
06B0: c3 a5 06    JMP  $06A5
06B3: 3a 01 5e    LDA  $5E01
06B6: fe aa       CPI  $AA
06B8: ca 8c 06    JZ   $068C
06BB: 3e 19       MVI  A,$19
06BD: c3 93 06    JMP  $0693
; accumulate_checksum
06C0: f5          PUSH PSW
06C1: e5          PUSH H
06C2: 97          SUB  A
06C3: 86          ADD  M
06C4: 23          INX  H
06C5: f5          PUSH PSW
06C6: cd ca 1f    CALL $1FCA
06C9: ca d0 06    JZ   $06D0
06CC: f1          POP  PSW
06CD: c3 c3 06    JMP  $06C3
06D0: f1          POP  PSW
06D1: 67          MOV  H,A
06D2: 3a 01 5e    LDA  $5E01
06D5: 84          ADD  H
06D6: 32 01 5e    STA  $5E01
06D9: e1          POP  H
06DA: f1          POP  PSW
06DB: c9          RET
; descriptor_ram_tests
06DC: c5          PUSH B
06DD: d5          PUSH D
06DE: e5          PUSH H
06DF: f5          PUSH PSW
06E0: cd 40 07    CALL $0740
06E3: 3e 1a       MVI  A,$1A
06E5: c2 93 06    JNZ  $0693
06E8: 06 50       MVI  B,$50
06EA: cd 51 07    CALL $0751
06ED: da 8c 06    JC   $068C
06F0: fe 40       CPI  $40
06F2: c2 ea 06    JNZ  $06EA
06F5: cd 02 07    CALL $0702
06F8: d2 ea 06    JNC  $06EA
06FB: 78          MOV  A,B
06FC: d6 50       SUI  $50
06FE: 0f          RRC
06FF: c3 93 06    JMP  $0693
; ram_address_pattern_test
0702: e5          PUSH H
0703: 75          MOV  M,L
0704: 23          INX  H
0705: cd ca 1f    CALL $1FCA
0708: c2 03 07    JNZ  $0703
070B: e1          POP  H
070C: e5          PUSH H
070D: 7e          MOV  A,M
070E: bd          CMP  L
070F: c2 36 07    JNZ  $0736
0712: 23          INX  H
0713: cd ca 1f    CALL $1FCA
0716: c2 0d 07    JNZ  $070D
0719: e1          POP  H
071A: e5          PUSH H
071B: 74          MOV  M,H
071C: 23          INX  H
071D: cd ca 1f    CALL $1FCA
0720: c2 1b 07    JNZ  $071B
0723: e1          POP  H
0724: e5          PUSH H
0725: 7e          MOV  A,M
0726: bc          CMP  H
0727: c2 36 07    JNZ  $0736
072A: 23          INX  H
072B: cd ca 1f    CALL $1FCA
072E: c2 25 07    JNZ  $0725
0731: e1          POP  H
0732: a7          ANA  A
0733: c3 38 07    JMP  $0738
0736: e1          POP  H
0737: 37          STC
0738: f5          PUSH PSW
0739: e5          PUSH H
073A: cd 2b 1f    CALL $1F2B
073D: e1          POP  H
073E: f1          POP  PSW
073F: c9          RET
; validate_memory_descriptors
0740: 21 50 00    LXI  H,$0050
0743: cd 1c 10    CALL $101C
0746: fe 80       CPI  $80
0748: c0          RNZ
0749: 2e 5f       MVI  L,$5F
074B: cd 1c 10    CALL $101C
074E: fe 80       CPI  $80
0750: c9          RET
; next_memory_descriptor
0751: 04          INR  B
0752: 78          MOV  A,B
0753: fe 5f       CPI  $5F
0755: 37          STC
0756: c8          RZ
0757: 68          MOV  L,B
0758: 26 00       MVI  H,$00
075A: cd 1c 10    CALL $101C
075D: 4f          MOV  C,A
075E: 04          INR  B
075F: 68          MOV  L,B
0760: cd 1c 10    CALL $101C
0763: 67          MOV  H,A
0764: 2e 00       MVI  L,$00
0766: 79          MOV  A,C
0767: e6 1f       ANI  $1F
0769: 07          RLC
076A: 07          RLC
076B: 57          MOV  D,A
076C: 1e 00       MVI  E,$00
076E: e5          PUSH H
076F: 19          DAD  D
0770: eb          XCHG
0771: e1          POP  H
0772: 79          MOV  A,C
0773: e6 c0       ANI  $C0
0775: a7          ANA  A
0776: c9          RET
; video_character_attribute_test
0777: c5          PUSH B
0778: d5          PUSH D
0779: e5          PUSH H
077A: f5          PUSH PSW
077B: cd a8 20    CALL $20A8
077E: 0e 03       MVI  C,$03
0780: cd 7d 20    CALL $207D
0783: 0e 00       MVI  C,$00
0785: 21 00 60    LXI  H,$6000
0788: 54          MOV  D,H
0789: 5d          MOV  E,L
078A: d5          PUSH D
078B: e5          PUSH H
078C: 79          MOV  A,C
078D: d3 70       OUT  $70
078F: 77          MOV  M,A
0790: 0c          INR  C
0791: cd dc 1e    CALL $1EDC
0794: cd ca 1f    CALL $1FCA
0797: c2 8c 07    JNZ  $078C
079A: e1          POP  H
079B: d1          POP  D
079C: 0e 00       MVI  C,$00
079E: 7e          MOV  A,M
079F: b9          CMP  C
07A0: c2 c0 07    JNZ  $07C0
07A3: 47          MOV  B,A
07A4: db 70       IN   $70
07A6: b8          CMP  B
07A7: c2 c5 07    JNZ  $07C5
07AA: 0c          INR  C
07AB: cd dc 1e    CALL $1EDC
07AE: cd ca 1f    CALL $1FCA
07B1: c2 9e 07    JNZ  $079E
07B4: cd ba 20    CALL $20BA
07B7: cd 91 20    CALL $2091
07BA: cd 12 15    CALL $1512
07BD: c3 8c 06    JMP  $068C
07C0: 3e 0f       MVI  A,$0F
07C2: c3 c7 07    JMP  $07C7
07C5: 3e 11       MVI  A,$11
07C7: f5          PUSH PSW
07C8: cd ba 20    CALL $20BA
07CB: cd 91 20    CALL $2091
07CE: cd 12 15    CALL $1512
07D1: f1          POP  PSW
07D2: c3 93 06    JMP  $0693
; serial_loopback_test
07D5: f3          DI
07D6: c5          PUSH B
07D7: d5          PUSH D
07D8: e5          PUSH H
07D9: f5          PUSH PSW
07DA: 3a 0e 5e    LDA  $5E0E
07DD: e6 bf       ANI  $BF
07DF: 32 0e 5e    STA  $5E0E
07E2: d3 60       OUT  $60
07E4: cd 4d 0a    CALL $0A4D
07E7: cd 6f 0c    CALL $0C6F
07EA: d2 e7 07    JNC  $07E7
07ED: 21 00 00    LXI  H,$0000
07F0: 22 52 5d    SHLD $5D52
07F3: 22 54 5d    SHLD $5D54
07F6: 2a 26 5c    LHLD $5C26
07F9: 22 05 5e    SHLD $5E05
07FC: 21 8d 08    LXI  H,$088D
07FF: 22 26 5c    SHLD $5C26
0802: 06 00       MVI  B,$00
0804: cd 69 08    CALL $0869
0807: ca 3f 08    JZ   $083F
080A: 06 80       MVI  B,$80
080C: cd 69 08    CALL $0869
080F: c2 3f 08    JNZ  $083F
0812: 06 02       MVI  B,$02
0814: cd 69 08    CALL $0869
0817: c2 3f 08    JNZ  $083F
081A: 97          SUB  A
081B: 32 07 5e    STA  $5E07
081E: 3e 55       MVI  A,$55
0820: cd 80 08    CALL $0880
0823: da 44 08    JC   $0844
0826: fe 55       CPI  $55
0828: c2 49 08    JNZ  $0849
082B: 3e 2a       MVI  A,$2A
082D: cd 80 08    CALL $0880
0830: da 44 08    JC   $0844
0833: fe 2a       CPI  $2A
0835: c2 49 08    JNZ  $0849
0838: 3a 07 5e    LDA  $5E07
083B: a7          ANA  A
083C: ca 4c 08    JZ   $084C
083F: 3e 12       MVI  A,$12
0841: c3 4b 08    JMP  $084B
0844: 3e 14       MVI  A,$14
0846: c3 4b 08    JMP  $084B
0849: 3e 13       MVI  A,$13
084B: 37          STC
084C: f5          PUSH PSW
084D: f3          DI
084E: 2a 05 5e    LHLD $5E05
0851: 22 26 5c    SHLD $5C26
0854: 3a 0e 5e    LDA  $5E0E
0857: f6 40       ORI  $40
0859: 32 0e 5e    STA  $5E0E
085C: d3 60       OUT  $60
085E: cd 4d 0a    CALL $0A4D
0861: f1          POP  PSW
0862: fb          EI
0863: d2 8c 06    JNC  $068C
0866: c3 93 06    JMP  $0693
0869: 3e 05       MVI  A,$05
086B: d3 01       OUT  $01
086D: 3a 1f 5e    LDA  $5E1F
0870: e6 6d       ANI  $6D
0872: f6 08       ORI  $08
0874: b0          ORA  B
0875: d3 01       OUT  $01
0877: 3e 10       MVI  A,$10
0879: d3 01       OUT  $01
087B: db 60       IN   $60
087D: e6 02       ANI  $02
087F: c9          RET
0880: cd 42 0c    CALL $0C42
0883: 01 80 88    LXI  B,$8880
0886: cd 12 1f    CALL $1F12
0889: cd 6f 0c    CALL $0C6F
088C: c9          RET
088D: 32 07 5e    STA  $5E07
0890: c9          RET
; keyboard_test
0891: c5          PUSH B
0892: d5          PUSH D
0893: e5          PUSH H
0894: f5          PUSH PSW
0895: af          XRA  A
0896: 32 07 5e    STA  $5E07
0899: cd d0 0c    CALL $0CD0
089C: d2 95 08    JNC  $0895
089F: 2a 2a 5c    LHLD $5C2A
08A2: 22 05 5e    SHLD $5E05
08A5: 21 8d 08    LXI  H,$088D
08A8: 22 2a 5c    SHLD $5C2A
08AB: fb          EI
08AC: 3a 0a 5e    LDA  $5E0A
08AF: a7          ANA  A
08B0: 3e 2d       MVI  A,$2D
08B2: ca b7 08    JZ   $08B7
08B5: 3e 81       MVI  A,$81
08B7: 01 00 44    LXI  B,$4400
08BA: cd fd 08    CALL $08FD
08BD: da ee 08    JC   $08EE
08C0: fe aa       CPI  $AA
08C2: 3e 17       MVI  A,$17
08C4: c2 f0 08    JNZ  $08F0
08C7: 3a 0a 5e    LDA  $5E0A
08CA: a7          ANA  A
08CB: 3e 2e       MVI  A,$2E
08CD: ca d2 08    JZ   $08D2
08D0: 3e 82       MVI  A,$82
08D2: 01 40 39    LXI  B,$3940
08D5: cd fd 08    CALL $08FD
08D8: da ee 08    JC   $08EE
08DB: fe aa       CPI  $AA
08DD: 3e 18       MVI  A,$18
08DF: c2 f0 08    JNZ  $08F0
08E2: 3a 07 5e    LDA  $5E07
08E5: a7          ANA  A
08E6: ca f1 08    JZ   $08F1
08E9: 3e 15       MVI  A,$15
08EB: c3 f0 08    JMP  $08F0
08EE: 3e 16       MVI  A,$16
08F0: 37          STC
08F1: 2a 05 5e    LHLD $5E05
08F4: 22 2a 5c    SHLD $5C2A
08F7: d2 8c 06    JNC  $068C
08FA: c3 93 06    JMP  $0693
08FD: cd e6 0c    CALL $0CE6
0900: cd 12 1f    CALL $1F12
0903: cd d0 0c    CALL $0CD0
0906: c9          RET
; initialize_services
0907: f3          DI
0908: f5          PUSH PSW
0909: 21 00 5c    LXI  H,$5C00
090C: 11 cf 5f    LXI  D,$5FCF
090F: cd 2b 1f    CALL $1F2B
0912: 3e 0a       MVI  A,$0A
0914: 30          SIM
0915: 3e f2       MVI  A,$F2
0917: 32 0e 5e    STA  $5E0E
091A: d3 60       OUT  $60
091C: 3e bf       MVI  A,$BF
091E: 32 3c 5e    STA  $5E3C
0921: 3e 18       MVI  A,$18
0923: 32 1a 5e    STA  $5E1A
0926: 21 01 01    LXI  H,$0101
0929: 22 16 5e    SHLD $5E16
092C: 21 21 a4    LXI  H,$A421
092F: 22 22 5e    SHLD $5E22
0932: 3e 97       MVI  A,$97
0934: d3 10       OUT  $10
0936: 3e 92       MVI  A,$92
0938: d3 10       OUT  $10
093A: 3e 20       MVI  A,$20
093C: d3 11       OUT  $11
093E: 21 58 02    LXI  H,$0258
0941: cd 12 1f    CALL $1F12
0944: 21 10 00    LXI  H,$0010
0947: 22 10 5c    SHLD $5C10
094A: 22 1c 5c    SHLD $5C1C
094D: 22 1a 5c    SHLD $5C1A
0950: 21 13 04    LXI  H,$0413
0953: 22 12 5c    SHLD $5C12
0956: 21 94 02    LXI  H,$0294
0959: 22 14 5c    SHLD $5C14
095C: 21 2d 04    LXI  H,$042D
095F: 22 16 5c    SHLD $5C16
0962: 21 99 04    LXI  H,$0499
0965: 22 18 5c    SHLD $5C18
0968: 21 11 00    LXI  H,$0011
096B: 22 1e 5c    SHLD $5C1E
096E: 22 20 5c    SHLD $5C20
0971: 22 22 5c    SHLD $5C22
0974: 22 26 5c    SHLD $5C26
0977: 22 28 5c    SHLD $5C28
097A: 22 2a 5c    SHLD $5C2A
097D: 22 2c 5c    SHLD $5C2C
0980: 22 24 5c    SHLD $5C24
0983: 3e c3       MVI  A,$C3
0985: d3 18       OUT  $18
0987: 21 9d 09    LXI  H,$099D
098A: 22 fa 5d    SHLD $5DFA
098D: cd d9 10    CALL $10D9
0990: cd a8 09    CALL $09A8
0993: 3e 2a       MVI  A,$2A
0995: cd e6 0c    CALL $0CE6
0998: da 93 09    JC   $0993
099B: f1          POP  PSW
099C: c9          RET
099D: e8 e8 e8 ff f8 af 80 80 80 80 80                DB $E8,$E8,$E8,$FF,$F8,$AF,$80,$80,$80,$80,$80
09A8: cd 5d 0b    CALL $0B5D
09AB: cd b5 09    CALL $09B5
09AE: cd d3 0a    CALL $0AD3
09B1: cd 12 15    CALL $1512
09B4: c9          RET
; initialize_serial
09B5: f3          DI
09B6: f5          PUSH PSW
09B7: c5          PUSH B
09B8: d5          PUSH D
09B9: e5          PUSH H
09BA: 3a 0f 5f    LDA  $5F0F
09BD: 07          RLC
09BE: 47          MOV  B,A
09BF: 3a 0e 5f    LDA  $5F0E
09C2: 2f          CMA
09C3: e6 01       ANI  $01
09C5: b0          ORA  B
09C6: 07          RLC
09C7: 07          RLC
09C8: 07          RLC
09C9: e6 18       ANI  $18
09CB: 47          MOV  B,A
09CC: 3a 10 5e    LDA  $5E10
09CF: e6 e3       ANI  $E3
09D1: b0          ORA  B
09D2: 32 10 5e    STA  $5E10
09D5: d3 50       OUT  $50
09D7: 21 2e 5c    LXI  H,$5C2E
09DA: 11 9d 5d    LXI  D,$5D9D
09DD: cd 2b 1f    CALL $1F2B
09E0: cd 4d 0a    CALL $0A4D
09E3: 3e 18       MVI  A,$18
09E5: d3 03       OUT  $03
09E7: 3e 04       MVI  A,$04
09E9: d3 03       OUT  $03
09EB: 3a 01 5f    LDA  $5F01
09EE: 4f          MOV  C,A
09EF: 3a 02 5f    LDA  $5F02
09F2: cd 89 0a    CALL $0A89
09F5: d3 03       OUT  $03
09F7: 3e 05       MVI  A,$05
09F9: d3 03       OUT  $03
09FB: 3a 00 5f    LDA  $5F00
09FE: cd ac 0a    CALL $0AAC
0A01: d3 03       OUT  $03
0A03: 79          MOV  A,C
0A04: 32 1c 5e    STA  $5E1C
0A07: 3e 03       MVI  A,$03
0A09: d3 03       OUT  $03
0A0B: 78          MOV  A,B
0A0C: f6 01       ORI  $01
0A0E: d3 03       OUT  $03
0A10: 3e 01       MVI  A,$01
0A12: d3 03       OUT  $03
0A14: 3e 16       MVI  A,$16
0A16: d3 03       OUT  $03
0A18: 3a 07 5f    LDA  $5F07
0A1B: cd 24 0b    CALL $0B24
0A1E: 3e 36       MVI  A,$36
0A20: d3 23       OUT  $23
0A22: 7e          MOV  A,M
0A23: d3 20       OUT  $20
0A25: 23          INX  H
0A26: 7e          MOV  A,M
0A27: d3 20       OUT  $20
0A29: af          XRA  A
0A2A: d3 01       OUT  $01
0A2C: db 01       IN   $01
0A2E: e6 28       ANI  $28
0A30: 32 f7 5d    STA  $5DF7
0A33: 3a 03 5f    LDA  $5F03
0A36: cd 24 0b    CALL $0B24
0A39: 3e 76       MVI  A,$76
0A3B: d3 23       OUT  $23
0A3D: 7e          MOV  A,M
0A3E: d3 21       OUT  $21
0A40: 23          INX  H
0A41: 7e          MOV  A,M
0A42: d3 21       OUT  $21
0A44: cd bd 0a    CALL $0ABD
0A47: e1          POP  H
0A48: d1          POP  D
0A49: c1          POP  B
0A4A: f1          POP  PSW
0A4B: fb          EI
0A4C: c9          RET
; initialize_serial_channel
0A4D: 3e 18       MVI  A,$18
0A4F: d3 01       OUT  $01
0A51: 3e 04       MVI  A,$04
0A53: d3 01       OUT  $01
0A55: 3a 05 5f    LDA  $5F05
0A58: 4f          MOV  C,A
0A59: 3a 06 5f    LDA  $5F06
0A5C: cd 89 0a    CALL $0A89
0A5F: d3 01       OUT  $01
0A61: 3e 05       MVI  A,$05
0A63: d3 01       OUT  $01
0A65: 3a 04 5f    LDA  $5F04
0A68: cd ac 0a    CALL $0AAC
0A6B: d3 01       OUT  $01
0A6D: 32 1f 5e    STA  $5E1F
0A70: 79          MOV  A,C
0A71: 32 1b 5e    STA  $5E1B
0A74: 3e 03       MVI  A,$03
0A76: d3 01       OUT  $01
0A78: 78          MOV  A,B
0A79: f6 01       ORI  $01
0A7B: 32 1e 5e    STA  $5E1E
0A7E: d3 01       OUT  $01
0A80: 3e 01       MVI  A,$01
0A82: d3 01       OUT  $01
0A84: 3e 13       MVI  A,$13
0A86: d3 01       OUT  $01
0A88: c9          RET
0A89: 06 00       MVI  B,$00
0A8B: a7          ANA  A
0A8C: ca 98 0a    JZ   $0A98
0A8F: 06 03       MVI  B,$03
0A91: fe 01       CPI  $01
0A93: ca 98 0a    JZ   $0A98
0A96: 06 01       MVI  B,$01
0A98: 79          MOV  A,C
0A99: a7          ANA  A
0A9A: 3e 04       MVI  A,$04
0A9C: ca a1 0a    JZ   $0AA1
0A9F: 3e 0c       MVI  A,$0C
0AA1: b0          ORA  B
0AA2: 47          MOV  B,A
0AA3: 3a 0f 5f    LDA  $5F0F
0AA6: a7          ANA  A
0AA7: 78          MOV  A,B
0AA8: c0          RNZ
0AA9: f6 40       ORI  $40
0AAB: c9          RET
0AAC: 0e 7f       MVI  C,$7F
0AAE: 06 40       MVI  B,$40
0AB0: a7          ANA  A
0AB1: ca b8 0a    JZ   $0AB8
0AB4: 0e ff       MVI  C,$FF
0AB6: 06 c0       MVI  B,$C0
0AB8: 78          MOV  A,B
0AB9: 0f          RRC
0ABA: f6 08       ORI  $08
0ABC: c9          RET
0ABD: 97          SUB  A
0ABE: 32 1d 5e    STA  $5E1D
0AC1: 3a 13 5f    LDA  $5F13
0AC4: a7          ANA  A
0AC5: c8          RZ
0AC6: 3e 11       MVI  A,$11
0AC8: cd da 03    CALL $03DA
0ACB: d8          RC
0ACC: cd d9 0b    CALL $0BD9
0ACF: da cc 0a    JC   $0ACC
0AD2: c9          RET
0AD3: f3          DI
0AD4: f5          PUSH PSW
0AD5: d5          PUSH D
0AD6: e5          PUSH H
0AD7: cd df 0a    CALL $0ADF
0ADA: e1          POP  H
0ADB: d1          POP  D
0ADC: f1          POP  PSW
0ADD: fb          EI
0ADE: c9          RET
0ADF: c5          PUSH B
0AE0: 21 c0 5d    LXI  H,$5DC0
0AE3: 11 f5 5d    LXI  D,$5DF5
0AE6: cd 2b 1f    CALL $1F2B
0AE9: 3e 97       MVI  A,$97
0AEB: d3 18       OUT  $18
0AED: 21 00 00    LXI  H,$0000
0AF0: 22 29 5e    SHLD $5E29
0AF3: 3a 08 5f    LDA  $5F08
0AF6: 07          RLC
0AF7: 07          RLC
0AF8: 47          MOV  B,A
0AF9: 3a 0a 5f    LDA  $5F0A
0AFC: b0          ORA  B
0AFD: e6 07       ANI  $07
0AFF: 47          MOV  B,A
0B00: 21 47 0b    LXI  H,$0B47
0B03: 7e          MOV  A,M
0B04: 23          INX  H
0B05: 23          INX  H
0B06: b8          CMP  B
0B07: c2 03 0b    JNZ  $0B03
0B0A: 2b          DCX  H
0B0B: 7e          MOV  A,M
0B0C: d3 18       OUT  $18
0B0E: 32 11 5e    STA  $5E11
0B11: 3a 0b 5f    LDA  $5F0B
0B14: cd 24 0b    CALL $0B24
0B17: 3e b6       MVI  A,$B6
0B19: d3 23       OUT  $23
0B1B: 7e          MOV  A,M
0B1C: d3 22       OUT  $22
0B1E: 23          INX  H
0B1F: 7e          MOV  A,M
0B20: d3 22       OUT  $22
0B22: c1          POP  B
0B23: c9          RET
; select_baud_divisor
0B24: 21 2f 0b    LXI  H,$0B2F
0B27: 3c          INR  A
0B28: 3d          DCR  A
0B29: c8          RZ
0B2A: 23          INX  H
0B2B: 23          INX  H
0B2C: c3 28 0b    JMP  $0B28
0B2F: 00 09 00 06 17 04 58 03 40 02 80 01 c0 00 60 00 DB $00,$09,$00,$06,$17,$04,$58,$03,$40,$02,$80,$01,$C0,$00,$60,$00
0B3F: 30 00 18 00 0c 00 06 00 00 15 01 01 02 05 03 01 DB $30,$00,$18,$00,$0C,$00,$06,$00,$00,$15,$01,$01,$02,$05,$03,$01
0B4F: 04 15 05 19 06 1d 07 19                         DB $04,$15,$05,$19,$06,$1D,$07,$19
0B57: f3          DI
0B58: f5          PUSH PSW
0B59: c5          PUSH B
0B5A: c3 7a 0b    JMP  $0B7A
0B5D: f3          DI
0B5E: f5          PUSH PSW
0B5F: c5          PUSH B
0B60: 3a 14 5f    LDA  $5F14
0B63: a7          ANA  A
0B64: cc 3a 0d    CZ   $0D3A
0B67: c4 40 0d    CNZ  $0D40
0B6A: da 60 0b    JC   $0B60
0B6D: 3a 15 5f    LDA  $5F15
0B70: a7          ANA  A
0B71: cc 46 0d    CZ   $0D46
0B74: c4 4c 0d    CNZ  $0D4C
0B77: da 6d 0b    JC   $0B6D
0B7A: 06 00       MVI  B,$00
0B7C: 3a 0c 5f    LDA  $5F0C
0B7F: a7          ANA  A
0B80: ca 85 0b    JZ   $0B85
0B83: 06 04       MVI  B,$04
0B85: 3a 0e 5e    LDA  $5E0E
0B88: e6 fb       ANI  $FB
0B8A: b0          ORA  B
0B8B: 32 0e 5e    STA  $5E0E
0B8E: 3a 10 5e    LDA  $5E10
0B91: e6 bb       ANI  $BB
0B93: 47          MOV  B,A
0B94: 3a 1b 5f    LDA  $5F1B
0B97: e6 01       ANI  $01
0B99: 0f          RRC
0B9A: 0f          RRC
0B9B: b0          ORA  B
0B9C: d3 50       OUT  $50
0B9E: 32 10 5e    STA  $5E10
0BA1: c1          POP  B
0BA2: f1          POP  PSW
0BA3: fb          EI
0BA4: c9          RET
0BA5: cd aa 0b    CALL $0BAA
0BA8: fb          EI
0BA9: c9          RET
0BAA: f5          PUSH PSW
0BAB: fe 03       CPI  $03
0BAD: d2 e9 20    JNC  $20E9
0BB0: f3          DI
0BB1: fe 01       CPI  $01
0BB3: da cd 0b    JC   $0BCD
0BB6: ca c3 0b    JZ   $0BC3
0BB9: 22 0a 5c    SHLD $5C0A
0BBC: eb          XCHG
0BBD: 22 08 5c    SHLD $5C08
0BC0: c3 d4 0b    JMP  $0BD4
0BC3: 22 06 5c    SHLD $5C06
0BC6: eb          XCHG
0BC7: 22 04 5c    SHLD $5C04
0BCA: c3 d4 0b    JMP  $0BD4
0BCD: 22 02 5c    SHLD $5C02
0BD0: eb          XCHG
0BD1: 22 00 5c    SHLD $5C00
0BD4: eb          XCHG
0BD5: f1          POP  PSW
0BD6: 37          STC
0BD7: 3f          CMC
0BD8: c9          RET
0BD9: cd de 0b    CALL $0BDE
0BDC: fb          EI
0BDD: c9          RET
0BDE: f3          DI
0BDF: f5          PUSH PSW
0BE0: 3a 51 5d    LDA  $5D51
0BE3: fe 03       CPI  $03
0BE5: ca e2 20    JZ   $20E2
0BE8: fe 01       CPI  $01
0BEA: c2 5f 0c    JNZ  $0C5F
0BED: 3a fb 5e    LDA  $5EFB
0BF0: a7          ANA  A
0BF1: c2 e9 20    JNZ  $20E9
0BF4: 3c          INR  A
0BF5: 32 fb 5e    STA  $5EFB
0BF8: f1          POP  PSW
0BF9: 32 24 5e    STA  $5E24
0BFC: 37          STC
0BFD: 3f          CMC
0BFE: c9          RET
0BFF: f3          DI
0C00: c5          PUSH B
0C01: f5          PUSH PSW
0C02: 47          MOV  B,A
0C03: 3a f8 5d    LDA  $5DF8
0C06: fe 01       CPI  $01
0C08: ca 35 0c    JZ   $0C35
0C0B: fe 02       CPI  $02
0C0D: c2 3c 0c    JNZ  $0C3C
0C10: 3a 10 5f    LDA  $5F10
0C13: a7          ANA  A
0C14: ca 1f 0c    JZ   $0C1F
0C17: 3a 2e 5d    LDA  $5D2E
0C1A: fe ff       CPI  $FF
0C1C: ca cb 0c    JZ   $0CCB
0C1F: 3a 51 5d    LDA  $5D51
0C22: fe 03       CPI  $03
0C24: ca 3c 0c    JZ   $0C3C
0C27: 78          MOV  A,B
0C28: cd 57 0c    CALL $0C57
0C2B: da cb 0c    JC   $0CCB
0C2E: 3a 10 5f    LDA  $5F10
0C31: a7          ANA  A
0C32: ca 3c 0c    JZ   $0C3C
0C35: 78          MOV  A,B
0C36: cd 34 0f    CALL $0F34
0C39: da cb 0c    JC   $0CCB
0C3C: f1          POP  PSW
0C3D: c1          POP  B
0C3E: 37          STC
0C3F: 3f          CMC
0C40: fb          EI
0C41: c9          RET
; serial_tx
0C42: f3          DI
0C43: f5          PUSH PSW
0C44: 3a 51 5d    LDA  $5D51
0C47: fe 03       CPI  $03
0C49: ca 52 0c    JZ   $0C52
0C4C: f1          POP  PSW
0C4D: cd 57 0c    CALL $0C57
0C50: fb          EI
0C51: c9          RET
0C52: f1          POP  PSW
0C53: 37          STC
0C54: 3f          CMC
0C55: fb          EI
0C56: c9          RET
0C57: f5          PUSH PSW
0C58: 3a 51 5d    LDA  $5D51
0C5B: a7          ANA  A
0C5C: c2 6a 0c    JNZ  $0C6A
0C5F: 3e 01       MVI  A,$01
0C61: 32 51 5d    STA  $5D51
0C64: f1          POP  PSW
0C65: d3 00       OUT  $00
0C67: 37          STC
0C68: 3f          CMC
0C69: c9          RET
0C6A: f1          POP  PSW
0C6B: cd 06 0f    CALL $0F06
0C6E: c9          RET
; serial_rx
0C6F: f3          DI
0C70: c5          PUSH B
0C71: f5          PUSH PSW
0C72: 3a 13 5f    LDA  $5F13
0C75: a7          ANA  A
0C76: ca 9a 0c    JZ   $0C9A
0C79: 3a 1d 5e    LDA  $5E1D
0C7C: a7          ANA  A
0C7D: ca 9a 0c    JZ   $0C9A
0C80: 3a 2e 5d    LDA  $5D2E
0C83: fe 21       CPI  $21
0C85: d2 9a 0c    JNC  $0C9A
0C88: 3e 11       MVI  A,$11
0C8A: cd da 03    CALL $03DA
0C8D: da 96 0c    JC   $0C96
0C90: cd de 0b    CALL $0BDE
0C93: da 9a 0c    JC   $0C9A
0C96: 97          SUB  A
0C97: 32 1d 5e    STA  $5E1D
0C9A: cd 4b 0f    CALL $0F4B
0C9D: da cb 0c    JC   $0CCB
0CA0: 47          MOV  B,A
0CA1: f1          POP  PSW
0CA2: 78          MOV  A,B
0CA3: c1          POP  B
0CA4: 37          STC
0CA5: 3f          CMC
0CA6: fb          EI
0CA7: c9          RET
; second_serial_tx
0CA8: f3          DI
0CA9: f5          PUSH PSW
0CAA: 3a 99 5d    LDA  $5D99
0CAD: a7          ANA  A
0CAE: c2 bc 0c    JNZ  $0CBC
0CB1: 3c          INR  A
0CB2: 32 99 5d    STA  $5D99
0CB5: f1          POP  PSW
0CB6: d3 02       OUT  $02
0CB8: 37          STC
0CB9: 3f          CMC
0CBA: fb          EI
0CBB: c9          RET
0CBC: f1          POP  PSW
0CBD: cd 1d 0f    CALL $0F1D
0CC0: fb          EI
0CC1: c9          RET
; second_serial_rx
0CC2: f3          DI
0CC3: c5          PUSH B
0CC4: f5          PUSH PSW
0CC5: cd 6d 0f    CALL $0F6D
0CC8: d2 a0 0c    JNC  $0CA0
0CCB: f1          POP  PSW
0CCC: c1          POP  B
0CCD: 37          STC
0CCE: fb          EI
0CCF: c9          RET
; keyboard_rx
0CD0: f3          DI
0CD1: c5          PUSH B
0CD2: f5          PUSH PSW
0CD3: cd fb 0e    CALL $0EFB
0CD6: da e1 0c    JC   $0CE1
0CD9: 47          MOV  B,A
0CDA: f1          POP  PSW
0CDB: 78          MOV  A,B
0CDC: c1          POP  B
0CDD: 37          STC
0CDE: 3f          CMC
0CDF: fb          EI
0CE0: c9          RET
0CE1: f1          POP  PSW
0CE2: c1          POP  B
0CE3: 37          STC
0CE4: fb          EI
0CE5: c9          RET
; keyboard_command_tx
0CE6: f5          PUSH PSW
0CE7: f3          DI
0CE8: f5          PUSH PSW
0CE9: db 10       IN   $10
0CEB: e6 02       ANI  $02
0CED: ca f8 0c    JZ   $0CF8
0CF0: f1          POP  PSW
0CF1: d3 11       OUT  $11
0CF3: f1          POP  PSW
0CF4: 37          STC
0CF5: 3f          CMC
0CF6: fb          EI
0CF7: c9          RET
0CF8: f1          POP  PSW
0CF9: f1          POP  PSW
0CFA: 37          STC
0CFB: fb          EI
0CFC: c9          RET
0CFD: f5          PUSH PSW
0CFE: a7          ANA  A
0CFF: ca f3 0c    JZ   $0CF3
0D02: fe 09       CPI  $09
0D04: d2 f3 0c    JNC  $0CF3
0D07: c3 e7 0c    JMP  $0CE7
0D0A: f5          PUSH PSW
0D0B: a7          ANA  A
0D0C: ca 19 0d    JZ   $0D19
0D0F: fe 09       CPI  $09
0D11: d2 f3 0c    JNC  $0CF3
0D14: c6 08       ADI  $08
0D16: c3 e7 0c    JMP  $0CE7
0D19: 3e 25       MVI  A,$25
0D1B: c3 e7 0c    JMP  $0CE7
0D1E: f5          PUSH PSW
0D1F: a7          ANA  A
0D20: ca f3 0c    JZ   $0CF3
0D23: fe 09       CPI  $09
0D25: d2 f3 0c    JNC  $0CF3
0D28: c6 10       ADI  $10
0D2A: c3 e7 0c    JMP  $0CE7
; keyboard_bell
0D2D: f5          PUSH PSW
0D2E: 3a 16 5f    LDA  $5F16
0D31: a7          ANA  A
0D32: c2 e2 20    JNZ  $20E2
0D35: 3e 24       MVI  A,$24
0D37: c3 e7 0c    JMP  $0CE7
0D3A: f5          PUSH PSW
0D3B: 3e 21       MVI  A,$21
0D3D: c3 e7 0c    JMP  $0CE7
0D40: f5          PUSH PSW
0D41: 3e 22       MVI  A,$22
0D43: c3 e7 0c    JMP  $0CE7
0D46: f5          PUSH PSW
0D47: 3e 28       MVI  A,$28
0D49: c3 e7 0c    JMP  $0CE7
0D4C: f5          PUSH PSW
0D4D: 3e 29       MVI  A,$29
0D4F: c3 e7 0c    JMP  $0CE7
0D52: f3          DI
0D53: f5          PUSH PSW
0D54: 3a e0 5d    LDA  $5DE0
0D57: a7          ANA  A
0D58: c2 73 0d    JNZ  $0D73
0D5B: 3a 17 5f    LDA  $5F17
0D5E: a7          ANA  A
0D5F: 3a 11 5e    LDA  $5E11
0D62: ca 6a 0d    JZ   $0D6A
0D65: f6 a0       ORI  $A0
0D67: c3 6c 0d    JMP  $0D6C
0D6A: f6 20       ORI  $20
0D6C: d3 18       OUT  $18
0D6E: 3e 01       MVI  A,$01
0D70: 32 e0 5d    STA  $5DE0
0D73: f1          POP  PSW
0D74: cd a5 0f    CALL $0FA5
0D77: fb          EI
0D78: c9          RET
0D79: f3          DI
0D7A: c5          PUSH B
0D7B: f5          PUSH PSW
0D7C: cd 8f 0f    CALL $0F8F
0D7F: da 8a 0d    JC   $0D8A
0D82: 47          MOV  B,A
0D83: f1          POP  PSW
0D84: 78          MOV  A,B
0D85: c1          POP  B
0D86: 37          STC
0D87: 3f          CMC
0D88: fb          EI
0D89: c9          RET
0D8A: f1          POP  PSW
0D8B: c1          POP  B
0D8C: 37          STC
0D8D: fb          EI
0D8E: c9          RET
0D8F: f5          PUSH PSW
0D90: e5          PUSH H
0D91: db 60       IN   $60
0D93: e6 01       ANI  $01
0D95: 21 1c 5f    LXI  H,$5F1C
0D98: be          CMP  M
0D99: ca e1 20    JZ   $20E1
0D9C: c3 e8 20    JMP  $20E8
0D9F: f3          DI
0DA0: f5          PUSH PSW
0DA1: 3e 03       MVI  A,$03
0DA3: 32 28 5e    STA  $5E28
0DA6: d3 01       OUT  $01
0DA8: 3a 1e 5e    LDA  $5E1E
0DAB: e6 fe       ANI  $FE
0DAD: d3 01       OUT  $01
0DAF: f1          POP  PSW
0DB0: fb          EI
0DB1: c9          RET
0DB2: f3          DI
0DB3: f5          PUSH PSW
0DB4: 3a 28 5e    LDA  $5E28
0DB7: a7          ANA  A
0DB8: ca d8 0d    JZ   $0DD8
0DBB: 3e 30       MVI  A,$30
0DBD: d3 01       OUT  $01
0DBF: 97          SUB  A
0DC0: 32 28 5e    STA  $5E28
0DC3: 32 2e 5d    STA  $5D2E
0DC6: 32 2f 5d    STA  $5D2F
0DC9: 32 30 5d    STA  $5D30
0DCC: 3e 03       MVI  A,$03
0DCE: d3 01       OUT  $01
0DD0: 3a 1e 5e    LDA  $5E1E
0DD3: d3 01       OUT  $01
0DD5: cd bd 0a    CALL $0ABD
0DD8: f1          POP  PSW
0DD9: fb          EI
0DDA: c9          RET
0DDB: cd e0 0d    CALL $0DE0
0DDE: fb          EI
0DDF: c9          RET
0DE0: f3          DI
0DE1: f5          PUSH PSW
0DE2: 3a 51 5d    LDA  $5D51
0DE5: a7          ANA  A
0DE6: ca f6 0d    JZ   $0DF6
0DE9: fe 01       CPI  $01
0DEB: c2 fb 0d    JNZ  $0DFB
0DEE: 3e 01       MVI  A,$01
0DF0: 32 52 5d    STA  $5D52
0DF3: c3 fb 0d    JMP  $0DFB
0DF6: 3e 02       MVI  A,$02
0DF8: 32 51 5d    STA  $5D51
0DFB: f1          POP  PSW
0DFC: c9          RET
0DFD: cd 02 0e    CALL $0E02
0E00: fb          EI
0E01: c9          RET
0E02: f3          DI
0E03: f5          PUSH PSW
0E04: 3a 51 5d    LDA  $5D51
0E07: fe 03       CPI  $03
0E09: ca 3d 0e    JZ   $0E3D
0E0C: fe 01       CPI  $01
0E0E: da 3d 0e    JC   $0E3D
0E11: c2 1b 0e    JNZ  $0E1B
0E14: 97          SUB  A
0E15: 32 52 5d    STA  $5D52
0E18: c3 3d 0e    JMP  $0E3D
0E1B: 97          SUB  A
0E1C: 32 52 5d    STA  $5D52
0E1F: 3a fb 5e    LDA  $5EFB
0E22: a7          ANA  A
0E23: c2 30 0e    JNZ  $0E30
0E26: cd 12 0f    CALL $0F12
0E29: d2 33 0e    JNC  $0E33
0E2C: 97          SUB  A
0E2D: c3 3a 0e    JMP  $0E3A
0E30: 3a 24 5e    LDA  $5E24
0E33: d3 00       OUT  $00
0E35: 97          SUB  A
0E36: 32 fb 5e    STA  $5EFB
0E39: 3c          INR  A
0E3A: 32 51 5d    STA  $5D51
0E3D: f1          POP  PSW
0E3E: c9          RET
0E3F: f3          DI
0E40: f5          PUSH PSW
0E41: 3e 05       MVI  A,$05
0E43: d3 01       OUT  $01
0E45: 3a 1f 5e    LDA  $5E1F
0E48: f6 10       ORI  $10
0E4A: d3 01       OUT  $01
0E4C: 32 1f 5e    STA  $5E1F
0E4F: 3e 03       MVI  A,$03
0E51: 32 51 5d    STA  $5D51
0E54: f1          POP  PSW
0E55: fb          EI
0E56: c9          RET
0E57: f3          DI
0E58: f5          PUSH PSW
0E59: 3a 51 5d    LDA  $5D51
0E5C: fe 03       CPI  $03
0E5E: c2 82 0e    JNZ  $0E82
0E61: 3e 05       MVI  A,$05
0E63: d3 01       OUT  $01
0E65: 3a 1f 5e    LDA  $5E1F
0E68: e6 ef       ANI  $EF
0E6A: d3 01       OUT  $01
0E6C: 32 1f 5e    STA  $5E1F
0E6F: 97          SUB  A
0E70: 32 53 5d    STA  $5D53
0E73: 32 54 5d    STA  $5D54
0E76: 32 55 5d    STA  $5D55
0E79: 32 fb 5e    STA  $5EFB
0E7C: 32 51 5d    STA  $5D51
0E7F: cd bd 0a    CALL $0ABD
0E82: f1          POP  PSW
0E83: fb          EI
0E84: c9          RET
0E85: cd 8a 0e    CALL $0E8A
0E88: fb          EI
0E89: c9          RET
0E8A: f3          DI
0E8B: f5          PUSH PSW
0E8C: c5          PUSH B
0E8D: 47          MOV  B,A
0E8E: e6 82       ANI  $82
0E90: 4f          MOV  C,A
0E91: 3e 05       MVI  A,$05
0E93: d3 01       OUT  $01
0E95: 3a 1f 5e    LDA  $5E1F
0E98: e6 7d       ANI  $7D
0E9A: b1          ORA  C
0E9B: 32 1f 5e    STA  $5E1F
0E9E: d3 01       OUT  $01
0EA0: 78          MOV  A,B
0EA1: 2f          CMA
0EA2: e6 20       ANI  $20
0EA4: 4f          MOV  C,A
0EA5: 3a 10 5e    LDA  $5E10
0EA8: e6 db       ANI  $DB
0EAA: b1          ORA  C
0EAB: 32 10 5e    STA  $5E10
0EAE: d3 50       OUT  $50
0EB0: c1          POP  B
0EB1: f1          POP  PSW
0EB2: c9          RET
; enqueue_32_common
0EB3: 7e          MOV  A,M
0EB4: fe 20       CPI  $20
0EB6: ca cf 0e    JZ   $0ECF
0EB9: 34          INR  M
0EBA: 23          INX  H
0EBB: 7e          MOV  A,M
0EBC: fe 1f       CPI  $1F
0EBE: c2 c3 0e    JNZ  $0EC3
0EC1: 36 ff       MVI  M,$FF
0EC3: 34          INR  M
0EC4: 6f          MOV  L,A
0EC5: 26 00       MVI  H,$00
0EC7: 19          DAD  D
0EC8: f1          POP  PSW
0EC9: 77          MOV  M,A
0ECA: e1          POP  H
0ECB: d1          POP  D
0ECC: 37          STC
0ECD: 3f          CMC
0ECE: c9          RET
0ECF: f1          POP  PSW
0ED0: e1          POP  H
0ED1: d1          POP  D
0ED2: 37          STC
0ED3: c9          RET
; dequeue_32_common
0ED4: 7e          MOV  A,M
0ED5: a7          ANA  A
0ED6: ca d0 0e    JZ   $0ED0
0ED9: 35          DCR  M
0EDA: 23          INX  H
0EDB: 23          INX  H
0EDC: 7e          MOV  A,M
0EDD: fe 1f       CPI  $1F
0EDF: c2 e4 0e    JNZ  $0EE4
0EE2: 36 ff       MVI  M,$FF
0EE4: 34          INR  M
0EE5: 6f          MOV  L,A
0EE6: 26 00       MVI  H,$00
0EE8: 19          DAD  D
0EE9: 7e          MOV  A,M
0EEA: e1          POP  H
0EEB: d1          POP  D
0EEC: 37          STC
0EED: 3f          CMC
0EEE: c9          RET
; keyboard_enqueue
0EEF: d5          PUSH D
0EF0: e5          PUSH H
0EF1: f5          PUSH PSW
0EF2: 11 9d 5d    LXI  D,$5D9D
0EF5: 21 bd 5d    LXI  H,$5DBD
0EF8: c3 b3 0e    JMP  $0EB3
; keyboard_dequeue
0EFB: d5          PUSH D
0EFC: e5          PUSH H
0EFD: 21 bd 5d    LXI  H,$5DBD
0F00: 11 9d 5d    LXI  D,$5D9D
0F03: c3 d4 0e    JMP  $0ED4
0F06: d5          PUSH D
0F07: e5          PUSH H
0F08: f5          PUSH PSW
0F09: 11 31 5d    LXI  D,$5D31
0F0C: 21 53 5d    LXI  H,$5D53
0F0F: c3 b3 0e    JMP  $0EB3
0F12: d5          PUSH D
0F13: e5          PUSH H
0F14: 11 31 5d    LXI  D,$5D31
0F17: 21 53 5d    LXI  H,$5D53
0F1A: c3 d4 0e    JMP  $0ED4
0F1D: d5          PUSH D
0F1E: e5          PUSH H
0F1F: f5          PUSH PSW
0F20: 11 79 5d    LXI  D,$5D79
0F23: 21 9a 5d    LXI  H,$5D9A
0F26: c3 b3 0e    JMP  $0EB3
0F29: d5          PUSH D
0F2A: e5          PUSH H
0F2B: 11 79 5d    LXI  D,$5D79
0F2E: 21 9a 5d    LXI  H,$5D9A
0F31: c3 d4 0e    JMP  $0ED4
; serial_rx_enqueue_255
0F34: d5          PUSH D
0F35: e5          PUSH H
0F36: f5          PUSH PSW
0F37: 21 2e 5d    LXI  H,$5D2E
0F3A: 11 2e 5c    LXI  D,$5C2E
0F3D: 7e          MOV  A,M
0F3E: fe ff       CPI  $FF
0F40: ca cf 0e    JZ   $0ECF
0F43: 34          INR  M
0F44: 23          INX  H
0F45: 7e          MOV  A,M
0F46: fe ff       CPI  $FF
0F48: c3 be 0e    JMP  $0EBE
; serial_rx_dequeue_255
0F4B: d5          PUSH D
0F4C: e5          PUSH H
0F4D: 21 2e 5d    LXI  H,$5D2E
0F50: 11 2e 5c    LXI  D,$5C2E
0F53: 7e          MOV  A,M
0F54: a7          ANA  A
0F55: ca d0 0e    JZ   $0ED0
0F58: 35          DCR  M
0F59: 23          INX  H
0F5A: 23          INX  H
0F5B: 7e          MOV  A,M
0F5C: fe ff       CPI  $FF
0F5E: c3 df 0e    JMP  $0EDF
0F61: d5          PUSH D
0F62: e5          PUSH H
0F63: f5          PUSH PSW
0F64: 11 56 5d    LXI  D,$5D56
0F67: 21 76 5d    LXI  H,$5D76
0F6A: c3 b3 0e    JMP  $0EB3
0F6D: d5          PUSH D
0F6E: e5          PUSH H
0F6F: 21 76 5d    LXI  H,$5D76
0F72: 11 56 5d    LXI  D,$5D56
0F75: c3 d4 0e    JMP  $0ED4
0F78: d5          PUSH D
0F79: e5          PUSH H
0F7A: f5          PUSH PSW
0F7B: 11 e4 5d    LXI  D,$5DE4
0F7E: 21 ec 5d    LXI  H,$5DEC
0F81: 7e          MOV  A,M
0F82: fe 08       CPI  $08
0F84: ca cf 0e    JZ   $0ECF
0F87: 34          INR  M
0F88: 23          INX  H
0F89: 7e          MOV  A,M
0F8A: fe 07       CPI  $07
0F8C: c3 be 0e    JMP  $0EBE
0F8F: d5          PUSH D
0F90: e5          PUSH H
0F91: 11 e4 5d    LXI  D,$5DE4
0F94: 21 ec 5d    LXI  H,$5DEC
0F97: 7e          MOV  A,M
0F98: a7          ANA  A
0F99: ca d0 0e    JZ   $0ED0
0F9C: 35          DCR  M
0F9D: 23          INX  H
0F9E: 23          INX  H
0F9F: 7e          MOV  A,M
0FA0: fe 07       CPI  $07
0FA2: c3 df 0e    JMP  $0EDF
; printer_enqueue
0FA5: d5          PUSH D
0FA6: e5          PUSH H
0FA7: f5          PUSH PSW
0FA8: 3a fe 5d    LDA  $5DFE
0FAB: a7          ANA  A
0FAC: c2 b8 0f    JNZ  $0FB8
0FAF: 11 c0 5d    LXI  D,$5DC0
0FB2: 21 e1 5d    LXI  H,$5DE1
0FB5: c3 b3 0e    JMP  $0EB3
0FB8: 2a ef 5d    LHLD $5DEF
0FBB: 11 d0 07    LXI  D,$07D0
0FBE: cd ca 1f    CALL $1FCA
0FC1: ca cf 0e    JZ   $0ECF
0FC4: 23          INX  H
0FC5: 22 ef 5d    SHLD $5DEF
0FC8: 2a f1 5d    LHLD $5DF1
0FCB: 11 cf 07    LXI  D,$07CF
0FCE: cd ca 1f    CALL $1FCA
0FD1: c2 d7 0f    JNZ  $0FD7
0FD4: 21 ff ff    LXI  H,$FFFF
0FD7: 23          INX  H
0FD8: 22 f1 5d    SHLD $5DF1
0FDB: eb          XCHG
0FDC: 2a ff 5d    LHLD $5DFF
0FDF: 19          DAD  D
0FE0: c3 c8 0e    JMP  $0EC8
; printer_dequeue
0FE3: d5          PUSH D
0FE4: e5          PUSH H
0FE5: 3a fe 5d    LDA  $5DFE
0FE8: a7          ANA  A
0FE9: c2 f5 0f    JNZ  $0FF5
0FEC: 11 c0 5d    LXI  D,$5DC0
0FEF: 21 e1 5d    LXI  H,$5DE1
0FF2: c3 d4 0e    JMP  $0ED4
0FF5: 2a ef 5d    LHLD $5DEF
0FF8: 7d          MOV  A,L
0FF9: b4          ORA  H
0FFA: ca d0 0e    JZ   $0ED0
0FFD: 2b          DCX  H
0FFE: 22 ef 5d    SHLD $5DEF
1001: 2a f3 5d    LHLD $5DF3
1004: 11 cf 07    LXI  D,$07CF
1007: cd ca 1f    CALL $1FCA
100A: c2 10 10    JNZ  $1010
100D: 21 ff ff    LXI  H,$FFFF
1010: 23          INX  H
1011: 22 f3 5d    SHLD $5DF3
1014: eb          XCHG
1015: 2a ff 5d    LHLD $5DFF
1018: 19          DAD  D
1019: c3 e9 0e    JMP  $0EE9
; nvram_read_byte
101C: d5          PUSH D
101D: e5          PUSH H
101E: f5          PUSH PSW
101F: cd 8c 10    CALL $108C
1022: da 4b 10    JC   $104B
1025: f3          DI
1026: 3a 10 5e    LDA  $5E10
1029: f6 04       ORI  $04
102B: d3 50       OUT  $50
102D: 7e          MOV  A,M
102E: e6 0f       ANI  $0F
1030: 57          MOV  D,A
1031: 24          INR  H
1032: 24          INR  H
1033: 7e          MOV  A,M
1034: 17          RAL
1035: 17          RAL
1036: 17          RAL
1037: 17          RAL
1038: e6 f0       ANI  $F0
103A: b2          ORA  D
103B: 57          MOV  D,A
103C: 3a 10 5e    LDA  $5E10
103F: e6 fb       ANI  $FB
1041: d3 50       OUT  $50
1043: fb          EI
1044: f1          POP  PSW
1045: 7a          MOV  A,D
1046: e1          POP  H
1047: d1          POP  D
1048: 37          STC
1049: 3f          CMC
104A: c9          RET
104B: f1          POP  PSW
104C: e1          POP  H
104D: d1          POP  D
104E: 37          STC
104F: c9          RET
; nvram_write_byte
1050: f5          PUSH PSW
1051: e5          PUSH H
1052: d5          PUSH D
1053: c5          PUSH B
1054: 57          MOV  D,A
1055: cd 8c 10    CALL $108C
1058: da e6 20    JC   $20E6
105B: 3e 01       MVI  A,$01
105D: 32 20 5e    STA  $5E20
1060: 7a          MOV  A,D
1061: 1f          RAR
1062: 1f          RAR
1063: 1f          RAR
1064: 1f          RAR
1065: e6 0f       ANI  $0F
1067: 5f          MOV  E,A
1068: 7a          MOV  A,D
1069: e6 0f       ANI  $0F
106B: cd 98 10    CALL $1098
106E: da 77 10    JC   $1077
1071: 24          INR  H
1072: 24          INR  H
1073: 7b          MOV  A,E
1074: cd 98 10    CALL $1098
1077: f5          PUSH PSW
1078: 3a 20 5e    LDA  $5E20
107B: fe 01       CPI  $01
107D: 3e 00       MVI  A,$00
107F: 32 20 5e    STA  $5E20
1082: c4 e5 03    CNZ  $03E5
1085: f1          POP  PSW
1086: da e6 20    JC   $20E6
1089: c3 df 20    JMP  $20DF
; nvram_address_check
108C: 7c          MOV  A,H
108D: fe 02       CPI  $02
108F: d2 ea 20    JNC  $20EA
1092: 3e 60       MVI  A,$60
1094: 84          ADD  H
1095: 67          MOV  H,A
1096: a7          ANA  A
1097: c9          RET
; nvram_write_nibble
1098: d5          PUSH D
1099: 57          MOV  D,A
109A: f3          DI
109B: 3a 10 5e    LDA  $5E10
109E: f6 04       ORI  $04
10A0: d3 50       OUT  $50
10A2: e5          PUSH H
10A3: 7e          MOV  A,M
10A4: e6 0f       ANI  $0F
10A6: ba          CMP  D
10A7: ca cc 10    JZ   $10CC
10AA: 24          INR  H
10AB: 24          INR  H
10AC: 24          INR  H
10AD: 24          INR  H
10AE: 77          MOV  M,A
10AF: 01 bf 07    LXI  B,$07BF
10B2: cd 12 1f    CALL $1F12
10B5: e1          POP  H
10B6: e5          PUSH H
10B7: 7e          MOV  A,M
10B8: e5          PUSH H
10B9: e1          POP  H
10BA: 72          MOV  M,D
10BB: 01 c6 00    LXI  B,$00C6
10BE: cd 12 1f    CALL $1F12
10C1: 7e          MOV  A,M
10C2: e5          PUSH H
10C3: e1          POP  H
10C4: 7e          MOV  A,M
10C5: e6 0f       ANI  $0F
10C7: ba          CMP  D
10C8: ca cc 10    JZ   $10CC
10CB: 37          STC
10CC: f5          PUSH PSW
10CD: 3a 10 5e    LDA  $5E10
10D0: e6 fb       ANI  $FB
10D2: d3 50       OUT  $50
10D4: fb          EI
10D5: f1          POP  PSW
10D6: e1          POP  H
10D7: d1          POP  D
10D8: c9          RET
10D9: f5          PUSH PSW
10DA: e5          PUSH H
10DB: d5          PUSH D
10DC: c5          PUSH B
10DD: 11 00 5f    LXI  D,$5F00
10E0: cd e6 10    CALL $10E6
10E3: c3 da 20    JMP  $20DA
; unpack_configuration
10E6: 2a fa 5d    LHLD $5DFA
10E9: 3e ff       MVI  A,$FF
10EB: f5          PUSH PSW
10EC: e5          PUSH H
10ED: e1          POP  H
10EE: 4e          MOV  C,M
10EF: 23          INX  H
10F0: f1          POP  PSW
10F1: 3c          INR  A
10F2: fe 0b       CPI  $0B
10F4: d0          RNC
10F5: f5          PUSH PSW
10F6: e5          PUSH H
10F7: 6f          MOV  L,A
10F8: 26 00       MVI  H,$00
10FA: cd 1c 10    CALL $101C
10FD: 47          MOV  B,A
10FE: 26 08       MVI  H,$08
1100: 79          MOV  A,C
1101: 07          RLC
1102: 2e 01       MVI  L,$01
1104: 07          RLC
1105: da 13 11    JC   $1113
1108: f5          PUSH PSW
1109: 7d          MOV  A,L
110A: 85          ADD  L
110B: c6 01       ADI  $01
110D: 6f          MOV  L,A
110E: f1          POP  PSW
110F: 25          DCR  H
1110: c2 04 11    JNZ  $1104
1113: f5          PUSH PSW
1114: 78          MOV  A,B
1115: e5          PUSH H
1116: 25          DCR  H
1117: ca 1e 11    JZ   $111E
111A: 0f          RRC
111B: c3 16 11    JMP  $1116
111E: e1          POP  H
111F: a5          ANA  L
1120: 12          STAX D
1121: 13          INX  D
1122: f1          POP  PSW
1123: 25          DCR  H
1124: c2 02 11    JNZ  $1102
1127: c3 ed 10    JMP  $10ED
; pack_configuration
112A: f5          PUSH PSW
112B: e5          PUSH H
112C: d5          PUSH D
112D: c5          PUSH B
112E: 11 00 5f    LXI  D,$5F00
1131: 2a fa 5d    LHLD $5DFA
1134: 0e 00       MVI  C,$00
1136: c5          PUSH B
1137: 0e 00       MVI  C,$00
1139: 06 09       MVI  B,$09
113B: 7e          MOV  A,M
113C: 07          RLC
113D: 05          DCR  B
113E: ca 5e 11    JZ   $115E
1141: 07          RLC
1142: d2 3d 11    JNC  $113D
1145: f5          PUSH PSW
1146: c5          PUSH B
1147: 1a          LDAX D
1148: 13          INX  D
1149: 05          DCR  B
114A: ca 51 11    JZ   $1151
114D: 07          RLC
114E: c3 49 11    JMP  $1149
1151: b1          ORA  C
1152: c1          POP  B
1153: 4f          MOV  C,A
1154: 78          MOV  A,B
1155: a7          ANA  A
1156: ca 5d 11    JZ   $115D
1159: f1          POP  PSW
115A: c3 3d 11    JMP  $113D
115D: f1          POP  PSW
115E: 79          MOV  A,C
115F: c1          POP  B
1160: e5          PUSH H
1161: 69          MOV  L,C
1162: 26 00       MVI  H,$00
1164: cd 50 10    CALL $1050
1167: e1          POP  H
1168: da e6 20    JC   $20E6
116B: 23          INX  H
116C: 0c          INR  C
116D: 79          MOV  A,C
116E: fe 0b       CPI  $0B
1170: da 36 11    JC   $1136
1173: c3 df 20    JMP  $20DF
1176: e5          PUSH H
1177: 21 01 01    LXI  H,$0101
117A: 22 16 5e    SHLD $5E16
117D: e1          POP  H
117E: c9          RET
117F: f5          PUSH PSW
1180: 3e 01       MVI  A,$01
1182: 32 16 5e    STA  $5E16
1185: f1          POP  PSW
1186: c9          RET
1187: cd a7 11    CALL $11A7
118A: d8          RC
118B: c3 92 11    JMP  $1192
118E: cd b7 11    CALL $11B7
1191: d8          RC
1192: f5          PUSH PSW
1193: cd 9c 11    CALL $119C
1196: d2 e9 20    JNC  $20E9
1199: c3 e2 20    JMP  $20E2
119C: d5          PUSH D
119D: eb          XCHG
119E: 2a 16 5e    LHLD $5E16
11A1: eb          XCHG
11A2: cd ca 1f    CALL $1FCA
11A5: d1          POP  D
11A6: c9          RET
11A7: f5          PUSH PSW
11A8: 3a 16 5e    LDA  $5E16
11AB: fe 50       CPI  $50
11AD: ca e9 20    JZ   $20E9
11B0: 3c          INR  A
11B1: 32 16 5e    STA  $5E16
11B4: c3 e2 20    JMP  $20E2
11B7: cd a7 11    CALL $11A7
11BA: d0          RNC
11BB: cd 23 12    CALL $1223
11BE: d8          RC
11BF: c3 7f 11    JMP  $117F
11C2: cd d7 11    CALL $11D7
11C5: d8          RC
11C6: c3 cd 11    JMP  $11CD
11C9: cd e5 11    CALL $11E5
11CC: d8          RC
11CD: f5          PUSH PSW
11CE: cd 9c 11    CALL $119C
11D1: da e9 20    JC   $20E9
11D4: c3 e2 20    JMP  $20E2
11D7: f5          PUSH PSW
11D8: 3a 16 5e    LDA  $5E16
11DB: 3d          DCR  A
11DC: ca e9 20    JZ   $20E9
11DF: 32 16 5e    STA  $5E16
11E2: c3 e2 20    JMP  $20E2
11E5: cd d7 11    CALL $11D7
11E8: d0          RNC
11E9: cd f5 11    CALL $11F5
11EC: d8          RC
11ED: f5          PUSH PSW
11EE: 3e 50       MVI  A,$50
11F0: 32 16 5e    STA  $5E16
11F3: f1          POP  PSW
11F4: c9          RET
11F5: f5          PUSH PSW
11F6: 3a 17 5e    LDA  $5E17
11F9: 3d          DCR  A
11FA: ca e9 20    JZ   $20E9
11FD: 32 17 5e    STA  $5E17
1200: c3 e2 20    JMP  $20E2
1203: f5          PUSH PSW
1204: 3a 17 5e    LDA  $5E17
1207: bc          CMP  H
1208: da e9 20    JC   $20E9
120B: ca e9 20    JZ   $20E9
120E: c3 f6 11    JMP  $11F6
1211: f5          PUSH PSW
1212: d5          PUSH D
1213: eb          XCHG
1214: 2a 16 5e    LHLD $5E16
1217: 25          DCR  H
1218: eb          XCHG
1219: cd ca 1f    CALL $1FCA
121C: d1          POP  D
121D: da e9 20    JC   $20E9
1220: c3 f6 11    JMP  $11F6
1223: f5          PUSH PSW
1224: 3a 17 5e    LDA  $5E17
1227: fe 19       CPI  $19
1229: ca e9 20    JZ   $20E9
122C: 3c          INR  A
122D: c3 fd 11    JMP  $11FD
1230: f5          PUSH PSW
1231: 3a 17 5e    LDA  $5E17
1234: bc          CMP  H
1235: d2 e9 20    JNC  $20E9
1238: c3 24 12    JMP  $1224
123B: f5          PUSH PSW
123C: d5          PUSH D
123D: eb          XCHG
123E: 2a 16 5e    LHLD $5E16
1241: 24          INR  H
1242: eb          XCHG
1243: cd ca 1f    CALL $1FCA
1246: d1          POP  D
1247: d2 e9 20    JNC  $20E9
124A: c3 24 12    JMP  $1224
; checked_cursor_set
124D: cd 82 1e    CALL $1E82
1250: d8          RC
; cursor_set
1251: 22 16 5e    SHLD $5E16
1254: c9          RET
; cursor_get
1255: 2a 16 5e    LHLD $5E16
1258: c9          RET
1259: f5          PUSH PSW
125A: 3e 28       MVI  A,$28
125C: cd 3f 13    CALL $133F
125F: 3d          DCR  A
1260: fe 1a       CPI  $1A
1262: ca 6a 12    JZ   $126A
1265: d3 35       OUT  $35
1267: c3 5c 12    JMP  $125C
126A: 3e 28       MVI  A,$28
126C: d3 35       OUT  $35
126E: cd 22 13    CALL $1322
1271: d3 36       OUT  $36
1273: f1          POP  PSW
1274: c9          RET
1275: f5          PUSH PSW
1276: 3e 28       MVI  A,$28
1278: cd 3f 13    CALL $133F
127B: 3c          INR  A
127C: d3 35       OUT  $35
127E: fe 36       CPI  $36
1280: c2 78 12    JNZ  $1278
1283: cd 3f 13    CALL $133F
1286: 3e 28       MVI  A,$28
1288: d3 35       OUT  $35
128A: cd 30 13    CALL $1330
128D: d3 36       OUT  $36
128F: f1          POP  PSW
1290: c9          RET
1291: f5          PUSH PSW
1292: cd 22 13    CALL $1322
1295: f1          POP  PSW
1296: c9          RET
1297: f5          PUSH PSW
1298: cd 30 13    CALL $1330
129B: f1          POP  PSW
129C: c9          RET
129D: f5          PUSH PSW
129E: e5          PUSH H
129F: d5          PUSH D
12A0: c5          PUSH B
12A1: cd 3f 13    CALL $133F
12A4: cd 22 13    CALL $1322
12A7: d3 36       OUT  $36
12A9: 26 18       MVI  H,$18
12AB: 16 19       MVI  D,$19
12AD: 3e 02       MVI  A,$02
12AF: cd e5 15    CALL $15E5
12B2: c3 da 20    JMP  $20DA
12B5: f5          PUSH PSW
12B6: c5          PUSH B
12B7: e5          PUSH H
12B8: 26 01       MVI  H,$01
12BA: cd a2 15    CALL $15A2
12BD: cd 22 13    CALL $1322
12C0: c3 d6 20    JMP  $20D6
12C3: f5          PUSH PSW
12C4: e5          PUSH H
12C5: d5          PUSH D
12C6: c5          PUSH B
12C7: 26 19       MVI  H,$19
12C9: 16 18       MVI  D,$18
12CB: 3e 02       MVI  A,$02
12CD: cd e5 15    CALL $15E5
12D0: cd 3f 13    CALL $133F
12D3: cd 30 13    CALL $1330
12D6: d3 36       OUT  $36
12D8: c3 da 20    JMP  $20DA
12DB: f5          PUSH PSW
12DC: c5          PUSH B
12DD: e5          PUSH H
12DE: 26 19       MVI  H,$19
12E0: cd a2 15    CALL $15A2
12E3: cd 30 13    CALL $1330
12E6: c3 d6 20    JMP  $20D6
12E9: f5          PUSH PSW
12EA: e5          PUSH H
12EB: d5          PUSH D
12EC: c5          PUSH B
12ED: cd 59 12    CALL $1259
12F0: c3 a9 12    JMP  $12A9
12F3: f5          PUSH PSW
12F4: c5          PUSH B
12F5: e5          PUSH H
12F6: cd 59 12    CALL $1259
12F9: 26 19       MVI  H,$19
12FB: cd a2 15    CALL $15A2
12FE: c3 d6 20    JMP  $20D6
1301: f5          PUSH PSW
1302: e5          PUSH H
1303: d5          PUSH D
1304: c5          PUSH B
1305: 26 19       MVI  H,$19
1307: 16 18       MVI  D,$18
1309: 3e 02       MVI  A,$02
130B: cd e5 15    CALL $15E5
130E: cd 75 12    CALL $1275
1311: c3 da 20    JMP  $20DA
1314: f5          PUSH PSW
1315: c5          PUSH B
1316: e5          PUSH H
1317: 26 19       MVI  H,$19
1319: cd a2 15    CALL $15A2
131C: cd 75 12    CALL $1275
131F: c3 d6 20    JMP  $20D6
1322: 3a 1a 5e    LDA  $5E1A
1325: 3c          INR  A
1326: fe 19       CPI  $19
1328: da 2c 13    JC   $132C
132B: 97          SUB  A
132C: 32 1a 5e    STA  $5E1A
132F: c9          RET
1330: 3a 1a 5e    LDA  $5E1A
1333: 3d          DCR  A
1334: fe ff       CPI  $FF
1336: c2 3b 13    JNZ  $133B
1339: 3e 18       MVI  A,$18
133B: 32 1a 5e    STA  $5E1A
133E: c9          RET
133F: f5          PUSH PSW
1340: 3a 26 5e    LDA  $5E26
1343: a7          ANA  A
1344: ca 49 13    JZ   $1349
1347: f1          POP  PSW
1348: c9          RET
1349: cd 1c 1f    CALL $1F1C
134C: f1          POP  PSW
134D: c9          RET
134E: f5          PUSH PSW
134F: 97          SUB  A
1350: c3 56 13    JMP  $1356
1353: f5          PUSH PSW
1354: 3e 01       MVI  A,$01
1356: 32 19 5e    STA  $5E19
1359: f1          POP  PSW
135A: c9          RET
135B: f5          PUSH PSW
135C: 97          SUB  A
135D: c3 63 13    JMP  $1363
1360: f5          PUSH PSW
1361: 3e 01       MVI  A,$01
1363: 32 18 5e    STA  $5E18
1366: f1          POP  PSW
1367: c9          RET
1368: f5          PUSH PSW
1369: e6 03       ANI  $03
136B: 0f          RRC
136C: 0f          RRC
136D: 32 02 5e    STA  $5E02
1370: 3a f6 5d    LDA  $5DF6
1373: cd 06 1f    CALL $1F06
1376: 32 f6 5d    STA  $5DF6
1379: 78          MOV  A,B
137A: e6 01       ANI  $01
137C: 32 f8 5e    STA  $5EF8
137F: 3a f9 5e    LDA  $5EF9
1382: fe 02       CPI  $02
1384: dc a3 13    CC   $13A3
1387: f1          POP  PSW
1388: c9          RET
1389: f5          PUSH PSW
138A: cd 06 1f    CALL $1F06
138D: 32 f6 5d    STA  $5DF6
1390: 3e 02       MVI  A,$02
1392: 32 f9 5e    STA  $5EF9
1395: f3          DI
1396: 3a 0e 5e    LDA  $5E0E
1399: f6 01       ORI  $01
139B: 32 0e 5e    STA  $5E0E
139E: d3 60       OUT  $60
13A0: fb          EI
13A1: f1          POP  PSW
13A2: c9          RET
13A3: f5          PUSH PSW
13A4: 3a f8 5e    LDA  $5EF8
13A7: 32 f9 5e    STA  $5EF9
13AA: a7          ANA  A
13AB: c2 95 13    JNZ  $1395
13AE: f3          DI
13AF: 3a 0e 5e    LDA  $5E0E
13B2: e6 fe       ANI  $FE
13B4: c3 9b 13    JMP  $139B
13B7: c5          PUSH B
13B8: f5          PUSH PSW
13B9: e5          PUSH H
13BA: c3 c3 13    JMP  $13C3
13BD: c5          PUSH B
13BE: f5          PUSH PSW
13BF: e5          PUSH H
13C0: 2a 16 5e    LHLD $5E16
13C3: cd ca 1e    CALL $1ECA
13C6: 06 80       MVI  B,$80
13C8: 4e          MOV  C,M
13C9: 20          RIM
13CA: a0          ANA  B
13CB: c2 c8 13    JNZ  $13C8
13CE: db 70       IN   $70
13D0: 47          MOV  B,A
13D1: c3 88 14    JMP  $1488
13D4: f5          PUSH PSW
13D5: c5          PUSH B
13D6: e5          PUSH H
13D7: c3 e0 13    JMP  $13E0
13DA: f5          PUSH PSW
13DB: c5          PUSH B
13DC: e5          PUSH H
13DD: 2a 16 5e    LHLD $5E16
13E0: cd ca 1e    CALL $1ECA
13E3: e6 3f       ANI  $3F
13E5: 47          MOV  B,A
13E6: 3a f8 5e    LDA  $5EF8
13E9: a7          ANA  A
13EA: ca fe 13    JZ   $13FE
13ED: 7e          MOV  A,M
13EE: 20          RIM
13EF: e6 80       ANI  $80
13F1: c2 ed 13    JNZ  $13ED
13F4: db 70       IN   $70
13F6: e6 c0       ANI  $C0
13F8: b0          ORA  B
13F9: d3 70       OUT  $70
13FB: c3 02 14    JMP  $1402
13FE: 78          MOV  A,B
13FF: cd 06 1f    CALL $1F06
1402: 0e 01       MVI  C,$01
1404: cd 7d 20    CALL $207D
1407: 77          MOV  M,A
1408: 20          RIM
1409: e6 80       ANI  $80
140B: c2 07 14    JNZ  $1407
140E: cd 91 20    CALL $2091
1411: c3 d6 20    JMP  $20D6
1414: f5          PUSH PSW
1415: e5          PUSH H
1416: d5          PUSH D
1417: c5          PUSH B
1418: e6 3f       ANI  $3F
141A: 47          MOV  B,A
141B: cd 06 1f    CALL $1F06
141E: cd bd 1e    CALL $1EBD
1421: eb          XCHG
1422: cd bd 1e    CALL $1EBD
1425: c3 42 14    JMP  $1442
1428: f5          PUSH PSW
1429: e5          PUSH H
142A: d5          PUSH D
142B: c5          PUSH B
142C: cd 9a 1e    CALL $1E9A
142F: da e6 20    JC   $20E6
1432: e6 3f       ANI  $3F
1434: 47          MOV  B,A
1435: cd 06 1f    CALL $1F06
1438: cd bd 1e    CALL $1EBD
143B: eb          XCHG
143C: 2a 16 5e    LHLD $5E16
143F: cd ca 1e    CALL $1ECA
1442: 0e 01       MVI  C,$01
1444: cd 7d 20    CALL $207D
1447: 0e 80       MVI  C,$80
1449: 3a f8 5e    LDA  $5EF8
144C: a7          ANA  A
144D: ca 5d 14    JZ   $145D
1450: 7e          MOV  A,M
1451: 20          RIM
1452: a1          ANA  C
1453: c2 50 14    JNZ  $1450
1456: db 70       IN   $70
1458: e6 c0       ANI  $C0
145A: b0          ORA  B
145B: d3 70       OUT  $70
145D: 77          MOV  M,A
145E: 20          RIM
145F: a1          ANA  C
1460: c2 5d 14    JNZ  $145D
1463: cd dc 1e    CALL $1EDC
1466: cd ca 1f    CALL $1FCA
1469: c2 49 14    JNZ  $1449
146C: cd 91 20    CALL $2091
146F: c3 df 20    JMP  $20DF
1472: c5          PUSH B
1473: f5          PUSH PSW
1474: e5          PUSH H
1475: c3 7e 14    JMP  $147E
1478: c5          PUSH B
1479: f5          PUSH PSW
147A: e5          PUSH H
147B: 2a 16 5e    LHLD $5E16
147E: cd ca 1e    CALL $1ECA
1481: 46          MOV  B,M
1482: 20          RIM
1483: e6 80       ANI  $80
1485: c2 81 14    JNZ  $1481
1488: e1          POP  H
1489: f1          POP  PSW
148A: 78          MOV  A,B
148B: c1          POP  B
148C: c9          RET
148D: f5          PUSH PSW
148E: c5          PUSH B
148F: e5          PUSH H
1490: 4f          MOV  C,A
1491: c3 a3 14    JMP  $14A3
; display_character
1494: f5          PUSH PSW
1495: c5          PUSH B
1496: e5          PUSH H
1497: 4f          MOV  C,A
1498: 3a f9 5d    LDA  $5DF9
149B: f6 01       ORI  $01
149D: 32 f9 5d    STA  $5DF9
14A0: 2a 16 5e    LHLD $5E16
14A3: 2d          DCR  L
14A4: 3a 1a 5e    LDA  $5E1A
14A7: 84          ADD  H
14A8: fe 19       CPI  $19
14AA: da af 14    JC   $14AF
14AD: d6 19       SUI  $19
14AF: c6 60       ADI  $60
14B1: 67          MOV  H,A
14B2: 3a f9 5e    LDA  $5EF9
14B5: fe 01       CPI  $01
14B7: c2 c6 14    JNZ  $14C6
14BA: 7e          MOV  A,M
14BB: 20          RIM
14BC: e6 80       ANI  $80
14BE: c2 ba 14    JNZ  $14BA
14C1: db 70       IN   $70
14C3: cd 06 1f    CALL $1F06
14C6: 71          MOV  M,C
14C7: 20          RIM
14C8: e6 80       ANI  $80
14CA: c2 c6 14    JNZ  $14C6
14CD: 3a f6 5d    LDA  $5DF6
14D0: d3 70       OUT  $70
14D2: c3 d6 20    JMP  $20D6
14D5: eb          XCHG
14D6: e5          PUSH H
14D7: 2a 16 5e    LHLD $5E16
14DA: e3          XTHL
14DB: 22 16 5e    SHLD $5E16
14DE: eb          XCHG
14DF: cd e8 14    CALL $14E8
14E2: e3          XTHL
14E3: 22 16 5e    SHLD $5E16
14E6: e1          POP  H
14E7: c9          RET
; display_string
14E8: f5          PUSH PSW
14E9: 7e          MOV  A,M
14EA: 23          INX  H
14EB: fe 20       CPI  $20
14ED: da fa 14    JC   $14FA
14F0: cd 7a 1f    CALL $1F7A
14F3: d2 e9 14    JNC  $14E9
14F6: f1          POP  PSW
14F7: 7e          MOV  A,M
14F8: 37          STC
14F9: c9          RET
14FA: f1          POP  PSW
14FB: 2b          DCX  H
14FC: 7e          MOV  A,M
14FD: 23          INX  H
14FE: 37          STC
14FF: 3f          CMC
1500: c9          RET
1501: f5          PUSH PSW
1502: e5          PUSH H
1503: d5          PUSH D
1504: c5          PUSH B
1505: 6c          MOV  L,H
1506: cd 82 1e    CALL $1E82
1509: da e6 20    JC   $20E6
150C: cd a2 15    CALL $15A2
150F: c3 df 20    JMP  $20DF
; clear_display
1512: f5          PUSH PSW
1513: e5          PUSH H
1514: d5          PUSH D
1515: c5          PUSH B
1516: 21 01 01    LXI  H,$0101
1519: 22 16 5e    SHLD $5E16
151C: 21 50 60    LXI  H,$6050
151F: 97          SUB  A
1520: cd 06 1f    CALL $1F06
1523: cd a8 20    CALL $20A8
1526: 0e 03       MVI  C,$03
1528: cd 7d 20    CALL $207D
152B: 06 00       MVI  B,$00
152D: 2d          DCR  L
152E: 70          MOV  M,B
152F: c2 2d 15    JNZ  $152D
1532: 2e 50       MVI  L,$50
1534: 24          INR  H
1535: 7c          MOV  A,H
1536: fe 7a       CPI  $7A
1538: c2 2d 15    JNZ  $152D
153B: cd ba 20    CALL $20BA
153E: cd 91 20    CALL $2091
1541: c3 da 20    JMP  $20DA
1544: f5          PUSH PSW
1545: e5          PUSH H
1546: d5          PUSH D
1547: c5          PUSH B
1548: cd 9a 1e    CALL $1E9A
154B: da e6 20    JC   $20E6
154E: cd bd 1e    CALL $1EBD
1551: eb          XCHG
1552: cd 5c 20    CALL $205C
1555: 2a 16 5e    LHLD $5E16
1558: cd ca 1e    CALL $1ECA
155B: 97          SUB  A
155C: cd 06 1f    CALL $1F06
155F: 0e 80       MVI  C,$80
1561: 3a f8 5e    LDA  $5EF8
1564: a7          ANA  A
1565: ca 8d 15    JZ   $158D
1568: 3a 25 5e    LDA  $5E25
156B: fe 02       CPI  $02
156D: d2 8d 15    JNC  $158D
1570: 7e          MOV  A,M
1571: 20          RIM
1572: a1          ANA  C
1573: c2 70 15    JNZ  $1570
1576: 3a 25 5e    LDA  $5E25
1579: a7          ANA  A
157A: c2 86 15    JNZ  $1586
157D: db 70       IN   $70
157F: e6 c0       ANI  $C0
1581: d3 70       OUT  $70
1583: c3 8d 15    JMP  $158D
1586: db 70       IN   $70
1588: e6 3f       ANI  $3F
158A: cd 06 1f    CALL $1F06
158D: 70          MOV  M,B
158E: 20          RIM
158F: a1          ANA  C
1590: c2 8d 15    JNZ  $158D
1593: cd dc 1e    CALL $1EDC
1596: cd ca 1f    CALL $1FCA
1599: c2 61 15    JNZ  $1561
159C: cd 91 20    CALL $2091
159F: c3 df 20    JMP  $20DF
15A2: 0e 03       MVI  C,$03
15A4: cd 7d 20    CALL $207D
15A7: cd ca 1e    CALL $1ECA
15AA: 2e 4f       MVI  L,$4F
15AC: 97          SUB  A
15AD: cd 06 1f    CALL $1F06
15B0: 0e 80       MVI  C,$80
15B2: 36 00       MVI  M,$00
15B4: 20          RIM
15B5: a1          ANA  C
15B6: c2 b2 15    JNZ  $15B2
15B9: 2d          DCR  L
15BA: c2 b2 15    JNZ  $15B2
15BD: 36 00       MVI  M,$00
15BF: 20          RIM
15C0: a1          ANA  C
15C1: c2 bd 15    JNZ  $15BD
15C4: cd 91 20    CALL $2091
15C7: c9          RET
15C8: f5          PUSH PSW
15C9: e5          PUSH H
15CA: d5          PUSH D
15CB: c5          PUSH B
15CC: 47          MOV  B,A
15CD: 2e 01       MVI  L,$01
15CF: 5d          MOV  E,L
15D0: cd 82 1e    CALL $1E82
15D3: da e6 20    JC   $20E6
15D6: eb          XCHG
15D7: cd 82 1e    CALL $1E82
15DA: eb          XCHG
15DB: da e6 20    JC   $20E6
15DE: 78          MOV  A,B
15DF: cd e5 15    CALL $15E5
15E2: c3 df 20    JMP  $20DF
15E5: cd 5c 20    CALL $205C
15E8: cd ca 1e    CALL $1ECA
15EB: eb          XCHG
15EC: cd ca 1e    CALL $1ECA
15EF: eb          XCHG
15F0: 2e 00       MVI  L,$00
15F2: 5d          MOV  E,L
15F3: cd dc 1f    CALL $1FDC
15F6: cd 35 20    CALL $2035
15F9: 2c          INR  L
15FA: 1c          INR  E
15FB: 7d          MOV  A,L
15FC: fe 50       CPI  $50
15FE: c2 f3 15    JNZ  $15F3
1601: cd 91 20    CALL $2091
1604: c9          RET
1605: f5          PUSH PSW
1606: e5          PUSH H
1607: d5          PUSH D
1608: c5          PUSH B
1609: 47          MOV  B,A
160A: 2e 01       MVI  L,$01
160C: 5d          MOV  E,L
160D: cd 82 1e    CALL $1E82
1610: da e6 20    JC   $20E6
1613: cd ca 1e    CALL $1ECA
1616: eb          XCHG
1617: cd 82 1e    CALL $1E82
161A: da e6 20    JC   $20E6
161D: cd ca 1e    CALL $1ECA
1620: eb          XCHG
1621: 78          MOV  A,B
1622: cd 5c 20    CALL $205C
1625: cd dc 1f    CALL $1FDC
1628: 2c          INR  L
1629: 1c          INR  E
162A: 7d          MOV  A,L
162B: fe 50       CPI  $50
162D: c2 25 16    JNZ  $1625
1630: cd 91 20    CALL $2091
1633: c3 df 20    JMP  $20DF
1636: f5          PUSH PSW
1637: e5          PUSH H
1638: d5          PUSH D
1639: c5          PUSH B
163A: 2e 01       MVI  L,$01
163C: cd ca 1e    CALL $1ECA
163F: 0e 03       MVI  C,$03
1641: cd 7d 20    CALL $207D
1644: 1a          LDAX D
1645: 13          INX  D
1646: 47          MOV  B,A
1647: 1a          LDAX D
1648: 13          INX  D
1649: 4f          MOV  C,A
164A: 0f          RRC
164B: 0f          RRC
164C: 0f          RRC
164D: 0f          RRC
164E: e6 0f       ANI  $0F
1650: cd 06 1f    CALL $1F06
1653: 70          MOV  M,B
1654: 20          RIM
1655: e6 80       ANI  $80
1657: c2 53 16    JNZ  $1653
165A: 2c          INR  L
165B: 79          MOV  A,C
165C: e6 0f       ANI  $0F
165E: cd 06 1f    CALL $1F06
1661: 1a          LDAX D
1662: 13          INX  D
1663: 47          MOV  B,A
1664: 70          MOV  M,B
1665: 20          RIM
1666: e6 80       ANI  $80
1668: c2 64 16    JNZ  $1664
166B: 2c          INR  L
166C: 7d          MOV  A,L
166D: fe 50       CPI  $50
166F: c2 44 16    JNZ  $1644
1672: cd 91 20    CALL $2091
1675: c3 da 20    JMP  $20DA
1678: f5          PUSH PSW
1679: e5          PUSH H
167A: d5          PUSH D
167B: c5          PUSH B
167C: 2e 01       MVI  L,$01
167E: cd ca 1e    CALL $1ECA
1681: 46          MOV  B,M
1682: 20          RIM
1683: e6 80       ANI  $80
1685: c2 81 16    JNZ  $1681
1688: 78          MOV  A,B
1689: 12          STAX D
168A: 13          INX  D
168B: db 70       IN   $70
168D: 07          RLC
168E: 07          RLC
168F: 07          RLC
1690: 07          RLC
1691: e6 f0       ANI  $F0
1693: 4f          MOV  C,A
1694: 13          INX  D
1695: 2c          INR  L
1696: 46          MOV  B,M
1697: 20          RIM
1698: e6 80       ANI  $80
169A: c2 96 16    JNZ  $1696
169D: 78          MOV  A,B
169E: 12          STAX D
169F: db 70       IN   $70
16A1: e6 0f       ANI  $0F
16A3: b1          ORA  C
16A4: 1b          DCX  D
16A5: 12          STAX D
16A6: 13          INX  D
16A7: 13          INX  D
16A8: 2c          INR  L
16A9: 7d          MOV  A,L
16AA: fe 50       CPI  $50
16AC: c2 81 16    JNZ  $1681
16AF: c3 da 20    JMP  $20DA
16B2: f5          PUSH PSW
16B3: e5          PUSH H
16B4: 2e 01       MVI  L,$01
16B6: cd 82 1e    CALL $1E82
16B9: da e8 20    JC   $20E8
16BC: 7c          MOV  A,H
16BD: 32 3f 5e    STA  $5E3F
16C0: d5          PUSH D
16C1: 11 40 5e    LXI  D,$5E40
16C4: cd 78 16    CALL $1678
16C7: cd 01 15    CALL $1501
16CA: c3 e0 20    JMP  $20E0
16CD: f5          PUSH PSW
16CE: e5          PUSH H
16CF: 3a 3f 5e    LDA  $5E3F
16D2: a7          ANA  A
16D3: ca e8 20    JZ   $20E8
16D6: d5          PUSH D
16D7: 67          MOV  H,A
16D8: 97          SUB  A
16D9: 32 3f 5e    STA  $5E3F
16DC: 11 40 5e    LXI  D,$5E40
16DF: cd 36 16    CALL $1636
16E2: c3 e0 20    JMP  $20E0
16E5: f5          PUSH PSW
16E6: e5          PUSH H
16E7: d5          PUSH D
16E8: c5          PUSH B
16E9: 2e 01       MVI  L,$01
16EB: cd ca 1e    CALL $1ECA
16EE: 0e 03       MVI  C,$03
16F0: cd 7d 20    CALL $207D
16F3: 1a          LDAX D
16F4: 13          INX  D
16F5: 47          MOV  B,A
16F6: 1a          LDAX D
16F7: 13          INX  D
16F8: d3 70       OUT  $70
16FA: 70          MOV  M,B
16FB: 20          RIM
16FC: e6 80       ANI  $80
16FE: c2 fa 16    JNZ  $16FA
1701: 2c          INR  L
1702: 7d          MOV  A,L
1703: fe 50       CPI  $50
1705: c2 f3 16    JNZ  $16F3
1708: cd 91 20    CALL $2091
170B: c3 da 20    JMP  $20DA
170E: f5          PUSH PSW
170F: e5          PUSH H
1710: d5          PUSH D
1711: c5          PUSH B
1712: 2e 01       MVI  L,$01
1714: cd ca 1e    CALL $1ECA
1717: 46          MOV  B,M
1718: 20          RIM
1719: e6 80       ANI  $80
171B: c2 17 17    JNZ  $1717
171E: 78          MOV  A,B
171F: 12          STAX D
1720: 13          INX  D
1721: db 70       IN   $70
1723: 12          STAX D
1724: 13          INX  D
1725: 2c          INR  L
1726: 7d          MOV  A,L
1727: fe 50       CPI  $50
1729: c2 17 17    JNZ  $1717
172C: c3 da 20    JMP  $20DA
172F: f5          PUSH PSW
1730: e5          PUSH H
1731: d5          PUSH D
1732: c5          PUSH B
1733: cd 5c 20    CALL $205C
1736: cd 13 18    CALL $1813
1739: 44          MOV  B,H
173A: 4d          MOV  C,L
173B: 2a 16 5e    LHLD $5E16
173E: e5          PUSH H
173F: 3e 01       MVI  A,$01
1741: 32 2d 5e    STA  $5E2D
1744: 7a          MOV  A,D
1745: b3          ORA  E
1746: ca 50 17    JZ   $1750
1749: cd 08 18    CALL $1808
174C: 1b          DCX  D
174D: c3 44 17    JMP  $1744
1750: eb          XCHG
1751: e1          POP  H
1752: cd d6 1f    CALL $1FD6
1755: d2 c7 17    JNC  $17C7
1758: eb          XCHG
1759: cd 13 18    CALL $1813
175C: eb          XCHG
175D: cd d6 1f    CALL $1FD6
1760: c2 24 18    JNZ  $1824
1763: eb          XCHG
1764: 60          MOV  H,B
1765: 69          MOV  L,C
1766: cd bd 1e    CALL $1EBD
1769: 44          MOV  B,H
176A: 4d          MOV  C,L
176B: eb          XCHG
176C: cd bd 1e    CALL $1EBD
176F: c3 f9 17    JMP  $17F9
1772: f5          PUSH PSW
1773: e5          PUSH H
1774: d5          PUSH D
1775: c5          PUSH B
1776: cd 5c 20    CALL $205C
1779: 44          MOV  B,H
177A: 4d          MOV  C,L
177B: 2a 16 5e    LHLD $5E16
177E: e5          PUSH H
177F: 3e ff       MVI  A,$FF
1781: 32 2d 5e    STA  $5E2D
1784: 7a          MOV  A,D
1785: b3          ORA  E
1786: ca 90 17    JZ   $1790
1789: cd 13 18    CALL $1813
178C: 1b          DCX  D
178D: c3 84 17    JMP  $1784
1790: eb          XCHG
1791: e1          POP  H
1792: cd d6 1f    CALL $1FD6
1795: da c7 17    JC   $17C7
1798: ca c7 17    JZ   $17C7
179B: eb          XCHG
179C: cd 08 18    CALL $1808
179F: c3 5c 17    JMP  $175C
17A2: f5          PUSH PSW
17A3: e5          PUSH H
17A4: d5          PUSH D
17A5: c5          PUSH B
17A6: cd 5c 20    CALL $205C
17A9: cd 13 18    CALL $1813
17AC: e5          PUSH H
17AD: 2a 16 5e    LHLD $5E16
17B0: 44          MOV  B,H
17B1: 4d          MOV  C,L
17B2: e1          POP  H
17B3: c3 7e 17    JMP  $177E
17B6: f5          PUSH PSW
17B7: e5          PUSH H
17B8: d5          PUSH D
17B9: c5          PUSH B
17BA: cd 5c 20    CALL $205C
17BD: e5          PUSH H
17BE: 2a 16 5e    LHLD $5E16
17C1: 44          MOV  B,H
17C2: 4d          MOV  C,L
17C3: e1          POP  H
17C4: c3 3e 17    JMP  $173E
17C7: cd bd 1e    CALL $1EBD
17CA: eb          XCHG
17CB: cd bd 1e    CALL $1EBD
17CE: eb          XCHG
17CF: e5          PUSH H
17D0: 60          MOV  H,B
17D1: 69          MOV  L,C
17D2: cd bd 1e    CALL $1EBD
17D5: 44          MOV  B,H
17D6: 4d          MOV  C,L
17D7: e1          POP  H
17D8: c5          PUSH B
17D9: eb          XCHG
17DA: cd dc 1f    CALL $1FDC
17DD: eb          XCHG
17DE: c1          POP  B
17DF: cd d6 1f    CALL $1FD6
17E2: ca f0 17    JZ   $17F0
17E5: cd e4 1e    CALL $1EE4
17E8: eb          XCHG
17E9: cd e4 1e    CALL $1EE4
17EC: eb          XCHG
17ED: c3 d8 17    JMP  $17D8
17F0: cd d0 1f    CALL $1FD0
17F3: ca 1e 18    JZ   $181E
17F6: cd e4 1e    CALL $1EE4
17F9: 7e          MOV  A,M
17FA: 20          RIM
17FB: e6 80       ANI  $80
17FD: c2 f9 17    JNZ  $17F9
1800: db 70       IN   $70
1802: cd 35 20    CALL $2035
1805: c3 f0 17    JMP  $17F0
1808: 2c          INR  L
1809: 7d          MOV  A,L
180A: fe 51       CPI  $51
180C: c0          RNZ
180D: 2e 01       MVI  L,$01
180F: 24          INR  H
1810: c0          RNZ
1811: 25          DCR  H
1812: c9          RET
1813: 2d          DCR  L
1814: c0          RNZ
1815: 2e 50       MVI  L,$50
1817: 25          DCR  H
1818: 7c          MOV  A,H
1819: fe ff       CPI  $FF
181B: c0          RNZ
181C: 24          INR  H
181D: c9          RET
181E: cd 91 20    CALL $2091
1821: c3 df 20    JMP  $20DF
1824: cd 91 20    CALL $2091
1827: c3 e6 20    JMP  $20E6
182A: f5          PUSH PSW
182B: e5          PUSH H
182C: d5          PUSH D
182D: c5          PUSH B
182E: 4f          MOV  C,A
182F: 3a 17 5e    LDA  $5E17
1832: bc          CMP  H
1833: ca b8 18    JZ   $18B8
1836: d2 e6 20    JNC  $20E6
1839: 47          MOV  B,A
183A: 54          MOV  D,H
183B: 25          DCR  H
183C: 79          MOV  A,C
183D: cd c8 15    CALL $15C8
1840: da e6 20    JC   $20E6
1843: 7c          MOV  A,H
1844: b8          CMP  B
1845: ca df 20    JZ   $20DF
1848: 25          DCR  H
1849: 15          DCR  D
184A: c3 3c 18    JMP  $183C
184D: f5          PUSH PSW
184E: e5          PUSH H
184F: d5          PUSH D
1850: c5          PUSH B
1851: 4f          MOV  C,A
1852: 3a 17 5e    LDA  $5E17
1855: bc          CMP  H
1856: ca b8 18    JZ   $18B8
1859: da e6 20    JC   $20E6
185C: 47          MOV  B,A
185D: 54          MOV  D,H
185E: 24          INR  H
185F: 79          MOV  A,C
1860: cd c8 15    CALL $15C8
1863: da e6 20    JC   $20E6
1866: 7c          MOV  A,H
1867: b8          CMP  B
1868: ca df 20    JZ   $20DF
186B: 24          INR  H
186C: 14          INR  D
186D: c3 5f 18    JMP  $185F
1870: f5          PUSH PSW
1871: e5          PUSH H
1872: d5          PUSH D
1873: c5          PUSH B
1874: 4f          MOV  C,A
1875: 3a 17 5e    LDA  $5E17
1878: bc          CMP  H
1879: ca b8 18    JZ   $18B8
187C: d2 e6 20    JNC  $20E6
187F: 44          MOV  B,H
1880: 67          MOV  H,A
1881: 57          MOV  D,A
1882: 24          INR  H
1883: 79          MOV  A,C
1884: cd c8 15    CALL $15C8
1887: da e6 20    JC   $20E6
188A: 7c          MOV  A,H
188B: b8          CMP  B
188C: ca df 20    JZ   $20DF
188F: 24          INR  H
1890: 14          INR  D
1891: c3 83 18    JMP  $1883
1894: f5          PUSH PSW
1895: e5          PUSH H
1896: d5          PUSH D
1897: c5          PUSH B
1898: 4f          MOV  C,A
1899: 3a 17 5e    LDA  $5E17
189C: bc          CMP  H
189D: ca b8 18    JZ   $18B8
18A0: da e6 20    JC   $20E6
18A3: 44          MOV  B,H
18A4: 67          MOV  H,A
18A5: 57          MOV  D,A
18A6: 25          DCR  H
18A7: 79          MOV  A,C
18A8: cd c8 15    CALL $15C8
18AB: da e6 20    JC   $20E6
18AE: 78          MOV  A,B
18AF: bc          CMP  H
18B0: ca df 20    JZ   $20DF
18B3: 25          DCR  H
18B4: 15          DCR  D
18B5: c3 a7 18    JMP  $18A7
18B8: 67          MOV  H,A
18B9: cd 01 15    CALL $1501
18BC: c3 df 20    JMP  $20DF
18BF: f5          PUSH PSW
18C0: e5          PUSH H
18C1: d5          PUSH D
18C2: c5          PUSH B
18C3: cd 9a 1e    CALL $1E9A
18C6: da e6 20    JC   $20E6
18C9: c5          PUSH B
18CA: cd bd 1e    CALL $1EBD
18CD: 22 12 5e    SHLD $5E12
18D0: 2a 16 5e    LHLD $5E16
18D3: cd ca 1e    CALL $1ECA
18D6: cd a8 20    CALL $20A8
18D9: 0e 03       MVI  C,$03
18DB: cd 7d 20    CALL $207D
18DE: c1          POP  B
18DF: 7e          MOV  A,M
18E0: f5          PUSH PSW
18E1: 0a          LDAX B
18E2: d3 70       OUT  $70
18E4: 1a          LDAX D
18E5: 77          MOV  M,A
18E6: f1          POP  PSW
18E7: 12          STAX D
18E8: db 70       IN   $70
18EA: 02          STAX B
18EB: cd dc 1e    CALL $1EDC
18EE: d5          PUSH D
18EF: eb          XCHG
18F0: 2a 12 5e    LHLD $5E12
18F3: cd ca 1f    CALL $1FCA
18F6: ca 00 19    JZ   $1900
18F9: eb          XCHG
18FA: d1          POP  D
18FB: 13          INX  D
18FC: 03          INX  B
18FD: c3 df 18    JMP  $18DF
1900: d1          POP  D
1901: cd ba 20    CALL $20BA
1904: cd 91 20    CALL $2091
1907: c3 df 20    JMP  $20DF
190A: c5          PUSH B
190B: d5          PUSH D
190C: e5          PUSH H
190D: f5          PUSH PSW
190E: cd 12 15    CALL $1512
1911: 11 2e 5e    LXI  D,$5E2E
1914: 06 05       MVI  B,$05
1916: 7e          MOV  A,M
1917: 12          STAX D
1918: 23          INX  H
1919: 13          INX  D
191A: 05          DCR  B
191B: c2 16 19    JNZ  $1916
191E: 11 b8 5e    LXI  D,$5EB8
1921: cd e6 10    CALL $10E6
1924: 21 09 01    LXI  H,$0109
1927: cd 4d 12    CALL $124D
192A: af          XRA  A
192B: cd 89 13    CALL $1389
192E: 2a 2e 5e    LHLD $5E2E
1931: cd a4 1d    CALL $1DA4
1934: 3e 20       MVI  A,$20
1936: cd 89 13    CALL $1389
1939: cd 7a 1f    CALL $1F7A
193C: cd 7a 1f    CALL $1F7A
193F: 3a 30 5e    LDA  $5E30
1942: a7          ANA  A
1943: ca 50 19    JZ   $1950
1946: c6 30       ADI  $30
1948: cd 7a 1f    CALL $1F7A
194B: 3e 20       MVI  A,$20
194D: cd 94 14    CALL $1494
1950: 97          SUB  A
1951: cd 89 13    CALL $1389
1954: 3a 31 5e    LDA  $5E31
1957: 47          MOV  B,A
1958: cd 5a 1a    CALL $1A5A
195B: 04          INR  B
195C: 3a 32 5e    LDA  $5E32
195F: 3c          INR  A
1960: b8          CMP  B
1961: c2 58 19    JNZ  $1958
1964: 3a 31 5e    LDA  $5E31
1967: 47          MOV  B,A
1968: cd 55 12    CALL $1255
196B: 2e 34       MVI  L,$34
196D: 97          SUB  A
196E: cd 28 14    CALL $1428
1971: cd 5a 1a    CALL $1A5A
1974: cd 55 12    CALL $1255
1977: 2e 34       MVI  L,$34
1979: 3e 03       MVI  A,$03
197B: cd 28 14    CALL $1428
197E: cd d0 0c    CALL $0CD0
1981: da 7e 19    JC   $197E
1984: fe ed       CPI  $ED
1986: c2 8f 19    JNZ  $198F
1989: cd e6 19    CALL $19E6
198C: c3 71 19    JMP  $1971
198F: fe b8       CPI  $B8
1991: ca 64 19    JZ   $1964
1994: fe b1       CPI  $B1
1996: c2 a4 19    JNZ  $19A4
1999: 3a 31 5e    LDA  $5E31
199C: b8          CMP  B
199D: ca 7e 19    JZ   $197E
19A0: 05          DCR  B
19A1: c3 68 19    JMP  $1968
19A4: fe b2       CPI  $B2
19A6: c2 b4 19    JNZ  $19B4
19A9: 3a 32 5e    LDA  $5E32
19AC: b8          CMP  B
19AD: ca 68 19    JZ   $1968
19B0: 04          INR  B
19B1: c3 68 19    JMP  $1968
19B4: fe f8       CPI  $F8
19B6: ca d1 19    JZ   $19D1
19B9: fe db       CPI  $DB
19BB: ca d1 19    JZ   $19D1
19BE: fe fc       CPI  $FC
19C0: c2 cb 19    JNZ  $19CB
19C3: c5          PUSH B
19C4: cd df 19    CALL $19DF
19C7: c1          POP  B
19C8: c3 7e 19    JMP  $197E
19CB: cd 2d 0d    CALL $0D2D
19CE: c3 7e 19    JMP  $197E
19D1: 47          MOV  B,A
19D2: cd 12 15    CALL $1512
19D5: 97          SUB  A
19D6: cd 89 13    CALL $1389
19D9: f1          POP  PSW
19DA: 78          MOV  A,B
19DB: e1          POP  H
19DC: d1          POP  D
19DD: c1          POP  B
19DE: c9          RET
19DF: 2a 08 5e    LHLD $5E08
19E2: 7c          MOV  A,H
19E3: b5          ORA  L
19E4: c8          RZ
19E5: e9          PCHL
19E6: c5          PUSH B
19E7: 2a 37 5e    LHLD $5E37
19EA: 46          MOV  B,M
19EB: 04          INR  B
19EC: 0e 00       MVI  C,$00
19EE: 0c          INR  C
19EF: cd 08 1b    CALL $1B08
19F2: 78          MOV  A,B
19F3: b9          CMP  C
19F4: 3e 00       MVI  A,$00
19F6: c2 fb 19    JNZ  $19FB
19F9: 3e 03       MVI  A,$03
19FB: cd 89 13    CALL $1389
19FE: cd c1 1a    CALL $1AC1
1A01: 3a 39 5e    LDA  $5E39
1A04: b9          CMP  C
1A05: c2 ee 19    JNZ  $19EE
1A08: 2a 35 5e    LHLD $5E35
1A0B: 7e          MOV  A,M
1A0C: b9          CMP  C
1A0D: da 11 1a    JC   $1A11
1A10: 97          SUB  A
1A11: 4f          MOV  C,A
1A12: 0c          INR  C
1A13: cd 08 1b    CALL $1B08
1A16: cd d0 0c    CALL $0CD0
1A19: da 16 1a    JC   $1A16
1A1C: fe ed       CPI  $ED
1A1E: ca 47 1a    JZ   $1A47
1A21: fe b8       CPI  $B8
1A23: c2 2b 1a    JNZ  $1A2B
1A26: 0e 01       MVI  C,$01
1A28: c3 13 1a    JMP  $1A13
1A2B: fe b4       CPI  $B4
1A2D: c2 37 1a    JNZ  $1A37
1A30: 0d          DCR  C
1A31: ca 26 1a    JZ   $1A26
1A34: c3 13 1a    JMP  $1A13
1A37: fe b3       CPI  $B3
1A39: c2 16 1a    JNZ  $1A16
1A3C: 3a 39 5e    LDA  $5E39
1A3F: b9          CMP  C
1A40: ca 16 1a    JZ   $1A16
1A43: 0c          INR  C
1A44: c3 13 1a    JMP  $1A13
1A47: 2a 35 5e    LHLD $5E35
1A4A: 0d          DCR  C
1A4B: 71          MOV  M,C
1A4C: 26 17       MVI  H,$17
1A4E: 0e 03       MVI  C,$03
1A50: cd 01 15    CALL $1501
1A53: 24          INR  H
1A54: 0d          DCR  C
1A55: c2 50 1a    JNZ  $1A50
1A58: c1          POP  B
1A59: c9          RET
1A5A: cd f5 1a    CALL $1AF5
1A5D: cd 01 15    CALL $1501
1A60: cd 71 1a    CALL $1A71
1A63: cd fa 1a    CALL $1AFA
1A66: 2a 35 5e    LHLD $5E35
1A69: 4e          MOV  C,M
1A6A: 0c          INR  C
1A6B: cd c1 1a    CALL $1AC1
1A6E: c3 f5 1a    JMP  $1AF5
1A71: c5          PUSH B
1A72: 2a 2e 5e    LHLD $5E2E
1A75: cd e5 1a    CALL $1AE5
1A78: 05          DCR  B
1A79: ca 8c 1a    JZ   $1A8C
1A7C: cd e5 1a    CALL $1AE5
1A7F: 23          INX  H
1A80: 5e          MOV  E,M
1A81: 23          INX  H
1A82: cd ed 1a    CALL $1AED
1A85: 1d          DCR  E
1A86: c2 82 1a    JNZ  $1A82
1A89: c3 78 1a    JMP  $1A78
1A8C: cd 12 1e    CALL $1E12
1A8F: 5e          MOV  E,M
1A90: 16 00       MVI  D,$00
1A92: e5          PUSH H
1A93: 21 00 5f    LXI  H,$5F00
1A96: 19          DAD  D
1A97: 22 35 5e    SHLD $5E35
1A9A: 7e          MOV  A,M
1A9B: 21 b8 5e    LXI  H,$5EB8
1A9E: 19          DAD  D
1A9F: 22 37 5e    SHLD $5E37
1AA2: be          CMP  M
1AA3: 3e 20       MVI  A,$20
1AA5: ca aa 1a    JZ   $1AAA
1AA8: 3e 2a       MVI  A,$2A
1AAA: cd 55 12    CALL $1255
1AAD: 2e 26       MVI  L,$26
1AAF: cd 4d 12    CALL $124D
1AB2: cd 94 14    CALL $1494
1AB5: e1          POP  H
1AB6: 23          INX  H
1AB7: 7e          MOV  A,M
1AB8: 32 39 5e    STA  $5E39
1ABB: 23          INX  H
1ABC: 22 33 5e    SHLD $5E33
1ABF: c1          POP  B
1AC0: c9          RET
1AC1: c5          PUSH B
1AC2: 2a 33 5e    LHLD $5E33
1AC5: 0d          DCR  C
1AC6: ca cf 1a    JZ   $1ACF
1AC9: cd ed 1a    CALL $1AED
1ACC: c3 c5 1a    JMP  $1AC5
1ACF: 7e          MOV  A,M
1AD0: fe 80       CPI  $80
1AD2: d2 da 1a    JNC  $1ADA
1AD5: cd 12 1e    CALL $1E12
1AD8: c1          POP  B
1AD9: c9          RET
1ADA: 21 3a 5e    LXI  H,$5E3A
1ADD: 77          MOV  M,A
1ADE: 23          INX  H
1ADF: 36 00       MVI  M,$00
1AE1: 2b          DCX  H
1AE2: c3 d5 1a    JMP  $1AD5
1AE5: 7e          MOV  A,M
1AE6: 23          INX  H
1AE7: fe 20       CPI  $20
1AE9: d2 e5 1a    JNC  $1AE5
1AEC: c9          RET
1AED: 7e          MOV  A,M
1AEE: fe 80       CPI  $80
1AF0: da e5 1a    JC   $1AE5
1AF3: 23          INX  H
1AF4: c9          RET
1AF5: 2e 0a       MVI  L,$0A
1AF7: c3 fc 1a    JMP  $1AFC
1AFA: 2e 28       MVI  L,$28
1AFC: 3a 31 5e    LDA  $5E31
1AFF: 4f          MOV  C,A
1B00: 78          MOV  A,B
1B01: 91          SUB  C
1B02: c6 03       ADI  $03
1B04: 67          MOV  H,A
1B05: c3 51 12    JMP  $1251
1B08: c5          PUSH B
1B09: 21 01 19    LXI  H,$1901
1B0C: 3a 39 5e    LDA  $5E39
1B0F: fe 07       CPI  $07
1B11: da 1d 1b    JC   $1B1D
1B14: 26 18       MVI  H,$18
1B16: fe 0d       CPI  $0D
1B18: da 1d 1b    JC   $1B1D
1B1B: 26 17       MVI  H,$17
1B1D: 0d          DCR  C
1B1E: ca 30 1b    JZ   $1B30
1B21: 7d          MOV  A,L
1B22: c6 0d       ADI  $0D
1B24: 6f          MOV  L,A
1B25: fe 45       CPI  $45
1B27: da 1d 1b    JC   $1B1D
1B2A: 2e 01       MVI  L,$01
1B2C: 24          INR  H
1B2D: c3 1d 1b    JMP  $1B1D
1B30: cd 4d 12    CALL $124D
1B33: c1          POP  B
1B34: c9          RET
; push_key_menu
1B35: f5          PUSH PSW
1B36: e5          PUSH H
1B37: d5          PUSH D
1B38: c5          PUSH B
1B39: cd 12 15    CALL $1512
1B3C: 21 14 01    LXI  H,$0114
1B3F: 22 16 5e    SHLD $5E16
1B42: af          XRA  A
1B43: cd 89 13    CALL $1389
1B46: 21 c1 1c    LXI  H,$1CC1
1B49: cd a4 1d    CALL $1DA4
1B4C: 06 01       MVI  B,$01
1B4E: cd a3 13    CALL $13A3
1B51: cd 75 1c    CALL $1C75
1B54: 7d          MOV  A,L
1B55: d6 04       SUI  $04
1B57: 6f          MOV  L,A
1B58: 22 16 5e    SHLD $5E16
1B5B: 78          MOV  A,B
1B5C: cd 35 1f    CALL $1F35
1B5F: cd b7 11    CALL $11B7
1B62: 3e 3a       MVI  A,$3A
1B64: cd 94 14    CALL $1494
1B67: cd 75 1c    CALL $1C75
1B6A: 78          MOV  A,B
1B6B: 3d          DCR  A
1B6C: cd 71 1d    CALL $1D71
1B6F: cd 58 1d    CALL $1D58
1B72: cd 1c 10    CALL $101C
1B75: cd a6 1c    CALL $1CA6
1B78: cd b7 11    CALL $11B7
1B7B: 23          INX  H
1B7C: 0d          DCR  C
1B7D: c2 72 1b    JNZ  $1B72
1B80: 04          INR  B
1B81: 78          MOV  A,B
1B82: fe 11       CPI  $11
1B84: c2 4e 1b    JNZ  $1B4E
1B87: cd a3 13    CALL $13A3
1B8A: 21 19 19    LXI  H,$1919
1B8D: 22 16 5e    SHLD $5E16
1B90: 21 cf 1c    LXI  H,$1CCF
1B93: cd e8 14    CALL $14E8
1B96: 3e 01       MVI  A,$01
1B98: cd 89 13    CALL $1389
1B9B: 21 db 1c    LXI  H,$1CDB
1B9E: cd e8 14    CALL $14E8
1BA1: 1e 00       MVI  E,$00
1BA3: 06 01       MVI  B,$01
1BA5: 78          MOV  A,B
1BA6: bb          CMP  E
1BA7: ca b8 1b    JZ   $1BB8
1BAA: cd 75 1c    CALL $1C75
1BAD: 78          MOV  A,B
1BAE: 3d          DCR  A
1BAF: cd 58 1d    CALL $1D58
1BB2: cd 71 1d    CALL $1D71
1BB5: 16 01       MVI  D,$01
1BB7: 58          MOV  E,B
1BB8: d5          PUSH D
1BB9: e5          PUSH H
1BBA: cd 1c 10    CALL $101C
1BBD: 5f          MOV  E,A
1BBE: 2a 16 5e    LHLD $5E16
1BC1: e5          PUSH H
1BC2: 21 25 19    LXI  H,$1925
1BC5: 22 16 5e    SHLD $5E16
1BC8: 3e 01       MVI  A,$01
1BCA: cd 89 13    CALL $1389
1BCD: 7b          MOV  A,E
1BCE: cd 5b 1f    CALL $1F5B
1BD1: e1          POP  H
1BD2: 22 16 5e    SHLD $5E16
1BD5: e1          POP  H
1BD6: d1          POP  D
1BD7: cd d0 0c    CALL $0CD0
1BDA: da d7 1b    JC   $1BD7
1BDD: fe db       CPI  $DB
1BDF: c2 ec 1b    JNZ  $1BEC
1BE2: cd 12 15    CALL $1512
1BE5: 97          SUB  A
1BE6: cd 89 13    CALL $1389
1BE9: c3 da 20    JMP  $20DA
1BEC: cd f2 1b    CALL $1BF2
1BEF: c3 a5 1b    JMP  $1BA5
; push_key_edit_command
1BF2: fe fc       CPI  $FC
1BF4: f5          PUSH PSW
1BF5: c5          PUSH B
1BF6: d5          PUSH D
1BF7: e5          PUSH H
1BF8: cc df 19    CZ   $19DF
1BFB: e1          POP  H
1BFC: d1          POP  D
1BFD: c1          POP  B
1BFE: f1          POP  PSW
1BFF: c8          RZ
1C00: fe cf       CPI  $CF
1C02: c2 0e 1c    JNZ  $1C0E
1C05: cd d0 0c    CALL $0CD0
1C08: da 05 1c    JC   $1C05
1C0B: c3 53 1c    JMP  $1C53
1C0E: fe ce       CPI  $CE
1C10: c2 1c 1c    JNZ  $1C1C
1C13: cd 80 1f    CALL $1F80
1C16: da 2d 0d    JC   $0D2D
1C19: c3 53 1c    JMP  $1C53
1C1C: fe b8       CPI  $B8
1C1E: c2 24 1c    JNZ  $1C24
1C21: 06 01       MVI  B,$01
1C23: c9          RET
1C24: fe b1       CPI  $B1
1C26: c2 2d 1c    JNZ  $1C2D
1C29: 05          DCR  B
1C2A: c0          RNZ
1C2B: 04          INR  B
1C2C: c9          RET
1C2D: fe b2       CPI  $B2
1C2F: c2 38 1c    JNZ  $1C38
1C32: 78          MOV  A,B
1C33: fe 10       CPI  $10
1C35: c8          RZ
1C36: 04          INR  B
1C37: c9          RET
1C38: fe b3       CPI  $B3
1C3A: c2 45 1c    JNZ  $1C45
1C3D: 7a          MOV  A,D
1C3E: b9          CMP  C
1C3F: c8          RZ
1C40: 14          INR  D
1C41: 23          INX  H
1C42: c3 b7 11    JMP  $11B7
1C45: fe b4       CPI  $B4
1C47: c2 53 1c    JNZ  $1C53
1C4A: 7a          MOV  A,D
1C4B: fe 01       CPI  $01
1C4D: c8          RZ
1C4E: 15          DCR  D
1C4F: 2b          DCX  H
1C50: c3 e5 11    JMP  $11E5
1C53: a7          ANA  A
1C54: ca 2d 0d    JZ   $0D2D
1C57: fe f8       CPI  $F8
1C59: d2 2d 0d    JNC  $0D2D
1C5C: fe b0       CPI  $B0
1C5E: d2 66 1c    JNC  $1C66
1C61: fe a0       CPI  $A0
1C63: d2 2d 0d    JNC  $0D2D
1C66: cd 50 10    CALL $1050
1C69: dc 2d 0d    CC   $0D2D
1C6C: cd 1c 10    CALL $101C
1C6F: cd a6 1c    CALL $1CA6
1C72: c3 3d 1c    JMP  $1C3D
; push_key_menu_position
1C75: 78          MOV  A,B
1C76: 26 03       MVI  H,$03
1C78: fe 05       CPI  $05
1C7A: da 8d 1c    JC   $1C8D
1C7D: d6 04       SUI  $04
1C7F: 26 05       MVI  H,$05
1C81: fe 05       CPI  $05
1C83: da 8d 1c    JC   $1C8D
1C86: d6 04       SUI  $04
1C88: 26 08       MVI  H,$08
1C8A: c3 9b 1c    JMP  $1C9B
1C8D: 2e 07       MVI  L,$07
1C8F: 5f          MOV  E,A
1C90: 1d          DCR  E
1C91: ca 51 12    JZ   $1251
1C94: 7d          MOV  A,L
1C95: c6 12       ADI  $12
1C97: 6f          MOV  L,A
1C98: c3 90 1c    JMP  $1C90
1C9B: 2e 07       MVI  L,$07
1C9D: 3d          DCR  A
1C9E: ca 51 12    JZ   $1251
1CA1: 24          INR  H
1CA2: 24          INR  H
1CA3: c3 9d 1c    JMP  $1C9D
1CA6: f5          PUSH PSW
1CA7: 3e 04       MVI  A,$04
1CA9: cd 89 13    CALL $1389
1CAC: f1          POP  PSW
1CAD: fe 80       CPI  $80
1CAF: d2 b7 1c    JNC  $1CB7
1CB2: fe 20       CPI  $20
1CB4: d2 94 14    JNC  $1494
1CB7: 3e 07       MVI  A,$07
1CB9: cd 89 13    CALL $1389
1CBC: 3e 20       MVI  A,$20
1CBE: c3 94 14    JMP  $1494
1CC1: 50 55 53 48 2d 4b 45 59 20 4d 45 4e 55 00 48 45 DB $50,$55,$53,$48,$2D,$4B,$45,$59,$20,$4D,$45,$4E,$55,$00,$48,$45
1CD1: 58 20 43 4f 44 45 20 3a 20 00 20 20 20 20 00    DB $58,$20,$43,$4F,$44,$45,$20,$3A,$20,$00,$20,$20,$20,$20,$00
1CE0: c5          PUSH B
1CE1: f5          PUSH PSW
1CE2: cd 58 1d    CALL $1D58
1CE5: da 21 1d    JC   $1D21
1CE8: d5          PUSH D
1CE9: e5          PUSH H
1CEA: eb          XCHG
1CEB: cd 71 1d    CALL $1D71
1CEE: 06 01       MVI  B,$01
1CF0: 78          MOV  A,B
1CF1: a7          ANA  A
1CF2: ca 09 1d    JZ   $1D09
1CF5: 1a          LDAX D
1CF6: a7          ANA  A
1CF7: ca 09 1d    JZ   $1D09
1CFA: fe f8       CPI  $F8
1CFC: d2 09 1d    JNC  $1D09
1CFF: fe b0       CPI  $B0
1D01: d2 0c 1d    JNC  $1D0C
1D04: fe a0       CPI  $A0
1D06: da 0c 1d    JC   $1D0C
1D09: 06 00       MVI  B,$00
1D0B: 97          SUB  A
1D0C: cd 50 10    CALL $1050
1D0F: da 1f 1d    JC   $1D1F
1D12: 13          INX  D
1D13: 23          INX  H
1D14: 0d          DCR  C
1D15: c2 f0 1c    JNZ  $1CF0
1D18: e1          POP  H
1D19: d1          POP  D
1D1A: f1          POP  PSW
1D1B: c1          POP  B
1D1C: 37          STC
1D1D: 3f          CMC
1D1E: c9          RET
1D1F: e1          POP  H
1D20: d1          POP  D
1D21: f1          POP  PSW
1D22: c1          POP  B
1D23: 37          STC
1D24: c9          RET
1D25: c5          PUSH B
1D26: f5          PUSH PSW
1D27: cd 58 1d    CALL $1D58
1D2A: da 21 1d    JC   $1D21
1D2D: d5          PUSH D
1D2E: e5          PUSH H
1D2F: eb          XCHG
1D30: 41          MOV  B,C
1D31: cd 71 1d    CALL $1D71
1D34: cd 1c 10    CALL $101C
1D37: 12          STAX D
1D38: 13          INX  D
1D39: 23          INX  H
1D3A: 0d          DCR  C
1D3B: c2 34 1d    JNZ  $1D34
1D3E: eb          XCHG
1D3F: 36 00       MVI  M,$00
1D41: 2b          DCX  H
1D42: 7e          MOV  A,M
1D43: fe 20       CPI  $20
1D45: c2 50 1d    JNZ  $1D50
1D48: 36 00       MVI  M,$00
1D4A: 0c          INR  C
1D4B: 79          MOV  A,C
1D4C: b8          CMP  B
1D4D: c2 41 1d    JNZ  $1D41
1D50: e1          POP  H
1D51: d1          POP  D
1D52: f1          POP  PSW
1D53: 78          MOV  A,B
1D54: c1          POP  B
1D55: 37          STC
1D56: 3f          CMC
1D57: c9          RET
; push_key_capacity
1D58: 0e 0c       MVI  C,$0C
1D5A: fe 08       CPI  $08
1D5C: da 6f 1d    JC   $1D6F
1D5F: 0e 20       MVI  C,$20
1D61: fe 0c       CPI  $0C
1D63: da 6f 1d    JC   $1D6F
1D66: 0e 30       MVI  C,$30
1D68: fe 10       CPI  $10
1D6A: da 6f 1d    JC   $1D6F
1D6D: 37          STC
1D6E: c9          RET
1D6F: a7          ANA  A
1D70: c9          RET
; push_key_nvram_address
1D71: d5          PUSH D
1D72: 21 84 1d    LXI  H,$1D84
1D75: f5          PUSH PSW
1D76: e6 0f       ANI  $0F
1D78: 87          ADD  A
1D79: 5f          MOV  E,A
1D7A: 16 00       MVI  D,$00
1D7C: 19          DAD  D
1D7D: 5e          MOV  E,M
1D7E: 23          INX  H
1D7F: 56          MOV  D,M
1D80: f1          POP  PSW
1D81: eb          XCHG
1D82: d1          POP  D
1D83: c9          RET
1D84: 60 00 6c 00 78 00 84 00 90 00 9c 00 a8 00 b4 00 DB $60,$00,$6C,$00,$78,$00,$84,$00,$90,$00,$9C,$00,$A8,$00,$B4,$00
1D94: c0 00 e0 00 00 01 20 01 40 01 70 01 a0 01 d0 01 DB $C0,$00,$E0,$00,$00,$01,$20,$01,$40,$01,$70,$01,$A0,$01,$D0,$01
1DA4: d5          PUSH D
1DA5: c5          PUSH B
1DA6: f5          PUSH PSW
1DA7: 3a 16 5e    LDA  $5E16
1DAA: fe 50       CPI  $50
1DAC: d2 25 1e    JNC  $1E25
1DAF: 0e 03       MVI  C,$03
1DB1: cd 7d 20    CALL $207D
1DB4: 3a f9 5e    LDA  $5EF9
1DB7: 47          MOV  B,A
1DB8: 3a f6 5d    LDA  $5DF6
1DBB: 4f          MOV  C,A
1DBC: c5          PUSH B
1DBD: 3e 02       MVI  A,$02
1DBF: 32 f9 5e    STA  $5EF9
1DC2: 3a 16 5e    LDA  $5E16
1DC5: e6 01       ANI  $01
1DC7: c2 d3 1d    JNZ  $1DD3
1DCA: 97          SUB  A
1DCB: cd 06 1f    CALL $1F06
1DCE: 3e 20       MVI  A,$20
1DD0: cd 7a 1f    CALL $1F7A
1DD3: 78          MOV  A,B
1DD4: fe 02       CPI  $02
1DD6: 3e 20       MVI  A,$20
1DD8: c2 dc 1d    JNZ  $1DDC
1DDB: 79          MOV  A,C
1DDC: f6 20       ORI  $20
1DDE: cd 06 1f    CALL $1F06
1DE1: 32 f6 5d    STA  $5DF6
1DE4: 0e 01       MVI  C,$01
1DE6: cd 2b 1e    CALL $1E2B
1DE9: c1          POP  B
1DEA: f5          PUSH PSW
1DEB: 79          MOV  A,C
1DEC: 32 f6 5d    STA  $5DF6
1DEF: 78          MOV  A,B
1DF0: 32 f9 5e    STA  $5EF9
1DF3: cd 91 20    CALL $2091
1DF6: f1          POP  PSW
1DF7: 57          MOV  D,A
1DF8: d2 1e 1e    JNC  $1E1E
1DFB: 56          MOV  D,M
1DFC: c3 25 1e    JMP  $1E25
1DFF: eb          XCHG
1E00: e5          PUSH H
1E01: 2a 16 5e    LHLD $5E16
1E04: e3          XTHL
1E05: 22 16 5e    SHLD $5E16
1E08: eb          XCHG
1E09: cd 12 1e    CALL $1E12
1E0C: e3          XTHL
1E0D: 22 16 5e    SHLD $5E16
1E10: e1          POP  H
1E11: c9          RET
1E12: d5          PUSH D
1E13: c5          PUSH B
1E14: f5          PUSH PSW
1E15: 0e 00       MVI  C,$00
1E17: cd 2b 1e    CALL $1E2B
1E1A: 57          MOV  D,A
1E1B: da 25 1e    JC   $1E25
1E1E: f1          POP  PSW
1E1F: 7a          MOV  A,D
1E20: c1          POP  B
1E21: d1          POP  D
1E22: 37          STC
1E23: 3f          CMC
1E24: c9          RET
1E25: f1          POP  PSW
1E26: 7a          MOV  A,D
1E27: c1          POP  B
1E28: d1          POP  D
1E29: 37          STC
1E2A: c9          RET
1E2B: cd 5f 1e    CALL $1E5F
1E2E: d8          RC
1E2F: fe 20       CPI  $20
1E31: 3f          CMC
1E32: d0          RNC
1E33: e5          PUSH H
1E34: d6 80       SUI  $80
1E36: 5f          MOV  E,A
1E37: 2a fc 5d    LHLD $5DFC
1E3A: 7c          MOV  A,H
1E3B: b5          ORA  L
1E3C: ca 4f 1e    JZ   $1E4F
1E3F: 7b          MOV  A,E
1E40: 83          ADD  E
1E41: 5f          MOV  E,A
1E42: 16 00       MVI  D,$00
1E44: 19          DAD  D
1E45: 5e          MOV  E,M
1E46: 23          INX  H
1E47: 56          MOV  D,M
1E48: eb          XCHG
1E49: cd 5f 1e    CALL $1E5F
1E4C: e1          POP  H
1E4D: d8          RC
1E4E: e5          PUSH H
1E4F: e1          POP  H
1E50: 7e          MOV  A,M
1E51: fe 80       CPI  $80
1E53: da 2b 1e    JC   $1E2B
1E56: 3e 20       MVI  A,$20
1E58: cd 6f 1e    CALL $1E6F
1E5B: d8          RC
1E5C: c3 2b 1e    JMP  $1E2B
1E5F: 7e          MOV  A,M
1E60: 23          INX  H
1E61: fe 20       CPI  $20
1E63: 3f          CMC
1E64: d0          RNC
1E65: fe 80       CPI  $80
1E67: d0          RNC
1E68: cd 6f 1e    CALL $1E6F
1E6B: d2 5f 1e    JNC  $1E5F
1E6E: c9          RET
1E6F: cd 7a 1f    CALL $1F7A
1E72: d8          RC
1E73: 79          MOV  A,C
1E74: a7          ANA  A
1E75: c8          RZ
1E76: 3e 20       MVI  A,$20
1E78: cd 94 14    CALL $1494
1E7B: cd a7 11    CALL $11A7
1E7E: dc 7f 11    CC   $117F
1E81: c9          RET
; validate_screen_coordinates
1E82: f5          PUSH PSW
1E83: 7d          MOV  A,L
1E84: a7          ANA  A
1E85: ca 97 1e    JZ   $1E97
1E88: fe 51       CPI  $51
1E8A: d2 97 1e    JNC  $1E97
1E8D: 7c          MOV  A,H
1E8E: a7          ANA  A
1E8F: ca 97 1e    JZ   $1E97
1E92: fe 1a       CPI  $1A
1E94: da e2 20    JC   $20E2
1E97: f1          POP  PSW
1E98: 37          STC
1E99: c9          RET
1E9A: f5          PUSH PSW
1E9B: e5          PUSH H
1E9C: d5          PUSH D
1E9D: cd 82 1e    CALL $1E82
1EA0: d2 af 1e    JNC  $1EAF
1EA3: 7c          MOV  A,H
1EA4: fe 1a       CPI  $1A
1EA6: c2 e7 20    JNZ  $20E7
1EA9: 7d          MOV  A,L
1EAA: fe 01       CPI  $01
1EAC: c2 e7 20    JNZ  $20E7
1EAF: eb          XCHG
1EB0: 2a 16 5e    LHLD $5E16
1EB3: eb          XCHG
1EB4: cd ca 1f    CALL $1FCA
1EB7: d2 e7 20    JNC  $20E7
1EBA: c3 e0 20    JMP  $20E0
1EBD: f5          PUSH PSW
1EBE: 7c          MOV  A,H
1EBF: fe 1a       CPI  $1A
1EC1: c2 cb 1e    JNZ  $1ECB
1EC4: 21 01 01    LXI  H,$0101
1EC7: c3 cb 1e    JMP  $1ECB
; cursor_to_video_address
1ECA: f5          PUSH PSW
1ECB: 2d          DCR  L
1ECC: 3a 1a 5e    LDA  $5E1A
1ECF: 84          ADD  H
1ED0: fe 19       CPI  $19
1ED2: da d7 1e    JC   $1ED7
1ED5: d6 19       SUI  $19
1ED7: c6 60       ADI  $60
1ED9: 67          MOV  H,A
1EDA: f1          POP  PSW
1EDB: c9          RET
; video_address_next
1EDC: 2c          INR  L
1EDD: c3 e9 1e    JMP  $1EE9
1EE0: 2d c3 e9 1e                                     DB $2D,$C3,$E9,$1E
1EE4: 3a 2d 5e    LDA  $5E2D
1EE7: 85          ADD  L
1EE8: 6f          MOV  L,A
1EE9: 7d          MOV  A,L
1EEA: fe 50       CPI  $50
1EEC: ca fc 1e    JZ   $1EFC
1EEF: fe ff       CPI  $FF
1EF1: c0          RNZ
1EF2: 2e 4f       MVI  L,$4F
1EF4: 25          DCR  H
1EF5: 7c          MOV  A,H
1EF6: fe 5f       CPI  $5F
1EF8: c0          RNZ
1EF9: 26 78       MVI  H,$78
1EFB: c9          RET
1EFC: 2e 00       MVI  L,$00
1EFE: 24          INR  H
1EFF: 7c          MOV  A,H
1F00: fe 79       CPI  $79
1F02: c0          RNZ
1F03: 26 60       MVI  H,$60
1F05: c9          RET
1F06: c5          PUSH B
1F07: e6 3f       ANI  $3F
1F09: 47          MOV  B,A
1F0A: 3a 02 5e    LDA  $5E02
1F0D: b0          ORA  B
1F0E: d3 70       OUT  $70
1F10: c1          POP  B
1F11: c9          RET
1F12: f5          PUSH PSW
1F13: 0b          DCX  B
1F14: 97          SUB  A
1F15: b0          ORA  B
1F16: b1          ORA  C
1F17: c2 13 1f    JNZ  $1F13
1F1A: f1          POP  PSW
1F1B: c9          RET
1F1C: fb          EI
1F1D: f5          PUSH PSW
1F1E: 97          SUB  A
1F1F: 32 f5 5d    STA  $5DF5
1F22: 3a f5 5d    LDA  $5DF5
1F25: a7          ANA  A
1F26: ca 22 1f    JZ   $1F22
1F29: f1          POP  PSW
1F2A: c9          RET
; zero_memory_range
1F2B: 36 00       MVI  M,$00
1F2D: 23          INX  H
1F2E: cd ca 1f    CALL $1FCA
1F31: c2 2b 1f    JNZ  $1F2B
1F34: c9          RET
; display_decimal_2
1F35: f5          PUSH PSW
1F36: e5          PUSH H
1F37: fe 64       CPI  $64
1F39: d2 e8 20    JNC  $20E8
1F3C: 26 30       MVI  H,$30
1F3E: d6 0a       SUI  $0A
1F40: da 47 1f    JC   $1F47
1F43: 24          INR  H
1F44: c3 3e 1f    JMP  $1F3E
1F47: c6 3a       ADI  $3A
1F49: 6f          MOV  L,A
1F4A: 7c          MOV  A,H
1F4B: cd 7a 1f    CALL $1F7A
1F4E: da e8 20    JC   $20E8
1F51: 7d          MOV  A,L
1F52: cd 7a 1f    CALL $1F7A
1F55: da e8 20    JC   $20E8
1F58: c3 e1 20    JMP  $20E1
; display_hex_byte
1F5B: f5          PUSH PSW
1F5C: e5          PUSH H
1F5D: 67          MOV  H,A
1F5E: 07          RLC
1F5F: 07          RLC
1F60: 07          RLC
1F61: 07          RLC
1F62: cd 72 1f    CALL $1F72
1F65: da e8 20    JC   $20E8
1F68: 7c          MOV  A,H
1F69: cd 72 1f    CALL $1F72
1F6C: da e8 20    JC   $20E8
1F6F: c3 e1 20    JMP  $20E1
1F72: e6 0f       ANI  $0F
1F74: c6 90       ADI  $90
1F76: 27          DAA
1F77: ce 40       ACI  $40
1F79: 27          DAA
1F7A: cd 94 14    CALL $1494
1F7D: c3 b7 11    JMP  $11B7
; input_hex_byte
1F80: cd 9c 1f    CALL $1F9C
1F83: d8          RC
1F84: 17          RAL
1F85: 17          RAL
1F86: 17          RAL
1F87: 17          RAL
1F88: e6 f0       ANI  $F0
1F8A: c5          PUSH B
1F8B: 47          MOV  B,A
1F8C: cd 9c 1f    CALL $1F9C
1F8F: da 99 1f    JC   $1F99
1F92: e6 0f       ANI  $0F
1F94: b0          ORA  B
1F95: c1          POP  B
1F96: 37          STC
1F97: 3f          CMC
1F98: c9          RET
1F99: c1          POP  B
1F9A: 37          STC
1F9B: c9          RET
1F9C: cd b1 1f    CALL $1FB1
1F9F: d6 30       SUI  $30
1FA1: d8          RC
1FA2: fe 0a       CPI  $0A
1FA4: da ae 1f    JC   $1FAE
1FA7: d6 07       SUI  $07
1FA9: fe 10       CPI  $10
1FAB: d2 9a 1f    JNC  $1F9A
1FAE: 37          STC
1FAF: 3f          CMC
1FB0: c9          RET
1FB1: cd d0 0c    CALL $0CD0
1FB4: da b1 1f    JC   $1FB1
1FB7: fe 60       CPI  $60
1FB9: d8          RC
1FBA: fe e0       CPI  $E0
1FBC: da c7 1f    JC   $1FC7
1FBF: fe ea       CPI  $EA
1FC1: d2 c7 1f    JNC  $1FC7
1FC4: d6 b0       SUI  $B0
1FC6: c9          RET
1FC7: e6 5f       ANI  $5F
1FC9: c9          RET
; compare_de_hl
1FCA: 7a          MOV  A,D
1FCB: bc          CMP  H
1FCC: c0          RNZ
1FCD: 7b          MOV  A,E
1FCE: bd          CMP  L
1FCF: c9          RET
; compare_bc_hl
1FD0: 78          MOV  A,B
1FD1: bc          CMP  H
1FD2: c0          RNZ
1FD3: 79          MOV  A,C
1FD4: bd          CMP  L
1FD5: c9          RET
; compare_bc_de
1FD6: 78          MOV  A,B
1FD7: ba          CMP  D
1FD8: c0          RNZ
1FD9: 79          MOV  A,C
1FDA: bb          CMP  E
1FDB: c9          RET
; copy_character_and_attribute
1FDC: 3a f8 5e    LDA  $5EF8
1FDF: a7          ANA  A
1FE0: ca f7 1f    JZ   $1FF7
1FE3: 3a 25 5e    LDA  $5E25
1FE6: fe 02       CPI  $02
1FE8: d2 f7 1f    JNC  $1FF7
1FEB: 1a          LDAX D
1FEC: 20          RIM
1FED: e6 80       ANI  $80
1FEF: c2 eb 1f    JNZ  $1FEB
1FF2: db 70       IN   $70
1FF4: 32 fa 5e    STA  $5EFA
1FF7: 4e          MOV  C,M
1FF8: 20          RIM
1FF9: e6 80       ANI  $80
1FFB: c2 f7 1f    JNZ  $1FF7
1FFE: db 70       IN   $70
2000: f5          PUSH PSW
2001: 47          MOV  B,A
2002: 3a 25 5e    LDA  $5E25
2005: fe 02       CPI  $02
2007: d2 28 20    JNC  $2028
200A: a7          ANA  A
200B: ca 1b 20    JZ   $201B
200E: 78          MOV  A,B
200F: e6 c0       ANI  $C0
2011: 47          MOV  B,A
2012: 3a fa 5e    LDA  $5EFA
2015: e6 3f       ANI  $3F
2017: b0          ORA  B
2018: c3 29 20    JMP  $2029
201B: 78          MOV  A,B
201C: e6 3f       ANI  $3F
201E: 47          MOV  B,A
201F: 3a fa 5e    LDA  $5EFA
2022: e6 c0       ANI  $C0
2024: b0          ORA  B
2025: c3 29 20    JMP  $2029
2028: 78          MOV  A,B
2029: d3 70       OUT  $70
202B: 79          MOV  A,C
202C: 12          STAX D
202D: 20          RIM
202E: e6 80       ANI  $80
2030: c2 2b 20    JNZ  $202B
2033: f1          POP  PSW
2034: c9          RET
2035: c5          PUSH B
2036: 47          MOV  B,A
2037: 3a 25 5e    LDA  $5E25
203A: fe 02       CPI  $02
203C: 0e 00       MVI  C,$00
203E: d2 4e 20    JNC  $204E
2041: a7          ANA  A
2042: 48          MOV  C,B
2043: c2 4e 20    JNZ  $204E
2046: 78          MOV  A,B
2047: e6 c0       ANI  $C0
2049: d3 70       OUT  $70
204B: c3 52 20    JMP  $2052
204E: 79          MOV  A,C
204F: cd 06 1f    CALL $1F06
2052: 36 00       MVI  M,$00
2054: 20          RIM
2055: e6 80       ANI  $80
2057: c2 52 20    JNZ  $2052
205A: c1          POP  B
205B: c9          RET
205C: c5          PUSH B
205D: 32 25 5e    STA  $5E25
2060: 47          MOV  B,A
2061: 3a f8 5e    LDA  $5EF8
2064: a7          ANA  A
2065: 78          MOV  A,B
2066: ca 6f 20    JZ   $206F
2069: a7          ANA  A
206A: ca 6f 20    JZ   $206F
206D: 3e 02       MVI  A,$02
206F: cd 74 20    CALL $2074
2072: c1          POP  B
2073: c9          RET
2074: fe 03       CPI  $03
2076: da 7b 20    JC   $207B
2079: 3e 02       MVI  A,$02
207B: 3c          INR  A
207C: 4f          MOV  C,A
207D: f3          DI
207E: 3a 0e 5e    LDA  $5E0E
2081: e6 03       ANI  $03
2083: 32 27 5e    STA  $5E27
2086: 3a 0e 5e    LDA  $5E0E
2089: e6 fc       ANI  $FC
208B: b1          ORA  C
208C: cd d0 20    CALL $20D0
208F: fb          EI
2090: c9          RET
2091: c5          PUSH B
2092: 3a f6 5d    LDA  $5DF6
2095: d3 70       OUT  $70
2097: f3          DI
2098: 3a 27 5e    LDA  $5E27
209B: 47          MOV  B,A
209C: 3a 0e 5e    LDA  $5E0E
209F: e6 fc       ANI  $FC
20A1: b0          ORA  B
20A2: cd d0 20    CALL $20D0
20A5: fb          EI
20A6: c1          POP  B
20A7: c9          RET
20A8: f3          DI
20A9: 3a 0e 5e    LDA  $5E0E
20AC: e6 df       ANI  $DF
20AE: f6 08       ORI  $08
20B0: cd d0 20    CALL $20D0
20B3: 3e 01       MVI  A,$01
20B5: 32 0f 5e    STA  $5E0F
20B8: fb          EI
20B9: c9          RET
20BA: f3          DI
20BB: 97          SUB  A
20BC: 32 0f 5e    STA  $5E0F
20BF: 3a 26 5e    LDA  $5E26
20C2: a7          ANA  A
20C3: c2 ce 20    JNZ  $20CE
20C6: 3a 0e 5e    LDA  $5E0E
20C9: f6 20       ORI  $20
20CB: cd d0 20    CALL $20D0
20CE: fb          EI
20CF: c9          RET
; write_control_2
20D0: 32 0e 5e    STA  $5E0E
20D3: d3 60       OUT  $60
20D5: c9          RET
20D6: e1          POP  H
20D7: c1          POP  B
20D8: f1          POP  PSW
20D9: c9          RET
20DA: c1          POP  B
20DB: d1          POP  D
20DC: e1          POP  H
20DD: f1          POP  PSW
20DE: c9          RET
20DF: c1          POP  B
20E0: d1          POP  D
20E1: e1          POP  H
20E2: f1          POP  PSW
20E3: 37          STC
20E4: 3f          CMC
20E5: c9          RET
20E6: c1          POP  B
20E7: d1          POP  D
20E8: e1          POP  H
20E9: f1          POP  PSW
20EA: 37          STC
20EB: c9          RET
20EC: 00 00 00 00 00 00 00 00 00 40 80 a0 c0 e0 58 68 DB $00,$00,$00,$00,$00,$00,$00,$00,$00,$40,$80,$A0,$C0,$E0,$58,$68
20FC: 88 82 36 01 80 80                               DB $88,$82,$36,$01,$80,$80
; application_entry
2102: da 02 21    JC   $2102
2105: 21 03 52    LXI  H,$5203
2108: 22 fc 5d    SHLD $5DFC
210B: 21 71 47    LXI  H,$4771
210E: 22 20 5c    SHLD $5C20
2111: 21 eb 47    LXI  H,$47EB
2114: 22 1e 5c    SHLD $5C1E
2117: 21 24 48    LXI  H,$4824
211A: 22 12 5c    SHLD $5C12
211D: 21 53 48    LXI  H,$4853
2120: 22 26 5c    SHLD $5C26
2123: 21 5a 48    LXI  H,$485A
2126: 22 2a 5c    SHLD $5C2A
2129: 21 61 48    LXI  H,$4861
212C: 22 2c 5c    SHLD $5C2C
212F: 21 32 48    LXI  H,$4832
2132: 22 22 5c    SHLD $5C22
2135: 21 3c 41    LXI  H,$413C
2138: 22 08 5e    SHLD $5E08
213B: 3e 00       MVI  A,$00
213D: 32 af 59    STA  $59AF
2140: 3e 20       MVI  A,$20
2142: cd 19 38    CALL $3819
2145: 21 99 4d    LXI  H,$4D99
2148: 22 fa 5d    SHLD $5DFA
214B: cd 5a 01    CALL $015A
214E: 3a 35 5f    LDA  $5F35
2151: a7          ANA  A
2152: 3e 23       MVI  A,$23
2154: c4 19 38    CNZ  $3819
2157: 3a af 59    LDA  $59AF
215A: f5          PUSH PSW
215B: 21 00 58    LXI  H,$5800
215E: 11 00 5b    LXI  D,$5B00
2161: cd 29 38    CALL $3829
2164: 97          SUB  A
2165: 32 39 5f    STA  $5F39
2168: 21 8c 00    LXI  H,$008C
216B: 22 87 58    SHLD $5887
216E: 21 00 a0    LXI  H,$A000
2171: 11 00 ff    LXI  D,$FF00
2174: cd 29 38    CALL $3829
2177: f1          POP  PSW
2178: 32 af 59    STA  $59AF
217B: 31 ff 5f    LXI  SP,$5FFF
217E: 3a 25 5f    LDA  $5F25
2181: c6 18       ADI  $18
2183: 32 60 58    STA  $5860
2186: 3a 03 5f    LDA  $5F03
2189: fe 04       CPI  $04
218B: da 91 21    JC   $2191
218E: 3c          INR  A
218F: e6 03       ANI  $03
2191: 06 00       MVI  B,$00
2193: cd 81 01    CALL $0181
2196: 3e 01       MVI  A,$01
2198: 32 fe 5d    STA  $5DFE
219B: 21 55 00    LXI  H,$0055
219E: cd 21 01    CALL $0121
21A1: fe 48       CPI  $48
21A3: ca 13 22    JZ   $2213
21A6: 21 57 00    LXI  H,$0057
21A9: cd 21 01    CALL $0121
21AC: fe 48       CPI  $48
21AE: ca f7 21    JZ   $21F7
21B1: 21 5b 00    LXI  H,$005B
21B4: cd 21 01    CALL $0121
21B7: fe 48       CPI  $48
21B9: ca d9 21    JZ   $21D9
21BC: 21 fe 5d    LXI  H,$5DFE
21BF: 36 00       MVI  M,$00
21C1: fe 42       CPI  $42
21C3: ca d9 21    JZ   $21D9
21C6: 21 cf 21    LXI  H,$21CF
21C9: cd a2 01    CALL $01A2
21CC: c3 cc 21    JMP  $21CC
21CF: 87 20 6e 6f 2e 3a 20 32 30 00                   DB $87,$20,$6E,$6F,$2E,$3A,$20,$32,$30,$00
21D9: 21 fc ff    LXI  H,$FFFC
21DC: 22 61 58    SHLD $5861
21DF: 21 00 f0    LXI  H,$F000
21E2: 22 ff 5d    SHLD $5DFF
21E5: 21 00 f8    LXI  H,$F800
21E8: 11 00 00    LXI  D,$0000
21EB: 3e 01       MVI  A,$01
21ED: 32 a5 58    STA  $58A5
21F0: 3a 60 58    LDA  $5860
21F3: 3c          INR  A
21F4: c3 44 22    JMP  $2244
21F7: 21 fc df    LXI  H,$DFFC
21FA: 22 61 58    SHLD $5861
21FD: 21 00 f8    LXI  H,$F800
2200: 22 ff 5d    SHLD $5DFF
2203: 3e 04       MVI  A,$04
2205: 32 a5 58    STA  $58A5
2208: 11 00 a0    LXI  D,$A000
220B: 21 00 d0    LXI  H,$D000
220E: 3e 65       MVI  A,$65
2210: c3 44 22    JMP  $2244
2213: 21 fc ff    LXI  H,$FFFC
2216: 22 61 58    SHLD $5861
2219: 3a 01 5f    LDA  $5F01
221C: a7          ANA  A
221D: c2 31 22    JNZ  $2231
2220: 97          SUB  A
2221: 32 fe 5d    STA  $5DFE
2224: 3e 08       MVI  A,$08
2226: 32 a5 58    STA  $58A5
2229: 11 00 80    LXI  D,$8000
222C: 3e c9       MVI  A,$C9
222E: c3 41 22    JMP  $2241
2231: 21 00 80    LXI  H,$8000
2234: 22 ff 5d    SHLD $5DFF
2237: 3e 07       MVI  A,$07
2239: 32 a5 58    STA  $58A5
223C: 11 00 88    LXI  D,$8800
223F: 3e b0       MVI  A,$B0
2241: 21 00 e0    LXI  H,$E000
2244: 32 aa 58    STA  $58AA
2247: 22 ad 58    SHLD $58AD
224A: eb          XCHG
224B: 22 ab 58    SHLD $58AB
224E: 3e 01       MVI  A,$01
2250: 32 a9 58    STA  $58A9
2253: 21 01 5b    LXI  H,$5B01
2256: 3a aa 58    LDA  $58AA
2259: 75          MOV  M,L
225A: 2c          INR  L
225B: bd          CMP  L
225C: c2 59 22    JNZ  $2259
225F: 75          MOV  M,L
2260: cd be 43    CALL $43BE
2263: cd 22 54    CALL $5422
2266: 3e 01       MVI  A,$01
2268: 32 a6 58    STA  $58A6
226B: cd 09 01    CALL $0109
226E: 3a af 59    LDA  $59AF
2271: a7          ANA  A
2272: f5          PUSH PSW
2273: cc 19 56    CZ   $5619
2276: f1          POP  PSW
2277: f5          PUSH PSW
2278: c4 34 57    CNZ  $5734
227B: f1          POP  PSW
227C: cc 28 56    CZ   $5628
227F: 3e 01       MVI  A,$01
2281: 32 af 59    STA  $59AF
2284: cd fd 44    CALL $44FD
2287: cd ea 37    CALL $37EA
228A: cd f0 35    CALL $35F0
228D: 21 d9 22    LXI  H,$22D9
2290: 22 57 58    SHLD $5857
2293: 21 f3 58    LXI  H,$58F3
2296: 36 00       MVI  M,$00
2298: 22 bf 58    SHLD $58BF
229B: c3 9e 22    JMP  $229E
; application_main_loop
229E: cd d5 22    CALL $22D5
22A1: 3a 2a 5f    LDA  $5F2A
22A4: a7          ANA  A
22A5: c2 9e 22    JNZ  $229E
22A8: cd 21 39    CALL $3921
22AB: eb          XCHG
22AC: 2a af 58    LHLD $58AF
22AF: cd c9 01    CALL $01C9
22B2: da be 22    JC   $22BE
22B5: 2a b1 58    LHLD $58B1
22B8: cd c9 01    CALL $01C9
22BB: da cc 22    JC   $22CC
22BE: 3a b3 58    LDA  $58B3
22C1: e6 01       ANI  $01
22C3: c4 bb 3f    CNZ  $3FBB
22C6: cd b3 38    CALL $38B3
22C9: cd 6d 37    CALL $376D
22CC: 2a 16 5e    LHLD $5E16
22CF: 22 a7 58    SHLD $58A7
22D2: c3 9e 22    JMP  $229E
22D5: 2a 57 58    LHLD $5857
22D8: e9          PCHL
; application_event_poll
22D9: 21 52 58    LXI  H,$5852
22DC: 35          DCR  M
22DD: ca ec 22    JZ   $22EC
22E0: cd be 00    CALL $00BE
22E3: da ec 22    JC   $22EC
22E6: 06 01       MVI  B,$01
22E8: 2a 55 58    LHLD $5855
22EB: e9          PCHL
22EC: cd 87 44    CALL $4487
22EF: cd 0a 23    CALL $230A
22F2: da 5a 23    JC   $235A
22F5: 21 52 58    LXI  H,$5852
22F8: 36 02       MVI  M,$02
22FA: fe f6       CPI  $F6
22FC: ca 7f 23    JZ   $237F
22FF: fe f3       CPI  $F3
2301: ca d2 23    JZ   $23D2
2304: 06 00       MVI  B,$00
2306: 2a 53 58    LHLD $5853
2309: e9          PCHL
230A: e5          PUSH H
230B: 2a bf 58    LHLD $58BF
230E: 7e          MOV  A,M
230F: a7          ANA  A
2310: ca 1a 23    JZ   $231A
2313: 23          INX  H
2314: 22 bf 58    SHLD $58BF
2317: c3 30 23    JMP  $2330
231A: cd bb 00    CALL $00BB
231D: da 45 23    JC   $2345
2320: fe a0       CPI  $A0
2322: da 30 23    JC   $2330
2325: fe b0       CPI  $B0
2327: d2 30 23    JNC  $2330
232A: cd 48 23    CALL $2348
232D: c3 0b 23    JMP  $230B
2330: fe e0       CPI  $E0
2332: da 3c 23    JC   $233C
2335: fe ea       CPI  $EA
2337: d2 3c 23    JNC  $233C
233A: d6 b0       SUI  $B0
233C: 21 53 23    LXI  H,$2353
233F: cd 33 38    CALL $3833
2342: e1          POP  H
2343: a7          ANA  A
2344: c9          RET
2345: e1          POP  H
2346: 37          STC
2347: c9          RET
2348: e6 0f       ANI  $0F
234A: 21 f3 58    LXI  H,$58F3
234D: 22 bf 58    SHLD $58BF
2350: c3 69 01    JMP  $0169
2353: ea 2d eb 2e ec 20 ff                            DB $EA,$2D,$EB,$2E,$EC,$20,$FF
235A: 3a ad 59    LDA  $59AD
235D: a7          ANA  A
235E: ca 6f 23    JZ   $236F
2361: 2a 22 5e    LHLD $5E22
2364: 7c          MOV  A,H
2365: 2d          DCR  L
2366: b5          ORA  L
2367: c8          RZ
2368: cd 07 57    CALL $5707
236B: 97          SUB  A
236C: 32 ad 59    STA  $59AD
236F: 2a 22 5e    LHLD $5E22
2372: 7c          MOV  A,H
2373: 2d          DCR  L
2374: b5          ORA  L
2375: c0          RNZ
2376: cd 0d 57    CALL $570D
2379: 3e 01       MVI  A,$01
237B: 32 ad 59    STA  $59AD
237E: c9          RET
237F: 3e 01       MVI  A,$01
2381: 32 93 58    STA  $5893
2384: 21 28 59    LXI  H,$5928
2387: 22 26 59    SHLD $5926
238A: cd bb 00    CALL $00BB
238D: da 8a 23    JC   $238A
2390: fe f7       CPI  $F7
2392: ca a0 23    JZ   $23A0
2395: 2a 26 59    LHLD $5926
2398: 77          MOV  M,A
2399: 23          INX  H
239A: 22 26 59    SHLD $5926
239D: c3 8a 23    JMP  $238A
23A0: 97          SUB  A
23A1: 32 93 58    STA  $5893
23A4: cd 1a 24    CALL $241A
23A7: 2a 26 59    LHLD $5926
23AA: eb          XCHG
23AB: 21 28 59    LXI  H,$5928
23AE: 7e          MOV  A,M
23AF: fe e0       CPI  $E0
23B1: d2 c2 23    JNC  $23C2
23B4: cd c9 01    CALL $01C9
23B7: ca ce 23    JZ   $23CE
23BA: 7e          MOV  A,M
23BB: 23          INX  H
23BC: cd 2b 24    CALL $242B
23BF: c3 b4 23    JMP  $23B4
23C2: f5          PUSH PSW
23C3: 3e 39       MVI  A,$39
23C5: cd a8 40    CALL $40A8
23C8: f1          POP  PSW
23C9: d6 b0       SUI  $B0
23CB: cd a8 40    CALL $40A8
23CE: cd 25 24    CALL $2425
23D1: c9          RET
23D2: cd 1a 24    CALL $241A
23D5: 3e 30       MVI  A,$30
23D7: cd a8 40    CALL $40A8
23DA: cd 25 24    CALL $2425
23DD: c9          RET
23DE: 3e 27       MVI  A,$27
23E0: cd 19 38    CALL $3819
23E3: 21 80 01    LXI  H,$0180
23E6: 06 30       MVI  B,$30
23E8: 2b          DCX  H
23E9: 7d          MOV  A,L
23EA: b4          ORA  H
23EB: ca ff 23    JZ   $23FF
23EE: cd bb 00    CALL $00BB
23F1: da e6 23    JC   $23E6
23F4: fe ef       CPI  $EF
23F6: ca ff 23    JZ   $23FF
23F9: 04          INR  B
23FA: fe f5       CPI  $F5
23FC: c2 e6 23    JNZ  $23E6
23FF: cd 1a 24    CALL $241A
2402: 3e 32       MVI  A,$32
2404: cd a8 40    CALL $40A8
2407: 78          MOV  A,B
2408: cd a8 40    CALL $40A8
240B: cd 25 24    CALL $2425
240E: c9          RET
240F: 3e 2b       MVI  A,$2B
2411: cd 19 38    CALL $3819
2414: c9          RET
2415: 3e 2c       MVI  A,$2C
2417: c3 11 24    JMP  $2411
241A: 3e 90       MVI  A,$90
241C: cd 76 40    CALL $4076
241F: 3e 4d       MVI  A,$4D
2421: cd a8 40    CALL $40A8
2424: c9          RET
2425: 3e 9c       MVI  A,$9C
2427: cd 76 40    CALL $4076
242A: c9          RET
242B: f5          PUSH PSW
242C: 1f          RAR
242D: 1f          RAR
242E: 1f          RAR
242F: 1f          RAR
2430: cd 34 24    CALL $2434
2433: f1          POP  PSW
2434: e6 0f       ANI  $0F
2436: c6 90       ADI  $90
2438: 27          DAA
2439: ce 40       ACI  $40
243B: 27          DAA
243C: cd a8 40    CALL $40A8
243F: c9          RET
; keyboard_character_dispatch
2440: fe 20       CPI  $20
2442: da a8 40    JC   $40A8
2445: cd 78 25    CALL $2578
2448: 21 65 58    LXI  H,$5865
244B: 36 ff       MVI  M,$FF
244D: 21 bf 25    LXI  H,$25BF
2450: fe 20       CPI  $20
2452: da 8e 25    JC   $258E
2455: fe 7f       CPI  $7F
2457: c8          RZ
2458: da c0 26    JC   $26C0
245B: 21 aa 59    LXI  H,$59AA
245E: 36 00       MVI  M,$00
2460: 21 ff 25    LXI  H,$25FF
2463: fe a0       CPI  $A0
2465: da 8e 25    JC   $258E
2468: fe ed       CPI  $ED
246A: ca 34 29    JZ   $2934
246D: 67          MOV  H,A
246E: fe c5       CPI  $C5
2470: ca 78 24    JZ   $2478
2473: fe c6       CPI  $C6
2475: c2 87 24    JNZ  $2487
2478: 3a 38 5f    LDA  $5F38
247B: a7          ANA  A
247C: c2 87 24    JNZ  $2487
247F: 3a 32 5f    LDA  $5F32
2482: a7          ANA  A
2483: 7c          MOV  A,H
2484: c2 f3 24    JNZ  $24F3
2487: 7c          MOV  A,H
2488: fe d0       CPI  $D0
248A: d2 95 24    JNC  $2495
248D: 21 3f 26    LXI  H,$263F
2490: d6 b0       SUI  $B0
2492: c3 8e 25    JMP  $258E
2495: fe f0       CPI  $F0
2497: d2 a2 24    JNC  $24A2
249A: 21 7f 26    LXI  H,$267F
249D: d6 d0       SUI  $D0
249F: c3 8e 25    JMP  $258E
24A2: fe f3       CPI  $F3
24A4: d0          RNC
24A5: d6 f0       SUI  $F0
24A7: 32 64 58    STA  $5864
24AA: cd aa 35    CALL $35AA
24AD: cd 20 38    CALL $3820
24B0: fe 4c       CPI  $4C
24B2: ca ad 2f    JZ   $2FAD
24B5: fe 50       CPI  $50
24B7: ca 36 2f    JZ   $2F36
24BA: fe 46       CPI  $46
24BC: ca 62 2f    JZ   $2F62
24BF: fe 41       CPI  $41
24C1: ca 27 2f    JZ   $2F27
24C4: fe 42       CPI  $42
24C6: c0          RNZ
24C7: 3a 64 58    LDA  $5864
24CA: c6 0a       ADI  $0A
24CC: 32 64 58    STA  $5864
24CF: c3 36 2f    JMP  $2F36
24D2: cd 78 25    CALL $2578
24D5: fe 80       CPI  $80
24D7: da a8 40    JC   $40A8
24DA: fe ed       CPI  $ED
24DC: ca 4e 25    JZ   $254E
24DF: fe 93       CPI  $93
24E1: ca c7 2a    JZ   $2AC7
24E4: fe 9d       CPI  $9D
24E6: ca 53 2b    JZ   $2B53
24E9: fe a0       CPI  $A0
24EB: da 76 40    JC   $4076
24EE: fe f0       CPI  $F0
24F0: d2 06 25    JNC  $2506
24F3: 47          MOV  B,A
24F4: 3a ac 59    LDA  $59AC
24F7: a7          ANA  A
24F8: 78          MOV  A,B
24F9: c2 9c 25    JNZ  $259C
24FC: f5          PUSH PSW
24FD: cd 74 40    CALL $4074
2500: f1          POP  PSW
2501: d6 70       SUI  $70
2503: c3 a8 40    JMP  $40A8
2506: fe f3       CPI  $F3
2508: d0          RNC
2509: d6 c0       SUI  $C0
250B: 32 64 58    STA  $5864
250E: cd aa 35    CALL $35AA
2511: cd 20 38    CALL $3820
2514: 16 4b       MVI  D,$4B
2516: fe 4c       CPI  $4C
2518: ca 3f 25    JZ   $253F
251B: 16 4e       MVI  D,$4E
251D: fe 46       CPI  $46
251F: ca 3f 25    JZ   $253F
2522: 16 4f       MVI  D,$4F
2524: fe 41       CPI  $41
2526: ca 3f 25    JZ   $253F
2529: 16 4a       MVI  D,$4A
252B: fe 50       CPI  $50
252D: ca 3f 25    JZ   $253F
2530: fe 42       CPI  $42
2532: c0          RNZ
2533: d5          PUSH D
2534: cd 74 40    CALL $4074
2537: 3e 31       MVI  A,$31
2539: cd a8 40    CALL $40A8
253C: c3 43 25    JMP  $2543
253F: d5          PUSH D
2540: cd 74 40    CALL $4074
2543: 3a 64 58    LDA  $5864
2546: cd a8 40    CALL $40A8
2549: d1          POP  D
254A: 7a          MOV  A,D
254B: c3 a8 40    JMP  $40A8
254E: 3e 0d       MVI  A,$0D
2550: c3 a8 40    JMP  $40A8
; host_character_dispatch
2553: 21 76 58    LXI  H,$5876
2556: 36 ff       MVI  M,$FF
2558: 21 bf 25    LXI  H,$25BF
255B: fe 20       CPI  $20
255D: da 8e 25    JC   $258E
2560: fe 7f       CPI  $7F
2562: da c0 26    JC   $26C0
2565: c8          RZ
2566: fe a0       CPI  $A0
2568: d2 c0 26    JNC  $26C0
256B: fe 9d       CPI  $9D
256D: c8          RZ
256E: 21 ff 25    LXI  H,$25FF
2571: c3 8e 25    JMP  $258E
2574: cd df 28 c9                                     DB $CD,$DF,$28,$C9
2578: 21 7f 25    LXI  H,$257F
257B: cd 33 38    CALL $3833
257E: c9          RET
257F: 99 09 9a 0a cd 0d ce 0e cf 0f db 1b ee 08 ff    DB $99,$09,$9A,$0A,$CD,$0D,$CE,$0E,$CF,$0F,$DB,$1B,$EE,$08,$FF
; dispatch_index_low5
258E: f5          PUSH PSW
258F: e6 1f       ANI  $1F
2591: 87          ADD  A
2592: 5f          MOV  E,A
2593: 16 00       MVI  D,$00
2595: 19          DAD  D
2596: 5e          MOV  E,M
2597: 23          INX  H
2598: 56          MOV  D,M
2599: eb          XCHG
259A: f1          POP  PSW
259B: e9          PCHL
259C: fe b1       CPI  $B1
259E: 0e 0b       MVI  C,$0B
25A0: ca bb 25    JZ   $25BB
25A3: fe b2       CPI  $B2
25A5: 0e 0a       MVI  C,$0A
25A7: ca bb 25    JZ   $25BB
25AA: fe b3       CPI  $B3
25AC: 0e 09       MVI  C,$09
25AE: ca bb 25    JZ   $25BB
25B1: fe b4       CPI  $B4
25B3: 0e 08       MVI  C,$08
25B5: ca bb 25    JZ   $25BB
25B8: c3 fc 24    JMP  $24FC
25BB: 79          MOV  A,C
25BC: c3 a8 40    JMP  $40A8
25BF: bf 26 bf 26 bf 26 bf 26 bf 26 18 29 bf 26 2d 29 DB $BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$18,$29,$BF,$26,$2D,$29
25CF: 0d 2e fa 2e 5b 29 bf 26 bf 26 47 29 77 29 72 29 DB $0D,$2E,$FA,$2E,$5B,$29,$BF,$26,$BF,$26,$47,$29,$77,$29,$72,$29
25DF: bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 DB $BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26
25EF: bf 26 bf 26 bf 26 b6 29 bf 26 bf 26 bf 26 7d 29 DB $BF,$26,$BF,$26,$BF,$26,$B6,$29,$BF,$26,$BF,$26,$BF,$26,$7D,$29
25FF: bf 26 bf 26 bf 26 bf 26 d7 2d 4d 2e bf 26 bf 26 DB $BF,$26,$BF,$26,$BF,$26,$BF,$26,$D7,$2D,$4D,$2E,$BF,$26,$BF,$26
260F: 83 2a bf 26 bf 26 bf 26 bf 26 c4 2d 8b 2a 99 2a DB $83,$2A,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$C4,$2D,$8B,$2A,$99,$2A
261F: a7 2a bf 26 bf 26 c7 2a bf 26 bf 26 7d 2a 77 2a DB $A7,$2A,$BF,$26,$BF,$26,$C7,$2A,$BF,$26,$BF,$26,$7D,$2A,$77,$2A
262F: bf 26 bf 26 bf 26 11 2b bf 26 53 2b d9 2b bf 26 DB $BF,$26,$BF,$26,$BF,$26,$11,$2B,$BF,$26,$53,$2B,$D9,$2B,$BF,$26
263F: af 2d c4 2d d7 2d e0 2d 0d 2e 4d 2e 55 2e 5d 2e DB $AF,$2D,$C4,$2D,$D7,$2D,$E0,$2D,$0D,$2E,$4D,$2E,$55,$2E,$5D,$2E
264F: 65 2e fa 2e 36 2f ad 2f bc 2f c1 2f 62 2f 27 2f DB $65,$2E,$FA,$2E,$36,$2F,$AD,$2F,$BC,$2F,$C1,$2F,$62,$2F,$27,$2F
265F: 0f 30 bf 26 bf 26 9a 30 30 31 e5 31 1d 32 24 30 DB $0F,$30,$BF,$26,$BF,$26,$9A,$30,$30,$31,$E5,$31,$1D,$32,$24,$30
266F: 40 30 bf 26 72 30 bf 26 bf 26 bf 26 bf 26 bf 26 DB $40,$30,$BF,$26,$72,$30,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26
267F: bf 26 bf 26 bf 26 65 32 90 32 bf 26 bf 26 97 32 DB $BF,$26,$BF,$26,$BF,$26,$65,$32,$90,$32,$BF,$26,$BF,$26,$97,$32
268F: ae 32 ba 33 bf 26 bf 26 4b 34 50 34 7d 34 9d 34 DB $AE,$32,$BA,$33,$BF,$26,$BF,$26,$4B,$34,$50,$34,$7D,$34,$9D,$34
269F: bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 DB $BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26
26AF: bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 bf 26 DB $BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26,$BF,$26
; ignored_control_return
26BF: c9          RET
26C0: 21 63 58    LXI  H,$5863
26C3: b6          ORA  M
26C4: 4f          MOV  C,A
26C5: 3a 2a 5f    LDA  $5F2A
26C8: fe 01       CPI  $01
26CA: da d3 26    JC   $26D3
26CD: ca 92 27    JZ   $2792
26D0: c3 7e 27    JMP  $277E
26D3: 79          MOV  A,C
26D4: fe 20       CPI  $20
26D6: ca 4f 27    JZ   $274F
26D9: fe 30       CPI  $30
26DB: da 31 27    JC   $2731
26DE: fe 3a       CPI  $3A
26E0: da 3c 27    JC   $273C
26E3: fe 40       CPI  $40
26E5: ca 0f 27    JZ   $270F
26E8: fe 41       CPI  $41
26EA: da 31 27    JC   $2731
26ED: fe 5b       CPI  $5B
26EF: da 47 27    JC   $2747
26F2: fe 5e       CPI  $5E
26F4: ca 0f 27    JZ   $270F
26F7: da 1a 27    JC   $271A
26FA: fe 61       CPI  $61
26FC: da 31 27    JC   $2731
26FF: fe 7b       CPI  $7B
2701: da 47 27    JC   $2747
2704: fe 7e       CPI  $7E
2706: ca 0f 27    JZ   $270F
2709: d2 31 27    JNC  $2731
270C: c3 1a 27    JMP  $271A
270F: 3a 03 5f    LDA  $5F03
2712: fe 04       CPI  $04
2714: c2 31 27    JNZ  $2731
2717: c3 47 27    JMP  $2747
271A: 3a 03 5f    LDA  $5F03
271D: a7          ANA  A
271E: ca 31 27    JZ   $2731
2721: fe 05       CPI  $05
2723: ca 31 27    JZ   $2731
2726: fe 04       CPI  $04
2728: c2 47 27    JNZ  $2747
272B: 79          MOV  A,C
272C: fe 5d       CPI  $5D
272E: c2 47 27    JNZ  $2747
2731: 3a b3 58    LDA  $58B3
2734: e6 10       ANI  $10
2736: c2 4f 27    JNZ  $274F
2739: c3 2d 29    JMP  $292D
273C: 3a b3 58    LDA  $58B3
273F: e6 20       ANI  $20
2741: c2 4f 27    JNZ  $274F
2744: c3 2d 29    JMP  $292D
2747: 3a b3 58    LDA  $58B3
274A: e6 40       ANI  $40
274C: ca 2d 29    JZ   $292D
274F: 21 b9 58    LXI  H,$58B9
2752: 36 01       MVI  M,$01
2754: 3a b4 58    LDA  $58B4
2757: e6 20       ANI  $20
2759: c2 63 27    JNZ  $2763
275C: 2a 16 5e    LHLD $5E16
275F: cd d0 27    CALL $27D0
2762: c9          RET
2763: 3a aa 59    LDA  $59AA
2766: a7          ANA  A
2767: c2 78 27    JNZ  $2778
276A: 2a af 58    LHLD $58AF
276D: cd 1d 3e    CALL $3E1D
2770: 11 01 00    LXI  D,$0001
2773: 3e 01       MVI  A,$01
2775: cd 1e 01    CALL $011E
2778: cd 97 00    CALL $0097
277B: c3 d0 27    JMP  $27D0
277E: cd 21 39    CALL $3921
2781: 78          MOV  A,B
2782: a7          ANA  A
2783: cc 43 38    CZ   $3843
2786: ca 92 27    JZ   $2792
2789: 7d          MOV  A,L
278A: 6c          MOV  L,H
278B: 26 5a       MVI  H,$5A
278D: be          CMP  M
278E: da 92 27    JC   $2792
2791: 77          MOV  M,A
2792: 2a 16 5e    LHLD $5E16
2795: cd 48 01    CALL $0148
2798: e6 0f       ANI  $0F
279A: fe 0e       CPI  $0E
279C: ca a9 27    JZ   $27A9
279F: 7d          MOV  A,L
27A0: fe 47       CPI  $47
27A2: cc 0b 38    CZ   $380B
27A5: cd d0 27    CALL $27D0
27A8: c9          RET
27A9: cd a3 00    CALL $00A3
27AC: 7d          MOV  A,L
27AD: fe 3f       CPI  $3F
27AF: cc 0b 38    CZ   $380B
27B2: cd d0 27    CALL $27D0
27B5: 3a aa 59    LDA  $59AA
27B8: a7          ANA  A
27B9: c2 c1 27    JNZ  $27C1
27BC: 0e 20       MVI  C,$20
27BE: cd d0 27    CALL $27D0
27C1: cd ff 37    CALL $37FF
27C4: 7d          MOV  A,L
27C5: fe 51       CPI  $51
27C7: c0          RNZ
27C8: 2e 4f       MVI  L,$4F
27CA: 22 16 5e    SHLD $5E16
27CD: c3 1b 28    JMP  $281B
27D0: 3a 00 5f    LDA  $5F00
27D3: a7          ANA  A
27D4: ca f7 27    JZ   $27F7
27D7: 3a aa 59    LDA  $59AA
27DA: a7          ANA  A
27DB: ca e4 27    JZ   $27E4
27DE: cd 3a 28    CALL $283A
27E1: c3 f7 27    JMP  $27F7
27E4: 16 01       MVI  D,$01
27E6: 3e 5e       MVI  A,$5E
27E8: b9          CMP  C
27E9: ca f3 27    JZ   $27F3
27EC: 14          INR  D
27ED: 3e 7e       MVI  A,$7E
27EF: b9          CMP  C
27F0: c2 f7 27    JNZ  $27F7
27F3: 7a          MOV  A,D
27F4: 32 aa 59    STA  $59AA
27F7: 79          MOV  A,C
27F8: cd 45 01    CALL $0145
27FB: 3a aa 59    LDA  $59AA
27FE: a7          ANA  A
27FF: c0          RNZ
2800: 3a 2a 5f    LDA  $5F2A
2803: a7          ANA  A
2804: c2 0d 28    JNZ  $280D
2807: 3a b4 58    LDA  $58B4
280A: e6 20       ANI  $20
280C: c0          RNZ
280D: 3a a4 58    LDA  $58A4
2810: a7          ANA  A
2811: c2 29 28    JNZ  $2829
2814: 2c          INR  L
2815: 7d          MOV  A,L
2816: fe 51       CPI  $51
2818: da 36 28    JC   $2836
281B: 2e 01       MVI  L,$01
281D: 3a 22 5f    LDA  $5F22
2820: a7          ANA  A
2821: c8          RZ
2822: 22 16 5e    SHLD $5E16
2825: cd 5b 29    CALL $295B
2828: c9          RET
2829: 2c          INR  L
282A: 7d          MOV  A,L
282B: 22 16 5e    SHLD $5E16
282E: fe 51       CPI  $51
2830: d8          RC
2831: 2d          DCR  L
2832: 22 16 5e    SHLD $5E16
2835: c9          RET
2836: 22 16 5e    SHLD $5E16
2839: c9          RET
283A: e5          PUSH H
283B: 21 c6 28    LXI  H,$28C6
283E: 23          INX  H
283F: 23          INX  H
2840: 23          INX  H
2841: 7e          MOV  A,M
2842: a7          ANA  A
2843: ca 58 28    JZ   $2858
2846: b9          CMP  C
2847: c2 3e 28    JNZ  $283E
284A: 23          INX  H
284B: 3a aa 59    LDA  $59AA
284E: 0f          RRC
284F: da 53 28    JC   $2853
2852: 23          INX  H
2853: 4e          MOV  C,M
2854: e1          POP  H
2855: c3 c4 28    JMP  $28C4
2858: e1          POP  H
2859: 3a a4 58    LDA  $58A4
285C: a7          ANA  A
285D: c2 9b 28    JNZ  $289B
2860: 3a 2a 5f    LDA  $5F2A
2863: a7          ANA  A
2864: c2 7e 28    JNZ  $287E
2867: 3a b4 58    LDA  $58B4
286A: e6 20       ANI  $20
286C: c2 86 28    JNZ  $2886
286F: eb          XCHG
2870: 2a b1 58    LHLD $58B1
2873: cd 1d 3e    CALL $3E1D
2876: 2d          DCR  L
2877: cd c9 01    CALL $01C9
287A: eb          XCHG
287B: ca a4 28    JZ   $28A4
287E: cd 0d 28    CALL $280D
2881: 97          SUB  A
2882: 32 aa 59    STA  $59AA
2885: c9          RET
2886: e5          PUSH H
2887: 2a af 58    LHLD $58AF
288A: cd 1d 3e    CALL $3E1D
288D: 11 01 00    LXI  D,$0001
2890: 3e 01       MVI  A,$01
2892: cd 1e 01    CALL $011E
2895: e1          POP  H
2896: 97          SUB  A
2897: 32 aa 59    STA  $59AA
289A: c9          RET
289B: 7d          MOV  A,L
289C: fe 4f       CPI  $4F
289E: da 7e 28    JC   $287E
28A1: c3 c4 28    JMP  $28C4
28A4: c5          PUSH B
28A5: 2a b1 58    LHLD $58B1
28A8: 3a b3 58    LDA  $58B3
28AB: e6 01       ANI  $01
28AD: c4 bb 3f    CNZ  $3FBB
28B0: 2c          INR  L
28B1: 22 16 5e    SHLD $5E16
28B4: cd b3 38    CALL $38B3
28B7: cd 6d 37    CALL $376D
28BA: 2a 16 5e    LHLD $5E16
28BD: 22 a7 58    SHLD $58A7
28C0: c1          POP  B
28C1: c3 c4 28    JMP  $28C4
28C4: 97          SUB  A
28C5: 32 aa 59    STA  $59AA
28C8: c9          RET
28C9: 61 10 15 65 11 16 69 12 17 6f 13 18 75 14 19 00 DB $61,$10,$15,$65,$11,$16,$69,$12,$17,$6F,$13,$18,$75,$14,$19,$00
28D9: d5 16 03 c3 e2 28 d5 16 00 f5 5f fe 80 7a da ec DB $D5,$16,$03,$C3,$E2,$28,$D5,$16,$00,$F5,$5F,$FE,$80,$7A,$DA,$EC
28E9: 28 f6 04 cd a3 00 7b e6 7f cd a9 00 cd 73 00 d2 DB $28,$F6,$04,$CD,$A3,$00,$7B,$E6,$7F,$CD,$A9,$00,$CD,$73,$00,$D2
28F9: 15 29 2a 16 5e 3a 60 58 bc c4 76 00 c2 15 29 3a DB $15,$29,$2A,$16,$5E,$3A,$60,$58,$BC,$C4,$76,$00,$C2,$15,$29,$3A
2909: 25 5f a7 c4 f7 00 cc f1 00 cd 6a 00 f1 d1 c9    DB $25,$5F,$A7,$C4,$F7,$00,$CC,$F1,$00,$CD,$6A,$00,$F1,$D1,$C9
2918: 3a 2a 5f    LDA  $5F2A
291B: fe 01       CPI  $01
291D: c0          RNZ
291E: 3a f8 5d    LDA  $5DF8
2921: fe 02       CPI  $02
2923: c0          RNZ
2924: 3a 2e 5f    LDA  $5F2E
2927: a7          ANA  A
2928: c8          RZ
2929: 3d          DCR  A
292A: c3 48 23    JMP  $2348
292D: cd 55 00    CALL $0055
2930: da 2d 29    JC   $292D
2933: c9          RET
2934: 3a 2a 5f    LDA  $5F2A
2937: fe 01       CPI  $01
2939: da c7 2a    JC   $2AC7
293C: cd 66 3f    CALL $3F66
293F: 3a 20 5f    LDA  $5F20
2942: a7          ANA  A
2943: c2 47 29    JNZ  $2947
2946: c9          RET
; carriage_return
2947: 3e 00       MVI  A,$00
2949: 32 aa 59    STA  $59AA
294C: 2a 16 5e    LHLD $5E16
294F: 2e 01       MVI  L,$01
2951: cd c9 38    CALL $38C9
2954: 3a 20 5f    LDA  $5F20
2957: a7          ANA  A
2958: 3e 0a       MVI  A,$0A
295A: c8          RZ
; line_feed
295B: 4f          MOV  C,A
295C: 3e 00       MVI  A,$00
295E: 32 aa 59    STA  $59AA
2961: cd 45 42    CALL $4245
2964: cd d7 38    CALL $38D7
2967: 24          INR  H
2968: cd c9 38    CALL $38C9
296B: d0          RNC
296C: 06 01       MVI  B,$01
296E: cd a8 30    CALL $30A8
2971: c9          RET
; shift_in
2972: 97          SUB  A
2973: 32 63 58    STA  $5863
2976: c9          RET
; shift_out
2977: 3e 80       MVI  A,$80
2979: 32 63 58    STA  $5863
297C: c9          RET
297D: 3a ae 59    LDA  $59AE
2980: fe 47       CPI  $47
2982: c0          RNZ
2983: af          XRA  A
2984: 32 ab 59    STA  $59AB
2987: 3e 1f       MVI  A,$1F
2989: cd 04 56    CALL $5604
298C: 3e 01       MVI  A,$01
298E: 32 ac 59    STA  $59AC
2991: 21 d2 24    LXI  H,$24D2
2994: 22 53 58    SHLD $5853
2997: 21 e2 56    LXI  H,$56E2
299A: 22 55 58    SHLD $5855
299D: cd 49 00    CALL $0049
29A0: 3a 26 5f    LDA  $5F26
29A3: 32 a9 59    STA  $59A9
29A6: 3a 25 5f    LDA  $5F25
29A9: a7          ANA  A
29AA: c0          RNZ
29AB: 3e 00       MVI  A,$00
29AD: 32 26 5f    STA  $5F26
29B0: 26 19       MVI  H,$19
29B2: cd 06 01    CALL $0106
29B5: c9          RET
; escape_dispatch
29B6: 3e 00       MVI  A,$00
29B8: 32 aa 59    STA  $59AA
29BB: cd aa 35    CALL $35AA
29BE: fe 23       CPI  $23
29C0: ca d9 29    JZ   $29D9
29C3: fe 63       CPI  $63
29C5: ca 40 21    JZ   $2140
29C8: fe 40       CPI  $40
29CA: d8          RC
29CB: fe 60       CPI  $60
29CD: d0          RNC
29CE: fe 5d       CPI  $5D
29D0: c8          RZ
29D1: d6 40       SUI  $40
29D3: 21 ff 25    LXI  H,$25FF
29D6: c3 8e 25    JMP  $258E
29D9: 3a 2a 5f    LDA  $5F2A
29DC: a7          ANA  A
29DD: c8          RZ
29DE: cd aa 35    CALL $35AA
29E1: 2a 16 5e    LHLD $5E16
29E4: 54          MOV  D,H
29E5: fe 36       CPI  $36
29E7: ca 1f 2a    JZ   $2A1F
29EA: fe 35       CPI  $35
29EC: c0          RNZ
29ED: cd a0 00    CALL $00A0
29F0: e6 0f       ANI  $0F
29F2: fe 0e       CPI  $0E
29F4: c0          RNZ
29F5: 97          SUB  A
29F6: cd a3 00    CALL $00A3
29F9: 1e 01       MVI  E,$01
29FB: 2e 01       MVI  L,$01
29FD: 22 16 5e    SHLD $5E16
2A00: eb          XCHG
2A01: cd 42 01    CALL $0142
2A04: eb          XCHG
2A05: cd 45 01    CALL $0145
2A08: 1c          INR  E
2A09: 1c          INR  E
2A0A: 2c          INR  L
2A0B: 7d          MOV  A,L
2A0C: fe 29       CPI  $29
2A0E: c2 00 2a    JNZ  $2A00
2A11: 97          SUB  A
2A12: cd 45 01    CALL $0145
2A15: 2c          INR  L
2A16: 7d          MOV  A,L
2A17: fe 51       CPI  $51
2A19: c2 11 2a    JNZ  $2A11
2A1C: c3 6b 2a    JMP  $2A6B
2A1F: cd a0 00    CALL $00A0
2A22: e6 0f       ANI  $0F
2A24: fe 0e       CPI  $0E
2A26: c8          RZ
2A27: 3e 0e       MVI  A,$0E
2A29: cd a3 00    CALL $00A3
2A2C: 1e 28       MVI  E,$28
2A2E: 2e 51       MVI  L,$51
2A30: 2d          DCR  L
2A31: 3e 20       MVI  A,$20
2A33: cd 45 01    CALL $0145
2A36: 2d          DCR  L
2A37: eb          XCHG
2A38: cd 42 01    CALL $0142
2A3B: eb          XCHG
2A3C: cd 45 01    CALL $0145
2A3F: 1d          DCR  E
2A40: c2 30 2a    JNZ  $2A30
2A43: 22 16 5e    SHLD $5E16
2A46: cd 3c 3e    CALL $3E3C
2A49: 54          MOV  D,H
2A4A: 14          INR  D
2A4B: 5d          MOV  E,L
2A4C: cd 26 3b    CALL $3B26
2A4F: 11 00 00    LXI  D,$0000
2A52: cd d8 3a    CALL $3AD8
2A55: 2a 16 5e    LHLD $5E16
2A58: 24          INR  H
2A59: 22 16 5e    SHLD $5E16
2A5C: 11 00 70    LXI  D,$7000
2A5F: cd d0 3a    CALL $3AD0
2A62: 2a 16 5e    LHLD $5E16
2A65: 25          DCR  H
2A66: 2e 01       MVI  L,$01
2A68: 22 16 5e    SHLD $5E16
2A6B: cd 3c 3e    CALL $3E3C
2A6E: 2e 01       MVI  L,$01
2A70: cd 43 38    CALL $3843
2A73: cd ff 37    CALL $37FF
2A76: c9          RET
2A77: 11 00 70    LXI  D,$7000
2A7A: c3 d0 3a    JMP  $3AD0
2A7D: 11 00 00    LXI  D,$0000
2A80: c3 d0 3a    JMP  $3AD0
2A83: 3a 2a 5f    LDA  $5F2A
2A86: a7          ANA  A
2A87: c4 7c 43    CNZ  $437C
2A8A: c9          RET
2A8B: cd aa 35    CALL $35AA
2A8E: fe 21       CPI  $21
2A90: d8          RC
2A91: fe 7f       CPI  $7F
2A93: d0          RNC
2A94: c6 80       ADI  $80
2A96: c3 c0 26    JMP  $26C0
2A99: cd aa 35    CALL $35AA
2A9C: fe 30       CPI  $30
2A9E: d8          RC
2A9F: fe 50       CPI  $50
2AA1: d0          RNC
2AA2: c6 50       ADI  $50
2AA4: c3 c0 26    JMP  $26C0
2AA7: 78          MOV  A,B
2AA8: a7          ANA  A
2AA9: c8          RZ
2AAA: cd aa 35    CALL $35AA
2AAD: fe 50       CPI  $50
2AAF: ca f9 2c    JZ   $2CF9
2AB2: fe 53       CPI  $53
2AB4: ca 8d 2c    JZ   $2C8D
2AB7: fe 42       CPI  $42
2AB9: ca 91 2c    JZ   $2C91
2ABC: fe 4c       CPI  $4C
2ABE: ca 51 2c    JZ   $2C51
2AC1: fe 4d       CPI  $4D
2AC3: ca 34 2c    JZ   $2C34
2AC6: c9          RET
2AC7: 78          MOV  A,B
2AC8: a7          ANA  A
2AC9: ca f1 2a    JZ   $2AF1
2ACC: 3a 31 5f    LDA  $5F31
2ACF: a7          ANA  A
2AD0: c8          RZ
2AD1: 3a 1e 5f    LDA  $5F1E
2AD4: a7          ANA  A
2AD5: ca e1 2a    JZ   $2AE1
2AD8: 32 39 5f    STA  $5F39
2ADB: 21 f0 2a    LXI  H,$2AF0
2ADE: 22 53 58    SHLD $5853
2AE1: 3e 01       MVI  A,$01
2AE3: cd ea 2a    CALL $2AEA
2AE6: cd a3 3e    CALL $3EA3
2AE9: 97          SUB  A
2AEA: 32 9b 58    STA  $589B
2AED: cd 1c 45    CALL $451C
2AF0: c9          RET
2AF1: 3a 31 5f    LDA  $5F31
2AF4: fe 01       CPI  $01
2AF6: da d1 2a    JC   $2AD1
2AF9: 3e 93       MVI  A,$93
2AFB: ca 76 40    JZ   $4076
2AFE: cd aa 35    CALL $35AA
2B01: fe 30       CPI  $30
2B03: d8          RC
2B04: fe 3a       CPI  $3A
2B06: d0          RNC
2B07: f5          PUSH PSW
2B08: 3e 91       MVI  A,$91
2B0A: cd 76 40    CALL $4076
2B0D: f1          POP  PSW
2B0E: c3 a8 40    JMP  $40A8
2B11: 3e 00       MVI  A,$00
2B13: 32 aa 59    STA  $59AA
2B16: cd aa 35    CALL $35AA
2B19: cd 2a 35    CALL $352A
2B1C: fe 40       CPI  $40
2B1E: dc 5f 35    CC   $355F
2B21: c3 27 2b    JMP  $2B27
2B24: cd aa 35    CALL $35AA
2B27: fe 20       CPI  $20
2B29: d8          RC
2B2A: fe 7f       CPI  $7F
2B2C: d0          RNC
2B2D: fe 40       CPI  $40
2B2F: d2 41 2b    JNC  $2B41
2B32: cd 34 35    CALL $3534
2B35: d2 24 2b    JNC  $2B24
2B38: cd aa 35    CALL $35AA
2B3B: fe 40       CPI  $40
2B3D: da 38 2b    JC   $2B38
2B40: c9          RET
2B41: 21 3f 26    LXI  H,$263F
2B44: d6 40       SUI  $40
2B46: fe 20       CPI  $20
2B48: da 8e 25    JC   $258E
2B4B: d6 20       SUI  $20
2B4D: 21 7f 26    LXI  H,$267F
2B50: c3 8e 25    JMP  $258E
2B53: 3a 2a 5f    LDA  $5F2A
2B56: fe 03       CPI  $03
2B58: c8          RZ
2B59: 3e 01       MVI  A,$01
2B5B: 32 a4 58    STA  $58A4
2B5E: cd 43 47    CALL $4743
2B61: cd 8c 38    CALL $388C
2B64: da cd 2b    JC   $2BCD
2B67: cd 0a 23    CALL $230A
2B6A: da 61 2b    JC   $2B61
2B6D: fe fb       CPI  $FB
2B6F: ca cd 2b    JZ   $2BCD
2B72: fe 9c       CPI  $9C
2B74: ca a3 2b    JZ   $2BA3
2B77: fe b4       CPI  $B4
2B79: ca 99 2b    JZ   $2B99
2B7C: fe 80       CPI  $80
2B7E: d2 61 2b    JNC  $2B61
2B81: fe 20       CPI  $20
2B83: da 61 2b    JC   $2B61
2B86: cd 97 00    CALL $0097
2B89: 4f          MOV  C,A
2B8A: cd d0 27    CALL $27D0
2B8D: cd 7f 00    CALL $007F
2B90: cd 73 00    CALL $0073
2B93: d2 61 2b    JNC  $2B61
2B96: c3 9c 2b    JMP  $2B9C
2B99: cd 7f 00    CALL $007F
2B9C: 97          SUB  A
2B9D: cd a9 00    CALL $00A9
2BA0: c3 61 2b    JMP  $2B61
2BA3: 3a 1c 5f    LDA  $5F1C
2BA6: f5          PUSH PSW
2BA7: 3e 01       MVI  A,$01
2BA9: 32 1c 5f    STA  $5F1C
2BAC: 3e 9d       MVI  A,$9D
2BAE: cd 76 40    CALL $4076
2BB1: 21 01 19    LXI  H,$1901
2BB4: 01 00 00    LXI  B,$0000
2BB7: cd 42 01    CALL $0142
2BBA: cd e5 3f    CALL $3FE5
2BBD: 2c          INR  L
2BBE: 7d          MOV  A,L
2BBF: fe 51       CPI  $51
2BC1: c2 b7 2b    JNZ  $2BB7
2BC4: 3e 9c       MVI  A,$9C
2BC6: cd 76 40    CALL $4076
2BC9: f1          POP  PSW
2BCA: 32 1c 5f    STA  $5F1C
2BCD: 3e 00       MVI  A,$00
2BCF: 32 a4 58    STA  $58A4
2BD2: cd 5e 47    CALL $475E
2BD5: cd 1c 45    CALL $451C
2BD8: c9          RET
2BD9: 3e 01       MVI  A,$01
2BDB: 32 a4 58    STA  $58A4
2BDE: cd 43 47    CALL $4743
2BE1: cd 8c 38    CALL $388C
2BE4: da 28 2c    JC   $2C28
2BE7: cd be 00    CALL $00BE
2BEA: da e1 2b    JC   $2BE1
2BED: fe 9c       CPI  $9C
2BEF: ca 17 2c    JZ   $2C17
2BF2: fe 1b       CPI  $1B
2BF4: ca 06 2c    JZ   $2C06
2BF7: fe 20       CPI  $20
2BF9: da e1 2b    JC   $2BE1
2BFC: cd 97 00    CALL $0097
2BFF: 4f          MOV  C,A
2C00: cd d0 27    CALL $27D0
2C03: c3 e1 2b    JMP  $2BE1
2C06: cd 8c 38    CALL $388C
2C09: da 28 2c    JC   $2C28
2C0C: cd be 00    CALL $00BE
2C0F: da 06 2c    JC   $2C06
2C12: fe 5c       CPI  $5C
2C14: c2 f7 2b    JNZ  $2BF7
2C17: cd 8c 38    CALL $388C
2C1A: da 28 2c    JC   $2C28
2C1D: cd bb 00    CALL $00BB
2C20: da 17 2c    JC   $2C17
2C23: fe fb       CPI  $FB
2C25: c2 17 2c    JNZ  $2C17
2C28: 3e 00       MVI  A,$00
2C2A: 32 a4 58    STA  $58A4
2C2D: cd 5e 47    CALL $475E
2C30: cd 1c 45    CALL $451C
2C33: c9          RET
2C34: cd aa 35    CALL $35AA
2C37: 32 25 59    STA  $5925
2C3A: cd dd 35    CALL $35DD
2C3D: c0          RNZ
2C3E: 3a 25 59    LDA  $5925
2C41: fe 30       CPI  $30
2C43: ca 15 24    JZ   $2415
2C46: fe 31       CPI  $31
2C48: ca 0f 24    JZ   $240F
2C4B: fe 32       CPI  $32
2C4D: ca de 23    JZ   $23DE
2C50: c9          RET
2C51: cd aa 35    CALL $35AA
2C54: fe 31       CPI  $31
2C56: d8          RC
2C57: fe 35       CPI  $35
2C59: d0          RNC
2C5A: d6 30       SUI  $30
2C5C: 32 9d 58    STA  $589D
2C5F: cd aa 35    CALL $35AA
2C62: fe 30       CPI  $30
2C64: d8          RC
2C65: fe 33       CPI  $33
2C67: d0          RNC
2C68: 32 9e 58    STA  $589E
2C6B: cd dd 35    CALL $35DD
2C6E: c0          RNZ
2C6F: 3a 9e 58    LDA  $589E
2C72: 16 08       MVI  D,$08
2C74: fe 30       CPI  $30
2C76: ca 82 2c    JZ   $2C82
2C79: 16 00       MVI  D,$00
2C7B: fe 31       CPI  $31
2C7D: ca 82 2c    JZ   $2C82
2C80: 16 10       MVI  D,$10
2C82: 3a 9d 58    LDA  $589D
2C85: 82          ADD  D
2C86: cd 64 00    CALL $0064
2C89: da 86 2c    JC   $2C86
2C8C: c9          RET
2C8D: 97          SUB  A
2C8E: c3 93 2c    JMP  $2C93
2C91: 3e 08       MVI  A,$08
2C93: 32 a3 58    STA  $58A3
2C96: 3a 25 5f    LDA  $5F25
2C99: a7          ANA  A
2C9A: c0          RNZ
2C9B: 3e 01       MVI  A,$01
2C9D: 32 a4 58    STA  $58A4
2CA0: 2a 16 5e    LHLD $5E16
2CA3: 22 a7 58    SHLD $58A7
2CA6: 21 40 19    LXI  H,$1940
2CA9: 22 a0 58    SHLD $58A0
2CAC: cd dd 35    CALL $35DD
2CAF: ca ed 2c    JZ   $2CED
2CB2: da ed 2c    JC   $2CED
2CB5: fe 20       CPI  $20
2CB7: da ed 2c    JC   $2CED
2CBA: fe 7f       CPI  $7F
2CBC: d2 ed 2c    JNC  $2CED
2CBF: f5          PUSH PSW
2CC0: 3e 01       MVI  A,$01
2CC2: 32 a2 58    STA  $58A2
2CC5: 3a a3 58    LDA  $58A3
2CC8: cd a3 00    CALL $00A3
2CCB: f1          POP  PSW
2CCC: 2a a0 58    LHLD $58A0
2CCF: 4f          MOV  C,A
2CD0: cd d0 27    CALL $27D0
2CD3: 2d          DCR  L
2CD4: 7d          MOV  A,L
2CD5: fe 4f       CPI  $4F
2CD7: ca e4 2c    JZ   $2CE4
2CDA: 2c          INR  L
2CDB: 22 a0 58    SHLD $58A0
2CDE: cd ff 37    CALL $37FF
2CE1: c3 ac 2c    JMP  $2CAC
2CE4: cd 82 00    CALL $0082
2CE7: cd ff 37    CALL $37FF
2CEA: c3 ac 2c    JMP  $2CAC
2CED: 3e 00       MVI  A,$00
2CEF: 32 a4 58    STA  $58A4
2CF2: 2a a7 58    LHLD $58A7
2CF5: 22 16 5e    SHLD $5E16
2CF8: c9          RET
2CF9: 97          SUB  A
2CFA: 32 bc 58    STA  $58BC
2CFD: cd aa 35    CALL $35AA
2D00: d6 30       SUI  $30
2D02: d8          RC
2D03: ca 0b 2d    JZ   $2D0B
2D06: fe 02       CPI  $02
2D08: d0          RNC
2D09: 3e 0a       MVI  A,$0A
2D0B: 32 bc 58    STA  $58BC
2D0E: cd aa 35    CALL $35AA
2D11: d6 30       SUI  $30
2D13: d8          RC
2D14: fe 0a       CPI  $0A
2D16: d0          RNC
2D17: 5f          MOV  E,A
2D18: 3a bc 58    LDA  $58BC
2D1B: 83          ADD  E
2D1C: 3d          DCR  A
2D1D: 16 0c       MVI  D,$0C
2D1F: fe 08       CPI  $08
2D21: da 30 2d    JC   $2D30
2D24: 16 20       MVI  D,$20
2D26: fe 0c       CPI  $0C
2D28: da 30 2d    JC   $2D30
2D2B: 16 30       MVI  D,$30
2D2D: fe 10       CPI  $10
2D2F: d0          RNC
2D30: 32 ba 58    STA  $58BA
2D33: 7a          MOV  A,D
2D34: 32 bb 58    STA  $58BB
2D37: 21 c1 58    LXI  H,$58C1
2D3A: 22 bd 58    SHLD $58BD
2D3D: 11 f3 58    LXI  D,$58F3
2D40: 36 20       MVI  M,$20
2D42: 23          INX  H
2D43: cd c9 01    CALL $01C9
2D46: c2 40 2d    JNZ  $2D40
2D49: cd dd 35    CALL $35DD
2D4C: ca 7b 2d    JZ   $2D7B
2D4F: cd 88 2d    CALL $2D88
2D52: d8          RC
2D53: 07          RLC
2D54: 07          RLC
2D55: 07          RLC
2D56: 07          RLC
2D57: e6 f0       ANI  $F0
2D59: 32 bc 58    STA  $58BC
2D5C: cd aa 35    CALL $35AA
2D5F: cd 88 2d    CALL $2D88
2D62: d8          RC
2D63: 5f          MOV  E,A
2D64: 3a bc 58    LDA  $58BC
2D67: b3          ORA  E
2D68: 2a bd 58    LHLD $58BD
2D6B: 77          MOV  M,A
2D6C: 23          INX  H
2D6D: 22 bd 58    SHLD $58BD
2D70: 3a bb 58    LDA  $58BB
2D73: 3d          DCR  A
2D74: f8          RM
2D75: 32 bb 58    STA  $58BB
2D78: c3 49 2d    JMP  $2D49
2D7B: 21 c1 58    LXI  H,$58C1
2D7E: 3a ba 58    LDA  $58BA
2D81: cd 66 01    CALL $0166
2D84: d0          RNC
2D85: c3 8c 4c    JMP  $4C8C
2D88: fe 67       CPI  $67
2D8A: d2 a6 2d    JNC  $2DA6
2D8D: fe 61       CPI  $61
2D8F: d2 a8 2d    JNC  $2DA8
2D92: fe 47       CPI  $47
2D94: d2 a6 2d    JNC  $2DA6
2D97: fe 41       CPI  $41
2D99: d2 aa 2d    JNC  $2DAA
2D9C: fe 3a       CPI  $3A
2D9E: d2 a6 2d    JNC  $2DA6
2DA1: fe 30       CPI  $30
2DA3: d2 ac 2d    JNC  $2DAC
2DA6: 37          STC
2DA7: c9          RET
2DA8: d6 20       SUI  $20
2DAA: d6 07       SUI  $07
2DAC: d6 30       SUI  $30
2DAE: c9          RET
2DAF: cd 28 39    CALL $3928
2DB2: d4 1b 01    CNC  $011B
2DB5: dc 1e 01    CC   $011E
2DB8: cd 21 39    CALL $3921
2DBB: cd 43 38    CALL $3843
2DBE: 21 b9 58    LXI  H,$58B9
2DC1: 36 01       MVI  M,$01
2DC3: c9          RET
2DC4: cd 83 35    CALL $3583
2DC7: 57          MOV  D,A
2DC8: 7c          MOV  A,H
2DC9: 92          SUB  D
2DCA: d8          RC
2DCB: 67          MOV  H,A
2DCC: cd 7c 3b    CALL $3B7C
2DCF: d2 c9 38    JNC  $38C9
2DD2: 16 01       MVI  D,$01
2DD4: c3 c8 2d    JMP  $2DC8
2DD7: cd 83 35    CALL $3583
2DDA: 84          ADD  H
2DDB: d8          RC
2DDC: 67          MOV  H,A
2DDD: c3 c9 38    JMP  $38C9
2DE0: cd d7 38    CALL $38D7
2DE3: cd 3c 3e    CALL $3E3C
2DE6: cd 86 35    CALL $3586
2DE9: 85          ADD  L
2DEA: 6f          MOV  L,A
2DEB: dc 9b 38    CC   $389B
2DEE: cd 9b 38    CALL $389B
2DF1: d2 ee 2d    JNC  $2DEE
2DF4: 25          DCR  H
2DF5: 6b          MOV  L,E
2DF6: cd 1d 3e    CALL $3E1D
2DF9: d8          RC
2DFA: eb          XCHG
2DFB: 2a 16 5e    LHLD $5E16
2DFE: eb          XCHG
2DFF: 7a          MOV  A,D
2E00: bc          CMP  H
2E01: ca 09 2e    JZ   $2E09
2E04: 3a 22 5f    LDA  $5F22
2E07: a7          ANA  A
2E08: c8          RZ
2E09: cd c9 38    CALL $38C9
2E0C: c9          RET
; backspace
2E0D: 3a aa 59    LDA  $59AA
2E10: a7          ANA  A
2E11: ca 1a 2e    JZ   $2E1A
2E14: 3e 00       MVI  A,$00
2E16: 32 aa 59    STA  $59AA
2E19: c9          RET
2E1A: cd 83 35    CALL $3583
2E1D: 57          MOV  D,A
2E1E: 7d          MOV  A,L
2E1F: 92          SUB  D
2E20: ca 32 2e    JZ   $2E32
2E23: da 32 2e    JC   $2E32
2E26: 6f          MOV  L,A
2E27: cd 7c 3b    CALL $3B7C
2E2A: d2 c9 38    JNC  $38C9
2E2D: 16 01       MVI  D,$01
2E2F: c3 1e 2e    JMP  $2E1E
2E32: 3a 21 5f    LDA  $5F21
2E35: a7          ANA  A
2E36: c8          RZ
2E37: 7a          MOV  A,D
2E38: 95          SUB  L
2E39: 57          MOV  D,A
2E3A: 25          DCR  H
2E3B: c8          RZ
2E3C: 2e 50       MVI  L,$50
2E3E: cd 48 01    CALL $0148
2E41: e6 0f       ANI  $0F
2E43: fe 0e       CPI  $0E
2E45: c2 1e 2e    JNZ  $2E1E
2E48: 2e 28       MVI  L,$28
2E4A: c3 1e 2e    JMP  $2E1E
2E4D: cd 83 35    CALL $3583
2E50: 2e 01       MVI  L,$01
2E52: c3 da 2d    JMP  $2DDA
2E55: cd 83 35    CALL $3583
2E58: 2e 01       MVI  L,$01
2E5A: c3 c7 2d    JMP  $2DC7
2E5D: cd 83 35    CALL $3583
2E60: 6f          MOV  L,A
2E61: cd c9 38    CALL $38C9
2E64: c9          RET
2E65: 21 01 01    LXI  H,$0101
2E68: cd 96 35    CALL $3596
2E6B: da 76 2e    JC   $2E76
2E6E: 67          MOV  H,A
2E6F: cd 96 35    CALL $3596
2E72: da 76 2e    JC   $2E76
2E75: 6f          MOV  L,A
2E76: 7d          MOV  A,L
2E77: a7          ANA  A
2E78: c8          RZ
2E79: fe 51       CPI  $51
2E7B: d0          RNC
2E7C: 3a 38 5f    LDA  $5F38
2E7F: a7          ANA  A
2E80: cc 48 01    CZ   $0148
2E83: c4 9e 3d    CNZ  $3D9E
2E86: e6 0f       ANI  $0F
2E88: fe 0e       CPI  $0E
2E8A: c2 91 2e    JNZ  $2E91
2E8D: 7d          MOV  A,L
2E8E: fe 29       CPI  $29
2E90: d0          RNC
2E91: 78          MOV  A,B
2E92: a7          ANA  A
2E93: c2 b0 2e    JNZ  $2EB0
2E96: 3a 2a 5f    LDA  $5F2A
2E99: a7          ANA  A
2E9A: ca b0 2e    JZ   $2EB0
2E9D: 7c          MOV  A,H
2E9E: 85          ADD  L
2E9F: fe 02       CPI  $02
2EA1: c2 b0 2e    JNZ  $2EB0
2EA4: eb          XCHG
2EA5: cd d7 38    CALL $38D7
2EA8: eb          XCHG
2EA9: 7a          MOV  A,D
2EAA: 83          ADD  E
2EAB: fe 02       CPI  $02
2EAD: c2 c9 38    JNZ  $38C9
2EB0: 3a 38 5f    LDA  $5F38
2EB3: a7          ANA  A
2EB4: ca c9 38    JZ   $38C9
2EB7: 3a 2a 5f    LDA  $5F2A
2EBA: a7          ANA  A
2EBB: cc ca 3b    CZ   $3BCA
2EBE: d8          RC
2EBF: e5          PUSH H
2EC0: cd 1d 3e    CALL $3E1D
2EC3: da cb 2e    JC   $2ECB
2EC6: cd c9 38    CALL $38C9
2EC9: e1          POP  H
2ECA: c9          RET
2ECB: e1          POP  H
2ECC: cd 3b 3d    CALL $3D3B
2ECF: 3a 60 58    LDA  $5860
2ED2: 47          MOV  B,A
2ED3: 3a a9 58    LDA  $58A9
2ED6: 4f          MOV  C,A
2ED7: bc          CMP  H
2ED8: da e8 2e    JC   $2EE8
2EDB: 7c          MOV  A,H
2EDC: 90          SUB  B
2EDD: ca e3 2e    JZ   $2EE3
2EE0: d2 f4 2e    JNC  $2EF4
2EE3: 3e 01       MVI  A,$01
2EE5: c3 f4 2e    JMP  $2EF4
2EE8: 3a aa 58    LDA  $58AA
2EEB: bc          CMP  H
2EEC: d8          RC
2EED: c8          RZ
2EEE: 90          SUB  B
2EEF: bc          CMP  H
2EF0: da f4 2e    JC   $2EF4
2EF3: 7c          MOV  A,H
2EF4: cd 17 3d    CALL $3D17
2EF7: c3 bf 2e    JMP  $2EBF
; horizontal_tab
2EFA: 3e 00       MVI  A,$00
2EFC: 32 aa 59    STA  $59AA
2EFF: cd 86 35    CALL $3586
2F02: 57          MOV  D,A
2F03: 3a 2a 5f    LDA  $5F2A
2F06: a7          ANA  A
2F07: ca 15 2f    JZ   $2F15
2F0A: cd 43 43    CALL $4343
2F0D: cd c9 38    CALL $38C9
2F10: 15          DCR  D
2F11: c2 0a 2f    JNZ  $2F0A
2F14: c9          RET
2F15: cd 21 39    CALL $3921
2F18: cd 92 3b    CALL $3B92
2F1B: d8          RC
2F1C: 15          DCR  D
2F1D: c2 18 2f    JNZ  $2F18
2F20: cd ca 3b    CALL $3BCA
2F23: d8          RC
2F24: c3 f9 38    JMP  $38F9
2F27: 3a 2a 5f    LDA  $5F2A
2F2A: a7          ANA  A
2F2B: c0          RNZ
2F2C: 2a b1 58    LHLD $58B1
2F2F: eb          XCHG
2F30: 2a af 58    LHLD $58AF
2F33: c3 b5 2f    JMP  $2FB5
2F36: 3a a9 58    LDA  $58A9
2F39: 67          MOV  H,A
2F3A: cd 81 38    CALL $3881
2F3D: 57          MOV  D,A
2F3E: 2e 01       MVI  L,$01
2F40: 5d          MOV  E,L
2F41: cd 95 39    CALL $3995
2F44: d2 ac 39    JNC  $39AC
2F47: f5          PUSH PSW
2F48: 26 01       MVI  H,$01
2F4A: 3a aa 58    LDA  $58AA
2F4D: 57          MOV  D,A
2F4E: f1          POP  PSW
2F4F: fe 0a       CPI  $0A
2F51: d8          RC
2F52: cc 21 39    CZ   $3921
2F55: eb          XCHG
2F56: fe 0b       CPI  $0B
2F58: cc 21 39    CZ   $3921
2F5B: eb          XCHG
2F5C: fe 0d       CPI  $0D
2F5E: dc ac 39    CC   $39AC
2F61: c9          RET
2F62: 3a 2a 5f    LDA  $5F2A
2F65: a7          ANA  A
2F66: ca 8c 2f    JZ   $2F8C
2F69: cd 43 43    CALL $4343
2F6C: f5          PUSH PSW
2F6D: cd e7 38    CALL $38E7
2F70: f1          POP  PSW
2F71: d2 77 2f    JNC  $2F77
2F74: 2e 01       MVI  L,$01
2F76: 24          INR  H
2F77: cd 3c 3e    CALL $3E3C
2F7A: eb          XCHG
2F7B: cd 5f 43    CALL $435F
2F7E: f5          PUSH PSW
2F7F: cd e7 38    CALL $38E7
2F82: f1          POP  PSW
2F83: dc 97 00    CC   $0097
2F86: cd 3c 3e    CALL $3E3C
2F89: c3 b5 2f    JMP  $2FB5
2F8C: cd 21 39    CALL $3921
2F8F: 54          MOV  D,H
2F90: 5d          MOV  E,L
2F91: cd 92 3b    CALL $3B92
2F94: d2 9a 2f    JNC  $2F9A
2F97: 2a b1 58    LHLD $58B1
2F9A: eb          XCHG
2F9B: cd 68 38    CALL $3868
2F9E: ca a7 2f    JZ   $2FA7
2FA1: cd b2 3b    CALL $3BB2
2FA4: d2 aa 2f    JNC  $2FAA
2FA7: 2a af 58    LHLD $58AF
2FAA: c3 b5 2f    JMP  $2FB5
2FAD: cd 21 39    CALL $3921
2FB0: 54          MOV  D,H
2FB1: 14          INR  D
2FB2: 1e 01       MVI  E,$01
2FB4: 6b          MOV  L,E
2FB5: cd 95 39    CALL $3995
2FB8: d4 ac 39    CNC  $39AC
2FBB: c9          RET
2FBC: 0e 00       MVI  C,$00
2FBE: c3 c3 2f    JMP  $2FC3
2FC1: 0e 01       MVI  C,$01
2FC3: 3a 2a 5f    LDA  $5F2A
2FC6: a7          ANA  A
2FC7: c8          RZ
2FC8: cd d7 38    CALL $38D7
2FCB: e5          PUSH H
2FCC: cd 86 35    CALL $3586
2FCF: 47          MOV  B,A
2FD0: cd 21 39    CALL $3921
2FD3: 3a 28 5f    LDA  $5F28
2FD6: a7          ANA  A
2FD7: c2 f2 2f    JNZ  $2FF2
2FDA: cd 79 38    CALL $3879
2FDD: 3d          DCR  A
2FDE: 57          MOV  D,A
2FDF: 7c          MOV  A,H
2FE0: d6 02       SUI  $02
2FE2: 80          ADD  B
2FE3: ba          CMP  D
2FE4: d2 0a 30    JNC  $300A
2FE7: 79          MOV  A,C
2FE8: a7          ANA  A
2FE9: cc 6d 3c    CZ   $3C6D
2FEC: c4 95 3c    CNZ  $3C95
2FEF: c3 0a 30    JMP  $300A
2FF2: eb          XCHG
2FF3: cd 6e 38    CALL $386E
2FF6: 67          MOV  H,A
2FF7: 7a          MOV  A,D
2FF8: c6 01       ADI  $01
2FFA: 90          SUB  B
2FFB: da 0a 30    JC   $300A
2FFE: bc          CMP  H
2FFF: da 0a 30    JC   $300A
3002: 79          MOV  A,C
3003: a7          ANA  A
3004: cc 95 3c    CZ   $3C95
3007: c4 6d 3c    CNZ  $3C6D
300A: e1          POP  H
300B: cd c9 38    CALL $38C9
300E: c9          RET
300F: cd 28 39    CALL $3928
3012: d4 15 01    CNC  $0115
3015: dc 18 01    CC   $0118
3018: cd 21 39    CALL $3921
301B: cd 43 38    CALL $3843
301E: 21 b9 58    LXI  H,$58B9
3021: 36 01       MVI  M,$01
3023: c9          RET
3024: 3a 2a 5f    LDA  $5F2A
3027: a7          ANA  A
3028: c8          RZ
3029: cd 78 35    CALL $3578
302C: a7          ANA  A
302D: ca 7c 43    JZ   $437C
3030: fe 02       CPI  $02
3032: ca 84 43    JZ   $4384
3035: fe 04       CPI  $04
3037: ca 8c 43    JZ   $438C
303A: fe 05       CPI  $05
303C: ca 8c 43    JZ   $438C
303F: c9          RET
3040: cd d7 38    CALL $38D7
3043: cd 3c 3e    CALL $3E3C
3046: cd 86 35    CALL $3586
3049: 85          ADD  L
304A: 6f          MOV  L,A
304B: dc 9b 38    CC   $389B
304E: cd 9b 38    CALL $389B
3051: d2 4e 30    JNC  $304E
3054: 25          DCR  H
3055: 6b          MOV  L,E
3056: cd 9e 3d    CALL $3D9E
3059: fe 0e       CPI  $0E
305B: cc ef 38    CZ   $38EF
305E: eb          XCHG
305F: cd 79 38    CALL $3879
3062: 3d          DCR  A
3063: ba          CMP  D
3064: d2 6b 30    JNC  $306B
3067: 7b          MOV  A,E
3068: fe 01       CPI  $01
306A: c0          RNZ
306B: cd 21 39    CALL $3921
306E: cd ac 39    CALL $39AC
3071: c9          RET
3072: cd 86 35    CALL $3586
3075: 57          MOV  D,A
3076: 3a 2a 5f    LDA  $5F2A
3079: a7          ANA  A
307A: ca 88 30    JZ   $3088
307D: cd 5f 43    CALL $435F
3080: cd c9 38    CALL $38C9
3083: 15          DCR  D
3084: c2 7d 30    JNZ  $307D
3087: c9          RET
3088: cd 21 39    CALL $3921
308B: cd 68 38    CALL $3868
308E: c8          RZ
308F: cd b2 3b    CALL $3BB2
3092: d8          RC
3093: 15          DCR  D
3094: c2 8b 30    JNZ  $308B
3097: c3 0a 39    JMP  $390A
309A: cd 86 35    CALL $3586
309D: 47          MOV  B,A
309E: cd d7 38    CALL $38D7
30A1: cd a8 30    CALL $30A8
30A4: cd c9 38    CALL $38C9
30A7: c9          RET
30A8: e5          PUSH H
30A9: c5          PUSH B
30AA: cd b4 30    CALL $30B4
30AD: c1          POP  B
30AE: 05          DCR  B
30AF: c2 a9 30    JNZ  $30A9
30B2: e1          POP  H
30B3: c9          RET
30B4: 3a 38 5f    LDA  $5F38
30B7: a7          ANA  A
30B8: c2 f2 30    JNZ  $30F2
30BB: cd d7 31    CALL $31D7
30BE: d8          RC
30BF: cd da 30    CALL $30DA
30C2: 3a a9 58    LDA  $58A9
30C5: 6f          MOV  L,A
30C6: cd 81 38    CALL $3881
30C9: 3d          DCR  A
30CA: 5f          MOV  E,A
30CB: 26 5a       MVI  H,$5A
30CD: 2c          INR  L
30CE: 7e          MOV  A,M
30CF: 2d          DCR  L
30D0: 77          MOV  M,A
30D1: 2c          INR  L
30D2: 7d          MOV  A,L
30D3: bb          CMP  E
30D4: c2 cd 30    JNZ  $30CD
30D7: 36 00       MVI  M,$00
30D9: c9          RET
30DA: 3a 24 5f    LDA  $5F24
30DD: a7          ANA  A
30DE: 3a 25 5f    LDA  $5F25
30E1: ca eb 30    JZ   $30EB
30E4: a7          ANA  A
30E5: ca ee 00    JZ   $00EE
30E8: c2 f4 00    JNZ  $00F4
30EB: a7          ANA  A
30EC: ca f1 00    JZ   $00F1
30EF: c2 f7 00    JNZ  $00F7
30F2: cd 21 39    CALL $3921
30F5: 24          INR  H
30F6: 3a 2a 5f    LDA  $5F2A
30F9: a7          ANA  A
30FA: cc ca 3b    CZ   $3BCA
30FD: d8          RC
30FE: 3a a9 58    LDA  $58A9
3101: 57          MOV  D,A
3102: cd 81 38    CALL $3881
3105: 4f          MOV  C,A
3106: 3a aa 58    LDA  $58AA
3109: b9          CMP  C
310A: ca 21 31    JZ   $3121
310D: 62          MOV  H,D
310E: cd 6d 3d    CALL $3D6D
3111: c5          PUSH B
3112: cd da 30    CALL $30DA
3115: c1          POP  B
3116: 61          MOV  H,C
3117: 51          MOV  D,C
3118: 15          DCR  D
3119: cd 5b 3d    CALL $3D5B
311C: 21 a9 58    LXI  H,$58A9
311F: 34          INR  M
3120: c9          RET
3121: cd d7 31    CALL $31D7
3124: d8          RC
3125: 26 01       MVI  H,$01
3127: 06 01       MVI  B,$01
3129: cd 95 3c    CALL $3C95
312C: cd bf 30    CALL $30BF
312F: c9          RET
3130: cd 86 35    CALL $3586
3133: 47          MOV  B,A
3134: cd d7 38    CALL $38D7
3137: cd 4b 31    CALL $314B
313A: 3a 2a 5f    LDA  $5F2A
313D: a7          ANA  A
313E: c2 c9 38    JNZ  $38C9
3141: cd 21 39    CALL $3921
3144: cd ea 3b    CALL $3BEA
3147: d4 0a 39    CNC  $390A
314A: c9          RET
314B: e5          PUSH H
314C: c5          PUSH B
314D: cd 57 31    CALL $3157
3150: c1          POP  B
3151: 05          DCR  B
3152: c2 4c 31    JNZ  $314C
3155: e1          POP  H
3156: c9          RET
3157: 3a 38 5f    LDA  $5F38
315A: a7          ANA  A
315B: c2 a9 31    JNZ  $31A9
315E: cd d7 31    CALL $31D7
3161: d8          RC
3162: cd 7d 31    CALL $317D
3165: 3a a9 58    LDA  $58A9
3168: 5f          MOV  E,A
3169: cd 81 38    CALL $3881
316C: 3d          DCR  A
316D: 6f          MOV  L,A
316E: 26 5a       MVI  H,$5A
3170: 2d          DCR  L
3171: 7e          MOV  A,M
3172: 2c          INR  L
3173: 77          MOV  M,A
3174: 2d          DCR  L
3175: 7d          MOV  A,L
3176: bb          CMP  E
3177: c2 70 31    JNZ  $3170
317A: 36 00       MVI  M,$00
317C: c9          RET
317D: 3a 24 5f    LDA  $5F24
3180: a7          ANA  A
3181: 3a 25 5f    LDA  $5F25
3184: ca 8e 31    JZ   $318E
3187: a7          ANA  A
3188: ca fa 00    JZ   $00FA
318B: c3 00 01    JMP  $0100
318E: a7          ANA  A
318F: c2 03 01    JNZ  $0103
3192: d5          PUSH D
3193: e5          PUSH H
3194: 11 01 19    LXI  D,$1901
3197: 21 01 1a    LXI  H,$1A01
319A: 3e 0f       MVI  A,$0F
319C: cd 4e 01    CALL $014E
319F: cd fd 00    CALL $00FD
31A2: 97          SUB  A
31A3: cd 4e 01    CALL $014E
31A6: e1          POP  H
31A7: d1          POP  D
31A8: c9          RET
31A9: cd 81 38    CALL $3881
31AC: 3d          DCR  A
31AD: 67          MOV  H,A
31AE: 3a a9 58    LDA  $58A9
31B1: 3d          DCR  A
31B2: ca c6 31    JZ   $31C6
31B5: 54          MOV  D,H
31B6: cd 6d 3d    CALL $3D6D
31B9: cd 7d 31    CALL $317D
31BC: 21 a9 58    LXI  H,$58A9
31BF: 35          DCR  M
31C0: 66          MOV  H,M
31C1: 54          MOV  D,H
31C2: cd 5b 3d    CALL $3D5B
31C5: c9          RET
31C6: cd d7 31    CALL $31D7
31C9: d8          RC
31CA: 3a aa 58    LDA  $58AA
31CD: 57          MOV  D,A
31CE: 06 01       MVI  B,$01
31D0: cd 6d 3c    CALL $3C6D
31D3: cd 62 31    CALL $3162
31D6: c9          RET
31D7: 3a 2a 5f    LDA  $5F2A
31DA: a7          ANA  A
31DB: 37          STC
31DC: c8          RZ
31DD: 3a 23 5f    LDA  $5F23
31E0: a7          ANA  A
31E1: 37          STC
31E2: c0          RNZ
31E3: 3f          CMC
31E4: c9          RET
31E5: cd 86 35    CALL $3586
31E8: 47          MOV  B,A
31E9: 3a 60 58    LDA  $5860
31EC: 4f          MOV  C,A
31ED: 3a a9 58    LDA  $58A9
31F0: 81          ADD  C
31F1: fe c8       CPI  $C8
31F3: d2 fa 31    JNC  $31FA
31F6: 05          DCR  B
31F7: c2 f0 31    JNZ  $31F0
31FA: 47          MOV  B,A
31FB: 3a aa 58    LDA  $58AA
31FE: 91          SUB  C
31FF: b8          CMP  B
3200: d2 39 32    JNC  $3239
3203: 47          MOV  B,A
3204: 3a 38 5f    LDA  $5F38
3207: a7          ANA  A
3208: c2 39 32    JNZ  $3239
320B: 3a a5 58    LDA  $58A5
320E: 47          MOV  B,A
320F: 3e 01       MVI  A,$01
3211: 05          DCR  B
3212: ca 19 32    JZ   $3219
3215: 81          ADD  C
3216: c3 11 32    JMP  $3211
3219: 47          MOV  B,A
321A: c3 39 32    JMP  $3239
321D: cd 86 35    CALL $3586
3220: 47          MOV  B,A
3221: 3a 60 58    LDA  $5860
3224: 4f          MOV  C,A
3225: 3a a9 58    LDA  $58A9
3228: 91          SUB  C
3229: da 36 32    JC   $3236
322C: ca 36 32    JZ   $3236
322F: 05          DCR  B
3230: c2 28 32    JNZ  $3228
3233: c3 38 32    JMP  $3238
3236: 3e 01       MVI  A,$01
3238: 47          MOV  B,A
3239: 3a a5 58    LDA  $58A5
323C: fe 01       CPI  $01
323E: c8          RZ
323F: cd d7 38    CALL $38D7
3242: 3a a9 58    LDA  $58A9
3245: 4f          MOV  C,A
3246: cd 3b 3d    CALL $3D3B
3249: 78          MOV  A,B
324A: cd 17 3d    CALL $3D17
324D: 3a 2a 5f    LDA  $5F2A
3250: a7          ANA  A
3251: c2 c9 38    JNZ  $38C9
3254: 3a a9 58    LDA  $58A9
3257: 67          MOV  H,A
3258: 2e 01       MVI  L,$01
325A: cd ca 3b    CALL $3BCA
325D: d2 f9 38    JNC  $38F9
3260: 79          MOV  A,C
3261: cd 17 3d    CALL $3D17
3264: c9          RET
3265: cd 78 35    CALL $3578
3268: a7          ANA  A
3269: c0          RNZ
326A: cd 74 40    CALL $4074
326D: 3a 3a 5f    LDA  $5F3A
3270: a7          ANA  A
3271: c2 81 32    JNZ  $3281
3274: 3a a5 58    LDA  $58A5
3277: c6 30       ADI  $30
3279: cd a8 40    CALL $40A8
327C: 3e 63       MVI  A,$63
327E: c3 a8 40    JMP  $40A8
3281: cd af 00    CALL $00AF
3284: cd a8 40    CALL $40A8
3287: cd a0 00    CALL $00A0
328A: cd a8 40    CALL $40A8
328D: c3 7c 32    JMP  $327C
3290: cd 83 35    CALL $3583
3293: 67          MOV  H,A
3294: c3 b0 2e    JMP  $2EB0
3297: 3a 2a 5f    LDA  $5F2A
329A: a7          ANA  A
329B: c8          RZ
329C: cd 78 35    CALL $3578
329F: a7          ANA  A
32A0: ca 84 43    JZ   $4384
32A3: fe 02       CPI  $02
32A5: ca 8c 43    JZ   $438C
32A8: fe 03       CPI  $03
32AA: ca 8c 43    JZ   $438C
32AD: c9          RET
32AE: 0e 00       MVI  C,$00
32B0: 3a 25 5f    LDA  $5F25
32B3: f5          PUSH PSW
32B4: cd 96 35    CALL $3596
32B7: da 2d 33    JC   $332D
32BA: 57          MOV  D,A
32BB: 21 4d 33    LXI  H,$334D
32BE: 7e          MOV  A,M
32BF: 23          INX  H
32C0: fe ff       CPI  $FF
32C2: ca b4 32    JZ   $32B4
32C5: ba          CMP  D
32C6: ca ce 32    JZ   $32CE
32C9: 23          INX  H
32CA: 23          INX  H
32CB: c3 be 32    JMP  $32BE
32CE: d5          PUSH D
32CF: 5e          MOV  E,M
32D0: 23          INX  H
32D1: 7e          MOV  A,M
32D2: 16 00       MVI  D,$00
32D4: 21 00 5f    LXI  H,$5F00
32D7: 19          DAD  D
32D8: d1          POP  D
32D9: 5f          MOV  E,A
32DA: 79          MOV  A,C
32DB: a7          ANA  A
32DC: c2 e9 32    JNZ  $32E9
32DF: 7e          MOV  A,M
32E0: 3c          INR  A
32E1: bb          CMP  E
32E2: ca b4 32    JZ   $32B4
32E5: 34          INR  M
32E6: c3 f0 32    JMP  $32F0
32E9: 7e          MOV  A,M
32EA: a7          ANA  A
32EB: ca b4 32    JZ   $32B4
32EE: 36 00       MVI  M,$00
32F0: 7a          MOV  A,D
32F1: fe 35       CPI  $35
32F3: cc 3f 01    CZ   $013F
32F6: fe 37       CPI  $37
32F8: cc 3f 01    CZ   $013F
32FB: fe 44       CPI  $44
32FD: cc 3f 01    CZ   $013F
3300: fe 56       CPI  $56
3302: cc 3f 01    CZ   $013F
3305: fe 02       CPI  $02
3307: cc 2a 37    CZ   $372A
330A: fe 0c       CPI  $0C
330C: cc 2a 37    CZ   $372A
330F: fe 43       CPI  $43
3311: cc 4c 36    CZ   $364C
3314: fe 28       CPI  $28
3316: da b4 32    JC   $32B4
3319: fe 2c       CPI  $2C
331B: d2 b4 32    JNC  $32B4
331E: 3a 09 5f    LDA  $5F09
3321: 32 17 5f    STA  $5F17
3324: cd 28 43    CALL $4328
3327: cd 3c 01    CALL $013C
332A: c3 b4 32    JMP  $32B4
332D: 3a 25 5f    LDA  $5F25
3330: 47          MOV  B,A
3331: f1          POP  PSW
3332: b8          CMP  B
3333: c2 57 21    JNZ  $2157
3336: 3a 29 5f    LDA  $5F29
3339: 32 a8 59    STA  $59A8
333C: 3a a5 58    LDA  $58A5
333F: 3d          DCR  A
3340: c2 46 33    JNZ  $3346
3343: 32 38 5f    STA  $5F38
3346: cd 8a 36    CALL $368A
3349: cd 1c 45    CALL $451C
334C: c9          RET
334D: 02 39 02 07 28 02 0c 2a 03 10 2b 02 1f 21 02 20 DB $02,$39,$02,$07,$28,$02,$0C,$2A,$03,$10,$2B,$02,$1F,$21,$02,$20
335D: 20 02 23 27 02 24 22 02 27 25 02 28 2f 05 2a 0b DB $20,$02,$23,$27,$02,$24,$22,$02,$27,$25,$02,$28,$2F,$05,$2A,$0B
336D: 0c 2b 09 02 2f 23 02 35 14 02 36 1f 02 37 15 02 DB $0C,$2B,$09,$02,$2F,$23,$02,$35,$14,$02,$36,$1F,$02,$37,$15,$02
337D: 3c 24 02 43 36 03 44 0c 02 45 29 03 46 32 02 47 DB $3C,$24,$02,$43,$36,$03,$44,$0C,$02,$45,$29,$03,$46,$32,$02,$47
338D: 26 02 48 30 04 49 31 03 4a 33 02 4b 37 03 4c 38 DB $26,$02,$48,$30,$04,$49,$31,$03,$4A,$33,$02,$4B,$37,$03,$4C,$38
339D: 02 4d 1c 02 4e 19 03 53 2d 02 56 1b 02 57 00 02 DB $02,$4D,$1C,$02,$4E,$19,$03,$53,$2D,$02,$56,$1B,$02,$57,$00,$02
33AD: 5e 2e 10 5f 1d 02 60 1e 02 63 3a 02 ff          DB $5E,$2E,$10,$5F,$1D,$02,$60,$1E,$02,$63,$3A,$02,$FF
33BA: 3a 29 5f    LDA  $5F29
33BD: fe 02       CPI  $02
33BF: c8          RZ
33C0: cd 78 35    CALL $3578
33C3: a7          ANA  A
33C4: ca 53 41    JZ   $4153
33C7: fe 08       CPI  $08
33C9: ca 5f 41    JZ   $415F
33CC: fe 05       CPI  $05
33CE: c0          RNZ
33CF: 3a 2a 5f    LDA  $5F2A
33D2: a7          ANA  A
33D3: c8          RZ
33D4: cd 0b 42    CALL $420B
33D7: d8          RC
33D8: 3e 01       MVI  A,$01
33DA: 32 98 58    STA  $5898
33DD: cd 46 34    CALL $3446
33E0: fe 1b       CPI  $1B
33E2: ca f1 33    JZ   $33F1
33E5: fe 9b       CPI  $9B
33E7: ca 22 34    JZ   $3422
33EA: 7a          MOV  A,D
33EB: cd 2b 42    CALL $422B
33EE: c3 dd 33    JMP  $33DD
33F1: cd 46 34    CALL $3446
33F4: fe 5b       CPI  $5B
33F6: 3e 1b       MVI  A,$1B
33F8: c4 2b 42    CNZ  $422B
33FB: c2 ea 33    JNZ  $33EA
33FE: cd 46 34    CALL $3446
3401: fe 34       CPI  $34
3403: 3e 1b       MVI  A,$1B
3405: c4 2b 42    CNZ  $422B
3408: 3e 5b       MVI  A,$5B
340A: c4 2b 42    CNZ  $422B
340D: c2 ea 33    JNZ  $33EA
3410: cd 46 34    CALL $3446
3413: fe 69       CPI  $69
3415: 3e 1b       MVI  A,$1B
3417: c4 2b 42    CNZ  $422B
341A: 3e 5b       MVI  A,$5B
341C: c4 2b 42    CNZ  $422B
341F: c3 39 34    JMP  $3439
3422: cd 46 34    CALL $3446
3425: fe 34       CPI  $34
3427: 3e 9b       MVI  A,$9B
3429: c4 2b 42    CNZ  $422B
342C: c2 ea 33    JNZ  $33EA
342F: cd 46 34    CALL $3446
3432: fe 69       CPI  $69
3434: 3e 9b       MVI  A,$9B
3436: c4 2b 42    CNZ  $422B
3439: 3e 34       MVI  A,$34
343B: c4 2b 42    CNZ  $422B
343E: c2 ea 33    JNZ  $33EA
3441: 97          SUB  A
3442: 32 98 58    STA  $5898
3445: c9          RET
3446: cd aa 35    CALL $35AA
3449: 57          MOV  D,A
344A: c9          RET
344B: 0e 01       MVI  C,$01
344D: c3 b0 32    JMP  $32B0
3450: 1e 00       MVI  E,$00
3452: cd 96 35    CALL $3596
3455: da 64 34    JC   $3464
3458: 21 6e 34    LXI  H,$346E
345B: cd 33 38    CALL $3833
345E: d8          RC
345F: b3          ORA  E
3460: 5f          MOV  E,A
3461: c3 52 34    JMP  $3452
3464: 3a 2a 5f    LDA  $5F2A
3467: a7          ANA  A
3468: c8          RZ
3469: 7b          MOV  A,E
346A: cd fc 37    CALL $37FC
346D: c9          RET
346E: 00 00 02 02 04 04 05 08 07 01 08 0f 32 0e ff    DB $00,$00,$02,$02,$04,$04,$05,$08,$07,$01,$08,$0F,$32,$0E,$FF
347D: cd 78 35    CALL $3578
3480: fe 06       CPI  $06
3482: c0          RNZ
3483: 3a 38 5f    LDA  $5F38
3486: a7          ANA  A
3487: cc 97 00    CZ   $0097
348A: c4 21 39    CNZ  $3921
348D: cd a0 00    CALL $00A0
3490: e6 0f       ANI  $0F
3492: fe 0e       CPI  $0E
3494: c2 35 40    JNZ  $4035
3497: 7d          MOV  A,L
3498: 0f          RRC
3499: 6f          MOV  L,A
349A: c3 35 40    JMP  $4035
349D: 97          SUB  A
349E: 32 9a 58    STA  $589A
34A1: 11 00 00    LXI  D,$0000
34A4: cd 96 35    CALL $3596
34A7: da de 34    JC   $34DE
34AA: fe 05       CPI  $05
34AC: dc ec 34    CC   $34EC
34AF: fe 08       CPI  $08
34B1: cc ec 34    CZ   $34EC
34B4: fe 1d       CPI  $1D
34B6: d2 a4 34    JNC  $34A4
34B9: fe 19       CPI  $19
34BB: da c0 34    JC   $34C0
34BE: d6 0f       SUI  $0F
34C0: fe 0e       CPI  $0E
34C2: d2 a4 34    JNC  $34A4
34C5: 21 f2 34    LXI  H,$34F2
34C8: d5          PUSH D
34C9: 87          ADD  A
34CA: 87          ADD  A
34CB: 5f          MOV  E,A
34CC: 16 00       MVI  D,$00
34CE: 19          DAD  D
34CF: d1          POP  D
34D0: 7a          MOV  A,D
34D1: a6          ANA  M
34D2: 23          INX  H
34D3: b6          ORA  M
34D4: 57          MOV  D,A
34D5: 23          INX  H
34D6: 7b          MOV  A,E
34D7: a6          ANA  M
34D8: 23          INX  H
34D9: b6          ORA  M
34DA: 5f          MOV  E,A
34DB: c3 a4 34    JMP  $34A4
34DE: 3a 9a 58    LDA  $589A
34E1: a7          ANA  A
34E2: c2 e9 34    JNZ  $34E9
34E5: 7a          MOV  A,D
34E6: f6 70       ORI  $70
34E8: 57          MOV  D,A
34E9: c3 d0 3a    JMP  $3AD0
34EC: 3c          INR  A
34ED: 32 9a 58    STA  $589A
34F0: 3d          DCR  A
34F1: c9          RET
34F2: 8f 70 e0 00 80 00 e0 00 ff 10 e0 00 ff 20 e0 00 DB $8F,$70,$E0,$00,$80,$00,$E0,$00,$FF,$10,$E0,$00,$FF,$20,$E0,$00
3502: ff 40 e0 00 ff 00 c0 20 ff 00 20 c0 ff 80 e0 00 DB $FF,$40,$E0,$00,$FF,$00,$C0,$20,$FF,$00,$20,$C0,$FF,$80,$E0,$00
3512: 80 02 e0 00 ff 00 20 80 ff 01 e0 00 ff 08 e0 00 DB $80,$02,$E0,$00,$FF,$00,$20,$80,$FF,$01,$E0,$00,$FF,$08,$E0,$00
3522: ff 04 e0 00 ff 02 e0 00                         DB $FF,$04,$E0,$00,$FF,$02,$E0,$00
352A: 21 76 58    LXI  H,$5876
352D: 04          INR  B
352E: 05          DCR  B
352F: c0          RNZ
3530: 21 65 58    LXI  H,$5865
3533: c9          RET
3534: cd 2a 35    CALL $352A
3537: fe 3b       CPI  $3B
3539: ca 5f 35    JZ   $355F
353C: d6 30       SUI  $30
353E: d8          RC
353F: fe 0a       CPI  $0A
3541: 3f          CMC
3542: d8          RC
3543: 57          MOV  D,A
3544: 23          INX  H
3545: 7e          MOV  A,M
3546: fe ff       CPI  $FF
3548: c2 44 35    JNZ  $3544
354B: 2b          DCX  H
354C: 7e          MOV  A,M
354D: fe 1a       CPI  $1A
354F: 3f          CMC
3550: d8          RC
3551: 87          ADD  A
3552: 5f          MOV  E,A
3553: 87          ADD  A
3554: 87          ADD  A
3555: 83          ADD  E
3556: 82          ADD  D
3557: d8          RC
3558: fe fe       CPI  $FE
355A: 3f          CMC
355B: d8          RC
355C: 77          MOV  M,A
355D: a7          ANA  A
355E: c9          RET
355F: f5          PUSH PSW
3560: 16 10       MVI  D,$10
3562: 15          DCR  D
3563: ca 75 35    JZ   $3575
3566: 7e          MOV  A,M
3567: 23          INX  H
3568: fe ff       CPI  $FF
356A: c2 62 35    JNZ  $3562
356D: 36 ff       MVI  M,$FF
356F: 2b          DCX  H
3570: 36 00       MVI  M,$00
3572: f1          POP  PSW
3573: a7          ANA  A
3574: c9          RET
3575: f1          POP  PSW
3576: 37          STC
3577: c9          RET
3578: e5          PUSH H
3579: cd 2a 35    CALL $352A
357C: 7e          MOV  A,M
357D: e1          POP  H
357E: fe ff       CPI  $FF
3580: c0          RNZ
3581: 97          SUB  A
3582: c9          RET
3583: cd d7 38    CALL $38D7
3586: e5          PUSH H
3587: cd 2a 35    CALL $352A
358A: 7e          MOV  A,M
358B: e1          POP  H
358C: fe ff       CPI  $FF
358E: ca 93 35    JZ   $3593
3591: a7          ANA  A
3592: c0          RNZ
3593: 3e 01       MVI  A,$01
3595: c9          RET
3596: e5          PUSH H
3597: cd 2a 35    CALL $352A
359A: 7e          MOV  A,M
359B: 36 fe       MVI  M,$FE
359D: 23          INX  H
359E: fe fe       CPI  $FE
35A0: ca 9a 35    JZ   $359A
35A3: e1          POP  H
35A4: fe ff       CPI  $FF
35A6: 37          STC
35A7: c8          RZ
35A8: a7          ANA  A
35A9: c9          RET
35AA: 78          MOV  A,B
35AB: a7          ANA  A
35AC: ca c6 35    JZ   $35C6
35AF: 2a 55 58    LHLD $5855
35B2: 22 5b 58    SHLD $585B
35B5: 21 be 35    LXI  H,$35BE
35B8: 22 55 58    SHLD $5855
35BB: c3 9e 22    JMP  $229E
35BE: e1 2a 5b 58 22 55 58 c9                         DB $E1,$2A,$5B,$58,$22,$55,$58,$C9
35C6: 2a 53 58    LHLD $5853
35C9: 22 59 58    SHLD $5859
35CC: 21 d5 35    LXI  H,$35D5
35CF: 22 53 58    SHLD $5853
35D2: c3 9e 22    JMP  $229E
35D5: e1 2a 59 58 22 53 58 c9                         DB $E1,$2A,$59,$58,$22,$53,$58,$C9
35DD: cd aa 35    CALL $35AA
35E0: fe 9c       CPI  $9C
35E2: c8          RZ
35E3: fe 1b       CPI  $1B
35E5: 37          STC
35E6: 3f          CMC
35E7: c0          RNZ
35E8: cd aa 35    CALL $35AA
35EB: fe 5c       CPI  $5C
35ED: c8          RZ
35EE: 37          STC
35EF: c9          RET
35F0: f3          DI
35F1: cd 72 01    CALL $0172
35F4: 3e 11       MVI  A,$11
35F6: 32 9c 58    STA  $589C
35F9: fb          EI
35FA: 3a 09 5f    LDA  $5F09
35FD: 32 17 5f    STA  $5F17
3600: cd 28 43    CALL $4328
3603: cd 3c 01    CALL $013C
3606: cd 4c 36    CALL $364C
3609: cd b0 54    CALL $54B0
360C: cd 3f 01    CALL $013F
360F: 3a 34 5f    LDA  $5F34
3612: a7          ANA  A
3613: 3e 30       MVI  A,$30
3615: c4 19 38    CNZ  $3819
3618: 3a 02 5f    LDA  $5F02
361B: 21 48 36    LXI  H,$3648
361E: 06 00       MVI  B,$00
3620: 4f          MOV  C,A
3621: 09          DAD  B
3622: 7e          MOV  A,M
3623: 32 3c 5e    STA  $5E3C
3626: 3a 29 5f    LDA  $5F29
3629: 32 a8 59    STA  $59A8
362C: 3a a5 58    LDA  $58A5
362F: 3d          DCR  A
3630: c2 36 36    JNZ  $3636
3633: 32 38 5f    STA  $5F38
3636: cd 8a 36    CALL $368A
3639: cd 2a 37    CALL $372A
363C: 3a 03 5f    LDA  $5F03
363F: fe 04       CPI  $04
3641: c8          RZ
3642: 3e 00       MVI  A,$00
3644: 32 00 5f    STA  $5F00
3647: c9          RET
3648: bf 9f 77 4f                                     DB $BF,$9F,$77,$4F
364C: f5          PUSH PSW
364D: 3a 0e 5f    LDA  $5F0E
3650: a7          ANA  A
3651: ca 6a 36    JZ   $366A
3654: 3a 36 5f    LDA  $5F36
3657: fe 02       CPI  $02
3659: c2 60 36    JNZ  $3660
365C: 97          SUB  A
365D: 32 36 5f    STA  $5F36
3660: 21 2c 5f    LXI  H,$5F2C
3663: 7e          MOV  A,M
3664: 36 02       MVI  M,$02
3666: be          CMP  M
3667: c4 22 54    CNZ  $5422
366A: 3a 36 5f    LDA  $5F36
366D: 21 23 48    LXI  H,$4823
3670: fe 02       CPI  $02
3672: c2 82 36    JNZ  $3682
3675: 3a 2c 5f    LDA  $5F2C
3678: fe 02       CPI  $02
367A: c2 60 36    JNZ  $3660
367D: 21 15 48    LXI  H,$4815
3680: 3e 01       MVI  A,$01
3682: 22 24 5c    SHLD $5C24
3685: 32 13 5f    STA  $5F13
3688: f1          POP  PSW
3689: c9          RET
368A: 3a a6 58    LDA  $58A6
368D: 4f          MOV  C,A
368E: 3a 2a 5f    LDA  $5F2A
3691: b9          CMP  C
3692: c8          RZ
3693: a7          ANA  A
3694: c2 23 37    JNZ  $3723
3697: cd 3b 3d    CALL $3D3B
369A: cd 6e 38    CALL $386E
369D: 67          MOV  H,A
369E: 2e 01       MVI  L,$01
36A0: cd ca 3b    CALL $3BCA
36A3: da 1a 37    JC   $371A
36A6: eb          XCHG
36A7: eb          XCHG
36A8: 3a aa 58    LDA  $58AA
36AB: bc          CMP  H
36AC: ca 0c 37    JZ   $370C
36AF: cd 20 3c    CALL $3C20
36B2: e6 70       ANI  $70
36B4: ca a7 36    JZ   $36A7
36B7: 79          MOV  A,C
36B8: e6 20       ANI  $20
36BA: ca cd 36    JZ   $36CD
36BD: 7c          MOV  A,H
36BE: ba          CMP  D
36BF: ca cd 36    JZ   $36CD
36C2: 3c          INR  A
36C3: ba          CMP  D
36C4: c2 1a 37    JNZ  $371A
36C7: 7b          MOV  A,E
36C8: fe 01       CPI  $01
36CA: c2 1a 37    JNZ  $371A
36CD: 79          MOV  A,C
36CE: fe 0e       CPI  $0E
36D0: ca a7 36    JZ   $36A7
36D3: cd c9 01    CALL $01C9
36D6: ca a7 36    JZ   $36A7
36D9: 7c          MOV  A,H
36DA: ba          CMP  D
36DB: ca ec 36    JZ   $36EC
36DE: 7d          MOV  A,L
36DF: fe 01       CPI  $01
36E1: c2 ec 36    JNZ  $36EC
36E4: 3a a5 58    LDA  $58A5
36E7: fe 01       CPI  $01
36E9: c2 02 37    JNZ  $3702
36EC: 79          MOV  A,C
36ED: e6 0f       ANI  $0F
36EF: 47          MOV  B,A
36F0: 3a a5 58    LDA  $58A5
36F3: fe 01       CPI  $01
36F5: 78          MOV  A,B
36F6: cc 4b 01    CZ   $014B
36F9: c4 b9 3d    CNZ  $3DB9
36FC: cd 5f 38    CALL $385F
36FF: c3 d3 36    JMP  $36D3
3702: 79          MOV  A,C
3703: cd d9 3d    CALL $3DD9
3706: 24          INR  H
3707: 2e 01       MVI  L,$01
3709: c3 d3 36    JMP  $36D3
370C: 3e 01       MVI  A,$01
370E: cd 17 3d    CALL $3D17
3711: cd 67 00    CALL $0067
3714: cd 6d 37    CALL $376D
3717: c3 23 37    JMP  $3723
371A: 3a a6 58    LDA  $58A6
371D: 32 2a 5f    STA  $5F2A
3720: cd 2a 37    CALL $372A
3723: 3a 2a 5f    LDA  $5F2A
3726: 32 a6 58    STA  $58A6
3729: c9          RET
372A: f5          PUSH PSW
372B: 21 d2 24    LXI  H,$24D2
372E: 11 53 25    LXI  D,$2553
3731: 3a 2a 5f    LDA  $5F2A
3734: fe 01       CPI  $01
3736: ca 4a 37    JZ   $374A
3739: 21 40 24    LXI  H,$2440
373C: da 4a 37    JC   $374A
373F: fe 02       CPI  $02
3741: ca 4a 37    JZ   $374A
3744: 21 d2 24    LXI  H,$24D2
3747: 11 74 25    LXI  D,$2574
374A: 3a 39 5f    LDA  $5F39
374D: a7          ANA  A
374E: 3a 14 5f    LDA  $5F14
3751: ca 5a 37    JZ   $375A
3754: 2f          CMA
3755: e6 01       ANI  $01
3757: 21 6c 37    LXI  H,$376C
375A: a7          ANA  A
375B: cc 58 00    CZ   $0058
375E: c4 5b 00    CNZ  $005B
3761: da 5b 37    JC   $375B
3764: 22 53 58    SHLD $5853
3767: eb          XCHG
3768: 22 55 58    SHLD $5855
376B: f1          POP  PSW
376C: c9          RET
376D: cd 21 39    CALL $3921
3770: cd ca 3b    CALL $3BCA
3773: d2 7d 37    JNC  $377D
3776: 2a a7 58    LHLD $58A7
3779: 22 16 5e    SHLD $5E16
377C: c9          RET
377D: cd f9 38    CALL $38F9
3780: cd 20 3c    CALL $3C20
3783: 32 b3 58    STA  $58B3
3786: 79          MOV  A,C
3787: 32 b4 58    STA  $58B4
378A: 22 af 58    SHLD $58AF
378D: eb          XCHG
378E: 22 b1 58    SHLD $58B1
3791: eb          XCHG
3792: 3a b4 58    LDA  $58B4
3795: 4f          MOV  C,A
3796: e6 0f       ANI  $0F
3798: cd fc 37    CALL $37FC
379B: 79          MOV  A,C
379C: e6 80       ANI  $80
379E: ca bb 37    JZ   $37BB
37A1: 79          MOV  A,C
37A2: 06 20       MVI  B,$20
37A4: e6 40       ANI  $40
37A6: ca ab 37    JZ   $37AB
37A9: 06 30       MVI  B,$30
37AB: cd c9 01    CALL $01C9
37AE: ca bb 37    JZ   $37BB
37B1: 78          MOV  A,B
37B2: cd 8e 3d    CALL $3D8E
37B5: cd 5f 38    CALL $385F
37B8: c3 ab 37    JMP  $37AB
37BB: 79          MOV  A,C
37BC: e6 20       ANI  $20
37BE: ca c8 37    JZ   $37C8
37C1: eb          XCHG
37C2: cd 68 38    CALL $3868
37C5: cd 18 39    CALL $3918
37C8: 21 40 24    LXI  H,$2440
37CB: 3a b3 58    LDA  $58B3
37CE: e6 04       ANI  $04
37D0: ca d6 37    JZ   $37D6
37D3: 21 d2 24    LXI  H,$24D2
37D6: 22 53 58    SHLD $5853
37D9: 2a 16 5e    LHLD $5E16
37DC: 22 a7 58    SHLD $58A7
37DF: 2a b7 58    LHLD $58B7
37E2: 22 b5 58    SHLD $58B5
37E5: 97          SUB  A
37E6: 32 b9 58    STA  $58B9
37E9: c9          RET
37EA: 2a ad 58    LHLD $58AD
37ED: 36 01       MVI  M,$01
37EF: 23          INX  H
37F0: 36 01       MVI  M,$01
37F2: 23          INX  H
37F3: 36 70       MVI  M,$70
37F5: 23          INX  H
37F6: 36 00       MVI  M,$00
37F8: 23          INX  H
37F9: 36 ff       MVI  M,$FF
37FB: c9          RET
37FC: 32 9f 58    STA  $589F
37FF: 3a 9f 58    LDA  $589F
3802: fe 0e       CPI  $0E
3804: cc a6 00    CZ   $00A6
3807: c4 a3 00    CNZ  $00A3
380A: c9          RET
380B: 3a 1f 5f    LDA  $5F1F
380E: a7          ANA  A
380F: c0          RNZ
3810: 3a f9 5d    LDA  $5DF9
3813: e6 06       ANI  $06
3815: ca 2d 29    JZ   $292D
3818: c9          RET
3819: cd 64 00    CALL $0064
381C: da 19 38    JC   $3819
381F: c9          RET
3820: fe 60       CPI  $60
3822: d8          RC
3823: fe 80       CPI  $80
3825: d0          RNC
3826: e6 5f       ANI  $5F
3828: c9          RET
3829: 36 00       MVI  M,$00
382B: 23          INX  H
382C: cd c9 01    CALL $01C9
382F: c2 29 38    JNZ  $3829
3832: c9          RET
; byte_pair_translation
3833: 57          MOV  D,A
3834: 7e          MOV  A,M
3835: fe ff       CPI  $FF
3837: 7a          MOV  A,D
3838: 37          STC
3839: c8          RZ
383A: be          CMP  M
383B: 23          INX  H
383C: 7e          MOV  A,M
383D: 23          INX  H
383E: c2 34 38    JNZ  $3834
3841: a7          ANA  A
3842: c9          RET
3843: f5          PUSH PSW
3844: c5          PUSH B
3845: e5          PUSH H
3846: 3a 2a 5f    LDA  $5F2A
3849: fe 02       CPI  $02
384B: c2 5b 38    JNZ  $385B
384E: 7d          MOV  A,L
384F: 6c          MOV  L,H
3850: 26 5a       MVI  H,$5A
3852: be          CMP  M
3853: ca 59 38    JZ   $3859
3856: d2 5b 38    JNC  $385B
3859: 36 ff       MVI  M,$FF
385B: e1          POP  H
385C: c1          POP  B
385D: f1          POP  PSW
385E: c9          RET
385F: 2c          INR  L
3860: 7d          MOV  A,L
3861: fe 51       CPI  $51
3863: d8          RC
3864: 2e 01       MVI  L,$01
3866: 24          INR  H
3867: c9          RET
3868: 2d          DCR  L
3869: c0          RNZ
386A: 2e 50       MVI  L,$50
386C: 25          DCR  H
386D: c9          RET
386E: 3a 38 5f    LDA  $5F38
3871: a7          ANA  A
3872: 3e 01       MVI  A,$01
3874: c0          RNZ
3875: 3a a9 58    LDA  $58A9
3878: c9          RET
3879: 3a 38 5f    LDA  $5F38
387C: a7          ANA  A
387D: 3a aa 58    LDA  $58AA
3880: c0          RNZ
3881: c5          PUSH B
3882: 3a a9 58    LDA  $58A9
3885: 47          MOV  B,A
3886: 3a 60 58    LDA  $5860
3889: 80          ADD  B
388A: c1          POP  B
388B: c9          RET
388C: 3a 95 58    LDA  $5895
388F: a7          ANA  A
3890: 37          STC
3891: c0          RNZ
3892: 3a 94 58    LDA  $5894
3895: a7          ANA  A
3896: c4 94 48    CNZ  $4894
3899: a7          ANA  A
389A: c9          RET
389B: 5d          MOV  E,L
389C: 2e 01       MVI  L,$01
389E: cd 9e 3d    CALL $3D9E
38A1: 24          INR  H
38A2: fe 0e       CPI  $0E
38A4: 16 28       MVI  D,$28
38A6: ca ab 38    JZ   $38AB
38A9: 16 50       MVI  D,$50
38AB: 7b          MOV  A,E
38AC: 92          SUB  D
38AD: 6f          MOV  L,A
38AE: d8          RC
38AF: a7          ANA  A
38B0: c0          RNZ
38B1: 37          STC
38B2: c9          RET
38B3: 3a b9 58    LDA  $58B9
38B6: a7          ANA  A
38B7: c8          RZ
38B8: e5          PUSH H
38B9: 2a b5 58    LHLD $58B5
38BC: 23          INX  H
38BD: 23          INX  H
38BE: 23          INX  H
38BF: 7e          MOV  A,M
38C0: f6 10       ORI  $10
38C2: 77          MOV  M,A
38C3: 97          SUB  A
38C4: 32 b9 58    STA  $58B9
38C7: e1          POP  H
38C8: c9          RET
38C9: 3a 60 58    LDA  $5860
38CC: bc          CMP  H
38CD: d8          RC
38CE: e5          PUSH H
38CF: cd e7 38    CALL $38E7
38D2: cd 91 00    CALL $0091
38D5: e1          POP  H
38D6: c9          RET
38D7: 2a 16 5e    LHLD $5E16
38DA: cd 48 01    CALL $0148
38DD: e6 0f       ANI  $0F
38DF: fe 0e       CPI  $0E
38E1: c0          RNZ
38E2: 7d          MOV  A,L
38E3: 3c          INR  A
38E4: 0f          RRC
38E5: 6f          MOV  L,A
38E6: c9          RET
38E7: cd 48 01    CALL $0148
38EA: e6 0f       ANI  $0F
38EC: fe 0e       CPI  $0E
38EE: c0          RNZ
38EF: 7d          MOV  A,L
38F0: 07          RLC
38F1: 3d          DCR  A
38F2: 6f          MOV  L,A
38F3: fe 50       CPI  $50
38F5: d8          RC
38F6: 2e 4f       MVI  L,$4F
38F8: c9          RET
38F9: cd 18 39    CALL $3918
38FC: d0          RNC
38FD: cd 6a 00    CALL $006A
3900: c5          PUSH B
3901: 06 01       MVI  B,$01
3903: cd a8 30    CALL $30A8
3906: c1          POP  B
3907: c3 f9 38    JMP  $38F9
390A: cd 18 39    CALL $3918
390D: d0          RNC
390E: c5          PUSH B
390F: 06 01       MVI  B,$01
3911: cd 4b 31    CALL $314B
3914: c1          POP  B
3915: c3 0a 39    JMP  $390A
3918: e5          PUSH H
3919: cd 1d 3e    CALL $3E1D
391C: d4 91 00    CNC  $0091
391F: e1          POP  H
3920: c9          RET
3921: 2a 16 5e    LHLD $5E16
3924: cd 3c 3e    CALL $3E3C
3927: c9          RET
3928: 2a 16 5e    LHLD $5E16
392B: eb          XCHG
392C: cd 86 35    CALL $3586
392F: 4f          MOV  C,A
3930: 3a 2a 5f    LDA  $5F2A
3933: a7          ANA  A
3934: ca 6a 39    JZ   $396A
3937: 3a 27 5f    LDA  $5F27
393A: a7          ANA  A
393B: ca 44 39    JZ   $3944
393E: cd 43 43    CALL $4343
3941: d2 48 39    JNC  $3948
3944: eb          XCHG
3945: 24          INR  H
3946: 2e 01       MVI  L,$01
3948: 59          MOV  E,C
3949: 16 00       MVI  D,$00
394B: cd a0 00    CALL $00A0
394E: e6 0f       ANI  $0F
3950: fe 0e       CPI  $0E
3952: 3e 02       MVI  A,$02
3954: c2 68 39    JNZ  $3968
3957: 7b          MOV  A,E
3958: 83          ADD  E
3959: 5f          MOV  E,A
395A: 7d          MOV  A,L
395B: fe 01       CPI  $01
395D: cc 68 38    CZ   $3868
3960: 7d          MOV  A,L
3961: e6 01       ANI  $01
3963: c4 68 38    CNZ  $3868
3966: 3e 01       MVI  A,$01
3968: a7          ANA  A
3969: c9          RET
396A: 3a b4 58    LDA  $58B4
396D: e6 20       ANI  $20
396F: c2 88 39    JNZ  $3988
3972: 2a b1 58    LHLD $58B1
3975: cd 1d 3e    CALL $3E1D
3978: 7a          MOV  A,D
3979: bc          CMP  H
397A: ca 81 39    JZ   $3981
397D: eb          XCHG
397E: 24          INR  H
397F: 2e 01       MVI  L,$01
3981: 59          MOV  E,C
3982: 16 00       MVI  D,$00
3984: 3e 01       MVI  A,$01
3986: a7          ANA  A
3987: c9          RET
3988: 2a af 58    LHLD $58AF
398B: cd 1d 3e    CALL $3E1D
398E: 59          MOV  E,C
398F: 16 00       MVI  D,$00
3991: 3e 01       MVI  A,$01
3993: 37          STC
3994: c9          RET
3995: 78          MOV  A,B
3996: a7          ANA  A
3997: 3a 64 58    LDA  $5864
399A: c4 78 35    CNZ  $3578
399D: a7          ANA  A
399E: cc 21 39    CZ   $3921
39A1: eb          XCHG
39A2: fe 01       CPI  $01
39A4: cc 21 39    CZ   $3921
39A7: eb          XCHG
39A8: fe 03       CPI  $03
39AA: 3f          CMC
39AB: c9          RET
39AC: 3a 2a 5f    LDA  $5F2A
39AF: a7          ANA  A
39B0: ca 0a 3a    JZ   $3A0A
39B3: cd 26 3b    CALL $3B26
39B6: 7c          MOV  A,H
39B7: ba          CMP  D
39B8: ca e0 39    JZ   $39E0
39BB: 7d          MOV  A,L
39BC: fe 01       CPI  $01
39BE: ca cf 39    JZ   $39CF
39C1: e5          PUSH H
39C2: d5          PUSH D
39C3: 54          MOV  D,H
39C4: 14          INR  D
39C5: 1e 01       MVI  E,$01
39C7: cd e0 39    CALL $39E0
39CA: d1          POP  D
39CB: e1          POP  H
39CC: 24          INR  H
39CD: 2e 01       MVI  L,$01
39CF: 7c          MOV  A,H
39D0: ba          CMP  D
39D1: ca dd 39    JZ   $39DD
39D4: 3e 02       MVI  A,$02
39D6: cd 66 3a    CALL $3A66
39D9: 24          INR  H
39DA: c3 cf 39    JMP  $39CF
39DD: 7b          MOV  A,E
39DE: bd          CMP  L
39DF: c8          RZ
39E0: e5          PUSH H
39E1: 2a 16 5e    LHLD $5E16
39E4: e3          XTHL
39E5: cd 43 38    CALL $3843
39E8: cd 1d 3e    CALL $3E1D
39EB: 22 16 5e    SHLD $5E16
39EE: eb          XCHG
39EF: cd 1d 3e    CALL $3E1D
39F2: cd a0 00    CALL $00A0
39F5: e6 0f       ANI  $0F
39F7: fe 0e       CPI  $0E
39F9: 3e 01       MVI  A,$01
39FB: ca 00 3a    JZ   $3A00
39FE: 3e 02       MVI  A,$02
3A00: 06 00       MVI  B,$00
3A02: cd 0c 01    CALL $010C
3A05: e1          POP  H
3A06: 22 16 5e    SHLD $5E16
3A09: c9          RET
3A0A: cd a6 00    CALL $00A6
3A0D: cd 14 3a    CALL $3A14
3A10: cd ff 37    CALL $37FF
3A13: c9          RET
3A14: 42          MOV  B,D
3A15: 4b          MOV  C,E
3A16: 3a aa 58    LDA  $58AA
3A19: bc          CMP  H
3A1A: c8          RZ
3A1B: c5          PUSH B
3A1C: e5          PUSH H
3A1D: cd 20 3c    CALL $3C20
3A20: e1          POP  H
3A21: c1          POP  B
3A22: eb          XCHG
3A23: e6 70       ANI  $70
3A25: ca 16 3a    JZ   $3A16
3A28: eb          XCHG
3A29: cd cc 01    CALL $01CC
3A2C: d8          RC
3A2D: c8          RZ
3A2E: e5          PUSH H
3A2F: 2a b7 58    LHLD $58B7
3A32: 23          INX  H
3A33: 23          INX  H
3A34: 23          INX  H
3A35: 7e          MOV  A,M
3A36: f6 10       ORI  $10
3A38: 77          MOV  M,A
3A39: e1          POP  H
3A3A: cd cf 01    CALL $01CF
3A3D: d2 42 3a    JNC  $3A42
3A40: 50          MOV  D,B
3A41: 59          MOV  E,C
3A42: cd c9 01    CALL $01C9
3A45: ca 16 3a    JZ   $3A16
3A48: 7c          MOV  A,H
3A49: ba          CMP  D
3A4A: ca 5c 3a    JZ   $3A5C
3A4D: 7d          MOV  A,L
3A4E: fe 01       CPI  $01
3A50: c2 5c 3a    JNZ  $3A5C
3A53: cd 66 3a    CALL $3A66
3A56: 24          INR  H
3A57: 2e 01       MVI  L,$01
3A59: c3 42 3a    JMP  $3A42
3A5C: 97          SUB  A
3A5D: cd 8e 3d    CALL $3D8E
3A60: cd 5f 38    CALL $385F
3A63: c3 42 3a    JMP  $3A42
3A66: c5          PUSH B
3A67: d5          PUSH D
3A68: e5          PUSH H
3A69: e5          PUSH H
3A6A: f5          PUSH PSW
3A6B: 3a a9 58    LDA  $58A9
3A6E: 47          MOV  B,A
3A6F: cd 81 38    CALL $3881
3A72: 4f          MOV  C,A
3A73: 7c          MOV  A,H
3A74: b8          CMP  B
3A75: da 7c 3a    JC   $3A7C
3A78: b9          CMP  C
3A79: da a2 3a    JC   $3AA2
3A7C: 7c          MOV  A,H
3A7D: cd 45 3e    CALL $3E45
3A80: f1          POP  PSW
3A81: fe 02       CPI  $02
3A83: ca 97 3a    JZ   $3A97
3A86: eb          XCHG
3A87: 06 28       MVI  B,$28
3A89: 36 00       MVI  M,$00
3A8B: 23          INX  H
3A8C: 23          INX  H
3A8D: 36 00       MVI  M,$00
3A8F: 23          INX  H
3A90: 05          DCR  B
3A91: c2 89 3a    JNZ  $3A89
3A94: c3 c6 3a    JMP  $3AC6
3A97: 21 78 00    LXI  H,$0078
3A9A: 19          DAD  D
3A9B: eb          XCHG
3A9C: cd 29 38    CALL $3829
3A9F: c3 c6 3a    JMP  $3AC6
3AA2: cd 1d 3e    CALL $3E1D
3AA5: f1          POP  PSW
3AA6: fe 02       CPI  $02
3AA8: cc 06 01    CZ   $0106
3AAB: ca c6 3a    JZ   $3AC6
3AAE: 54          MOV  D,H
3AAF: 2a 16 5e    LHLD $5E16
3AB2: eb          XCHG
3AB3: 2e 01       MVI  L,$01
3AB5: 22 16 5e    SHLD $5E16
3AB8: 24          INR  H
3AB9: 2e 01       MVI  L,$01
3ABB: 3e 01       MVI  A,$01
3ABD: 06 00       MVI  B,$00
3ABF: cd 0c 01    CALL $010C
3AC2: eb          XCHG
3AC3: 22 16 5e    SHLD $5E16
3AC6: e1          POP  H
3AC7: 6c          MOV  L,H
3AC8: 26 5a       MVI  H,$5A
3ACA: 36 00       MVI  M,$00
3ACC: e1          POP  H
3ACD: d1          POP  D
3ACE: c1          POP  B
3ACF: c9          RET
3AD0: cd a0 00    CALL $00A0
3AD3: e6 0f       ANI  $0F
3AD5: fe 0e       CPI  $0E
3AD7: c8          RZ
3AD8: 3a 2a 5f    LDA  $5F2A
3ADB: a7          ANA  A
3ADC: c8          RZ
3ADD: 2a ad 58    LHLD $58AD
3AE0: 7e          MOV  A,M
3AE1: 23          INX  H
3AE2: fe ff       CPI  $FF
3AE4: c2 e0 3a    JNZ  $3AE0
3AE7: 2b          DCX  H
3AE8: d5          PUSH D
3AE9: eb          XCHG
3AEA: 2a 61 58    LHLD $5861
3AED: cd c9 01    CALL $01C9
3AF0: d1          POP  D
3AF1: c8          RZ
3AF2: 3a 9f 58    LDA  $589F
3AF5: e6 0f       ANI  $0F
3AF7: b3          ORA  E
3AF8: 5f          MOV  E,A
3AF9: d5          PUSH D
3AFA: cd 21 39    CALL $3921
3AFD: 54          MOV  D,H
3AFE: 5d          MOV  E,L
3AFF: cd 40 3c    CALL $3C40
3B02: 4e          MOV  C,M
3B03: 23          INX  H
3B04: 46          MOV  B,M
3B05: 2b          DCX  H
3B06: cd cf 01    CALL $01CF
3B09: ca 1f 3b    JZ   $3B1F
3B0C: 01 04 00    LXI  B,$0004
3B0F: 09          DAD  B
3B10: c1          POP  B
3B11: 7e          MOV  A,M
3B12: 73          MOV  M,E
3B13: 5a          MOV  E,D
3B14: 50          MOV  D,B
3B15: 41          MOV  B,C
3B16: 4f          MOV  C,A
3B17: 7e          MOV  A,M
3B18: 23          INX  H
3B19: fe ff       CPI  $FF
3B1B: c2 11 3b    JNZ  $3B11
3B1E: c9          RET
3B1F: d1          POP  D
3B20: 23          INX  H
3B21: 23          INX  H
3B22: 72          MOV  M,D
3B23: 23          INX  H
3B24: 73          MOV  M,E
3B25: c9          RET
3B26: c5          PUSH B
3B27: d5          PUSH D
3B28: e5          PUSH H
3B29: 7c          MOV  A,H
3B2A: 85          ADD  L
3B2B: fe 02       CPI  $02
3B2D: c2 3e 3b    JNZ  $3B3E
3B30: 2a ad 58    LHLD $58AD
3B33: 23          INX  H
3B34: 23          INX  H
3B35: 36 70       MVI  M,$70
3B37: 23          INX  H
3B38: 36 00       MVI  M,$00
3B3A: 23          INX  H
3B3B: c3 41 3b    JMP  $3B41
3B3E: cd 54 3b    CALL $3B54
3B41: eb          XCHG
3B42: cd 54 3b    CALL $3B54
3B45: 7e          MOV  A,M
3B46: 36 00       MVI  M,$00
3B48: 12          STAX D
3B49: 23          INX  H
3B4A: 13          INX  D
3B4B: fe ff       CPI  $FF
3B4D: c2 45 3b    JNZ  $3B45
3B50: e1          POP  H
3B51: d1          POP  D
3B52: c1          POP  B
3B53: c9          RET
3B54: 44          MOV  B,H
3B55: 4d          MOV  C,L
3B56: cd 40 3c    CALL $3C40
3B59: 7e          MOV  A,M
3B5A: b9          CMP  C
3B5B: c2 63 3b    JNZ  $3B63
3B5E: 23          INX  H
3B5F: 7e          MOV  A,M
3B60: 2b          DCX  H
3B61: b8          CMP  B
3B62: c8          RZ
3B63: 01 04 00    LXI  B,$0004
3B66: 09          DAD  B
3B67: c9          RET
3B68: 3a 2a 5f a7 c0 c5 d5 e5 cd 20 3c e6 08 e1 d1 c1 DB $3A,$2A,$5F,$A7,$C0,$C5,$D5,$E5,$CD,$20,$3C,$E6,$08,$E1,$D1,$C1
3B78: 37 c0 a7 c9                                     DB $37,$C0,$A7,$C9
3B7C: 3a 2a 5f    LDA  $5F2A
3B7F: a7          ANA  A
3B80: c0          RNZ
3B81: e5          PUSH H
3B82: 3a a9 58    LDA  $58A9
3B85: 3d          DCR  A
3B86: 84          ADD  H
3B87: 67          MOV  H,A
3B88: cd 20 3c    CALL $3C20
3B8B: e1          POP  H
3B8C: e6 70       ANI  $70
3B8E: 37          STC
3B8F: c8          RZ
3B90: 3f          CMC
3B91: c9          RET
3B92: c5          PUSH B
3B93: d5          PUSH D
3B94: cd 20 3c    CALL $3C20
3B97: cd 79 38    CALL $3879
3B9A: ba          CMP  D
3B9B: ca ae 3b    JZ   $3BAE
3B9E: da ae 3b    JC   $3BAE
3BA1: eb          XCHG
3BA2: cd 20 3c    CALL $3C20
3BA5: e6 80       ANI  $80
3BA7: ca 97 3b    JZ   $3B97
3BAA: a7          ANA  A
3BAB: d1          POP  D
3BAC: c1          POP  B
3BAD: c9          RET
3BAE: d1          POP  D
3BAF: c1          POP  B
3BB0: 37          STC
3BB1: c9          RET
3BB2: c5          PUSH B
3BB3: d5          PUSH D
3BB4: cd 20 3c    CALL $3C20
3BB7: e6 80       ANI  $80
3BB9: c2 c2 3b    JNZ  $3BC2
3BBC: cd 68 38    CALL $3868
3BBF: c2 b4 3b    JNZ  $3BB4
3BC2: d1          POP  D
3BC3: c1          POP  B
3BC4: cd 6e 38    CALL $386E
3BC7: bc          CMP  H
3BC8: 3f          CMC
3BC9: c9          RET
3BCA: c5          PUSH B
3BCB: d5          PUSH D
3BCC: cd 79 38    CALL $3879
3BCF: bc          CMP  H
3BD0: ca e6 3b    JZ   $3BE6
3BD3: da e6 3b    JC   $3BE6
3BD6: e5          PUSH H
3BD7: cd 20 3c    CALL $3C20
3BDA: e1          POP  H
3BDB: eb          XCHG
3BDC: e6 70       ANI  $70
3BDE: ca cc 3b    JZ   $3BCC
3BE1: eb          XCHG
3BE2: d1          POP  D
3BE3: c1          POP  B
3BE4: a7          ANA  A
3BE5: c9          RET
3BE6: d1          POP  D
3BE7: c1          POP  B
3BE8: 37          STC
3BE9: c9          RET
3BEA: c5          PUSH B
3BEB: d5          PUSH D
3BEC: e5          PUSH H
3BED: cd 20 3c    CALL $3C20
3BF0: eb          XCHG
3BF1: e1          POP  H
3BF2: e6 70       ANI  $70
3BF4: c2 12 3c    JNZ  $3C12
3BF7: eb          XCHG
3BF8: cd 6e 38    CALL $386E
3BFB: bc          CMP  H
3BFC: c2 0c 3c    JNZ  $3C0C
3BFF: 7d          MOV  A,L
3C00: fe 01       CPI  $01
3C02: c2 0c 3c    JNZ  $3C0C
3C05: 67          MOV  H,A
3C06: 2e 01       MVI  L,$01
3C08: d1          POP  D
3C09: c1          POP  B
3C0A: 37          STC
3C0B: c9          RET
3C0C: cd 68 38    CALL $3868
3C0F: c3 ec 3b    JMP  $3BEC
3C12: cd 6e 38    CALL $386E
3C15: bc          CMP  H
3C16: ca 1c 3c    JZ   $3C1C
3C19: d2 05 3c    JNC  $3C05
3C1C: d1          POP  D
3C1D: c1          POP  B
3C1E: a7          ANA  A
3C1F: c9          RET
3C20: cd 40 3c    CALL $3C40
3C23: 5e          MOV  E,M
3C24: 23          INX  H
3C25: 56          MOV  D,M
3C26: 23          INX  H
3C27: 46          MOV  B,M
3C28: 23          INX  H
3C29: 4e          MOV  C,M
3C2A: 23          INX  H
3C2B: 7e          MOV  A,M
3C2C: fe ff       CPI  $FF
3C2E: ca 37 3c    JZ   $3C37
3C31: 23          INX  H
3C32: 66          MOV  H,M
3C33: 6f          MOV  L,A
3C34: c3 3d 3c    JMP  $3C3D
3C37: 3a aa 58    LDA  $58AA
3C3A: 67          MOV  H,A
3C3B: 2e 01       MVI  L,$01
3C3D: eb          XCHG
3C3E: 78          MOV  A,B
3C3F: c9          RET
3C40: f5          PUSH PSW
3C41: c5          PUSH B
3C42: d5          PUSH D
3C43: eb          XCHG
3C44: 2a ad 58    LHLD $58AD
3C47: 7e          MOV  A,M
3C48: fe ff       CPI  $FF
3C4A: ca 62 3c    JZ   $3C62
3C4D: 4e          MOV  C,M
3C4E: 23          INX  H
3C4F: 46          MOV  B,M
3C50: 23          INX  H
3C51: 23          INX  H
3C52: 23          INX  H
3C53: cd cf 01    CALL $01CF
3C56: ca 62 3c    JZ   $3C62
3C59: da 47 3c    JC   $3C47
3C5C: 01 f8 ff    LXI  B,$FFF8
3C5F: c3 65 3c    JMP  $3C65
3C62: 01 fc ff    LXI  B,$FFFC
3C65: 09          DAD  B
3C66: 22 b7 58    SHLD $58B7
3C69: d1          POP  D
3C6A: c1          POP  B
3C6B: f1          POP  PSW
3C6C: c9          RET
3C6D: f5          PUSH PSW
3C6E: 7a          MOV  A,D
3C6F: 90          SUB  B
3C70: d2 75 3c    JNC  $3C75
3C73: 3e 00       MVI  A,$00
3C75: 44          MOV  B,H
3C76: 67          MOV  H,A
3C77: 7c          MOV  A,H
3C78: b8          CMP  B
3C79: da 84 3c    JC   $3C84
3C7C: cd b9 3c    CALL $3CB9
3C7F: 25          DCR  H
3C80: 15          DCR  D
3C81: c3 77 3c    JMP  $3C77
3C84: 62          MOV  H,D
3C85: 7c          MOV  A,H
3C86: b8          CMP  B
3C87: da 93 3c    JC   $3C93
3C8A: 3e 02       MVI  A,$02
3C8C: cd 66 3a    CALL $3A66
3C8F: 25          DCR  H
3C90: c3 85 3c    JMP  $3C85
3C93: f1          POP  PSW
3C94: c9          RET
3C95: f5          PUSH PSW
3C96: 7c          MOV  A,H
3C97: 80          ADD  B
3C98: 42          MOV  B,D
3C99: 54          MOV  D,H
3C9A: 67          MOV  H,A
3C9B: 78          MOV  A,B
3C9C: bc          CMP  H
3C9D: da a8 3c    JC   $3CA8
3CA0: cd b9 3c    CALL $3CB9
3CA3: 24          INR  H
3CA4: 14          INR  D
3CA5: c3 9b 3c    JMP  $3C9B
3CA8: 62          MOV  H,D
3CA9: 78          MOV  A,B
3CAA: bc          CMP  H
3CAB: da b7 3c    JC   $3CB7
3CAE: 3e 02       MVI  A,$02
3CB0: cd 66 3a    CALL $3A66
3CB3: 24          INR  H
3CB4: c3 a9 3c    JMP  $3CA9
3CB7: f1          POP  PSW
3CB8: c9          RET
3CB9: c5          PUSH B
3CBA: d5          PUSH D
3CBB: e5          PUSH H
3CBC: 3a a9 58    LDA  $58A9
3CBF: 47          MOV  B,A
3CC0: cd 81 38    CALL $3881
3CC3: 4f          MOV  C,A
3CC4: 7a          MOV  A,D
3CC5: b8          CMP  B
3CC6: da cd 3c    JC   $3CCD
3CC9: b9          CMP  C
3CCA: da d9 3c    JC   $3CD9
3CCD: 7c          MOV  A,H
3CCE: b8          CMP  B
3CCF: da 00 3d    JC   $3D00
3CD2: b9          CMP  C
3CD3: da fa 3c    JC   $3CFA
3CD6: c3 00 3d    JMP  $3D00
3CD9: 7c          MOV  A,H
3CDA: b8          CMP  B
3CDB: da f4 3c    JC   $3CF4
3CDE: b9          CMP  C
3CDF: da e5 3c    JC   $3CE5
3CE2: c3 f4 3c    JMP  $3CF4
3CE5: 05          DCR  B
3CE6: 7c          MOV  A,H
3CE7: 90          SUB  B
3CE8: 67          MOV  H,A
3CE9: 7a          MOV  A,D
3CEA: 90          SUB  B
3CEB: 57          MOV  D,A
3CEC: 3e 02       MVI  A,$02
3CEE: cd 2a 01    CALL $012A
3CF1: c3 0c 3d    JMP  $3D0C
3CF4: cd 5b 3d    CALL $3D5B
3CF7: c3 0c 3d    JMP  $3D0C
3CFA: cd 6d 3d    CALL $3D6D
3CFD: c3 0c 3d    JMP  $3D0C
3D00: 5a          MOV  E,D
3D01: 6c          MOV  L,H
3D02: 26 5b       MVI  H,$5B
3D04: 54          MOV  D,H
3D05: 1a          LDAX D
3D06: 4f          MOV  C,A
3D07: 7e          MOV  A,M
3D08: 12          STAX D
3D09: 71          MOV  M,C
3D0A: 53          MOV  D,E
3D0B: 65          MOV  H,L
3D0C: 5a          MOV  E,D
3D0D: 6c          MOV  L,H
3D0E: 26 5a       MVI  H,$5A
3D10: 54          MOV  D,H
3D11: 7e          MOV  A,M
3D12: 12          STAX D
3D13: e1          POP  H
3D14: d1          POP  D
3D15: c1          POP  B
3D16: c9          RET
3D17: f5          PUSH PSW
3D18: c5          PUSH B
3D19: d5          PUSH D
3D1A: e5          PUSH H
3D1B: 47          MOV  B,A
3D1C: 3a a5 58    LDA  $58A5
3D1F: fe 01       CPI  $01
3D21: ca 36 3d    JZ   $3D36
3D24: 78          MOV  A,B
3D25: 32 a9 58    STA  $58A9
3D28: 67          MOV  H,A
3D29: 57          MOV  D,A
3D2A: 3a 60 58    LDA  $5860
3D2D: cd 5b 3d    CALL $3D5B
3D30: 24          INR  H
3D31: 14          INR  D
3D32: 3d          DCR  A
3D33: c2 2d 3d    JNZ  $3D2D
3D36: e1          POP  H
3D37: d1          POP  D
3D38: c1          POP  B
3D39: f1          POP  PSW
3D3A: c9          RET
3D3B: f5          PUSH PSW
3D3C: d5          PUSH D
3D3D: e5          PUSH H
3D3E: 3a a5 58    LDA  $58A5
3D41: fe 01       CPI  $01
3D43: ca 57 3d    JZ   $3D57
3D46: 3a a9 58    LDA  $58A9
3D49: 57          MOV  D,A
3D4A: 67          MOV  H,A
3D4B: 3a 60 58    LDA  $5860
3D4E: cd 6d 3d    CALL $3D6D
3D51: 24          INR  H
3D52: 14          INR  D
3D53: 3d          DCR  A
3D54: c2 4e 3d    JNZ  $3D4E
3D57: e1          POP  H
3D58: d1          POP  D
3D59: f1          POP  PSW
3D5A: c9          RET
3D5B: f5          PUSH PSW
3D5C: d5          PUSH D
3D5D: e5          PUSH H
3D5E: eb          XCHG
3D5F: cd 1d 3e    CALL $3E1D
3D62: 7a          MOV  A,D
3D63: cd 45 3e    CALL $3E45
3D66: cd a8 01    CALL $01A8
3D69: e1          POP  H
3D6A: d1          POP  D
3D6B: f1          POP  PSW
3D6C: c9          RET
3D6D: f5          PUSH PSW
3D6E: d5          PUSH D
3D6F: e5          PUSH H
3D70: cd 1d 3e    CALL $3E1D
3D73: 7a          MOV  A,D
3D74: cd 45 3e    CALL $3E45
3D77: cd ab 01    CALL $01AB
3D7A: e1          POP  H
3D7B: d1          POP  D
3D7C: f1          POP  PSW
3D7D: c9          RET
3D7E: e5          PUSH H
3D7F: cd 1d 3e    CALL $3E1D
3D82: d4 42 01    CNC  $0142
3D85: e1          POP  H
3D86: d0          RNC
3D87: e5          PUSH H
3D88: cd 69 3e    CALL $3E69
3D8B: 7e          MOV  A,M
3D8C: e1          POP  H
3D8D: c9          RET
3D8E: e5          PUSH H
3D8F: cd 1d 3e    CALL $3E1D
3D92: d4 45 01    CNC  $0145
3D95: e1          POP  H
3D96: d0          RNC
3D97: e5          PUSH H
3D98: cd 69 3e    CALL $3E69
3D9B: 77          MOV  M,A
3D9C: e1          POP  H
3D9D: c9          RET
3D9E: e5          PUSH H
3D9F: cd 1d 3e    CALL $3E1D
3DA2: d4 48 01    CNC  $0148
3DA5: d2 b5 3d    JNC  $3DB5
3DA8: e1          POP  H
3DA9: e5          PUSH H
3DAA: cd 71 3e    CALL $3E71
3DAD: 7e          MOV  A,M
3DAE: d2 b5 3d    JNC  $3DB5
3DB1: 1f          RAR
3DB2: 1f          RAR
3DB3: 1f          RAR
3DB4: 1f          RAR
3DB5: e6 0f       ANI  $0F
3DB7: e1          POP  H
3DB8: c9          RET
3DB9: c5          PUSH B
3DBA: e5          PUSH H
3DBB: cd 71 3e    CALL $3E71
3DBE: d2 ce 3d    JNC  $3DCE
3DC1: 07          RLC
3DC2: 07          RLC
3DC3: 07          RLC
3DC4: 07          RLC
3DC5: e6 f0       ANI  $F0
3DC7: 47          MOV  B,A
3DC8: 7e          MOV  A,M
3DC9: e6 0f       ANI  $0F
3DCB: c3 d4 3d    JMP  $3DD4
3DCE: e6 0f       ANI  $0F
3DD0: 47          MOV  B,A
3DD1: 7e          MOV  A,M
3DD2: e6 f0       ANI  $F0
3DD4: b0          ORA  B
3DD5: 77          MOV  M,A
3DD6: e1          POP  H
3DD7: c1          POP  B
3DD8: c9          RET
3DD9: f5          PUSH PSW
3DDA: c5          PUSH B
3DDB: d5          PUSH D
3DDC: e5          PUSH H
3DDD: e6 0f       ANI  $0F
3DDF: 4f          MOV  C,A
3DE0: 0f          RRC
3DE1: 0f          RRC
3DE2: 0f          RRC
3DE3: 0f          RRC
3DE4: e6 f0       ANI  $F0
3DE6: b1          ORA  C
3DE7: 4f          MOV  C,A
3DE8: 7c          MOV  A,H
3DE9: cd 45 3e    CALL $3E45
3DEC: eb          XCHG
3DED: 06 28       MVI  B,$28
3DEF: 23          INX  H
3DF0: 71          MOV  M,C
3DF1: 23          INX  H
3DF2: 23          INX  H
3DF3: 05          DCR  B
3DF4: c2 ef 3d    JNZ  $3DEF
3DF7: e1          POP  H
3DF8: d1          POP  D
3DF9: c1          POP  B
3DFA: f1          POP  PSW
3DFB: c9          RET
3DFC: 06 30 d6 64 da 07 3e 04 c3 fe 3d c6 64 4f 78 f5 DB $06,$30,$D6,$64,$DA,$07,$3E,$04,$C3,$FE,$3D,$C6,$64,$4F,$78,$F5
3E0C: 79 06 30 d6 0a da 18 3e 04 c3 0f 3e c6 3a 4f f1 DB $79,$06,$30,$D6,$0A,$DA,$18,$3E,$04,$C3,$0F,$3E,$C6,$3A,$4F,$F1
3E1C: c9                                              DB $C9
3E1D: f5          PUSH PSW
3E1E: c5          PUSH B
3E1F: 3a a9 58    LDA  $58A9
3E22: 3d          DCR  A
3E23: 47          MOV  B,A
3E24: 7c          MOV  A,H
3E25: 90          SUB  B
3E26: c1          POP  B
3E27: 67          MOV  H,A
3E28: 3a 60 58    LDA  $5860
3E2B: 3c          INR  A
3E2C: bc          CMP  H
3E2D: ca 39 3e    JZ   $3E39
3E30: cd b1 01    CALL $01B1
3E33: da 39 3e    JC   $3E39
3E36: f1          POP  PSW
3E37: a7          ANA  A
3E38: c9          RET
3E39: f1          POP  PSW
3E3A: 37          STC
3E3B: c9          RET
3E3C: f5          PUSH PSW
3E3D: 3a a9 58    LDA  $58A9
3E40: 3d          DCR  A
3E41: 84          ADD  H
3E42: 67          MOV  H,A
3E43: f1          POP  PSW
3E44: c9          RET
; backing_row_address
3E45: f5          PUSH PSW
3E46: c5          PUSH B
3E47: e5          PUSH H
3E48: 26 5b       MVI  H,$5B
3E4A: 6f          MOV  L,A
3E4B: 7e          MOV  A,M
3E4C: 2a ab 58    LHLD $58AB
3E4F: 11 78 00    LXI  D,$0078
3E52: 3d          DCR  A
3E53: ca 64 3e    JZ   $3E64
3E56: 06 08       MVI  B,$08
3E58: 0f          RRC
3E59: d2 5d 3e    JNC  $3E5D
3E5C: 19          DAD  D
3E5D: eb          XCHG
3E5E: 29          DAD  H
3E5F: eb          XCHG
3E60: 05          DCR  B
3E61: c2 58 3e    JNZ  $3E58
3E64: eb          XCHG
3E65: e1          POP  H
3E66: c1          POP  B
3E67: f1          POP  PSW
3E68: c9          RET
3E69: cd 71 3e    CALL $3E71
3E6C: 2b          DCX  H
3E6D: d8          RC
3E6E: 23          INX  H
3E6F: 23          INX  H
3E70: c9          RET
; packed_cell_address
3E71: f5          PUSH PSW
3E72: c5          PUSH B
3E73: d5          PUSH D
3E74: 7c          MOV  A,H
3E75: cd 45 3e    CALL $3E45
3E78: eb          XCHG
3E79: 2b          DCX  H
3E7A: 2b          DCX  H
3E7B: 7b          MOV  A,E
3E7C: e6 01       ANI  $01
3E7E: f5          PUSH PSW
3E7F: 7b          MOV  A,E
3E80: ca 85 3e    JZ   $3E85
3E83: c6 01       ADI  $01
3E85: 0f          RRC
3E86: 06 06       MVI  B,$06
3E88: 11 03 00    LXI  D,$0003
3E8B: 0f          RRC
3E8C: d2 90 3e    JNC  $3E90
3E8F: 19          DAD  D
3E90: eb          XCHG
3E91: 29          DAD  H
3E92: eb          XCHG
3E93: 05          DCR  B
3E94: c2 8b 3e    JNZ  $3E8B
3E97: f1          POP  PSW
3E98: d1          POP  D
3E99: c1          POP  B
3E9A: c2 a0 3e    JNZ  $3EA0
3E9D: f1          POP  PSW
3E9E: a7          ANA  A
3E9F: c9          RET
3EA0: f1          POP  PSW
3EA1: 37          STC
3EA2: c9          RET
3EA3: 3a aa 58    LDA  $58AA
3EA6: 67          MOV  H,A
3EA7: 16 01       MVI  D,$01
3EA9: 3a 38 5f    LDA  $5F38
3EAC: a7          ANA  A
3EAD: c2 b8 3e    JNZ  $3EB8
3EB0: 3a a9 58    LDA  $58A9
3EB3: 57          MOV  D,A
3EB4: cd 81 38    CALL $3881
3EB7: 67          MOV  H,A
3EB8: 2e 01       MVI  L,$01
3EBA: 1e 01       MVI  E,$01
3EBC: 3a 2b 5f    LDA  $5F2B
3EBF: a7          ANA  A
3EC0: cc 21 39    CZ   $3921
3EC3: eb          XCHG
3EC4: 3a 2a 5f    LDA  $5F2A
3EC7: a7          ANA  A
3EC8: c2 1b 3f    JNZ  $3F1B
3ECB: cd b3 38    CALL $38B3
3ECE: 42          MOV  B,D
3ECF: 4b          MOV  C,E
3ED0: cd cc 01    CALL $01CC
3ED3: da 47 3f    JC   $3F47
3ED6: ca 47 3f    JZ   $3F47
3ED9: c5          PUSH B
3EDA: e5          PUSH H
3EDB: cd 20 3c    CALL $3C20
3EDE: 2a b7 58    LHLD $58B7
3EE1: 23          INX  H
3EE2: 23          INX  H
3EE3: 23          INX  H
3EE4: 7e          MOV  A,M
3EE5: e6 ef       ANI  $EF
3EE7: 77          MOV  M,A
3EE8: e1          POP  H
3EE9: 78          MOV  A,B
3EEA: e6 02       ANI  $02
3EEC: c2 02 3f    JNZ  $3F02
3EEF: 78          MOV  A,B
3EF0: e6 70       ANI  $70
3EF2: ca 16 3f    JZ   $3F16
3EF5: 3a 1d 5f    LDA  $5F1D
3EF8: a7          ANA  A
3EF9: ca 02 3f    JZ   $3F02
3EFC: 79          MOV  A,C
3EFD: e6 10       ANI  $10
3EFF: ca 16 3f    JZ   $3F16
3F02: 3a 1d 5f    LDA  $5F1D
3F05: a7          ANA  A
3F06: c4 35 40    CNZ  $4035
3F09: c1          POP  B
3F0A: cd cf 01    CALL $01CF
3F0D: d2 12 3f    JNC  $3F12
3F10: 50          MOV  D,B
3F11: 59          MOV  E,C
3F12: cd c6 3f    CALL $3FC6
3F15: c5          PUSH B
3F16: c1          POP  B
3F17: eb          XCHG
3F18: c3 d0 3e    JMP  $3ED0
3F1B: 06 00       MVI  B,$00
3F1D: 7c          MOV  A,H
3F1E: ba          CMP  D
3F1F: ca 47 3f    JZ   $3F47
3F22: d5          PUSH D
3F23: e5          PUSH H
3F24: 2e 01       MVI  L,$01
3F26: 0e 00       MVI  C,$00
3F28: 16 00       MVI  D,$00
3F2A: cd 9e 3d    CALL $3D9E
3F2D: fe 0e       CPI  $0E
3F2F: cc aa 3f    CZ   $3FAA
3F32: c4 9a 3f    CNZ  $3F9A
3F35: 7a          MOV  A,D
3F36: a7          ANA  A
3F37: ca 40 3f    JZ   $3F40
3F3A: cd 19 40    CALL $4019
3F3D: c3 41 3f    JMP  $3F41
3F40: 04          INR  B
3F41: e1          POP  H
3F42: d1          POP  D
3F43: 24          INR  H
3F44: c3 1d 3f    JMP  $3F1D
3F47: 3a 19 5f    LDA  $5F19
3F4A: fe 01       CPI  $01
3F4C: da 5c 3f    JC   $3F5C
3F4F: ca 57 3f    JZ   $3F57
3F52: 3e 0d       MVI  A,$0D
3F54: c3 5e 3f    JMP  $3F5E
3F57: 3e 03       MVI  A,$03
3F59: c3 5e 3f    JMP  $3F5E
3F5C: 3e 17       MVI  A,$17
3F5E: cd 8f 40    CALL $408F
3F61: 97          SUB  A
3F62: 32 b9 58    STA  $58B9
3F65: c9          RET
3F66: 01 00 00    LXI  B,$0000
3F69: cd 21 39    CALL $3921
3F6C: 3a 33 5f    LDA  $5F33
3F6F: a7          ANA  A
3F70: ca 81 3f    JZ   $3F81
3F73: 6c          MOV  L,H
3F74: 26 5a       MVI  H,$5A
3F76: 7e          MOV  A,M
3F77: 65          MOV  H,L
3F78: a7          ANA  A
3F79: ca 81 3f    JZ   $3F81
3F7C: fe ff       CPI  $FF
3F7E: c2 82 3f    JNZ  $3F82
3F81: 97          SUB  A
3F82: 6f          MOV  L,A
3F83: 2c          INR  L
3F84: e5          PUSH H
3F85: cd 1d 3e    CALL $3E1D
3F88: 22 16 5e    SHLD $5E16
3F8B: e1          POP  H
3F8C: cd 9e 3d    CALL $3D9E
3F8F: fe 0e       CPI  $0E
3F91: cc aa 3f    CZ   $3FAA
3F94: c4 9a 3f    CNZ  $3F9A
3F97: c3 19 40    JMP  $4019
3F9A: f5          PUSH PSW
3F9B: cd 7e 3d    CALL $3D7E
3F9E: cd e5 3f    CALL $3FE5
3FA1: 2c          INR  L
3FA2: 7d          MOV  A,L
3FA3: fe 51       CPI  $51
3FA5: da 9b 3f    JC   $3F9B
3FA8: f1          POP  PSW
3FA9: c9          RET
3FAA: f5          PUSH PSW
3FAB: cd 7e 3d    CALL $3D7E
3FAE: cd e5 3f    CALL $3FE5
3FB1: 2c          INR  L
3FB2: 2c          INR  L
3FB3: 7d          MOV  A,L
3FB4: fe 50       CPI  $50
3FB6: da ab 3f    JC   $3FAB
3FB9: f1          POP  PSW
3FBA: c9          RET
3FBB: 2a af 58    LHLD $58AF
3FBE: cd 35 40    CALL $4035
3FC1: eb          XCHG
3FC2: 2a b1 58    LHLD $58B1
3FC5: eb          XCHG
3FC6: c5          PUSH B
3FC7: 01 00 00    LXI  B,$0000
3FCA: cd c9 01    CALL $01C9
3FCD: ca de 3f    JZ   $3FDE
3FD0: cd 7e 3d    CALL $3D7E
3FD3: d5          PUSH D
3FD4: cd e5 3f    CALL $3FE5
3FD7: d1          POP  D
3FD8: cd 5f 38    CALL $385F
3FDB: c3 ca 3f    JMP  $3FCA
3FDE: 3e 1f       MVI  A,$1F
3FE0: cd 8f 40    CALL $408F
3FE3: c1          POP  B
3FE4: c9          RET
3FE5: a7          ANA  A
3FE6: c2 eb 3f    JNZ  $3FEB
3FE9: 3e 20       MVI  A,$20
3FEB: fe 20       CPI  $20
3FED: c2 fb 3f    JNZ  $3FFB
3FF0: 3a 1c 5f    LDA  $5F1C
3FF3: a7          ANA  A
3FF4: ca f9 3f    JZ   $3FF9
3FF7: 0c          INR  C
3FF8: c9          RET
3FF9: 3e 20       MVI  A,$20
3FFB: f5          PUSH PSW
3FFC: 16 01       MVI  D,$01
3FFE: 04          INR  B
3FFF: 05          DCR  B
