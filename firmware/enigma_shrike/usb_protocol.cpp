// USB protocol implementation

#include "usb_protocol.h"

// Static member initialization
bool USBProtocol::ready_ = false;
char USBProtocol::rx_buffer_[MAX_MESSAGE_LENGTH];
size_t USBProtocol::rx_index_ = 0;

void USBProtocol::init() {
  Serial.begin(USB_BAUD);
  rx_index_ = 0;
  ready_ = false;
  
  DEBUG_PRINTLN("USBProtocol: Initialized");
}

void USBProtocol::process() {
  // Non-blocking read
  while (Serial.available() && rx_index_ < MAX_MESSAGE_LENGTH - 1) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (rx_index_ > 0) {
        rx_buffer_[rx_index_] = '\0';
        processMessage(rx_buffer_);
        rx_index_ = 0;
      }
    } else {
      rx_buffer_[rx_index_++] = c;
    }
  }
  
  // Buffer overflow protection
  if (rx_index_ >= MAX_MESSAGE_LENGTH - 1) {
    sendError("Command too long");
    rx_index_ = 0;
  }
}

bool USBProtocol::isReady() {
  return ready_;
}

void USBProtocol::setReady(bool ready) {
  ready_ = ready;
  DEBUG_PRINTF("USBProtocol: Ready = %d\n", ready);
}

void USBProtocol::sendStatus(const char* status, const char* message) {
  StaticJsonDocument<256> doc;
  doc["status"] = status;
  if (message) doc["message"] = message;
  
  serializeJson(doc, Serial);
  Serial.println();
}

void USBProtocol::sendError(const char* error) {
  StaticJsonDocument<256> doc;
  doc["status"] = "error";
  doc["error"] = error;
  
  serializeJson(doc, Serial);
  Serial.println();
}

void USBProtocol::processMessage(const char* message) {
  DEBUG_PRINTF("USBProtocol: RX: %s\n", message);
  
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    sendError("Invalid JSON");
    return;
  }
  
  if (!doc.containsKey("cmd")) {
    sendError("Missing 'cmd' field");
    return;
  }
  
  const char* cmd = doc["cmd"];
  
  if (strcmp(cmd, "ping") == 0) {
    handlePing(doc);
  } else if (strcmp(cmd, "config") == 0) {
    handleConfig(doc);
  } else if (strcmp(cmd, "encrypt") == 0) {
    handleEncrypt(doc);
  } else if (strcmp(cmd, "decrypt") == 0) {
    handleDecrypt(doc);
  } else if (strcmp(cmd, "reset") == 0) {
    handleReset(doc);
  } else if (strcmp(cmd, "status") == 0) {
    handleStatus(doc);
  } else {
    sendError("Unknown command");
  }
}

void USBProtocol::handlePing(JsonDocument& cmd) {
  StaticJsonDocument<256> response;
  response["status"] = "ok";
  response["firmware"] = FIRMWARE_VERSION;
  response["board"] = BOARD_NAME;
  response["ready"] = ready_;
  
  uint8_t fpga_version;
  if (UARTProtocol::ping(&fpga_version)) {
    response["fpga_version"] = fpga_version;
  }
  
  serializeJson(response, Serial);
  Serial.println();
}

void USBProtocol::handleConfig(JsonDocument& cmd) {
  if (!ready_) {
    sendError("Board not ready");
    return;
  }
  
  // Extract configuration
  if (!cmd.containsKey("rotors") || !cmd.containsKey("windows") || !cmd.containsKey("rings")) {
    sendError("Missing configuration fields");
    return;
  }
  
  JsonArray rotors_arr = cmd["rotors"];
  JsonArray windows_arr = cmd["windows"];
  JsonArray rings_arr = cmd["rings"];
  
  if (rotors_arr.size() != 3 || windows_arr.size() != 3 || rings_arr.size() != 3) {
    sendError("Invalid array sizes");
    return;
  }
  
  uint8_t rotors[3], windows[3], rings[3];
  for (int i = 0; i < 3; i++) {
    rotors[i] = rotors_arr[i];
    windows[i] = windows_arr[i];
    rings[i] = rings_arr[i];
    
    // Validate ranges
    if (rotors[i] > 4 || windows[i] > 25 || rings[i] > 25) {
      sendError("Value out of range");
      return;
    }
  }
  
  // Validate distinct rotors
  if (rotors[0] == rotors[1] || rotors[0] == rotors[2] || rotors[1] == rotors[2]) {
    sendError("Rotors must be distinct");
    return;
  }
  
  // Configure plugboard if provided
  if (cmd.containsKey("plugboard")) {
    Plugboard::clear();
    if (!applyPlugboard(cmd["plugboard"])) {
      sendError("Invalid plugboard configuration");
      return;
    }
  }
  
  // Send to FPGA
  if (!UARTProtocol::config(rotors, windows, rings)) {
    sendError("FPGA configuration failed");
    return;
  }
  
  StaticJsonDocument<256> response;
  response["status"] = "ok";
  response["windows"] = windows_arr;
  
  serializeJson(response, Serial);
  Serial.println();
}

void USBProtocol::handleEncrypt(JsonDocument& cmd) {
  if (!ready_) {
    sendError("Board not ready");
    return;
  }
  
  if (!cmd.containsKey("message")) {
    sendError("Missing message field");
    return;
  }
  
  const char* message = cmd["message"];
  String result;
  uint8_t final_windows[3];
  
  if (!transformMessage(message, result, final_windows)) {
    sendError("Encryption failed");
    return;
  }
  
  StaticJsonDocument<512> response;
  response["status"] = "ok";
  response["result"] = result;
  
  JsonArray windows_arr = response.createNestedArray("windows");
  windows_arr.add(final_windows[0]);
  windows_arr.add(final_windows[1]);
  windows_arr.add(final_windows[2]);
  
  serializeJson(response, Serial);
  Serial.println();
}

void USBProtocol::handleDecrypt(JsonDocument& cmd) {
  // Encryption and decryption are the same in Enigma
  handleEncrypt(cmd);
}

void USBProtocol::handleReset(JsonDocument& cmd) {
  if (!UARTProtocol::reset()) {
    sendError("FPGA reset failed");
    return;
  }
  
  Plugboard::clear();
  sendStatus("ok", "Reset complete");
}

void USBProtocol::handleStatus(JsonDocument& cmd) {
  uint8_t windows[3];
  bool state_ok = UARTProtocol::readState(windows);
  
  StaticJsonDocument<256> response;
  response["status"] = "ok";
  response["ready"] = ready_;
  response["state_certain"] = UARTProtocol::isStateCertain();
  
  if (state_ok) {
    JsonArray windows_arr = response.createNestedArray("windows");
    windows_arr.add(windows[0]);
    windows_arr.add(windows[1]);
    windows_arr.add(windows[2]);
  }
  
  serializeJson(response, Serial);
  Serial.println();
}

bool USBProtocol::applyPlugboard(JsonArray plugboard) {
  for (JsonVariant pair : plugboard) {
    const char* pair_str = pair;
    if (strlen(pair_str) != 2) {
      return false;
    }
    
    if (!Plugboard::setPair(pair_str[0], pair_str[1])) {
      return false;
    }
  }
  
  return Plugboard::isValid();
}

bool USBProtocol::transformMessage(const char* message, String& result, 
                                    uint8_t* final_windows) {
  result = "";
  
  for (size_t i = 0; message[i] != '\0'; i++) {
    char c = toupper(message[i]);
    
    if (c < 'A' || c > 'Z') {
      // Skip non-letters
      continue;
    }
    
    // Apply input plugboard
    char plugged_in = Plugboard::map(c);
    uint8_t contact_in = plugged_in - 'A';
    
    // Transform through FPGA
    uint8_t contact_out;
    if (!UARTProtocol::transform(contact_in, &contact_out, final_windows)) {
      return false;
    }
    
    // Apply output plugboard
    char plugged_out = Plugboard::map('A' + contact_out);
    result += plugged_out;
  }
  
  return true;
}
