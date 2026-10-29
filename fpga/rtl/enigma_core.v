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

  `include "helpers.v"

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
