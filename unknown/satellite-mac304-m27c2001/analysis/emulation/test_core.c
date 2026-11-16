#include "emu8051/emu8051.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
  struct em8051 c = {0};
  unsigned char code[65536] = {0}, ram[65536] = {0}, upper[128] = {0};
  c.mCodeMem = code;
  c.mCodeMemMaxIdx = 65535;
  c.mExtData = ram;
  c.mExtDataMaxIdx = 65535;
  c.mUpperData = upper;
  reset(&c, 0);
  /* Actual LCALL/RET using the firmware's upper-IRAM stack. */
  code[0] = 0x12;
  code[1] = 0;
  code[2] = 4;
  code[4] = 0x22;
  c.mSFR[REG_SP] = 0xa9;
  c.mSFR[0x2a] = 0x5a;
  c.mSFR[0x2b] = 0xa5;
  assert(tick(&c));
  assert(c.mPC == 4);
  assert(upper[0x2a] == 3 && upper[0x2b] == 0);
  assert(c.mSFR[0x2a] == 0x5a && c.mSFR[0x2b] == 0xa5);
  assert(!tick(&c));
  assert(c.mPC == 4);
  assert(tick(&c));
  assert(c.mPC == 3 && c.mSFR[REG_SP] == 0xa9);
  /* NOP is one machine cycle; LCALL and RET are two. */
  assert(!tick(&c));
  assert(tick(&c));
  assert(c.mPC == 4);
  puts("PASS upper-IRAM stack isolation and 1/2-cycle instruction timing");
}
