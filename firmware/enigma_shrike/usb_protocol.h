// USB serial protocol for desktop GUI communication
// JSON-based command interface

#ifndef USB_PROTOCOL_H
#define USB_PROTOCOL_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include "board_config.h"
#include "uart_protocol.h"
#include "plugboard.h"

// ============================================================================
// USB PROTOCOL INTERFACE
// ============================================================================

class USBProtocol {
public:
  // Initialize USB serial communication
  static void init();
  
  // Process incoming USB commands (non-blocking)
  // Call from main loop
  static void process();
  
  // Send status response
  static void sendStatus(const char* status, const char* message = nullptr);
  
  // Send error response
  static void sendError(const char* error);
  
  // Check if board is ready for commands
  static bool isReady();
  static void setReady(bool ready);
  
private:
  static bool ready_;
  static char rx_buffer_[MAX_MESSAGE_LENGTH];
  static size_t rx_index_;
  
  // Command handlers
  static void handlePing(JsonDocument& cmd);
  static void handleConfig(JsonDocument& cmd);
  static void handleEncrypt(JsonDocument& cmd);
  static void handleDecrypt(JsonDocument& cmd);
  static void handleReset(JsonDocument& cmd);
  static void handleStatus(JsonDocument& cmd);
  
  // Helper: Process complete message (JSON)
  static void processMessage(const char* message);
  
  // Helper: Apply plugboard configuration from JSON
  static bool applyPlugboard(JsonArray plugboard);
  
  // Helper: Transform a message through plugboard + FPGA
  static bool transformMessage(const char* message, String& result, 
                               uint8_t* final_windows);
};

#endif // USB_PROTOCOL_H
