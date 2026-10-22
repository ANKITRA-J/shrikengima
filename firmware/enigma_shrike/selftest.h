// Hardware selftest with known vectors
// Verifies FPGA communication and cipher correctness

#ifndef SELFTEST_H
#define SELFTEST_H

#include <Arduino.h>
#include "board_config.h"
#include "uart_protocol.h"

// ============================================================================
// SELFTEST INTERFACE
// ============================================================================

class Selftest {
public:
  // Run complete selftest suite
  // Returns true if all tests pass
  static bool run();
  
  // Get last error message
  static const char* getLastError();
  
private:
  static char error_message_[128];
  
  // Individual test cases
  static bool testPing();
  static bool testBasicVector();      // AAAAA -> BDZGO
  static bool testHelloWorld();       // HELLOWORLD -> ILBDAAMTAZ
  static bool testDoubleStepping();   // ADU -> ADV -> AEW -> BFX -> BFY
  static bool testStateReadback();    // Config and verify windows
  
  // Helper: Configure FPGA with test settings
  static bool configureTest(uint8_t rotors[3], uint8_t windows[3], uint8_t rings[3]);
  
  // Helper: Transform string and compare result
  static bool transformAndVerify(const char* input, const char* expected, 
                                 uint8_t* final_windows);
};

#endif // SELFTEST_H
