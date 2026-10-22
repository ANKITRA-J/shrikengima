// LED controller with retriggerable 80ms pulse
// At 50MHz, 80ms = 4,000,000 clocks

module led_controller (
  input clk,
  input rst,
  input trigger,
  output reg led
);

  localparam PULSE_CLOCKS = 22'd4000000;
  
  reg [21:0] counter;
  reg counting;
  
  always @(posedge clk) begin
    if (rst) begin
      led <= 1'b0;
      counter <= 22'd0;
      counting <= 1'b0;
    end else begin
      if (trigger) begin
        // (Re)start the pulse
        led <= 1'b1;
        counter <= 22'd0;
        counting <= 1'b1;
      end else if (counting) begin
        if (counter == PULSE_CLOCKS - 1) begin
          // Pulse complete
          led <= 1'b0;
          counting <= 1'b0;
          counter <= 22'd0;
        end else begin
          counter <= counter + 1;
        end
      end
    end
  end

endmodule
