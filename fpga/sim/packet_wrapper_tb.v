`timescale 1ns/1ps
module packet_wrapper_tb;
reg clk=0; always #5 clk=~clk;
reg rst=1;
reg [7:0] rx_data=0; reg rx_valid=0;
wire [7:0] tx_data; wire tx_start,tx_busy,serial_line;
wire core_start,cfg_we,core_rst,core_busy,core_done;
wire [4:0] letter,cfg_data,result,wl,wm,wr; wire [3:0] cfg_addr;
packet_wrapper dut(clk,rst,rx_data,rx_valid,tx_busy,tx_data,tx_start,
 core_start,letter,cfg_we,cfg_addr,cfg_data,core_rst,core_busy,core_done,result,wl,wm,wr);
enigma_core core(clk,rst|core_rst,core_start,letter,cfg_we,cfg_addr,cfg_data,core_busy,core_done,result,wl,wm,wr);
uart_tx #(.CLKS_PER_BIT(16)) tx(clk,rst,tx_start,tx_data,serial_line,tx_busy);
wire [7:0] received; wire received_valid,received_error,received_busy;
uart_rx #(.CLKS_PER_BIT(16)) rx(clk,rst,serial_line,received,received_valid,received_error,received_busy);
reg [7:0] captured[0:31]; integer count=0;
always @(posedge clk) if(received_valid) begin captured[count]=received; count=count+1; end
reg [7:0] vectors[0:4139]; integer order_index,letter_index,offset;
reg [7:0] payload[0:8]; reg [7:0] crc; integer i,n,seqnum=0;
function [7:0] update_crc;
 input [7:0] prev,byte_value; integer k; reg [7:0] c;
 begin c=prev^byte_value; for(k=0;k<8;k=k+1)c=c[7]?(c<<1)^8'h07:c<<1; update_crc=c; end
endfunction
task byte_in; input [7:0] value;
 begin @(negedge clk); rx_data=value; rx_valid=1; @(negedge clk); rx_valid=0; repeat(3)@(negedge clk); end
endtask
task request; input [7:0] op,len; input corrupt;
 integer j;
 begin
 count=0; crc=0;
 byte_in(8'ha5); byte_in(1); crc=update_crc(crc,1);
 byte_in(seqnum); crc=update_crc(crc,seqnum);
 byte_in(op); crc=update_crc(crc,op);
 byte_in(len); crc=update_crc(crc,len);
 for(j=0;j<len;j=j+1)begin byte_in(payload[j]);crc=update_crc(crc,payload[j]);end
 byte_in(crc ^ corrupt);
 end
endtask
task response; input [7:0] op,status,data_len;
 integer j,t; reg [7:0] check;
 begin
 t=0;
 while(count < 7+data_len && t<4000)begin @(negedge clk);t=t+1;end
 if(count != 7+data_len)$fatal(1,"Response length: got %0d want %0d",count,7+data_len);
 if(captured[0]!==8'h5a || captured[1]!==1 || captured[2]!==seqnum[7:0] || captured[3]!== (op|8'h80) || captured[4]!==data_len+1 || captured[5]!==status) $fatal(1,"Bad response header");
 check=0;for(j=1;j<count-1;j=j+1)check=update_crc(check,captured[j]);
 if(check!==captured[count-1])$fatal(1,"Bad response CRC");
 repeat(50)@(negedge clk);seqnum=seqnum+1;
 end
endtask
initial begin
 repeat(5)@(negedge clk);rst=0;repeat(5)@(negedge clk);
 request(1,0,0);response(1,0,4);
 if(captured[6]!=="E" || captured[7]!=="N" || captured[8]!=="G")$fatal(1,"Bad ping");
 request(8'h70,0,0);response(8'h70,3,0);
 payload[0]=0;request(1,1,0);response(1,1,0);
 request(1,0,1);repeat(4000)@(negedge clk);if(count!=0)$fatal(1,"Responded to bad CRC");
 // All six basic operations, including RESET after stepping.
 request(5,0,0);response(5,0,3);
 payload[0]=0;request(3,1,0);response(3,0,4);
 if(captured[6]!==1 || captured[9]!==1)$fatal(1,"A must encrypt to B, final AAB");
 request(4,0,0);response(4,0,3);
 if(captured[8]!==1)$fatal(1,"Readback mismatch");
 request(5,0,0);response(5,0,3);
 if(wr!==0)$fatal(1,"Reset did not reach core");
 // Incomplete packet must expire and accept another marker.
 byte_in(8'ha5);byte_in(1);repeat(500010)@(negedge clk);
 request(1,0,0);response(1,0,4);
 // Oracle-generated all-rotor cases are included by the test runner.
 $readmemh("packet_vectors.hex", vectors);
 offset=0;
 for(order_index=0;order_index<60;order_index=order_index+1)begin
   for(i=0;i<9;i=i+1)payload[i]=vectors[offset+i];
   offset=offset+9;request(2,9,0);response(2,0,3);
   for(letter_index=0;letter_index<12;letter_index=letter_index+1)begin
     payload[0]=vectors[offset];request(3,1,0);response(3,0,4);
     for(i=0;i<4;i=i+1)
       if(captured[6+i]!==vectors[offset+1+i])$fatal(1,"Oracle mismatch order=%0d letter=%0d byte=%0d",order_index,letter_index,i);
     offset=offset+5;
   end
 end
 $display("PASS: real UART serialization, CRC, errors, timeout recovery, all 60 rotor orders");
 $finish;
end
initial begin #100000000; $fatal(1,"Watchdog"); end
endmodule
