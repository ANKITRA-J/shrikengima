#ifndef USB_PROTOCOL_H
#define USB_PROTOCOL_H
#include <Arduino.h>
#include <ArduinoJson.h>
#include "board_config.h"
#include "uart_protocol.h"
#include "plugboard.h"
class USBProtocol {
public:
  static void init();
  static void process();
  static bool isReady();
  static void setReady(bool ready);
  static void sendError(const char* error);
private:
  static void processMessage(const char* message);
};
#endif
