#include <WiFi.h>
#include "board_config.h"
#include "fpga_loader.h"
#include "uart_protocol.h"
#include "plugboard.h"
#include "usb_protocol.h"
#include "selftest.h"

BoardState board_state = STATE_INIT;
void setup() {
  USBProtocol::init();
  pinMode(STATUS_LED_PIN,OUTPUT);
  digitalWrite(STATUS_LED_PIN,HIGH);
#if DISABLE_WIRELESS
  WiFi.mode(WIFI_OFF);
  btStop();
#endif
  Plugboard::init();
  board_state=STATE_LOADING_FPGA;
  if (!FPGALoader::init() || !FPGALoader::loadBitstream()) {
    board_state=STATE_ERROR; return; // USB hello remains available, ready=false.
  }
  UARTProtocol::init();
  board_state=STATE_RUNNING_SELFTEST;
  if (!Selftest::run() || !UARTProtocol::reset()) { board_state=STATE_ERROR; return; }
  uint8_t windows[3];
  if (!UARTProtocol::readState(windows) || windows[0] || windows[1] || windows[2]) {
    board_state=STATE_ERROR; return;
  }
  board_state=STATE_READY;
  USBProtocol::setReady(true);
  digitalWrite(STATUS_LED_PIN,LOW);
}
void loop() {
  USBProtocol::process();
  if (board_state==STATE_ERROR || !UARTProtocol::isStateCertain()) {
    static unsigned long last_blink=0;
    if (millis()-last_blink>500) {
      digitalWrite(STATUS_LED_PIN,!digitalRead(STATUS_LED_PIN)); last_blink=millis();
    }
  }
  delay(1);
}
