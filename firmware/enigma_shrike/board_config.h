// Board configuration for Shrike Fi (ESP32-S3)
// Pin mappings, hardware settings, and constants

#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

#include <Arduino.h>

// ============================================================================
// BOARD IDENTIFICATION
// ============================================================================

#define BOARD_NAME "Shrike Fi"
#define FIRMWARE_VERSION "1.0.0"
#define BOARD_REVISION "A"  // Update based on actual board revision

// ============================================================================
// PIN DEFINITIONS (ESP32-S3 to FPGA)
// ============================================================================

// UART to FPGA (Hardware Serial2)
// ESP32 GPIO11 -> FPGA Pin 6 (FPGA TX, our RX)
// ESP32 GPIO13 -> FPGA Pin 5 (FPGA RX, our TX)
#define FPGA_UART_RX 11
#define FPGA_UART_TX 13
#define FPGA_UART_BAUD 115200

// FPGA Configuration Pins
// These will be managed by Arduino FPGA library
// Exact pins depend on library implementation for ESP32-S3
#define FPGA_SS_PIN 10      // SPI Chip Select (adjust per library)
#define FPGA_RESET_PIN 9    // FPGA reset (adjust per library)

// Status LED (board-specific)
#define STATUS_LED_PIN LED_BUILTIN  // Use built-in LED or specific GPIO

// ============================================================================
// UART PROTOCOL CONSTANTS (from specification Section 5)
// ============================================================================

// Packet markers
#define PKT_REQ_MARKER 0xA5
#define PKT_RESP_MARKER 0x5A
#define PKT_VERSION 0x01

// Opcodes
#define OP_PING 0x01
#define OP_CONFIG 0x02
#define OP_TRANSFORM 0x03
#define OP_READ_STATE 0x04
#define OP_RESET 0x05

// Status codes
#define STATUS_OK 0x00
#define STATUS_INVALID 0x01
#define STATUS_BUSY 0x02
#define STATUS_UNKNOWN_OP 0x03
#define STATUS_INTERNAL 0x04

// Packet constraints
#define MAX_PAYLOAD_LEN 9
#define PACKET_TIMEOUT_MS 100  // Per specification: 100ms deadline

// CRC-8 parameters
#define CRC8_POLYNOMIAL 0x07
#define CRC8_INIT 0x00
#define CRC8_CHECK_VALUE 0xF4  // For ASCII "123456789"

// ============================================================================
// SYSTEM CONSTANTS
// ============================================================================

// Alphabet
#define ALPHABET_SIZE 26

// Plugboard
#define MAX_PLUGBOARD_PAIRS 13  // 26 letters / 2

// Rotor constraints
#define NUM_ROTORS 3
#define MIN_ROTOR_ID 0
#define MAX_ROTOR_ID 4
#define MIN_POSITION 0
#define MAX_POSITION 25

// USB Serial
#define USB_BAUD 115200
#define MAX_MESSAGE_LENGTH 1024  // Bounded buffer for safety

// Timing
#define BOOT_DELAY_MS 1000
#define FPGA_LOAD_TIMEOUT_MS 10000
#define SELFTEST_TIMEOUT_MS 5000

// ============================================================================
// FLASH AND STORAGE
// ============================================================================

// Filesystem paths
#define FPGA_BITSTREAM_PATH "/fpga_bitstream.bin"
#define SETTINGS_FILE_PATH "/settings.json"

// Flash detection (do NOT assume 8MB)
// Will detect actual capacity at runtime

// ============================================================================
// FEATURE FLAGS
// ============================================================================

#define ENABLE_SELFTEST 1
#define ENABLE_SERIAL_DEBUG 1
#define DISABLE_WIRELESS 1  // Security requirement

// ============================================================================
// DEBUG MACROS
// ============================================================================

#if ENABLE_SERIAL_DEBUG
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(fmt, ...) Serial.printf(fmt, ##__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(fmt, ...)
#endif

// ============================================================================
// ERROR CODES
// ============================================================================

enum FirmwareError {
  ERR_NONE = 0,
  ERR_FPGA_LOAD_FAILED = 1,
  ERR_FPGA_NO_RESPONSE = 2,
  ERR_SELFTEST_FAILED = 3,
  ERR_UART_TIMEOUT = 4,
  ERR_INVALID_CRC = 5,
  ERR_INVALID_SEQUENCE = 6,
  ERR_INVALID_CONFIG = 7,
  ERR_STATE_UNCERTAIN = 8,
  ERR_FILESYSTEM = 9,
  ERR_JSON_PARSE = 10
};

// ============================================================================
// BOARD STATE
// ============================================================================

enum BoardState {
  STATE_INIT = 0,
  STATE_LOADING_FPGA = 1,
  STATE_RUNNING_SELFTEST = 2,
  STATE_READY = 3,
  STATE_ERROR = 4,
  STATE_UNCERTAIN = 5  // After FPGA timeout
};

#endif // BOARD_CONFIG_H
