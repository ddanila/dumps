; NASM -f bin bioschk.asm -o BIOSCHK.COM
; 8088-compatible DOS probe. No BIOS patches or emulated RAM injections.
bits 16
cpu 8086
org 100h
start:
    push cs
    pop ds
    push cs
    pop es
    mov dx, filename
    xor cx, cx
    mov ah, 3ch
    int 21h
    jc fatal
    mov [handle], ax
    mov si, started
    call report
    int 12h
    cmp ax, 640
    jne fail
    mov si, memory
    call report
    mov ah, 0fh
    int 10h
    cmp al, 3
    jne fail
    cmp ah, 80
    jne fail
    mov si, video
    call report
    xor ah, ah
    int 1ah
    mov [ticks], dx
    ; Timer interrupts must continue while we poll the BIOS tick service.
    mov bp, 0ffffh
.timer:
    xor ah, ah
    int 1ah
    sub dx, [ticks]
    cmp dx, 3
    jae .timer_ok
    dec bp
    jnz .timer
    jmp fail
.timer_ok:
    mov si, timer
    call report
    xor ax, ax
    xor dx, dx
    int 13h
    jc fail
    mov ax, 0201h
    mov bx, buffer
    mov cx, 1
    xor dx, dx
    int 13h
    jc fail
    cmp word [buffer+510], 0aa55h
    jne fail
    mov si, disk
    call report
    ; Last sector of a 360 KiB floppy: cylinder 39, head 1, sector 9.
    ; Host prepares it as 512 bytes of A5, outside allocated DOS files.
    mov ax, 0201h
    mov bx, buffer
    mov cx, 2709h
    mov dx, 0100h
    int 13h
    jc fail
    mov si, buffer
    mov cx, 256
.compare:
    lodsw
    cmp ax, 0a5a5h
    jne fail
    loop .compare
    mov si, seek
    call report
    mov si, prompt
    call report
.key:
    xor ah, ah
    int 16h
    cmp ax, 256bh ; physical K key, lowercase k
    jne .key
    mov si, keyboard
    call report
    mov si, passed
    call report
    mov bx, [handle]
    mov ah, 3eh
    int 21h
    jc fatal
    mov ax, 4c00h
    int 21h
fail:
    mov si, failed
    call report
    mov bx, [handle]
    mov ah, 3eh
    int 21h
fatal:
    mov ax, 4c01h
    int 21h
report:
    push ax
    push bx
    push cx
    push dx
    push si
    mov dx, si
    xor cx, cx
.len:
    lodsb
    test al, al
    jz .write
    inc cx
    jmp .len
.write:
    mov bx, [handle]
    mov ah, 40h
    int 21h
    pop si
    push si
.screen:
    lodsb
    test al, al
    jz .done
    mov ah, 0eh
    mov bx, 7
    int 10h
    jmp .screen
.done:
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
handle dw 0
ticks dw 0
filename db 'BIOSCHK.TXT',0
started db 'DOS boot and BIOS service probe started',13,10,0
memory db 'PASS INT 12h: 640 KiB',13,10,0
video db 'PASS INT 10h: mode 3, 80 columns; teletype output',13,10,0
timer db 'PASS INT 1Ah: timer advances at least 3 ticks',13,10,0
disk db 'PASS INT 13h: reset and boot-sector read',13,10,0
seek db 'PASS INT 13h: C39 H1 S9 data matches 512-byte pattern',13,10,0
prompt db 'Press lowercase k to test INT 16h keyboard input...',13,10,0
keyboard db 'PASS INT 16h: scan 25h, ASCII 6Bh',13,10,0
passed db 'ALL BIOS CHECKS PASS',13,10,0
failed db 'FAIL BIOS CHECK',13,10,0
buffer times 512 db 0
