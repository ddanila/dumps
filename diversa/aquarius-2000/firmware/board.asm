; Driver entry points and register contracts are described in README.md.
column: equ 800bh
irq_live: equ 8011h
board_init:
	xor a
	out (50h),a
	ld a,76h
	out (54h),a
	ld a,33h
	out (51h),a
	ld a,0dfh
	out (55h),a
	ld a,0fh
	out (34h),a
	ld a,0ffh
	out (44h),a
	ld a,5
	out (30h),a
	xor a
	out (56h),a
	ret

delay:
	dec bc
	ld a,b
	or c
	jr nz,delay
	ret
lcd_init:
	ld bc,4096
	call delay
	ld a,38h
	call lcd_command
	ld bc,1024
	call delay
	ld a,1
	call lcd_command
	ld bc,2560
	call delay
	ld a,0ch
	call lcd_command
	ld bc,1024
	call delay
	ld a,6
	jp lcd_command

; Foreground only. irq_live is zero until boot installs the IM2 table.
lcd_command:
	push bc
	ld b,0
	jr lcd_write
lcd_data:
	push bc
	ld b,1
lcd_write:
	out (40h),a
	di
	in a,(51h)
	and 0f8h
	or b
	out (51h),a
	or 4
	out (51h),a
	nop
	and 0fbh
	out (51h),a
	bit 0,b
	jr nz,lcd_count
	or 1
	out (51h),a
	xor a
	ld (column),a
	jr lcd_restore
lcd_count:
	ld a,(column)
	inc a
	ld (column),a
lcd_restore:
	ld a,(irq_live)
	or a
	jr z,lcd_wait
	ei
lcd_wait:
	ld a,12
lcd_settle:
	dec a
	jr nz,lcd_settle
	pop bc
	ret

; Called in foreground with interrupts enabled. Always ends with bit 3 low.
chirp:
	push af
	ld b,96
chirp_edge:
	di
	in a,(51h)
	xor 8
	out (51h),a
	ei
	ld c,150
chirp_delay:
	dec c
	jr nz,chirp_delay
	djnz chirp_edge
	di
	in a,(51h)
	and 0f7h
	out (51h),a
	ei
	pop af
	ret

; A new request alternates selector 1/2. Factory 211Eh/2197h use
; external CTC channel 0 interrupts to sample the other three counters.
channel:    equ 800ch
remaining:  equ 800dh
capture1:   equ 800eh
capture2:   equ 800fh
capture3:   equ 8010h
capture:
	di
	ld a,3
	out (10h),a
	ld a,8
	out (10h),a
	ld a,0c7h
	out (10h),a
	ld a,80h
	out (10h),a
	ld a,47h
	out (11h),a
	out (12h),a
	out (13h),a
	xor a
	out (11h),a
	out (12h),a
	out (13h),a
	ld a,(channel)
	cp 1
	ld a,1
	jr nz,gate
	inc a
gate:
	ld (channel),a
	out (30h),a
	or 8
	out (30h),a
	ld a,169
	ld (remaining),a
	ei
	ld d,128
capture_wait:
	ld bc,256
	call delay
	ld a,(remaining)
	or a
	jr z,capture_end
	in a,(51h)
	xor 10h
	out (51h),a
	dec d
	jr nz,capture_wait
capture_end:
	di
	ld a,3
	out (10h),a
	ld a,5
	out (30h),a
	call tick_start
	ei
	ret
capture_isr:
	push af
	ld a,(remaining)
	or a
	jr z,capture_exit
	in a,(11h)
	ld (capture1),a
	in a,(12h)
	ld (capture2),a
	in a,(13h)
	ld (capture3),a
	ld a,(remaining)
	dec a
	ld (remaining),a
capture_exit:
	pop af
	ei
	reti
tick_start:
	ld a,10h
	out (10h),a
	ld a,87h
	out (10h),a
	ld a,0fah
	out (10h),a
	ret

edge5: equ 8013h
edge6: equ 8014h
edge7: equ 8015h
subsecond: equ 8016h
seconds: equ 8018h
tick_isr:
	push af
	push hl
	push bc
	in a,(51h)
	xor 10h
	out (51h),a
	ld hl,(ticks)
	inc hl
	ld (ticks),hl
	ld hl,(subsecond)
	inc hl
	ld a,h
	cp 3
	jr nz,store_subsecond
	ld a,l
	cp 0e8h
	jr nz,store_subsecond
	ld hl,(seconds)
	inc hl
	ld (seconds),hl
	ld hl,0
store_subsecond:
	ld (subsecond),hl
	in a,(30h)
	and 0f0h
	ld b,a
	ld hl,last_pin
	xor (hl)
	and (hl)              ; old high, new low
	ld (hl),b
	ld hl,edges
	bit 4,a
	jr z,test5
	inc (hl)
test5:
	ld hl,edge5
	bit 5,a
	jr z,test6
	inc (hl)
test6:
	inc hl
	bit 6,a
	jr z,test7
	inc (hl)
test7:
	inc hl
	bit 7,a
	jr z,tick_done
	inc (hl)
tick_done:
	pop bc
	pop hl
	pop af
	ei
	reti

; Read word A (0..63) using the factory 302Eh framing. Preserve PA1/PA2.
; Bounded ready wait, always deselect, no write-enable or program commands.
nv_word:
	and 3fh
	or 80h
	ld c,a
	in a,(50h)
	and 06h
	ld d,a
	ld b,0
nv_ready:
	ld a,10h
	or d
	out (50h),a
	in a,(50h)
	bit 7,a
	jr nz,nv_command
	djnz nv_ready
	xor a
	or d
	out (50h),a
	scf
	ret
nv_command:
	ld b,9                 ; leading start bit plus eight command bits
	ld a,50h
nv_send:
	or d
	out (50h),a
	or 20h
	out (50h),a
	ld a,10h
	sla c
	jr nc,nv_next
	or 40h
nv_next:
	djnz nv_send
	ld b,16
	ld hl,0
nv_read:
	ld a,10h
	or d
	out (50h),a
	or 20h
	out (50h),a
	in a,(50h)
	rlca
	adc hl,hl
	djnz nv_read
	xor a
	or d
	out (50h),a
	ret

; One factory-style MSB-first byte. Hold data while strobe is active.
; Status 01 = acknowledged, FF = timeout. Active diagnostic on chord 21h.
link_status: equ 8012h
link_probe:
	ld e,55h
	ld d,8
link_bit:
	ld b,0
link_wait_low:
	in a,(50h)
	bit 0,a
	jr z,link_present
	djnz link_wait_low
	jr link_timeout
link_present:
	di
	in a,(51h)
	and 3fh
	sla e
	jr nc,link_strobe
	or 80h
link_strobe:
	or 40h
	out (51h),a
	ei
	ld b,0
link_wait_high:
	in a,(50h)
	bit 0,a
	jr nz,link_ack
	djnz link_wait_high
	jr link_timeout
link_ack:
	di
	in a,(51h)
	and 0bfh
	out (51h),a
	ei
	dec d
	jr nz,link_bit
	ld c,1
	jr link_idle
link_timeout:
	ld c,0ffh
link_idle:
	di
	in a,(51h)
	and 3fh
	out (51h),a
	ei
	ld a,c
	ld (link_status),a
	ret
