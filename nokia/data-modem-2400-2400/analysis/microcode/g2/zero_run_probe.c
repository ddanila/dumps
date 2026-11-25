/* Run state-AF receive dispatch and state step on one preserved ROM image. */
/* Rename the inherited callback and its local struct field spelling so this
 * probe can supply byte-specific modeled USART reads without editing the core. */
#define xread inherited_xread
#define main interface_probe_original_main
#include "../../interface_probe.c"
#undef main
#undef xread

static unsigned char line_byte;
static unsigned status_reads, data_reads;
static unsigned char line_xread(struct em8051 *c, uint16_t address) {
    (void)c;
    if (pc==0x1DBD && address==5) { status_reads++; return 2; }
    if (pc==0x1DC6 && address==1) { data_reads++; return line_byte; }
    errors++; event("unexpected_read",pc,address); return 0;
}

static int call(struct em8051 *c, unsigned entry, unsigned stop, unsigned limit) {
    c->mLowerData[112]=stop & 255;
    c->mLowerData[113]=stop >> 8;
    c->mSFR[REG_SP]=113;
    c->mPC=entry;
    for (unsigned n=0;n<limit && c->mPC!=stop;n++,cycle++) tick(c);
    return c->mPC==stop && !errors;
}

int main(int argc, char **argv) {
    if (argc<5 || argc>28) return 2;
    unsigned delay=strtoul(argv[2],0,0);
    unsigned long history=strtoul(argv[3],0,0);
    if ((delay!=5 && delay!=18) || history >= (1UL<<23)) return 2;
    FILE *rom=fopen(argv[1],"rb"); if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
    c.except=exception; c.inherited_xread=line_xread; c.xwrite=xwrite;
    reset(&c,0);
    for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    errors=event_count=cycle=0;
    c.mSFR[REG_IE]=0;
    c.mLowerData[0x34]=0xAF;
    c.mLowerData[0x22]=0x10; /* qualified state */
    c.mLowerData[0x24]=(delay==5)?2:0;
    c.mLowerData[0x42]=(history>>16)&255;
    c.mLowerData[0x43]=(history>>8)&255;
    c.mLowerData[0x44]=history&255;
    printf("{\"octets\":[");
    for (int i=4;i<argc;i++) {
        char *end=0;
        unsigned long value=strtoul(argv[i],&end,0);
        if (!end || *end || value>255) return 2;
        line_byte=(unsigned char)value;
        status_reads=data_reads=0;
        c.mLowerData[0x21]&=~0x10; /* no earlier output pending */
        if (!call(&c,0x08E9,0x1F00,1000)) return 3;
        if (status_reads!=1 || data_reads!=1) return 4;
        unsigned decoded=c.mLowerData[0x3A];
        printf("%s{\"line\":%lu,\"decoded\":%u,\"zero_octets\":%u,\"status_reads\":%u,\"data_reads\":%u}",
               i==4?"":",",value,decoded,c.mLowerData[0x63],
               status_reads,data_reads);
    }
    c.mPC=0x1000;
    c.mSFR[REG_SP]=113;
    for (unsigned n=0;n<300 && c.mPC!=0x1755;n++,cycle++) tick(&c);
    printf("],\"state_after\":%u,\"zero_octets\":%u,\"errors\":%u,\"reached_stop\":%s}\n",
           c.mLowerData[0x34],c.mLowerData[0x63],errors,
           c.mPC==0x1755?"true":"false");
    return errors || c.mPC!=0x1755;
}
