/* MAC 3.04 research harness. The ROM is read-only; CPU instructions execute
 * in the vendored MIT core. See README.txt for synthetic I2C/IMbus semantics.
 * OSD hooks observe firmware register-write entry points; they do not replace
 * instructions or decode physical wire/video timing. Persistent display memory
 * is separate from each call's ordered write delta. */
#include "emu8051/emu8051.h"
#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char osd[65536];
static unsigned osdaddr;
static unsigned char stream[65536];
static unsigned streamlen;
static FILE *calls;
static unsigned long long call_delay, notbefore = 4000000;
static int callindex, callr5, callr6, calllang;
static int callbank = -1, called, callentry, callarg;
static FILE *osdlog, *buslog, *settinglog, *slotlog;
static int plan_error, completed;
static unsigned planned;
static unsigned char rom[262144], code[65536], ram[65536], upper[128];
static unsigned long long cycles, counts[5][65536], rd[65536], wr[65536];
static unsigned long long sfrcounts[128];
static unsigned pc, bank;
static int pending, phase, remaining;
static unsigned events;
static unsigned rxpos;
static unsigned rxlen, rxcommand;
static int mock;
static uint8_t sr(struct em8051 *c, uint8_t a) { return c->mSFR[a - 128] & ~1; }
static void sw(struct em8051 *c, uint8_t a) {
  if (sfrcounts[a - 128]++ < 32 && a != 0xe0 && a != 0xd0 && a != 0x81 &&
      a != 0x82 && a != 0x83)
    printf("S %llu %04x %02x=%02x\n", cycles, pc, a, c->mSFR[a - 128]);
}
static uint8_t xr(struct em8051 *c, uint16_t a) {
  unsigned v = ram[a];
  if (mock && a == 0x8700)
    pending = 1;
  if (rd[a]++ < 4)
    printf("R %llu %04x %04x=%02x\n", cycles, pc, a, v);
  return v;
}
static void xw(struct em8051 *c, uint16_t a, uint8_t v) {
  if (a == 0x8000) {
    bank = (v >> 4) - 1;
    if (bank > 3) {
      fprintf(stderr, "invalid bank %u\n", bank);
      exit(3);
    }
    memcpy(code + 32768, rom + 32768 + bank * 32768, 32768);
    printf("BANK %llu %04x %u\n", cycles, pc, bank);
  }
  if (wr[a]++ < 4)
    printf("W %llu %04x %04x=%02x\n", cycles, pc, a, v);
  ram[a] = v;
}
static void interrupt(struct em8051 *c, unsigned status) {
  c->mSFR[0x59] = status;
  c->mSFR[0x58] |= 8;
  push_to_stack(c, c->mPC & 255);
  push_to_stack(c, c->mPC >> 8);
  c->int_a[0] = c->mSFR[REG_ACC];
  c->int_psw[0] = c->mSFR[REG_PSW];
  c->int_sp[0] = c->mSFR[REG_SP];
  c->mInterruptActive = 1;
  c->mPC = 0x2b;
  c->mTickDelay = 0;
  printf("I2C %llu status=%02x data=%02x\n", cycles, status, c->mSFR[0x5a]);
  events++;
}
static void hardware(struct em8051 *c) {
  if (!mock || c->mInterruptActive || c->mTickDelay > 1 ||
      (c->mSFR[REG_IE] & 0xa0) != 0xa0)
    return;
  if (pending) {
    pending = 0;
    phase = 1;
    remaining = ram[0x6eca];
    interrupt(c, 0xa8);
  } else if (phase == 1) {
    if (--remaining > 0)
      interrupt(c, 0xb8);
    else {
      phase = mock >= 2 ? 2 : 0;
      interrupt(c, 0xc0);
    }
  } else if (phase == 2) {
    if (mock >= 4 && !(bank == 2 && c->mPC == 0x8ced))
      return;
    rxpos = 0;
    rxlen = mock >= 4 ? ram[0x6865] : (mock >= 3 ? 3 : 8);
    if (rxlen < 1 || rxlen > 17)
      rxlen = 3;
    rxcommand = mock >= 4 ? ram[0x6864] : 0x84;
    phase = 3;
    interrupt(c, 0x60);
  } else if (phase == 3) {
    c->mSFR[0x5a] =
        rxpos == 0 ? rxcommand
                   : (mock >= 3 && rxcommand == 0x84 && rxpos == 1 ? 0x40 : 0);
    rxpos++;
    if (rxpos == rxlen)
      phase = 4;
    interrupt(c, 0x80);
  } else if (phase == 4) {
    phase = 0;
    interrupt(c, 0xa0);
  }
}
static void ex(struct em8051 *c, int e) {
  printf("EX %llu %04x %d\n", cycles, pc, e);
  if (e == 5)
    exit(2);
}
void sat_trace(struct em8051 *c) {
  pc = c->mPC;
  unsigned rb = c->mSFR[REG_PSW] & 24;
  unsigned target = (c->mLowerData[rb + 6] << 8) | c->mLowerData[rb + 7];
  if (buslog && (pc == 0x03c8 || pc == 0x0354))
    fprintf(buslog, "%llu %04x %04x %02x%02x\n", cycles, pc, target,
            c->mLowerData[0x5c], pc == 0x03c8 ? c->mLowerData[0x5d] : 0);
  if (slotlog && pc == 0x26e9)
    fprintf(slotlog, "%llu %d %04x %u 02 %04x\n", cycles, callindex, pc,
            ram[0x7447], (c->mSFR[REG_DPH] << 8) | c->mSFR[REG_DPL]);
  if (slotlog && bank == 2 && (pc == 0xac32 || pc == 0xac5c))
    fprintf(slotlog, "%llu %d %04x %u %02x %04x\n", cycles, callindex, pc,
            ram[0x7447], c->mLowerData[rb + 5], target);
  if (settinglog && bank == 2 && pc == 0x8dee) {
    unsigned p = (ram[0x6866] << 8) | ram[0x6867];
    fprintf(settinglog, "%llu %04x %02x %04x", cycles, target, ram[0x6865], p);
    for (unsigned i = 0; i < ram[0x6864] && i < 32; i++)
      fprintf(settinglog, " %02x", ram[(p + i) & 65535]);
    fputc('\n', settinglog);
  }
  if (pc == 0x03c8 && target == 0x17a)
    osdaddr = (c->mLowerData[0x5c] << 8) | c->mLowerData[0x5d];
  if (pc == 0x0354 && target == 0x17c) {
    unsigned v = c->mLowerData[0x5c];
    osd[osdaddr++ & 65535] = v;
    if (called && streamlen < sizeof stream)
      stream[streamlen++] = v;
    if (osdlog)
      fprintf(osdlog, "%llu %04x %02x\n", cycles, (osdaddr - 1) & 65535, v);
  }
  unsigned region = pc < 0x8000 ? 0 : bank + 1;
  if (counts[region][pc]++ == 0) {
    char s[128];
    decode(c, pc, s);
    printf("I %llu %u:%04x %s A=%02x DP=%02x%02x SP=%02x\n", cycles, region, pc,
           s, c->mSFR[REG_ACC], c->mSFR[REG_DPH], c->mSFR[REG_DPL],
           c->mSFR[REG_SP]);
  }
}
static int nextcall(void) {
  if (!calls)
    return 0;
  unsigned b, e, a, r5, r6, l;
  char line[1024];
  call_delay = 0;
  if (!fgets(line, sizeof line, calls))
    return 0;
  if (sscanf(line, "%x %x %x %x %x %x %llu", &b, &e, &a, &r5, &r6, &l,
             &call_delay) < 6) {
    plan_error = 1;
    fprintf(stderr, "malformed call plan\n");
    return 0;
  }
  if (b > 3 || e > 65535 || a > 255 || r5 > 255 || r6 > 255 || l > 9) {
    plan_error = 1;
    return 0;
  }
  callbank = b;
  callentry = e;
  callarg = a;
  callr5 = r5;
  callr6 = r6;
  calllang = l;
  return 1;
}
static void startcall(struct em8051 *c) {
  called = 1;
  streamlen = 0;
  printf("CALL %llu index=%d bank=%d entry=%04x arg=%02x lang=%d\n", cycles,
         callindex, callbank, callentry, callarg, calllang);
  unsigned rb = c->mSFR[REG_PSW] & 24;
  c->mLowerData[rb + 5] = callr5;
  c->mLowerData[rb + 6] = callr6;
  c->mLowerData[rb + 7] = callarg;
  ram[0x7447] = calllang;
  ram[0x6868] = ram[0x6869] = 0;
  const char *env = getenv("SAT_XRAM");
  if (env) {
    char buf[1024];
    snprintf(buf, sizeof buf, "%s", env);
    for (char *t = strtok(buf, ","); t; t = strtok(NULL, ",")) {
      unsigned addr, v;
      if (sscanf(t, "%x=%x", &addr, &v) == 2 && addr < 65536 && v < 256) {
        ram[addr] = v;
        printf("MOCK_XRAM %04x=%02x\n", addr, v);
      }
    }
  }
  c->mSFR[REG_ACC] = callbank;
  c->mSFR[REG_DPH] = callentry >> 8;
  c->mSFR[REG_DPL] = callentry;
  push_to_stack(c, 0x0a);
  push_to_stack(c, 1);
  c->mPC = 0x07c5;
  c->mTickDelay =
      0; /* OSD memory persists; only real firmware writes alter it. */
}
static void savecall(void) {
  char name[80];
  sprintf(name, "call-%04d.bin", callindex);
  FILE *f = fopen(name, "wb");
  fwrite(stream, 1, streamlen, f);
  fclose(f);
  sprintf(name, "screen-%04d.bin", callindex);
  f = fopen(name, "wb");
  fwrite(osd, 1, sizeof osd, f);
  fclose(f);
  callindex++;
}
/* Reject overflow, negative values, junk suffixes and empty CLI arguments. */
static int number(const char *s, int base, unsigned limit, unsigned *out) {
  char *end;
  if (!s || !*s || *s == '-' || isspace((unsigned char)*s))
    return 0;
  errno = 0;
  unsigned long value = strtoul(s, &end, base);
  if (errno || *end || value > limit)
    return 0;
  *out = value;
  return 1;
}
int main(int argc, char **argv) {
  struct em8051 c = {0};
  if (argc < 3) {
    fprintf(stderr,
            "usage: sat-run ROM dis START END [BANK] | ROM TICKS [MOCK]\n");
    return 1;
  }
  char *rompath = argv[1];
  argv++;
  argc--;
  FILE *f = fopen(rompath, "rb");
  if (!f)
    return 1;
  if (fread(rom, 1, sizeof rom, f) != sizeof rom) {
    fprintf(stderr, "ROM must be 256KiB\n");
    return 1;
  }
  fclose(f);
  memcpy(code, rom, 65536);
  c.mCodeMem = code;
  c.mCodeMemMaxIdx = 65535;
  c.mExtData = ram;
  c.mExtDataMaxIdx = 65535;
  c.mUpperData = upper;
  reset(&c, 0);
  c.xread = xr;
  c.xwrite = xw;
  c.except = ex;
  for (int i = 0; i < 128; i++)
    c.sfrwrite[i] = sw;
  if (argc > 1 && !strcmp(argv[1], "dis")) {
    unsigned start, end;
    if (argc < 4 || argc > 5 || !number(argv[2], 16, 65535, &start) ||
        !number(argv[3], 16, 65536, &end) || end <= start ||
        (argc == 5 && !number(argv[4], 0, 3, &bank))) {
      fprintf(stderr,
              "usage: sat-run ROM dis START_HEX END_HEX [BANK_0_TO_3]\n");
      return 1;
    }
    memcpy(code + 32768, rom + 32768 + bank * 32768, 32768);
    while (start < end) {
      char s[128];
      int n = decode(&c, start, s);
      printf("%04x  %-24s\n", start, s);
      start += n ? n : 1;
    }
    return 0;
  }
  unsigned long long max = argc > 1 ? strtoull(argv[1], 0, 0) : 1000000;
  mock = argc > 2 ? atoi(argv[2]) : 0;
  if (mock >= 5)
    c.sfrread[REG_P1] = sr;
  if (argc > 5) {
    callbank = strtoul(argv[3], 0, 0);
    callentry = strtoul(argv[4], 0, 16);
    callarg = strtoul(argv[5], 0, 16);
  }
  if (argc > 3 && argv[3][0] == '@') {
    calls = fopen(argv[3] + 1, "r");
    if (calls) {
      while (nextcall())
        planned++;
      rewind(calls);
    }
    if (plan_error || !calls || !planned || !nextcall()) {
      fprintf(stderr, "invalid call file\n");
      return 1;
    }
  }
  osdlog = fopen("osd-writes.tsv", "w");
  buslog = fopen("imbus-writes.tsv", "w");
  settinglog = fopen("settings-writes.tsv", "w");
  slotlog = fopen("language-slots.tsv", "w");
  for (cycles = 0; cycles < max; cycles++) {
    hardware(&c);
    if (callbank >= 0 && !called && cycles > notbefore && !c.mInterruptActive &&
        c.mPC == 0xfeea && bank == 0) {
      startcall(&c);
    }
    if (called && c.mPC == 0x010a) {
      printf("RETURN %llu R7=%02x SP=%02x gate=%02x timeout=%02x menu=%02x\n",
             cycles, c.mLowerData[7], c.mSFR[REG_SP], ram[0x77c0], ram[0x68de],
             ram[0x77ef]);
      savecall();
      if (!nextcall()) {
        completed = !plan_error;
        break;
      }
      if (call_delay) {
        called = 0;
        notbefore = cycles + call_delay;
        c.mPC = 0xfeea;
        c.mTickDelay = 0;
      } else
        startcall(&c);
    }
    tick(&c);
  }
  fclose(osdlog);
  fclose(buslog);
  fclose(settinglog);
  fclose(slotlog);
  f = fopen("osd.bin", "wb");
  fwrite(osd, 1, 65536, f);
  fclose(f);
  printf("END bank=%u pc=%04x IE=%02x TCON=%02x P1=%02x P3=%02x PCON=%02x\n",
         bank, c.mPC, c.mSFR[REG_IE], c.mSFR[REG_TCON], c.mSFR[REG_P1],
         c.mSFR[REG_P3], c.mSFR[REG_PCON]);
  f = fopen("coverage.tsv", "w");
  for (int b = 0; b < 5; b++)
    for (int i = 0; i < 65536; i++)
      if (counts[b][i])
        fprintf(f, "%u:%04x\t%llu\n", b, i, counts[b][i]);
  fclose(f);
  f = fopen("xram.bin", "wb");
  fwrite(ram, 1, 65536, f);
  fclose(f);
  f = fopen("iram.bin", "wb");
  fwrite(c.mLowerData, 1, 128, f);
  fwrite(upper, 1, 128, f);
  fwrite(c.mSFR, 1, 128, f);
  fclose(f);
  if (callbank >= 0 &&
      (!completed || (calls && (unsigned)callindex != planned))) {
    fprintf(stderr,
            "call plan unfinished or invalid: %d returned, budget=%llu\n",
            callindex, max);
    return 4;
  }
  return 0;
}
