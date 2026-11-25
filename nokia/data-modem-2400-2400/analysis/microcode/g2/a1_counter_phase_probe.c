/* Re-enter the unchanged 8031 send routine with RAM/SFR state preserved. */
#define main interface_probe_original_main
#include "../../interface_probe.c"
#undef main

static void send_a1(struct em8051 *c, unsigned call) {
    unsigned prior32=c->mLowerData[0x32], prior49=c->mLowerData[0x49];
    unsigned prior24=c->mLowerData[0x24];
    unsigned prior22=c->mLowerData[0x22], prior23=c->mLowerData[0x23];
    unsigned prior4a=c->mLowerData[0x4a], prior65=c->mLowerData[0x65];
    unsigned input2c=c->mLowerData[0x2c];
    c->mPC=0x1ee2; sending=1; tx_due=0; event_count=0;
    unsigned completed=0;
    for (unsigned ticks=0;ticks<2000 && c->mPC!=0x1ee8;ticks++,cycle++) {
        tick(c);
        if (tx_due && cycle>=tx_due) {
            c->mSFR[REG_SCON]|=2; tx_due=0; completed++;
        }
    }
    if (c->mPC!=0x1ee8 || errors || completed!=4) exit(4);
    unsigned wire[4]={0},writes=0;
    for (unsigned i=0;i<event_count;i++)
        if (!strcmp(events[i].kind,"tx")) {
            if (writes<4) wire[writes]=events[i].value;
            writes++;
        }
    if (writes!=4) exit(5);
    printf("%s{\"call\":%u,\"prior32\":%u,\"prior49\":%u,\"prior4a\":%u,\"prior65\":%u,\"prior22\":%u,\"prior23\":%u,\"prior24\":%u,\"input2c\":%u,\"out32\":%u,\"out49\":%u,\"out4a\":%u,\"out65\":%u,\"out24\":%u,\"wire\":[%u,%u,%u,%u]}",
           call?",":"",call,prior32,prior49,prior4a,prior65,
           prior22,prior23,prior24,input2c,c->mLowerData[0x32],
           c->mLowerData[0x49],c->mLowerData[0x4a],c->mLowerData[0x65],
           c->mLowerData[0x24],wire[0],wire[1],wire[2],wire[3]);
}

int main(int argc, char **argv) {
    if (argc!=3) return 2;
    unsigned mode=strtoul(argv[2],0,0);
    if (mode>2) return 2;
    FILE *rom=fopen(argv[1],"rb"); if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
    c.except=exception; c.xread=xread; c.xwrite=xwrite;
    reset(&c,0);
    for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    decoding_probe=1; memset(decode_seen,0,sizeof decode_seen);
    errors=event_count=cycle=0; delay=8;
    c.mSFR[REG_SP]=113; c.mSFR[REG_IE]=0;
    c.mSFR[REG_P1]=0xf8;
    c.mLowerData[0x35]=0x6e;
    if (mode) {
        c.mLowerData[0x34]=0xa0;
        c.mLowerData[0x22]=0x10;
        c.mLowerData[0x17]=0x80;
        c.mPC=0x1000;
        unsigned ticks=0;
        for (;ticks<200 && c.mPC!=0x1755;ticks++,cycle++) tick(&c);
        if (c.mPC!=0x1755 || c.mLowerData[0x34]!=0xa1 || errors) return 3;
    } else c.mLowerData[0x34]=0xa1;
    if (mode==2) c.mLowerData[0x24]|=0x20; /* main-loop observed changed-input flag */
    printf("{\"mode\":%u,\"entry32\":%u,\"entry49\":%u,\"entry24\":%u,\"rows\":[",
           mode,c.mLowerData[0x32],c.mLowerData[0x49],c.mLowerData[0x24]);
    for (unsigned call=0;call<20;call++) {
        if (mode==2 && call==1)
            c.mLowerData[0x24]&=(unsigned char)~0x20;
        send_a1(&c,call);
    }
    printf("],\"errors\":%u}\n",errors);
    return errors!=0;
}
