`timescale 1ns/1ps

module enigma_core_tb;

  reg clk;
  reg rst;
  reg start;
  reg [4:0] letter;
  reg cfg_we;
  reg [3:0] cfg_addr;
  reg [4:0] cfg_data;
  wire busy;
  wire done;
  wire [4:0] result;
  wire [4:0] window_left;
  wire [4:0] window_middle;
  wire [4:0] window_right;
  
  // Instantiate DUT
  enigma_core dut (
    .clk(clk),
    .rst(rst),
    .start(start),
    .letter(letter),
    .cfg_we(cfg_we),
    .cfg_addr(cfg_addr),
    .cfg_data(cfg_data),
    .busy(busy),
    .done(done),
    .result(result),
    .window_left(window_left),
    .window_middle(window_middle),
    .window_right(window_right)
  );
  
  // Clock generation: 50MHz = 20ns period
  initial begin
    clk = 0;
    forever #10 clk = ~clk;
  end
  
  // Timeout watchdog
  initial begin
    #100000000; // 100ms timeout
    $display("ERROR: Testbench timeout");
    $fatal(1, "Simulation timeout");
  end
  
  // Test vectors
  integer i;
  reg [4:0] expected_result;
  reg [4:0] expected_left, expected_middle, expected_right;
  integer timeout_counter;
  
  initial begin
    $dumpfile("enigma_core_tb.vcd");
    $dumpvars(0, enigma_core_tb);
    
    // Initialize
    rst = 1;
    start = 0;
    letter = 0;
    cfg_we = 0;
    cfg_addr = 0;
    cfg_data = 0;
    
    // Apply reset
    repeat(5) @(posedge clk);
    rst = 0;
    repeat(2) @(posedge clk);
    
    $display("=== Test Case 1: AAAAA -> BDZGO ===");
    // Default config is I,II,III (0,1,2), AAA windows, AAA rings
    
    // Test A -> B, windows AAA -> AAB
    test_letter(5'd0, 5'd1, 5'd0, 5'd0, 5'd1);
    
    // Test A -> D, windows AAB -> AAC
    test_letter(5'd0, 5'd3, 5'd0, 5'd0, 5'd2);
    
    // Test A -> Z, windows AAC -> AAD
    test_letter(5'd0, 5'd25, 5'd0, 5'd0, 5'd3);
    
    // Test A -> G, windows AAD -> AAE
    test_letter(5'd0, 5'd6, 5'd0, 5'd0, 5'd4);
    
    // Test A -> O, windows AAE -> AAF
    test_letter(5'd0, 5'd14, 5'd0, 5'd0, 5'd5);
    
    $display("Test Case 1: PASS");
    
    $display("=== Test Case 2: HELLOWORLD -> ILBDAAMTAZ ===");
    // Reset and reconfigure to AAA
    rst = 1;
    repeat(5) @(posedge clk);
    rst = 0;
    repeat(2) @(posedge clk);
    
    test_letter(5'd7, 5'd8, 5'd0, 5'd0, 5'd1);   // H -> I
    test_letter(5'd4, 5'd11, 5'd0, 5'd0, 5'd2);  // E -> L
    test_letter(5'd11, 5'd1, 5'd0, 5'd0, 5'd3);  // L -> B
    test_letter(5'd11, 5'd3, 5'd0, 5'd0, 5'd4);  // L -> D
    test_letter(5'd14, 5'd0, 5'd0, 5'd0, 5'd5);  // O -> A
    test_letter(5'd22, 5'd0, 5'd0, 5'd0, 5'd6);  // W -> A
    test_letter(5'd14, 5'd12, 5'd0, 5'd0, 5'd7); // O -> M
    test_letter(5'd17, 5'd19, 5'd0, 5'd0, 5'd8); // R -> T
    test_letter(5'd11, 5'd0, 5'd0, 5'd0, 5'd9);  // L -> A
    test_letter(5'd3, 5'd25, 5'd0, 5'd0, 5'd10); // D -> Z
    
    $display("Test Case 2: PASS");
    
    $display("=== Test Case 3: Double-stepping ADU sequence ===");
    // Configure windows to ADU (0, 3, 20)
    rst = 1;
    repeat(5) @(posedge clk);
    rst = 0;
    repeat(2) @(posedge clk);
    
    // Set window positions
    cfg_we = 1;
    cfg_addr = 4'd3; cfg_data = 5'd0; @(posedge clk);  // Left = A
    cfg_addr = 4'd4; cfg_data = 5'd3; @(posedge clk);  // Middle = D
    cfg_addr = 4'd5; cfg_data = 5'd20; @(posedge clk); // Right = U
    cfg_we = 0;
    repeat(2) @(posedge clk);
    
    // Letter 1: ADU -> ADV (right steps, not at notch yet)
    test_letter_nocheck(5'd0);
    check_windows(5'd0, 5'd3, 5'd21, "After letter 1: ADU->ADV");
    
    // Letter 2: ADV -> AEW (right at notch V(21), double-step: middle D->E, left A->B... wait, need to check)
    // Actually: right at V(21) which is turnover for rotor III
    // Middle at D(3), not at turnover E(4) for rotor II
    // So: right steps V->W, middle steps D->E (because right at notch), left doesn't step
    test_letter_nocheck(5'd0);
    check_windows(5'd0, 5'd4, 5'd22, "After letter 2: ADV->AEW");
    
    // Letter 3: AEW -> BFX (middle at E(4), which is turnover for rotor II, so left steps, middle steps)
    test_letter_nocheck(5'd0);
    check_windows(5'd1, 5'd5, 5'd23, "After letter 3: AEW->BFX");
    
    // Letter 4: BFX -> BFY (only right steps)
    test_letter_nocheck(5'd0);
    check_windows(5'd1, 5'd5, 5'd24, "After letter 4: BFX->BFY");
    
    $display("Test Case 3: PASS");
    
    $display("=== Test Case 4: Wraparound XYZ -> XZA ===");
    rst = 1;
    repeat(5) @(posedge clk);
    rst = 0;
    repeat(2) @(posedge clk);
    
    cfg_we = 1;
    cfg_addr = 4'd3; cfg_data = 5'd23; @(posedge clk); // Left = X
    cfg_addr = 4'd4; cfg_data = 5'd24; @(posedge clk); // Middle = Y
    cfg_addr = 4'd5; cfg_data = 5'd25; @(posedge clk); // Right = Z
    cfg_we = 0;
    repeat(2) @(posedge clk);
    
    test_letter_nocheck(5'd0);
    check_windows(5'd23, 5'd25, 5'd0, "After wraparound: XYZ->XZA");
    
    $display("Test Case 4: PASS");
    
    $display("=== Test Case 5: Non-A rings BCD ===");
    rst = 1;
    repeat(5) @(posedge clk);
    rst = 0;
    repeat(2) @(posedge clk);
    
    // Set rings to BCD (1,2,3)
    cfg_we = 1;
    cfg_addr = 4'd6; cfg_data = 5'd1; @(posedge clk); // Left ring = B
    cfg_addr = 4'd7; cfg_data = 5'd2; @(posedge clk); // Middle ring = C
    cfg_addr = 4'd8; cfg_data = 5'd3; @(posedge clk); // Right ring = D
    cfg_we = 0;
    repeat(2) @(posedge clk);
    
    // Feed 5 A's - results will differ from AAA ring setting
    // Just verify it completes and windows advance correctly
    for (i = 0; i < 5; i = i + 1) begin
      test_letter_nocheck(5'd0);
    end
    check_windows(5'd0, 5'd0, 5'd5, "After 5 letters with BCD rings");
    
    $display("Test Case 5: PASS");
    
    $display("=== Test Case 6: Invalid inputs ===");
    rst = 1;
    repeat(5) @(posedge clk);
    rst = 0;
    repeat(2) @(posedge clk);
    
    // Try invalid letter (26)
    start = 1;
    letter = 5'd26;
    @(posedge clk);
    start = 0;
    repeat(10) @(posedge clk);
    if (done) begin
      $fatal(1, "ERROR: Core accepted invalid letter 26");
    end
    $display("Invalid letter correctly rejected");
    
    // Try start while busy
    letter = 5'd0;
    start = 1;
    @(posedge clk);
    start = 0;
    @(posedge clk);
    // Core should be busy now
    if (busy) begin
      start = 1; // Try to start again
      @(posedge clk);
      start = 0;
      // Wait for first operation to complete
      timeout_counter = 0;
      while (!done && timeout_counter < 100) begin
        @(posedge clk);
        timeout_counter = timeout_counter + 1;
      end
      @(posedge clk);
      // Check that windows only advanced once
      if (window_right != 5'd1) begin
        $fatal(1, "ERROR: Start while busy was not ignored, window_right=%d", window_right);
      end
      $display("Start while busy correctly ignored");
    end
    
    $display("Test Case 6: PASS");
    
    $display("");
    $display("========================================");
    $display("ALL TESTS PASSED");
    $display("========================================");
    
    $finish;
  end
  
  // Task to test a letter and check result and windows
  task test_letter;
    input [4:0] in_letter;
    input [4:0] exp_result;
    input [4:0] exp_left;
    input [4:0] exp_middle;
    input [4:0] exp_right;
    begin
      letter = in_letter;
      start = 1;
      @(posedge clk);
      start = 0;
      
      // Wait for done with timeout
      timeout_counter = 0;
      while (!done && timeout_counter < 64) begin
        @(posedge clk);
        timeout_counter = timeout_counter + 1;
      end
      
      if (timeout_counter >= 64) begin
        $fatal(1, "ERROR: Core timeout after 64 clocks");
      end
      
      if (result != exp_result) begin
        $fatal(1, "ERROR: Expected result %d, got %d for letter %d", 
               exp_result, result, in_letter);
      end
      
      if (window_left != exp_left || window_middle != exp_middle || window_right != exp_right) begin
        $fatal(1, "ERROR: Window mismatch. Expected %d%d%d, got %d%d%d",
               exp_left, exp_middle, exp_right,
               window_left, window_middle, window_right);
      end
      
      @(posedge clk); // Wait one more cycle
    end
  endtask
  
  // Task to test a letter without checking result (for complex sequences)
  task test_letter_nocheck;
    input [4:0] in_letter;
    begin
      letter = in_letter;
      start = 1;
      @(posedge clk);
      start = 0;
      
      timeout_counter = 0;
      while (!done && timeout_counter < 64) begin
        @(posedge clk);
        timeout_counter = timeout_counter + 1;
      end
      
      if (timeout_counter >= 64) begin
        $fatal(1, "ERROR: Core timeout after 64 clocks");
      end
      
      @(posedge clk);
    end
  endtask
  
  // Task to check window values
  task check_windows;
    input [4:0] exp_left;
    input [4:0] exp_middle;
    input [4:0] exp_right;
    input [80*8:1] msg;
    begin
      if (window_left != exp_left || window_middle != exp_middle || window_right != exp_right) begin
        $display("%s", msg);
        $fatal(1, "ERROR: Window mismatch. Expected %d%d%d, got %d%d%d",
               exp_left, exp_middle, exp_right,
               window_left, window_middle, window_right);
      end
      $display("%s: %d%d%d OK", msg, window_left, window_middle, window_right);
    end
  endtask

endmodule
