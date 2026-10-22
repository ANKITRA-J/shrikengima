// UART protocol for communication with FPGA
// Implements packet format from specification Section 5

#ifndef UART_PROTOCOL_H
#define UART_PROTOCOL_H

#include <Arduino.h>
#include "board_config.h"

// ============================================================================
// UART PROTOCOL INTERFACE
// ============================================================================

class UARTProtocol {
public:
  // Initialize UART communication with FPGA
  static void init();
  
  // Send PING command, returns FPGA version
  static bool ping(uint8_t* version);
  
  // Configure rotors, windows, and rings
  // rotors: 3 bytes (0-4 each, must be distinct)
  // windows: 3 bytes (0-25 each)
  // rings: 3 bytes (0-25 each)
  // Returns current windows in windows parameter
  static bool config(uint8_t rotors[3], uint8_t windows[3], uint8_t rings[3]);
  
  // Transform a single contact (0-25)
  // Returns result contact and final windows
  static bool transform(uint8_t contact, uint8_t* result, uint8_t windows[3]);
  
  // Read current state (windows)
  static bool readState(uint8_t windows[3]);
  
  // Reset FPGA to default state
  static bool reset();
  
  // Check if state is certain (no timeouts since last config)
  static bool isStateCertain();
  
  // Mark state as uncertain (after timeout)
  static void markStateUncertain();
  
private:
  static uint8_t sequence_;
  static bool state_certain_;
  static unsigned long last_command_time_;
  
  // Build and send request packet
  static bool sendRequest(uint8_t opcode, const uint8_t* payload, uint8_t payload_len);
  
  // Receive and validate response packet
  static bool receiveResponse(uint8_t expected_opcode, uint8_t* status, 
                              uint8_t* data, uint8_t* data_len);
  
  // CRC-8 calculation (polynomial 0x07)
  static uint8_t calculateCRC(const uint8_t* data, size_t length);
  static uint8_t updateCRC(uint8_t crc, uint8_t byte);
  
  // Wait for response with timeout
  static bool waitForByte(uint8_t* byte, unsigned long timeout_ms);
  
  // Clear UART receive buffer
  static void clearRxBuffer();
};

#endif // UART_PROTOCOL_H
