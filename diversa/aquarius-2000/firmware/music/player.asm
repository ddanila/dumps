; Native ROM player for flat JukuPoly v1 rows (three tones, slide, drums).
; Each voice has a phase, step, current level, target level, envelope mask
; and mode. Phase carry generates one impulse, as in the Juku engine.
voice1:       equ 801bh
voice2:       equ voice1+8
voice3:       equ voice2+8
slide_step:   equ voice3+8
music_row:    equ slide_step+2
rows_left:    equ music_row+2    ; frames remaining in the current row
env_clock:    equ rows_left+1
drum_pos:     equ env_clock+1
drum_frames:  equ drum_pos+2
sample_count: equ drum_frames+1
deadline:     equ sample_count+1
fraction:     equ deadline+1

play_canyon:
	ld hl,canyon_song_rows
	ld de,canyon_title
	jr play_song
play_suspense:
	ld hl,suspense_song_rows
	ld de,suspense_title
play_song:
	push hl
	ex de,hl
	call show_key
	ld a,0c0h
	call lcd_command
	ld hl,stop_text
	call lcd_text
	call pad
	ld hl,voice1
	ld de,voice1+1
	ld bc,fraction-voice1
	ld (hl),0
	ldir
	pop hl
	ld (music_row),hl
	in a,(10h)
	ld (deadline),a
music_frame:
	in a,(52h)
	bit 0,a               ; RESET abort, including while the chord is held
	jp z,music_end
	ld hl,env_clock
	inc (hl)
	ld ix,voice1
	call envelope
	ld ix,voice2
	call envelope
	ld ix,voice3
	call envelope
	ld hl,(voice1+2)
	ld a,h
	or l
	jr z,no_slide
	ld de,(slide_step)
	add hl,de
	ld (voice1+2),hl
no_slide:
	ld hl,rows_left
	ld a,(hl)
	or a
	jr z,next_row
	dec (hl)
	jr start_samples
next_row:
	ld hl,(music_row)
	ld a,(hl)
	dec a
	ld (rows_left),a
	inc hl
	ld b,(hl)             ; flags survive voice parsing
	inc hl
	bit 7,b
	jp nz,music_end
	ld ix,voice1
	bit 0,b
	call nz,read_voice
	ld ix,voice2
	bit 1,b
	call nz,read_voice
	ld ix,voice3
	bit 2,b
	call nz,read_voice
	bit 3,b
	jr z,no_new_slide
	ld e,(hl)
	inc hl
	ld d,(hl)
	inc hl
	ld (slide_step),de
no_new_slide:
	bit 4,b
	jr z,row_ready
	ld e,(hl)
	inc hl
	ld d,(hl)
	inc hl
	ex de,hl
	ld c,(hl)
	inc hl
	ld b,(hl)
	inc hl
	ld a,(hl)
	ld (drum_frames),a
	ld (drum_pos),bc
	ex de,hl
row_ready:
	ld (music_row),hl
start_samples:
	exx
	ld bc,(voice1+2)
	ld de,(voice2+2)
	exx
	ld a,144
	ld (sample_count),a
music_sample:
	; The 4 MHz CPU and CTC prescale of 16 give 250000 counts/s.
	; 34 + 13/18 counts per sample gives 7200 Hz on average.
	ld a,(fraction)
	add a,13
	ld b,34
	cp 18
	jr c,sample_budget
	sub 18
	inc b
sample_budget:
	ld (fraction),a
	ld a,(deadline)
	sub b
	jr nc,deadline_set
	add a,250
deadline_set:
	ld (deadline),a
	ld c,a
wait_sample:
	in a,(10h)
	sub c
	jr nc,check_deadline
	add a,250
check_deadline:
	jr z,on_time
	cp 125                 ; down-counter still ahead of our target
	jr c,wait_sample
on_time:
	exx                    ; BC and DE hold the first two steps for this frame
	xor a
	ld hl,(voice1)
	add hl,bc
	ld (voice1),hl
	jr nc,mix_second
	ld a,(voice1+4)
mix_second:
	ld hl,(voice2)
	add hl,de
	ld (voice2),hl
	jr nc,mix_third
	ld l,a
	ld a,(voice2+4)
	or l
mix_third:
	exx
	ld c,a
	ld hl,(voice3)
	ld de,(voice3+2)
	add hl,de
	ld (voice3),hl
	jr nc,mix_drum
	ld a,(voice3+4)
	or c
	ld c,a
mix_drum:
	ld a,(drum_frames)
	or a
	jr z,mixed
	ld hl,(drum_pos)
	ld a,(hl)
	or c
	ld c,a
	inc hl
	ld (drum_pos),hl
mixed:
	ld a,c
	or a
	jr z,sample_done
	; Two variable-width edges share PB with the LCD and periodic output.
	; Jump into a NOP ladder for 4 extra clocks per amplitude level.
	ld a,15
	sub c
	ld e,a
	ld d,0
	ld hl,pulse_delay
	add hl,de
	di
	in a,(51h)
	or 8
	out (51h),a
	jp (hl)
pulse_delay:
	defs 15,0              ; NOPs
	and 0f7h
	out (51h),a
	ei
sample_done:
	ld hl,sample_count
	dec (hl)
	jp nz,music_sample
	ld hl,drum_frames
	ld a,(hl)
	or a
	jp z,music_frame
	dec (hl)
	jp music_frame
music_end:
	; Every pulse already ends low. Leave interrupts and the CTC running.
	ret

; Consume a variable-length tone packet, preserving B (row flags).
read_voice:
	ld e,(hl)
	inc hl
	ld d,(hl)
	inc hl
	ld a,d
	and 7fh
	ld (ix+2),e
	ld (ix+3),a
	or e
	jr nz,read_envelope
	xor a
	ld (ix+0),a
	ld (ix+1),a
	ld (ix+4),a
	ret
read_envelope:
	ld a,(hl)
	inc hl
	ld (ix+6),a
	ld a,(hl)
	inc hl
	ld c,a
	and 0fh
	ld (ix+5),a
	ld a,c
	and 30h
	ld (ix+7),a
	bit 7,d
	ret nz                 ; legato retains phase and current volume
	ld (ix+0),0
	ld (ix+1),0
	or a
	jr z,voice_volume
	ld a,(ix+5)
voice_volume:
	ld (ix+4),a
	ret
envelope:
	ld a,(env_clock)
	and (ix+6)
	ret nz
	ld a,(ix+7)
	or a
	jr z,attack
	cp 10h
	ret nz
	ld a,(ix+4)
	or a
	ret z
	dec (ix+4)
	ret
attack:
	ld a,(ix+4)
	cp (ix+5)
	ret nc
	inc (ix+4)
	ret
canyon_title: db 'JUKUPOLY CANYON',0
suspense_title: db 'JUKUPOLY SUSPENSE',0
stop_text: db 'RESET STOPS MUSIC',0
