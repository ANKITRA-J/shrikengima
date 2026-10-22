// Shrike Fi Enigma - ESP32-S3 Firmware
// Main sketch integrating FPGA loader, UART protocol, plugboard, and USB interface

#include "board_config.h"
#include "fpga_loader.h"
#include "uart_protocol.h"
#include "plugboard.h"
#include "usb_protocol.h"
#include "selftest.h"

// Global state
BoardState board_state = STATE_INIT;

void setup() {
  // Initialize USB serial first for debugging
  Serial.begin(USB_BAUD);
  delay(BOOT_DELAY_MS);
  
  DEBUG_PRINTLN("==========================================");
  DEBUG_PRINTLN("Shrike Fi Enigma - Starting");
  DEBUG_PRINTF("Firmware: %s\n", FIRMWARE_VERSION);
  DEBUG_PRINTF("Board: %s rev %s\n", BOARD_NAME, BOARD_REVISION);
  DEBUG_PRINTLN("==========================================");
  
#if DISABLE_WIRELESS
  // Disable WiFi and Bluetooth for security
  WiFi.mode(WIFI_OFF);
  btStop();
  DEBUG_PRINTLN("Wireless: DISABLED");
#endif
  
  // Detect board characteristics
  uint32_t flash_size = ESP.getFlashChipSize();
  uint32_t psram_size = ESP.getPsramSize();
  
  DEBUG_PRINTF("Flash: %u bytes\n", flash_size);
  DEBUG_PRINTF("PSRAM: %u bytes\n", psram_size);
  
  // Initialize LED
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, HIGH);  // LED on during init
  
  // Initialize subsystems
  DEBUG_PRINTLN("Initializing FPGA loader...");
  if (!FPGALoader::init()) {
    errorHalt("FPGA loader init failed");
    return;
  }
  
  // Load FPGA bitstream
  board_state = STATE_LOADING_FPGA;
  DEBUG_PRINTLN("Loading FPGA bitstream...");
  
  // NOTE: Actual loading requires Arduino FPGA library with ESP32-S3 support
  // This is a placeholder until library compatibility is verified
  // if (!FPGALoader::loadBitstream()) {
  //   errorHalt(FPGALoader::getStatus());
  //   return;
  // }
  
  DEBUG_PRINTLN("FPGA bitstream loading: PLACEHOLDER (library pending)");
  DEBUG_PRINTLN("Skipping FPGA load for compilation purposes");
  
  // FPGALoader::releaseConfigPins();
  
  // Initialize UART to FPGA
  DEBUG_PRINTLN("Initializing UART protocol...");
  UARTProtocol::init();
  
  // Initialize plugboard
  DEBUG_PRINTLN("Initializing plugboard...");
  Plugboard::init();
  
  // Initialize USB protocol
  DEBUG_PRINTLN("Initializing USB protocol...");
  USBProtocol::init();
  
#if ENABLE_SELFTEST
  // Run selftest
  board_state = STATE_RUNNING_SELFTEST;
  DEBUG_PRINTLN("==========================================");
  DEBUG_PRINTLN("Running hardware selftest...");
  DEBUG_PRINTLN("==========================================");
  
  // NOTE: Selftest requires actual FPGA hardware
  // Uncomment when FPGA is loaded and responding:
  // if (!Selftest::run()) {
  //   errorHalt(Selftest::getLastError());
  //   return;
  // }
  
  DEBUG_PRINTLN("Selftest: SKIPPED (FPGA not loaded)");
  DEBUG_PRINTLN("In production, selftest must pass before ready state");
#endif
  
  // Mark board as ready
  board_state = STATE_READY;
  USBProtocol::setReady(true);
  digitalWrite(STATUS_LED_PIN, LOW);  // LED off when ready
  
  DEBUG_PRINTLN("==========================================");
  DEBUG_PRINTLN("BOARD READY - Waiting for commands");
  DEBUG_PRINTLN("==========================================");
}

void loop() {
  // Non-blocking USB command processing
  USBProtocol::process();
  
  // Blink LED if state is uncertain
  if (!UARTProtocol::isStateCertain()) {
    static unsigned long last_blink = 0;
    if (millis() - last_blink > 500) {
      digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
      last_blink = millis();
    }
  }
  
  // Small delay to prevent tight loop
  delay(1);
}

void errorHalt(const char* error) {
  board_state = STATE_ERROR;
  USBProtocol::setReady(false);
  
  DEBUG_PRINTLN("==========================================");
  DEBUG_PRINTLN("FATAL ERROR");
  DEBUG_PRINTLN(error);
  DEBUG_PRINTLN("==========================================");
  
  USBProtocol::sendError(error);
  
  // Blink LED rapidly to indicate error
  while (true) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(100);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(100);
  }
}
