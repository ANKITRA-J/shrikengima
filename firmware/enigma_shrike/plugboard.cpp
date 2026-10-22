// Plugboard implementation

#include "plugboard.h"

// Static member initialization
uint8_t Plugboard::mapping_[ALPHABET_SIZE];
uint8_t Plugboard::pair_count_ = 0;

void Plugboard::init() {
  // Identity mapping: A->A, B->B, etc.
  for (uint8_t i = 0; i < ALPHABET_SIZE; i++) {
    mapping_[i] = i;
  }
  pair_count_ = 0;
  
  DEBUG_PRINTLN("Plugboard: Initialized to identity");
}

bool Plugboard::setPair(char a, char b) {
  uint8_t ca = charToContact(toupper(a));
  uint8_t cb = charToContact(toupper(b));
  
  if (!validatePair(ca, cb)) {
    return false;
  }
  
  // Check if either letter already has a pair
  if (mapping_[ca] != ca || mapping_[cb] != cb) {
    DEBUG_PRINTF("Plugboard: Letter already paired: %c or %c\n", a, b);
    return false;
  }
  
  // Set bidirectional mapping
  mapping_[ca] = cb;
  mapping_[cb] = ca;
  pair_count_++;
  
  DEBUG_PRINTF("Plugboard: Set pair %c<->%c\n", contactToChar(ca), contactToChar(cb));
  
  return true;
}

void Plugboard::clear() {
  init();
}

char Plugboard::map(char letter) {
  uint8_t contact = charToContact(toupper(letter));
  uint8_t mapped = mapping_[contact];
  return contactToChar(mapped);
}

bool Plugboard::isValid() {
  // Check that mapping is symmetric
  for (uint8_t i = 0; i < ALPHABET_SIZE; i++) {
    uint8_t mapped = mapping_[i];
    if (mapping_[mapped] != i) {
      return false;  // Not symmetric
    }
  }
  return true;
}

uint8_t Plugboard::getPairCount() {
  return pair_count_;
}

bool Plugboard::getPair(uint8_t index, char* a, char* b) {
  if (index >= pair_count_) {
    return false;
  }
  
  uint8_t found = 0;
  for (uint8_t i = 0; i < ALPHABET_SIZE; i++) {
    if (mapping_[i] != i && mapping_[i] > i) {  // Only count each pair once
      if (found == index) {
        *a = contactToChar(i);
        *b = contactToChar(mapping_[i]);
        return true;
      }
      found++;
    }
  }
  
  return false;
}

uint8_t Plugboard::charToContact(char c) {
  c = toupper(c);
  if (c >= 'A' && c <= 'Z') {
    return c - 'A';
  }
  return 0;  // Default to A
}

char Plugboard::contactToChar(uint8_t contact) {
  if (contact < ALPHABET_SIZE) {
    return 'A' + contact;
  }
  return 'A';  // Default
}

bool Plugboard::validatePair(uint8_t a, uint8_t b) {
  // Check range
  if (a >= ALPHABET_SIZE || b >= ALPHABET_SIZE) {
    return false;
  }
  
  // No self-connections
  if (a == b) {
    DEBUG_PRINTLN("Plugboard: Self-connection not allowed");
    return false;
  }
  
  // Check max pairs
  if (pair_count_ >= MAX_PLUGBOARD_PAIRS) {
    DEBUG_PRINTLN("Plugboard: Maximum pairs reached");
    return false;
  }
  
  return true;
}
