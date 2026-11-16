// Host test of rsos_link (spec/BLE_PAIRING.md B1). Prints "ok N" and exits 0, or names the failed check.
#include "rsos_link.h"
#include <stdio.h>
#include <string.h>
#include <string>

static int failed = 0, passed = 0;
#define CHECK(c) do { if (c) passed++; else { failed++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static uint32_t seq[] = {0, 111111, 123456, 654321, 999999, 42, 7};
static int si = 0;
static uint32_t scripted() { return seq[si++ % 7]; }
static uint32_t lcg_state = 1;
static uint32_t lcg() { lcg_state = lcg_state * 1664525u + 1013904223u; return lcg_state; }
static uint32_t zero() { return 0; }

static rsos::LineBuffer::Result feed(rsos::LineBuffer& b, const std::string& s) {
  rsos::LineBuffer::Result r = rsos::LineBuffer::kMore;
  for (char c : s) r = b.push(c);
  return r;
}

int main() {
  using rsos::LinkPolicy;
  // P3 window
  LinkPolicy p; p.begin(1000);
  CHECK(p.window_open(1000));
  CHECK(p.window_open(1000 + 119999));
  CHECK(!p.window_open(1000 + 120000));
  CHECK(p.on_new_bond(1000 + 120000, 0) == LinkPolicy::kRefuseClosed);
  CHECK(p.on_new_bond(1000 + 5000, 0) == LinkPolicy::kAccept);
  p.open_window(500000);                                   // USB PAIR
  CHECK(p.window_open(500000 + 60000));
  CHECK(!p.window_open(500000 + 120000));
  // millis() wrap-around
  LinkPolicy w; w.begin(0xFFFFFFFFu - 1000);
  CHECK(w.window_open(0xFFFFFFFFu));
  CHECK(w.window_open(5000));
  CHECK(!w.window_open(200000));
  // P4 failures
  LinkPolicy f; f.begin(0);
  f.on_auth_fail(10); f.on_auth_fail(20);
  CHECK(f.window_open(30));
  f.on_auth_fail(30);
  CHECK(!f.window_open(40));
  CHECK(f.on_new_bond(40, 0) == LinkPolicy::kRefuseClosed);
  f.open_window(50);
  CHECK(f.window_open(60) && f.fails() == 0);
  // FIXES_R6 B5/B6: requests and the passkey screen only in the window, and not after the failure limit
  LinkPolicy q; q.begin(0);
  CHECK(q.accept_request(1000) && q.show_passkey(1000));
  CHECK(!q.accept_request(120000) && !q.show_passkey(120000));
  q.open_window(200000); q.on_auth_fail(200001); q.on_auth_fail(200002);
  CHECK(q.accept_request(200003));
  q.on_auth_fail(200003);
  CHECK(!q.accept_request(200004) && !q.show_passkey(200004));
  for (int i = 0; i < 50; i++) q.on_auth_fail(300000 + i);   // 50 more attempts outside the window change nothing
  CHECK(!q.accept_request(300100));
  // P5 bond limit
  LinkPolicy b; b.begin(0);
  for (int i = 0; i < 4; i++) CHECK(b.on_new_bond(10, i) == LinkPolicy::kAccept);
  CHECK(b.on_new_bond(10, 4) == LinkPolicy::kRefuseFull);
  // P2 passkeys
  CHECK(!LinkPolicy::valid_passkey(0));
  CHECK(!LinkPolicy::valid_passkey(111111));
  CHECK(!LinkPolicy::valid_passkey(999999));
  CHECK(!LinkPolicy::valid_passkey(123456));
  CHECK(!LinkPolicy::valid_passkey(654321));
  CHECK(!LinkPolicy::valid_passkey(1000000));
  CHECK(LinkPolicy::valid_passkey(42));                    // shown as 000042
  CHECK(LinkPolicy::make_passkey(scripted) == 42);
  CHECK(LinkPolicy::make_passkey(zero) == 0);
  bool all_ok = true;
  for (int i = 0; i < 100000; i++) { uint32_t k = LinkPolicy::make_passkey(lcg); if (!LinkPolicy::valid_passkey(k)) all_ok = false; }
  CHECK(all_ok);
  // P6 USB-only commands
  const char* usb[] = {"PASSKEY", "PAIR", "UNPAIR", "NEWKEY", "  PAIR", "PAIR now", "PASSKEY\r"};
  for (const char* s : usb) CHECK(LinkPolicy::usb_only(s));
  const char* other[] = {"START", "LOAD 4 0.40", "PAIRS", "UNPAIRED", "HELLO", "", "XPAIR"};
  for (const char* s : other) CHECK(!LinkPolicy::usb_only(s));
  // P7 line length
  rsos::LineBuffer lb;
  CHECK(feed(lb, std::string(95, 'A') + "\n") == rsos::LineBuffer::kLine && strlen(lb.line()) == 95);
  CHECK(feed(lb, std::string(96, 'A') + "\n") == rsos::LineBuffer::kTooLong && lb.line()[0] == 0);
  CHECK(feed(lb, "START\r\n") == rsos::LineBuffer::kLine && strcmp(lb.line(), "START") == 0);   // recovers after overflow
  CHECK(feed(lb, std::string(500, 'B') + "START\n") == rsos::LineBuffer::kTooLong);           // a START hidden past the limit is not run
  printf("ok %d\n", passed);
  if (failed) { printf("failed %d\n", failed); return 1; }
  return 0;
}
