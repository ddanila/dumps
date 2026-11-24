/* Uninterrupted 8031 polling-loop probe with explicit peripheral events. */
#include "emu8051.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char code[65536];
static unsigned cycle, pc, errors, tx_due, tx_count, write_count;
static unsigned char tx[16], writes[32];

void sat_trace(struct em8051 *c) { pc=c->mPC; if(pc>=8192) errors++; }
static void exception(struct em8051 *c,int kind) { (void)c;(void)kind;errors++; }
static void sfr_write(struct em8051 *c,uint8_t address) {
    if(address==0x99) {
        if(tx_count<16) tx[tx_count++]=c->mSFR[REG_SBUF];
        else errors++;
        tx_due=cycle+8;
    }
}
static unsigned char xread(struct em8051 *c,uint16_t address) {
    (void)c;(void)address;
    if(pc==0x08e5 || pc==0x0539 || pc==0x1d9d || pc==0x1dbd) return 0;
    fprintf(stderr,"unexpected read pc=%04X address=%04X\n",pc,address);
    errors++;return 0;
}
static void xwrite(struct em8051 *c,uint16_t address,uint8_t value) {
    (void)c;
    if(address==1 || address==2 || address==5 || address==6) {
        if(write_count<32) writes[write_count++]=value;
        else errors++;
    } else {fprintf(stderr,"unexpected write pc=%04X address=%04X value=%02X\n",pc,address,value);errors++;}
}

int main(int argc,char **argv) {
    if(argc!=4) return 2;
    unsigned selector=strtoul(argv[2],0,0), wanted=strtoul(argv[3],0,0);
    if(selector>255 || wanted<1 || wanted>12) return 2;
    FILE *rom=fopen(argv[1],"rb"); if(!rom) return 2;
    memset(code,255,sizeof code);
    if(fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code;c.mCodeMemMaxIdx=65535;
    c.except=exception;c.xread=xread;c.xwrite=xwrite;
    reset(&c,0);
    for(unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    c.mSFR[REG_SP]=113;c.mSFR[REG_IE]=0;
    c.mLowerData[0x34]=0xa0;c.mLowerData[0x22]=0x10;
    c.mLowerData[0x17]=0x80;c.mLowerData[0x13]=0xff;c.mLowerData[0x12]=0xff;
    c.mPC=0x1ed3;
    unsigned char input[]={0,7,0,0,0,(unsigned char)selector,0};
    unsigned rx=0, completed=0, last_pc=0;
    printf("{\"selector\":%u,\"iterations\":[",selector);
    for(cycle=0;cycle<200000 && !errors && completed<wanted;cycle++) {
        unsigned pre=c.mPC;
        if(cycle && pre==0x1ed3 && last_pc!=0x1ed3) {
            if(completed) putchar(',');
            printf("{\"cycle\":%u,\"state\":%u,\"timer\":%u,\"rx\":%u,\"tx\":[",
                   cycle,c.mLowerData[0x34],256*c.mLowerData[0x17]+c.mLowerData[0x16],rx);
            for(unsigned j=0;j<tx_count;j++) printf("%s%u",j?",":"",tx[j]);
            printf("],\"writes\":[");
            for(unsigned j=0;j<write_count;j++) printf("%s%u",j?",":"",writes[j]);
            printf("]}");
            completed++;
            tx_count=write_count=rx=0;
            c.mLowerData[0x17]=0x80; /* externally supplied timer-underflow condition */
            if(completed==wanted) break;
        }
        tick(&c);
        if((c.mSFR[REG_SCON]&0x10) && !(c.mSFR[REG_SCON]&1) && rx<7 &&
           (pre==0x0807 || pre==0x0810 || pre==0x0826 || pre==0x083c ||
            pre==0x0852 || pre==0x0868 || pre==0x087e)) {
            c.mSFR[REG_SBUF]=input[rx++];c.mSFR[REG_SCON]|=1;
        }
        if(tx_due && cycle>=tx_due) {c.mSFR[REG_SCON]|=2;tx_due=0;}
        last_pc=pre;
    }
    printf("],\"completed\":%u,\"errors\":%u,\"final_pc\":%u}\n",completed,errors,c.mPC);
    return errors || completed!=wanted;
}
