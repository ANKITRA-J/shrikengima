// USB API specified in docs/SPEC.md. Only the FPGA computes the cipher.
#include "usb_protocol.h"
#include "selftest.h"
#include "fpga_loader.h"
namespace {
constexpr size_t LINE_LIMIT = 4096, TEXT_LIMIT = 512;
char line[LINE_LIMIT + 1];
size_t used = 0;
bool dropping = false, ready = false;
unsigned long last_byte = 0;
int request_id = -1;
uint8_t rotors[3] = {0,1,2}, initial[3] = {0,0,0}, rings[3] = {0,0,0};
const char* rotor_names[] = {"I", "II", "III", "IV", "V"};

String positions(const uint8_t* values) {
  char s[4] = {char('A'+values[0]), char('A'+values[1]), char('A'+values[2]), 0};
  return String(s);
}
void emit(JsonDocument& doc) {
  if (request_id < 0) doc["id"] = nullptr;
  else doc["id"] = request_id;
  serializeJson(doc, Serial);
  Serial.println();
}
void fail(const char* code, const char* message, int processed = -1) {
  StaticJsonDocument<512> doc;
  doc["ok"] = false;
  JsonObject err = doc.createNestedObject("error");
  err["code"] = code;
  err["message"] = message;
  if (processed >= 0) {
    err["letters_processed"] = processed;
    err["state_certain"] = UARTProtocol::isStateCertain();
  }
  emit(doc);
}
bool allowed(JsonObject obj, const char* fields) {
  for (JsonPair item : obj) {
    String key = String("|") + item.key().c_str() + "|";
    if (!strstr(fields, key.c_str())) return false;
  }
  return true;
}
bool parsePositions(JsonVariant value, uint8_t* out) {
  if (!value.is<const char*>()) return false;
  JsonString s = value.as<JsonString>();
  if (s.size() != 3) return false;
  for (int i=0;i<3;i++) {
    if (s.c_str()[i] < 'A' || s.c_str()[i] > 'Z') return false;
    out[i] = s.c_str()[i] - 'A';
  }
  return true;
}
bool applyInitial() {
  uint8_t windows[3]; memcpy(windows, initial, 3);
  return UARTProtocol::config(rotors, windows, rings);
}
void settings(JsonDocument& doc) {
  auto r = doc.createNestedArray("rotors");
  for (auto id : rotors) r.add(rotor_names[id]);
  doc["initial_positions"] = positions(initial);
  doc["rings"] = positions(rings);
  auto p = doc.createNestedArray("plugs");
  for (uint8_t i=0;i<Plugboard::getPairCount();i++) {
    char pair[3] = {}; Plugboard::getPair(i, &pair[0], &pair[1]); p.add(String(pair));
  }
}
}
void USBProtocol::init() {
  // Hold a complete bounded JSON line even when USB delivers a burst.
  Serial.setRxBufferSize(LINE_LIMIT + 64);
  Serial.setTxBufferSize(LINE_LIMIT + 64);
  Serial.begin(USB_BAUD); used = 0; dropping = false; ready = false;
}
bool USBProtocol::isReady() { return ready; }
void USBProtocol::setReady(bool value) { ready = value; }
void USBProtocol::sendError(const char* message) { fail("NOT_READY", message); }
void USBProtocol::process() {
  if (used && millis() - last_byte >= 2000) {
    used = 0; request_id = -1; fail("BAD_JSON", "Partial line timed out");
  }
  while (Serial.available()) {
    char c = Serial.read(); last_byte = millis();
    if (dropping) { if (c == '\n') dropping = false; continue; }
    if (c == '\n') {
      line[used] = 0;
      if (used) processMessage(line);
      used = 0;
    } else if (used == LINE_LIMIT) {
      used = 0; dropping = true; request_id = -1; fail("TOO_LONG", "JSON line exceeds 4096 bytes");
    } else if (c == '\0') {
      used = 0; dropping = true; request_id = -1; fail("BAD_JSON", "NUL in JSON line");
    } else line[used++] = c;
  }
}
void USBProtocol::processMessage(const char* message) {
  request_id = -1;
  DynamicJsonDocument doc(8192);
  if (deserializeJson(doc, message) || !doc.is<JsonObject>()) { fail("BAD_JSON", "Expected a JSON object"); return; }
  JsonVariant id = doc["id"];
  if (!id.is<int>() || id.is<bool>() || id.as<int>() < 0 || id.as<int>() > 65535) {
    fail("INVALID_REQUEST", "id must be an integer from 0 to 65535"); return;
  }
  request_id = id.as<int>();
  if (!doc["cmd"].is<const char*>()) { fail("INVALID_REQUEST", "cmd must be a string"); return; }
  const char* cmd = doc["cmd"];
  // Reject embedded NULs, which strcmp would otherwise silently truncate.
  if (doc["cmd"].as<JsonString>().size() != strlen(cmd)) { fail("INVALID_REQUEST", "Invalid command"); return; }
  const bool configure = strcmp(cmd,"configure") == 0;
  const bool process = strcmp(cmd,"process") == 0;
  if (!allowed(doc.as<JsonObject>(), configure ? "|id||cmd||rotors||positions||rings||plugs|" :
      process ? "|id||cmd||mode||text|" : "|id||cmd|")) {
    fail("INVALID_REQUEST", "Unknown field"); return;
  }
  DynamicJsonDocument response(2048);
  response["ok"] = true;
  if (!strcmp(cmd,"hello")) {
    response["firmware"] = FIRMWARE_VERSION;
    response["ready"] = ready;
    if (!ready) { response["loader_status"] = FPGALoader::getStatus(); response["selftest_status"] = Selftest::getLastError(); response["bitstream_bytes"] = FPGALoader::getBitstreamSize(); }
    response["engine"] = "fpga_enigma";
    response["max_line_bytes"] = LINE_LIMIT;
    response["max_text_bytes"] = TEXT_LIMIT;
    emit(response); return;
  }
  if (!strcmp(cmd,"status")) {
    response["ready"] = ready;
    if (!ready) { response["loader_status"] = FPGALoader::getStatus(); response["selftest_status"] = Selftest::getLastError(); response["bitstream_bytes"] = FPGALoader::getBitstreamSize(); }
    settings(response);
    uint8_t windows[3];
    if (ready && UARTProtocol::readState(windows)) response["final_positions"] = positions(windows);
    response["state_certain"] = UARTProtocol::isStateCertain();
    emit(response); return;
  }
  if (!configure && !process && strcmp(cmd,"reset") && strcmp(cmd,"selftest")) {
    fail("INVALID_REQUEST", "Unknown command"); return;
  }
  if (!ready) { fail("NOT_READY", "FPGA has not passed startup verification"); return; }
  if (configure) {
    uint8_t next_rotors[3], next_windows[3], next_rings[3];
    JsonArray ids = doc["rotors"].as<JsonArray>();
    JsonArray pairs = doc["plugs"].as<JsonArray>();
    if (ids.isNull() || ids.size()!=3 || pairs.isNull() || pairs.size()>13 ||
        !parsePositions(doc["positions"],next_windows) || !parsePositions(doc["rings"],next_rings)) {
      fail("INVALID_SETTINGS", "Invalid rotors, positions, rings or plugs"); return;
    }
    for (int i=0;i<3;i++) {
      next_rotors[i] = 255;
      for (int j=0;j<5;j++) if (ids[i].is<const char*>() && ids[i].as<String>() == rotor_names[j]) next_rotors[i]=j;
      if (next_rotors[i]==255) { fail("INVALID_SETTINGS", "Unknown rotor"); return; }
    }
    if (next_rotors[0]==next_rotors[1] || next_rotors[0]==next_rotors[2] || next_rotors[1]==next_rotors[2]) {
      fail("INVALID_SETTINGS", "Rotors must be distinct"); return;
    }
    bool seen[26] = {};
    for (JsonVariant pair : pairs) {
      if (!pair.is<const char*>() || pair.as<JsonString>().size()!=2) { fail("INVALID_SETTINGS", "Invalid plug pair"); return; }
      const char* s = pair.as<const char*>();
      if (s[0]<'A'||s[0]>'Z'||s[1]<'A'||s[1]>'Z'||s[0]==s[1]||seen[s[0]-'A']||seen[s[1]-'A']) {
        fail("INVALID_SETTINGS", "Plug pairs must be disjoint ASCII letters"); return;
      }
      seen[s[0]-'A'] = seen[s[1]-'A'] = true;
    }
    if (!UARTProtocol::config(next_rotors,next_windows,next_rings)) { fail("FPGA_PROTOCOL", "Configuration failed"); return; }
    memcpy(rotors,next_rotors,3); memcpy(initial,next_windows,3); memcpy(rings,next_rings,3);
    Plugboard::clear();
    for (JsonVariant pair : pairs) { const char* s=pair.as<const char*>(); Plugboard::setPair(s[0],s[1]); }
    settings(response); response["final_positions"] = positions(initial); emit(response); return;
  }
  if (!strcmp(cmd,"reset")) {
    if (!UARTProtocol::reset()) { fail("FPGA_PROTOCOL", "Reset failed"); return; }
    for (int i=0;i<3;i++) { rotors[i]=i; initial[i]=0; rings[i]=0; }
    Plugboard::clear(); settings(response); response["final_positions"]="AAA"; emit(response); return;
  }
  if (!strcmp(cmd,"selftest")) {
    bool passed = Selftest::run();
    bool restored = applyInitial();
    if (!restored) ready=false;
    if (!passed || !restored) { fail("SELFTEST_FAILED", restored ? Selftest::getLastError() : "Could not restore settings"); return; }
    response["final_positions"] = positions(initial); emit(response); return;
  }
  if (!doc["text"].is<const char*>() || !doc["mode"].is<const char*>() ||
      (doc["mode"].as<String>()!="encrypt" && doc["mode"].as<String>()!="decrypt")) {
    fail("INVALID_REQUEST", "Expected mode encrypt/decrypt and text string"); return;
  }
  JsonString text = doc["text"].as<JsonString>();
  if (text.size()>TEXT_LIMIT) { fail("TOO_LONG", "Message exceeds 512 bytes"); return; }
  for (size_t i=0;i<text.size();i++) {
    uint8_t c=text.c_str()[i];
    if (!(c>=32 && c<=126) && c!='\t' && c!='\n' && c!='\r') { fail("INVALID_TEXT", "Only printable ASCII, tab, CR and LF are allowed"); return; }
  }
  // Reconfiguration is deliberate recovery; never automatically replay a letter.
  if (!applyInitial()) { fail("FPGA_PROTOCOL", "Could not restore initial settings", 0); return; }
  String result; result.reserve(text.size());
  uint8_t windows[3]; memcpy(windows,initial,3);
  int processed=0;
  for (size_t i=0;i<text.size();i++) {
    char c=text.c_str()[i]; if (c>='a'&&c<='z') c-=32;
    if (c>='A'&&c<='Z') {
      uint8_t out;
      if (!UARTProtocol::transform(Plugboard::map(c)-'A', &out, windows)) {
        UARTProtocol::markStateUncertain(); fail("FPGA_PROTOCOL", "Transform failed; reconfigure before retrying", processed); return;
      }
      result += Plugboard::map('A'+out); processed++;
    } else result += c;
  }
  uint8_t readback[3];
  if (!UARTProtocol::readState(readback) || memcmp(windows,readback,3)) {
    UARTProtocol::markStateUncertain(); fail("FPGA_PROTOCOL", "Final state verification failed", processed); return;
  }
  response["result"]=result;
  response["engine"]="fpga_enigma";
  response["initial_positions"]=positions(initial);
  response["final_positions"]=positions(windows);
  response["letters_processed"]=processed;
  emit(response);
}
