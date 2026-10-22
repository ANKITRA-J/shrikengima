`timescale 1ns/1ps

module led_controller_tb;

  reg clk;
  reg rst;
  reg trigger;
  wire led;
  
  // Instantiate DUT
  led_controller dut (
    .clk(clk),
    .rst(rst),
    .trigger(trigger),
    .led(led)
  );
  
  // Clock generation: 50MHz = 20ns period
  initial begin
    clk = 0;
    forever #10 clk = ~clk;
  end
  
  integer i;
  
  initial begin
    $dumpfile("led_controller_tb.vcd");
    $dumpvars(0, led_controller_tb);
    
    // Initialize
    rst = 1;
    trigger = 0;
    
    repeat(10) @(posedge clk);
    rst = 0;
    repeat(5) @(posedge clk);
    
    $display("=== Test 1: Single 80ms pulse ===");
    // Trigger pulse
    trigger = 1;
    @(posedge clk);
    trigger = 0;
    
    // LED should go high
    if (!led) begin
      $fatal(1, "ERROR: LED did not go high after trigger");
    end
    $display("LED activated");
    
    // Wait for exactly 4,000,000 clocks
    for (i = 0; i < 3999999; i = i + 1) begin
      @(posedge clk);
      if (!led) begin
        $fatal(1, "ERROR: LED went low too early at clock %d", i);
      end
    end
    
    // At clock 4,000,000, LED should go low
    @(posedge clk);
    if (led) begin
      $fatal(1, "ERROR: LED did not go low after 4,000,000 clocks");
    end
    $display("LED deactivated after exactly 4,000,000 clocks");
    $display("Test 1: PASS");
    
    repeat(10) @(posedge clk);
    
    $display("=== Test 2: Retriggerable pulse ===");
    // Trigger pulse
    trigger = 1;
    @(posedge clk);
    trigger = 0;
    
    if (!led) begin
      $fatal(1, "ERROR: LED did not go high after trigger");
    end
    
    // Wait 2,000,000 clocks (halfway)
    for (i = 0; i < 2000000; i = i + 1) begin
      @(posedge clk);
    end
    
    $display("Retriggering at 2,000,000 clocks");
    // Retrigger
    trigger = 1;
    @(posedge clk);
    trigger = 0;
    
    // LED should still be high
    if (!led) begin
      $fatal(1, "ERROR: LED went low after retrigger");
    end
    
    // Now wait another 4,000,000 clocks from retrigger point
    for (i = 0; i < 3999999; i = i + 1) begin
      @(posedge clk);
      if (!led) begin
        $fatal(1, "ERROR: LED went low too early after retrigger at clock %d", i);
      end
    end
    
    @(posedge clk);
    if (led) begin
      $fatal(1, "ERROR: LED did not go low after 4,000,000 clocks from retrigger");
    end
    $display("LED correctly retriggered and stayed high for full 4,000,000 clocks");
    $display("Test 2: PASS");
    
    repeat(10) @(posedge clk);
    
    $display("=== Test 3: Continuous triggers ===");
    // Apply triggers every 1,000,000 clocks
    trigger = 1;
    @(posedge clk);
    trigger = 0;
    
    if (!led) begin
      $fatal(1, "ERROR: LED did not go high");
    end
    
    for (i = 0; i < 10; i = i + 1) begin
      repeat(1000000) @(posedge clk);
      if (!led) begin
        $fatal(1, "ERROR: LED went low during continuous triggers at iteration %d", i);
      end
      trigger = 1;
      @(posedge clk);
      trigger = 0;
    end
    
    $display("LED stayed high during continuous retriggering");
    $display("Test 3: PASS");
    
    $display("");
    $display("========================================");
    $display("ALL LED CONTROLLER TESTS PASSED");
    $display("========================================");
    
    $finish;
  end

endmodule
