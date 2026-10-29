// Generated from fpga/rtl by tools/prepare_fpga.py.
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

// Enigma cipher core module
// Implements three-rotor Enigma with reflector, configurable settings, and sequential datapath

module enigma_core (
  input clk,
  input rst,
  input start,
  input [4:0] letter,
  input cfg_we,
  input [3:0] cfg_addr,
  input [4:0] cfg_data,
  output reg busy,
  output reg done,
  output reg [4:0] result,
  output reg [4:0] window_left,
  output reg [4:0] window_middle,
  output reg [4:0] window_right
);

  // Modular arithmetic helpers for Enigma rotor computations
// All operations modulo 26

// Increment modulo 26: (x + 6'd1) mod 26
function automatic [4:0] inc26;
  input [4:0] x;
  reg [5:0] tmp;
  begin
    tmp = x + 6'd1;
    inc26 = (tmp >= 6'd26) ? (tmp - 6'd26) : tmp[4:0];
  end
endfunction

// Add modulo 26: (a + b) mod 26
function automatic [4:0] add26;
  input [4:0] a;
  input [4:0] b;
  reg [5:0] tmp;
  begin
    tmp = a + b;
    add26 = (tmp >= 6'd26) ? (tmp - 6'd26) : tmp[4:0];
  end
endfunction

// Subtract modulo 26: (a - b) mod 26
function automatic [4:0] sub26;
  input [4:0] a;
  input [4:0] b;
  reg [5:0] tmp;
  begin
    tmp = {1'b0, a} - {1'b0, b};
    sub26 = tmp[5] ? (tmp[4:0] + 5'd26) : tmp[4:0];
  end
endfunction


  // Configuration registers
  reg [2:0] rotor_left, rotor_middle, rotor_right;
  reg [4:0] ring_left, ring_middle, ring_right;
  
  // Turnover positions for each rotor (when middle/right rotor triggers stepping)
  // Rotor I: Q(16), II: E(4), III: V(21), IV: J(9), V: Z(25)
  function automatic [4:0] get_turnover;
    input [2:0] rotor_id;
    begin
      case (rotor_id)
        3'd0: get_turnover = 5'd16;  // I -> Q
        3'd1: get_turnover = 5'd4;   // II -> E
        3'd2: get_turnover = 5'd21;  // III -> V
        3'd3: get_turnover = 5'd9;   // IV -> J
        3'd4: get_turnover = 5'd25;  // V -> Z
        default: get_turnover = 5'd0;
      endcase
    end
  endfunction
  
  // State machine - need extra states for ROM lookups
  localparam IDLE = 4'd0;
  localparam STEP = 4'd1;
  localparam RIGHT_FWD_SETUP = 4'd2;
  localparam RIGHT_FWD_WAIT = 4'd3;
  localparam MIDDLE_FWD_SETUP = 4'd4;
  localparam MIDDLE_FWD_WAIT = 4'd5;
  localparam LEFT_FWD_SETUP = 4'd6;
  localparam LEFT_FWD_WAIT = 4'd7;
  localparam REFLECT_SETUP = 4'd8;
  localparam REFLECT_WAIT = 4'd9;
  localparam LEFT_INV_SETUP = 4'd10;
  localparam LEFT_INV_WAIT = 4'd11;
  localparam MIDDLE_INV_SETUP = 4'd12;
  localparam MIDDLE_INV_WAIT = 4'd13;
  localparam RIGHT_INV_SETUP = 4'd14;
  localparam RIGHT_INV_WAIT = 4'd15;
  
  reg [3:0] state, next_state;
  reg [4:0] current_val;
  reg [4:0] shift_val; // Temporary for ring offset calculations
  
  // Select operands before arithmetic so the six rotor traversals share
  // one ring-offset and input-translation datapath.
  wire right_stage = state == RIGHT_FWD_SETUP || state == RIGHT_INV_SETUP;
  wire middle_stage = state == MIDDLE_FWD_SETUP || state == MIDDLE_INV_SETUP;
  wire [4:0] selected_window = right_stage ? window_right : middle_stage ? window_middle : window_left;
  wire [4:0] selected_ring = right_stage ? ring_right : middle_stage ? ring_middle : ring_left;
  wire [4:0] selected_shift = sub26(selected_window, selected_ring);
  wire [4:0] translated_input = add26(current_val, selected_shift);

  // ROM interface
  reg [2:0] rom_rotor;
  reg rom_inv;
  reg [4:0] rom_x;
  wire [4:0] rom_y;
  
  rotor_rom rom_inst (
    .rotor(rom_rotor),
    .inv(rom_inv),
    .x(rom_x),
    .y(rom_y)
  );
  
  always @(posedge clk) begin
    if (rst) begin
      // Reset to I, II, III with AAA windows and AAA rings
      rotor_left <= 3'd0;   // Rotor I
      rotor_middle <= 3'd1; // Rotor II
      rotor_right <= 3'd2;  // Rotor III
      window_left <= 5'd0;
      window_middle <= 5'd0;
      window_right <= 5'd0;
      ring_left <= 5'd0;
      ring_middle <= 5'd0;
      ring_right <= 5'd0;
      state <= IDLE;
      next_state <= IDLE;
      busy <= 1'b0;
      done <= 1'b0;
      result <= 5'd0;
      current_val <= 5'd0;
      shift_val <= 5'd0;
      rom_rotor <= 3'd0;
      rom_inv <= 1'b0;
      rom_x <= 5'd0;
    end else begin
      case (state)
        IDLE: begin
          done <= 1'b0;
          
          // Handle configuration writes
          if (cfg_we && !busy) begin
            case (cfg_addr)
              4'd0: if (cfg_data <= 5'd4) rotor_left <= cfg_data[2:0];
              4'd1: if (cfg_data <= 5'd4) rotor_middle <= cfg_data[2:0];
              4'd2: if (cfg_data <= 5'd4) rotor_right <= cfg_data[2:0];
              4'd3: if (cfg_data <= 5'd25) window_left <= cfg_data;
              4'd4: if (cfg_data <= 5'd25) window_middle <= cfg_data;
              4'd5: if (cfg_data <= 5'd25) window_right <= cfg_data;
              4'd6: if (cfg_data <= 5'd25) ring_left <= cfg_data;
              4'd7: if (cfg_data <= 5'd25) ring_middle <= cfg_data;
              4'd8: if (cfg_data <= 5'd25) ring_right <= cfg_data;
              default: ; // Invalid address, preserve config
            endcase
          end
          
          // Handle start signal
          if (start && !busy && !cfg_we && letter <= 5'd25) begin
            busy <= 1'b1;
            current_val <= letter;
            state <= STEP;
          end
        end
        
        STEP: begin
          // Stepping logic: evaluate notches from OLD positions
          if (window_middle == get_turnover(rotor_middle)) begin
            // Double-step: left and middle advance
            window_left <= inc26(window_left);
            window_middle <= inc26(window_middle);
            window_right <= inc26(window_right);
          end else if (window_right == get_turnover(rotor_right)) begin
            // Right at notch: middle advances
            window_middle <= inc26(window_middle);
            window_right <= inc26(window_right);
          end else begin
            // Normal: only right advances
            window_right <= inc26(window_right);
          end
          
          state <= RIGHT_FWD_SETUP;
        end
        
        RIGHT_FWD_SETUP: begin
          shift_val <= selected_shift;
          rom_rotor <= rotor_right;
          rom_inv <= 1'b0;
          rom_x <= translated_input;
          state <= RIGHT_FWD_WAIT;
        end
        
        RIGHT_FWD_WAIT: begin
          current_val <= sub26(rom_y, shift_val);
          state <= MIDDLE_FWD_SETUP;
        end
        
        MIDDLE_FWD_SETUP: begin
          shift_val <= selected_shift;
          rom_rotor <= rotor_middle;
          rom_inv <= 1'b0;
          rom_x <= translated_input;
          state <= MIDDLE_FWD_WAIT;
        end
        
        MIDDLE_FWD_WAIT: begin
          current_val <= sub26(rom_y, shift_val);
          state <= LEFT_FWD_SETUP;
        end
        
        LEFT_FWD_SETUP: begin
          shift_val <= selected_shift;
          rom_rotor <= rotor_left;
          rom_inv <= 1'b0;
          rom_x <= translated_input;
          state <= LEFT_FWD_WAIT;
        end
        
        LEFT_FWD_WAIT: begin
          current_val <= sub26(rom_y, shift_val);
          state <= REFLECT_SETUP;
        end
        
        REFLECT_SETUP: begin
          // Reflector is rotor 5, no ring offset
          rom_rotor <= 3'd5;
          rom_inv <= 1'b0;
          rom_x <= current_val;
          state <= REFLECT_WAIT;
        end
        
        REFLECT_WAIT: begin
          current_val <= rom_y;
          state <= LEFT_INV_SETUP;
        end
        
        LEFT_INV_SETUP: begin
          shift_val <= selected_shift;
          rom_rotor <= rotor_left;
          rom_inv <= 1'b1;
          rom_x <= translated_input;
          state <= LEFT_INV_WAIT;
        end
        
        LEFT_INV_WAIT: begin
          current_val <= sub26(rom_y, shift_val);
          state <= MIDDLE_INV_SETUP;
        end
        
        MIDDLE_INV_SETUP: begin
          shift_val <= selected_shift;
          rom_rotor <= rotor_middle;
          rom_inv <= 1'b1;
          rom_x <= translated_input;
          state <= MIDDLE_INV_WAIT;
        end
        
        MIDDLE_INV_WAIT: begin
          current_val <= sub26(rom_y, shift_val);
          state <= RIGHT_INV_SETUP;
        end
        
        RIGHT_INV_SETUP: begin
          shift_val <= selected_shift;
          rom_rotor <= rotor_right;
          rom_inv <= 1'b1;
          rom_x <= translated_input;
          state <= RIGHT_INV_WAIT;
        end
        
        RIGHT_INV_WAIT: begin
          result <= sub26(rom_y, shift_val);
          done <= 1'b1;
          busy <= 1'b0;
          state <= IDLE;
        end
        
        default: state <= IDLE;
      endcase
    end
  end

endmodule

// Generated by tools/gen_fpga_files.py; one 32-bit truth table per output bit.
module rotor_rom (input [2:0] rotor, input inv,
  input [4:0] x, output reg [4:0] y);
wire [4:0] table_0;
localparam [31:0] MASK_0_0 = 32'h02c98f58;
assign table_0[0] = MASK_0_0[x];
localparam [31:0] MASK_0_1 = 32'h010db872;
assign table_0[1] = MASK_0_1[x];
localparam [31:0] MASK_0_2 = 32'h000bb52d;
assign table_0[2] = MASK_0_2[x];
localparam [31:0] MASK_0_3 = 32'h02285616;
assign table_0[3] = MASK_0_3[x];
localparam [31:0] MASK_0_4 = 32'h00876b80;
assign table_0[4] = MASK_0_4[x];
wire [4:0] table_1;
localparam [31:0] MASK_1_0 = 32'h025b87e0;
assign table_1[0] = MASK_1_0[x];
localparam [31:0] MASK_1_1 = 32'h010fb0aa;
assign table_1[1] = MASK_1_1[x];
localparam [31:0] MASK_1_2 = 32'h014349cb;
assign table_1[2] = MASK_1_2[x];
localparam [31:0] MASK_1_3 = 32'h03686284;
assign table_1[3] = MASK_1_3[x];
localparam [31:0] MASK_1_4 = 32'h00968307;
assign table_1[4] = MASK_1_4[x];
wire [4:0] table_2;
localparam [31:0] MASK_2_0 = 32'h00dc2f46;
assign table_2[0] = MASK_2_0[x];
localparam [31:0] MASK_2_1 = 32'h0112bd1c;
assign table_2[1] = MASK_2_1[x];
localparam [31:0] MASK_2_2 = 32'h03da5980;
assign table_2[2] = MASK_2_2[x];
localparam [31:0] MASK_2_3 = 32'h013c442a;
assign table_2[3] = MASK_2_3[x];
localparam [31:0] MASK_2_4 = 32'h00a531d0;
assign table_2[4] = MASK_2_4[x];
wire [4:0] table_3;
localparam [31:0] MASK_3_0 = 32'h013827d6;
assign table_3[0] = MASK_3_0[x];
localparam [31:0] MASK_3_1 = 32'h02323cac;
assign table_3[1] = MASK_3_1[x];
localparam [31:0] MASK_3_2 = 32'h017e9124;
assign table_3[2] = MASK_3_2[x];
localparam [31:0] MASK_3_3 = 32'h00c85896;
assign table_3[3] = MASK_3_3[x];
localparam [31:0] MASK_3_4 = 32'h0321e070;
assign table_3[4] = MASK_3_4[x];
wire [4:0] table_4;
localparam [31:0] MASK_4_0 = 32'h00003fbf;
assign table_4[0] = MASK_4_0[x];
localparam [31:0] MASK_4_1 = 32'h029606ea;
assign table_4[1] = MASK_4_1[x];
localparam [31:0] MASK_4_2 = 32'h0266ac8c;
assign table_4[2] = MASK_4_2[x];
localparam [31:0] MASK_4_3 = 32'h023170b0;
assign table_4[3] = MASK_4_3[x];
localparam [31:0] MASK_4_4 = 32'h01c25f00;
assign table_4[4] = MASK_4_4[x];
wire [4:0] table_5;
localparam [31:0] MASK_5_0 = 32'h006cf899;
assign table_5[0] = MASK_5_0[x];
localparam [31:0] MASK_5_1 = 32'h01b480f5;
assign table_5[1] = MASK_5_1[x];
localparam [31:0] MASK_5_2 = 32'h0314be14;
assign table_5[2] = MASK_5_2[x];
localparam [31:0] MASK_5_3 = 32'h03ab6010;
assign table_5[3] = MASK_5_3[x];
localparam [31:0] MASK_5_4 = 32'h00555541;
assign table_5[4] = MASK_5_4[x];
wire [4:0] table_6;
localparam [31:0] MASK_6_0 = 32'h0227f078;
assign table_6[0] = MASK_6_0[x];
localparam [31:0] MASK_6_1 = 32'h017ce016;
assign table_6[1] = MASK_6_1[x];
localparam [31:0] MASK_6_2 = 32'h018b641d;
assign table_6[2] = MASK_6_2[x];
localparam [31:0] MASK_6_3 = 32'h00918974;
assign table_6[3] = MASK_6_3[x];
localparam [31:0] MASK_6_4 = 32'h0104572a;
assign table_6[4] = MASK_6_4[x];
wire [4:0] table_7;
localparam [31:0] MASK_7_0 = 32'h022519eb;
assign table_7[0] = MASK_7_0[x];
localparam [31:0] MASK_7_1 = 32'h00b85b45;
assign table_7[1] = MASK_7_1[x];
localparam [31:0] MASK_7_2 = 32'h02829e8d;
assign table_7[2] = MASK_7_2[x];
localparam [31:0] MASK_7_3 = 32'h01d30982;
assign table_7[3] = MASK_7_3[x];
localparam [31:0] MASK_7_4 = 32'h0048346e;
assign table_7[4] = MASK_7_4[x];
wire [4:0] table_8;
localparam [31:0] MASK_8_0 = 32'h0048fa4f;
assign table_8[0] = MASK_8_0[x];
localparam [31:0] MASK_8_1 = 32'h0322ee50;
assign table_8[1] = MASK_8_1[x];
localparam [31:0] MASK_8_2 = 32'h00e6b311;
assign table_8[2] = MASK_8_2[x];
localparam [31:0] MASK_8_3 = 32'h022c52a2;
assign table_8[3] = MASK_8_3[x];
localparam [31:0] MASK_8_4 = 32'h001285cb;
assign table_8[4] = MASK_8_4[x];
wire [4:0] table_9;
localparam [31:0] MASK_9_0 = 32'h03c2c798;
assign table_9[0] = MASK_9_0[x];
localparam [31:0] MASK_9_1 = 32'h018e1a3a;
assign table_9[1] = MASK_9_1[x];
localparam [31:0] MASK_9_2 = 32'h018969f0;
assign table_9[2] = MASK_9_2[x];
localparam [31:0] MASK_9_3 = 32'h0094ac8c;
assign table_9[3] = MASK_9_3[x];
localparam [31:0] MASK_9_4 = 32'h00415635;
assign table_9[4] = MASK_9_4[x];
wire [4:0] table_10;
localparam [31:0] MASK_10_0 = 32'h02ce07ca;
assign table_10[0] = MASK_10_0[x];
localparam [31:0] MASK_10_1 = 32'h02303be8;
assign table_10[1] = MASK_10_1[x];
localparam [31:0] MASK_10_2 = 32'h00655f0c;
assign table_10[2] = MASK_10_2[x];
localparam [31:0] MASK_10_3 = 32'h0088f541;
assign table_10[3] = MASK_10_3[x];
localparam [31:0] MASK_10_4 = 32'h02680237;
assign table_10[4] = MASK_10_4[x];
always @(*) begin
  case ({rotor, inv})
    4'd0: y = table_0;
    4'd1: y = table_1;
    4'd2: y = table_2;
    4'd3: y = table_3;
    4'd4: y = table_4;
    4'd5: y = table_5;
    4'd6: y = table_6;
    4'd7: y = table_7;
    4'd8: y = table_8;
    4'd9: y = table_9;
    4'd10: y = table_10;
    default: y = 5'd0;
  endcase
end
endmodule

// Packet wrapper module for internal board protocol
// Handles UART communication, packet parsing, CRC validation, and enigma_core interface

module packet_wrapper #(parameter TIMEOUT_CLOCKS = 500000) (
  input clk,
  input rst,
  
  // UART interface
  input [7:0] uart_rx_data,
  input uart_rx_valid,
  input uart_tx_busy,
  output reg [7:0] uart_tx_data,
  output reg uart_tx_start,
  
  // Enigma core interface
  output reg core_start,
  output reg [4:0] core_letter,
  output reg core_cfg_we,
  output reg [3:0] core_cfg_addr,
  output reg [4:0] core_cfg_data,
  output reg core_rst,
  input core_busy,
  input core_done,
  input [4:0] core_result,
  input [4:0] core_window_left,
  input [4:0] core_window_middle,
  input [4:0] core_window_right
);

  // Protocol constants
  localparam REQ_MARKER = 8'hA5;
  localparam RESP_MARKER = 8'h5A;
  localparam VERSION = 8'h01;
  
  // Opcodes
  localparam OP_PING = 8'h01;
  localparam OP_CONFIG = 8'h02;
  localparam OP_TRANSFORM = 8'h03;
  localparam OP_READ_STATE = 8'h04;
  localparam OP_RESET = 8'h05;
  
  // Status codes
  localparam STATUS_OK = 8'h00;
  localparam STATUS_INVALID = 8'h01;
  localparam STATUS_BUSY = 8'h02;
  localparam STATUS_UNKNOWN_OP = 8'h03;
  localparam STATUS_INTERNAL = 8'h04;
  
  // State machine
  localparam IDLE = 5'd0;
  localparam RX_VERSION = 5'd1;
  localparam RX_SEQUENCE = 5'd2;
  localparam RX_OPCODE = 5'd3;
  localparam RX_LENGTH = 5'd4;
  localparam RX_PAYLOAD = 5'd5;
  localparam RX_CRC = 5'd6;
  localparam VALIDATE = 5'd7;
  localparam EXECUTE_PING = 5'd8;
  localparam EXECUTE_CONFIG = 5'd9;
  localparam CONFIG_WRITE = 5'd10;
  localparam EXECUTE_TRANSFORM = 5'd11;
  localparam WAIT_CORE = 5'd12;
  localparam EXECUTE_READ = 5'd13;
  localparam EXECUTE_RESET = 5'd14;
  localparam BUILD_RESPONSE = 5'd15;
  localparam TX_RESPONSE = 5'd16;
  
  reg [4:0] state;
  
  // Packet fields
  reg version_valid;
  reg [7:0] request_sequence;
  reg [7:0] opcode;
  reg [7:0] length;
  reg [4:0] payload [0:8];
  reg payload_invalid;
  reg crc_valid;
  reg [3:0] payload_index;
  
  // Response fields
  reg [7:0] resp_status;
  reg [7:0] resp_data [0:3];
  reg [3:0] resp_length;
  reg [3:0] resp_index;
  reg [3:0] tx_index;
  
  // CRC calculation
  reg [7:0] crc_byte_in;
  reg crc_update;
  wire [7:0] crc_out;
  
  crc8 crc_inst (
    .clk(clk),
    .rst(rst || (state == IDLE) || (state == BUILD_RESPONSE)),
    .byte_in(crc_byte_in),
    .update(crc_update),
    .crc_out(crc_out)
  );
  
  // Timeout counter (10ms = 500,000 clocks at 50MHz)
  localparam TIMEOUT_BITS = $clog2(TIMEOUT_CLOCKS);
  reg [TIMEOUT_BITS-1:0] timeout_counter;
  wire timeout = (timeout_counter == (TIMEOUT_CLOCKS-1));
  
  // Config write counter for CONFIG command
  reg [3:0] cfg_write_index;
  
  always @(posedge clk) begin
    if (rst) begin
      state <= IDLE;
      uart_tx_start <= 1'b0;
      core_start <= 1'b0;
      core_cfg_we <= 1'b0;
      core_rst <= 1'b0;
      timeout_counter <= 0;
      crc_update <= 1'b0;
      resp_length <= 0;
    end else begin
      // Default signal values
      uart_tx_start <= 1'b0;
      core_start <= 1'b0;
      core_cfg_we <= 1'b0;
      core_rst <= 1'b0;
      crc_update <= 1'b0;
      
      // Timeout counter
      if (state == IDLE) begin
        timeout_counter <= 0;
      end else if (uart_rx_valid) begin
        timeout_counter <= 0;
      end else if (!timeout) begin
        timeout_counter <= timeout_counter + 1;
      end
      
      // Handle timeout
      if (timeout && state != IDLE && state != TX_RESPONSE) begin
        state <= IDLE;
      end else begin
      
      case (state)
        IDLE: begin
          if (uart_rx_valid && uart_rx_data == REQ_MARKER) begin
            state <= RX_VERSION;
            payload_index <= 4'd0;
            payload_invalid <= 1'b0;
          end
        end
        
        RX_VERSION: begin
          if (uart_rx_valid) begin
            version_valid <= uart_rx_data == VERSION;
            crc_byte_in <= uart_rx_data;
            crc_update <= 1'b1;
            state <= RX_SEQUENCE;
          end
        end
        
        RX_SEQUENCE: begin
          if (uart_rx_valid) begin
            request_sequence <= uart_rx_data;
            crc_byte_in <= uart_rx_data;
            crc_update <= 1'b1;
            state <= RX_OPCODE;
          end
        end
        
        RX_OPCODE: begin
          if (uart_rx_valid) begin
            opcode <= uart_rx_data;
            crc_byte_in <= uart_rx_data;
            crc_update <= 1'b1;
            state <= RX_LENGTH;
          end
        end
        
        RX_LENGTH: begin
          if (uart_rx_valid) begin
            length <= uart_rx_data;
            crc_byte_in <= uart_rx_data;
            crc_update <= 1'b1;
            
            if (uart_rx_data > 8'd9) begin
              // Invalid length, drop packet
              state <= IDLE;
            end else if (uart_rx_data == 8'd0) begin
              // No payload, go to CRC
              state <= RX_CRC;
            end else begin
              state <= RX_PAYLOAD;
            end
          end
        end
        
        RX_PAYLOAD: begin
          if (uart_rx_valid) begin
            payload[payload_index] <= uart_rx_data[4:0];
            if (uart_rx_data > 8'd25 || (opcode == OP_CONFIG && payload_index < 4'd3 && uart_rx_data > 8'd4)) payload_invalid <= 1'b1;
            crc_byte_in <= uart_rx_data;
            crc_update <= 1'b1;
            
            if (payload_index == length - 8'd1) begin
              state <= RX_CRC;
            end else begin
              payload_index <= payload_index + 1;
            end
          end
        end
        
        RX_CRC: begin
          if (uart_rx_valid) begin
            crc_valid <= uart_rx_data == crc_out;
            state <= VALIDATE;
          end
        end
        
        VALIDATE: begin
          resp_length <= 0; // Error replies never reuse previous data.
          // Check version and CRC
          if (!version_valid || !crc_valid) begin
            // Invalid packet, drop silently
            state <= IDLE;
          end else begin
            // Dispatch based on opcode
            case (opcode)
              OP_PING: begin
                if (length == 0) state <= EXECUTE_PING;
                else begin
                  resp_status <= STATUS_INVALID;
                  state <= BUILD_RESPONSE;
                end
              end
              OP_CONFIG: begin
                if (length == 8'd9 && !payload_invalid) begin
                  // Validate rotor and window/ring values
                  if (payload[0] != payload[1] && payload[0] != payload[2] && payload[1] != payload[2]) begin
                    state <= EXECUTE_CONFIG;
                  end else begin
                    resp_status <= STATUS_INVALID;
                    state <= BUILD_RESPONSE;
                  end
                end else begin
                  resp_status <= STATUS_INVALID;
                  state <= BUILD_RESPONSE;
                end
              end
              OP_TRANSFORM: begin
                if (length == 8'd1 && !payload_invalid) begin
                  if (!core_busy) begin
                    state <= EXECUTE_TRANSFORM;
                  end else begin
                    resp_status <= STATUS_BUSY;
                    state <= BUILD_RESPONSE;
                  end
                end else begin
                  resp_status <= STATUS_INVALID;
                  state <= BUILD_RESPONSE;
                end
              end
              OP_READ_STATE: begin
                if (length == 8'd0) begin
                  state <= EXECUTE_READ;
                end else begin
                  resp_status <= STATUS_INVALID;
                  state <= BUILD_RESPONSE;
                end
              end
              OP_RESET: begin
                if (length == 8'd0) begin
                  state <= EXECUTE_RESET;
                end else begin
                  resp_status <= STATUS_INVALID;
                  state <= BUILD_RESPONSE;
                end
              end
              default: begin
                resp_status <= STATUS_UNKNOWN_OP;
                state <= BUILD_RESPONSE;
              end
            endcase
          end
        end
        
        EXECUTE_PING: begin
          resp_status <= STATUS_OK;
          resp_data[0] <= 8'h45;  // 'E'
          resp_data[1] <= 8'h4E;  // 'N'
          resp_data[2] <= 8'h47;  // 'G'
          resp_data[3] <= VERSION;
          resp_length <= 4'd4;
          state <= BUILD_RESPONSE;
        end
        
        EXECUTE_CONFIG: begin
          cfg_write_index <= 4'd0;
          state <= CONFIG_WRITE;
        end
        
        CONFIG_WRITE: begin
          if (cfg_write_index < 4'd9) begin
            core_cfg_we <= 1'b1;
            core_cfg_addr <= cfg_write_index;
            core_cfg_data <= payload[cfg_write_index][4:0];
            cfg_write_index <= cfg_write_index + 1;
          end else begin
            // Response with current windows
            resp_status <= STATUS_OK;
            resp_data[0] <= {3'b000, core_window_left};
            resp_data[1] <= {3'b000, core_window_middle};
            resp_data[2] <= {3'b000, core_window_right};
            resp_length <= 4'd3;
            state <= BUILD_RESPONSE;
          end
        end
        
        EXECUTE_TRANSFORM: begin
          core_letter <= payload[0][4:0];
          core_start <= 1'b1;
          state <= WAIT_CORE;
        end
        
        WAIT_CORE: begin
          if (core_done) begin
            resp_status <= STATUS_OK;
            resp_data[0] <= {3'b000, core_result};
            resp_data[1] <= {3'b000, core_window_left};
            resp_data[2] <= {3'b000, core_window_middle};
            resp_data[3] <= {3'b000, core_window_right};
            resp_length <= 4'd4;
            state <= BUILD_RESPONSE;
          end
        end
        
        EXECUTE_READ: begin
          // Read configuration by reading windows (other values stored in core)
          resp_status <= STATUS_OK;
          resp_data[0] <= {3'b000, core_window_left};
          resp_data[1] <= {3'b000, core_window_middle};
          resp_data[2] <= {3'b000, core_window_right};
          resp_length <= 4'd3;
          state <= BUILD_RESPONSE;
        end
        
        EXECUTE_RESET: begin
          core_rst <= 1'b1;
          resp_status <= STATUS_OK;
          resp_data[0] <= 8'h00;  // AAA windows
          resp_data[1] <= 8'h00;
          resp_data[2] <= 8'h00;
          resp_length <= 4'd3;
          state <= BUILD_RESPONSE;
        end
        
        BUILD_RESPONSE: begin
          // Build response packet and calculate CRC
          tx_index <= 4'd0;
          resp_index <= 4'd0;
          state <= TX_RESPONSE;
        end
        
        TX_RESPONSE: begin
          if (!uart_tx_busy && !uart_tx_start) begin
            case (tx_index)
              4'd0: begin
                // Marker (not in CRC)
                uart_tx_data <= RESP_MARKER;
                uart_tx_start <= 1'b1;
                tx_index <= tx_index + 1;
              end
              4'd1: begin
                // Version
                uart_tx_data <= VERSION;
                uart_tx_start <= 1'b1;
                crc_byte_in <= VERSION;
                crc_update <= 1'b1;
                tx_index <= tx_index + 1;
              end
              4'd2: begin
                // Sequence
                uart_tx_data <= request_sequence;
                uart_tx_start <= 1'b1;
                crc_byte_in <= request_sequence;
                crc_update <= 1'b1;
                tx_index <= tx_index + 1;
              end
              4'd3: begin
                // Opcode with response bit
                uart_tx_data <= opcode | 8'h80;
                uart_tx_start <= 1'b1;
                crc_byte_in <= opcode | 8'h80;
                crc_update <= 1'b1;
                tx_index <= tx_index + 1;
              end
              4'd4: begin
                // Length (1 + resp_length for status + data)
                uart_tx_data <= {4'b0000, resp_length} + 8'd1;
                uart_tx_start <= 1'b1;
                crc_byte_in <= {4'b0000, resp_length} + 8'd1;
                crc_update <= 1'b1;
                tx_index <= tx_index + 1;
              end
              4'd5: begin
                // Status
                uart_tx_data <= resp_status;
                uart_tx_start <= 1'b1;
                crc_byte_in <= resp_status;
                crc_update <= 1'b1;
                tx_index <= tx_index + 1;
              end
              default: begin
                if (resp_index < resp_length) begin
                  // Data bytes
                  uart_tx_data <= resp_data[resp_index[1:0]];
                  uart_tx_start <= 1'b1;
                  crc_byte_in <= resp_data[resp_index[1:0]];
                  crc_update <= 1'b1;
                  resp_index <= resp_index + 1;
                  tx_index <= tx_index + 1;
                end else begin
                  // CRC
                  uart_tx_data <= crc_out;
                  uart_tx_start <= 1'b1;
                  state <= IDLE;
                end
              end
            endcase
          end
        end
        
        default: state <= IDLE;
      endcase
      end
    end
  end

endmodule

// CRC-8 module with polynomial 0x07
// Init: 0x00, no reflection, no final XOR
// Check value: 0xF4 for ASCII "123456789"

module crc8 (
  input clk,
  input rst,
  input [7:0] byte_in,
  input update,
  output reg [7:0] crc_out
);

  // CRC-8 lookup table for polynomial 0x07
  // Table[i] = CRC of byte i with init 0x00
  function automatic [7:0] crc_table;
    input [7:0] index;
    reg [7:0] crc;
    integer i;
    begin
      crc = index;
      for (i = 0; i < 8; i = i + 1) begin
        if (crc[7])
          crc = (crc << 1) ^ 8'h07;
        else
          crc = crc << 1;
      end
      crc_table = crc;
    end
  endfunction

  always @(posedge clk) begin
    if (rst) begin
      crc_out <= 8'h00;
    end else if (update) begin
      // Update CRC: newCRC = table[oldCRC ^ byte_in]
      crc_out <= crc_table(crc_out ^ byte_in);
    end
  end

endmodule

// UART receiver module
// 115200 baud, 8N1 format, with 2-FF synchronizer and framing error detection

module uart_rx #(
  parameter CLKS_PER_BIT = 434  // 50MHz / 115200 = 434
)(
  input clk,
  input rst,
  input rx_serial,
  output reg [7:0] rx_data,
  output reg rx_valid,
  output reg rx_error,
  output reg busy
);

  // 2-FF synchronizer for metastability protection
  reg rx_sync1, rx_sync2;
  
  // State machine
  localparam IDLE = 3'd0;
  localparam START = 3'd1;
  localparam DATA = 3'd2;
  localparam STOP = 3'd3;
  
  reg [2:0] state;
  localparam COUNTER_BITS = $clog2(CLKS_PER_BIT);
  reg [COUNTER_BITS-1:0] clk_count;
  reg [2:0] bit_index;
  reg [7:0] rx_shift;
  
  always @(posedge clk) begin
    if (rst) begin
      rx_sync1 <= 1'b1;
      rx_sync2 <= 1'b1;
      state <= IDLE;
      clk_count <= 0;
      bit_index <= 3'd0;
      rx_shift <= 8'd0;
      rx_data <= 8'd0;
      rx_valid <= 1'b0;
      rx_error <= 1'b0;
      busy <= 1'b0;
    end else begin
      // Synchronizer
      rx_sync1 <= rx_serial;
      rx_sync2 <= rx_sync1;
      
      // Clear pulse outputs
      rx_valid <= 1'b0;
      rx_error <= 1'b0;
      
      case (state)
        IDLE: begin
          busy <= 1'b0;
          clk_count <= 0;
          bit_index <= 3'd0;
          // Detect start bit (idle-to-low transition)
          if (rx_sync2 == 1'b0) begin
            state <= START;
            busy <= 1'b1;
          end
        end
        
        START: begin
          if (clk_count == (CLKS_PER_BIT - 1) / 2) begin
            // Sample at bit center
            if (rx_sync2 == 1'b0) begin
              // Valid start bit
              clk_count <= 0;
              state <= DATA;
            end else begin
              // False start bit (glitch)
              state <= IDLE;
            end
          end else begin
            clk_count <= clk_count + 1;
          end
        end
        
        DATA: begin
          if (clk_count == CLKS_PER_BIT - 1) begin
            clk_count <= 0;
            // Sample data bit (LSB first)
            rx_shift[bit_index] <= rx_sync2;
            
            if (bit_index == 3'd7) begin
              bit_index <= 3'd0;
              state <= STOP;
            end else begin
              bit_index <= bit_index + 1;
            end
          end else begin
            clk_count <= clk_count + 1;
          end
        end
        
        STOP: begin
          if (clk_count == CLKS_PER_BIT - 1) begin
            clk_count <= 0;
            // Check stop bit
            if (rx_sync2 == 1'b1) begin
              // Valid stop bit
              rx_data <= rx_shift;
              rx_valid <= 1'b1;
            end else begin
              // Framing error
              rx_error <= 1'b1;
            end
            state <= IDLE;
          end else begin
            clk_count <= clk_count + 1;
          end
        end
        
        default: state <= IDLE;
      endcase
    end
  end

endmodule

// UART transmitter module
// 115200 baud, 8N1 format

module uart_tx #(
  parameter CLKS_PER_BIT = 434  // 50MHz / 115200 = 434
)(
  input clk,
  input rst,
  input tx_start,
  input [7:0] tx_data,
  output reg tx_serial,
  output reg busy
);

  // State machine
  localparam IDLE = 3'd0;
  localparam START = 3'd1;
  localparam DATA = 3'd2;
  localparam STOP = 3'd3;
  
  reg [2:0] state;
  localparam COUNTER_BITS = $clog2(CLKS_PER_BIT);
  reg [COUNTER_BITS-1:0] clk_count;
  reg [2:0] bit_index;
  reg [7:0] tx_shift;
  
  always @(posedge clk) begin
    if (rst) begin
      state <= IDLE;
      clk_count <= 0;
      bit_index <= 3'd0;
      tx_shift <= 8'd0;
      tx_serial <= 1'b1;
      busy <= 1'b0;
    end else begin
      case (state)
        IDLE: begin
          tx_serial <= 1'b1;
          busy <= 1'b0;
          clk_count <= 0;
          bit_index <= 3'd0;
          
          if (tx_start) begin
            tx_shift <= tx_data;
            busy <= 1'b1;
            state <= START;
          end
        end
        
        START: begin
          tx_serial <= 1'b0;  // Start bit
          
          if (clk_count == CLKS_PER_BIT - 1) begin
            clk_count <= 0;
            state <= DATA;
          end else begin
            clk_count <= clk_count + 1;
          end
        end
        
        DATA: begin
          tx_serial <= tx_shift[bit_index];  // LSB first
          
          if (clk_count == CLKS_PER_BIT - 1) begin
            clk_count <= 0;
            
            if (bit_index == 3'd7) begin
              bit_index <= 3'd0;
              state <= STOP;
            end else begin
              bit_index <= bit_index + 1;
            end
          end else begin
            clk_count <= clk_count + 1;
          end
        end
        
        STOP: begin
          tx_serial <= 1'b1;  // Stop bit
          
          if (clk_count == CLKS_PER_BIT - 1) begin
            clk_count <= 0;
            state <= IDLE;
          end else begin
            clk_count <= clk_count + 1;
          end
        end
        
        default: state <= IDLE;
      endcase
    end
  end

endmodule

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
