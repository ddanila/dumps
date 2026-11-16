
BANK 0 CPU 0000 FILE 000000
0x00000000      02002e         ljmp 0x002e
0x00000003      020c20         ljmp 0x0c20
0x00000006      00             nop
0x00000007      00             nop
0x00000008      00             nop
0x00000009      00             nop
0x0000000a      00             nop
0x0000000b      02061b         ljmp 0x061b
0x0000000e      00             nop
0x0000000f      00             nop
0x00000010      00             nop
0x00000011      00             nop
0x00000012      00             nop
0x00000013      020648         ljmp 0x0648
0x00000016      00             nop
0x00000017      00             nop
0x00000018      00             nop
0x00000019      00             nop
0x0000001a      00             nop
0x0000001b      00             nop
0x0000001c      00             nop
0x0000001d      00             nop
0x0000001e      00             nop
0x0000001f      00             nop
0x00000020      00             nop
0x00000021      00             nop
0x00000022      00             nop
0x00000023      020c6a         ljmp 0x0c6a
0x00000026      00             nop
0x00000027      00             nop
0x00000028      00             nop
0x00000029      00             nop
0x0000002a      00             nop
0x0000002b      02067f         ljmp 0x067f
0x0000002e      c2b1           clr 0xb0.1
0x00000030      c2d3           clr 0xd0.3
0x00000032      c2d4           clr 0xd0.4
0x00000034      906000         mov dptr, #0x6000
0x00000037      74ff           mov a, #0xff
0x00000039      f0             movx @dptr, a
0x0000003a      a3             inc dptr
0x0000003b      e583           mov a, 0x83
0x0000003d      b480f7         cjne a, #0x80, 0x0037
0x00000040      7800           mov r0, #0x00
0x00000042      7600           mov @r0, #0x00
0x00000044      d8fc           djnz r0, 0x0042
0x00000046      75d000         mov 0xd0, #0x00
0x00000049      7581a9         mov 0x81, #0xa9
0x0000004c      1207bb         lcall 0x07bb
0x0000004f      120d20         lcall 0x0d20
0x00000052      7581a9         mov 0x81, #0xa9
0x00000055      75d000         mov 0xd0, #0x00
0x00000058      90740d         mov dptr, #0x740d
0x0000005b      ae83           mov r6, 0x83
0x0000005d      af82           mov r7, 0x82
0x0000005f      9068d0         mov dptr, #0x68d0
0x00000062      120098         lcall 0x0098
0x00000065      6005           jz 0x006c
0x00000067      e4             clr a
0x00000068      f0             movx @dptr, a
0x00000069      a3             inc dptr
0x0000006a      80f6           sjmp 0x0062
0x0000006c      9000f6         mov dptr, #0x00f6
0x0000006f      1200a1         lcall 0x00a1
0x00000072      9000fa         mov dptr, #0x00fa
0x00000075      1200a1         lcall 0x00a1
0x00000078      9000fe         mov dptr, #0x00fe
0x0000007b      1200bf         lcall 0x00bf
0x0000007e      900104         mov dptr, #0x0104
0x00000081      1200bf         lcall 0x00bf
0x00000084      75d000         mov 0xd0, #0x00
0x00000087      7581a9         mov 0x81, #0xa9
0x0000008a      1207bb         lcall 0x07bb
0x0000008d      7400           mov a, #0x00
0x0000008f      90fee2         mov dptr, #0xfee2
0x00000092      1207c5         lcall 0x07c5
0x00000095      02010a         ljmp 0x010a
0x00000098      ef             mov a, r7
0x00000099      6582           xrl a, 0x82
0x0000009b      7003           jnz 0x00a0
0x0000009d      ee             mov a, r6
0x0000009e      6583           xrl a, 0x83
0x000000a0      22             ret
0x000000a1      e4             clr a
0x000000a2      93             movc a, @a+dptr
0x000000a3      f8             mov r0, a
0x000000a4      7401           mov a, #0x01
0x000000a6      93             movc a, @a+dptr
0x000000a7      f9             mov r1, a
0x000000a8      7402           mov a, #0x02
0x000000aa      93             movc a, @a+dptr
0x000000ab      fe             mov r6, a
0x000000ac      7403           mov a, #0x03
0x000000ae      93             movc a, @a+dptr
0x000000af      f582           mov 0x82, a
0x000000b1      8e83           mov 0x83, r6
0x000000b3      e8             mov a, r0
0x000000b4      69             xrl a, r1
0x000000b5      7001           jnz 0x00b8
0x000000b7      22             ret
0x000000b8      e4             clr a
0x000000b9      93             movc a, @a+dptr
0x000000ba      f6             mov @r0, a
0x000000bb      a3             inc dptr
0x000000bc      08             inc r0
0x000000bd      80f4           sjmp 0x00b3
0x000000bf      e4             clr a
0x000000c0      93             movc a, @a+dptr
0x000000c1      fc             mov r4, a
0x000000c2      7401           mov a, #0x01
0x000000c4      93             movc a, @a+dptr
0x000000c5      fd             mov r5, a
0x000000c6      7402           mov a, #0x02
0x000000c8      93             movc a, @a+dptr
0x000000c9      fe             mov r6, a
0x000000ca      7403           mov a, #0x03
0x000000cc      93             movc a, @a+dptr
0x000000cd      ff             mov r7, a
0x000000ce      7404           mov a, #0x04
0x000000d0      93             movc a, @a+dptr
0x000000d1      f8             mov r0, a
0x000000d2      7405           mov a, #0x05
0x000000d4      93             movc a, @a+dptr
0x000000d5      f582           mov 0x82, a
0x000000d7      8883           mov 0x83, r0
0x000000d9      120098         lcall 0x0098
0x000000dc      7001           jnz 0x00df
0x000000de      22             ret
0x000000df      e4             clr a
0x000000e0      93             movc a, @a+dptr
0x000000e1      a3             inc dptr
0x000000e2      a883           mov r0, 0x83
0x000000e4      a982           mov r1, 0x82
0x000000e6      8c83           mov 0x83, r4
0x000000e8      8d82           mov 0x82, r5
0x000000ea      f0             movx @dptr, a
0x000000eb      a3             inc dptr
0x000000ec      ac83           mov r4, 0x83
0x000000ee      ad82           mov r5, 0x82
0x000000f0      8883           mov 0x83, r0
0x000000f2      8982           mov 0x82, r1
0x000000f4      80e3           sjmp 0x00d9
0x000000f6      6e             xrl a, r6
0x000000f7      6e             xrl a, r6
0x000000f8      29             add a, r1
0x000000f9      d5aaaa         djnz 0xaa, 0x00a6
0x000000fc      29             add a, r1
0x000000fd      d5740d         djnz 0x74, 0x010d
0x00000100      2e             add a, r6
0x00000101      fc             mov r4, a
0x00000102      29             add a, r1
0x00000103      d57934         djnz 0x79, 0x013a
0x00000106      66             xrl a, @r0
0x00000107      8266           anl c, 0x2c.6
0x00000109      82             invalid

BANK 0 CPU 061b FILE 00061b
0x0000061b      d24d           setb 0x29.5
0x0000061d      758a00         mov 0x8a, #0x00
0x00000620      758c40         mov 0x8c, #0x40
0x00000623      c0d0           push 0xd0
0x00000625      c0e0           push 0xe0
0x00000627      c083           push 0x83
0x00000629      c082           push 0x82
0x0000062b      d2d3           setb 0xd0.3
0x0000062d      c2d4           clr 0xd0.4
0x0000062f      7a0d           mov r2, #0x0d
0x00000631      9068d2         mov dptr, #0x68d2
0x00000634      e0             movx a, @dptr
0x00000635      6002           jz 0x0639
0x00000637      14             dec a
0x00000638      f0             movx @dptr, a
0x00000639      a3             inc dptr
0x0000063a      daf8           djnz r2, 0x0634
0x0000063c      120c34         lcall 0x0c34
0x0000063f      d082           pop 0x82
0x00000641      d083           pop 0x83
0x00000643      d0e0           pop 0xe0
0x00000645      d0d0           pop 0xd0
0x00000647      32             reti
0x00000648      d24d           setb 0x29.5
0x0000064a      c0d0           push 0xd0
0x0000064c      c0e0           push 0xe0
0x0000064e      c083           push 0x83
0x00000650      c082           push 0x82
0x00000652      d203           setb 0x20.3
0x00000654      9068e3         mov dptr, #0x68e3
0x00000657      e0             movx a, @dptr
0x00000658      04             inc a
0x00000659      f0             movx @dptr, a
0x0000065a      701a           jnz 0x0676
0x0000065c      d204           setb 0x20.4
0x0000065e      9068e2         mov dptr, #0x68e2
0x00000661      e0             movx a, @dptr
0x00000662      04             inc a
0x00000663      f0             movx @dptr, a
0x00000664      7010           jnz 0x0676
0x00000666      9068e1         mov dptr, #0x68e1
0x00000669      e0             movx a, @dptr
0x0000066a      04             inc a
0x0000066b      f0             movx @dptr, a
0x0000066c      7008           jnz 0x0676
0x0000066e      9068e0         mov dptr, #0x68e0
0x00000671      e0             movx a, @dptr
0x00000672      04             inc a
0x00000673      540f           anl a, #0x0f
0x00000675      f0             movx @dptr, a
0x00000676      d082           pop 0x82
0x00000678      d083           pop 0x83
0x0000067a      d0e0           pop 0xe0
0x0000067c      d0d0           pop 0xd0
0x0000067e      32             reti
0x0000067f      c0d0           push 0xd0
0x00000681      c0e0           push 0xe0
0x00000683      c083           push 0x83
0x00000685      c082           push 0x82
0x00000687      e5d9           mov a, 0xd9
0x00000689      6010           jz 0x069b
0x0000068b      2438           add a, #0x38
0x0000068d      400c           jc 0x069b
0x0000068f      e5d9           mov a, 0xd9
0x00000691      24a0           add a, #0xa0
0x00000693      5006           jnc 0x069b
0x00000695      90069b         mov dptr, #0x069b
0x00000698      e5d9           mov a, 0xd9
0x0000069a      73             jmp @a+dptr
0x0000069b      75d8d4         mov 0xd8, #0xd4
0x0000069e      8046           sjmp 0x06e6
0x000006a0      7895           mov r0, #0x95
0x000006a2      7a00           mov r2, #0x00
0x000006a4      7b11           mov r3, #0x11
0x000006a6      c205           clr 0x20.5
0x000006a8      803c           sjmp 0x06e6
0x000006aa      bb0002         cjne r3, #0x00, 0x06af
0x000006ad      800f           sjmp 0x06be
0x000006af      e5da           mov a, 0xda
0x000006b1      f6             mov @r0, a
0x000006b2      08             inc r0
0x000006b3      0a             inc r2
0x000006b4      db08           djnz r3, 0x06be
0x000006b6      75d840         mov 0xd8, #0x40
0x000006b9      802b           sjmp 0x06e6
0x000006bb      120768         lcall 0x0768
0x000006be      75d844         mov 0xd8, #0x44
0x000006c1      8023           sjmp 0x06e6
0x000006c3      7893           mov r0, #0x93
0x000006c5      796e           mov r1, #0x6e
0x000006c7      906eca         mov dptr, #0x6eca
0x000006ca      e0             movx a, @dptr
0x000006cb      fa             mov r2, a
0x000006cc      20070e         jb 0x20.7, 0x06dd
0x000006cf      8882           mov 0x82, r0
0x000006d1      8983           mov 0x83, r1
0x000006d3      e0             movx a, @dptr
0x000006d4      f5da           mov 0xda, a
0x000006d6      a3             inc dptr
0x000006d7      a882           mov r0, 0x82
0x000006d9      a983           mov r1, 0x83
0x000006db      8006           sjmp 0x06e3
0x000006dd      d207           setb 0x20.7
0x000006df      908600         mov dptr, #0x8600
0x000006e2      e0             movx a, @dptr
0x000006e3      75d844         mov 0xd8, #0x44
0x000006e6      d082           pop 0x82
0x000006e8      d083           pop 0x83
0x000006ea      d0e0           pop 0xe0
0x000006ec      d0d0           pop 0xd0
0x000006ee      32             reti
0x000006ef      80ca           sjmp 0x06bb
0x000006f1      00             nop
0x000006f2      00             nop
0x000006f3      00             nop
0x000006f4      00             nop
0x000006f5      00             nop
0x000006f6      00             nop
0x000006f7      00             nop
0x000006f8      00             nop
0x000006f9      00             nop
0x000006fa      00             nop
0x000006fb      75d844         mov 0xd8, #0x44
0x000006fe      75d018         mov 0xd0, #0x18
0x00000701      809d           sjmp 0x06a0
0x00000703      75d844         mov 0xd8, #0x44
0x00000706      80de           sjmp 0x06e6
0x00000708      80b9           sjmp 0x06c3
0x0000070a      00             nop
0x0000070b      75d844         mov 0xd8, #0x44
0x0000070e      80d6           sjmp 0x06e6
0x00000710      80cb           sjmp 0x06dd
0x00000712      00             nop
0x00000713      75d844         mov 0xd8, #0x44
0x00000716      80ce           sjmp 0x06e6
0x00000718      80b2           sjmp 0x06cc
0x0000071a      00             nop
0x0000071b      75d018         mov 0xd0, #0x18
0x0000071e      808a           sjmp 0x06aa
0x00000720      00             nop
0x00000721      00             nop
0x00000722      00             nop
0x00000723      75d844         mov 0xd8, #0x44
0x00000726      d205           setb 0x20.5
0x00000728      80bc           sjmp 0x06e6
0x0000072a      00             nop
0x0000072b      75d844         mov 0xd8, #0x44
0x0000072e      80b6           sjmp 0x06e6
0x00000730      00             nop
0x00000731      00             nop
0x00000732      00             nop
0x00000733      75d844         mov 0xd8, #0x44
0x00000736      80ae           sjmp 0x06e6
0x00000738      00             nop
0x00000739      00             nop
0x0000073a      00             nop
0x0000073b      75d018         mov 0xd0, #0x18
0x0000073e      d205           setb 0x20.5
0x00000740      80ad           sjmp 0x06ef
0x00000742      00             nop
0x00000743      75d018         mov 0xd0, #0x18
0x00000746      80c0           sjmp 0x0708
0x00000748      00             nop
0x00000749      00             nop
0x0000074a      00             nop
0x0000074b      75d844         mov 0xd8, #0x44
0x0000074e      80d8           sjmp 0x0728
0x00000750      00             nop
0x00000751      00             nop
0x00000752      00             nop
0x00000753      75d018         mov 0xd0, #0x18
0x00000756      80c0           sjmp 0x0718
0x00000758      00             nop
0x00000759      00             nop
0x0000075a      00             nop
0x0000075b      75d018         mov 0xd0, #0x18
0x0000075e      80b0           sjmp 0x0710
0x00000760      00             nop
0x00000761      00             nop
0x00000762      00             nop
0x00000763      75d844         mov 0xd8, #0x44
0x00000766      80c0           sjmp 0x0728
0x00000768      7895           mov r0, #0x95
0x0000076a      e6             mov a, @r0
0x0000076b      b4830b         cjne a, #0x83, 0x0779
0x0000076e      906ec2         mov dptr, #0x6ec2
0x00000771      e6             mov a, @r0
0x00000772      f0             movx @dptr, a
0x00000773      a3             inc dptr
0x00000774      08             inc r0
0x00000775      e6             mov a, @r0
0x00000776      f0             movx @dptr, a
0x00000777      801f           sjmp 0x0798
0x00000779      b48502         cjne a, #0x85, 0x077e
0x0000077c      80f0           sjmp 0x076e
0x0000077e      b48106         cjne a, #0x81, 0x0787
0x00000781      906ec2         mov dptr, #0x6ec2
0x00000784      e0             movx a, @dptr
0x00000785      60e7           jz 0x076e
0x00000787      20080e         jb 0x21.0, 0x0798
0x0000078a      906ec9         mov dptr, #0x6ec9
0x0000078d      ea             mov a, r2
0x0000078e      f0             movx @dptr, a
0x0000078f      906ea9         mov dptr, #0x6ea9
0x00000792      e6             mov a, @r0
0x00000793      f0             movx @dptr, a
0x00000794      a3             inc dptr
0x00000795      08             inc r0
0x00000796      dafa           djnz r2, 0x0792
0x00000798      22             ret
0x00000799      758a00         mov 0x8a, #0x00
0x0000079c      758c40         mov 0x8c, #0x40
0x0000079f      75db2a         mov 0xdb, #0x2a
0x000007a2      d296           setb 0x90.6
0x000007a4      d297           setb 0x90.7
0x000007a6      75d844         mov 0xd8, #0x44
0x000007a9      758921         mov 0x89, #0x21
0x000007ac      d28c           setb 0x88.4
0x000007ae      d28a           setb 0x88.2
0x000007b0      d288           setb 0x88.0
0x000007b2      75a8a7         mov 0xa8, #0xa7
0x000007b5      75b811         mov 0xb8, #0x11
0x000007b8      d2bc           setb 0xb8.4
0x000007ba      22             ret
0x000007bb      753000         mov 0x30, #0x00
0x000007be      7410           mov a, #0x10
0x000007c0      908000         mov dptr, #0x8000
0x000007c3      f0             movx @dptr, a
0x000007c4      22             ret
0x000007c5      c030           push 0x30
0x000007c7      c0d0           push 0xd0
0x000007c9      c083           push 0x83
0x000007cb      c082           push 0x82
0x000007cd      d3             setb c
0x000007ce      10af01         jbc 0xa8.7, 0x07d2
0x000007d1      c3             clr c
0x000007d2      f530           mov 0x30, a
0x000007d4      04             inc a
0x000007d5      c4             swap a
0x000007d6      908000         mov dptr, #0x8000
0x000007d9      f0             movx @dptr, a
0x000007da      92af           mov 0xa8.7, c
0x000007dc      d082           pop 0x82
0x000007de      d083           pop 0x83
0x000007e0      d0d0           pop 0xd0
0x000007e2      e4             clr a
0x000007e3      73             jmp @a+dptr
0x000007e4      d0e0           pop 0xe0
0x000007e6      c0d0           push 0xd0
0x000007e8      d3             setb c
0x000007e9      10af01         jbc 0xa8.7, 0x07ed
0x000007ec      c3             clr c
0x000007ed      f530           mov 0x30, a
0x000007ef      04             inc a
0x000007f0      c4             swap a
0x000007f1      908000         mov dptr, #0x8000
0x000007f4      f0             movx @dptr, a
0x000007f5      92af           mov 0xa8.7, c
0x000007f7      d0d0           pop 0xd0
0x000007f9      22             ret

BANK 0 CPU 2487 FILE 002487
0x00002487      d083           pop 0x83
0x00002489      d082           pop 0x82
0x0000248b      e4             clr a
0x0000248c      93             movc a, @a+dptr
0x0000248d      7009           jnz 0x2498
0x0000248f      7401           mov a, #0x01
0x00002491      93             movc a, @a+dptr
0x00002492      7004           jnz 0x2498
0x00002494      a3             inc dptr
0x00002495      a3             inc dptr
0x00002496      800b           sjmp 0x24a3
0x00002498      7402           mov a, #0x02
0x0000249a      93             movc a, @a+dptr
0x0000249b      6f             xrl a, r7
0x0000249c      6005           jz 0x24a3
0x0000249e      a3             inc dptr
0x0000249f      a3             inc dptr
0x000024a0      a3             inc dptr
0x000024a1      80e8           sjmp 0x248b
0x000024a3      7401           mov a, #0x01
0x000024a5      93             movc a, @a+dptr
0x000024a6      c0e0           push 0xe0
0x000024a8      e4             clr a
0x000024a9      93             movc a, @a+dptr
0x000024aa      c0e0           push 0xe0
0x000024ac      22             ret

BANK 0 CPU 26e9 FILE 0026e9
0x000026e9      e4             clr a
0x000026ea      93             movc a, @a+dptr
0x000026eb      fd             mov r5, a
0x000026ec      7401           mov a, #0x01
0x000026ee      93             movc a, @a+dptr
0x000026ef      fe             mov r6, a
0x000026f0      7402           mov a, #0x02
0x000026f2      93             movc a, @a+dptr
0x000026f3      ff             mov r7, a
0x000026f4      4e             orl a, r6
0x000026f5      22             ret

BANK 3 CPU ad43 FILE 022d43
0x0000ad43      90685b         mov dptr, #0x685b
0x0000ad46      ef             mov a, r7
0x0000ad47      f0             movx @dptr, a
0x0000ad48      9077c0         mov dptr, #0x77c0
0x0000ad4b      e0             movx a, @dptr
0x0000ad4c      24c1           add a, #0xc1
0x0000ad4e      f582           mov 0x82, a
0x0000ad50      e4             clr a
0x0000ad51      3477           addc a, #0x77
0x0000ad53      f583           mov 0x83, a
0x0000ad55      e0             movx a, @dptr
0x0000ad56      ff             mov r7, a
0x0000ad57      90685b         mov dptr, #0x685b
0x0000ad5a      e0             movx a, @dptr
0x0000ad5b      6f             xrl a, r7
0x0000ad5c      7008           jnz 0xad66
0x0000ad5e      9077c0         mov dptr, #0x77c0
0x0000ad61      e0             movx a, @dptr
0x0000ad62      14             dec a
0x0000ad63      f0             movx @dptr, a
0x0000ad64      8006           sjmp 0xad6c
0x0000ad66      9077c0         mov dptr, #0x77c0
0x0000ad69      7403           mov a, #0x03
0x0000ad6b      f0             movx @dptr, a
0x0000ad6c      9077c0         mov dptr, #0x77c0
0x0000ad6f      e0             movx a, @dptr
0x0000ad70      6402           xrl a, #0x02
0x0000ad72      7006           jnz 0xad7a
0x0000ad74      9068de         mov dptr, #0x68de
0x0000ad77      7432           mov a, #0x32
0x0000ad79      f0             movx @dptr, a
0x0000ad7a      9077c0         mov dptr, #0x77c0
0x0000ad7d      e0             movx a, @dptr
0x0000ad7e      700c           jnz 0xad8c
0x0000ad80      9068de         mov dptr, #0x68de
0x0000ad83      e0             movx a, @dptr
0x0000ad84      7006           jnz 0xad8c
0x0000ad86      9077c0         mov dptr, #0x77c0
0x0000ad89      7403           mov a, #0x03
0x0000ad8b      f0             movx @dptr, a
0x0000ad8c      9077c0         mov dptr, #0x77c0
0x0000ad8f      e0             movx a, @dptr
0x0000ad90      ff             mov r7, a
0x0000ad91      0207e4         ljmp 0x07e4

BANK 3 CPU b3e5 FILE 0233e5
0x0000b3e5      9068a7         mov dptr, #0x68a7
0x0000b3e8      e0             movx a, @dptr
0x0000b3e9      ff             mov r7, a
0x0000b3ea      7403           mov a, #0x03
0x0000b3ec      90ad43         mov dptr, #0xad43
0x0000b3ef      1207c5         lcall 0x07c5
0x0000b3f2      ef             mov a, r7
0x0000b3f3      702b           jnz 0xb420
0x0000b3f5      9077ef         mov dptr, #0x77ef
0x0000b3f8      7405           mov a, #0x05
0x0000b3fa      f0             movx @dptr, a
0x0000b3fb      7402           mov a, #0x02
0x0000b3fd      90abf1         mov dptr, #0xabf1
0x0000b400      1207c5         lcall 0x07c5
0x0000b403      7402           mov a, #0x02
0x0000b405      909739         mov dptr, #0x9739
0x0000b408      1207c5         lcall 0x07c5
0x0000b40b      9068a9         mov dptr, #0x68a9
0x0000b40e      e0             movx a, @dptr
0x0000b40f      906886         mov dptr, #0x6886
0x0000b412      f0             movx @dptr, a
0x0000b413      7fff           mov r7, #0xff
0x0000b415      7403           mov a, #0x03
0x0000b417      90a847         mov dptr, #0xa847
0x0000b41a      1207c5         lcall 0x07c5
0x0000b41d      0207e4         ljmp 0x07e4

BANK 3 CPU abd3 FILE 022bd3
0x0000abd3      9077be         mov dptr, #0x77be
0x0000abd6      e0             movx a, @dptr
0x0000abd7      ff             mov r7, a
0x0000abd8      7037           jnz 0xac11
0x0000abda      9077be         mov dptr, #0x77be
0x0000abdd      7401           mov a, #0x01
0x0000abdf      f0             movx @dptr, a
0x0000abe0      7403           mov a, #0x03
0x0000abe2      90ac16         mov dptr, #0xac16
0x0000abe5      1207c5         lcall 0x07c5
0x0000abe8      9077bf         mov dptr, #0x77bf
0x0000abeb      e0             movx a, @dptr
0x0000abec      90686a         mov dptr, #0x686a
0x0000abef      f0             movx @dptr, a
0x0000abf0      a3             inc dptr
0x0000abf1      e4             clr a
0x0000abf2      f0             movx @dptr, a
0x0000abf3      9077be         mov dptr, #0x77be
0x0000abf6      e0             movx a, @dptr
0x0000abf7      c3             clr c
0x0000abf8      33             rlc a
0x0000abf9      247d           add a, #0x7d
0x0000abfb      ff             mov r7, a
0x0000abfc      e4             clr a
0x0000abfd      3468           addc a, #0x68
0x0000abff      fe             mov r6, a
0x0000ac00      7d01           mov r5, #0x01
0x0000ac02      7403           mov a, #0x03
0x0000ac04      90a7d0         mov dptr, #0xa7d0
0x0000ac07      1207c5         lcall 0x07c5
0x0000ac0a      9077bf         mov dptr, #0x77bf
0x0000ac0d      ef             mov a, r7
0x0000ac0e      f0             movx @dptr, a
0x0000ac0f      8000           sjmp 0xac11
0x0000ac11      8000           sjmp 0xac13
0x0000ac13      0207e4         ljmp 0x07e4

BANK 3 CPU a9b5 FILE 0229b5
0x0000a9b5      ef             mov a, r7
0x0000a9b6      6401           xrl a, #0x01
0x0000a9b8      705b           jnz 0xaa15
0x0000a9ba      9077bf         mov dptr, #0x77bf
0x0000a9bd      e0             movx a, @dptr
0x0000a9be      ff             mov r7, a
0x0000a9bf      6404           xrl a, #0x04
0x0000a9c1      7032           jnz 0xa9f5
0x0000a9c3      9077be         mov dptr, #0x77be
0x0000a9c6      7402           mov a, #0x02
0x0000a9c8      f0             movx @dptr, a
0x0000a9c9      c3             clr c
0x0000a9ca      33             rlc a
0x0000a9cb      247d           add a, #0x7d
0x0000a9cd      f582           mov 0x82, a
0x0000a9cf      e4             clr a
0x0000a9d0      3468           addc a, #0x68
0x0000a9d2      f583           mov 0x83, a
0x0000a9d4      e0             movx a, @dptr
0x0000a9d5      9077bf         mov dptr, #0x77bf
0x0000a9d8      f0             movx @dptr, a
0x0000a9d9      906885         mov dptr, #0x6885
0x0000a9dc      e0             movx a, @dptr
0x0000a9dd      ff             mov r7, a
0x0000a9de      7403           mov a, #0x03
0x0000a9e0      90ad30         mov dptr, #0xad30
0x0000a9e3      1207c5         lcall 0x07c5
0x0000a9e6      9077bf         mov dptr, #0x77bf
0x0000a9e9      e0             movx a, @dptr
0x0000a9ea      ff             mov r7, a
0x0000a9eb      7402           mov a, #0x02
0x0000a9ed      90aab5         mov dptr, #0xaab5
0x0000a9f0      1207c5         lcall 0x07c5
0x0000a9f3      8020           sjmp 0xaa15
0x0000a9f5      ef             mov a, r7
0x0000a9f6      6405           xrl a, #0x05
0x0000a9f8      701b           jnz 0xaa15
0x0000a9fa      9077be         mov dptr, #0x77be
0x0000a9fd      7403           mov a, #0x03
0x0000a9ff      f0             movx @dptr, a
0x0000aa00      906885         mov dptr, #0x6885
0x0000aa03      e0             movx a, @dptr
0x0000aa04      ff             mov r7, a
0x0000aa05      7403           mov a, #0x03
0x0000aa07      90ad1d         mov dptr, #0xad1d
0x0000aa0a      1207c5         lcall 0x07c5
0x0000aa0d      9076f1         mov dptr, #0x76f1
0x0000aa10      7401           mov a, #0x01
0x0000aa12      f0             movx @dptr, a
0x0000aa13      8000           sjmp 0xaa15
0x0000aa15      02ac13         ljmp 0xac13

BANK 1 CPU 9f99 FILE 011f99
0x00009f99      906863         mov dptr, #0x6863
0x00009f9c      7418           mov a, #0x18
0x00009f9e      f0             movx @dptr, a
0x00009f9f      a3             inc dptr
0x00009fa0      7406           mov a, #0x06
0x00009fa2      f0             movx @dptr, a
0x00009fa3      907769         mov dptr, #0x7769
0x00009fa6      1226e9         lcall 0x26e9
0x00009fa9      7402           mov a, #0x02
0x00009fab      90a215         mov dptr, #0xa215
0x00009fae      1207c5         lcall 0x07c5
0x00009fb1      906862         mov dptr, #0x6862
0x00009fb4      7418           mov a, #0x18
0x00009fb6      f0             movx @dptr, a
0x00009fb7      a3             inc dptr
0x00009fb8      740c           mov a, #0x0c
0x00009fba      f0             movx @dptr, a
0x00009fbb      906ecd         mov dptr, #0x6ecd
0x00009fbe      e0             movx a, @dptr
0x00009fbf      ff             mov r7, a
0x00009fc0      7402           mov a, #0x02
0x00009fc2      90a4f2         mov dptr, #0xa4f2
0x00009fc5      1207c5         lcall 0x07c5

BANK 1 CPU a953 FILE 012953
0x0000a953      7f00           mov r7, #0x00
0x0000a955      7402           mov a, #0x02
0x0000a957      90a44b         mov dptr, #0xa44b
0x0000a95a      1207c5         lcall 0x07c5
0x0000a95d      906867         mov dptr, #0x6867
0x0000a960      7401           mov a, #0x01
0x0000a962      f0             movx @dptr, a
0x0000a963      a3             inc dptr
0x0000a964      7409           mov a, #0x09
0x0000a966      f0             movx @dptr, a
0x0000a967      a3             inc dptr
0x0000a968      7420           mov a, #0x20
0x0000a96a      f0             movx @dptr, a
0x0000a96b      a3             inc dptr
0x0000a96c      e4             clr a
0x0000a96d      f0             movx @dptr, a
0x0000a96e      a3             inc dptr
0x0000a96f      7402           mov a, #0x02
0x0000a971      f0             movx @dptr, a
0x0000a972      a3             inc dptr
0x0000a973      740d           mov a, #0x0d
0x0000a975      f0             movx @dptr, a
0x0000a976      7f01           mov r7, #0x01
0x0000a978      7402           mov a, #0x02
0x0000a97a      90a9e3         mov dptr, #0xa9e3
0x0000a97d      1207c5         lcall 0x07c5
0x0000a980      90686b         mov dptr, #0x686b
0x0000a983      7401           mov a, #0x01
0x0000a985      f0             movx @dptr, a
0x0000a986      a3             inc dptr
0x0000a987      7409           mov a, #0x09
0x0000a989      f0             movx @dptr, a
0x0000a98a      a3             inc dptr
0x0000a98b      7420           mov a, #0x20
0x0000a98d      f0             movx @dptr, a
0x0000a98e      7d01           mov r5, #0x01
0x0000a990      7e77           mov r6, #0x77
0x0000a992      7fa3           mov r7, #0xa3
0x0000a994      7402           mov a, #0x02
0x0000a996      90a2e7         mov dptr, #0xa2e7
0x0000a999      1207c5         lcall 0x07c5

BANK 1 CPU aed0 FILE 012ed0
0x0000aed0      906865         mov dptr, #0x6865
0x0000aed3      ef             mov a, r7
0x0000aed4      f0             movx @dptr, a
0x0000aed5      122487         lcall 0x2487
0x0000aed8      aef4           mov r6, 0xf4
0x0000aeda      00             nop
0x0000aedb      af1e           mov r7, 0x1e
0x0000aedd      01af           ajmp 0xa8af
0x0000aedf      48             orl a, r0
0x0000aee0      02af71         ljmp 0xaf71
0x0000aee3      03             rr a
0x0000aee4      af8f           mov r7, 0x8f
0x0000aee6      04             inc a
0x0000aee7      afad           mov r7, 0xad
0x0000aee9      05af           inc 0xaf
0x0000aeeb      ce             xch a, r6
0x0000aeec      06             inc @r0
0x0000aeed      afd0           mov r7, 0xd0
0x0000aeef      07             inc @r1
0x0000aef0      00             nop
0x0000aef1      00             nop
0x0000aef2      afd2           mov r7, 0xd2
0x0000aef4      906865         mov dptr, #0x6865
0x0000aef7      e0             movx a, @dptr
0x0000aef8      c3             clr c
0x0000aef9      33             rlc a
0x0000aefa      2418           add a, #0x18
0x0000aefc      f582           mov 0x82, a
0x0000aefe      e4             clr a
0x0000aeff      346b           addc a, #0x6b
0x0000af01      f583           mov 0x83, a
0x0000af03      e0             movx a, @dptr
0x0000af04      fe             mov r6, a
0x0000af05      a3             inc dptr
0x0000af06      e0             movx a, @dptr
0x0000af07      90690b         mov dptr, #0x690b
0x0000af0a      f0             movx @dptr, a
0x0000af0b      7400           mov a, #0x00
0x0000af0d      90b845         mov dptr, #0xb845
0x0000af10      1207c5         lcall 0x07c5
0x0000af13      7402           mov a, #0x02
0x0000af15      909142         mov dptr, #0x9142
0x0000af18      1207c5         lcall 0x07c5
0x0000af1b      02afd2         ljmp 0xafd2
0x0000af1e      906865         mov dptr, #0x6865
0x0000af21      e0             movx a, @dptr
0x0000af22      c3             clr c
0x0000af23      33             rlc a
0x0000af24      2418           add a, #0x18
0x0000af26      f582           mov 0x82, a
0x0000af28      e4             clr a
0x0000af29      346b           addc a, #0x6b
0x0000af2b      f583           mov 0x83, a
0x0000af2d      e0             movx a, @dptr
0x0000af2e      fe             mov r6, a
0x0000af2f      a3             inc dptr
0x0000af30      e0             movx a, @dptr
0x0000af31      90690c         mov dptr, #0x690c
0x0000af34      f0             movx @dptr, a
0x0000af35      7400           mov a, #0x00
0x0000af37      90b845         mov dptr, #0xb845
0x0000af3a      1207c5         lcall 0x07c5
0x0000af3d      7402           mov a, #0x02
0x0000af3f      909142         mov dptr, #0x9142
0x0000af42      1207c5         lcall 0x07c5
0x0000af45      02afd2         ljmp 0xafd2
0x0000af48      906865         mov dptr, #0x6865
0x0000af4b      e0             movx a, @dptr
0x0000af4c      c3             clr c
0x0000af4d      33             rlc a
0x0000af4e      2418           add a, #0x18
0x0000af50      f582           mov 0x82, a
0x0000af52      e4             clr a
0x0000af53      346b           addc a, #0x6b
0x0000af55      f583           mov 0x83, a
0x0000af57      e0             movx a, @dptr
0x0000af58      fe             mov r6, a
0x0000af59      a3             inc dptr
0x0000af5a      e0             movx a, @dptr
0x0000af5b      90690d         mov dptr, #0x690d
0x0000af5e      f0             movx @dptr, a
0x0000af5f      7400           mov a, #0x00
0x0000af61      90b845         mov dptr, #0xb845
0x0000af64      1207c5         lcall 0x07c5
0x0000af67      7402           mov a, #0x02
0x0000af69      909142         mov dptr, #0x9142
0x0000af6c      1207c5         lcall 0x07c5
0x0000af6f      8061           sjmp 0xafd2
0x0000af71      906865         mov dptr, #0x6865
0x0000af74      e0             movx a, @dptr
0x0000af75      c3             clr c
0x0000af76      33             rlc a
0x0000af77      2418           add a, #0x18
0x0000af79      f582           mov 0x82, a
0x0000af7b      e4             clr a
0x0000af7c      346b           addc a, #0x6b
0x0000af7e      f583           mov 0x83, a
0x0000af80      e0             movx a, @dptr
0x0000af81      fe             mov r6, a
0x0000af82      a3             inc dptr
0x0000af83      e0             movx a, @dptr
0x0000af84      ff             mov r7, a
0x0000af85      7402           mov a, #0x02
0x0000af87      90916a         mov dptr, #0x916a
0x0000af8a      1207c5         lcall 0x07c5
0x0000af8d      8043           sjmp 0xafd2
0x0000af8f      906865         mov dptr, #0x6865
0x0000af92      e0             movx a, @dptr
0x0000af93      c3             clr c
0x0000af94      33             rlc a
0x0000af95      2418           add a, #0x18
0x0000af97      f582           mov 0x82, a
0x0000af99      e4             clr a
0x0000af9a      346b           addc a, #0x6b
0x0000af9c      f583           mov 0x83, a
0x0000af9e      e0             movx a, @dptr
0x0000af9f      fe             mov r6, a
0x0000afa0      a3             inc dptr
0x0000afa1      e0             movx a, @dptr
0x0000afa2      ff             mov r7, a
0x0000afa3      7402           mov a, #0x02
0x0000afa5      90916a         mov dptr, #0x916a
0x0000afa8      1207c5         lcall 0x07c5
0x0000afab      8025           sjmp 0xafd2
0x0000afad      906865         mov dptr, #0x6865
0x0000afb0      e0             movx a, @dptr
0x0000afb1      c3             clr c
0x0000afb2      33             rlc a
0x0000afb3      2418           add a, #0x18
0x0000afb5      f582           mov 0x82, a
0x0000afb7      e4             clr a
0x0000afb8      346b           addc a, #0x6b
0x0000afba      f583           mov 0x83, a
0x0000afbc      e0             movx a, @dptr
0x0000afbd      fe             mov r6, a
0x0000afbe      a3             inc dptr
0x0000afbf      e0             movx a, @dptr
0x0000afc0      906ecb         mov dptr, #0x6ecb
0x0000afc3      f0             movx @dptr, a
0x0000afc4      7402           mov a, #0x02
0x0000afc6      909739         mov dptr, #0x9739
0x0000afc9      1207c5         lcall 0x07c5
0x0000afcc      8004           sjmp 0xafd2
0x0000afce      8002           sjmp 0xafd2
0x0000afd0      8000           sjmp 0xafd2
0x0000afd2      0207e4         ljmp 0x07e4
0x0000afd5      906876         mov dptr, #0x6876
0x0000afd8      e4             clr a
0x0000afd9      f0             movx @dptr, a
0x0000afda      906876         mov dptr, #0x6876
0x0000afdd      e0             movx a, @dptr
0x0000afde      c3             clr c
0x0000afdf      9408           subb a, #0x08
0x0000afe1      4003           jc 0xafe6
0x0000afe3      02b07e         ljmp 0xb07e
0x0000afe6      906876         mov dptr, #0x6876
0x0000afe9      e0             movx a, @dptr
0x0000afea      75f008         mov 0xf0, #0x08
0x0000afed      a4             mul ab
0x0000afee      248e           add a, #0x8e
0x0000aff0      f582           mov 0x82, a
0x0000aff2      e4             clr a
0x0000aff3      3477           addc a, #0x77
0x0000aff5      f583           mov 0x83, a
0x0000aff7      e4             clr a
0x0000aff8      93             movc a, @a+dptr
0x0000aff9      ff             mov r7, a
0x0000affa      6408           xrl a, #0x08
0x0000affc      7047           jnz 0xb045
0x0000affe      906877         mov dptr, #0x6877
0x0000b001      e4             clr a
0x0000b002      f0             movx @dptr, a
0x0000b003      906877         mov dptr, #0x6877
0x0000b006      e0             movx a, @dptr
0x0000b007      c3             clr c
0x0000b008      9404           subb a, #0x04
0x0000b00a      5037           jnc 0xb043
0x0000b00c      906877         mov dptr, #0x6877
0x0000b00f      e0             movx a, @dptr
0x0000b010      24be           add a, #0xbe
0x0000b012      f582           mov 0x82, a
0x0000b014      e4             clr a
0x0000b015      3474           addc a, #0x74
0x0000b017      f583           mov 0x83, a
0x0000b019      e0             movx a, @dptr
0x0000b01a      906869         mov dptr, #0x6869
0x0000b01d      f0             movx @dptr, a
0x0000b01e      906876         mov dptr, #0x6876
0x0000b021      e0             movx a, @dptr
0x0000b022      75f008         mov 0xf0, #0x08
0x0000b025      a4             mul ab
0x0000b026      248f           add a, #0x8f
0x0000b028      f582           mov 0x82, a
0x0000b02a      e4             clr a
0x0000b02b      3477           addc a, #0x77
0x0000b02d      f583           mov 0x83, a
0x0000b02f      e4             clr a
0x0000b030      93             movc a, @a+dptr
0x0000b031      ff             mov r7, a
0x0000b032      906877         mov dptr, #0x6877
0x0000b035      e0             movx a, @dptr
0x0000b036      2f             add a, r7
0x0000b037      ff             mov r7, a
0x0000b038      120178         lcall 0x0178
0x0000b03b      906877         mov dptr, #0x6877
0x0000b03e      e0             movx a, @dptr
0x0000b03f      04             inc a
0x0000b040      f0             movx @dptr, a
0x0000b041      80c0           sjmp 0xb003
0x0000b043      8030           sjmp 0xb075
0x0000b045      906876         mov dptr, #0x6876
0x0000b048      e0             movx a, @dptr
0x0000b049      c3             clr c
0x0000b04a      33             rlc a
0x0000b04b      2418           add a, #0x18
0x0000b04d      f582           mov 0x82, a
0x0000b04f      e4             clr a
0x0000b050      346b           addc a, #0x6b
0x0000b052      f583           mov 0x83, a
0x0000b054      e0             movx a, @dptr
0x0000b055      fe             mov r6, a
0x0000b056      a3             inc dptr
0x0000b057      e0             movx a, @dptr
0x0000b058      906869         mov dptr, #0x6869
0x0000b05b      f0             movx @dptr, a
0x0000b05c      906876         mov dptr, #0x6876
0x0000b05f      e0             movx a, @dptr
0x0000b060      75f008         mov 0xf0, #0x08
0x0000b063      a4             mul ab
0x0000b064      248f           add a, #0x8f
0x0000b066      f582           mov 0x82, a
0x0000b068      e4             clr a
0x0000b069      3477           addc a, #0x77
0x0000b06b      f583           mov 0x83, a
0x0000b06d      e4             clr a
0x0000b06e      93             movc a, @a+dptr
0x0000b06f      ff             mov r7, a
0x0000b070      120178         lcall 0x0178
0x0000b073      8000           sjmp 0xb075
0x0000b075      906876         mov dptr, #0x6876
0x0000b078      e0             movx a, @dptr
0x0000b079      04             inc a
0x0000b07a      f0             movx @dptr, a
0x0000b07b      02afda         ljmp 0xafda
0x0000b07e      7401           mov a, #0x01
0x0000b080      90a953         mov dptr, #0xa953
0x0000b083      1207c5         lcall 0x07c5

BANK 1 CPU acca FILE 012cca
0x0000acca      906875         mov dptr, #0x6875
0x0000accd      ef             mov a, r7
0x0000acce      f0             movx @dptr, a
0x0000accf      a3             inc dptr
0x0000acd0      e0             movx a, @dptr
0x0000acd1      75f008         mov 0xf0, #0x08
0x0000acd4      a4             mul ab
0x0000acd5      248e           add a, #0x8e
0x0000acd7      f582           mov 0x82, a
0x0000acd9      e4             clr a
0x0000acda      3477           addc a, #0x77
0x0000acdc      f583           mov 0x83, a
0x0000acde      e4             clr a
0x0000acdf      93             movc a, @a+dptr
0x0000ace0      ff             mov r7, a
0x0000ace1      6402           xrl a, #0x02
0x0000ace3      705d           jnz 0xad42
0x0000ace5      906875         mov dptr, #0x6875
0x0000ace8      e0             movx a, @dptr
0x0000ace9      c3             clr c
0x0000acea      9408           subb a, #0x08
0x0000acec      5037           jnc 0xad25
0x0000acee      906873         mov dptr, #0x6873
0x0000acf1      7401           mov a, #0x01
0x0000acf3      f0             movx @dptr, a
0x0000acf4      906875         mov dptr, #0x6875
0x0000acf7      e0             movx a, @dptr
0x0000acf8      600e           jz 0xad08
0x0000acfa      906873         mov dptr, #0x6873
0x0000acfd      e0             movx a, @dptr
0x0000acfe      c3             clr c
0x0000acff      33             rlc a
0x0000ad00      f0             movx @dptr, a
0x0000ad01      a3             inc dptr
0x0000ad02      a3             inc dptr
0x0000ad03      e0             movx a, @dptr
0x0000ad04      14             dec a
0x0000ad05      f0             movx @dptr, a
0x0000ad06      80ec           sjmp 0xacf4
0x0000ad08      906873         mov dptr, #0x6873
0x0000ad0b      e0             movx a, @dptr
0x0000ad0c      ff             mov r7, a
0x0000ad0d      7e00           mov r6, #0x00
0x0000ad0f      906876         mov dptr, #0x6876
0x0000ad12      e0             movx a, @dptr
0x0000ad13      c3             clr c
0x0000ad14      33             rlc a
0x0000ad15      2418           add a, #0x18
0x0000ad17      f582           mov 0x82, a
0x0000ad19      e4             clr a
0x0000ad1a      346b           addc a, #0x6b
0x0000ad1c      f583           mov 0x83, a
0x0000ad1e      e0             movx a, @dptr
0x0000ad1f      6e             xrl a, r6
0x0000ad20      f0             movx @dptr, a
0x0000ad21      a3             inc dptr
0x0000ad22      e0             movx a, @dptr
0x0000ad23      6f             xrl a, r7
0x0000ad24      f0             movx @dptr, a
0x0000ad25      906876         mov dptr, #0x6876
0x0000ad28      e0             movx a, @dptr
0x0000ad29      ff             mov r7, a
0x0000ad2a      7401           mov a, #0x01
0x0000ad2c      90aac7         mov dptr, #0xaac7
0x0000ad2f      1207c5         lcall 0x07c5
0x0000ad32      906876         mov dptr, #0x6876
0x0000ad35      e0             movx a, @dptr
0x0000ad36      ff             mov r7, a
0x0000ad37      7401           mov a, #0x01
0x0000ad39      90aed0         mov dptr, #0xaed0
0x0000ad3c      1207c5         lcall 0x07c5
0x0000ad3f      02addd         ljmp 0xaddd
0x0000ad42      ef             mov a, r7
0x0000ad43      6408           xrl a, #0x08
0x0000ad45      6003           jz 0xad4a
0x0000ad47      02addd         ljmp 0xaddd
0x0000ad4a      906874         mov dptr, #0x6874
0x0000ad4d      e4             clr a
0x0000ad4e      f0             movx @dptr, a
0x0000ad4f      906874         mov dptr, #0x6874
0x0000ad52      e0             movx a, @dptr
0x0000ad53      24be           add a, #0xbe
0x0000ad55      f582           mov 0x82, a
0x0000ad57      e4             clr a
0x0000ad58      3474           addc a, #0x74
0x0000ad5a      f583           mov 0x83, a
0x0000ad5c      e0             movx a, @dptr
0x0000ad5d      642d           xrl a, #0x2d
0x0000ad5f      6002           jz 0xad63
0x0000ad61      7401           mov a, #0x01
0x0000ad63      ff             mov r7, a
0x0000ad64      906874         mov dptr, #0x6874
0x0000ad67      e0             movx a, @dptr
0x0000ad68      c3             clr c
0x0000ad69      9404           subb a, #0x04
0x0000ad6b      e4             clr a
0x0000ad6c      33             rlc a
0x0000ad6d      5f             anl a, r7
0x0000ad6e      6008           jz 0xad78
0x0000ad70      906874         mov dptr, #0x6874
0x0000ad73      e0             movx a, @dptr
0x0000ad74      04             inc a
0x0000ad75      f0             movx @dptr, a
0x0000ad76      80d7           sjmp 0xad4f
0x0000ad78      906874         mov dptr, #0x6874
0x0000ad7b      e0             movx a, @dptr
0x0000ad7c      6404           xrl a, #0x04
0x0000ad7e      702b           jnz 0xadab
0x0000ad80      906874         mov dptr, #0x6874
0x0000ad83      e4             clr a
0x0000ad84      f0             movx @dptr, a
0x0000ad85      906874         mov dptr, #0x6874
0x0000ad88      e0             movx a, @dptr
0x0000ad89      c3             clr c
0x0000ad8a      9404           subb a, #0x04
0x0000ad8c      5018           jnc 0xada6
0x0000ad8e      906874         mov dptr, #0x6874
0x0000ad91      e0             movx a, @dptr
0x0000ad92      24be           add a, #0xbe
0x0000ad94      f582           mov 0x82, a
0x0000ad96      e4             clr a
0x0000ad97      3474           addc a, #0x74
0x0000ad99      f583           mov 0x83, a
0x0000ad9b      742d           mov a, #0x2d
0x0000ad9d      f0             movx @dptr, a
0x0000ad9e      906874         mov dptr, #0x6874
0x0000ada1      e0             movx a, @dptr
0x0000ada2      04             inc a
0x0000ada3      f0             movx @dptr, a
0x0000ada4      80df           sjmp 0xad85
0x0000ada6      906874         mov dptr, #0x6874
0x0000ada9      e4             clr a
0x0000adaa      f0             movx @dptr, a
0x0000adab      906875         mov dptr, #0x6875
0x0000adae      e0             movx a, @dptr
0x0000adaf      2430           add a, #0x30
0x0000adb1      ff             mov r7, a
0x0000adb2      906874         mov dptr, #0x6874
0x0000adb5      e0             movx a, @dptr
0x0000adb6      24be           add a, #0xbe
0x0000adb8      f582           mov 0x82, a
0x0000adba      e4             clr a
0x0000adbb      3474           addc a, #0x74
0x0000adbd      f583           mov 0x83, a
0x0000adbf      ef             mov a, r7
0x0000adc0      f0             movx @dptr, a
0x0000adc1      906876         mov dptr, #0x6876
0x0000adc4      e0             movx a, @dptr
0x0000adc5      ff             mov r7, a
0x0000adc6      7401           mov a, #0x01
0x0000adc8      90aac7         mov dptr, #0xaac7
0x0000adcb      1207c5         lcall 0x07c5
0x0000adce      906876         mov dptr, #0x6876
0x0000add1      e0             movx a, @dptr
0x0000add2      ff             mov r7, a
0x0000add3      7401           mov a, #0x01
0x0000add5      90aed0         mov dptr, #0xaed0
0x0000add8      1207c5         lcall 0x07c5
0x0000addb      8000           sjmp 0xaddd
0x0000addd      02             invalid

BANK 1 CPU ade0 FILE 012de0
0x0000ade0      ef             mov a, r7
0x0000ade1      33             rlc a
0x0000ade2      95e0           subb a, 0xe0
0x0000ade4      fe             mov r6, a
0x0000ade5      906874         mov dptr, #0x6874
0x0000ade8      e0             movx a, @dptr
0x0000ade9      c3             clr c
0x0000adea      33             rlc a
0x0000adeb      2418           add a, #0x18
0x0000aded      fb             mov r3, a
0x0000adee      e4             clr a
0x0000adef      346b           addc a, #0x6b
0x0000adf1      fa             mov r2, a
0x0000adf2      7901           mov r1, #0x01
0x0000adf4      8f82           mov 0x82, r7
0x0000adf6      8e83           mov 0x83, r6
0x0000adf8      12276a         lcall 0x276a
0x0000adfb      906874         mov dptr, #0x6874
0x0000adfe      e0             movx a, @dptr
0x0000adff      c3             clr c
0x0000ae00      33             rlc a
0x0000ae01      2418           add a, #0x18
0x0000ae03      f582           mov 0x82, a
0x0000ae05      e4             clr a
0x0000ae06      346b           addc a, #0x6b
0x0000ae08      f583           mov 0x83, a
0x0000ae0a      e0             movx a, @dptr
0x0000ae0b      fe             mov r6, a
0x0000ae0c      a3             inc dptr
0x0000ae0d      e0             movx a, @dptr
0x0000ae0e      ff             mov r7, a
0x0000ae0f      906874         mov dptr, #0x6874
0x0000ae12      e0             movx a, @dptr
0x0000ae13      75f008         mov 0xf0, #0x08
0x0000ae16      a4             mul ab
0x0000ae17      2490           add a, #0x90
0x0000ae19      f582           mov 0x82, a
0x0000ae1b      e4             clr a
0x0000ae1c      3477           addc a, #0x77
0x0000ae1e      f583           mov 0x83, a
0x0000ae20      e4             clr a
0x0000ae21      93             movc a, @a+dptr
0x0000ae22      fb             mov r3, a
0x0000ae23      7a00           mov r2, #0x00
0x0000ae25      c3             clr c
0x0000ae26      ef             mov a, r7
0x0000ae27      9b             subb a, r3
0x0000ae28      ee             mov a, r6
0x0000ae29      9a             subb a, r2
0x0000ae2a      502c           jnc 0xae58
0x0000ae2c      906874         mov dptr, #0x6874
0x0000ae2f      e0             movx a, @dptr
0x0000ae30      75f008         mov 0xf0, #0x08
0x0000ae33      a4             mul ab
0x0000ae34      2491           add a, #0x91
0x0000ae36      f582           mov 0x82, a
0x0000ae38      e4             clr a
0x0000ae39      3477           addc a, #0x77
0x0000ae3b      f583           mov 0x83, a
0x0000ae3d      e4             clr a
0x0000ae3e      93             movc a, @a+dptr
0x0000ae3f      ff             mov r7, a
0x0000ae40      7e00           mov r6, #0x00
0x0000ae42      906874         mov dptr, #0x6874
0x0000ae45      e0             movx a, @dptr
0x0000ae46      c3             clr c
0x0000ae47      33             rlc a
0x0000ae48      2418           add a, #0x18
0x0000ae4a      f582           mov 0x82, a
0x0000ae4c      e4             clr a
0x0000ae4d      346b           addc a, #0x6b
0x0000ae4f      f583           mov 0x83, a
0x0000ae51      ee             mov a, r6
0x0000ae52      f0             movx @dptr, a
0x0000ae53      a3             inc dptr
0x0000ae54      ef             mov a, r7
0x0000ae55      f0             movx @dptr, a
0x0000ae56      805b           sjmp 0xaeb3
0x0000ae58      906874         mov dptr, #0x6874
0x0000ae5b      e0             movx a, @dptr
0x0000ae5c      c3             clr c
0x0000ae5d      33             rlc a
0x0000ae5e      2418           add a, #0x18
0x0000ae60      f582           mov 0x82, a
0x0000ae62      e4             clr a
0x0000ae63      346b           addc a, #0x6b
0x0000ae65      f583           mov 0x83, a
0x0000ae67      e0             movx a, @dptr
0x0000ae68      fe             mov r6, a
0x0000ae69      a3             inc dptr
0x0000ae6a      e0             movx a, @dptr
0x0000ae6b      ff             mov r7, a
0x0000ae6c      906874         mov dptr, #0x6874
0x0000ae6f      e0             movx a, @dptr
0x0000ae70      75f008         mov 0xf0, #0x08
0x0000ae73      a4             mul ab
0x0000ae74      2491           add a, #0x91
0x0000ae76      f582           mov 0x82, a
0x0000ae78      e4             clr a
0x0000ae79      3477           addc a, #0x77
0x0000ae7b      f583           mov 0x83, a
0x0000ae7d      e4             clr a
0x0000ae7e      93             movc a, @a+dptr
0x0000ae7f      fb             mov r3, a
0x0000ae80      7a00           mov r2, #0x00
0x0000ae82      d3             setb c
0x0000ae83      ef             mov a, r7
0x0000ae84      9b             subb a, r3
0x0000ae85      ee             mov a, r6
0x0000ae86      9a             subb a, r2
0x0000ae87      402a           jc 0xaeb3
0x0000ae89      906874         mov dptr, #0x6874
0x0000ae8c      e0             movx a, @dptr
0x0000ae8d      75f008         mov 0xf0, #0x08
0x0000ae90      a4             mul ab
0x0000ae91      2490           add a, #0x90
0x0000ae93      f582           mov 0x82, a
0x0000ae95      e4             clr a
0x0000ae96      3477           addc a, #0x77
0x0000ae98      f583           mov 0x83, a
0x0000ae9a      e4             clr a
0x0000ae9b      93             movc a, @a+dptr
0x0000ae9c      ff             mov r7, a
0x0000ae9d      7e00           mov r6, #0x00
0x0000ae9f      906874         mov dptr, #0x6874
0x0000aea2      e0             movx a, @dptr
0x0000aea3      c3             clr c
0x0000aea4      33             rlc a
0x0000aea5      2418           add a, #0x18
0x0000aea7      f582           mov 0x82, a
0x0000aea9      e4             clr a
0x0000aeaa      346b           addc a, #0x6b
0x0000aeac      f583           mov 0x83, a
0x0000aeae      ee             mov a, r6
0x0000aeaf      f0             movx @dptr, a
0x0000aeb0      a3             inc dptr
0x0000aeb1      ef             mov a, r7
0x0000aeb2      f0             movx @dptr, a
0x0000aeb3      906874         mov dptr, #0x6874
0x0000aeb6      e0             movx a, @dptr
0x0000aeb7      ff             mov r7, a
0x0000aeb8      7401           mov a, #0x01
0x0000aeba      90aac7         mov dptr, #0xaac7
0x0000aebd      1207c5         lcall 0x07c5
0x0000aec0      906874         mov dptr, #0x6874
0x0000aec3      e0             movx a, @dptr
0x0000aec4      ff             mov r7, a
0x0000aec5      7401           mov a, #0x01
0x0000aec7      90aed0         mov dptr, #0xaed0
0x0000aeca      1207c5         lcall 0x07c5
0x0000aecd      0207e4         ljmp 0x07e4

BANK 1 CPU a3c1 FILE 0123c1
0x0000a3c1      90687c         mov dptr, #0x687c
0x0000a3c4      ef             mov a, r7
0x0000a3c5      f0             movx @dptr, a
0x0000a3c6      9073ba         mov dptr, #0x73ba
0x0000a3c9      7401           mov a, #0x01
0x0000a3cb      f0             movx @dptr, a
0x0000a3cc      906aff         mov dptr, #0x6aff
0x0000a3cf      e0             movx a, @dptr
0x0000a3d0      5420           anl a, #0x20
0x0000a3d2      6057           jz 0xa42b
0x0000a3d4      7400           mov a, #0x00
0x0000a3d6      90f76b         mov dptr, #0xf76b
0x0000a3d9      1207c5         lcall 0x07c5
0x0000a3dc      90687c         mov dptr, #0x687c
0x0000a3df      e0             movx a, @dptr
0x0000a3e0      6024           jz 0xa406
0x0000a3e2      906afe         mov dptr, #0x6afe
0x0000a3e5      e0             movx a, @dptr
0x0000a3e6      2402           add a, #0x02
0x0000a3e8      f582           mov 0x82, a
0x0000a3ea      e4             clr a
0x0000a3eb      346b           addc a, #0x6b
0x0000a3ed      f583           mov 0x83, a
0x0000a3ef      e0             movx a, @dptr
0x0000a3f0      647f           xrl a, #0x7f
0x0000a3f2      6010           jz 0xa404
0x0000a3f4      906afe         mov dptr, #0x6afe
0x0000a3f7      e0             movx a, @dptr
0x0000a3f8      2402           add a, #0x02
0x0000a3fa      f582           mov 0x82, a
0x0000a3fc      e4             clr a
0x0000a3fd      346b           addc a, #0x6b
0x0000a3ff      f583           mov 0x83, a
0x0000a401      e0             movx a, @dptr
0x0000a402      04             inc a
0x0000a403      f0             movx @dptr, a
0x0000a404      8022           sjmp 0xa428
0x0000a406      906afe         mov dptr, #0x6afe
0x0000a409      e0             movx a, @dptr
0x0000a40a      2402           add a, #0x02
0x0000a40c      f582           mov 0x82, a
0x0000a40e      e4             clr a
0x0000a40f      346b           addc a, #0x6b
0x0000a411      f583           mov 0x83, a
0x0000a413      e0             movx a, @dptr
0x0000a414      6480           xrl a, #0x80
0x0000a416      6010           jz 0xa428
0x0000a418      906afe         mov dptr, #0x6afe
0x0000a41b      e0             movx a, @dptr
0x0000a41c      2402           add a, #0x02
0x0000a41e      f582           mov 0x82, a
0x0000a420      e4             clr a
0x0000a421      346b           addc a, #0x6b
0x0000a423      f583           mov 0x83, a
0x0000a425      e0             movx a, @dptr
0x0000a426      14             dec a
0x0000a427      f0             movx @dptr, a
0x0000a428      02a4e2         ljmp 0xa4e2
0x0000a42b      90687c         mov dptr, #0x687c
0x0000a42e      e0             movx a, @dptr
0x0000a42f      6059           jz 0xa48a
0x0000a431      906afe         mov dptr, #0x6afe
0x0000a434      e0             movx a, @dptr
0x0000a435      2402           add a, #0x02
0x0000a437      f582           mov 0x82, a
0x0000a439      e4             clr a
0x0000a43a      346b           addc a, #0x6b
0x0000a43c      f583           mov 0x83, a
0x0000a43e      e0             movx a, @dptr
0x0000a43f      ff             mov r7, a
0x0000a440      906afe         mov dptr, #0x6afe
0x0000a443      e0             movx a, @dptr
0x0000a444      fb             mov r3, a
0x0000a445      33             rlc a
0x0000a446      95e0           subb a, 0xe0
0x0000a448      c007           push 0x07
0x0000a44a      fe             mov r6, a
0x0000a44b      8b07           mov 0x07, r3
0x0000a44d      7902           mov r1, #0x02
0x0000a44f      7a77           mov r2, #0x77
0x0000a451      7bd3           mov r3, #0xd3
0x0000a453      741b           mov a, #0x1b
0x0000a455      122753         lcall 0x2753
0x0000a458      122625         lcall 0x2625
0x0000a45b      d0e0           pop 0xe0
0x0000a45d      c3             clr c
0x0000a45e      9f             subb a, r7
0x0000a45f      5027           jnc 0xa488
0x0000a461      906afe         mov dptr, #0x6afe
0x0000a464      e0             movx a, @dptr
0x0000a465      ff             mov r7, a
0x0000a466      33             rlc a
0x0000a467      95e0           subb a, 0xe0
0x0000a469      fe             mov r6, a
0x0000a46a      7902           mov r1, #0x02
0x0000a46c      7a77           mov r2, #0x77
0x0000a46e      7bd5           mov r3, #0xd5
0x0000a470      741b           mov a, #0x1b
0x0000a472      122753         lcall 0x2753
0x0000a475      122625         lcall 0x2625
0x0000a478      906afe         mov dptr, #0x6afe
0x0000a47b      e0             movx a, @dptr
0x0000a47c      2402           add a, #0x02
0x0000a47e      f582           mov 0x82, a
0x0000a480      e4             clr a
0x0000a481      346b           addc a, #0x6b
0x0000a483      f583           mov 0x83, a
0x0000a485      e0             movx a, @dptr
0x0000a486      2f             add a, r7
0x0000a487      f0             movx @dptr, a
0x0000a488      8058           sjmp 0xa4e2
0x0000a48a      906afe         mov dptr, #0x6afe
0x0000a48d      e0             movx a, @dptr
0x0000a48e      2402           add a, #0x02
0x0000a490      f582           mov 0x82, a
0x0000a492      e4             clr a
0x0000a493      346b           addc a, #0x6b
0x0000a495      f583           mov 0x83, a
0x0000a497      e0             movx a, @dptr
0x0000a498      ff             mov r7, a
0x0000a499      906afe         mov dptr, #0x6afe
0x0000a49c      e0             movx a, @dptr
0x0000a49d      fb             mov r3, a
0x0000a49e      33             rlc a
0x0000a49f      95e0           subb a, 0xe0
0x0000a4a1      c007           push 0x07
0x0000a4a3      fe             mov r6, a
0x0000a4a4      8b07           mov 0x07, r3
0x0000a4a6      7902           mov r1, #0x02
0x0000a4a8      7a77           mov r2, #0x77
0x0000a4aa      7bd2           mov r3, #0xd2
0x0000a4ac      741b           mov a, #0x1b
0x0000a4ae      122753         lcall 0x2753
0x0000a4b1      122625         lcall 0x2625
0x0000a4b4      d0e0           pop 0xe0
0x0000a4b6      d3             setb c
0x0000a4b7      9f             subb a, r7
0x0000a4b8      4028           jc 0xa4e2
0x0000a4ba      906afe         mov dptr, #0x6afe
0x0000a4bd      e0             movx a, @dptr
0x0000a4be      ff             mov r7, a
0x0000a4bf      33             rlc a
0x0000a4c0      95e0           subb a, 0xe0
0x0000a4c2      fe             mov r6, a
0x0000a4c3      7902           mov r1, #0x02
0x0000a4c5      7a77           mov r2, #0x77
0x0000a4c7      7bd5           mov r3, #0xd5
0x0000a4c9      741b           mov a, #0x1b
0x0000a4cb      122753         lcall 0x2753
0x0000a4ce      122625         lcall 0x2625
0x0000a4d1      906afe         mov dptr, #0x6afe
0x0000a4d4      e0             movx a, @dptr
0x0000a4d5      2402           add a, #0x02
0x0000a4d7      f582           mov 0x82, a
0x0000a4d9      e4             clr a
0x0000a4da      346b           addc a, #0x6b
0x0000a4dc      f583           mov 0x83, a
0x0000a4de      e0             movx a, @dptr
0x0000a4df      c3             clr c
0x0000a4e0      9f             subb a, r7
0x0000a4e1      f0             movx @dptr, a
0x0000a4e2      906aff         mov dptr, #0x6aff
0x0000a4e5      e0             movx a, @dptr
0x0000a4e6      5410           anl a, #0x10
0x0000a4e8      7003           jnz 0xa4ed
0x0000a4ea      02a56b         ljmp 0xa56b
0x0000a4ed      906afe         mov dptr, #0x6afe
0x0000a4f0      e0             movx a, @dptr
0x0000a4f1      2402           add a, #0x02
0x0000a4f3      f582           mov 0x82, a
0x0000a4f5      e4             clr a
0x0000a4f6      346b           addc a, #0x6b
0x0000a4f8      f583           mov 0x83, a
0x0000a4fa      e0             movx a, @dptr
0x0000a4fb      c3             clr c
0x0000a4fc      13             rrc a
0x0000a4fd      c3             clr c
0x0000a4fe      13             rrc a
0x0000a4ff      ff             mov r7, a
0x0000a500      e4             clr a
0x0000a501      90687a         mov dptr, #0x687a
0x0000a504      f0             movx @dptr, a
0x0000a505      a3             inc dptr
0x0000a506      fe             mov r6, a
0x0000a507      ef             mov a, r7
0x0000a508      f0             movx @dptr, a
0x0000a509      ee             mov a, r6
0x0000a50a      7bd7           mov r3, #0xd7
0x0000a50c      7a02           mov r2, #0x02
0x0000a50e      121d6f         lcall 0x1d6f
0x0000a511      ee             mov a, r6
0x0000a512      ff             mov r7, a
0x0000a513      33             rlc a
0x0000a514      95e0           subb a, 0xe0
0x0000a516      ef             mov a, r7
0x0000a517      54fc           anl a, #0xfc
0x0000a519      ff             mov r7, a
0x0000a51a      906afe         mov dptr, #0x6afe
0x0000a51d      e0             movx a, @dptr
0x0000a51e      04             inc a
0x0000a51f      2402           add a, #0x02
0x0000a521      f582           mov 0x82, a
0x0000a523      e4             clr a
0x0000a524      346b           addc a, #0x6b
0x0000a526      f583           mov 0x83, a
0x0000a528      ef             mov a, r7
0x0000a529      f0             movx @dptr, a
0x0000a52a      906afe         mov dptr, #0x6afe
0x0000a52d      e0             movx a, @dptr
0x0000a52e      ff             mov r7, a
0x0000a52f      33             rlc a
0x0000a530      95e0           subb a, 0xe0
0x0000a532      fe             mov r6, a
0x0000a533      7902           mov r1, #0x02
0x0000a535      7a77           mov r2, #0x77
0x0000a537      7bf0           mov r3, #0xf0
0x0000a539      741b           mov a, #0x1b
0x0000a53b      122753         lcall 0x2753
0x0000a53e      122625         lcall 0x2625
0x0000a541      906865         mov dptr, #0x6865
0x0000a544      ef             mov a, r7
0x0000a545      f0             movx @dptr, a
0x0000a546      906afd         mov dptr, #0x6afd
0x0000a549      e0             movx a, @dptr
0x0000a54a      04             inc a
0x0000a54b      906866         mov dptr, #0x6866
0x0000a54e      f0             movx @dptr, a
0x0000a54f      a3             inc dptr
0x0000a550      7420           mov a, #0x20
0x0000a552      f0             movx @dptr, a
0x0000a553      906afe         mov dptr, #0x6afe
0x0000a556      e0             movx a, @dptr
0x0000a557      04             inc a
0x0000a558      2402           add a, #0x02
0x0000a55a      f582           mov 0x82, a
0x0000a55c      e4             clr a
0x0000a55d      346b           addc a, #0x6b
0x0000a55f      f583           mov 0x83, a
0x0000a561      e0             movx a, @dptr
0x0000a562      ff             mov r7, a
0x0000a563      7401           mov a, #0x01
0x0000a565      909a68         mov dptr, #0x9a68
0x0000a568      1207c5         lcall 0x07c5

BANK 1 CPU ff46 FILE 017f46
0x0000ff46      121d3a         lcall 0x1d3a
0x0000ff49      ef             mov a, r7
0x0000ff4a      7003           jnz 0xff4f
0x0000ff4c      0207e4         ljmp 0x07e4
0x0000ff4f      906862         mov dptr, #0x6862
0x0000ff52      74a1           mov a, #0xa1
0x0000ff54      f0             movx @dptr, a
0x0000ff55      a3             inc dptr
0x0000ff56      748c           mov a, #0x8c
0x0000ff58      f0             movx @dptr, a
0x0000ff59      7fff           mov r7, #0xff
0x0000ff5b      7402           mov a, #0x02
0x0000ff5d      908fb4         mov dptr, #0x8fb4
0x0000ff60      1207c5         lcall 0x07c5
0x0000ff63      906ea9         mov dptr, #0x6ea9
0x0000ff66      e0             movx a, @dptr
0x0000ff67      604d           jz 0xffb6
0x0000ff69      30054a         jnb 0x20.5, 0xffb6
0x0000ff6c      906ea9         mov dptr, #0x6ea9
0x0000ff6f      e0             movx a, @dptr
0x0000ff70      906e6f         mov dptr, #0x6e6f
0x0000ff73      f0             movx @dptr, a
0x0000ff74      906ea9         mov dptr, #0x6ea9
0x0000ff77      e4             clr a
0x0000ff78      f0             movx @dptr, a
0x0000ff79      906e6f         mov dptr, #0x6e6f
0x0000ff7c      e0             movx a, @dptr
0x0000ff7d      5440           anl a, #0x40
0x0000ff7f      7025           jnz 0xffa6
0x0000ff81      906e6f         mov dptr, #0x6e6f
0x0000ff84      e0             movx a, @dptr
0x0000ff85      543f           anl a, #0x3f
0x0000ff87      24d5           add a, #0xd5
0x0000ff89      f582           mov 0x82, a
0x0000ff8b      e4             clr a
0x0000ff8c      347d           addc a, #0x7d
0x0000ff8e      f583           mov 0x83, a
0x0000ff90      e4             clr a
0x0000ff91      93             movc a, @a+dptr
0x0000ff92      ff             mov r7, a
0x0000ff93      7403           mov a, #0x03
0x0000ff95      90ad43         mov dptr, #0xad43
0x0000ff98      1207c5         lcall 0x07c5
0x0000ff9b      ef             mov a, r7
0x0000ff9c      7008           jnz 0xffa6
0x0000ff9e      7403           mov a, #0x03
0x0000ffa0      90c26e         mov dptr, #0xc26e
0x0000ffa3      1207c5         lcall 0x07c5
0x0000ffa6      906e6f         mov dptr, #0x6e6f
0x0000ffa9      e0             movx a, @dptr
0x0000ffaa      64b4           xrl a, #0xb4
0x0000ffac      7008           jnz 0xffb6
0x0000ffae      7403           mov a, #0x03
0x0000ffb0      90c4a5         mov dptr, #0xc4a5
0x0000ffb3      1207c5         lcall 0x07c5
0x0000ffb6      80ab           sjmp 0xff63
