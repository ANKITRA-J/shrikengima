#pragma once
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cstdio>
#include <deque>
#include <vector>
#define SERIAL_8N1 0
inline unsigned long test_time=0;
inline unsigned long millis(){return test_time++;}
inline void delay(unsigned long n){test_time+=n;}
struct TestSerial {
  std::deque<uint8_t> rx;
  std::vector<uint8_t> tx;
  void begin(int,int,int,int){}
  void setTimeout(int){}
  int available(){return rx.size();}
  int read(){auto c=rx.front();rx.pop_front();return c;}
  size_t write(const uint8_t* p,size_t n){tx.assign(p,p+n);return n;}
  void flush(){}
};
inline TestSerial Serial2;
