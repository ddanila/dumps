/* Isolated 8080-compatible instruction probes. Not a terminal/8085 emulator. */
#include "i8080.h"
#include <string.h>
static i8080 cpu;
static unsigned char mem[65536], rom[16384], inputs[256], input_set[256];
static unsigned char out_port[4096], out_value[4096];
static unsigned out_count, fault, fault_address;
static int bad_read_address=-1;
static unsigned char bad_read_xor;
static uint8_t rd(void *u,uint16_t a) {
    if(a>=0x4000 && a<0x5800) {fault=3;fault_address=a;}
    return mem[a] ^ (a==bad_read_address ? bad_read_xor : 0);
}
static void wr(void *u,uint16_t a,uint8_t v) {
    if(a<0x5800) {fault=4;fault_address=a;return;} mem[a]=v;
}
static uint8_t pi(void*u,uint8_t p) {
    if(!input_set[p]){fault=5;fault_address=p;} return inputs[p];
}
static void po(void*u,uint8_t p,uint8_t v) {
    if(out_count>=4096){fault=6;return;}
    out_port[out_count]=p;out_value[out_count++]=v;
}
void load(const unsigned char*b){memcpy(rom,b,16384);}
void reset(void){
 memset(mem,0,sizeof(mem));memcpy(mem,rom,16384);
 memset(input_set,0,sizeof(input_set));out_count=fault=fault_address=0;bad_read_address=-1;
 i8080_init(&cpu);cpu.read_byte=rd;cpu.write_byte=wr;cpu.port_in=pi;cpu.port_out=po;
 cpu.sp=0xf000;mem[0xf000]=0xff;mem[0xf001]=0xff;
}
void put(unsigned a,unsigned v){mem[a&65535]=v;}
unsigned peek(unsigned a){return mem[a&65535];}
void input(unsigned p,unsigned v){inputs[p&255]=v;input_set[p&255]=1;}
void corrupt_read(unsigned a,unsigned mask){bad_read_address=a;bad_read_xor=mask;}
void set(unsigned r,unsigned v){switch(r){case 0:cpu.a=v;break;case 1:cpu.b=v>>8;cpu.c=v;break;case 2:cpu.d=v>>8;cpu.e=v;break;case 3:cpu.h=v>>8;cpu.l=v;break;case 4:cpu.cf=v;break;case 5:cpu.sp=v;break;}}
unsigned get(unsigned r){switch(r){case 0:return cpu.a;case 1:return cpu.b*256+cpu.c;case 2:return cpu.d*256+cpu.e;case 3:return cpu.h*256+cpu.l;case 4:return cpu.cf;case 5:return cpu.sp;case 6:return cpu.pc;case 7:return fault_address;case 8:return out_count;case 9:return cpu.zf;}return 0;}
unsigned output(unsigned i){return out_port[i]*256+out_value[i];}
int run(unsigned start,unsigned stop,unsigned limit){
 cpu.pc=start;
 for(unsigned i=0;i<limit;i++){
  if(cpu.pc==stop)return i;
  if(cpu.pc>=16384){fault_address=cpu.pc;return -1;}
  unsigned op=mem[cpu.pc];
  /* Reject every 8080-undefined / 8085-specific opcode, rather than treating
     RIM/SIM or 8085 undocumented instructions as 8080 NOP/aliases. */
  switch(op){case 0x08:case 0x10:case 0x18:case 0x20:case 0x28:case 0x30:case 0x38:
    case 0xcb:case 0xd9:case 0xdd:case 0xed:case 0xfd:fault_address=cpu.pc;return -2;}
  i8080_step(&cpu);if(fault)return -(int)fault;
  if(cpu.halted)return -7;
 }
 return -8;
}
