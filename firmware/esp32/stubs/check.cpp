// Compile-check of the ESP32 sketch against the stubs (no hardware behaviour is tested here).
#include "Arduino.h"
SerialT Serial;
#ifdef RSOS_SITES
#include "Wire.h"
TwoWire Wire;
#endif
#ifdef RSOS_DISPLAY
#include "LittleFS.h"
LittleFSFS LittleFS;
#endif
#include "../rsos_esp32/rsos_esp32.ino"
int main() { setup(); loop(); return 0; }
