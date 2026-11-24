; reset: CPU df5d, 65 bytes
df5d: 0f           sei
df5e: 8e 38 00     lds 0x3800
df61: bd e0 a6     jsr (0xE0A6)
df64: 8e 38 00     lds 0x3800
df67: ce 37 bc     ldx 0x37BC
df6a: 18 ce db f6  ldy 0xDBF6
df6e: 86 24        ldaa 0x24
df70: 18 e6 00     ldab (Y+0x00)
df73: e7 00        stab (X+0x00)
df75: 08           inx
df76: 18 08        iny
df78: 4a           deca
df79: 26 f5        bne [0xDF70]
df7b: 18 ce dc 1a  ldy 0xDC1A
df7f: cd ee 01     ldx (Y+0x01)
df82: 8d 29        bsr [0xDFAD]
df84: 18 ce da 9d  ldy 0xDA9D
df88: 18 e6 00     ldab (Y+0x00)
df8b: 26 03        bne [0xDF90]
df8d: 7e de f6     jmp (0xDEF6)
df90: cd ee 01     ldx (Y+0x01)
df93: 6f 00        clr (X+0x00)
df95: 6f 01        clr (X+0x01)
df97: 4f           clra
df98: 8d 04        bsr [0xDF9E]
df9a: 18 3a        aby
df9c: 20 ea        bra [0xDF88]

; startup: CPU e0a6, 89 bytes
e0a6: 86 a0     ldaa 0xA0
e0a8: b7 10 3d  staa (0x103D)
e0ab: b6 01 12  ldaa (0x0112)
e0ae: b7 10 3d  staa (0x103D)
e0b1: 86 ef     ldaa 0xEF
e0b3: 97 00     staa (0x0000)
e0b5: 96 3f     ldaa (0x003F)
e0b7: 81 0d     cmpa 0x0D
e0b9: 27 0a     beq [0xE0C5]
e0bb: 86 ef     ldaa 0xEF
e0bd: b7 10 00  staa (0x1000)
e0c0: b7 01 00  staa (0x0100)
e0c3: 20 e1     bra [0xE0A6]
e0c5: 86 af     ldaa 0xAF
e0c7: 97 00     staa (0x0000)
e0c9: 86 01     ldaa 0x01
e0cb: b7 01 13  staa (0x0113)
e0ce: 86 00     ldaa 0x00
e0d0: 97 24     staa (0x0024)
e0d2: 86 3f     ldaa 0x3F
e0d4: 97 00     staa (0x0000)
e0d6: 86 80     ldaa 0x80
e0d8: 97 26     staa (0x0026)
e0da: 7c 01 13  inc (0x0113)
e0dd: 86 ff     ldaa 0xFF
e0df: 97 52     staa (0x0052)
e0e1: 4f        clra
e0e2: 97 53     staa (0x0053)
e0e4: 86 cf     ldaa 0xCF
e0e6: 97 00     staa (0x0000)
e0e8: 7c 01 13  inc (0x0113)
e0eb: 96 0a     ldaa (0x000A)
e0ed: 81 7e     cmpa 0x7E
e0ef: 27 0e     beq [0xE0FF]
e0f1: b6 01 0d  ldaa (0x010D)
e0f4: 81 01     cmpa 0x01
e0f6: 27 07     beq [0xE0FF]
e0f8: b6 01 0f  ldaa (0x010F)
e0fb: 81 03     cmpa 0x03
e0fd: 27 71     beq [0xE170]

; ram-test: CPU e1ec, 124 bytes
e1ec: 86 0f     ldaa 0x0F
e1ee: 97 58     staa (0x0058)
e1f0: ce 01 20  ldx 0x0120
e1f3: cc aa aa  ldd 0xAAAA
e1f6: ed 00     std (X+0x00)
e1f8: a3 00     subd (X+0x00)
e1fa: 26 ad     bne [0xE1A9]
e1fc: cc 55 55  ldd 0x5555
e1ff: ed 00     std (X+0x00)
e201: a3 00     subd (X+0x00)
e203: 26 a4     bne [0xE1A9]
e205: 08        inx
e206: 08        inx
e207: 8c 60 00  cpx 0x6000
e20a: 26 e7     bne [0xE1F3]
e20c: ce a0 00  ldx 0xA000
e20f: cc aa aa  ldd 0xAAAA
e212: ed 00     std (X+0x00)
e214: a3 00     subd (X+0x00)
e216: 26 91     bne [0xE1A9]
e218: cc 55 55  ldd 0x5555
e21b: ed 00     std (X+0x00)
e21d: a3 00     subd (X+0x00)
e21f: 26 88     bne [0xE1A9]
e221: 08        inx
e222: 08        inx
e223: 8c b6 00  cpx 0xB600
e226: 26 e7     bne [0xE20F]
e228: ce b8 00  ldx 0xB800
e22b: cc aa aa  ldd 0xAAAA
e22e: ed 00     std (X+0x00)
e230: a3 00     subd (X+0x00)
e232: 27 03     beq [0xE237]
e234: 7e e1 a9  jmp (0xE1A9)
e237: cc 55 55  ldd 0x5555
e23a: ed 00     std (X+0x00)
e23c: a3 00     subd (X+0x00)
e23e: 27 03     beq [0xE243]
e240: 7e e1 a9  jmp (0xE1A9)
e243: 08        inx
e244: 08        inx
e245: 8c c0 00  cpx 0xC000
e248: 26 e1     bne [0xE22B]
e24a: 86 4f     ldaa 0x4F
e24c: 97 00     staa (0x0000)
e24e: 86 10     ldaa 0x10
e250: bb 01 13  adda (0x0113)
e253: b7 01 13  staa (0x0113)
e256: 86 00     ldaa 0x00
e258: b7 01 02  staa (0x0102)
e25b: 8e b0 c7  lds 0xB0C7
e25e: 86 03     ldaa 0x03
e260: 97 60     staa (0x0060)
e262: bd e3 49  jsr (0xE349)
e265: 7e e1 72  jmp (0xE172)

; checksum: CPU e268, 64 bytes
e268: 4f        clra
e269: ce c0 00  ldx 0xC000
e26c: ab 00     adda (X+0x00)
e26e: 08        inx
e26f: 8c ff b0  cpx 0xFFB0
e272: 26 f8     bne [0xE26C]
e274: ce ff c8  ldx 0xFFC8
e277: ab 00     adda (X+0x00)
e279: 08        inx
e27a: 8c 00 00  cpx 0x0000
e27d: 26 f8     bne [0xE277]
e27f: 5f        clrb
e280: d7 58     stab (0x0058)
e282: ce 40 00  ldx 0x4000
e285: ab 00     adda (X+0x00)
e287: 08        inx
e288: 8c 80 00  cpx 0x8000
e28b: 26 f8     bne [0xE285]
e28d: 5c        incb
e28e: c1 0d     cmpb 0x0D
e290: 26 ee     bne [0xE280]
e292: 43        coma
e293: b7 01 01  staa (0x0101)
e296: b1 ff bf  cmpa (0xFFBF)
e299: 26 0d     bne [0xE2A8]
e29b: 86 0f     ldaa 0x0F
e29d: 97 00     staa (0x0000)
e29f: 86 0d     ldaa 0x0D
e2a1: bb 01 13  adda (0x0113)
e2a4: b7 01 13  staa (0x0113)
e2a7: 39        rts

; far-call: CPU f408, 88 bytes
f408: b7 37 be     staa (0x37BE)
f40b: 97 58        staa (0x0058)
f40d: 18 ad 00     jsr (Y+0x00)
f410: 20 09        bra [0xF41B]
f412: 00           test
f413: 8d 29        bsr [0xF43E]
f415: 18 3c        pshy
f417: 86 00        ldaa 0x00
f419: 20 33        bra [0xF44E]
f41b: 86 00        ldaa 0x00
f41d: b7 37 be     staa (0x37BE)
f420: 97 58        staa (0x0058)
f422: 39           rts
f423: b7 37 be     staa (0x37BE)
f426: 97 58        staa (0x0058)
f428: 18 ad 00     jsr (Y+0x00)
f42b: 20 09        bra [0xF436]
f42d: 00           test
f42e: 8d 0e        bsr [0xF43E]
f430: 18 3c        pshy
f432: 86 01        ldaa 0x01
f434: 20 18        bra [0xF44E]
f436: 86 01        ldaa 0x01
f438: b7 37 be     staa (0x37BE)
f43b: 97 58        staa (0x0058)
f43d: 39           rts
f43e: 17           tba
f43f: 18 ce db dc  ldy 0xDBDC
f443: f6 37 be     ldab (0x37BE)
f446: 58           aslb
f447: 18 3a        aby
f449: 18 ee 00     ldy (Y+0x00)
f44c: 16           tab
f44d: 39           rts
f44e: 3c           pshx
f44f: 3a           abx
f450: ee 00        ldx (X+0x00)
f452: ee 00        ldx (X+0x00)
f454: 1a ee 04     ldy (X+0x04)
f457: 38           pulx
f458: b7 37 be     staa (0x37BE)
f45b: 97 58        staa (0x0058)
f45d: 18 6e 03     jmp (Y+0x03)

; scheduler: CPU dc42, 142 bytes
dc42: 07           tpa
dc43: 0f           sei
dc44: 18 3c        pshy
dc46: 3c           pshx
dc47: 36           psha
dc48: 37           pshb
dc49: 36           psha
dc4a: 3a           abx
dc4b: 18 fe 37 bc  ldy (0x37BC)
dc4f: 18 ee 00     ldy (Y+0x00)
dc52: 18 ec 06     ldd (Y+0x06)
dc55: ed 00        std (X+0x00)
dc57: ee 02        ldx (X+0x02)
dc59: cd ef 06     stx (Y+0x06)
dc5c: 6c 08        inc (X+0x08)
dc5e: 2e 3a        bgt [0xDC9A]
dc60: 6d 09        tst (X+0x09)
dc62: 1a ef 06     sty (X+0x06)
dc65: ec 04        ldd (X+0x04)
dc67: 1a b3 37 bc  cpd (0x37BC)
dc6b: 27 27        beq [0xDC94]
dc6d: 24 07        bcc [0xDC76]
dc6f: 7d 37 c2     tst (0x37C2)
dc72: 2e cc        bgt [0xDC40]
dc74: 20 1e        bra [0xDC94]
dc76: 18 ec 00     ldd (Y+0x00)
dc79: fe 37 bc     ldx (0x37BC)
dc7c: ed 00        std (X+0x00)
dc7e: cd ee 06     ldx (Y+0x06)
dc81: ee 04        ldx (X+0x04)
dc83: ff 37 bc     stx (0x37BC)
dc86: a6 02        ldaa (X+0x02)
dc88: 97 53        staa (0x0053)
dc8a: 33           pulb
dc8b: 36           psha
dc8c: 1a ef 00     sty (X+0x00)
dc8f: 4f           clra
dc90: 5f           clrb
dc91: 18 ed 00     std (Y+0x00)
dc94: 18 6d 12     tst (Y+0x12)
dc97: 7e 37 de     jmp (0x37DE)
dc9a: 6f 08        clr (X+0x08)
dc9c: cd a3 06     cpd (Y+0x06)
dc9f: 27 f3        beq [0xDC94]
dca1: 6d 0b        tst (X+0x0B)
dca3: ee 04        ldx (X+0x04)
dca5: a6 02        ldaa (X+0x02)
dca7: 33           pulb
dca8: 36           psha
dca9: 18 af 0e     sts (Y+0x0E)
dcac: b6 37 be     ldaa (0x37BE)
dcaf: 18 a7 10     staa (Y+0x10)
dcb2: 18 ec 00     ldd (Y+0x00)
dcb5: fe 37 bc     ldx (0x37BC)
dcb8: ed 00        std (X+0x00)
dcba: 18 ec 06     ldd (Y+0x06)
dcbd: 8f           xgdx
dcbe: ec 00        ldd (X+0x00)
dcc0: 26 fb        bne [0xDCBD]
dcc2: 1a ef 00     sty (X+0x00)
dcc5: 4f           clra
dcc6: 5f           clrb
dcc7: 18 ed 00     std (Y+0x00)
dcca: 7e de f6     jmp (0xDEF6)
dccd: 1a ee 02     ldy (X+0x02)

; trap-monitor: CPU e5ab, 172 bytes
e5ab: bd e4 cb  jsr (0xE4CB)
e5ae: 30        tsx
e5af: 1a ee 09  ldy (X+0x09)
e5b2: 18 a6 00  ldaa (Y+0x00)
e5b5: b7 38 19  staa (0x3819)
e5b8: 81 7b     cmpa 0x7B
e5ba: 27 15     beq [0xE5D1]
e5bc: 81 87     cmpa 0x87
e5be: 26 15     bne [0xE5D5]
e5c0: 18 a6 01  ldaa (Y+0x01)
e5c3: 81 f4     cmpa 0xF4
e5c5: 26 0e     bne [0xE5D5]
e5c7: cc 5e 09  ldd 0x5E09
e5ca: b7 38 19  staa (0x3819)
e5cd: 3a        abx
e5ce: 35        txs
e5cf: 20 04     bra [0xE5D5]
e5d1: 38        pulx
e5d2: 7e e8 69  jmp (0xE869)
e5d5: 86 0d     ldaa 0x0D
e5d7: bd e5 0a  jsr (0xE50A)
e5da: bd e5 2d  jsr (0xE52D)
e5dd: bd e4 ff  jsr (0xE4FF)
e5e0: 81 52     cmpa 0x52
e5e2: 27 29     beq [0xE60D]
e5e4: 81 57     cmpa 0x57
e5e6: 27 34     beq [0xE61C]
e5e8: 81 53     cmpa 0x53
e5ea: 27 39     beq [0xE625]
e5ec: 81 4b     cmpa 0x4B
e5ee: 27 3f     beq [0xE62F]
e5f0: 81 50     cmpa 0x50
e5f2: 27 48     beq [0xE63C]
e5f4: 81 44     cmpa 0x44
e5f6: 27 52     beq [0xE64A]
e5f8: 81 42     cmpa 0x42
e5fa: 26 03     bne [0xE5FF]
e5fc: 7e df 5d  jmp (0xDF5D)
e5ff: 81 49     cmpa 0x49
e601: 27 49     beq [0xE64C]
e603: 81 4c     cmpa 0x4C
e605: 27 49     beq [0xE650]
e607: 81 56     cmpa 0x56
e609: 27 2b     beq [0xE636]
e60b: 20 cd     bra [0xE5DA]
e60d: 8d 54     bsr [0xE663]
e60f: 8f        xgdx
e610: 8d 58     bsr [0xE66A]
e612: a6 00     ldaa (X+0x00)
e614: 08        inx
e615: 8d 61     bsr [0xE678]
e617: 5a        decb
e618: 26 f8     bne [0xE612]
e61a: 20 b9     bra [0xE5D5]
e61c: 8d 45     bsr [0xE663]
e61e: 8f        xgdx
e61f: 8d 49     bsr [0xE66A]
e621: e7 00     stab (X+0x00)
e623: 20 b0     bra [0xE5D5]
e625: 30        tsx
e626: 08        inx
e627: 8f        xgdx
e628: 8d 4e     bsr [0xE678]
e62a: 17        tba
e62b: 8d 4b     bsr [0xE678]
e62d: 20 a6     bra [0xE5D5]
e62f: b6 38 19  ldaa (0x3819)
e632: 8d 44     bsr [0xE678]
e634: 20 9f     bra [0xE5D5]
e636: 86 51     ldaa 0x51
e638: 8d 3e     bsr [0xE678]
e63a: 20 99     bra [0xE5D5]
e63c: 8d 25     bsr [0xE663]
e63e: 18 8f     xgdy
e640: 8d 28     bsr [0xE66A]
e642: 17        tba
e643: 18 a7 00  staa (Y+0x00)
e646: 38        pulx
e647: 7e e6 d9  jmp (0xE6D9)
e64a: 38        pulx
e64b: 3b        rti
e64c: 8d 19     bsr [0xE667]
e64e: 20 85     bra [0xE5D5]
e650: 8d 3a     bsr [0xE68C]
e652: 8d 24     bsr [0xE678]
e654: 7e e5 d5  jmp (0xE5D5)

; sci: CPU e47a, 50 bytes
e47a: 4f     clra
e47b: 97 2c  staa (0x002C)
e47d: 86 0c  ldaa 0x0C
e47f: 97 2d  staa (0x002D)
e481: 86 32  ldaa 0x32
e483: 97 2b  staa (0x002B)
e485: 39     rts
e486: 36     psha
e487: 96 2e  ldaa (0x002E)
e489: 85 20  bita 0x20
e48b: 27 0c  beq [0xE499]
e48d: 96 2f  ldaa (0x002F)
e48f: 81 13  cmpa 0x13
e491: 26 06  bne [0xE499]
e493: 96 2f  ldaa (0x002F)
e495: 81 11  cmpa 0x11
e497: 26 fa  bne [0xE493]
e499: 96 2e  ldaa (0x002E)
e49b: 85 80  bita 0x80
e49d: 27 fa  beq [0xE499]
e49f: 32     pula
e4a0: 97 2f  staa (0x002F)
e4a2: 39     rts
e4a3: a6 00  ldaa (X+0x00)
e4a5: 8d df  bsr [0xE486]
e4a7: 08     inx
e4a8: 5a     decb
e4a9: 26 f8  bne [0xE4A3]
e4ab: 39     rts

; bank6-function: CPU 4000, 272 bytes
4000: 3c        pshx
4001: 3a        abx
4002: ef 0d     stx (X+0x0D)
4004: 1a ee 0b  ldy (X+0x0B)
4007: 18 ee 0b  ldy (Y+0x0B)
400a: 18 ee 08  ldy (Y+0x08)
400d: 18 a6 1a  ldaa (Y+0x1A)
4010: 26 07     bne [0x4019]
4012: a6 00     ldaa (X+0x00)
4014: 26 03     bne [0x4019]
4016: 5f        clrb
4017: 20 02     bra [0x401B]
4019: c6 01     ldab 0x01
401b: e7 0f     stab (X+0x0F)
401d: a6 01     ldaa (X+0x01)
401f: 26 11     bne [0x4032]
4021: 4f        clra
4022: 1a ee 03  ldy (X+0x03)
4025: 18 a7 00  staa (Y+0x00)
4028: 4f        clra
4029: 1a ee 05  ldy (X+0x05)
402c: 18 a7 00  staa (Y+0x00)
402f: 7e 41 0b  jmp (0x410B)
4032: 1a ee 03  ldy (X+0x03)
4035: 18 a6 00  ldaa (Y+0x00)
4038: 27 04     beq [0x403E]
403a: a6 0f     ldaa (X+0x0F)
403c: 27 36     beq [0x4074]
403e: a6 02     ldaa (X+0x02)
4040: 27 17     beq [0x4059]
4042: 86 01     ldaa 0x01
4044: 1a ee 03  ldy (X+0x03)
4047: 18 a7 00  staa (Y+0x00)
404a: a6 02     ldaa (X+0x02)
404c: 1a ee 05  ldy (X+0x05)
404f: 18 a7 00  staa (Y+0x00)
4052: 80 10     suba 0x10
4054: 23 01     bls [0x4057]
4056: 51        ?
4057: 20 18     bra [0x4071]
4059: a6 0f     ldaa (X+0x0F)
405b: 27 14     beq [0x4071]
405d: 4f        clra
405e: 1a ee 03  ldy (X+0x03)
4061: 18 a7 00  staa (Y+0x00)
4064: a6 02     ldaa (X+0x02)
4066: 1a ee 05  ldy (X+0x05)
4069: 18 a7 00  staa (Y+0x00)
406c: 80 10     suba 0x10
406e: 23 01     bls [0x4071]
4070: 51        ?
4071: 7e 41 0b  jmp (0x410B)
4074: 1a ee 05  ldy (X+0x05)
4077: 18 a6 00  ldaa (Y+0x00)
407a: a0 02     suba (X+0x02)
407c: 27 77     beq [0x40F5]
407e: a6 02     ldaa (X+0x02)
4080: 27 3f     beq [0x40C1]
4082: a6 01     ldaa (X+0x01)
4084: 80 02     suba 0x02
4086: 27 22     beq [0x40AA]
4088: 1a ee 05  ldy (X+0x05)
408b: 18 a6 00  ldaa (Y+0x00)
408e: a0 02     suba (X+0x02)
4090: 22 18     bhi [0x40AA]
4092: 1a ee 03  ldy (X+0x03)
4095: 18 a6 00  ldaa (Y+0x00)
4098: 80 02     suba 0x02
409a: 27 0e     beq [0x40AA]
409c: 1a ee 0b  ldy (X+0x0B)
409f: 18 ee 0b  ldy (Y+0x0B)
40a2: 18 ee 08  ldy (Y+0x08)
40a5: 18 a6 19  ldaa (Y+0x19)
40a8: 27 15     beq [0x40BF]
40aa: 86 01     ldaa 0x01
40ac: 1a ee 03  ldy (X+0x03)
40af: 18 a7 00  staa (Y+0x00)
40b2: a6 02     ldaa (X+0x02)
40b4: 1a ee 05  ldy (X+0x05)
40b7: 18 a7 00  staa (Y+0x00)
40ba: 80 10     suba 0x10
40bc: 23 01     bls [0x40BF]
40be: 51        ?
40bf: 20 32     bra [0x40F3]
40c1: a6 01     ldaa (X+0x01)
40c3: 80 02     suba 0x02
40c5: 26 16     bne [0x40DD]
40c7: 4f        clra
40c8: 1a ee 03  ldy (X+0x03)
40cb: 18 a7 00  staa (Y+0x00)
40ce: a6 02     ldaa (X+0x02)
40d0: 1a ee 05  ldy (X+0x05)
40d3: 18 a7 00  staa (Y+0x00)
40d6: 80 10     suba 0x10
40d8: 23 01     bls [0x40DB]
40da: 51        ?
40db: 20 16     bra [0x40F3]
40dd: 1a ee 0b  ldy (X+0x0B)
40e0: 18 ee 0b  ldy (Y+0x0B)
40e3: 18 ee 08  ldy (Y+0x08)
40e6: 18 a6 19  ldaa (Y+0x19)
40e9: 27 08     beq [0x40F3]
40eb: 86 02     ldaa 0x02
40ed: 1a ee 03  ldy (X+0x03)
40f0: 18 a7 00  staa (Y+0x00)
40f3: 20 16     bra [0x410B]
40f5: 1a ee 0b  ldy (X+0x0B)
40f8: 18 ee 0b  ldy (Y+0x0B)
40fb: 18 ee 08  ldy (Y+0x08)
40fe: 18 a6 19  ldaa (Y+0x19)
4101: 27 08     beq [0x410B]
4103: 86 02     ldaa 0x02
4105: 1a ee 03  ldy (X+0x03)
4108: 18 a7 00  staa (Y+0x00)
410b: 1a ee 09  ldy (X+0x09)
