0:000: ff     mov  a,r7
0:001: d5     sel  rb1
0:002: 9e     anld p6,a
0:003: b4 21  call $521
0:005: 01     idl
0:006: fb     mov  a,r3
0:007: c5     sel  rb0
0:008: bc a4  mov  r4,#$A4
0:00a: 56 c3  jt1  $0C3
0:00c: 30     xchd a,@r0
0:00d: fb     mov  a,r3
0:00e: f8     mov  a,r0
0:00f: 12 e1  jb0  $0E1
0:011: 26 62  jnt0 $062
0:013: 6f     add  a,r7
0:014: fa     mov  a,r2
0:015: e4 26  jmp  $726
0:017: 3a     outl p2,a
0:018: 8c     orld p4,a
0:019: 0c     movd a,p4
0:01a: 26 3a  jnt0 $03A
0:01c: ff     mov  a,r7
0:01d: ae     mov  r6,a
0:01e: 5f     anl  a,r7
0:01f: b8 2e  mov  r0,#$2E
0:021: 12 c8  jb0  $0C8
0:023: 17     inc  a
0:024: 80     movx a,@r0
0:025: 2e     xch  a,r6
0:026: 80     movx a,@r0
0:027: 3f     movd p7,a
0:028: 90     movx @r0,a
0:029: 44 f2  jmp  $2F2
0:02b: fb     mov  a,r3
0:02c: 52 fa  jb2  $0FA
0:02e: 44 06  jmp  $206
0:030: 1f     inc  r7
0:031: 06     illegal
0:032: ac     mov  r4,a
0:033: 3c     movd p4,a
0:034: a8     mov  r0,a
0:035: 01     idl
0:036: f4 8a  call $78A
0:038: df     xrl  a,r7
0:039: 5f     anl  a,r7
0:03a: 3c     movd p4,a
0:03b: 07     dec  a
0:03c: 9a f0  anl  p2,#$F0
0:03e: fb     mov  a,r3
0:03f: 47     swap a
0:040: 3a     outl p2,a
0:041: 77     rr   a
0:042: 01     idl
0:043: 48     orl  a,r0
0:044: eb bb  djnz r3,$0BB
0:046: 83     ret
0:047: 05     en   i
0:048: 85     clr  f0
0:049: fe     mov  a,r6
0:04a: 06     illegal
0:04b: 5e     anl  a,r6
0:04c: 95     cpl  f0
0:04d: bc 52  mov  r4,#$52
0:04f: b3     jmpp @a
0:050: 57     da   a
0:051: 46 aa  jnt1 $0AA
0:053: 72 fa  jb3  $0FA
0:055: 80     movx a,@r0
0:056: 01     idl
0:057: 95     cpl  f0
0:058: 2e     xch  a,r6
0:059: 2e     xch  a,r6
0:05a: 77     rr   a
0:05b: 4d     orl  a,r5
0:05c: fc     mov  a,r4
0:05d: 77     rr   a
0:05e: ec fa  djnz r4,$0FA
0:060: 56 aa  jt1  $0AA
0:062: 71     addc a,@r1
0:063: 72 7f  jb3  $07F
0:065: b3     jmpp @a
0:066: ef fe  djnz r7,$0FE
0:068: bc 53  mov  r4,#$53
0:06a: d6     illegal
0:06b: c3     illegal
0:06c: 36 74  jt0  $074
0:06e: 04 74  jmp  $074
0:070: fe     mov  a,r6
0:071: bf ef  mov  r7,#$EF
0:073: 1f     inc  r7
0:074: a4 07  jmp  $507
0:076: 77     rr   a
0:077: bc 34  mov  r4,#$34
0:079: 07     dec  a
0:07a: 93     retr
0:07b: 26 f4  jnt0 $0F4
0:07d: a4 87  jmp  $587
0:07f: 95     cpl  f0
0:080: a4 14  jmp  $514
0:082: 46 aa  jnt1 $0AA
0:084: 1c     inc  r4
0:085: fa     mov  a,r2
0:086: 08     ins  a,bus
0:087: bc 2f  mov  r4,#$2F
0:089: 07     dec  a
0:08a: 8f     orld p7,a
0:08b: 95     cpl  f0
0:08c: f4 c3  call $7C3
0:08e: 01     idl
0:08f: fa     mov  a,r2
0:090: 46 aa  jnt1 $0AA
0:092: 8f     orld p7,a
0:093: bc 10  mov  r4,#$10
0:095: 26 a4  jnt0 $0A4
0:097: 30     xchd a,@r0
0:098: f4 96  call $796
0:09a: 15     dis  i
0:09b: cd     dec  r5
0:09c: 3f     movd p7,a
0:09d: c5     sel  rb0
0:09e: c9     dec  r1
0:09f: 3f     movd p7,a
0:0a0: 96 ae  jnz  $0AE
0:0a2: ff     mov  a,r7
0:0a3: 96 6e  jnz  $06E
0:0a5: 96 a6  jnz  $0A6
0:0a7: 26 0c  jnt0 $00C
0:0a9: e4 0f  jmp  $70F
0:0ab: 03 f1  add  a,#$F1
0:0ad: 56 d6  jt1  $0D6
0:0af: 86 84  jni  $084
0:0b1: 0f     movd a,p7
0:0b2: b8 f1  mov  r0,#$F1
0:0b4: 56 86  jt1  $086
0:0b6: 02     outl bus,a
0:0b7: e9 96  djnz r1,$096
0:0b9: 08     ins  a,bus
0:0ba: bf 05  mov  r7,#$05
0:0bc: 26 33  jnt0 $033
0:0be: 26 b8  jnt0 $0B8
0:0c0: 01     idl
0:0c1: bc b4  mov  r4,#$B4
0:0c3: bc a0  mov  r4,#$A0
0:0c5: 2f     xch  a,r7
0:0c6: 8f     orld p7,a
0:0c7: 1d     inc  r5
0:0c8: 11     inc  @r1
0:0c9: 06     illegal
0:0ca: b8 f1  mov  r0,#$F1
0:0cc: b0 06  mov  @r0,#$06
0:0ce: 01     idl
0:0cf: e9 96  djnz r1,$096
0:0d1: 4a     orl  a,r2
0:0d2: 02     outl bus,a
0:0d3: e4 21  jmp  $721
0:0d5: 26 f1  jnt0 $0F1
0:0d7: 96 26  jnz  $026
0:0d9: bc a4  mov  r4,#$A4
0:0db: b4 f8  call $5F8
0:0dd: 0c     movd a,p4
0:0de: cc     dec  r4
0:0df: a7     cpl  c
0:0e0: bc a4  mov  r4,#$A4
0:0e2: b4 42  call $542
0:0e4: 17     inc  a
0:0e5: cc     dec  r4
0:0e6: d4 96  call $696
0:0e8: 27     clr  a
0:0e9: b8 a0  mov  r0,#$A0
0:0eb: e9 d7  djnz r1,$0D7
0:0ed: 3f     movd p7,a
0:0ee: e8 26  djnz r0,$026
0:0f0: 01     idl
0:0f1: af     mov  r7,a
0:0f2: e4 d5  jmp  $7D5
0:0f4: ab     mov  r3,a
0:0f5: 26 62  jnt0 $062
0:0f7: 55     strt t
0:0f8: 25     en   tcnti
0:0f9: fb     mov  a,r3
0:0fa: eb ef  djnz r3,$0EF
0:0fc: fb     mov  a,r3
0:0fd: fb     mov  a,r3
0:0fe: fc     mov  a,r4
0:0ff: fc     mov  a,r4
0:100: fb     mov  a,r3
0:101: 43 17  orl  a,#$17
0:103: 86 43  jni  $143
0:105: 26 d1  jnt0 $1D1
0:107: bf 05  mov  r7,#$05
0:109: a1     mov  @r1,a
0:10a: 0e     movd a,p6
0:10b: 27     clr  a
0:10c: 11     inc  @r1
0:10d: b8 ad  mov  r0,#$AD
0:10f: af     mov  r7,a
0:110: ae     mov  r6,a
0:111: e9 b3  djnz r1,$1B3
0:113: a4 f1  jmp  $5F1
0:115: b1 11  mov  @r1,#$11
0:117: 91     movx @r1,a
0:118: dd     xrl  a,r5
0:119: a4 96  jmp  $596
0:11b: a4 11  jmp  $511
0:11d: d1     xrl  a,@r1
0:11e: 11     inc  @r1
0:11f: 71     addc a,@r1
0:120: 6e     add  a,r6
0:121: a4 a1  jmp  $5A1
0:123: a4 11  jmp  $511
0:125: 11     inc  @r1
0:126: 11     inc  @r1
0:127: 51     anl  a,@r1
0:128: a1     mov  @r1,a
0:129: a4 a7  jmp  $5A7
0:12b: a4 11  jmp  $511
0:12d: 31     xchd a,@r1
0:12e: 11     inc  @r1
0:12f: ef 16  djnz r7,$116
0:131: cd     dec  r5
0:132: a4 af  jmp  $5AF
0:134: f1     mov  a,@r1
0:135: 11     inc  @r1
0:136: 2d     xch  a,r5
0:137: fd     mov  a,r5
0:138: f1     mov  a,@r1
0:139: 11     inc  @r1
0:13a: ef c3  djnz r7,$1C3
0:13c: cd     dec  r5
0:13d: a4 38  jmp  $538
0:13f: 43 26  orl  a,#$26
0:141: d1     xrl  a,@r1
0:142: 21     xch  a,@r1
0:143: f1     mov  a,@r1
0:144: 0f     movd a,p7
0:145: 86 07  jni  $107
0:147: c8     dec  r0
0:148: 11     inc  @r1
0:149: 93     retr
0:14a: 71     addc a,@r1
0:14b: 43 d8  orl  a,#$D8
0:14d: 51     anl  a,@r1
0:14e: be aa  mov  r6,#$AA
0:150: f1     mov  a,@r1
0:151: 21     xch  a,@r1
0:152: bf ff  mov  r7,#$FF
0:154: dc     xrl  a,r4
0:155: aa     mov  r2,a
0:156: 3f     movd p7,a
0:157: a8     mov  r0,a
0:158: f1     mov  a,@r1
0:159: ef bf  djnz r7,$1BF
0:15b: ff     mov  a,r7
0:15c: e9 53  djnz r1,$153
0:15e: 3f     movd p7,a
0:15f: d6     illegal
0:160: 0a     in   a,p2
0:161: 6f     add  a,r7
0:162: f1     mov  a,@r1
0:163: df     xrl  a,r7
0:164: c3     illegal
0:165: ff     mov  a,r7
0:166: e4 c3  jmp  $7C3
0:168: 6f     add  a,r7
0:169: 07     dec  a
0:16a: 86 51  jni  $151
0:16c: 26 d1  jnt0 $1D1
0:16e: 21     xch  a,@r1
0:16f: ff     mov  a,r7
0:170: a8     mov  r0,a
0:171: f1     mov  a,@r1
0:172: ef 26  djnz r7,$126
0:174: 27     clr  a
0:175: e9 5b  djnz r1,$15B
0:177: 06     illegal
0:178: bc 94  mov  r4,#$94
0:17a: 3f     movd p7,a
0:17b: 03 1d  add  a,#$1D
0:17d: 26 b8  jnt0 $1B8
0:17f: f1     mov  a,@r1
0:180: e9 02  djnz r1,$102
0:182: 3e     movd p6,a
0:183: e9 26  djnz r1,$126
0:185: b8 f1  mov  r0,#$F1
0:187: 26 06  jnt0 $106
0:189: 3b     illegal
0:18a: e9 ff  djnz r1,$1FF
0:18c: b8 f1  mov  r0,#$F1
0:18e: 26 b8  jnt0 $1B8
0:190: 00     nop
0:191: e9 15  djnz r1,$115
0:193: 07     dec  a
0:194: f1     mov  a,@r1
0:195: b8 ff  mov  r0,#$FF
0:197: f1     mov  a,@r1
0:198: 0a     in   a,p2
0:199: c8     dec  r0
0:19a: 0a     in   a,p2
0:19b: ee a0  djnz r6,$1A0
0:19d: f1     mov  a,@r1
0:19e: 06     illegal
0:19f: a0     mov  @r0,a
0:1a0: f1     mov  a,@r1
0:1a1: 06     illegal
0:1a2: ac     mov  r4,a
0:1a3: 96 0a  jnz  $10A
0:1a5: eb cf  djnz r3,$1CF
0:1a7: ff     mov  a,r7
0:1a8: a6     illegal
0:1a9: 42     mov  a,t
0:1aa: c3     illegal
0:1ab: 8c     orld p4,a
0:1ac: 96 17  jnz  $117
0:1ae: aa     mov  r2,a
0:1af: ff     mov  a,r7
0:1b0: 8a 0c  orl  p2,#$0C
0:1b2: b8 f1  mov  r0,#$F1
0:1b4: 7f     addc a,r7
0:1b5: 37     cpl  a
0:1b6: 05     en   i
0:1b7: e9 11  djnz r1,$111
0:1b9: ba bc  mov  r2,#$BC
0:1bb: f4 bc  call $7BC
0:1bd: 07     dec  a
0:1be: 32 be  jb1  $1BE
0:1c0: 0f     movd a,p7
0:1c1: c5     sel  rb0
0:1c2: 1f     inc  r7
0:1c3: 28     xch  a,r0
0:1c4: 12 be  jb0  $1BE
0:1c6: bc b8  mov  r4,#$B8
0:1c8: 20     xch  a,@r0
0:1c9: ed 84  djnz r5,$184
0:1cb: 9a 21  anl  p2,#$21
0:1cd: bd 3a  mov  r5,#$3A
0:1cf: 83     ret
0:1d0: 99 8c  anl  p1,#$8C
0:1d2: 9b     illegal
0:1d3: 23 b9  mov  a,#$B9
0:1d5: bb bc  mov  r3,#$BC
0:1d7: fc     mov  a,r4
0:1d8: 21     xch  a,@r1
0:1d9: ff     mov  a,r7
0:1da: c4 da  jmp  $6DA
0:1dc: e5     sel  mb0
0:1dd: fd     mov  a,r5
0:1de: 7a     addc a,r2
0:1df: c3     illegal
0:1e0: d9     xrl  a,r1
0:1e1: cc     dec  r4
0:1e2: db     xrl  a,r3
0:1e3: 94 f9  call $4F9
0:1e5: fb     mov  a,r3
0:1e6: 3f     movd p7,a
0:1e7: 01     idl
0:1e8: e8 3f  djnz r0,$13F
0:1ea: fa     mov  a,r2
0:1eb: 56 ff  jt1  $1FF
0:1ed: e1     illegal
0:1ee: f4 e0  call $7E0
0:1f0: c3     illegal
0:1f1: e1     illegal
0:1f2: f4 06  call $706
0:1f4: f1     mov  a,@r1
0:1f5: fa     mov  a,r2
0:1f6: 5e     anl  a,r6
0:1f7: ce     dec  r6
0:1f8: a6     illegal
0:1f9: a0     mov  @r0,a
0:1fa: 1c     inc  r4
0:1fb: ed 17  djnz r5,$117
0:1fd: 18     inc  r0
0:1fe: ea 26  djnz r2,$126
0:200: 06     illegal
0:201: e4 05  jmp  $705
0:203: 0c     movd a,p4
0:204: f1     mov  a,@r1
0:205: d6     illegal
0:206: 93     retr
0:207: 41     orl  a,@r1
0:208: 25     en   tcnti
0:209: d6     illegal
0:20a: 17     inc  a
0:20b: 02     outl bus,a
0:20c: 11     inc  @r1
0:20d: 93     retr
0:20e: bc f4  mov  r4,#$F4
0:210: 37     cpl  a
0:211: 17     inc  a
0:212: 52 15  jb2  $215
0:214: b2 b1  jb5  $2B1
0:216: c1     illegal
0:217: f1     mov  a,@r1
0:218: 03 06  add  a,#$06
0:21a: 25     en   tcnti
0:21b: 02     outl bus,a
0:21c: d6     illegal
0:21d: 93     retr
0:21e: bc f4  mov  r4,#$F4
0:220: d6     illegal
0:221: a4 c8  jmp  $5C8
0:223: 02     outl bus,a
0:224: 20     xch  a,@r0
0:225: f1     mov  a,@r1
0:226: bc f4  mov  r4,#$F4
0:228: 37     cpl  a
0:229: 30     xchd a,@r0
0:22a: f7     rlc  a
0:22b: b1 72  mov  @r1,#$72
0:22d: d6     illegal
0:22e: a4 17  jmp  $517
0:230: bc f4  mov  r4,#$F4
0:232: 92 d6  jb4  $2D6
0:234: 02     outl bus,a
0:235: 37     cpl  a
0:236: 3e     movd p6,a
0:237: ef a4  djnz r7,$2A4
0:239: f5     sel  mb1
0:23a: d6     illegal
0:23b: 32 91  jb1  $291
0:23d: 11     inc  @r1
0:23e: ad     mov  r5,a
0:23f: 56 53  jt1  $253
0:241: 93     retr
0:242: 17     inc  a
0:243: b1 a7  mov  @r1,#$A7
0:245: 56 11  jt1  $211
0:247: 71     addc a,@r1
0:248: df     xrl  a,r7
0:249: bc da  mov  r4,#$DA
0:24b: 05     en   i
0:24c: 11     inc  @r1
0:24d: 71     addc a,@r1
0:24e: bc b4  mov  r4,#$B4
0:250: 04 d9  jmp  $0D9
0:252: 05     en   i
0:253: 93     retr
0:254: 41     orl  a,@r1
0:255: bc f4  mov  r4,#$F4
0:257: 64 26  jmp  $326
0:259: 33     illegal
0:25a: 26 a4  jnt0 $2A4
0:25c: 08     ins  a,bus
0:25d: 5b     anl  a,r3
0:25e: 05     en   i
0:25f: 71     addc a,@r1
0:260: 20     xch  a,@r0
0:261: 01     idl
0:262: c3     illegal
0:263: 53 bc  anl  a,#$BC
0:265: f4 6a  call $76A
0:267: ac     mov  r4,a
0:268: 41     orl  a,@r1
0:269: 11     inc  @r1
0:26a: 26 11  jnt0 $211
0:26c: e4 bc  jmp  $7BC
0:26e: 02     outl bus,a
0:26f: b1 26  mov  @r1,#$26
0:271: f1     mov  a,@r1
0:272: af     mov  r7,a
0:273: 0f     movd a,p7
0:274: 05     en   i
0:275: e4 56  jmp  $756
0:277: c3     illegal
0:278: 95     cpl  f0
0:279: 07     dec  a
0:27a: e4 ab  jmp  $7AB
0:27c: 26 f1  jnt0 $2F1
0:27e: 07     dec  a
0:27f: b8 07  mov  r0,#$07
0:281: e9 93  djnz r1,$293
0:283: ff     mov  a,r7
0:284: f1     mov  a,@r1
0:285: fb     mov  a,r3
0:286: 95     cpl  f0
0:287: 56 0f  jt1  $20F
0:289: 06     illegal
0:28a: b8 f1  mov  r0,#$F1
0:28c: 47     swap a
0:28d: fd     mov  a,r5
0:28e: 07     dec  a
0:28f: e9 ff  djnz r1,$2FF
0:291: 97     clr  c
0:292: 8b     illegal
0:293: 8b     illegal
0:294: b2 71  jb5  $271
0:296: 71     addc a,@r1
0:297: bc 27  mov  r4,#$27
0:299: 72 b4  jb3  $2B4
0:29b: 41     orl  a,@r1
0:29c: f4 a0  call $7A0
0:29e: 0f     movd a,p7
0:29f: d2 b4  jb6  $2B4
0:2a1: 41     orl  a,@r1
0:2a2: ff     mov  a,r7
0:2a3: 96 b4  jnz  $2B4
0:2a5: d2 a6  jb6  $2A6
0:2a7: c3     illegal
0:2a8: c0     illegal
0:2a9: 03 04  add  a,#$04
0:2ab: e4 f1  jmp  $7F1
0:2ad: d6     illegal
0:2ae: 93     retr
0:2af: b4 ff  call $5FF
0:2b1: 11     inc  @r1
0:2b2: fd     mov  a,r5
0:2b3: bc 27  mov  r4,#$27
0:2b5: b1 32  mov  @r1,#$32
0:2b7: 91     movx @r1,a
0:2b8: bb 12  mov  r3,#$12
0:2ba: 91     movx @r1,a
0:2bb: 71     addc a,@r1
0:2bc: fd     mov  a,r5
0:2bd: c0     illegal
0:2be: 61     add  a,@r1
0:2bf: be f1  mov  r6,#$F1
0:2c1: d6     illegal
0:2c2: 93     retr
0:2c3: b4 03  call $503
0:2c5: 04 ca  jmp  $0CA
0:2c7: ff     mov  a,r7
0:2c8: 91     movx @r1,a
0:2c9: 26 f1  jnt0 $2F1
0:2cb: d6     illegal
0:2cc: e0     illegal
0:2cd: 06     illegal
0:2ce: e4 05  jmp  $705
0:2d0: c3     illegal
0:2d1: f1     mov  a,@r1
0:2d2: d6     illegal
0:2d3: 93     retr
0:2d4: e4 03  jmp  $703
0:2d6: 02     outl bus,a
0:2d7: e4 b4  jmp  $7B4
0:2d9: 71     addc a,@r1
0:2da: 27     clr  a
0:2db: 06     illegal
0:2dc: ff     mov  a,r7
0:2dd: b6 b8  jf0  $2B8
0:2df: f1     mov  a,@r1
0:2e0: e9 06  djnz r1,$206
0:2e2: e4 07  jmp  $707
0:2e4: 26 f1  jnt0 $2F1
0:2e6: 56 06  jt1  $206
0:2e8: ea f1  djnz r2,$2F1
0:2ea: f8     mov  a,r0
0:2eb: f9     mov  a,r1
0:2ec: b6 f3  jf0  $2F3
0:2ee: fa     mov  a,r2
0:2ef: fb     mov  a,r3
0:2f0: f2 e1  jb7  $2E1
0:2f2: 81     movx a,@r1
0:2f3: 61     add  a,@r1
0:2f4: f2 fa  jb7  $2FA
0:2f6: 0f     movd a,p7
0:2f7: 00     nop
0:2f8: 61     add  a,@r1
0:2f9: c1     illegal
0:2fa: 61     add  a,@r1
0:2fb: e1     illegal
0:2fc: 4e     orl  a,r6
0:2fd: 4c     orl  a,r4
0:2fe: 6b     add  a,r3
0:2ff: 25     en   tcnti
0:300: 26 d1  jnt0 $3D1
0:302: aa     mov  r2,a
0:303: 38     illegal
0:304: 02     outl bus,a
0:305: df     xrl  a,r7
0:306: be bd  mov  r6,#$BD
0:308: 05     en   i
0:309: 9d     anld p5,a
0:30a: 38     illegal
0:30b: 2b     xch  a,r3
0:30c: d1     xrl  a,@r1
0:30d: b8 bc  mov  r0,#$BC
0:30f: be 06  mov  r6,#$06
0:311: 24 07  jmp  $107
0:313: 2b     xch  a,r3
0:314: b9 bd  mov  r1,#$BD
0:316: bb 85  mov  r3,#$85
0:318: f1     mov  a,@r1
0:319: bc b4  mov  r4,#$B4
0:31b: 21     xch  a,@r1
0:31c: 71     addc a,@r1
0:31d: 27     clr  a
0:31e: 82     illegal
0:31f: ba 26  mov  r2,#$26
0:321: d1     xrl  a,@r1
0:322: aa     mov  r2,a
0:323: 39     outl p1,a
0:324: 06     illegal
0:325: df     xrl  a,r7
0:326: be bd  mov  r6,#$BD
0:328: 05     en   i
0:329: 9d     anld p5,a
0:32a: 38     illegal
0:32b: 01     idl
0:32c: d1     xrl  a,@r1
0:32d: bc bf  mov  r4,#$BF
0:32f: f4 06  call $706
0:331: 57     da   a
0:332: e3     movp3 a,@a
0:333: 1c     inc  r4
0:334: 08     ins  a,bus
0:335: a4 3b  jmp  $53B
0:337: f4 16  call $716
0:339: 57     da   a
0:33a: ef fb  djnz r7,$3FB
0:33c: 00     nop
0:33d: a4 31  jmp  $531
0:33f: ba 39  mov  r2,#$39
0:341: bd d1  mov  r5,#$D1
0:343: 26 ae  jnt0 $3AE
0:345: 05     en   i
0:346: b5     cpl  f1
0:347: 06     illegal
0:348: d1     xrl  a,@r1
0:349: 96 06  jnz  $306
0:34b: df     xrl  a,r7
0:34c: fd     mov  a,r5
0:34d: 26 d1  jnt0 $3D1
0:34f: aa     mov  r2,a
0:350: be bd  mov  r6,#$BD
0:352: d1     xrl  a,@r1
0:353: b8 39  mov  r0,#$39
0:355: 05     en   i
0:356: 9d     anld p5,a
0:357: 39     outl p1,a
0:358: bc be  mov  r4,#$BE
0:35a: b9 bd  mov  r1,#$BD
0:35c: 2b     xch  a,r3
0:35d: 02     outl bus,a
0:35e: 22     illegal
0:35f: 07     dec  a
0:360: bb 85  mov  r3,#$85
0:362: 8c     orld p4,a
0:363: 27     clr  a
0:364: 2b     xch  a,r3
0:365: f1     mov  a,@r1
0:366: bc b4  mov  r4,#$B4
0:368: 3e     movd p6,a
0:369: ba a6  mov  r2,#$A6
0:36b: 26 21  jnt0 $321
0:36d: ff     mov  a,r7
0:36e: 96 05  jnz  $305
0:370: d1     xrl  a,@r1
0:371: aa     mov  r2,a
0:372: 39     outl p1,a
0:373: 01     idl
0:374: df     xrl  a,r7
0:375: be bd  mov  r6,#$BD
0:377: d1     xrl  a,@r1
0:378: 9d     anld p5,a
0:379: 39     outl p1,a
0:37a: 2b     xch  a,r3
0:37b: 02     outl bus,a
0:37c: b8 bc  mov  r0,#$BC
0:37e: be b9  mov  r6,#$B9
0:380: 20     xch  a,@r0
0:381: 07     dec  a
0:382: 2b     xch  a,r3
0:383: f1     mov  a,@r1
0:384: bd bb  mov  r5,#$BB
0:386: 85     clr  f0
0:387: 71     addc a,@r1
0:388: bc b4  mov  r4,#$B4
0:38a: 21     xch  a,@r1
0:38b: 27     clr  a
0:38c: 27     clr  a
0:38d: 87     illegal
0:38e: ba 17  mov  r2,#$17
0:390: d1     xrl  a,@r1
0:391: aa     mov  r2,a
0:392: 39     outl p1,a
0:393: 05     en   i
0:394: df     xrl  a,r7
0:395: be bd  mov  r6,#$BD
0:397: d1     xrl  a,@r1
0:398: 9d     anld p5,a
0:399: 3d     movd p5,a
0:39a: 38     illegal
0:39b: 06     illegal
0:39c: b8 bc  mov  r0,#$BC
0:39e: bd 97  mov  r5,#$97
0:3a0: d1     xrl  a,@r1
0:3a1: d1     xrl  a,@r1
0:3a2: d1     xrl  a,@r1
0:3a3: fb     mov  a,r3
0:3a4: a9     mov  r1,a
0:3a5: 93     retr
0:3a6: 93     retr
0:3a7: ba 39  mov  r2,#$39
0:3a9: bd d1  mov  r5,#$D1
0:3ab: 27     clr  a
0:3ac: ae     mov  r6,a
0:3ad: 05     en   i
0:3ae: b5     cpl  f1
0:3af: 17     inc  a
0:3b0: d1     xrl  a,@r1
0:3b1: 96 f1  jnz  $3F1
0:3b3: 07     dec  a
0:3b4: fd     mov  a,r5
0:3b5: 27     clr  a
0:3b6: e4 b8  jmp  $7B8
0:3b8: 00     nop
0:3b9: e9 3f  djnz r1,$33F
0:3bb: 3d     movd p5,a
0:3bc: f1     mov  a,@r1
0:3bd: be b9  mov  r6,#$B9
0:3bf: d1     xrl  a,@r1
0:3c0: c2     illegal
0:3c1: 06     illegal
0:3c2: 3d     movd p5,a
0:3c3: 3d     movd p5,a
0:3c4: b9 b8  mov  r1,#$B8
0:3c6: bc bd  mov  r4,#$BD
0:3c8: 06     illegal
0:3c9: d1     xrl  a,@r1
0:3ca: e9 bc  djnz r1,$3BC
0:3cc: 97     clr  c
0:3cd: a9     mov  r1,a
0:3ce: c6 27  jz   $327
0:3d0: f4 b4  call $7B4
0:3d2: db     xrl  a,r3
0:3d3: d6     illegal
0:3d4: d6     illegal
0:3d5: c3     illegal
0:3d6: f4 0f  call $70F
0:3d8: c3     illegal
0:3d9: bc b4  mov  r4,#$B4
0:3db: 96 db  jnz  $3DB
0:3dd: 27     clr  a
0:3de: 00     nop
0:3df: 26 05  jnt0 $305
0:3e1: e4 db  jmp  $7DB
0:3e3: 3e     movd p6,a
0:3e4: f1     mov  a,@r1
0:3e5: d2 be  jb6  $3BE
0:3e7: b9 3c  mov  r1,#$3C
0:3e9: c2     illegal
0:3ea: 38     illegal
0:3eb: a4 d1  jmp  $5D1
0:3ed: bc 27  mov  r4,#$27
0:3ef: 1c     inc  r4
0:3f0: bf f4  mov  r7,#$F4
0:3f2: a4 ef  jmp  $5EF
0:3f4: 06     illegal
0:3f5: 47     swap a
0:3f6: 1c     inc  r4
0:3f7: f2 27  jb7  $327
0:3f9: cc     dec  r4
0:3fa: 3a     outl p2,a
0:3fb: 34 a4  call $1A4
0:3fd: b8 f0  mov  r0,#$F0
0:3ff: c8     dec  r0
0:400: cc     dec  r4
0:401: 34 17  call $117
0:403: df     xrl  a,r7
0:404: f0     mov  a,@r0
0:405: 27     clr  a
0:406: d1     xrl  a,@r1
0:407: ba 39  mov  r2,#$39
0:409: bd d1  mov  r5,#$D1
0:40b: 96 ae  jnz  $4AE
0:40d: 05     en   i
0:40e: b5     cpl  f1
0:40f: be 3e  mov  r6,#$3E
0:411: 3c     movd p4,a
0:412: c2     illegal
0:413: 3c     movd p4,a
0:414: b9 d1  mov  r1,#$D1
0:416: bc f4  mov  r4,#$F4
0:418: 85     clr  f0
0:419: 19     inc  r1
0:41a: b8 bc  mov  r0,#$BC
0:41c: c3     illegal
0:41d: 95     cpl  f0
0:41e: 3e     movd p6,a
0:41f: 2b     xch  a,r3
0:420: be bd  mov  r6,#$BD
0:422: b3     jmpp @a
0:423: ce     dec  r6
0:424: 06     illegal
0:425: 06     illegal
0:426: 28     xch  a,r0
0:427: ce     dec  r6
0:428: b9 bb  mov  r1,#$BB
0:42a: 85     clr  f0
0:42b: 8c     orld p4,a
0:42c: 2c     xch  a,r4
0:42d: 2b     xch  a,r3
0:42e: f1     mov  a,@r1
0:42f: 27     clr  a
0:430: 17     inc  a
0:431: df     xrl  a,r7
0:432: be bd  mov  r6,#$BD
0:434: d1     xrl  a,@r1
0:435: aa     mov  r2,a
0:436: 39     outl p1,a
0:437: 05     en   i
0:438: d1     xrl  a,@r1
0:439: b8 bc  mov  r0,#$BC
0:43b: be 9d  mov  r6,#$9D
0:43d: 39     outl p1,a
0:43e: 2e     xch  a,r6
0:43f: 06     illegal
0:440: b9 bd  mov  r1,#$BD
0:442: bb 85  mov  r3,#$85
0:444: 21     xch  a,@r1
0:445: 01     idl
0:446: 2e     xch  a,r6
0:447: f1     mov  a,@r1
0:448: 8c     orld p4,a
0:449: 28     xch  a,r0
0:44a: 01     idl
0:44b: 56 bc  jt1  $4BC
0:44d: bf f4  mov  r7,#$F4
0:44f: 0f     movd a,p7
0:450: c3     illegal
0:451: d6     illegal
0:452: 93     retr
0:453: 1c     inc  r4
0:454: 53 0f  anl  a,#$0F
0:456: 62     mov  t,a
0:457: ef 4d  djnz r7,$44D
0:459: 28     xch  a,r0
0:45a: 01     idl
0:45b: 0f     movd a,p7
0:45c: bc bf  mov  r4,#$BF
0:45e: b4 1c  call $51C
0:460: ef 21  djnz r7,$421
0:462: 27     clr  a
0:463: d1     xrl  a,@r1
0:464: 5d     anl  a,r5
0:465: ba 17  mov  r2,#$17
0:467: df     xrl  a,r7
0:468: aa     mov  r2,a
0:469: 39     outl p1,a
0:46a: 01     idl
0:46b: 9d     anld p5,a
0:46c: be bd  mov  r6,#$BD
0:46e: d1     xrl  a,@r1
0:46f: bc 3c  mov  r4,#$3C
0:471: 56 a4  jt1  $4A4
0:473: 02     outl bus,a
0:474: f4 f0  call $7F0
0:476: 26 d1  jnt0 $4D1
0:478: df     xrl  a,r7
0:479: be bd  mov  r6,#$BD
0:47b: d1     xrl  a,@r1
0:47c: aa     mov  r2,a
0:47d: 38     illegal
0:47e: 05     en   i
0:47f: 9d     anld p5,a
0:480: b8 bc  mov  r0,#$BC
0:482: bd 97  mov  r5,#$97
0:484: 3c     movd p4,a
0:485: 31     xchd a,@r1
0:486: 01     idl
0:487: d1     xrl  a,@r1
0:488: a9     mov  r1,a
0:489: 93     retr
0:48a: ba ae  mov  r2,#$AE
0:48c: d1     xrl  a,@r1
0:48d: fb     mov  a,r3
0:48e: 38     illegal
0:48f: bd 05  mov  r5,#$05
0:491: b5     cpl  f1
0:492: 02     outl bus,a
0:493: fd     mov  a,r5
0:494: d1     xrl  a,@r1
0:495: 26 d1  jnt0 $4D1
0:497: 26 05  jnt0 $405
0:499: df     xrl  a,r7
0:49a: be bd  mov  r6,#$BD
0:49c: d1     xrl  a,@r1
0:49d: aa     mov  r2,a
0:49e: 39     outl p1,a
0:49f: 01     idl
0:4a0: d1     xrl  a,@r1
0:4a1: bc bf  mov  r4,#$BF
0:4a3: 97     clr  c
0:4a4: 9d     anld p5,a
0:4a5: 38     illegal
0:4a6: 01     idl
0:4a7: a7     cpl  c
0:4a8: 1c     inc  r4
0:4a9: 16 57  jtf  $457
0:4ab: e3     movp3 a,@a
0:4ac: f4 00  call $700
0:4ae: a4 b2  jmp  $5B2
0:4b0: ef fb  djnz r7,$4FB
0:4b2: 39     outl p1,a
0:4b3: bd a8  mov  r5,#$A8
0:4b5: ba ae  mov  r2,#$AE
0:4b7: 01     idl
0:4b8: d1     xrl  a,@r1
0:4b9: 26 d1  jnt0 $4D1
0:4bb: be b5  mov  r6,#$B5
0:4bd: 05     en   i
0:4be: fd     mov  a,r5
0:4bf: 3c     movd p4,a
0:4c0: b9 fe  mov  r1,#$FE
0:4c2: 27     clr  a
0:4c3: e9 0a  djnz r1,$40A
0:4c5: a8     mov  r0,a
0:4c6: f1     mov  a,@r1
0:4c7: ce     dec  r6
0:4c8: e9 71  djnz r1,$471
0:4ca: 26 f1  jnt0 $4F1
0:4cc: c2     illegal
0:4cd: da     xrl  a,r2
0:4ce: 0e     movd a,p6
0:4cf: e4 07  jmp  $707
0:4d1: d8     xrl  a,r0
0:4d2: f1     mov  a,@r1
0:4d3: ec 93  djnz r4,$493
0:4d5: ac     mov  r4,a
0:4d6: f1     mov  a,@r1
0:4d7: d1     xrl  a,@r1
0:4d8: b8 f1  mov  r0,#$F1
0:4da: 96 a6  jnz  $4A6
0:4dc: 0e     movd a,p6
0:4dd: e9 ff  djnz r1,$4FF
0:4df: 96 26  jnz  $426
0:4e1: f1     mov  a,@r1
0:4e2: 17     inc  a
0:4e3: d6     illegal
0:4e4: 06     illegal
0:4e5: e4 af  jmp  $7AF
0:4e7: 03 93  add  a,#$93
0:4e9: 71     addc a,@r1
0:4ea: 27     clr  a
0:4eb: f0     mov  a,@r0
0:4ec: ef da  djnz r7,$4DA
0:4ee: 81     movx a,@r1
0:4ef: ff     mov  a,r7
0:4f0: b8 f1  mov  r0,#$F1
0:4f2: 96 f1  jnz  $4F1
0:4f4: 06     illegal
0:4f5: e9 53  djnz r1,$453
0:4f7: 11     inc  @r1
0:4f8: d6     illegal
0:4f9: f1     mov  a,@r1
0:4fa: 01     idl
0:4fb: e4 c3  jmp  $7C3
0:4fd: 26 f1  jnt0 $4F1
0:4ff: 07     dec  a
0:500: c3     illegal
0:501: b8 f1  mov  r0,#$F1
0:503: 96 07  jnz  $507
0:505: 01     idl
0:506: e9 f1  djnz r1,$5F1
0:508: c8     dec  r0
0:509: 27     clr  a
0:50a: b4 72  call $572
0:50c: bc f4  mov  r4,#$F4
0:50e: 10     inc  @r0
0:50f: 12 b4  jb0  $5B4
0:511: 11     inc  @r1
0:512: 71     addc a,@r1
0:513: 96 08  jnz  $508
0:515: bc 8b  mov  r4,#$8B
0:517: 11     inc  @r1
0:518: d6     illegal
0:519: 23 03  mov  a,#$03
0:51b: e4 c3  jmp  $7C3
0:51d: 26 f1  jnt0 $5F1
0:51f: 07     dec  a
0:520: c3     illegal
0:521: b8 f1  mov  r0,#$F1
0:523: 96 27  jnz  $527
0:525: 03 e9  add  a,#$E9
0:527: 26 01  jnt0 $501
0:529: df     xrl  a,r7
0:52a: be bd  mov  r6,#$BD
0:52c: d1     xrl  a,@r1
0:52d: aa     mov  r2,a
0:52e: 39     outl p1,a
0:52f: 01     idl
0:530: d1     xrl  a,@r1
0:531: bc bf  mov  r4,#$BF
0:533: 97     clr  c
0:534: 9d     anld p5,a
0:535: 38     illegal
0:536: 01     idl
0:537: a7     cpl  c
0:538: 1c     inc  r4
0:539: 16 57  jtf  $557
0:53b: e3     movp3 a,@a
0:53c: f4 00  call $700
0:53e: a4 42  jmp  $542
0:540: ef fb  djnz r7,$5FB
0:542: 39     outl p1,a
0:543: bd 38  mov  r5,#$38
0:545: ba ae  mov  r2,#$AE
0:547: 01     idl
0:548: d1     xrl  a,@r1
0:549: 26 d1  jnt0 $5D1
0:54b: 26 b5  jnt0 $5B5
0:54d: 01     idl
0:54e: fd     mov  a,r5
0:54f: 48     orl  a,r0
0:550: a1     mov  @r1,a
0:551: bc f4  mov  r4,#$F4
0:553: 82     illegal
0:554: 22     illegal
0:555: 02     outl bus,a
0:556: d2 d6  jb6  $5D6
0:558: 40     orl  a,@r0
0:559: 27     clr  a
0:55a: e4 39  jmp  $739
0:55c: a4 f1  jmp  $5F1
0:55e: ba 12  mov  r2,#$12
0:560: 66     illegal
0:561: 3f     movd p7,a
0:562: 39     outl p1,a
0:563: 06     illegal
0:564: ba be  mov  r2,#$BE
0:566: bd d1  mov  r5,#$D1
0:568: 9d     anld p5,a
0:569: 39     outl p1,a
0:56a: 56 a4  jt1  $5A4
0:56c: bc f4  mov  r4,#$F4
0:56e: 0f     movd a,p7
0:56f: b8 39  mov  r0,#$39
0:571: 3c     movd p4,a
0:572: 06     illegal
0:573: a4 bc  jmp  $5BC
0:575: bf f0  mov  r7,#$F0
0:577: c8     dec  r0
0:578: cc     dec  r4
0:579: 75     ent0 clk
0:57a: 31     xchd a,@r1
0:57b: 3a     outl p2,a
0:57c: ef bc  djnz r7,$5BC
0:57e: b4 1c  call $51C
0:580: b4 bc  call $5BC
0:582: f4 95  call $795
0:584: 05     en   i
0:585: 32 12  jb1  $512
0:587: b1 8e  mov  @r1,#$8E
0:589: ce     dec  r6
0:58a: 31     xchd a,@r1
0:58b: ac     mov  r4,a
0:58c: a1     mov  @r1,a
0:58d: bc f4  mov  r4,#$F4
0:58f: 06     illegal
0:590: fd     mov  a,r5
0:591: f0     mov  a,@r0
0:592: 96 03  jnz  $503
0:594: a8     mov  r0,a
0:595: a4 f1  jmp  $5F1
0:597: d6     illegal
0:598: 04 93  jmp  $093
0:59a: 95     cpl  f0
0:59b: c8     dec  r0
0:59c: 85     clr  f0
0:59d: 9f     anld p7,a
0:59e: f1     mov  a,@r1
0:59f: 95     cpl  f0
0:5a0: bc f4  mov  r4,#$F4
0:5a2: b3     jmpp @a
0:5a3: 07     dec  a
0:5a4: 35     dis  tcnti
0:5a5: af     mov  r7,a
0:5a6: bc 93  mov  r4,#$93
0:5a8: ae     mov  r6,a
0:5a9: f5     sel  mb1
0:5aa: 37     cpl  a
0:5ab: ce     dec  r6
0:5ac: a1     mov  @r1,a
0:5ad: a4 12  jmp  $512
0:5af: b1 8e  mov  @r1,#$8E
0:5b1: 31     xchd a,@r1
0:5b2: a1     mov  @r1,a
0:5b3: ff     mov  a,r7
0:5b4: bc 14  mov  r4,#$14
0:5b6: ce     dec  r6
0:5b7: a6     illegal
0:5b8: 96 31  jnz  $531
0:5ba: a8     mov  r0,a
0:5bb: f4 bc  call $7BC
0:5bd: f4 ac  call $7AC
0:5bf: 2f     xch  a,r7
0:5c0: 12 2f  jb0  $52F
0:5c2: f0     mov  a,@r0
0:5c3: ca     dec  r2
0:5c4: c7     mov  a,psw
0:5c5: 46 a1  jnt1 $5A1
0:5c7: 2f     xch  a,r7
0:5c8: 46 a0  jnt1 $5A0
0:5ca: 03 06  add  a,#$06
0:5cc: 0f     movd a,p7
0:5cd: f1     mov  a,@r1
0:5ce: d6     illegal
0:5cf: 93     retr
0:5d0: b8 c8  mov  r0,#$C8
0:5d2: b4 cc  call $5CC
0:5d4: f1     mov  a,@r1
0:5d5: cc     dec  r4
0:5d6: fb     mov  a,r3
0:5d7: b4 ff  call $5FF
0:5d9: 31     xchd a,@r1
0:5da: 06     illegal
0:5db: a8     mov  r0,a
0:5dc: bc f4  mov  r4,#$F4
0:5de: fd     mov  a,r5
0:5df: ac     mov  r4,a
0:5e0: f4 bc  call $7BC
0:5e2: f4 ed  call $7ED
0:5e4: af     mov  r7,a
0:5e5: 35     dis  tcnti
0:5e6: 12 ff  jb0  $5FF
0:5e8: 06     illegal
0:5e9: 57     da   a
0:5ea: 96 47  jnz  $547
0:5ec: 0a     in   a,p2
0:5ed: a0     mov  @r0,a
0:5ee: ff     mov  a,r7
0:5ef: 06     illegal
0:5f0: 0a     in   a,p2
0:5f1: 47     swap a
0:5f2: 96 02  jnz  $502
0:5f4: 57     da   a
0:5f5: a0     mov  @r0,a
0:5f6: bc f4  mov  r4,#$F4
0:5f8: 56 a4  jt1  $5A4
0:5fa: f1     mov  a,@r1
0:5fb: 46 9f  jnt1 $59F
0:5fd: 27     clr  a
0:5fe: e4 02  jmp  $702
0:600: ad     mov  r5,a
0:601: 00     nop
0:602: e9 39  djnz r1,$639
0:604: b8 f1  mov  r0,#$F1
0:606: be fd  mov  r6,#$FD
0:608: 12 be  jb0  $6BE
0:60a: ba bd  mov  r2,#$BD
0:60c: 09     in   a,p1
0:60d: 3f     movd p7,a
0:60e: 3c     movd p4,a
0:60f: 06     illegal
0:610: d1     xrl  a,@r1
0:611: 71     addc a,@r1
0:612: 96 39  jnz  $639
0:614: b5     cpl  f1
0:615: be b8  mov  r6,#$B8
0:617: bc 2b  mov  r4,#$2B
0:619: 04 27  jmp  $027
0:61b: 06     illegal
0:61c: be b9  mov  r6,#$B9
0:61e: bd bb  mov  r5,#$BB
0:620: 2e     xch  a,r6
0:621: f1     mov  a,@r1
0:622: b8 bc  mov  r0,#$BC
0:624: 85     clr  f0
0:625: 8c     orld p4,a
0:626: 3a     outl p2,a
0:627: 2c     xch  a,r4
0:628: be b9  mov  r6,#$B9
0:62a: bd bb  mov  r5,#$BB
0:62c: 04 28  jmp  $028
0:62e: 02     outl bus,a
0:62f: 2a     xch  a,r2
0:630: 85     clr  f0
0:631: 71     addc a,@r1
0:632: 2e     xch  a,r6
0:633: 0f     movd a,p7
0:634: f1     mov  a,@r1
0:635: bc b4  mov  r4,#$B4
0:637: cc     dec  r4
0:638: b4 bc  call $5BC
0:63a: b8 f0  mov  r0,#$F0
0:63c: 1f     inc  r7
0:63d: 27     clr  a
0:63e: 32 bf  jb1  $6BF
0:640: 00     nop
0:641: 45     strt cnt
0:642: 2f     xch  a,r7
0:643: a4 12  jmp  $512
0:645: bf ff  mov  r7,#$FF
0:647: 21     xch  a,@r1
0:648: ba 01  mov  r2,#$01
0:64a: df     xrl  a,r7
0:64b: be 26  mov  r6,#$26
0:64d: d1     xrl  a,@r1
0:64e: aa     mov  r2,a
0:64f: 39     outl p1,a
0:650: bd d1  mov  r5,#$D1
0:652: b8 bc  mov  r0,#$BC
0:654: 01     idl
0:655: 9d     anld p5,a
0:656: 39     outl p1,a
0:657: 2b     xch  a,r3
0:658: be b9  mov  r6,#$B9
0:65a: bd bb  mov  r5,#$BB
0:65c: 04 26  jmp  $026
0:65e: 07     dec  a
0:65f: 2b     xch  a,r3
0:660: 85     clr  f0
0:661: 8c     orld p4,a
0:662: 27     clr  a
0:663: 9e     anld p6,a
0:664: f1     mov  a,@r1
0:665: bc b4  mov  r4,#$B4
0:667: 21     xch  a,@r1
0:668: ba 84  mov  r2,#$84
0:66a: 3a     outl p2,a
0:66b: ff     mov  a,r7
0:66c: 83     ret
0:66d: 84 ff  jmp  $4FF
0:66f: ff     mov  a,r7
0:670: 39     outl p1,a
0:671: 84 3a  jmp  $43A
0:673: ff     mov  a,r7
0:674: b9 8c  mov  r1,#$8C
0:676: ff     mov  a,r7
0:677: ff     mov  a,r7
0:678: 39     outl p1,a
0:679: 29     xch  a,r1
0:67a: 9c     anld p4,a
0:67b: 39     outl p1,a
0:67c: 9c     anld p4,a
0:67d: b5     cpl  f1
0:67e: ff     mov  a,r7
0:67f: ab     mov  r3,a
0:680: ff     mov  a,r7
0:681: fa     mov  a,r2
0:682: 6c     add  a,r4
0:683: bc e1  mov  r4,#$E1
0:685: 06     illegal
0:686: a8     mov  r0,a
0:687: 27     clr  a
0:688: bf f8  mov  r7,#$F8
0:68a: 17     inc  a
0:68b: c8     dec  r0
0:68c: 08     ins  a,bus
0:68d: a6     illegal
0:68e: a4 cc  jmp  $5CC
0:690: ef 96  djnz r7,$696
0:692: a6     illegal
0:693: f4 8a  call $78A
0:695: ff     mov  a,r7
0:696: 96 16  jnz  $616
0:698: 00     nop
0:699: a4 86  jmp  $586
0:69b: f1     mov  a,@r1
0:69c: 57     da   a
0:69d: 1c     inc  r4
0:69e: fa     mov  a,r2
0:69f: e4 06  jmp  $706
0:6a1: 57     da   a
0:6a2: ac     mov  r4,a
0:6a3: a4 00  jmp  $500
0:6a5: 2e     xch  a,r6
0:6a6: 2e     xch  a,r6
0:6a7: ca     dec  r2
0:6a8: ce     dec  r6
0:6a9: 9d     anld p5,a
0:6aa: f4 57  call $757
0:6ac: ed 96  djnz r5,$696
0:6ae: 70     addc a,@r0
0:6af: a4 18  jmp  $518
0:6b1: ed 86  djnz r5,$686
0:6b3: ac     mov  r4,a
0:6b4: 1c     inc  r4
0:6b5: a9     mov  r1,a
0:6b6: fa     mov  a,r2
0:6b7: f4 2e  call $72E
0:6b9: 2e     xch  a,r6
0:6ba: e9 ce  djnz r1,$6CE
0:6bc: a8     mov  r0,a
0:6bd: f1     mov  a,@r1
0:6be: ca     dec  r2
0:6bf: ed b5  djnz r5,$6B5
0:6c1: 27     clr  a
0:6c2: e4 32  jmp  $732
0:6c4: 96 f1  jnz  $6F1
0:6c6: 85     clr  f0
0:6c7: cc     dec  r4
0:6c8: 95     cpl  f0
0:6c9: 39     outl p1,a
0:6ca: cf     dec  r7
0:6cb: 3f     movd p7,a
0:6cc: ba 12  mov  r2,#$12
0:6ce: ba bd  mov  r2,#$BD
0:6d0: 06     illegal
0:6d1: 9d     anld p5,a
0:6d2: d3 f9  xrl  a,#$F9
0:6d4: d1     xrl  a,@r1
0:6d5: b3     jmpp @a
0:6d6: 96 a8  jnz  $6A8
0:6d8: ac     mov  r4,a
0:6d9: 06     illegal
0:6da: d1     xrl  a,@r1
0:6db: 96 bd  jnz  $6BD
0:6dd: 97     clr  c
0:6de: a9     mov  r1,a
0:6df: ab     mov  r3,a
0:6e0: e7     rl   a
0:6e1: d1     xrl  a,@r1
0:6e2: 59     anl  a,r1
0:6e3: ec ad  djnz r4,$6AD
0:6e5: f2 c3  jb7  $6C3
0:6e7: 27     clr  a
0:6e8: 17     inc  a
0:6e9: d6     illegal
0:6ea: f1     mov  a,@r1
0:6eb: 2b     xch  a,r3
0:6ec: ab     mov  r3,a
0:6ed: 04 20  jmp  $020
0:6ef: f1     mov  a,@r1
0:6f0: 20     xch  a,@r0
0:6f1: 27     clr  a
0:6f2: f1     mov  a,@r1
0:6f3: a9     mov  r1,a
0:6f4: 96 17  jnz  $617
0:6f6: e4 26  jmp  $726
0:6f8: 80     movx a,@r0
0:6f9: eb 96  djnz r3,$696
0:6fb: d1     xrl  a,@r1
0:6fc: e7     rl   a
0:6fd: fc     mov  a,r4
0:6fe: ab     mov  r3,a
0:6ff: f2 d9  jb7  $7D9
0:701: 04 e9  jmp  $0E9
0:703: bc b8  mov  r4,#$B8
0:705: f1     mov  a,@r1
0:706: 96 36  jnz  $736
0:708: f4 6f  call $76F
0:70a: f1     mov  a,@r1
0:70b: 12 96  jb0  $796
0:70d: af     mov  r7,a
0:70e: dc     xrl  a,r4
0:70f: 0a     in   a,p2
0:710: 52 ff  jb2  $7FF
0:712: 3c     movd p4,a
0:713: 2f     xch  a,r7
0:714: 0a     in   a,p2
0:715: 96 31  jnz  $731
0:717: 2a     xch  a,r2
0:718: 25     en   tcnti
0:719: 1e     inc  r6
0:71a: 16 e1  jtf  $7E1
0:71c: 20     xch  a,@r0
0:71d: 17     inc  a
0:71e: 0f     movd a,p7
0:71f: fa     mov  a,r2
0:720: 6d     add  a,r5
0:721: 12 96  jb0  $796
0:723: 05     en   i
0:724: 06     illegal
0:725: a6     illegal
0:726: 26 f1  jnt0 $7F1
0:728: e4 00  jmp  $700
0:72a: b8 b0  mov  r0,#$B0
0:72c: 06     illegal
0:72d: 57     da   a
0:72e: 39     outl p1,a
0:72f: 00     nop
0:730: c8     dec  r0
0:731: c8     dec  r0
0:732: 31     xchd a,@r1
0:733: bc a0  mov  r4,#$A0
0:735: b0 c8  mov  @r0,#$C8
0:737: 1d     inc  r5
0:738: 11     inc  @r1
0:739: 06     illegal
0:73a: 57     da   a
0:73b: 42     mov  a,t
0:73c: b0 06  mov  @r0,#$06
0:73e: 33     illegal
0:73f: 06     illegal
0:740: 50     anl  a,@r0
0:741: a0     mov  @r0,a
0:742: 39     outl p1,a
0:743: 2b     xch  a,r3
0:744: 57     da   a
0:745: b8 bc  mov  r0,#$BC
0:747: be 04  mov  r6,#$04
0:749: 27     clr  a
0:74a: 07     dec  a
0:74b: 2b     xch  a,r3
0:74c: b9 bd  mov  r1,#$BD
0:74e: bb 85  mov  r3,#$85
0:750: f1     mov  a,@r1
0:751: bc b4  mov  r4,#$B4
0:753: f1     mov  a,@r1
0:754: 8c     orld p4,a
0:755: 27     clr  a
0:756: af     mov  r7,a
0:757: 03 d6  add  a,#$D6
0:759: 93     retr
0:75a: bc 11  mov  r4,#$11
0:75c: 06     illegal
0:75d: 61     add  a,@r1
0:75e: 1d     inc  r5
0:75f: b0 17  mov  @r0,#$17
0:761: f1     mov  a,@r1
0:762: f1     mov  a,@r1
0:763: d6     illegal
0:764: 94 c8  call $4C8
0:766: 03 02  add  a,#$02
0:768: 93     retr
0:769: b8 80  mov  r0,#$80
0:76b: 3f     movd p7,a
0:76c: 72 2e  jb3  $72E
0:76e: 17     inc  a
0:76f: 90     movx @r0,a
0:770: f1     mov  a,@r1
0:771: 21     xch  a,@r1
0:772: 19     inc  r1
0:773: 56 c8  jt1  $7C8
0:775: ba f0  mov  r2,#$F0
0:777: f0     mov  a,@r0
0:778: b3     jmpp @a
0:779: ee 95  djnz r6,$795
0:77b: 82     illegal
0:77c: 82     illegal
0:77d: 7f     addc a,r7
0:77e: e1     illegal
0:77f: c3     illegal
0:780: 8c     orld p4,a
0:781: 47     swap a
0:782: ed e1  djnz r5,$7E1
0:784: 95     cpl  f0
0:785: a4 88  jmp  $588
0:787: a0     mov  @r0,a
0:788: cc     dec  r4
0:789: f0     mov  a,@r0
0:78a: 0f     movd a,p7
0:78b: 97     clr  c
0:78c: 19     inc  r1
0:78d: 56 b3  jt1  $7B3
0:78f: ee 91  djnz r6,$791
0:791: e1     illegal
0:792: c3     illegal
0:793: 95     cpl  f0
0:794: 95     cpl  f0
0:795: 97     clr  c
0:796: 9d     anld p5,a
0:797: a4 ed  jmp  $5ED
0:799: e1     illegal
0:79a: cc     dec  r4
0:79b: e1     illegal
0:79c: 99 a0  anl  p1,#$A0
0:79e: c8     dec  r0
0:79f: 71     addc a,@r1
0:7a0: fb     mov  a,r3
0:7a1: f4 a9  call $7A9
0:7a3: 0f     movd a,p7
0:7a4: ac     mov  r4,a
0:7a5: 93     retr
0:7a6: b4 fb  call $5FB
0:7a8: cb     dec  r3
0:7a9: 93     retr
0:7aa: 27     clr  a
0:7ab: f9     mov  a,r1
0:7ac: d9     xrl  a,r1
0:7ad: a0     mov  @r0,a
0:7ae: af     mov  r7,a
0:7af: d6     illegal
0:7b0: 28     xch  a,r0
0:7b1: b1 f9  mov  @r1,#$F9
0:7b3: 29     xch  a,r1
0:7b4: 93     retr
0:7b5: 1f     inc  r7
0:7b6: d6     illegal
0:7b7: 93     retr
0:7b8: ba ff  mov  r2,#$FF
0:7ba: c6 ac  jz   $7AC
0:7bc: 1f     inc  r7
0:7bd: 93     retr
0:7be: f9     mov  a,r1
0:7bf: f4 06  call $706
0:7c1: a4 a7  jmp  $5A7
0:7c3: fa     mov  a,r2
0:7c4: 10     inc  @r0
0:7c5: 11     inc  @r1
0:7c6: 93     retr
0:7c7: 96 bc  jnz  $7BC
0:7c9: b4 96  call $596
0:7cb: a6     illegal
0:7cc: 36 ff  jt0  $7FF
0:7ce: ff     mov  a,r7
0:7cf: 96 f2  jnz  $7F2
0:7d1: d2 e7  jb6  $7E7
0:7d3: e7     rl   a
0:7d4: fa     mov  a,r2
0:7d5: fa     mov  a,r2
0:7d6: 17     inc  a
0:7d7: ac     mov  r4,a
0:7d8: 86 03  jni  $703
0:7da: c3     illegal
0:7db: f1     mov  a,@r1
0:7dc: f1     mov  a,@r1
0:7dd: 17     inc  a
0:7de: dc     xrl  a,r4
0:7df: c8     dec  r0
0:7e0: 96 d0  jnz  $7D0
0:7e2: b0 1c  mov  @r0,#$1C
0:7e4: f1     mov  a,@r1
0:7e5: 11     inc  @r1
0:7e6: a8     mov  r0,a
0:7e7: 11     inc  @r1
0:7e8: b0 68  mov  @r0,#$68
0:7ea: 28     xch  a,r0
0:7eb: d0     xrl  a,@r0
0:7ec: 47     swap a
0:7ed: 86 f1  jni  $7F1
0:7ef: f8     mov  a,r0
0:7f0: 3f     movd p7,a
0:7f1: 1c     inc  r4
0:7f2: 3f     movd p7,a
0:7f3: 86 94  jni  $794
0:7f5: 47     swap a
0:7f6: 94 71  call $471
0:7f8: 9d     anld p5,a
0:7f9: 26 3a  jnt0 $73A
0:7fb: e8 94  djnz r0,$794
0:7fd: 4f     orl  a,r7
0:7fe: 01     idl
0:7ff: ff     mov  a,r7
