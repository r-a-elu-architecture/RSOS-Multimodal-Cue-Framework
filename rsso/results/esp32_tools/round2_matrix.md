# ESP32_TOOLS round 2: the compile matrix after amendment A1 (code c4d9b8b)

arduino-cli 1.6.0, `--warnings default`. Cores 2.0.17, 3.3.12, 3.2.1 (C1b). GFX Library: 1.6.1 on 2.0.17, 1.6.9 on 3.x;
the two ESP32-S3 2.0.17 display builds failed inside GFX 1.6.1 and were rebuilt with 1.6.0 (round 2b). Flash and RAM as
arduino-cli reports them (default partition scheme: 1,310,720 bytes of program space; 327,680 bytes of RAM).

| Build | Flags | Exit | Flash (bytes, %) | Static RAM (bytes, %) | Note |
|---|---|---|---|---|---|
| esp32-2.0.17-band | — | 0 | 1,131,917 (86%) | 43,564 (13%) |  |
| esp32-2.0.17-thermal | -DRSOS_THERMAL | 0 | 1,141,277 (87%) | 43,828 (13%) |  |
| esp32-2.0.17-sites | -DRSOS_SITES | 0 | 1,149,317 (87%) | 44,028 (13%) |  |
| esp32-2.0.17-display | -DRSOS_DISPLAY | 0 | 1,226,781 (93%) | 44,540 (13%) |  |
| esp32-2.0.17-all | -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 0 | 1,250,681 (95%) | 44,916 (13%) |  |
| esp32c3-2.0.17-band | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 | 0 | 987,838 (75%) | 43,092 (13%) |  |
| esp32c3-2.0.17-thermal | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_THERMAL | 0 | 995,976 (75%) | 43,300 (13%) |  |
| esp32c3-2.0.17-sites | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_SITES | 0 | 1,005,504 (76%) | 43,444 (13%) |  |
| esp32c3-2.0.17-display | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_DISPLAY | 0 | 1,077,412 (82%) | 43,924 (13%) |  |
| esp32c3-2.0.17-all | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 0 | 1,093,410 (83%) | 44,244 (13%) |  |
| esp32s3-2.0.17-band | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 | 0 | 922,373 (70%) | 48,940 (14%) |  |
| esp32s3-2.0.17-thermal | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_THERMAL | 0 | 933,777 (71%) | 49,364 (15%) |  |
| esp32s3-2.0.17-sites | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_SITES | 0 | 939,465 (71%) | 49,380 (15%) |  |
| esp32s3-2.0.17-display | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_DISPLAY | 0 | 1,015,949 (77%) | 49,868 (15%) | round 2: exit 1 in GFX 1.6.1 (`Arduino_ESP32RGBPanel.cpp:147:3: error: 'esp_rgb_panel_t' was not declared in this scope`); round 2b with GFX 1.6.0 |
| esp32s3-2.0.17-all | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 0 | 1,041,733 (79%) | 50,412 (15%) | round 2: exit 1 in GFX 1.6.1 (`Arduino_ESP32RGBPanel.cpp:147:3: error: 'esp_rgb_panel_t' was not declared in this scope`); round 2b with GFX 1.6.0 |
| esp32-3.3.12-band | — | 0 | 1,114,030 (84%) | 46,020 (14%) |  |
| esp32-3.3.12-thermal | -DRSOS_THERMAL | 0 | 1,124,414 (85%) | 46,180 (14%) |  |
| esp32-3.3.12-sites | -DRSOS_SITES | 0 | 1,141,710 (87%) | 47,516 (14%) |  |
| esp32-3.3.12-display | -DRSOS_DISPLAY | 0 | 1,212,174 (92%) | 48,228 (14%) |  |
| esp32-3.3.12-all | -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 0 | 1,227,250 (93%) | 48,500 (14%) |  |
| esp32c3-3.3.12-band | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32c3-3.3.12-thermal | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_THERMAL | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32c3-3.3.12-sites | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_SITES | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32c3-3.3.12-display | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_DISPLAY | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32c3-3.3.12-all | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32s3-3.3.12-band | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32s3-3.3.12-thermal | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_THERMAL | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32s3-3.3.12-sites | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_SITES | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32s3-3.3.12-display | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_DISPLAY | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32s3-3.3.12-all | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 1 | — | — | stops at the F3 guard (NimBLE) |
| esp32c3-3.2.1-band | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 | 0 | 1,007,724 (76%) | 42,088 (12%) |  |
| esp32c3-3.2.1-thermal | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_THERMAL | 0 | 1,021,578 (77%) | 42,360 (12%) |  |
| esp32c3-3.2.1-sites | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_SITES | 0 | 1,038,502 (79%) | 42,880 (13%) |  |
| esp32c3-3.2.1-display | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_DISPLAY | 0 | 1,117,318 (85%) | 43,496 (13%) |  |
| esp32c3-3.2.1-all | -DRSOS_MOTOR_PIN=5 -DRSOS_SCENT_PIN=6 -DRSOS_TASTE_PIN=7 -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 0 | 1,137,750 (86%) | 43,872 (13%) |  |
| esp32s3-3.2.1-band | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 | 0 | 938,242 (71%) | 51,016 (15%) |  |
| esp32s3-3.2.1-thermal | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_THERMAL | 0 | 951,974 (72%) | 51,368 (15%) |  |
| esp32s3-3.2.1-sites | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_SITES | 0 | 966,038 (73%) | 52,480 (16%) |  |
| esp32s3-3.2.1-display | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_DISPLAY | 0 | 1,052,634 (80%) | 53,120 (16%) |  |
| esp32s3-3.2.1-all | -DRSOS_MOTOR_PIN=4 -DRSOS_SCENT_PIN=5 -DRSOS_TASTE_PIN=6 -DRSOS_THERMAL -DRSOS_SITES -DRSOS_DISPLAY | 0 | 1,071,118 (81%) | 53,576 (16%) |  |

30 of 40 builds compiled.
