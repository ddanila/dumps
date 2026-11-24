/* Local RAM34 state-step probe using the same 8031 core and callbacks. */
#define main interface_probe_original_main
#include "../../interface_probe.c"
#undef main

int main(int argc, char **argv) {
    if (argc != 8) return 2;
    unsigned values[6];
    for (int i=0;i<6;i++) {
        char *end;
        unsigned long v=strtoul(argv[i+2],&end,0);
        if (*end || v>255) return 2;
        values[i]=(unsigned)v;
    }
    FILE *rom=fopen(argv[1],"rb");
    if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
    c.except=exception; c.xread=xread; c.xwrite=xwrite;
    reset(&c,0);
    for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    decoding_probe=1;
    memset(decode_seen,0,sizeof decode_seen);
    errors=event_count=0;
    c.mPC=0x1000;
    c.mSFR[REG_SP]=113;
    c.mLowerData[0x34]=values[0]; /* state */
    c.mLowerData[0x24]=values[1]; /* 04h.5 changed-input/reload flag */
    c.mLowerData[0x16]=values[2]; /* timer low */
    c.mLowerData[0x17]=values[3]; /* timer high */
    c.mLowerData[0x15]=values[4]; /* gate tested before state dispatch */
    c.mLowerData[0x22]=values[5]; /* reset/qualification flags */
    c.mLowerData[0x14]=0;
    c.mSFR[REG_IE]=0; /* no synthetic interrupts during this one step */
    for (cycle=0;cycle<200 && c.mPC!=0x1755;cycle++) tick(&c);
    printf("{\"reached_stop\":%s,\"cycles\":%u,\"pc\":%u,\"errors\":%u,\"state\":%u,\"timer16\":%u,\"timer17\":%u,\"flag24\":%u,\"visited\":[",
        c.mPC==0x1755?"true":"false",cycle,c.mPC,errors,c.mLowerData[0x34],
        c.mLowerData[0x16],c.mLowerData[0x17],c.mLowerData[0x24]);
    unsigned count=0;
    for (unsigned p=0;p<8192;p++) if (decode_seen[p]) printf("%s%u",count++?",":"",p);
    puts("]}");
    return errors || c.mPC!=0x1755;
}
