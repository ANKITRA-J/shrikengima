// Selftest implementation

#include "selftest.h"
#include "plugboard.h"

// Static member initialization
char Selftest::error_message_[128] = "No error";

bool Selftest::run() {
  DEBUG_PRINTLN("Selftest: Starting hardware verification...");
  
  // Test 1: FPGA communication
  if (!testPing()) {
    snprintf(error_message_, sizeof(error_message_), "PING test failed");
    DEBUG_PRINTLN(error_message_);
    return false;
  }
  
  // Test 2: Basic vector (AAAAA -> BDZGO)
  if (!testBasicVector()) {
    snprintf(error_message_, sizeof(error_message_), "Basic vector test failed");
    DEBUG_PRINTLN(error_message_);
    return false;
  }
  
  // Test 3: HELLOWORLD vector
  if (!testHelloWorld()) {
    snprintf(error_message_, sizeof(error_message_), "HELLOWORLD test failed");
    DEBUG_PRINTLN(error_message_);
    return false;
  }
  
  // Test 4: Double stepping
  if (!testDoubleStepping()) {
    snprintf(error_message_, sizeof(error_message_), "Double stepping test failed");
    DEBUG_PRINTLN(error_message_);
    return false;
  }
  
  // Test 5: State readback
  if (!testStateReadback()) {
    snprintf(error_message_, sizeof(error_message_), "State readback test failed");
    DEBUG_PRINTLN(error_message_);
    return false;
  }
  
  DEBUG_PRINTLN("Selftest: All tests PASSED");
  snprintf(error_message_, sizeof(error_message_), "All tests passed");
  
  return true;
}

const char* Selftest::getLastError() {
  return error_message_;
}

bool Selftest::testPing() {
  DEBUG_PRINTLN("Selftest: Testing PING...");
  
  uint8_t version;
  if (!UARTProtocol::ping(&version)) {
    return false;
  }
  
  DEBUG_PRINTF("Selftest: FPGA version: 0x%02X\n", version);
  
  if (version != PKT_VERSION) {
    DEBUG_PRINTF("Selftest: Version mismatch (expected 0x%02X)\n", PKT_VERSION);
    return false;
  }
  
  return true;
}

bool Selftest::testBasicVector() {
  DEBUG_PRINTLN("Selftest: Testing AAAAA -> BDZGO...");
  
  // Rotors I II III (0 1 2), AAA windows (0 0 0), AAA rings (0 0 0)
  uint8_t rotors[3] = {0, 1, 2};
  uint8_t windows[3] = {0, 0, 0};
  uint8_t rings[3] = {0, 0, 0};
  
  if (!configureTest(rotors, windows, rings)) {
    return false;
  }
  
  // Transform AAAAA, expect BDZGO
  uint8_t final_windows[3];
  if (!transformAndVerify("AAAAA", "BDZGO", final_windows)) {
    return false;
  }
  
  // Verify final windows: AAE (0 0 4)
  if (final_windows[0] != 0 || final_windows[1] != 0 || final_windows[2] != 4) {
    DEBUG_PRINTF("Selftest: Window mismatch: got %d %d %d, expected 0 0 4\n",
                 final_windows[0], final_windows[1], final_windows[2]);
    return false;
  }
  
  DEBUG_PRINTLN("Selftest: AAAAA -> BDZGO PASSED");
  return true;
}

bool Selftest::testHelloWorld() {
  DEBUG_PRINTLN("Selftest: Testing HELLOWORLD -> ILBDAAMTAZ...");
  
  // Reset to AAA
  uint8_t rotors[3] = {0, 1, 2};
  uint8_t windows[3] = {0, 0, 0};
  uint8_t rings[3] = {0, 0, 0};
  
  if (!configureTest(rotors, windows, rings)) {
    return false;
  }
  
  // Transform HELLOWORLD, expect ILBDAAMTAZ
  uint8_t final_windows[3];
  if (!transformAndVerify("HELLOWORLD", "ILBDAAMTAZ", final_windows)) {
    return false;
  }
  
  DEBUG_PRINTLN("Selftest: HELLOWORLD -> ILBDAAMTAZ PASSED");
  return true;
}

bool Selftest::testDoubleStepping() {
  DEBUG_PRINTLN("Selftest: Testing double stepping...");
  
  // Configure to ADU (windows: 0 3 20)
  uint8_t rotors[3] = {0, 1, 2};
  uint8_t windows[3] = {0, 3, 20};
  uint8_t rings[3] = {0, 0, 0};
  
  if (!configureTest(rotors, windows, rings)) {
    return false;
  }
  
  // Expected window sequences:
  // Start: A D U (0 3 20)
  // After 1: A D V (0 3 21)
  // After 2: A E W (0 4 22) - double step!
  // After 3: B F X (1 5 23) - double step again!
  // After 4: B F Y (1 5 24)
  
  uint8_t expected_windows[5][3] = {
    {0, 3, 20},  // ADU (start)
    {0, 3, 21},  // ADV
    {0, 4, 22},  // AEW (double step)
    {1, 5, 23},  // BFX (double step)
    {1, 5, 24}   // BFY
  };
  
  // Transform 4 letters and check windows after each
  for (int i = 0; i < 4; i++) {
    uint8_t result;
    uint8_t result_windows[3];
    
    if (!UARTProtocol::transform(0, &result, result_windows)) {  // Transform 'A'
      DEBUG_PRINTF("Selftest: Transform %d failed\n", i + 1);
      return false;
    }
    
    // Check windows match expected
    if (result_windows[0] != expected_windows[i + 1][0] ||
        result_windows[1] != expected_windows[i + 1][1] ||
        result_windows[2] != expected_windows[i + 1][2]) {
      DEBUG_PRINTF("Selftest: Window mismatch at step %d: got %d %d %d, expected %d %d %d\n",
                   i + 1,
                   result_windows[0], result_windows[1], result_windows[2],
                   expected_windows[i + 1][0], expected_windows[i + 1][1], expected_windows[i + 1][2]);
      return false;
    }
    
    DEBUG_PRINTF("Selftest: Step %d: %c%c%c OK\n", i + 1,
                 'A' + result_windows[0], 'A' + result_windows[1], 'A' + result_windows[2]);
  }
  
  DEBUG_PRINTLN("Selftest: Double stepping PASSED");
  return true;
}

bool Selftest::testStateReadback() {
  DEBUG_PRINTLN("Selftest: Testing state readback...");
  
  // Configure with specific settings
  uint8_t rotors[3] = {2, 0, 4};  // III I V
  uint8_t windows[3] = {10, 15, 20};  // KPU
  uint8_t rings[3] = {5, 10, 15};  // FKP
  
  if (!configureTest(rotors, windows, rings)) {
    return false;
  }
  
  // Read back state
  uint8_t read_windows[3];
  if (!UARTProtocol::readState(read_windows)) {
    DEBUG_PRINTLN("Selftest: State readback failed");
    return false;
  }
  
  // Verify windows match
  if (read_windows[0] != windows[0] ||
      read_windows[1] != windows[1] ||
      read_windows[2] != windows[2]) {
    DEBUG_PRINTF("Selftest: Readback mismatch: got %d %d %d, expected %d %d %d\n",
                 read_windows[0], read_windows[1], read_windows[2],
                 windows[0], windows[1], windows[2]);
    return false;
  }
  
  DEBUG_PRINTLN("Selftest: State readback PASSED");
  return true;
}

bool Selftest::configureTest(uint8_t rotors[3], uint8_t windows[3], uint8_t rings[3]) {
  uint8_t result_windows[3];
  
  if (!UARTProtocol::config(rotors, windows, rings)) {
    DEBUG_PRINTLN("Selftest: Configuration failed");
    return false;
  }
  
  // Verify windows were set correctly
  if (!UARTProtocol::readState(result_windows)) {
    DEBUG_PRINTLN("Selftest: Readback after config failed");
    return false;
  }
  
  if (result_windows[0] != windows[0] ||
      result_windows[1] != windows[1] ||
      result_windows[2] != windows[2]) {
    DEBUG_PRINTLN("Selftest: Config window mismatch");
    return false;
  }
  
  return true;
}

bool Selftest::transformAndVerify(const char* input, const char* expected, 
                                   uint8_t* final_windows) {
  size_t len = strlen(input);
  
  for (size_t i = 0; i < len; i++) {
    char c = toupper(input[i]);
    if (c < 'A' || c > 'Z') continue;  // Skip non-letters
    
    uint8_t contact = c - 'A';
    uint8_t result;
    
    if (!UARTProtocol::transform(contact, &result, final_windows)) {
      DEBUG_PRINTF("Selftest: Transform failed at position %d\n", i);
      return false;
    }
    
    char result_char = 'A' + result;
    char expected_char = toupper(expected[i]);
    
    if (result_char != expected_char) {
      DEBUG_PRINTF("Selftest: Mismatch at position %d: got %c, expected %c\n",
                   i, result_char, expected_char);
      return false;
    }
  }
  
  return true;
}
