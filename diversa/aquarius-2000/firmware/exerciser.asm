; Aquarius 2000 diagnostic EPROM. RAM below the factory stack top is scratch.
ticks:      equ 8000h
edges:      equ 8002h
last_pin:   equ 8004h
stable:     equ 8005h
candidate:  equ 8006h
page:       equ 8007h
previous:   equ 8008h
samples:    equ 8009h
refresh:    equ 800ah
nv_addr:    equ 801ah
	org 0
	di
	jp boot
	defs 38h-$,0
	reti
	defs 66h-$,0
	retn
	defs 108h-$,0
	dw capture_isr
	defs 110h-$,0
	dw tick_isr
boot:
	ld sp,8100h
	ld hl,ticks
	ld de,ticks+1
	ld bc,nv_addr-ticks
	ld (hl),0
	ldir
	ld a,3fh
	ld (nv_addr),a
	call board_init
	in a,(30h)
	and 0f0h
	ld (last_pin),a
	call lcd_init
	ld a,80h
	call lcd_command
	ld hl,title
	call lcd_text
	ld a,1
	ld i,a
	im 2
	call tick_start
	ld a,1
	ld (irq_live),a
	ei
	call render
poll:
	ld bc,512
	call delay
	in a,(52h)
	cpl
	ld b,a
	ld a,(candidate)
	cp b
	jr z,unchanged
	ld a,b
	ld (candidate),a
	xor a
	ld (samples),a
	jp poll
unchanged:
	ld a,(samples)
	cp 2
	jr nc,settled
	inc a
	ld (samples),a
	jp poll
settled:
	ld a,(stable)
	cp b
	jr z,periodic
	ld (previous),a
	cpl
	and b
	ld c,a                ; new presses, independent of held keys
	ld a,b
	ld (stable),a
	ld a,c
	or a
	jr z,redraw
	ld a,b
	cp 12h
	jr z,canyon_key
	cp 90h
	jr z,suspense_key
	cp 21h
	jr nz,single
	ld a,5
	ld (page),a
	call link_probe
	ld hl,chord_name
	call show_key
	jr redraw
canyon_key:
	call play_canyon
	jr music_return
suspense_key:
	call play_suspense
music_return:
	ld a,4
	ld (page),a
	jp redraw
single:
	ld a,c
	ld b,0
select_page:
	rrca
	jr c,selected
	inc b
	jr select_page
selected:
	ld a,b
	ld (page),a
	push af
	add a,a
	ld e,a
	ld d,0
	ld hl,key_names
	add hl,de
	ld e,(hl)
	inc hl
	ld d,(hl)
	ex de,hl
	call show_key
	pop af
	cp 4
	call z,chirp
	cp 6
	jr nz,try_capture
	ld a,(nv_addr)
	inc a
	and 3fh
	ld (nv_addr),a
	jr redraw
try_capture:
	cp 2
	call z,capture
redraw:
	call render
	jp poll
periodic:
	ld hl,refresh
	inc (hl)
	ld a,(hl)
	and 0fh
	jr z,redraw
	jp poll

; Fixed second-row layout: raw pressed mask, followed by the selected reading.
render:
	ld a,0c0h
	call lcd_command
	ld a,(stable)
	call hex_byte
	ld a,' '
	call lcd_data
	ld a,(page)
	add a,a
	ld e,a
	ld d,0
	ld hl,pages
	add hl,de
	ld e,(hl)
	inc hl
	ld d,(hl)
	ex de,hl
	jp (hl)
show_key:
	ld a,80h
	call lcd_command
	call lcd_text
	jp pad
key_names:
	dw reset_name,plus_name,right_name,norm_name,select_name,setup_name,left_name,minus_name
reset_name: db 'KEY RESET',0
plus_name: db 'KEY +',0
right_name: db 'KEY RIGHT',0
norm_name: db 'KEY NORM',0
select_name: db 'KEY SELECT',0
setup_name: db 'KEY SETUP',0
left_name: db 'KEY LEFT',0
minus_name: db 'KEY -',0
chord_name: db 'SETUP + RESET',0
pages:
	dw keys_view,pulse_view,counter_view,timer_view,sound_view,pins_view,nv_view,ram_view
keys_view:
	ld hl,key_label
	call lcd_text
	ld a,(previous)
	call hex_byte
	jp pad
pulse_view:
	ld hl,pulse_label
	call lcd_text
	ld a,(edges)
	call hex_byte
	ld a,(edge5)
	call hex_byte
	ld a,(edge6)
	call hex_byte
	ld a,(edge7)
	call hex_byte
	jp pad
timer_view:
	ld hl,tick_label
	call lcd_text
	ld hl,(ticks)
	ld a,h
	call hex_byte
	ld a,l
	call hex_byte
	ld a,'/'
	call lcd_data
	ld hl,(seconds)
word_view:
	ld a,h
	call hex_byte
	ld a,l
	call hex_byte
	jp pad
counter_view:
	ld hl,counter_label
	call lcd_text
	ld a,(channel)
	call nibble
	ld a,32
	call lcd_data
	ld a,(remaining)
	or a
	ld hl,timeout_label
	jr nz,message
	ld a,(capture1)
	call hex_byte
	ld a,(capture2)
	call hex_byte
	ld a,(capture3)
	call hex_byte
	jp pad
pins_view:
	ld hl,pins_label
	call lcd_text
	in a,(30h)
	call hex_byte
	in a,(50h)
	call hex_byte
	in a,(51h)
	call hex_byte
	ld a,32
	call lcd_data
	ld a,(link_status)
	call hex_byte
	jp pad
sound_view:
	ld hl,sound_label
	jr message
nv_view:
	ld hl,nv_label
	call lcd_text
	ld a,(nv_addr)
	call hex_byte
	ld a,32
	call lcd_data
	ld a,(nv_addr)
	call nv_word
	jr nc,word_view
	ld hl,timeout_label
	jr message
ram_view:
	ld hl,8070h
	ld c,(hl)
	ld (hl),55h
	ld a,(hl)
	cp 55h
	jr nz,ram_done
	ld (hl),0aah
	ld a,(hl)
	cp 0aah
ram_done:
	ld (hl),c
	ld hl,ram_bad
	jr nz,message
	ld hl,ram_ok
message:
	call lcd_text
pad:
	; Clear through column 20 using the tracked character count.
	ld a,(column)
	cp 20
	ret nc
	ld a,' '
	call lcd_data
	jp pad

hex_byte:
	push af
	rrca
	rrca
	rrca
	rrca
	call nibble
	pop af
nibble:
	and 15
	add a,'0'
	cp '9'+1
	jr c,emit
	add a,7
emit:
	jp lcd_data
lcd_text:
	ld a,(hl)
	or a
	ret z
	call lcd_data
	inc hl
	jr lcd_text

title: db 'AQ2000 BOARD TEST',0
key_label: db 'KEY PREV ',0
pulse_label: db 'EDGES ',0
counter_label: db 'CTC ',0
tick_label: db 'TICKS ',0
sound_label: db 'SEL SOUND +/-MUS',0
pins_label: db 'PINS ',0
nv_label: db 'NV',0
timeout_label: db 'TIMEOUT',0
ram_bad: db 'RAM FAIL',0
ram_ok: db 'RAM OK',0
include 'board.asm'
include 'music/player.asm'
include 'music/canyon.inc'
include 'music/suspense.inc'
	defs 8000h-$,0ffh
