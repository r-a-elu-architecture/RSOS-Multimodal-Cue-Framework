"""spec/BLE_PAIRING.md acceptance B1 and B3: the pairing policy on the host, and static checks on the ESP32 sketch."""
import pathlib
import re
import shutil
import subprocess
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
CORE = REPO / "firmware/rsos_core"
SKETCH_DIR = REPO / "firmware/esp32/rsos_esp32"
SKETCH = (SKETCH_DIR / "rsos_esp32.ino").read_text(encoding="utf-8")


@unittest.skipUnless(shutil.which("g++") or shutil.which("c++"), "no C++ compiler")
class Policy(unittest.TestCase):
    def test_link_policy_host_test(self):   # B1
        subprocess.run(["make", "-s", "-C", str(CORE), "link_test"], check=True)
        r = subprocess.run([str(CORE / "link_test")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"^ok \d+")


class Sketch(unittest.TestCase):   # B3
    def test_copies_identical(self):
        for f in ("rsos_link.h", "rsos_link.cpp"):
            self.assertEqual((CORE / f).read_bytes(), (SKETCH_DIR / f).read_bytes(), f)

    def test_rx_and_tx_descriptor_need_an_authenticated_link(self):
        self.assertIn("rx->setAccessPermissions(ESP_GATT_PERM_WRITE_ENC_MITM)", SKETCH)
        self.assertIn("cccd->setAccessPermissions(ESP_GATT_PERM_READ_ENC_MITM | ESP_GATT_PERM_WRITE_ENC_MITM)", SKETCH)
        self.assertIn("ESP_LE_AUTH_REQ_SC_MITM_BOND", SKETCH)
        self.assertIn("ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH_ENABLE", SKETCH)
        self.assertNotRegex(SKETCH, r"ESP_GATT_PERM_WRITE(?!_ENC_MITM)\b")

    def test_lines_need_an_authenticated_link(self):
        on_write = SKETCH[SKETCH.index("void onWrite"):SKETCH.index("int bondCount")]
        self.assertIn("if (!linkAuthed) return;", on_write)
        self.assertIn("bleConnected && linkAuthed && txChar", SKETCH)

    def test_passkey_never_on_bluetooth(self):
        sends = re.findall(r"(?:sendLine|hw\.send|txChar->setValue|core\.line)\([^;]*;", SKETCH)
        self.assertTrue(sends)
        for s in sends:
            self.assertNotIn("passkey", s.lower(), s)
        usb = SKETCH[SKETCH.index("void usbCommand"):SKETCH.index("void onLine")]
        self.assertNotIn("sendLine", usb)

    def test_usb_only_commands_refused_over_bluetooth(self):
        on_line = SKETCH[SKETCH.index("void onLine"):]
        self.assertIn('if (src == rsos::kUsb) usbCommand(line, now);\n    else sendLine("ERR LINK usb-only");', on_line)

    def test_no_unbounded_line_buffers(self):
        self.assertNotIn("bleLine +=", SKETCH)
        self.assertNotIn("serialLine +=", SKETCH)


if __name__ == "__main__":
    unittest.main()


class FixesR6(unittest.TestCase):   # spec/FIXES_R6.md §5
    def test_requests_answered_only_in_the_window(self):   # B5
        self.assertIn("case ESP_GAP_BLE_SEC_REQ_EVT:", SKETCH)
        self.assertIn("esp_ble_gap_security_rsp(param->ble_security.ble_req.bd_addr, link.accept_request(millis()));", SKETCH)

    def test_passkey_shown_only_in_the_window(self):   # B6
        self.assertIn("if (link.show_passkey(millis())) keyScreen = 1;", SKETCH)
        self.assertNotIn("case ESP_GAP_BLE_PASSKEY_NOTIF_EVT: keyScreen = 1;", SKETCH)

    def test_no_key_exchange_only_for_known_hosts(self):   # B7
        self.assertIn("} else if (!bonded(param->ble_security.auth_cmpl.bd_addr)) {", SKETCH)

    def test_receive_line_works_on_2x_and_3x(self):   # B8
        self.assertIn("String v = c->getValue().c_str();", SKETCH)
        stub = (REPO / "firmware/esp32/stubs/BLEDevice.h").read_text(encoding="utf-8")
        self.assertIn("String getValue()", stub)
        self.assertIn("std::string getValue()", stub)
        self.assertNotIn("String(const std::string", (REPO / "firmware/esp32/stubs/Arduino.h").read_text(encoding="utf-8"))

    def test_ring_emptied_on_link_loss(self):   # B9
        self.assertIn("rxTail = rxHead; }", SKETCH)
        self.assertIn("writeValueWithResponse", (REPO / "docs/js/rdp.js").read_text(encoding="utf-8"))
