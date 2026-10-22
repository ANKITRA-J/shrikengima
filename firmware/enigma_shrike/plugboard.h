// Plugboard substitution for Enigma
// Implements letter pair swaps with validation

#ifndef PLUGBOARD_H
#define PLUGBOARD_H

#include <Arduino.h>
#include "board_config.h"

// ============================================================================
// PLUGBOARD INTERFACE
// ============================================================================

class Plugboard {
public:
  // Initialize to identity mapping (A->A, B->B, etc.)
  static void init();
  
  // Set a plugboard pair (bidirectional swap)
  // Returns false if invalid (self-connection, overlapping pairs)
  static bool setPair(char a, char b);
  
  // Clear all pairs (reset to identity)
  static void clear();
  
  // Map a letter through the plugboard
  // Input/output: uppercase A-Z
  static char map(char letter);
  
  // Check if current configuration is valid
  static bool isValid();
  
  // Get number of active pairs
  static uint8_t getPairCount();
  
  // Get pair at index (for serialization)
  static bool getPair(uint8_t index, char* a, char* b);
  
private:
  static uint8_t mapping_[ALPHABET_SIZE];  // 0-25 mapping
  static uint8_t pair_count_;
  
  // Convert char to contact number (0-25)
  static uint8_t charToContact(char c);
  
  // Convert contact number to char (A-Z)
  static char contactToChar(uint8_t contact);
  
  // Validate a pair before setting
  static bool validatePair(uint8_t a, uint8_t b);
};

#endif // PLUGBOARD_H
