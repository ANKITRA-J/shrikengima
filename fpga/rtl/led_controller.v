// LED controller with retriggerable 80ms pulse
// At 50MHz, 80ms = 4,000,000 clocks

module led_controller #(parameter PULSE_CLOCKS = 4000000) (
  input clk,
  input rst,
  input trigger,
  output reg led
);

  localparam COUNTER_BITS = $clog2(PULSE_CLOCKS);
  
  reg [COUNTER_BITS-1:0] counter;
  reg counting;
  
  always @(posedge clk) begin
    if (rst) begin
      led <= 1'b0;
      counter <= 0;
      counting <= 1'b0;
    end else begin
      if (trigger) begin
        // (Re)start the pulse
        led <= 1'b1;
        counter <= 0;
        counting <= 1'b1;
      end else if (counting) begin
        if (counter == PULSE_CLOCKS - 1) begin
          // Pulse complete
          led <= 1'b0;
          counting <= 1'b0;
          counter <= 0;
        end else begin
          counter <= counter + 1;
        end
      end
    end
  end

endmodule
