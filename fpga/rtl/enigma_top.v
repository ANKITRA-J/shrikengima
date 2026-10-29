// Top-level module for Shrike Fi board integration
// Connects UART, packet protocol, enigma core, and LED controller

(* top *)
module enigma_top (
  (* iopad_external_pin, clkbuf_inhibit *) input OSC_CLK,
  (* iopad_external_pin, clkbuf_inhibit *) input core_clk,
  (* iopad_external_pin *) output core_clk_out,
  (* iopad_external_pin *) output core_clk_en,
  (* iopad_external_pin *) output OSC_EN,
  (* iopad_external_pin *) input uart_rx_pin,
  (* iopad_external_pin *) output uart_tx_pin,
  (* iopad_external_pin *) output uart_tx_oe,
  (* iopad_external_pin *) output led_out,
  (* iopad_external_pin *) output led_oe
);
  reg [3:0] clock_div = 0;
  always @(posedge OSC_CLK) clock_div <= clock_div + 4'd1;
  // Dedicated LaC1 loopback is mapped in pins.csv; no external jumper.
  assign core_clk_out = clock_div[3]; // 50 MHz / 16 = 3.125 MHz
  assign core_clk_en = 1'b1;
  wire clk = core_clk;
  assign OSC_EN = 1'b1;
  assign led_oe = 1'b1;
  assign uart_tx_oe = 1'b1;
  // Forge registers power up at their synthesized initial values.
  // Hold the entire design reset for 255 core-clock edges after configuration.
  reg [7:0] startup = 0;
  always @(posedge clk) if (!(&startup)) startup <= startup + 1'b1;
  wire rst = !(&startup);

  // UART RX signals
  wire [7:0] uart_rx_data;
  wire uart_rx_valid;
  wire uart_rx_error;
  wire uart_rx_busy;
  
  // UART TX signals
  wire [7:0] uart_tx_data;
  wire uart_tx_start;
  wire uart_tx_busy;
  
  // Enigma core signals
  wire core_start;
  wire [4:0] core_letter;
  wire core_cfg_we;
  wire [3:0] core_cfg_addr;
  wire [4:0] core_cfg_data;
  wire core_rst;
  wire core_busy;
  wire core_done;
  wire [4:0] core_result;
  wire [4:0] core_window_left;
  wire [4:0] core_window_middle;
  wire [4:0] core_window_right;
  
  // UART RX instantiation
  uart_rx #(
    .CLKS_PER_BIT(27)
  ) uart_rx_inst (
    .clk(clk),
    .rst(rst),
    .rx_serial(uart_rx_pin),
    .rx_data(uart_rx_data),
    .rx_valid(uart_rx_valid),
    .rx_error(uart_rx_error),
    .busy(uart_rx_busy)
  );
  
  // UART TX instantiation
  uart_tx #(
    .CLKS_PER_BIT(27)
  ) uart_tx_inst (
    .clk(clk),
    .rst(rst),
    .tx_start(uart_tx_start),
    .tx_data(uart_tx_data),
    .tx_serial(uart_tx_pin),
    .busy(uart_tx_busy)
  );
  
  // Packet wrapper instantiation
  packet_wrapper #(.TIMEOUT_CLOCKS(31250)) packet_wrapper_inst (
    .clk(clk),
    .rst(rst),
    .uart_rx_data(uart_rx_data),
    .uart_rx_valid(uart_rx_valid),
    .uart_tx_busy(uart_tx_busy),
    .uart_tx_data(uart_tx_data),
    .uart_tx_start(uart_tx_start),
    .core_start(core_start),
    .core_letter(core_letter),
    .core_cfg_we(core_cfg_we),
    .core_cfg_addr(core_cfg_addr),
    .core_cfg_data(core_cfg_data),
    .core_rst(core_rst),
    .core_busy(core_busy),
    .core_done(core_done),
    .core_result(core_result),
    .core_window_left(core_window_left),
    .core_window_middle(core_window_middle),
    .core_window_right(core_window_right)
  );
  
  // Enigma core instantiation
  enigma_core enigma_core_inst (
    .clk(clk),
    .rst(rst || core_rst),
    .start(core_start),
    .letter(core_letter),
    .cfg_we(core_cfg_we),
    .cfg_addr(core_cfg_addr),
    .cfg_data(core_cfg_data),
    .busy(core_busy),
    .done(core_done),
    .result(core_result),
    .window_left(core_window_left),
    .window_middle(core_window_middle),
    .window_right(core_window_right)
  );
  
  // LED controller instantiation
  led_controller #(.PULSE_CLOCKS(250000)) led_controller_inst (
    .clk(clk),
    .rst(rst),
    .trigger(core_done),
    .led(led_out)
  );

endmodule
