// UART protocol implementation

#include "uart_protocol.h"

// Static member initialization
uint8_t UARTProtocol::sequence_ = 0;
bool UARTProtocol::state_certain_ = true;
unsigned long UARTProtocol::last_command_time_ = 0;

// Hardware Serial for FPGA communication
#define FPGA_SERIAL Serial2

void UARTProtocol::init() {
  // Initialize UART to FPGA
  FPGA_SERIAL.begin(FPGA_UART_BAUD, SERIAL_8N1, FPGA_UART_RX, FPGA_UART_TX);
  FPGA_SERIAL.setTimeout(PACKET_TIMEOUT_MS);
  
  sequence_ = 0;
  state_certain_ = true;
  
  DEBUG_PRINTLN("UARTProtocol: Initialized");
  
  // Clear any garbage in buffer
  clearRxBuffer();
}

bool UARTProtocol::ping(uint8_t* version) {
  uint8_t status;
  uint8_t data[9];
  uint8_t data_len;
  
  if (!sendRequest(OP_PING, nullptr, 0)) {
    return false;
  }
  
  if (!receiveResponse(OP_PING, &status, data, &data_len)) {
    markStateUncertain();
    return false;
  }
  
  if (status != STATUS_OK || data_len != 4) {
    return false;
  }
  
  // Response: "ENG" + version
  if (data[0] == 'E' && data[1] == 'N' && data[2] == 'G') {
    *version = data[3];
    return true;
  }
  
  return false;
}

bool UARTProtocol::config(uint8_t rotors[3], uint8_t windows[3], uint8_t rings[3]) {
  uint8_t payload[9];
  uint8_t status;
  uint8_t resp_data[9];
  uint8_t resp_len;
  
  // Build payload: rotor_L, rotor_M, rotor_R, win_L, win_M, win_R, ring_L, ring_M, ring_R
  for (int i = 0; i < 3; i++) {
    payload[i] = rotors[i];
    payload[i + 3] = windows[i];
    payload[i + 6] = rings[i];
  }
  
  if (!sendRequest(OP_CONFIG, payload, 9)) {
    return false;
  }
  
  if (!receiveResponse(OP_CONFIG, &status, resp_data, &resp_len)) {
    markStateUncertain();
    return false;
  }
  
  if (status != STATUS_OK || resp_len != 3 || resp_data[0] > 25 || resp_data[1] > 25 || resp_data[2] > 25) {
    markStateUncertain();
    return false;
  }
  
  if (memcmp(windows, resp_data, 3) != 0) {
    markStateUncertain();
    return false;
  }
  // Response contains current windows
  windows[0] = resp_data[0];
  windows[1] = resp_data[1];
  windows[2] = resp_data[2];
  
  // After successful config, state is certain
  state_certain_ = true;
  
  return true;
}

bool UARTProtocol::transform(uint8_t contact, uint8_t* result, uint8_t windows[3]) {
  if (!state_certain_ || contact > 25) return false;
  uint8_t payload[1] = {contact};
  uint8_t status;
  uint8_t resp_data[9];
  uint8_t resp_len;
  
  if (!sendRequest(OP_TRANSFORM, payload, 1)) {
    return false;
  }
  
  if (!receiveResponse(OP_TRANSFORM, &status, resp_data, &resp_len)) {
    markStateUncertain();
    return false;
  }
  
  if (status == STATUS_BUSY) {
    DEBUG_PRINTLN("UARTProtocol: FPGA busy");
    return false;
  }
  
  if (status != STATUS_OK || resp_len != 4 || resp_data[0] > 25 || resp_data[1] > 25 || resp_data[2] > 25 || resp_data[3] > 25) {
    markStateUncertain();
    return false;
  }
  
  // Response: result contact + 3 final windows
  *result = resp_data[0];
  windows[0] = resp_data[1];
  windows[1] = resp_data[2];
  windows[2] = resp_data[3];
  
  return true;
}

bool UARTProtocol::readState(uint8_t windows[3]) {
  uint8_t status;
  uint8_t resp_data[9];
  uint8_t resp_len;
  
  if (!sendRequest(OP_READ_STATE, nullptr, 0)) {
    return false;
  }
  
  if (!receiveResponse(OP_READ_STATE, &status, resp_data, &resp_len)) {
    markStateUncertain();
    return false;
  }
  
  if (status != STATUS_OK || resp_len != 3 || resp_data[0] > 25 || resp_data[1] > 25 || resp_data[2] > 25) {
    markStateUncertain();
    return false;
  }
  
  windows[0] = resp_data[0];
  windows[1] = resp_data[1];
  windows[2] = resp_data[2];
  
  return true;
}

bool UARTProtocol::reset() {
  uint8_t status;
  uint8_t resp_data[9];
  uint8_t resp_len;
  
  if (!sendRequest(OP_RESET, nullptr, 0)) {
    return false;
  }
  
  if (!receiveResponse(OP_RESET, &status, resp_data, &resp_len)) {
    markStateUncertain();
    return false;
  }
  
  if (status != STATUS_OK || resp_len != 3 || resp_data[0] != 0 || resp_data[1] != 0 || resp_data[2] != 0) {
    markStateUncertain();
    return false;
  }

  state_certain_ = true;
  return true;
}

bool UARTProtocol::isStateCertain() {
  return state_certain_;
}

void UARTProtocol::markStateUncertain() {
  state_certain_ = false;
  DEBUG_PRINTLN("UARTProtocol: State marked UNCERTAIN");
}

bool UARTProtocol::sendRequest(uint8_t opcode, const uint8_t* payload, uint8_t payload_len) {
  uint8_t packet[16];  // Max: 1 marker + 1 version + 1 seq + 1 op + 1 len + 9 payload + 1 CRC = 15
  uint8_t idx = 0;
  
  // Build packet (CRC calculated on all except marker and CRC itself)
  packet[idx++] = PKT_REQ_MARKER;  // Marker (not in CRC)
  packet[idx++] = PKT_VERSION;     // Version
  packet[idx++] = sequence_;       // Sequence
  packet[idx++] = opcode;          // Opcode
  packet[idx++] = payload_len;     // Length
  
  // Copy payload
  for (uint8_t i = 0; i < payload_len; i++) {
    packet[idx++] = payload[i];
  }
  
  // Calculate CRC on bytes 1 through idx-1 (skip marker)
  uint8_t crc = calculateCRC(&packet[1], idx - 1);
  packet[idx++] = crc;
  
  // Send packet
  FPGA_SERIAL.write(packet, idx);
  FPGA_SERIAL.flush();
  
  last_command_time_ = millis();
  
  DEBUG_PRINTF("UARTProtocol: TX seq=%d op=%02X len=%d crc=%02X\n", 
               sequence_, opcode, payload_len, crc);
  
  // Increment sequence for next command
  sequence_++;
  
  return true;
}

bool UARTProtocol::receiveResponse(uint8_t expected_opcode, uint8_t* status, 
                                    uint8_t* data, uint8_t* data_len) {
  uint8_t byte;
  unsigned long start_time = millis();
  
  auto readByte = [&](uint8_t* out) {
    unsigned long elapsed = millis() - start_time;
    return elapsed < PACKET_TIMEOUT_MS && waitForByte(out, PACKET_TIMEOUT_MS - elapsed);
  };
  // Wait for marker
  if (!waitForByte(&byte, PACKET_TIMEOUT_MS)) {
    DEBUG_PRINTLN("UARTProtocol: RX timeout waiting for marker");
    return false;
  }
  
  if (byte != PKT_RESP_MARKER) {
    DEBUG_PRINTF("UARTProtocol: Invalid marker: %02X\n", byte);
    clearRxBuffer();
    return false;
  }
  
  // Read header
  uint8_t version, seq, opcode, length;
  
  if (!readByte(&version)) return false;
  if (!readByte(&seq)) return false;
  if (!readByte(&opcode)) return false;
  if (!readByte(&length)) return false;
  
  // Validate header
  if (version != PKT_VERSION) {
    DEBUG_PRINTF("UARTProtocol: Invalid version: %02X\n", version);
    clearRxBuffer();
    return false;
  }
  
  if (seq != static_cast<uint8_t>(sequence_ - 1)) {  // We already incremented in sendRequest
    DEBUG_PRINTF("UARTProtocol: Sequence mismatch: got %d expected %d\n", seq, sequence_ - 1);
    clearRxBuffer();
    return false;
  }
  
  if (opcode != (expected_opcode | 0x80)) {
    DEBUG_PRINTF("UARTProtocol: Opcode mismatch: got %02X expected %02X\n", opcode, expected_opcode);
    clearRxBuffer();
    return false;
  }
  
  if (length < 1 || length > 10) {  // Status + up to 9 data bytes
    DEBUG_PRINTF("UARTProtocol: Invalid length: %d\n", length);
    clearRxBuffer();
    return false;
  }
  
  // Read payload
  uint8_t payload[10];
  for (uint8_t i = 0; i < length; i++) {
    if (!readByte(&payload[i])) {
      DEBUG_PRINTLN("UARTProtocol: Timeout reading payload");
      return false;
    }
  }
  
  // Read CRC
  uint8_t rx_crc;
  if (!readByte(&rx_crc)) {
    DEBUG_PRINTLN("UARTProtocol: Timeout reading CRC");
    return false;
  }
  
  // Verify CRC (calculated on version, seq, opcode, length, payload)
  uint8_t crc_data[14];  // Max: 1 ver + 1 seq + 1 op + 1 len + 10 payload
  crc_data[0] = version;
  crc_data[1] = seq;
  crc_data[2] = opcode;
  crc_data[3] = length;
  memcpy(&crc_data[4], payload, length);
  
  uint8_t expected_crc = calculateCRC(crc_data, 4 + length);
  
  if (rx_crc != expected_crc) {
    DEBUG_PRINTF("UARTProtocol: CRC mismatch: got %02X expected %02X\n", rx_crc, expected_crc);
    clearRxBuffer();
    return false;
  }
  
  // Extract status and data
  *status = payload[0];
  *data_len = (length > 0) ? (length - 1) : 0;
  if (*data_len > 0) {
    memcpy(data, &payload[1], *data_len);
  }
  
  DEBUG_PRINTF("UARTProtocol: RX seq=%d op=%02X status=%02X len=%d\n", 
               seq, opcode, *status, *data_len);
  
  return true;
}

uint8_t UARTProtocol::calculateCRC(const uint8_t* data, size_t length) {
  uint8_t crc = CRC8_INIT;
  for (size_t i = 0; i < length; i++) {
    crc = updateCRC(crc, data[i]);
  }
  return crc;
}

uint8_t UARTProtocol::updateCRC(uint8_t crc, uint8_t byte) {
  // CRC-8 with polynomial 0x07
  crc ^= byte;
  for (uint8_t i = 0; i < 8; i++) {
    if (crc & 0x80) {
      crc = (crc << 1) ^ CRC8_POLYNOMIAL;
    } else {
      crc <<= 1;
    }
  }
  return crc;
}

bool UARTProtocol::waitForByte(uint8_t* byte, unsigned long timeout_ms) {
  unsigned long start = millis();
  while (millis() - start < timeout_ms) {
    if (FPGA_SERIAL.available()) {
      *byte = FPGA_SERIAL.read();
      return true;
    }
    delay(1);  // Small delay to prevent tight loop
  }
  return false;
}

void UARTProtocol::clearRxBuffer() {
  while (FPGA_SERIAL.available()) {
    FPGA_SERIAL.read();
  }
}
