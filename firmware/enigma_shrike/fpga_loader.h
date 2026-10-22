// FPGA bitstream loader for Shrike Fi
// Loads bitstream from filesystem and manages configuration

#ifndef FPGA_LOADER_H
#define FPGA_LOADER_H

#include <Arduino.h>
#include "board_config.h"

// ============================================================================
// FPGA LOADER INTERFACE
// ============================================================================

class FPGALoader {
public:
  // Initialize FPGA loader subsystem
  static bool init();
  
  // Load bitstream from filesystem
  // Returns true on success, false on failure
  static bool loadBitstream(const char* path = FPGA_BITSTREAM_PATH);
  
  // Check if FPGA is configured and responding
  static bool isConfigured();
  
  // Release configuration pins (allow FPGA runtime operation)
  static void releaseConfigPins();
  
  // Get loader status information
  static const char* getStatus();
  static uint32_t getBitstreamSize();
  
private:
  static bool configured_;
  static uint32_t bitstream_size_;
  static char status_message_[128];
  
  // Verify bitstream metadata
  static bool verifyBitstream(const uint8_t* data, size_t length);
};

#endif // FPGA_LOADER_H
