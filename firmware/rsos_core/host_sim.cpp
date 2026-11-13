// Host simulator for the RDP/1 device core: reads protocol lines on stdin, writes device lines on
// stdout. Time is simulated: `TICK <t>` advances the device clock to t ms. Used by the conformance
// suite (rsso/rsso/protocol.py) to test the exact firmware logic without hardware.
#include <stdio.h>
#include <string.h>

#include "rsos_core.h"

class StdoutOutput : public rsos::Output {
 public:
  void motor(float) override {}
  void valve(char, bool) override {}
  void send(const char* line) override { printf("%s\n", line); fflush(stdout); }
};

int main(int argc, char** argv) {
  const char* caps = argc > 1 ? argv[1] : "haptic,olfactory,gustatory";  // RDP/1.1 rigs add thermal,display
  StdoutOutput out;
  rsos::Core core(out, caps, 1.0f);
  char buf[128];
  unsigned long now = 0;
  while (fgets(buf, sizeof buf, stdin)) {
    buf[strcspn(buf, "\r\n")] = 0;
    unsigned long t;
    if (sscanf(buf, "TICK %lu", &t) == 1) {
      if (t > now) now = t;
      core.update((uint32_t)now);
      printf("TOCK %lu\n", now); fflush(stdout);
    } else if (!strcmp(buf, "LINK_LOST")) {
      core.link_lost((uint32_t)now);
    } else if (!strcmp(buf, "QUIT")) {
      break;
    } else if (buf[0]) {
      core.line(buf, (uint32_t)now);
    }
  }
  return 0;
}
