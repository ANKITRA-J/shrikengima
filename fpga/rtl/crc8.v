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
