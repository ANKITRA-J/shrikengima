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
