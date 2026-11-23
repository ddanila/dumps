/* Run both ROMs on a real Z80 instruction core; model only the signals below. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <z80ex/z80ex.h>

typedef uint8_t byte;
typedef uint16_t word;
typedef Z80EX_CONTEXT CPU;
typedef struct { byte port, value; } Write;
static struct {
    byte mem[65536], ports[256], lcd[128], cursor, keys, pin, vector;
    int replacement, tone_edges, ready, serial_clocks, trigger, irq_count;
    int peer, sent, bits;
    byte ctc_control[4], ctc_load[4], ctc_constant[4];
    int elapsed, scheduled, commands, init_count;
    Write trace[512];
    int tracing, count;
} m;

static byte mem_read(CPU *cpu, word addr, int fetch, void *ctx) {
    (void)cpu; (void)fetch; (void)ctx;
    return m.mem[addr];
}
static void mem_write(CPU *cpu, word addr, byte value, void *ctx) {
    (void)cpu; (void)ctx;
    assert(addr >= 0x8000);
    if (m.replacement) assert(addr < 0x8100);
    m.mem[addr] = value;
}
static byte port_read(CPU *cpu, word port, void *ctx) {
    (void)cpu; (void)ctx;
    switch ((byte)port) {
    case 0x52: return ~m.keys;
    case 0x30: return (m.ports[0x30] & 15) | m.pin;
    case 0x11: return 0x12;
    case 0x12: return 0x34;
    case 0x13: return 0x56;
    case 0x50: {
        int bit = m.ready;
        if (m.serial_clocks >= 10 && m.serial_clocks <= 25)
            bit = (0xa53c >> (25-m.serial_clocks)) & 1;
        return (m.ports[0x50] & 0x7e) | (bit << 7) |
               (m.peer && (m.ports[0x51] & 64) ? 1 : 0);
    }
    default: return m.ports[(byte)port];
    }
}
static void port_write(CPU *cpu, word port, byte value, void *ctx) {
    (void)cpu; (void)ctx;
    byte p = port, old = m.ports[p];
    m.ports[p] = value;
    if (m.tracing) {
        assert(m.count < 512);
        m.trace[m.count++] = (Write){p,value};
    }
    if (p >= 0x10 && p <= 0x13) {
        unsigned ch = p - 0x10;
        if (m.ctc_load[ch]) {
            m.ctc_constant[ch] = value;
            m.ctc_load[ch] = 0;
        } else if (value & 1) {
            m.ctc_control[ch] = value;
            m.ctc_load[ch] = value & 4;
        } else if (!ch) {
            m.vector = value & 0xf8;
        }
    }
    if (p == 0x50) {
        if (!(value & 0x10)) m.serial_clocks = 0;
        if ((value & 0x30) == 0x30 && !(old & 0x20)) ++m.serial_clocks;
    }
    if (p != 0x51) return;
    if (!(old & 64) && (value & 64)) {
        m.sent = ((m.sent << 1) | (value >> 7)) & 255;
        ++m.bits;
    }
    if ((old ^ value) & 8) ++m.tone_edges;
    if (!(old & 4) || (value & 4)) return;
    byte data = m.ports[0x40];
    if (old & 1) m.lcd[m.cursor++ & 127] = data;
    else if (data & 128) m.cursor = data & 127;
    else if (data == 1) memset(m.lcd,' ',sizeof m.lcd);
    if (!(old & 1)) {
        static const byte setup[] = {0x38,1,12,6};
        if (m.init_count < 4 && data == setup[m.init_count]) ++m.init_count;
        ++m.commands;
    }
}
static byte vector_read(CPU *cpu, void *ctx) {
    (void)cpu; (void)ctx;
    return m.vector;
}
static CPU *load(const char *path, int replacement) {
    memset(&m,0,sizeof m);
    memset(m.mem+0x8000,0x96,32768);
    FILE *file = fopen(path,"rb");
    assert(file && fread(m.mem,1,32768,file)==32768 && fgetc(file)==EOF);
    fclose(file);
    m.replacement = replacement;
    m.ready = m.trigger = 1;
    return z80ex_create(mem_read,NULL,mem_write,NULL,port_read,NULL,
                        port_write,NULL,vector_read,NULL);
}
static void step(CPU *cpu) {
    m.elapsed += z80ex_step(cpu);
    int period = 0;
    if (m.ctc_control[0] == 0x87) period = 16 * m.ctc_constant[0];
    if (m.ctc_control[0] == 0xc7 && m.trigger && m.ctc_constant[0] == 128 &&
        (m.ports[0x30] == 9 || m.ports[0x30] == 10)) period = 4000;
    if (m.scheduled && period && m.elapsed >= period && !m.ctc_load[0]) {
        if (z80ex_int(cpu)) { ++m.irq_count; m.elapsed = 0; }
    }
}
static void run(CPU *cpu, int steps) {
    while (steps--) step(cpu);
}
static void until_pc(CPU *cpu, word addr) {
    for (int n=0; n<1000000; ++n) {
        if (z80ex_get_reg(cpu,regPC)==addr) return;
        step(cpu);
    }
    fprintf(stderr,"failed to reach %04x from PC %04x\n",addr,z80ex_get_reg(cpu,regPC));
    assert(0);
}
static void routine(CPU *cpu, word pc, byte a) {
    m.mem[0x80fc]=0xfe;
    m.mem[0x80fd]=0x7f;
    z80ex_set_reg(cpu,regSP,0x80fc);
    z80ex_set_reg(cpu,regAF,a<<8);
    z80ex_set_reg(cpu,regPC,pc);
    until_pc(cpu,0x7ffe);
}
static void row(int offset, const char *prefix) {
    if (memcmp(m.lcd+offset,prefix,strlen(prefix))) {
        fprintf(stderr,"expected [%s], screen [%.20s]\n",prefix,m.lcd+offset);
        assert(0);
    }
}
static void check_init(CPU *cpu, int replacement, Write *init) {
    m.tracing = 1;
    while (m.count < 8) { step(cpu); assert(m.elapsed < 20000); }
    if (replacement) assert(!memcmp(init,m.trace,8*sizeof *init));
    else memcpy(init,m.trace,8*sizeof *init);
    m.tracing = 0;
}
static void capture_trace(CPU *cpu, word pc, byte a, byte shared) {
    m.ports[0x51] = shared;
    m.tracing = 1;
    m.count = 0;
    routine(cpu,pc,a);
    m.tracing = 0;
}
static word symbol(const char *name) {
    FILE *f = fopen("build/symbols.txt","r");
    char line[256], label[128];
    unsigned addr;
    assert(f);
    while (fgets(line,sizeof line,f)) {
        if (sscanf(line,"%127[^:]: equ $%x",label,&addr)==2 && !strcmp(label,name)) {
            fclose(f);
            return addr;
        }
    }
    fclose(f);
    assert(0);
    return 0;
}
int main(int argc,char **argv) {
    assert(argc==3);
    Write init[8], reference[3][100], nv_reads[64][64];
    int lengths[3];
    CPU *cpu = load(argv[1],0);
    check_init(cpu,0,init);
    /* Retained checksum permits the factory startup path past its RAM wipe. */
    m.mem[0x8302]=0xe8;
    m.mem[0x8303]=0x0a;
    until_pc(cpu,0x31d2);
    assert(m.mem[0x8080]==0xe8 && m.mem[0x8081]==0x0a && m.init_count==4);
    const word factory[] = {0x2857,0x2876,0x302e};
    for (int i=0; i<3; ++i) {
        capture_trace(cpu,factory[i],i==2?0:0x41,0xe9);
        lengths[i]=m.count;
        assert(m.count <= 100);
        memcpy(reference[i],m.trace,m.count*sizeof(Write));
        if (i==2) assert(z80ex_get_reg(cpu,regDE)==0xa53c);
    }
    for (int addr=0; addr<64; ++addr) {
        capture_trace(cpu,0x302e,2*addr,0);
        assert(m.count==lengths[2] && m.count<=64);
        memcpy(nv_reads[addr],m.trace,m.count*sizeof(Write));
    }
    for (int bit=0; bit<8; ++bit) {
        memset(m.mem+0x8200,0,0x300);
        z80ex_set_reg(cpu,regIX,0x8401);
        m.keys=1<<bit;
        for (int i=0; i<3; ++i) {
            m.mem[0x842e]=1; /* ISR debounce scan is due */
            routine(cpu,0x2526,0);
        }
        routine(cpu,0x2511,0);
        assert(z80ex_get_reg(cpu,regAF)>>8 == (0x80>>bit));
    }
    z80ex_destroy(cpu);
    cpu=load(argv[2],1);
    const char *drivers[]={"lcd_command","lcd_data","nv_word"};
    for (int i=0; i<3; ++i) {
        capture_trace(cpu,symbol(drivers[i]),i==2?0:0x41,0xe9);
        assert(m.count==lengths[i] && !memcmp(reference[i],m.trace,m.count*sizeof(Write)));
        if (i==2) assert(z80ex_get_reg(cpu,regHL)==0xa53c);
    }
    for (int addr=0; addr<64; ++addr) {
        m.ports[0x50]=6;
        capture_trace(cpu,symbol("nv_word"),addr,0);
        assert(m.count==lengths[2]);
        for (int i=0; i<m.count; ++i) {
            assert(m.trace[i].port==0x50);
            assert(m.trace[i].value==(nv_reads[addr][i].value|6));
        }
    }
    z80ex_destroy(cpu);
    cpu=load(argv[2],1);
    check_init(cpu,1,init);
    m.scheduled=1;
    run(cpu,200000);
    row(0,"AQ2000 BOARD TEST");
    row(64,"00 KEY PREV 00");
    assert(m.init_count==4 && m.irq_count>0);
    m.keys=0x10; run(cpu,500); m.keys=0; run(cpu,30000);
    assert(m.tone_edges==0); /* suppress a brief contact bounce */
    m.pin=0xf0; run(cpu,2000);
    m.pin=0; run(cpu,2000);
    const char *pages[]={"01 KEY PREV 00","02 EDGES 01010101","04 CTC 1 123456",
        "08 TICKS ","10 SEL SOUND","20 PINS ","40 NV00 A53C","80 RAM OK"};
    const char *names[]={"KEY RESET","KEY +","KEY RIGHT","KEY NORM","KEY SELECT","KEY SETUP","KEY LEFT","KEY -"};
    for (int bit=0; bit<8; ++bit) {
        int before=m.tone_edges;
        m.keys=1<<bit;
        run(cpu,300000);
        row(64,pages[bit]);
        row(0,names[bit]);
        assert(m.tone_edges-before==(bit==4?96:0));
        assert(!(m.ports[0x51]&8));
        m.keys=0;
        run(cpu,60000);
        row(64,"00 ");
    }
    for (int ch=1; ch<=3; ++ch)
        assert(m.ctc_control[ch]==0x47 && m.ctc_constant[ch]==0);
    assert(m.mem[0x8070]==0x96 && m.mem[symbol("seconds")]>0);
    m.peer=1; m.keys=0x21; run(cpu,120000);
    assert(m.bits==8 && m.sent==0x55 && !(m.ports[0x51]&0xc0));
    assert(m.mem[symbol("link_status")]==1);
    m.keys=0; run(cpu,60000);
    m.peer=0; m.keys=0x21; run(cpu,120000);
    assert(m.mem[symbol("link_status")]==255 && !(m.ports[0x51]&0xc0));
    m.ready=0; m.keys=0x40; run(cpu,100000);
    row(64,"40 NV01 TIMEOUT"); assert(!m.ports[0x50]);
    m.trigger=0; m.keys=4; run(cpu,400000);
    row(64,"04 CTC 2 TIMEOUT");
    assert(m.vector==16 && m.ports[0x30]==5);
    z80ex_destroy(cpu);
    puts("PASS: factory boot I/O, LCD and NV traces, factory key mapping, replacement cold boot, IM2, all keys, chirp, edges, counters, handshake, timeouts and scratch RAM");
    return 0;
}
