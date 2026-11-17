#include "rsos_link.h"
#include <string.h>

namespace rsos {

LinkPolicy::Decision LinkPolicy::on_new_bond(uint32_t now, int bonds_before) const {
  if (!window_open(now)) return kRefuseClosed;
  if (bonds_before >= kMaxBonds) return kRefuseFull;
  return kAccept;
}

void LinkPolicy::on_auth_fail(uint32_t now) {
  (void)now;
  if (++fails_ >= kMaxFails) open_ = false;
}

bool LinkPolicy::valid_passkey(uint32_t pk) {
  if (pk == 0 || pk > 999999) return false;
  if (pk == 123456 || pk == 654321 || pk == 12345) return false;   // 012345 shown as six digits
  uint32_t d = pk % 10, x = pk;
  bool same = true;
  for (int i = 0; i < 6; i++) { if (x % 10 != d) same = false; x /= 10; }
  return !same;
}

uint32_t LinkPolicy::make_passkey(uint32_t (*rnd)()) {
  for (int i = 0; i < 1000; i++) {
    uint32_t pk = rnd() % 1000000;
    if (valid_passkey(pk)) return pk;
  }
  return 0;   // the caller treats 0 as "no passkey" and keeps the link closed
}

bool LinkPolicy::usb_only(const char* line) {
  static const char* const kCmds[] = {"PASSKEY", "PAIR", "UNPAIR", "NEWKEY"};
  while (*line == ' ' || *line == '\t') line++;
  for (const char* c : kCmds) {
    size_t n = strlen(c);
    if (strncmp(line, c, n) == 0 && (line[n] == 0 || line[n] == ' ' || line[n] == '\t' || line[n] == '\r')) return true;
  }
  return false;
}

LineBuffer::Result LineBuffer::push(char c) {
  if (c == '\r') return kMore;
  if (c == '\n') {
    bool over = over_;
    buf_[n_] = 0; n_ = 0; over_ = false;
    if (over) { buf_[0] = 0; return kTooLong; }
    return kLine;
  }
  if (over_) return kMore;
  if (n_ >= kMax) { over_ = true; return kMore; }
  buf_[n_++] = c;
  return kMore;
}

}  // namespace rsos
