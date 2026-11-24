/* Execute repeated received-octet classifier calls, then the state-83 step. */
#define main interface_probe_original_main
#include "../../interface_probe.c"
#undef main

int main(int argc, char **argv) {
    if (argc < 3 || argc > 10) return 2;
    FILE *rom=fopen(argv[1],"rb"); if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
    c.except=exception; c.xread=xread; c.xwrite=xwrite;
    reset(&c,0);
    for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    errors=event_count=cycle=0;
    c.mSFR[REG_IE]=0;
    c.mLowerData[0x34]=0x83;
    c.mLowerData[0x22]=0x10; /* qualified state */
    printf("{\"octets\":[");
    for (int i=2;i<argc;i++) {
        char *end=0;
        unsigned long value=strtoul(argv[i],&end,0);
        if (!end || *end || value>255) return 2;
        c.mLowerData[0x3a]=(unsigned char)value;
        c.mLowerData[0x21]|=0x10; /* new descrambled octet pending */
        c.mLowerData[112]=0x00; c.mLowerData[113]=0x1f;
        c.mSFR[REG_SP]=113; c.mPC=0x1c07;
        unsigned count=0;
        for (;count<200 && c.mPC!=0x1f00;count++,cycle++) tick(&c);
        if (c.mPC!=0x1f00 || errors) return 3;
        printf("%s{\"byte\":%lu,\"class\":%u,\"equal_count\":%u,\"prior\":%u}",
            i==2?"":",",value,c.mLowerData[0x24]&0x0c,
            c.mLowerData[0x63],c.mLowerData[0x66]);
    }
    c.mSFR[REG_SP]=113; c.mPC=0x1000;
    c.mLowerData[0x15]=0;
    c.mLowerData[0x17]=0;
    unsigned count=0;
    for (;count<200 && c.mPC!=0x1755;count++,cycle++) tick(&c);
    if (c.mPC!=0x1755 || errors) return 4;
    printf("],\"state_after\":%u,\"equal_count\":%u,\"errors\":%u}\n",
        c.mLowerData[0x34],c.mLowerData[0x63],errors);
    return 0;
}
