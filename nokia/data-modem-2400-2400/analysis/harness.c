/* Unmodified-ROM 8031 execution probe. External inputs are synthetic.
 * CPU core: repository's vendored, MIT-licensed emu8051 (see README). */
#include "emu8051.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char code[65536], ram[65536];
static unsigned long counts[65536], rd[65536], wr[65536], sf[128], steps, cyc, resets, txcount, rxcount, txdue;
static unsigned pc, input, pins, errors;
static FILE *trace;
void sat_trace(struct em8051 *c) {
 pc=c->mPC; steps++;
 if(pc>=8192){fprintf(stderr,"Out-of-ROM PC %04x\n",pc);exit(3);}
 if(counts[pc]++==0){char s[128];decode(c,pc,s);fprintf(trace,"I %lu %04x %-30s A=%02x DP=%02x%02x SP=%02x\n",cyc,pc,s,c->mSFR[REG_ACC],c->mSFR[REG_DPH],c->mSFR[REG_DPL],c->mSFR[REG_SP]);}
}
static uint8_t xr(struct em8051 *c,uint16_t a){if(code[pc]==0xe2 || code[pc]==0xe3)a|=(unsigned)c->mSFR[REG_P2]<<8;if(rd[a]++<8)fprintf(trace,"R %lu %04x %04x %02x\n",cyc,pc,a,input);return input;}
static void xw(struct em8051 *c,uint16_t a,uint8_t v){if(code[pc]==0xf2 || code[pc]==0xf3)a|=(unsigned)c->mSFR[REG_P2]<<8;if(wr[a]++<16)fprintf(trace,"W %lu %04x %04x %02x\n",cyc,pc,a,v);ram[a]=v;}
static uint8_t sr(struct em8051 *c,uint8_t a){return c->mSFR[a-128]&pins;}
static void sw(struct em8051 *c,uint8_t a){if(a==0x99){txdue=cyc+8;if(txcount++<128)fprintf(trace,"TX %lu %04x %02x\n",cyc,pc,c->mSFR[REG_SBUF]);}if(sf[a-128]++<32)fprintf(trace,"S %lu %04x %02x %02x\n",cyc,pc,a,c->mSFR[a-128]);}
static void ex(struct em8051 *c,int e){errors++;if(errors<20)fprintf(trace,"EX %lu %04x %d\n",cyc,c->mPC,e);if(e==5)exit(4);}
int main(int argc,char **argv){if(argc!=6)return 2; FILE*f=fopen(argv[1],"rb");if(!f)return 2;memset(code,255,sizeof code);if(fread(code,1,8192,f)!=8192)return 2;fclose(f);input=strtoul(argv[2],0,0);pins=strtoul(argv[3],0,0);unsigned limit=strtoul(argv[4],0,0);trace=fopen(argv[5],"w");if(!trace)return 2;
 struct em8051 c={0};c.mCodeMem=code;c.mCodeMemMaxIdx=65535;c.mExtData=ram;c.mExtDataMaxIdx=65535;c.except=ex;c.xread=xr;c.xwrite=xw;reset(&c,0);
 if(getenv("PRESEED"))for(int i=0;i<0x60;i++)c.mLowerData[i]=i;
 for(int a=0;a<128;a++)c.sfrwrite[a]=sw;
 c.sfrread[REG_P1]=sr;c.sfrread[REG_P3]=sr;
 if(getenv("DISASM")){for(unsigned a=0;a<8192;){char buf[128];unsigned n=decode(&c,a,buf);printf("%04x  %-32s\n",a,buf);a+=n?n:1;}return 0;}
 for(cyc=0;cyc<limit;cyc++){tick(&c);if(getenv("SHIFT")){if(txdue && cyc>=txdue){c.mSFR[REG_SCON]|=2;txdue=0;}if((c.mSFR[REG_SCON]&0x11)==0x10 && cyc%8==0){c.mSFR[REG_SBUF]=strtoul(getenv("SHIFT"),0,0);c.mSFR[REG_SCON]|=1;if(rxcount++<64)fprintf(trace,"RX %lu %04x %02x\n",cyc,c.mPC,c.mSFR[REG_SBUF]);}}if(getenv("WATCHDOG") && c.mPC==0x1ec4 && cyc%2000==1999){reset(&c,0);resets++;fprintf(trace,"RESET %lu retain-iram\n",cyc);}}
 printf("{\"resets\":%lu,\"tx_count\":%lu,\"rx_count\":%lu,",resets,txcount,rxcount);
 printf("\"cycles\":%u,\"instructions\":%lu,\"pc\":%u,\"exceptions\":%u,\"input\":%u,\"pins\":%u,\"coverage\":[",limit,steps,c.mPC,errors,input,pins);
 int sep=0;for(int i=0;i<8192;i++)if(counts[i]){printf("%s[%d,%lu]",sep?",":"",i,counts[i]);sep=1;}
 printf("],\"reads\":[");sep=0;for(int i=0;i<65536;i++)if(rd[i]){printf("%s[%d,%lu]",sep?",":"",i,rd[i]);sep=1;}
 printf("],\"writes\":[");sep=0;for(int i=0;i<65536;i++)if(wr[i]){printf("%s[%d,%lu,%d]",sep?",":"",i,wr[i],ram[i]);sep=1;}
 printf("],\"iram\":[");for(int i=0;i<128;i++)printf("%s%d",i?",":"",c.mLowerData[i]);printf("]}\n");fclose(trace);return 0;}
