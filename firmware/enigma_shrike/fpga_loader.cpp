// ESP32-S3 sequence follows Vicharak Shrike 1.1.0, src/Shrike.cpp.
// Own the SPI instance so it can be ended before GPIO11/13 become UART pins.
#include "fpga_loader.h"
#include <LittleFS.h>
#include <SPI.h>
namespace { SPIClass config_spi(HSPI); }
bool FPGALoader::configured_ = false;
uint32_t FPGALoader::bitstream_size_ = 0;
char FPGALoader::status_message_[128] = "Not initialized";
bool FPGALoader::init() {
  configured_ = false;
  // Never format automatically: a mount failure must not erase the FPGA image.
  if (!LittleFS.begin(false)) {
    snprintf(status_message_,sizeof(status_message_),"LittleFS mount failed; upload filesystem image");
    return false;
  }
  return true;
}
bool FPGALoader::loadBitstream(const char* path) {
  configured_ = false;
  File file=LittleFS.open(path,"r");
  if (!file) { snprintf(status_message_,sizeof(status_message_),"Missing FPGA image"); return false; }
  bitstream_size_=file.size();
  // The tracked placeholder must never be sent to the board.
  if (bitstream_size_<1024) {
    file.close(); snprintf(status_message_,sizeof(status_message_),"FPGA image is empty or a placeholder"); return false;
  }
  pinMode(9,OUTPUT); pinMode(8,OUTPUT); pinMode(10,OUTPUT);
  digitalWrite(10,LOW); digitalWrite(9,LOW); digitalWrite(8,LOW);
  delay(100); digitalWrite(9,HIGH); digitalWrite(8,HIGH); delay(100);
  config_spi.begin(12,13,11,10);
  delay(500); digitalWrite(10,HIGH); delayMicroseconds(2000); digitalWrite(10,LOW);
  config_spi.beginTransaction(SPISettings(1600000,MSBFIRST,SPI_MODE0));
  uint8_t buffer[512]; size_t sent=0;
  unsigned long started=millis();
  while (sent<bitstream_size_ && millis()-started<FPGA_LOAD_TIMEOUT_MS) {
    size_t n=file.read(buffer,sizeof(buffer));
    if (!n) break;
    config_spi.transfer(buffer,n); sent+=n;
  }
  config_spi.endTransaction(); digitalWrite(10,HIGH); file.close(); delay(100);
  releaseConfigPins();
  configured_=sent==bitstream_size_;
  snprintf(status_message_,sizeof(status_message_),configured_ ? "Image transferred; UART verification required" : "Incomplete image transfer");
  return configured_;
}
void FPGALoader::releaseConfigPins() {
  config_spi.end();
  pinMode(11,INPUT); pinMode(13,INPUT); pinMode(12,INPUT);
  // Keep power/enable asserted and configuration select high.
}
bool FPGALoader::isConfigured() { return configured_; }
const char* FPGALoader::getStatus() { return status_message_; }
uint32_t FPGALoader::getBitstreamSize() { return bitstream_size_; }
bool FPGALoader::verifyBitstream(const uint8_t* data,size_t length) {
  // Format/integrity validation needs vendor image metadata; size alone is not authenticity.
  return data && length>=1024;
}
