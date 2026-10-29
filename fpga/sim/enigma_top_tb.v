`timescale 1ns/1ps
// Full board-facing path at 50 MHz, including divider, startup and both UARTs.
module enigma_top_tb;
reg clk=0; always #10 clk=~clk;
reg host_rst=1, host_start=0;
reg [7:0] host_data=0;
wire host_busy, to_fpga, from_fpga, osc_en, tx_oe, led, led_oe;
uart_tx #(.CLKS_PER_BIT(434)) host_tx(clk,host_rst,host_start,host_data,to_fpga,host_busy);
wire core_clk_out, core_clk_en;
// Model the device's dedicated LaC1 feedback network explicitly.
wire core_clk = core_clk_en ? core_clk_out : 1'b0;
enigma_top dut(.OSC_CLK(clk), .core_clk(core_clk),
 .core_clk_out(core_clk_out), .core_clk_en(core_clk_en), .OSC_EN(osc_en),
 .uart_rx_pin(to_fpga), .uart_tx_pin(from_fpga), .uart_tx_oe(tx_oe),
 .led_out(led), .led_oe(led_oe));
wire [7:0] received; wire valid,framing,busy;
uart_rx #(.CLKS_PER_BIT(434)) host_rx(clk,host_rst,from_fpga,received,valid,framing,busy);
reg [7:0] captured[0:31]; integer count=0;
always @(posedge clk)begin
 if(valid)begin captured[count]=received;count=count+1;end
 if(framing)$fatal(1,"FPGA response framing error");
end
function [7:0] crc8; input [7:0] prev,b; integer k; reg [7:0] c;
 begin c=prev^b;for(k=0;k<8;k=k+1)c=c[7]?(c<<1)^8'h07:c<<1;crc8=c;end
endfunction
task send; input [7:0] b;
 begin
 while(host_busy)@(negedge clk);
 host_data=b;host_start=1;@(negedge clk);host_start=0;
 @(negedge clk);while(host_busy)@(negedge clk);
 end
endtask
task request; input [7:0] seqnum,op,len,value; reg [7:0] c;
 begin
 count=0;c=0;send(8'ha5);send(1);c=crc8(c,1);
 send(seqnum);c=crc8(c,seqnum);send(op);c=crc8(c,op);
 send(len);c=crc8(c,len);if(len!=0)begin send(value);c=crc8(c,value);end
 send(c);
 end
endtask
task response; input integer expected; integer t,j;reg [7:0] c;
 begin
 t=0;while(count<expected && t<100000)begin @(negedge clk);t=t+1;end
 if(count!=expected)$fatal(1,"Top response count %0d expected %0d",count,expected);
 c=0;for(j=1;j<count-1;j=j+1)c=crc8(c,captured[j]);
 if(c!==captured[count-1] || captured[0]!==8'h5a || captured[5]!==0)$fatal(1,"Top CRC/status");
 repeat(2000)@(negedge clk);
 end
endtask
initial begin
 repeat(10)@(negedge clk);host_rst=0;
 repeat(10000)@(negedge clk);
 if(!osc_en || !tx_oe || !led_oe)$fatal(1,"Output enables");
 request(0,1,0,0);response(11);
 if(captured[6]!=="E" || captured[7]!=="N" || captured[8]!=="G")$fatal(1,"Top ping");
 request(1,3,1,0);response(11);
 if(captured[6]!==1 || captured[9]!==1 || !led)$fatal(1,"Top A -> B / AAB / LED");
 request(2,5,0,0);response(10);
 if(captured[6]!==0 || captured[7]!==0 || captured[8]!==0)$fatal(1,"Top reset");
 $display("PASS: 50 MHz top, divided clock, power-on reset, physical UART framing, A -> B and built-in LED output");
 $finish;
end
initial begin #20000000;$fatal(1,"Top watchdog");end
endmodule
