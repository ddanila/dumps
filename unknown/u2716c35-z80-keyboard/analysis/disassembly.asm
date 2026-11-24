; z80dasm 1.1.6
; command line: z80dasm -a -t -l -g 0x6800 -b blocks.txt -S symbols.txt -o disassembly.asm ../rom.bin

	org	06800h
keymap_external:	equ 0x7130
sequences_external:	equ 0x71f0
current_keys:	equ 0x789f
current_count:	equ 0x78a5
repeat_countdown:	equ 0x78a6
previous_keys:	equ 0x78a7
key_flags:	equ 0x78af
key_ready:	equ 0x78b1
output_key:	equ 0x78b2
queue_write_pointer:	equ 0x78b3
queue_read_pointer:	equ 0x78b5
repeat_key:	equ 0x78b7
queue_start:	equ 0x7942


; BLOCK 'header' (start 0x6800 end 0x6838)
header_start:
	defw 01831h		;6800	31 18 	1 .
	defw 0101ch		;6802	1c 10 	. .
	defw 0ffffh		;6804	ff ff 	. .
	defw 0ffffh		;6806	ff ff 	. .
	defw 0ffffh		;6808	ff ff 	. .
	defw 01000h		;680a	00 10 	. .
	defw 01800h		;680c	00 18 	. .
	defw 01814h		;680e	14 18 	. .
	defw 010e2h		;6810	e2 10 	. .
	defw 01161h		;6812	61 11 	a .
	defw 01128h		;6814	28 11 	( .
	defw 0114bh		;6816	4b 11 	K .
	defw 06dbah		;6818	ba 6d 	. m
	defw 018e1h		;681a	e1 18 	. .
	defw 0ffffh		;681c	ff ff 	. .
	defw 0ffffh		;681e	ff ff 	. .
	defw 03730h		;6820	30 37 	0 7
	defw 026b0h		;6822	b0 26 	. &
	defw 0ffffh		;6824	ff ff 	. .
	defw 0066bh		;6826	6b 06 	k .
	defw 069deh		;6828	de 69 	. i
	defw 0ffffh		;682a	ff ff 	. .
	defw 069e1h		;682c	e1 69 	. i
	defw 01b23h		;682e	23 1b 	# .
	defw 02520h		;6830	20 25 	  %
	defw 0247ch		;6832	7c 24 	| $
	defw 026b3h		;6834	b3 26 	. &
	defw 024ceh		;6836	ce 24 	. $
header_end:

; BLOCK 'header_padding' (start 0x6838 end 0x6858)
header_padding_start:
	defb 0ffh		;6838	ff 	.
	defb 0ffh		;6839	ff 	.
	defb 0ffh		;683a	ff 	.
	defb 0ffh		;683b	ff 	.
	defb 0ffh		;683c	ff 	.
	defb 0ffh		;683d	ff 	.
	defb 0ffh		;683e	ff 	.
	defb 0ffh		;683f	ff 	.
	defb 0ffh		;6840	ff 	.
	defb 0ffh		;6841	ff 	.
	defb 0ffh		;6842	ff 	.
	defb 0ffh		;6843	ff 	.
	defb 0ffh		;6844	ff 	.
	defb 0ffh		;6845	ff 	.
	defb 0ffh		;6846	ff 	.
	defb 0ffh		;6847	ff 	.
	defb 0ffh		;6848	ff 	.
	defb 0ffh		;6849	ff 	.
	defb 0ffh		;684a	ff 	.
	defb 0ffh		;684b	ff 	.
	defb 0ffh		;684c	ff 	.
	defb 0ffh		;684d	ff 	.
	defb 0ffh		;684e	ff 	.
	defb 0ffh		;684f	ff 	.
	defb 0ffh		;6850	ff 	.
	defb 0ffh		;6851	ff 	.
	defb 0ffh		;6852	ff 	.
	defb 0ffh		;6853	ff 	.
	defb 0ffh		;6854	ff 	.
	defb 0ffh		;6855	ff 	.
	defb 0ffh		;6856	ff 	.
	defb 0ffh		;6857	ff 	.
header_padding_end:

; BLOCK 'dispatch' (start 0x6858 end 0x69c6)
dispatch_start:
	jp 0014bh		;6858	c3 4b 01 	. K .
	jp l6dd3h		;685b	c3 d3 6d 	. . m
	jp 0036ah		;685e	c3 6a 03 	. j .
	jp 0ffffh		;6861	c3 ff ff 	. . .
	jp 006c5h		;6864	c3 c5 06 	. . .
	jp 006fbh		;6867	c3 fb 06 	. . .
l686ah:
	jp 00637h		;686a	c3 37 06 	. 7 .
	jp 00575h		;686d	c3 75 05 	. u .
	jp 005efh		;6870	c3 ef 05 	. . .
	jp 00526h		;6873	c3 26 05 	. & .
	jp 004f9h		;6876	c3 f9 04 	. . .
	jp 004c8h		;6879	c3 c8 04 	. . .
	jp 003ech		;687c	c3 ec 03 	. . .
	jp 0075fh		;687f	c3 5f 07 	. _ .
	jp 0366ah		;6882	c3 6a 36 	. j 6
	jp 0ffffh		;6885	c3 ff ff 	. . .
	jp l6de7h		;6888	c3 e7 6d 	. . m
	jp 0ffffh		;688b	c3 ff ff 	. . .
	jp 016abh		;688e	c3 ab 16 	. . .
	jp 01662h		;6891	c3 62 16 	. b .
	jp 00ba0h		;6894	c3 a0 0b 	. . .
	jp 00038h		;6897	c3 38 00 	. 8 .
	jp 01035h		;689a	c3 35 10 	. 5 .
	jp 0106ch		;689d	c3 6c 10 	. l .
	jp 01077h		;68a0	c3 77 10 	. w .
	jp 01098h		;68a3	c3 98 10 	. . .
	jp l6da5h		;68a6	c3 a5 6d 	. . m
	jp 01042h		;68a9	c3 42 10 	. B .
	jp 01060h		;68ac	c3 60 10 	. ` .
	jp 0ffffh		;68af	c3 ff ff 	. . .
	jp 0128ch		;68b2	c3 8c 12 	. . .
	jp 01242h		;68b5	c3 42 12 	. B .
	jp 01227h		;68b8	c3 27 12 	. ' .
	jp 01200h		;68bb	c3 00 12 	. . .
	jp 0160bh		;68be	c3 0b 16 	. . .
	jp 01715h		;68c1	c3 15 17 	. . .
	jp 0195ah		;68c4	c3 5a 19 	. Z .
	jp 01a49h		;68c7	c3 49 1a 	. I .
	jp 01842h		;68ca	c3 42 18 	. B .
	jp 01aedh		;68cd	c3 ed 1a 	. . .
	jp 0ffffh		;68d0	c3 ff ff 	. . .
	jp 01b20h		;68d3	c3 20 1b 	.   .
	jp 01b26h		;68d6	c3 26 1b 	. & .
	jp 01b29h		;68d9	c3 29 1b 	. ) .
	jp 0ffffh		;68dc	c3 ff ff 	. . .
	jp 02321h		;68df	c3 21 23 	. ! #
	jp 0232bh		;68e2	c3 2b 23 	. + #
	jp 02020h		;68e5	c3 20 20 	.
	jp 02058h		;68e8	c3 58 20 	. X
	jp 0205dh		;68eb	c3 5d 20 	. ]
	jp 02000h		;68ee	c3 00 20 	. .
	jp 02005h		;68f1	c3 05 20 	. .
	jp 02117h		;68f4	c3 17 21 	. . !
	jp 0ffffh		;68f7	c3 ff ff 	. . .
	jp 02420h		;68fa	c3 20 24 	.   $
	jp 02443h		;68fd	c3 43 24 	. C $
	jp 0245ah		;6900	c3 5a 24 	. Z $
	jp 02481h		;6903	c3 81 24 	. . $
	jp 024d3h		;6906	c3 d3 24 	. . $
	jp 02468h		;6909	c3 68 24 	. h $
	jp 0252ah		;690c	c3 2a 25 	. * %
	jp 02550h		;690f	c3 50 25 	. P %
	jp 025eah		;6912	c3 ea 25 	. . %
	jp 02650h		;6915	c3 50 26 	. P &
	jp 02597h		;6918	c3 97 25 	. . %
	jp 02629h		;691b	c3 29 26 	. ) &
	jp 02666h		;691e	c3 66 26 	. f &
	jp 0ffffh		;6921	c3 ff ff 	. . .
	jp 026b6h		;6924	c3 b6 26 	. . &
	jp 02800h		;6927	c3 00 28 	. . (
	jp 00038h		;692a	c3 38 00 	. 8 .
	jp 02a85h		;692d	c3 85 2a 	. . *
	jp 02a6dh		;6930	c3 6d 2a 	. m *
	jp 02854h		;6933	c3 54 28 	. T (
	jp 0ffffh		;6936	c3 ff ff 	. . .
	jp 02dc6h		;6939	c3 c6 2d 	. . -
	jp 02aa4h		;693c	c3 a4 2a 	. . *
	jp 029abh		;693f	c3 ab 29 	. . )
	jp 02c66h		;6942	c3 66 2c 	. f ,
	jp 02bc5h		;6945	c3 c5 2b 	. . +
	jp 02bd3h		;6948	c3 d3 2b 	. . +
	jp 02b4bh		;694b	c3 4b 2b 	. K +
	jp 0293bh		;694e	c3 3b 29 	. ; )
	jp 02efah		;6951	c3 fa 2e 	. . .
	jp 0ffffh		;6954	c3 ff ff 	. . .
	jp 035d9h		;6957	c3 d9 35 	. . 5
	jp 035efh		;695a	c3 ef 35 	. . 5
	jp 033f0h		;695d	c3 f0 33 	. . 3
	jp 03516h		;6960	c3 16 35 	. . 5
	jp 034a8h		;6963	c3 a8 34 	. . 4
	jp 0446eh		;6966	c3 6e 44 	. n D
	jp 04490h		;6969	c3 90 44 	. . D
	jp 0389fh		;696c	c3 9f 38 	. . 8
	jp 03b75h		;696f	c3 75 3b 	. u ;
	jp 03c69h		;6972	c3 69 3c 	. i <
	jp 04210h		;6975	c3 10 42 	. . B
	jp 03811h		;6978	c3 11 38 	. . 8
	jp 03d80h		;697b	c3 80 3d 	. . =
	jp 03ef2h		;697e	c3 f2 3e 	. . >
	jp 03f3fh		;6981	c3 3f 3f 	. ? ?
	jp 04618h		;6984	c3 18 46 	. . F
	jp 038fch		;6987	c3 fc 38 	. . 8
	jp 040abh		;698a	c3 ab 40 	. . @
	jp 03800h		;698d	c3 00 38 	. . 8
	jp 045b5h		;6990	c3 b5 45 	. . E
	jp 0ffffh		;6993	c3 ff ff 	. . .
	jp 04d6ch		;6996	c3 6c 4d 	. l M
	jp 04e3bh		;6999	c3 3b 4e 	. ; N
	jp 051cdh		;699c	c3 cd 51 	. . Q
	jp 0495bh		;699f	c3 5b 49 	. [ I
	jp 051eah		;69a2	c3 ea 51 	. . Q
	jp 04e2ch		;69a5	c3 2c 4e 	. , N
	jp 04a2dh		;69a8	c3 2d 4a 	. - J
	jp 0489dh		;69ab	c3 9d 48 	. . H
	jp translations_end		;69ae	c3 81 6d 	. . m
	jp 048dbh		;69b1	c3 db 48 	. . H
	jp 0ffffh		;69b4	c3 ff ff 	. . .
	jp 0ffffh		;69b7	c3 ff ff 	. . .
	jp 06003h		;69ba	c3 03 60 	. . `
	jp 06000h		;69bd	c3 00 60 	. . `
	jp 06006h		;69c0	c3 06 60 	. . `
	jp 06009h		;69c3	c3 09 60 	. . `
dispatch_end:

; BLOCK 'dispatch_padding' (start 0x69c6 end 0x69de)
dispatch_padding_start:
	defb 0ffh		;69c6	ff 	.
	defb 0ffh		;69c7	ff 	.
	defb 0ffh		;69c8	ff 	.
	defb 0ffh		;69c9	ff 	.
	defb 0ffh		;69ca	ff 	.
	defb 0ffh		;69cb	ff 	.
	defb 0ffh		;69cc	ff 	.
	defb 0ffh		;69cd	ff 	.
	defb 0ffh		;69ce	ff 	.
	defb 0ffh		;69cf	ff 	.
	defb 0ffh		;69d0	ff 	.
	defb 0ffh		;69d1	ff 	.
	defb 0ffh		;69d2	ff 	.
	defb 0ffh		;69d3	ff 	.
	defb 0ffh		;69d4	ff 	.
	defb 0ffh		;69d5	ff 	.
	defb 0ffh		;69d6	ff 	.
	defb 0ffh		;69d7	ff 	.
	defb 0ffh		;69d8	ff 	.
	defb 0ffh		;69d9	ff 	.
	defb 0ffh		;69da	ff 	.
	defb 0ffh		;69db	ff 	.
	defb 0ffh		;69dc	ff 	.
	defb 0ffh		;69dd	ff 	.
dispatch_padding_end:

; BLOCK 'keyboard' (start 0x69de end 0x6d5d)
keyboard_start:
	jp scan_irq		;69de	c3 1f 6a 	. . j
release_irq:
	rst 10h			;69e1	d7 	.
	push ix		;69e2	dd e5 	. .
	ei			;69e4	fb 	.
	ld de,(key_flags)		;69e5	ed 5b af 78 	. [ . x
	ld c,003h		;69e9	0e 03 	. .
	ld hl,release_special		;69eb	21 fe 69 	! . i
	ld ix,previous_keys		;69ee	dd 21 a7 78 	. ! . x
	call translate_and_dispatch		;69f2	cd 4b 6b 	. K k
	ld (key_flags),de		;69f5	ed 53 af 78 	. S . x
	pop ix		;69f9	dd e1 	. .
	rst 18h			;69fb	df 	.
	reti		;69fc	ed 4d 	. M
release_special:
	cp 0a5h		;69fe	fe a5 	. .
	jr z,l6a0fh		;6a00	28 0d 	( .
	cp 0bdh		;6a02	fe bd 	. .
	jr z,l6a13h		;6a04	28 0d 	( .
	cp 0abh		;6a06	fe ab 	. .
	ret nz			;6a08	c0 	.
	ld a,0ach		;6a09	3e ac 	> .
	set 7,e		;6a0b	cb fb 	. .
	jr l6a17h		;6a0d	18 08 	. .
l6a0fh:
	set 5,e		;6a0f	cb eb 	. .
	jr l6a17h		;6a11	18 04 	. .
l6a13h:
	set 6,e		;6a13	cb f3 	. .
	ld a,0beh		;6a15	3e be 	> .
l6a17h:
	ld (ix+003h),0ffh		;6a17	dd 36 03 ff 	. 6 . .
	call emit_key		;6a1b	cd d8 6c 	. . l
	ret			;6a1e	c9 	.
scan_irq:
	rst 10h			;6a1f	d7 	.
	push ix		;6a20	dd e5 	. .
	push iy		;6a22	fd e5 	. .
	ei			;6a24	fb 	.
	call scan_matrix		;6a25	cd e4 6a 	. . j
	ld de,(key_flags)		;6a28	ed 5b af 78 	. [ . x
	ld a,(current_count)		;6a2c	3a a5 78 	: . x
	cp 004h		;6a2f	fe 04 	. .
	jr z,l6a62h		;6a31	28 2f 	( /
	res 0,d		;6a33	cb 82 	. .
	res 4,d		;6a35	cb a2 	. .
	res 5,d		;6a37	cb aa 	. .
	cp 000h		;6a39	fe 00 	. .
	jr z,l6a55h		;6a3b	28 18 	( .
	ld c,003h		;6a3d	0e 03 	. .
	ld hl,classify_special		;6a3f	21 80 6a 	! . j
	ld ix,current_keys		;6a42	dd 21 9f 78 	. ! . x
	call translate_and_dispatch		;6a46	cd 4b 6b 	. K k
	ld c,002h		;6a49	0e 02 	. .
	ld hl,process_key		;6a4b	21 b5 6a 	! . j
	ld ix,current_keys		;6a4e	dd 21 9f 78 	. ! . x
	call translate_and_dispatch		;6a52	cd 4b 6b 	. K k
l6a55h:
	push de			;6a55	d5 	.
	ld hl,current_keys		;6a56	21 9f 78 	! . x
	ld de,previous_keys		;6a59	11 a7 78 	. . x
	ld bc,00007h		;6a5c	01 07 00 	. . .
	ldir		;6a5f	ed b0 	. .
	pop de			;6a61	d1 	.
l6a62h:
	di			;6a62	f3 	.
	bit 0,d		;6a63	cb 42 	. B
	jr nz,l6a6ch		;6a65	20 05 	  .
	ld a,043h		;6a67	3e 43 	> C
	out (0b2h),a		;6a69	d3 b2 	. .
	ei			;6a6b	fb 	.
l6a6ch:
	ld hl,key_ready		;6a6c	21 b1 78 	! . x
	bit 0,(hl)		;6a6f	cb 46 	. F
	call z,queue_get_or_repeat		;6a71	cc 0b 6d 	. . m
	ld (key_flags),de		;6a74	ed 53 af 78 	. S . x
	pop iy		;6a78	fd e1 	. .
	pop ix		;6a7a	dd e1 	. .
	rst 18h			;6a7c	df 	.
	ei			;6a7d	fb 	.
	reti		;6a7e	ed 4d 	. M
classify_special:
	cp 0a5h		;6a80	fe a5 	. .
	jr z,l6a99h		;6a82	28 15 	( .
	cp 0abh		;6a84	fe ab 	. .
	jr z,l6a99h		;6a86	28 11 	( .
	cp 0bdh		;6a88	fe bd 	. .
	jr z,l6a99h		;6a8a	28 0d 	( .
	cp 0e3h		;6a8c	fe e3 	. .
	jr z,l6a9ch		;6a8e	28 0c 	( .
	cp 0e4h		;6a90	fe e4 	. .
	jr z,l6a9fh		;6a92	28 0b 	( .
	cp 0e2h		;6a94	fe e2 	. .
	jr z,l6aa2h		;6a96	28 0a 	( .
	ret			;6a98	c9 	.
l6a99h:
	set 0,d		;6a99	cb c2 	. .
	ret			;6a9b	c9 	.
l6a9ch:
	set 4,d		;6a9c	cb e2 	. .
	ret			;6a9e	c9 	.
l6a9fh:
	set 5,d		;6a9f	cb ea 	. .
	ret			;6aa1	c9 	.
l6aa2h:
	ld a,(queue_write_pointer)		;6aa2	3a b3 78 	: . x
	ld hl,queue_read_pointer		;6aa5	21 b5 78 	! . x
	cp (hl)			;6aa8	be 	.
	ret nz			;6aa9	c0 	.
	bit 3,d		;6aaa	cb 5a 	. Z
	ret nz			;6aac	c0 	.
	res 3,e		;6aad	cb 9b 	. .
	ld hl,07918h		;6aaf	21 18 79 	! . y
	res 4,(hl)		;6ab2	cb a6 	. .
	ret			;6ab4	c9 	.
process_key:
	set 7,d		;6ab5	cb fa 	. .
	set 6,d		;6ab7	cb f2 	. .
	cp 0e3h		;6ab9	fe e3 	. .
	jr z,l6ac0h		;6abb	28 03 	( .
	ld (repeat_key),a		;6abd	32 b7 78 	2 . x
l6ac0h:
	ld (ix+003h),0ffh		;6ac0	dd 36 03 ff 	. 6 . .
	bit 0,e		;6ac4	cb 43 	. C
	call nz,alternate_translation		;6ac6	c4 42 6c 	. B l
	bit 7,a		;6ac9	cb 7f 	. 
	jr z,l6adeh		;6acb	28 11 	( .
	bit 1,e		;6acd	cb 4b 	. K
	call nz,sub_6c76h		;6acf	c4 76 6c 	. v l
	cp 0f0h		;6ad2	fe f0 	. .
	jr c,l6adbh		;6ad4	38 05 	8 .
	call function_sequence		;6ad6	cd 8f 6c 	. . l
	jr l6adeh		;6ad9	18 03 	. .
l6adbh:
	call special_key		;6adb	cd 84 6b 	. . k
l6adeh:
	bit 7,d		;6ade	cb 7a 	. z
	call nz,emit_translated		;6ae0	c4 a8 6c 	. . l
	ret			;6ae3	c9 	.
scan_matrix:
	ld ix,current_keys		;6ae4	dd 21 9f 78 	. ! . x
	ld bc,00c00h		;6ae8	01 00 0c 	. . .
	di			;6aeb	f3 	.
	in a,(0c8h)		;6aec	db c8 	. .
	and 0f0h		;6aee	e6 f0 	. .
l6af0h:
	out (0c8h),a		;6af0	d3 c8 	. .
	ld d,0ffh		;6af2	16 ff 	. .
	in a,(0c9h)		;6af4	db c9 	. .
	cp 0ffh		;6af6	fe ff 	. .
	jr z,l6b39h		;6af8	28 3f 	( ?
	ei			;6afa	fb 	.
	cpl			;6afb	2f 	/
l6afch:
	inc c			;6afc	0c 	.
	bit 2,c		;6afd	cb 51 	. Q
	jr nz,l6b3eh		;6aff	20 3d 	  =
l6b01h:
	inc d			;6b01	14 	.
	srl a		;6b02	cb 3f 	. ?
	jr nc,l6b01h		;6b04	30 fb 	0 .
	push af			;6b06	f5 	.
	ld a,00ch		;6b07	3e 0c 	> .
	sub b			;6b09	90 	.
	rlca			;6b0a	07 	.
	rlca			;6b0b	07 	.
	rlca			;6b0c	07 	.
	add a,d			;6b0d	82 	.
	rlca			;6b0e	07 	.
	ld (ix+000h),a		;6b0f	dd 77 00 	. w .
	ld (ix+003h),001h		;6b12	dd 36 03 01 	. 6 . .
	ld iy,repeat_countdown		;6b16	fd 21 a6 78 	. ! . x
	ld e,(iy+007h)		;6b1a	fd 5e 07 	. ^ .
l6b1dh:
	dec e			;6b1d	1d 	.
	jp m,l6b33h		;6b1e	fa 33 6b 	. 3 k
	inc iy		;6b21	fd 23 	. #
	cp (iy+000h)		;6b23	fd be 00 	. . .
	jr nz,l6b1dh		;6b26	20 f5 	  .
	ld a,(iy+003h)		;6b28	fd 7e 03 	. ~ .
	cp 001h		;6b2b	fe 01 	. .
	jr nz,l6b30h		;6b2d	20 01 	  .
	inc a			;6b2f	3c 	<
l6b30h:
	ld (ix+003h),a		;6b30	dd 77 03 	. w .
l6b33h:
	inc ix		;6b33	dd 23 	. #
	pop af			;6b35	f1 	.
	jr nz,l6afch		;6b36	20 c4 	  .
	di			;6b38	f3 	.
l6b39h:
	in a,(0c8h)		;6b39	db c8 	. .
	inc a			;6b3b	3c 	<
	djnz l6af0h		;6b3c	10 b2 	. .
l6b3eh:
	di			;6b3e	f3 	.
	in a,(0c8h)		;6b3f	db c8 	. .
	or 00fh		;6b41	f6 0f 	. .
	out (0c8h),a		;6b43	d3 c8 	. .
	ld a,c			;6b45	79 	y
	ld (current_count),a		;6b46	32 a5 78 	2 . x
	ei			;6b49	fb 	.
	ret			;6b4a	c9 	.
translate_and_dispatch:
	ld b,(ix+006h)		;6b4b	dd 46 06 	. F .
l6b4eh:
	dec b			;6b4e	05 	.
	ret m			;6b4f	f8 	.
	ld a,c			;6b50	79 	y
	cp (ix+003h)		;6b51	dd be 03 	. . .
	jr nz,l6b80h		;6b54	20 2a 	  *
	push bc			;6b56	c5 	.
	push hl			;6b57	e5 	.
	ld bc,l6b7eh		;6b58	01 7e 6b 	. ~ k
	push bc			;6b5b	c5 	.
	push hl			;6b5c	e5 	.
	ld hl,keymap_external		;6b5d	21 30 71 	! 0 q
	ld c,(ix+000h)		;6b60	dd 4e 00 	. N .
	ld b,000h		;6b63	06 00 	. .
	add hl,bc			;6b65	09 	.
	ld a,(0723eh)		;6b66	3a 3e 72 	: > r
	bit 1,a		;6b69	cb 4f 	. O
	jr nz,l6b77h		;6b6b	20 0a 	  .
	bit 5,d		;6b6d	cb 6a 	. j
	jr nz,l6b7bh		;6b6f	20 0a 	  .
	bit 4,e		;6b71	cb 63 	. c
	jr nz,l6b7bh		;6b73	20 06 	  .
	jr l6b7ch		;6b75	18 05 	. .
l6b77h:
	bit 2,d		;6b77	cb 52 	. R
	jr z,l6b7ch		;6b79	28 01 	( .
l6b7bh:
	inc hl			;6b7b	23 	#
l6b7ch:
	ld a,(hl)			;6b7c	7e 	~
	ret			;6b7d	c9 	.
l6b7eh:
	pop hl			;6b7e	e1 	.
	pop bc			;6b7f	c1 	.
l6b80h:
	inc ix		;6b80	dd 23 	. #
	jr l6b4eh		;6b82	18 ca 	. .
special_key:
	res 6,d		;6b84	cb b2 	. .
	cp 0e2h		;6b86	fe e2 	. .
	jp z,l6c0fh		;6b88	ca 0f 6c 	. . l
	ld hl,07918h		;6b8b	21 18 79 	! . y
	bit 4,(hl)		;6b8e	cb 66 	. f
	jp nz,l686ah		;6b90	c2 6a 68 	. j h
	cp 0a5h		;6b93	fe a5 	. .
	jr z,l6bc8h		;6b95	28 31 	( 1
	cp 0abh		;6b97	fe ab 	. .
	jr z,l6bd3h		;6b99	28 38 	( 8
	cp 0bdh		;6b9b	fe bd 	. .
	jr z,l6bdah		;6b9d	28 3b 	( ;
	cp 0c3h		;6b9f	fe c3 	. .
	jr z,l6bf3h		;6ba1	28 50 	( P
	cp 0e6h		;6ba3	fe e6 	. .
	jr z,l6c01h		;6ba5	28 5a 	( Z
	cp 0e7h		;6ba7	fe e7 	. .
	jr z,l6bfch		;6ba9	28 51 	( Q
	cp 0e1h		;6bab	fe e1 	. .
	jr z,l6bf9h		;6bad	28 4a 	( J
	cp 0e3h		;6baf	fe e3 	. .
	jr z,l6c06h		;6bb1	28 53 	( S
	cp 0e4h		;6bb3	fe e4 	. .
	jr z,l6c0fh		;6bb5	28 58 	( X
	cp 0e5h		;6bb7	fe e5 	. .
	jr z,l6c14h		;6bb9	28 59 	( Y
	cp 0e8h		;6bbb	fe e8 	. .
	jr z,l6c29h		;6bbd	28 6a 	( j
	cp 0e9h		;6bbf	fe e9 	. .
	jr z,l6c3bh		;6bc1	28 78 	( x
	cp 0eah		;6bc3	fe ea 	. .
	jr z,l6c32h		;6bc5	28 6b 	( k
	ret			;6bc7	c9 	.
l6bc8h:
	bit 5,e		;6bc8	cb 6b 	. k
	res 5,e		;6bca	cb ab 	. .
	ret nz			;6bcc	c0 	.
	res 7,d		;6bcd	cb ba 	. .
	ld b,028h		;6bcf	06 28 	. (
	jr l6be2h		;6bd1	18 0f 	. .
l6bd3h:
	bit 7,e		;6bd3	cb 7b 	. {
	res 7,e		;6bd5	cb bb 	. .
	ret nz			;6bd7	c0 	.
	jr l6bdfh		;6bd8	18 05 	. .
l6bdah:
	bit 6,e		;6bda	cb 73 	. s
	res 6,e		;6bdc	cb b3 	. .
	ret nz			;6bde	c0 	.
l6bdfh:
	ld c,a			;6bdf	4f 	O
	ld b,014h		;6be0	06 14 	. .
l6be2h:
	di			;6be2	f3 	.
	ld a,0c7h		;6be3	3e c7 	> .
	out (0b2h),a		;6be5	d3 b2 	. .
	ld a,b			;6be7	78 	x
	out (0b2h),a		;6be8	d3 b2 	. .
	set 0,d		;6bea	cb c2 	. .
	ld a,c			;6bec	79 	y
	ld (ix+003h),003h		;6bed	dd 36 03 03 	. 6 . .
	ei			;6bf1	fb 	.
	ret			;6bf2	c9 	.
l6bf3h:
	call emit_key		;6bf3	cd d8 6c 	. . l
	ld a,0c4h		;6bf6	3e c4 	> .
	ret			;6bf8	c9 	.
l6bf9h:
	set 0,e		;6bf9	cb c3 	. .
	ret			;6bfb	c9 	.
l6bfch:
	res 2,e		;6bfc	cb 93 	. .
	set 1,e		;6bfe	cb cb 	. .
	ret			;6c00	c9 	.
l6c01h:
	set 2,e		;6c01	cb d3 	. .
	set 1,e		;6c03	cb cb 	. .
	ret			;6c05	c9 	.
l6c06h:
	ld hl,078b0h		;6c06	21 b0 78 	! . x
	bit 6,(hl)		;6c09	cb 76 	. v
	jr z,l6c0fh		;6c0b	28 02 	( .
	set 6,d		;6c0d	cb f2 	. .
l6c0fh:
	ld (ix+003h),003h		;6c0f	dd 36 03 03 	. 6 . .
	ret			;6c13	c9 	.
l6c14h:
	ld c,a			;6c14	4f 	O
	ld a,(0785bh)		;6c15	3a 5b 78 	: [ x
	cp 000h		;6c18	fe 00 	. .
	jr z,l6c27h		;6c1a	28 0b 	( .
	ld hl,07916h		;6c1c	21 16 79 	! . y
	ld a,010h		;6c1f	3e 10 	> .
	xor e			;6c21	ab 	.
	ld e,a			;6c22	5f 	_
	ld a,008h		;6c23	3e 08 	> .
	xor (hl)			;6c25	ae 	.
	ld (hl),a			;6c26	77 	w
l6c27h:
	ld a,c			;6c27	79 	y
	ret			;6c28	c9 	.
l6c29h:
	ld a,01fh		;6c29	3e 1f 	> .
	set 6,d		;6c2b	cb f2 	. .
	res 2,d		;6c2d	cb 92 	. .
	res 1,d		;6c2f	cb 8a 	. .
	ret			;6c31	c9 	.
l6c32h:
	ld a,040h		;6c32	3e 40 	> @
	set 6,d		;6c34	cb f2 	. .
	set 1,d		;6c36	cb ca 	. .
	res 2,d		;6c38	cb 92 	. .
	ret			;6c3a	c9 	.
l6c3bh:
	ld a,03bh		;6c3b	3e 3b 	> ;
	set 6,d		;6c3d	cb f2 	. .
	set 2,d		;6c3f	cb d2 	. .
	ret			;6c41	c9 	.
alternate_translation:
	res 0,e		;6c42	cb 83 	. .
	bit 7,a		;6c44	cb 7f 	. 
	ret nz			;6c46	c0 	.
	ld hl,keyboard_end		;6c47	21 5d 6d 	! ] m
	ld c,(hl)			;6c4a	4e 	N
	ld b,000h		;6c4b	06 00 	. .
	inc hl			;6c4d	23 	#
	cpir		;6c4e	ed b1 	. .
	jr nz,l6c5fh		;6c50	20 0d 	  .
	ld c,a			;6c52	4f 	O
	ld a,(hl)			;6c53	7e 	~
	cp 0c2h		;6c54	fe c2 	. .
	ret nz			;6c56	c0 	.
	ld hl,0723fh		;6c57	21 3f 72 	! ? r
	bit 7,(hl)		;6c5a	cb 7e 	. ~
	ret nz			;6c5c	c0 	.
	ld a,c			;6c5d	79 	y
	ret			;6c5e	c9 	.
l6c5fh:
	ld hl,l6d7ch		;6c5f	21 7c 6d 	! | m
	ld bc,0000ah		;6c62	01 0a 00 	. . .
	cpdr		;6c65	ed b9 	. .
	ret nz			;6c67	c0 	.
	res 6,d		;6c68	cb b2 	. .
l6c6ah:
	ld a,062h		;6c6a	3e 62 	> b
	dec c			;6c6c	0d 	.
	ret m			;6c6d	f8 	.
	and 01fh		;6c6e	e6 1f 	. .
	call emit_key		;6c70	cd d8 6c 	. . l
	ret z			;6c73	c8 	.
	jr l6c6ah		;6c74	18 f4 	. .
sub_6c76h:
	res 1,e		;6c76	cb 8b 	. .
	ld hl,l6d7dh		;6c78	21 7d 6d 	! } m
	cp 0b3h		;6c7b	fe b3 	. .
	jr z,l6c84h		;6c7d	28 05 	( .
	inc hl			;6c7f	23 	#
	inc hl			;6c80	23 	#
	cp 0b4h		;6c81	fe b4 	. .
	ret nz			;6c83	c0 	.
l6c84h:
	bit 2,e		;6c84	cb 53 	. S
	res 2,e		;6c86	cb 93 	. .
	jr nz,l6c8bh		;6c88	20 01 	  .
	inc hl			;6c8a	23 	#
l6c8bh:
	ld a,(hl)			;6c8b	7e 	~
	res 6,d		;6c8c	cb b2 	. .
	ret			;6c8e	c9 	.
function_sequence:
	ld hl,sequences_external		;6c8f	21 f0 71 	! . q
	ld c,(hl)			;6c92	4e 	N
	ld b,000h		;6c93	06 00 	. .
	inc hl			;6c95	23 	#
	cpir		;6c96	ed b1 	. .
	ret nz			;6c98	c0 	.
	res 7,d		;6c99	cb ba 	. .
l6c9bh:
	ld a,(hl)			;6c9b	7e 	~
	bit 7,a		;6c9c	cb 7f 	. 
	ret nz			;6c9e	c0 	.
	push hl			;6c9f	e5 	.
	call emit_translated		;6ca0	cd a8 6c 	. . l
	pop hl			;6ca3	e1 	.
	ret z			;6ca4	c8 	.
	inc hl			;6ca5	23 	#
	jr l6c9bh		;6ca6	18 f3 	. .
emit_translated:
	push bc			;6ca8	c5 	.
	ld c,a			;6ca9	4f 	O
	bit 7,a		;6caa	cb 7f 	. 
	jr nz,l6cd2h		;6cac	20 24 	  $
	sub 060h		;6cae	d6 60 	. `
	jr nc,l6cd2h		;6cb0	30 20 	0
	ld a,(0723eh)		;6cb2	3a 3e 72 	: > r
	bit 5,c		;6cb5	cb 69 	. i
	jr nz,l6ccbh		;6cb7	20 12 	  .
	res 2,d		;6cb9	cb 92 	. .
	bit 6,c		;6cbb	cb 71 	. q
	jr nz,l6cd1h		;6cbd	20 12 	  .
	bit 0,a		;6cbf	cb 47 	. G
	jr nz,l6cd1h		;6cc1	20 0e 	  .
	bit 1,d		;6cc3	cb 4a 	. J
	jr z,l6cd1h		;6cc5	28 0a 	( .
	set 6,c		;6cc7	cb f1 	. .
	jr l6cd1h		;6cc9	18 06 	. .
l6ccbh:
	bit 2,a		;6ccb	cb 57 	. W
	jr nz,l6cd1h		;6ccd	20 02 	  .
	set 2,d		;6ccf	cb d2 	. .
l6cd1h:
	ld a,c			;6cd1	79 	y
l6cd2h:
	call emit_key		;6cd2	cd d8 6c 	. . l
	ld a,c			;6cd5	79 	y
	pop bc			;6cd6	c1 	.
	ret			;6cd7	c9 	.
emit_key:
	cp 0feh		;6cd8	fe fe 	. .
	jr z,l6ce3h		;6cda	28 07 	( .
	bit 3,e		;6cdc	cb 5b 	. [
	jr z,queue_put		;6cde	28 07 	( .
	cp 0e2h		;6ce0	fe e2 	. .
	ret z			;6ce2	c8 	.
l6ce3h:
	call l686ah		;6ce3	cd 6a 68 	. j h
	ret			;6ce6	c9 	.
queue_put:
	push hl			;6ce7	e5 	.
	ld hl,(queue_write_pointer)		;6ce8	2a b3 78 	* . x
	ld (hl),a			;6ceb	77 	w
	ld a,042h		;6cec	3e 42 	> B
	add a,040h		;6cee	c6 40 	. @
	inc hl			;6cf0	23 	#
	cp l			;6cf1	bd 	.
	jr nz,l6cf7h		;6cf2	20 03 	  .
	ld hl,queue_start		;6cf4	21 42 79 	! B y
l6cf7h:
	ld (queue_write_pointer),hl		;6cf7	22 b3 78 	" . x
	ld a,(queue_read_pointer)		;6cfa	3a b5 78 	: . x
	cp l			;6cfd	bd 	.
	jr nz,l6d09h		;6cfe	20 09 	  .
	set 3,e		;6d00	cb db 	. .
	set 3,d		;6d02	cb da 	. .
	ld hl,07918h		;6d04	21 18 79 	! . y
	set 4,(hl)		;6d07	cb e6 	. .
l6d09h:
	pop hl			;6d09	e1 	.
	ret			;6d0a	c9 	.
queue_get_or_repeat:
	ld hl,(queue_read_pointer)		;6d0b	2a b5 78 	* . x
	ld a,(queue_write_pointer)		;6d0e	3a b3 78 	: . x
	cp l			;6d11	bd 	.
	jr nz,l6d45h		;6d12	20 31 	  1
	bit 3,d		;6d14	cb 5a 	. Z
	res 3,d		;6d16	cb 9a 	. .
	jr nz,l6d45h		;6d18	20 2b 	  +
	bit 4,d		;6d1a	cb 62 	. b
	ret z			;6d1c	c8 	.
	bit 6,d		;6d1d	cb 72 	. r
	jr nz,l6d25h		;6d1f	20 04 	  .
	call l686ah		;6d21	cd 6a 68 	. j h
	ret			;6d24	c9 	.
l6d25h:
	ld hl,repeat_countdown		;6d25	21 a6 78 	! . x
	dec (hl)			;6d28	35 	5
	ret p			;6d29	f0 	.
	ld a,(repeat_key)		;6d2a	3a b7 78 	: . x
	cp 0f0h		;6d2d	fe f0 	. .
	jr c,l6d38h		;6d2f	38 07 	8 .
	ld (hl),006h		;6d31	36 06 	6 .
	call function_sequence		;6d33	cd 8f 6c 	. . l
	jr l6d42h		;6d36	18 0a 	. .
l6d38h:
	ld (hl),002h		;6d38	36 02 	6 .
	cp 0a0h		;6d3a	fe a0 	. .
	call nc,special_key		;6d3c	d4 84 6b 	. . k
	call emit_translated		;6d3f	cd a8 6c 	. . l
l6d42h:
	ld hl,(queue_read_pointer)		;6d42	2a b5 78 	* . x
l6d45h:
	ld a,(hl)			;6d45	7e 	~
	ld (output_key),a		;6d46	32 b2 78 	2 . x
	ld a,042h		;6d49	3e 42 	> B
	add a,040h		;6d4b	c6 40 	. @
	inc hl			;6d4d	23 	#
	cp l			;6d4e	bd 	.
	jr nz,l6d54h		;6d4f	20 03 	  .
	ld hl,queue_start		;6d51	21 42 79 	! B y
l6d54h:
	ld (queue_read_pointer),hl		;6d54	22 b5 78 	" . x
	ld hl,key_ready		;6d57	21 b1 78 	! . x
	set 0,(hl)		;6d5a	cb c6 	. .
	ret			;6d5c	c9 	.
keyboard_end:

; BLOCK 'translations' (start 0x6d5d end 0x6d81)
translations_start:
	defb 014h		;6d5d	14 	.
	defb 003h		;6d5e	03 	.
	defb 0afh		;6d5f	af 	.
	defb 019h		;6d60	19 	.
	defb 0b0h		;6d61	b0 	.
	defb 00eh		;6d62	0e 	.
	defb 0b1h		;6d63	b1 	.
	defb 009h		;6d64	09 	.
	defb 0c8h		;6d65	c8 	.
	defb 001h		;6d66	01 	.
	defb 0c9h		;6d67	c9 	.
	defb 00dh		;6d68	0d 	.
	defb 0cah		;6d69	ca 	.
	defb 01ah		;6d6a	1a 	.
	defb 0c2h		;6d6b	c2 	.
	defb 062h		;6d6c	62 	b
	defb 0c5h		;6d6d	c5 	.
	defb 01dh		;6d6e	1d 	.
	defb 0c6h		;6d6f	c6 	.
	defb 010h		;6d70	10 	.
	defb 0c7h		;6d71	c7 	.
	defb 0ffh		;6d72	ff 	.
	defb 037h		;6d73	37 	7
	defb 033h		;6d74	33 	3
	defb 021h		;6d75	21 	!
	defb 02ah		;6d76	2a 	*
	defb 030h		;6d77	30 	0
	defb 035h		;6d78	35 	5
	defb 027h		;6d79	27 	'
	defb 026h		;6d7a	26 	&
	defb 038h		;6d7b	38 	8
l6d7ch:
	defb 036h		;6d7c	36 	6
l6d7dh:
	defb 0b5h		;6d7d	b5 	.
	defb 0b7h		;6d7e	b7 	.
	defb 0b6h		;6d7f	b6 	.
	defb 0b8h		;6d80	b8 	.
translations_end:

; BLOCK 'wrappers' (start 0x6d81 end 0x6df9)
wrappers_start:
	cp 0b9h		;6d81	fe b9 	. .
	jp nz,04800h		;6d83	c2 00 48 	. . H
	rst 10h			;6d86	d7 	.
	ld a,(07802h)		;6d87	3a 02 78 	: . x
	cp 00ch		;6d8a	fe 0c 	. .
	jr nz,l6da1h		;6d8c	20 13 	  .
	ld hl,07253h		;6d8e	21 53 72 	! S r
	ld a,0ffh		;6d91	3e ff 	> .
	cp (hl)			;6d93	be 	.
	jr z,l6da1h		;6d94	28 0b 	( .
	ld a,(07804h)		;6d96	3a 04 78 	: . x
	cp (hl)			;6d99	be 	.
	jr nc,l6da1h		;6d9a	30 05 	0 .
	ld hl,0780eh		;6d9c	21 0e 78 	! . x
	set 7,(hl)		;6d9f	cb fe 	. .
l6da1h:
	rst 18h			;6da1	df 	.
	jp 04800h		;6da2	c3 00 48 	. . H
l6da5h:
	ld hl,07929h		;6da5	21 29 79 	! ) y
	res 7,(hl)		;6da8	cb be 	. .
	ld hl,07905h		;6daa	21 05 79 	! . y
	res 3,(hl)		;6dad	cb 9e 	. .
	ld hl,07914h		;6daf	21 14 79 	! . y
	res 3,(hl)		;6db2	cb 9e 	. .
	inc hl			;6db4	23 	#
	res 3,(hl)		;6db5	cb 9e 	. .
	jp 010c4h		;6db7	c3 c4 10 	. . .
	push af			;6dba	f5 	.
	ld a,(07907h)		;6dbb	3a 07 79 	: . y
	bit 7,a		;6dbe	cb 7f 	. 
	jr z,l6dc9h		;6dc0	28 07 	( .
	push hl			;6dc2	e5 	.
	ld hl,07914h		;6dc3	21 14 79 	! . y
	set 3,(hl)		;6dc6	cb de 	. .
	pop hl			;6dc8	e1 	.
l6dc9h:
	pop af			;6dc9	f1 	.
	jp 0116ah		;6dca	c3 6a 11 	. j .
	ld de,07896h		;6dcd	11 96 78 	. . x
	jp 0031ah		;6dd0	c3 1a 03 	. . .
l6dd3h:
	call 0031ah		;6dd3	cd 1a 03 	. . .
	di			;6dd6	f3 	.
	ld hl,07860h		;6dd7	21 60 78 	! ` x
	res 4,(hl)		;6dda	cb a6 	. .
	ld a,(hl)			;6ddc	7e 	~
	and 0fch		;6ddd	e6 fc 	. .
	cp 048h		;6ddf	fe 48 	. H
	jr nz,l6de5h		;6de1	20 02 	  .
	set 2,(hl)		;6de3	cb d6 	. .
l6de5h:
	ei			;6de5	fb 	.
	ret			;6de6	c9 	.
l6de7h:
	call 00800h		;6de7	cd 00 08 	. . .
	rst 10h			;6dea	d7 	.
	ld hl,07860h		;6deb	21 60 78 	! ` x
	ld a,(hl)			;6dee	7e 	~
	and 0fch		;6def	e6 fc 	. .
	cp 048h		;6df1	fe 48 	. H
	jr nz,l6df7h		;6df3	20 02 	  .
	set 2,(hl)		;6df5	cb d6 	. .
l6df7h:
	rst 18h			;6df7	df 	.
	ret			;6df8	c9 	.
wrappers_end:

; BLOCK 'padding' (start 0x6df9 end 0x6ffe)
padding_start:
	defb 0ffh		;6df9	ff 	.
	defb 0ffh		;6dfa	ff 	.
	defb 0ffh		;6dfb	ff 	.
	defb 0ffh		;6dfc	ff 	.
	defb 0ffh		;6dfd	ff 	.
	defb 0ffh		;6dfe	ff 	.
	defb 0ffh		;6dff	ff 	.
	defb 0ffh		;6e00	ff 	.
	defb 0ffh		;6e01	ff 	.
	defb 0ffh		;6e02	ff 	.
	defb 0ffh		;6e03	ff 	.
	defb 0ffh		;6e04	ff 	.
	defb 0ffh		;6e05	ff 	.
	defb 0ffh		;6e06	ff 	.
	defb 0ffh		;6e07	ff 	.
	defb 0ffh		;6e08	ff 	.
	defb 0ffh		;6e09	ff 	.
	defb 0ffh		;6e0a	ff 	.
	defb 0ffh		;6e0b	ff 	.
	defb 0ffh		;6e0c	ff 	.
	defb 0ffh		;6e0d	ff 	.
	defb 0ffh		;6e0e	ff 	.
	defb 0ffh		;6e0f	ff 	.
	defb 0ffh		;6e10	ff 	.
	defb 0ffh		;6e11	ff 	.
	defb 0ffh		;6e12	ff 	.
	defb 0ffh		;6e13	ff 	.
	defb 0ffh		;6e14	ff 	.
	defb 0ffh		;6e15	ff 	.
	defb 0ffh		;6e16	ff 	.
	defb 0ffh		;6e17	ff 	.
	defb 0ffh		;6e18	ff 	.
	defb 0ffh		;6e19	ff 	.
	defb 0ffh		;6e1a	ff 	.
	defb 0ffh		;6e1b	ff 	.
	defb 0ffh		;6e1c	ff 	.
	defb 0ffh		;6e1d	ff 	.
	defb 0ffh		;6e1e	ff 	.
	defb 0ffh		;6e1f	ff 	.
	defb 0ffh		;6e20	ff 	.
	defb 0ffh		;6e21	ff 	.
	defb 0ffh		;6e22	ff 	.
	defb 0ffh		;6e23	ff 	.
	defb 0ffh		;6e24	ff 	.
	defb 0ffh		;6e25	ff 	.
	defb 0ffh		;6e26	ff 	.
	defb 0ffh		;6e27	ff 	.
	defb 0ffh		;6e28	ff 	.
	defb 0ffh		;6e29	ff 	.
	defb 0ffh		;6e2a	ff 	.
	defb 0ffh		;6e2b	ff 	.
	defb 0ffh		;6e2c	ff 	.
	defb 0ffh		;6e2d	ff 	.
	defb 0ffh		;6e2e	ff 	.
	defb 0ffh		;6e2f	ff 	.
	defb 0ffh		;6e30	ff 	.
	defb 0ffh		;6e31	ff 	.
	defb 0ffh		;6e32	ff 	.
	defb 0ffh		;6e33	ff 	.
	defb 0ffh		;6e34	ff 	.
	defb 0ffh		;6e35	ff 	.
	defb 0ffh		;6e36	ff 	.
	defb 0ffh		;6e37	ff 	.
	defb 0ffh		;6e38	ff 	.
	defb 0ffh		;6e39	ff 	.
	defb 0ffh		;6e3a	ff 	.
	defb 0ffh		;6e3b	ff 	.
	defb 0ffh		;6e3c	ff 	.
	defb 0ffh		;6e3d	ff 	.
	defb 0ffh		;6e3e	ff 	.
	defb 0ffh		;6e3f	ff 	.
	defb 0ffh		;6e40	ff 	.
	defb 0ffh		;6e41	ff 	.
	defb 0ffh		;6e42	ff 	.
	defb 0ffh		;6e43	ff 	.
	defb 0ffh		;6e44	ff 	.
	defb 0ffh		;6e45	ff 	.
	defb 0ffh		;6e46	ff 	.
	defb 0ffh		;6e47	ff 	.
	defb 0ffh		;6e48	ff 	.
	defb 0ffh		;6e49	ff 	.
	defb 0ffh		;6e4a	ff 	.
	defb 0ffh		;6e4b	ff 	.
	defb 0ffh		;6e4c	ff 	.
	defb 0ffh		;6e4d	ff 	.
	defb 0ffh		;6e4e	ff 	.
	defb 0ffh		;6e4f	ff 	.
	defb 0ffh		;6e50	ff 	.
	defb 0ffh		;6e51	ff 	.
	defb 0ffh		;6e52	ff 	.
	defb 0ffh		;6e53	ff 	.
	defb 0ffh		;6e54	ff 	.
	defb 0ffh		;6e55	ff 	.
	defb 0ffh		;6e56	ff 	.
	defb 0ffh		;6e57	ff 	.
	defb 0ffh		;6e58	ff 	.
	defb 0ffh		;6e59	ff 	.
	defb 0ffh		;6e5a	ff 	.
	defb 0ffh		;6e5b	ff 	.
	defb 0ffh		;6e5c	ff 	.
	defb 0ffh		;6e5d	ff 	.
	defb 0ffh		;6e5e	ff 	.
	defb 0ffh		;6e5f	ff 	.
	defb 0ffh		;6e60	ff 	.
	defb 0ffh		;6e61	ff 	.
	defb 0ffh		;6e62	ff 	.
	defb 0ffh		;6e63	ff 	.
	defb 0ffh		;6e64	ff 	.
	defb 0ffh		;6e65	ff 	.
	defb 0ffh		;6e66	ff 	.
	defb 0ffh		;6e67	ff 	.
	defb 0ffh		;6e68	ff 	.
	defb 0ffh		;6e69	ff 	.
	defb 0ffh		;6e6a	ff 	.
	defb 0ffh		;6e6b	ff 	.
	defb 0ffh		;6e6c	ff 	.
	defb 0ffh		;6e6d	ff 	.
	defb 0ffh		;6e6e	ff 	.
	defb 0ffh		;6e6f	ff 	.
	defb 0ffh		;6e70	ff 	.
	defb 0ffh		;6e71	ff 	.
	defb 0ffh		;6e72	ff 	.
	defb 0ffh		;6e73	ff 	.
	defb 0ffh		;6e74	ff 	.
	defb 0ffh		;6e75	ff 	.
	defb 0ffh		;6e76	ff 	.
	defb 0ffh		;6e77	ff 	.
	defb 0ffh		;6e78	ff 	.
	defb 0ffh		;6e79	ff 	.
	defb 0ffh		;6e7a	ff 	.
	defb 0ffh		;6e7b	ff 	.
	defb 0ffh		;6e7c	ff 	.
	defb 0ffh		;6e7d	ff 	.
	defb 0ffh		;6e7e	ff 	.
	defb 0ffh		;6e7f	ff 	.
	defb 0ffh		;6e80	ff 	.
	defb 0ffh		;6e81	ff 	.
	defb 0ffh		;6e82	ff 	.
	defb 0ffh		;6e83	ff 	.
	defb 0ffh		;6e84	ff 	.
	defb 0ffh		;6e85	ff 	.
	defb 0ffh		;6e86	ff 	.
	defb 0ffh		;6e87	ff 	.
	defb 0ffh		;6e88	ff 	.
	defb 0ffh		;6e89	ff 	.
	defb 0ffh		;6e8a	ff 	.
	defb 0ffh		;6e8b	ff 	.
	defb 0ffh		;6e8c	ff 	.
	defb 0ffh		;6e8d	ff 	.
	defb 0ffh		;6e8e	ff 	.
	defb 0ffh		;6e8f	ff 	.
	defb 0ffh		;6e90	ff 	.
	defb 0ffh		;6e91	ff 	.
	defb 0ffh		;6e92	ff 	.
	defb 0ffh		;6e93	ff 	.
	defb 0ffh		;6e94	ff 	.
	defb 0ffh		;6e95	ff 	.
	defb 0ffh		;6e96	ff 	.
	defb 0ffh		;6e97	ff 	.
	defb 0ffh		;6e98	ff 	.
	defb 0ffh		;6e99	ff 	.
	defb 0ffh		;6e9a	ff 	.
	defb 0ffh		;6e9b	ff 	.
	defb 0ffh		;6e9c	ff 	.
	defb 0ffh		;6e9d	ff 	.
	defb 0ffh		;6e9e	ff 	.
	defb 0ffh		;6e9f	ff 	.
	defb 0ffh		;6ea0	ff 	.
	defb 0ffh		;6ea1	ff 	.
	defb 0ffh		;6ea2	ff 	.
	defb 0ffh		;6ea3	ff 	.
	defb 0ffh		;6ea4	ff 	.
	defb 0ffh		;6ea5	ff 	.
	defb 0ffh		;6ea6	ff 	.
	defb 0ffh		;6ea7	ff 	.
	defb 0ffh		;6ea8	ff 	.
	defb 0ffh		;6ea9	ff 	.
	defb 0ffh		;6eaa	ff 	.
	defb 0ffh		;6eab	ff 	.
	defb 0ffh		;6eac	ff 	.
	defb 0ffh		;6ead	ff 	.
	defb 0ffh		;6eae	ff 	.
	defb 0ffh		;6eaf	ff 	.
	defb 0ffh		;6eb0	ff 	.
	defb 0ffh		;6eb1	ff 	.
	defb 0ffh		;6eb2	ff 	.
	defb 0ffh		;6eb3	ff 	.
	defb 0ffh		;6eb4	ff 	.
	defb 0ffh		;6eb5	ff 	.
	defb 0ffh		;6eb6	ff 	.
	defb 0ffh		;6eb7	ff 	.
	defb 0ffh		;6eb8	ff 	.
	defb 0ffh		;6eb9	ff 	.
	defb 0ffh		;6eba	ff 	.
	defb 0ffh		;6ebb	ff 	.
	defb 0ffh		;6ebc	ff 	.
	defb 0ffh		;6ebd	ff 	.
	defb 0ffh		;6ebe	ff 	.
	defb 0ffh		;6ebf	ff 	.
	defb 0ffh		;6ec0	ff 	.
	defb 0ffh		;6ec1	ff 	.
	defb 0ffh		;6ec2	ff 	.
	defb 0ffh		;6ec3	ff 	.
	defb 0ffh		;6ec4	ff 	.
	defb 0ffh		;6ec5	ff 	.
	defb 0ffh		;6ec6	ff 	.
	defb 0ffh		;6ec7	ff 	.
	defb 0ffh		;6ec8	ff 	.
	defb 0ffh		;6ec9	ff 	.
	defb 0ffh		;6eca	ff 	.
	defb 0ffh		;6ecb	ff 	.
	defb 0ffh		;6ecc	ff 	.
	defb 0ffh		;6ecd	ff 	.
	defb 0ffh		;6ece	ff 	.
	defb 0ffh		;6ecf	ff 	.
	defb 0ffh		;6ed0	ff 	.
	defb 0ffh		;6ed1	ff 	.
	defb 0ffh		;6ed2	ff 	.
	defb 0ffh		;6ed3	ff 	.
	defb 0ffh		;6ed4	ff 	.
	defb 0ffh		;6ed5	ff 	.
	defb 0ffh		;6ed6	ff 	.
	defb 0ffh		;6ed7	ff 	.
	defb 0ffh		;6ed8	ff 	.
	defb 0ffh		;6ed9	ff 	.
	defb 0ffh		;6eda	ff 	.
	defb 0ffh		;6edb	ff 	.
	defb 0ffh		;6edc	ff 	.
	defb 0ffh		;6edd	ff 	.
	defb 0ffh		;6ede	ff 	.
	defb 0ffh		;6edf	ff 	.
	defb 0ffh		;6ee0	ff 	.
	defb 0ffh		;6ee1	ff 	.
	defb 0ffh		;6ee2	ff 	.
	defb 0ffh		;6ee3	ff 	.
	defb 0ffh		;6ee4	ff 	.
	defb 0ffh		;6ee5	ff 	.
	defb 0ffh		;6ee6	ff 	.
	defb 0ffh		;6ee7	ff 	.
	defb 0ffh		;6ee8	ff 	.
	defb 0ffh		;6ee9	ff 	.
	defb 0ffh		;6eea	ff 	.
	defb 0ffh		;6eeb	ff 	.
	defb 0ffh		;6eec	ff 	.
	defb 0ffh		;6eed	ff 	.
	defb 0ffh		;6eee	ff 	.
	defb 0ffh		;6eef	ff 	.
	defb 0ffh		;6ef0	ff 	.
	defb 0ffh		;6ef1	ff 	.
	defb 0ffh		;6ef2	ff 	.
	defb 0ffh		;6ef3	ff 	.
	defb 0ffh		;6ef4	ff 	.
	defb 0ffh		;6ef5	ff 	.
	defb 0ffh		;6ef6	ff 	.
	defb 0ffh		;6ef7	ff 	.
	defb 0ffh		;6ef8	ff 	.
	defb 0ffh		;6ef9	ff 	.
	defb 0ffh		;6efa	ff 	.
	defb 0ffh		;6efb	ff 	.
	defb 0ffh		;6efc	ff 	.
	defb 0ffh		;6efd	ff 	.
	defb 0ffh		;6efe	ff 	.
	defb 0ffh		;6eff	ff 	.
	defb 0ffh		;6f00	ff 	.
	defb 0ffh		;6f01	ff 	.
	defb 0ffh		;6f02	ff 	.
	defb 0ffh		;6f03	ff 	.
	defb 0ffh		;6f04	ff 	.
	defb 0ffh		;6f05	ff 	.
	defb 0ffh		;6f06	ff 	.
	defb 0ffh		;6f07	ff 	.
	defb 0ffh		;6f08	ff 	.
	defb 0ffh		;6f09	ff 	.
	defb 0ffh		;6f0a	ff 	.
	defb 0ffh		;6f0b	ff 	.
	defb 0ffh		;6f0c	ff 	.
	defb 0ffh		;6f0d	ff 	.
	defb 0ffh		;6f0e	ff 	.
	defb 0ffh		;6f0f	ff 	.
	defb 0ffh		;6f10	ff 	.
	defb 0ffh		;6f11	ff 	.
	defb 0ffh		;6f12	ff 	.
	defb 0ffh		;6f13	ff 	.
	defb 0ffh		;6f14	ff 	.
	defb 0ffh		;6f15	ff 	.
	defb 0ffh		;6f16	ff 	.
	defb 0ffh		;6f17	ff 	.
	defb 0ffh		;6f18	ff 	.
	defb 0ffh		;6f19	ff 	.
	defb 0ffh		;6f1a	ff 	.
	defb 0ffh		;6f1b	ff 	.
	defb 0ffh		;6f1c	ff 	.
	defb 0ffh		;6f1d	ff 	.
	defb 0ffh		;6f1e	ff 	.
	defb 0ffh		;6f1f	ff 	.
	defb 0ffh		;6f20	ff 	.
	defb 0ffh		;6f21	ff 	.
	defb 0ffh		;6f22	ff 	.
	defb 0ffh		;6f23	ff 	.
	defb 0ffh		;6f24	ff 	.
	defb 0ffh		;6f25	ff 	.
	defb 0ffh		;6f26	ff 	.
	defb 0ffh		;6f27	ff 	.
	defb 0ffh		;6f28	ff 	.
	defb 0ffh		;6f29	ff 	.
	defb 0ffh		;6f2a	ff 	.
	defb 0ffh		;6f2b	ff 	.
	defb 0ffh		;6f2c	ff 	.
	defb 0ffh		;6f2d	ff 	.
	defb 0ffh		;6f2e	ff 	.
	defb 0ffh		;6f2f	ff 	.
	defb 0ffh		;6f30	ff 	.
	defb 0ffh		;6f31	ff 	.
	defb 0ffh		;6f32	ff 	.
	defb 0ffh		;6f33	ff 	.
	defb 0ffh		;6f34	ff 	.
	defb 0ffh		;6f35	ff 	.
	defb 0ffh		;6f36	ff 	.
	defb 0ffh		;6f37	ff 	.
	defb 0ffh		;6f38	ff 	.
	defb 0ffh		;6f39	ff 	.
	defb 0ffh		;6f3a	ff 	.
	defb 0ffh		;6f3b	ff 	.
	defb 0ffh		;6f3c	ff 	.
	defb 0ffh		;6f3d	ff 	.
	defb 0ffh		;6f3e	ff 	.
	defb 0ffh		;6f3f	ff 	.
	defb 0ffh		;6f40	ff 	.
	defb 0ffh		;6f41	ff 	.
	defb 0ffh		;6f42	ff 	.
	defb 0ffh		;6f43	ff 	.
	defb 0ffh		;6f44	ff 	.
	defb 0ffh		;6f45	ff 	.
	defb 0ffh		;6f46	ff 	.
	defb 0ffh		;6f47	ff 	.
	defb 0ffh		;6f48	ff 	.
	defb 0ffh		;6f49	ff 	.
	defb 0ffh		;6f4a	ff 	.
	defb 0ffh		;6f4b	ff 	.
	defb 0ffh		;6f4c	ff 	.
	defb 0ffh		;6f4d	ff 	.
	defb 0ffh		;6f4e	ff 	.
	defb 0ffh		;6f4f	ff 	.
	defb 0ffh		;6f50	ff 	.
	defb 0ffh		;6f51	ff 	.
	defb 0ffh		;6f52	ff 	.
	defb 0ffh		;6f53	ff 	.
	defb 0ffh		;6f54	ff 	.
	defb 0ffh		;6f55	ff 	.
	defb 0ffh		;6f56	ff 	.
	defb 0ffh		;6f57	ff 	.
	defb 0ffh		;6f58	ff 	.
	defb 0ffh		;6f59	ff 	.
	defb 0ffh		;6f5a	ff 	.
	defb 0ffh		;6f5b	ff 	.
	defb 0ffh		;6f5c	ff 	.
	defb 0ffh		;6f5d	ff 	.
	defb 0ffh		;6f5e	ff 	.
	defb 0ffh		;6f5f	ff 	.
	defb 0ffh		;6f60	ff 	.
	defb 0ffh		;6f61	ff 	.
	defb 0ffh		;6f62	ff 	.
	defb 0ffh		;6f63	ff 	.
	defb 0ffh		;6f64	ff 	.
	defb 0ffh		;6f65	ff 	.
	defb 0ffh		;6f66	ff 	.
	defb 0ffh		;6f67	ff 	.
	defb 0ffh		;6f68	ff 	.
	defb 0ffh		;6f69	ff 	.
	defb 0ffh		;6f6a	ff 	.
	defb 0ffh		;6f6b	ff 	.
	defb 0ffh		;6f6c	ff 	.
	defb 0ffh		;6f6d	ff 	.
	defb 0ffh		;6f6e	ff 	.
	defb 0ffh		;6f6f	ff 	.
	defb 0ffh		;6f70	ff 	.
	defb 0ffh		;6f71	ff 	.
	defb 0ffh		;6f72	ff 	.
	defb 0ffh		;6f73	ff 	.
	defb 0ffh		;6f74	ff 	.
	defb 0ffh		;6f75	ff 	.
	defb 0ffh		;6f76	ff 	.
	defb 0ffh		;6f77	ff 	.
	defb 0ffh		;6f78	ff 	.
	defb 0ffh		;6f79	ff 	.
	defb 0ffh		;6f7a	ff 	.
	defb 0ffh		;6f7b	ff 	.
	defb 0ffh		;6f7c	ff 	.
	defb 0ffh		;6f7d	ff 	.
	defb 0ffh		;6f7e	ff 	.
	defb 0ffh		;6f7f	ff 	.
	defb 0ffh		;6f80	ff 	.
	defb 0ffh		;6f81	ff 	.
	defb 0ffh		;6f82	ff 	.
	defb 0ffh		;6f83	ff 	.
	defb 0ffh		;6f84	ff 	.
	defb 0ffh		;6f85	ff 	.
	defb 0ffh		;6f86	ff 	.
	defb 0ffh		;6f87	ff 	.
	defb 0ffh		;6f88	ff 	.
	defb 0ffh		;6f89	ff 	.
	defb 0ffh		;6f8a	ff 	.
	defb 0ffh		;6f8b	ff 	.
	defb 0ffh		;6f8c	ff 	.
	defb 0ffh		;6f8d	ff 	.
	defb 0ffh		;6f8e	ff 	.
	defb 0ffh		;6f8f	ff 	.
	defb 0ffh		;6f90	ff 	.
	defb 0ffh		;6f91	ff 	.
	defb 0ffh		;6f92	ff 	.
	defb 0ffh		;6f93	ff 	.
	defb 0ffh		;6f94	ff 	.
	defb 0ffh		;6f95	ff 	.
	defb 0ffh		;6f96	ff 	.
	defb 0ffh		;6f97	ff 	.
	defb 0ffh		;6f98	ff 	.
	defb 0ffh		;6f99	ff 	.
	defb 0ffh		;6f9a	ff 	.
	defb 0ffh		;6f9b	ff 	.
	defb 0ffh		;6f9c	ff 	.
	defb 0ffh		;6f9d	ff 	.
	defb 0ffh		;6f9e	ff 	.
	defb 0ffh		;6f9f	ff 	.
	defb 0ffh		;6fa0	ff 	.
	defb 0ffh		;6fa1	ff 	.
	defb 0ffh		;6fa2	ff 	.
	defb 0ffh		;6fa3	ff 	.
	defb 0ffh		;6fa4	ff 	.
	defb 0ffh		;6fa5	ff 	.
	defb 0ffh		;6fa6	ff 	.
	defb 0ffh		;6fa7	ff 	.
	defb 0ffh		;6fa8	ff 	.
	defb 0ffh		;6fa9	ff 	.
	defb 0ffh		;6faa	ff 	.
	defb 0ffh		;6fab	ff 	.
	defb 0ffh		;6fac	ff 	.
	defb 0ffh		;6fad	ff 	.
	defb 0ffh		;6fae	ff 	.
	defb 0ffh		;6faf	ff 	.
	defb 0ffh		;6fb0	ff 	.
	defb 0ffh		;6fb1	ff 	.
	defb 0ffh		;6fb2	ff 	.
	defb 0ffh		;6fb3	ff 	.
	defb 0ffh		;6fb4	ff 	.
	defb 0ffh		;6fb5	ff 	.
	defb 0ffh		;6fb6	ff 	.
	defb 0ffh		;6fb7	ff 	.
	defb 0ffh		;6fb8	ff 	.
	defb 0ffh		;6fb9	ff 	.
	defb 0ffh		;6fba	ff 	.
	defb 0ffh		;6fbb	ff 	.
	defb 0ffh		;6fbc	ff 	.
	defb 0ffh		;6fbd	ff 	.
	defb 0ffh		;6fbe	ff 	.
	defb 0ffh		;6fbf	ff 	.
	defb 0ffh		;6fc0	ff 	.
	defb 0ffh		;6fc1	ff 	.
	defb 0ffh		;6fc2	ff 	.
	defb 0ffh		;6fc3	ff 	.
	defb 0ffh		;6fc4	ff 	.
	defb 0ffh		;6fc5	ff 	.
	defb 0ffh		;6fc6	ff 	.
	defb 0ffh		;6fc7	ff 	.
	defb 0ffh		;6fc8	ff 	.
	defb 0ffh		;6fc9	ff 	.
	defb 0ffh		;6fca	ff 	.
	defb 0ffh		;6fcb	ff 	.
	defb 0ffh		;6fcc	ff 	.
	defb 0ffh		;6fcd	ff 	.
	defb 0ffh		;6fce	ff 	.
	defb 0ffh		;6fcf	ff 	.
	defb 0ffh		;6fd0	ff 	.
	defb 0ffh		;6fd1	ff 	.
	defb 0ffh		;6fd2	ff 	.
	defb 0ffh		;6fd3	ff 	.
	defb 0ffh		;6fd4	ff 	.
	defb 0ffh		;6fd5	ff 	.
	defb 0ffh		;6fd6	ff 	.
	defb 0ffh		;6fd7	ff 	.
	defb 0ffh		;6fd8	ff 	.
	defb 0ffh		;6fd9	ff 	.
	defb 0ffh		;6fda	ff 	.
	defb 0ffh		;6fdb	ff 	.
	defb 0ffh		;6fdc	ff 	.
	defb 0ffh		;6fdd	ff 	.
	defb 0ffh		;6fde	ff 	.
	defb 0ffh		;6fdf	ff 	.
	defb 0ffh		;6fe0	ff 	.
	defb 0ffh		;6fe1	ff 	.
	defb 0ffh		;6fe2	ff 	.
	defb 0ffh		;6fe3	ff 	.
	defb 0ffh		;6fe4	ff 	.
	defb 0ffh		;6fe5	ff 	.
	defb 0ffh		;6fe6	ff 	.
	defb 0ffh		;6fe7	ff 	.
	defb 0ffh		;6fe8	ff 	.
	defb 0ffh		;6fe9	ff 	.
	defb 0ffh		;6fea	ff 	.
	defb 0ffh		;6feb	ff 	.
	defb 0ffh		;6fec	ff 	.
	defb 0ffh		;6fed	ff 	.
	defb 0ffh		;6fee	ff 	.
	defb 0ffh		;6fef	ff 	.
	defb 0ffh		;6ff0	ff 	.
	defb 0ffh		;6ff1	ff 	.
	defb 0ffh		;6ff2	ff 	.
	defb 0ffh		;6ff3	ff 	.
	defb 0ffh		;6ff4	ff 	.
	defb 0ffh		;6ff5	ff 	.
	defb 0ffh		;6ff6	ff 	.
	defb 0ffh		;6ff7	ff 	.
	defb 0ffh		;6ff8	ff 	.
	defb 0ffh		;6ff9	ff 	.
	defb 0ffh		;6ffa	ff 	.
	defb 0ffh		;6ffb	ff 	.
	defb 0ffh		;6ffc	ff 	.
	defb 0ffh		;6ffd	ff 	.
padding_end:

; BLOCK 'unidentified_trailer' (start 0x6ffe end 0x7000)
unidentified_trailer_start:
	defw 03df6h		;6ffe	f6 3d 	. =
unidentified_trailer_end:
