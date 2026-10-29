#include "uart_protocol.h"
#include <cassert>
#include <iostream>
static uint8_t crc(const std::vector<uint8_t>& bytes) {
  uint8_t c=0;
  for(auto b:bytes){c^=b;for(int i=0;i<8;i++)c=(c&128)?(c<<1)^7:c<<1;}
  return c;
}
static void reply(uint8_t seq,uint8_t op,std::vector<uint8_t> data,bool bad_crc=false) {
  std::vector<uint8_t> p={1,seq,op,static_cast<uint8_t>(data.size())};
  p.insert(p.end(),data.begin(),data.end());
  Serial2.rx.push_back(0x5a);
  for(auto b:p)Serial2.rx.push_back(b);
  Serial2.rx.push_back(crc(p)^(bad_crc?1:0));
}
int main(){
  UARTProtocol::init();
  uint8_t version;
  for(int i=0;i<300;i++){
    reply(i,0x81,{0,'E','N','G',1});
    assert(UARTProtocol::ping(&version)); assert(version==1);
  }
  reply(static_cast<uint8_t>(300),0x81,{}); assert(!UARTProtocol::ping(&version));
  reply(static_cast<uint8_t>(301),0x01,{0,'E','N','G',1}); assert(!UARTProtocol::ping(&version));
  reply(static_cast<uint8_t>(302),0x81,{0,'E','N','G',1},true); assert(!UARTProtocol::ping(&version));
  auto before=millis(); assert(!UARTProtocol::ping(&version)); assert(millis()-before<120);
  uint8_t r[3]={0,1,2},w[3]={0,0,0},g[3]={0,0,0},out;
  reply(static_cast<uint8_t>(304),0x82,{0,0,0,0}); assert(UARTProtocol::config(r,w,g));
  reply(static_cast<uint8_t>(305),0x83,{0,26,0,0,1}); assert(!UARTProtocol::transform(0,&out,w));
  assert(!UARTProtocol::isStateCertain());
  auto sent=Serial2.tx; assert(!UARTProtocol::transform(0,&out,w));assert(sent==Serial2.tx);

  // A valid packet CRC is insufficient: RESET must acknowledge exactly AAA.
  const std::vector<std::vector<uint8_t>> bad_reset_replies = {
    {0}, {0,0,0}, {0,0,0,0,0},
    {0,1,0,0}, {0,0,1,0}, {0,0,0,1}, {1,0,0,0}
  };
  for (const auto& data : bad_reset_replies) {
    UARTProtocol::init();
    reply(0,0x85,data);
    assert(!UARTProtocol::reset());
    assert(!UARTProtocol::isStateCertain());
    sent=Serial2.tx;
    assert(!UARTProtocol::transform(0,&out,w));
    assert(sent==Serial2.tx); // No transform may advance an uncertain machine.
    reply(1,0x85,{0,0,0,0});
    assert(UARTProtocol::reset());
    assert(UARTProtocol::isStateCertain());
    reply(2,0x83,{0,1,0,0,1});
    assert(UARTProtocol::transform(0,&out,w));
    assert(out==1 && w[0]==0 && w[1]==0 && w[2]==1);
  }

  // Malformed READ_STATE replies must invalidate certainty and leave outputs alone.
  const std::vector<std::vector<uint8_t>> bad_state_replies = {
    {0}, {0,0,0}, {0,0,0,0,0},
    {0,26,0,0}, {0,0,26,0}, {0,0,0,26}, {1,0,0,0}
  };
  for (const auto& data : bad_state_replies) {
    UARTProtocol::init();
    uint8_t windows[3]={7,8,9};
    reply(0,0x84,data);
    assert(!UARTProtocol::readState(windows));
    assert(!UARTProtocol::isStateCertain());
    assert(windows[0]==7 && windows[1]==8 && windows[2]==9);
    sent=Serial2.tx;
    assert(!UARTProtocol::transform(0,&out,windows));
    assert(sent==Serial2.tx);
    reply(1,0x85,{0,0,0,0});
    assert(UARTProtocol::reset());
    assert(UARTProtocol::isStateCertain());
    reply(2,0x84,{0,0,12,25});
    assert(UARTProtocol::readState(windows));
    assert(windows[0]==0 && windows[1]==12 && windows[2]==25);
  }
  std::cout<<"PASS: sequence wrap, zero length, opcode, CRC, deadline, impossible contact, no retry, malformed reset/state rejection and valid reset recovery\n";
}
