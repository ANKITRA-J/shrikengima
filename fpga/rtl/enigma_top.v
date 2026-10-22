// Top-level module for Shrike Fi board integration
// Connects UART, packet protocol, enigma core, and LED controller

(* top_module *)
module enigma_top (
  (* clock_pin = "OSC_CLK" *) input OSC_CLK,
  (* clock_enable_pin = "OSC_EN" *) input OSC_EN,
  (* io_pin = "5" *) input uart_rx_pin,
  (* io_pin = "6", io_dir = "output" *) output uart_tx_pin,
  (* io_pin = "GPIO16", io_dir = "output" *) output led_out,
  (* io_pin = "GPIO16_OE", io_dir = "output" *) output led_oe
);

  // System signals
  wire clk = OSC_CLK;
  wire rst;
  
  // Generate reset from inverted clock enable (active-high reset)
  assign rst = !OSC_EN;
  assign led_oe = 1'b1;  // Always enable LED output
  
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
    .CLKS_PER_BIT(434)
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
    .CLKS_PER_BIT(434)
  ) uart_tx_inst (
    .clk(clk),
    .rst(rst),
    .tx_start(uart_tx_start),
    .tx_data(uart_tx_data),
    .tx_serial(uart_tx_pin),
    .busy(uart_tx_busy)
  );
  
  // Packet wrapper instantiation
  packet_wrapper packet_wrapper_inst (
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
  led_controller led_controller_inst (
    .clk(clk),
    .rst(rst),
    .trigger(core_done),
    .led(led_out)
  );

endmodule
