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
