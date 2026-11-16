// Stand-ins for the ESP-IDF Bluedroid security API used by rsos_esp32.ino; compile-check only.
#pragma once
#include <stdint.h>
typedef uint8_t esp_bd_addr_t[6];
typedef uint16_t esp_gatt_perm_t;
#define ESP_GATT_PERM_READ_ENC_MITM  (1 << 2)
#define ESP_GATT_PERM_WRITE_ENC_MITM (1 << 6)
typedef enum { ESP_BLE_SEC_ENCRYPT = 1, ESP_BLE_SEC_ENCRYPT_NO_MITM, ESP_BLE_SEC_ENCRYPT_MITM } esp_ble_sec_act_t;
typedef uint8_t esp_ble_auth_req_t;
typedef uint8_t esp_ble_io_cap_t;
#define ESP_LE_AUTH_REQ_SC_MITM_BOND 0x0D
#define ESP_IO_CAP_OUT 0
#define ESP_BLE_ONLY_ACCEPT_SPECIFIED_AUTH_ENABLE 1
#define ESP_BLE_ENC_KEY_MASK (1 << 0)
#define ESP_BLE_ID_KEY_MASK (1 << 1)
typedef enum { ESP_BLE_SM_PASSKEY = 0, ESP_BLE_SM_AUTHEN_REQ_MODE, ESP_BLE_SM_IOCAP_MODE, ESP_BLE_SM_SET_INIT_KEY, ESP_BLE_SM_SET_RSP_KEY,
               ESP_BLE_SM_MAX_KEY_SIZE, ESP_BLE_SM_SET_STATIC_PASSKEY, ESP_BLE_SM_ONLY_ACCEPT_SPECIFIED_SEC_AUTH } esp_ble_sm_param_t;
typedef enum { ESP_GAP_BLE_AUTH_CMPL_EVT = 8, ESP_GAP_BLE_KEY_EVT = 9, ESP_GAP_BLE_SEC_REQ_EVT = 10, ESP_GAP_BLE_PASSKEY_NOTIF_EVT = 11 } esp_gap_ble_cb_event_t;
struct esp_ble_auth_cmpl_t { esp_bd_addr_t bd_addr; bool success; };
struct esp_ble_sec_req_t { esp_bd_addr_t bd_addr; };
union esp_ble_sec_t { esp_ble_auth_cmpl_t auth_cmpl; esp_ble_sec_req_t ble_req; };
union esp_ble_gap_cb_param_t { struct { esp_ble_sec_t ble_security; }; };
union esp_ble_gatts_cb_param_t { struct { uint16_t conn_id; esp_bd_addr_t remote_bda; } connect; };
struct esp_ble_bond_dev_t { esp_bd_addr_t bd_addr; };
inline int esp_ble_gap_set_security_param(esp_ble_sm_param_t, void*, uint8_t) { return 0; }
inline int esp_ble_gap_security_rsp(esp_bd_addr_t, bool) { return 0; }
inline int esp_ble_set_encryption(esp_bd_addr_t, esp_ble_sec_act_t) { return 0; }
inline int esp_ble_get_bond_device_num() { return 0; }
inline int esp_ble_get_bond_device_list(int*, esp_ble_bond_dev_t*) { return 0; }
inline int esp_ble_remove_bond_device(esp_bd_addr_t) { return 0; }
inline uint32_t esp_random() { return 4242; }
