// firm.hwtrade Icarus testbench: the same stimulus, registers and output lines as tb/hwt_tb.cpp.
module hwt_tb;
  parameter int LOC = 1;
  parameter int BURST = 4;
  parameter int REFILL = 64;
  logic clk = 0, rst = 1, in_valid = 0, in_last = 0, kill = 0;
  logic [7:0] in_keep = 0;
  logic [63:0] in_data = 0;
  logic [31:0] thresh, max_qty, order_id, order_qty, order_price;
  logic order_valid;
  logic [15:0] rejects;
  hwt_trigger #(.LOC(LOC), .BURST(BURST), .REFILL(REFILL)) dut (.*);

  bit idle[$];
  bit lastq[$];
  logic [7:0] keepq[$];
  logic [63:0] dataq[$];
  initial begin
    int fd, rc, l, n, cycle, kill_at;
    string kind, sfile;
    logic [7:0] k;
    logic [63:0] d;
    bit have;
    if (!$value$plusargs("stim=%s", sfile) || !$value$plusargs("thresh=%d", thresh) ||
        !$value$plusargs("maxq=%d", max_qty) || !$value$plusargs("kill=%d", kill_at))
      $fatal(1, "usage: +stim= +thresh= +maxq= +kill=");
    fd = $fopen(sfile, "r");
    while ($fscanf(fd, "%s", kind) == 1) begin
      if (kind == "I") begin idle.push_back(1); lastq.push_back(0); keepq.push_back(0); dataq.push_back(0); end
      else begin
        rc = $fscanf(fd, "%d %h %h", l, k, d);
        idle.push_back(0); lastq.push_back(l != 0); keepq.push_back(k); dataq.push_back(d);
      end
    end
    $fclose(fd);
    repeat (2) begin clk = 0; #1; clk = 1; #1; end
    rst = 0;
    n = idle.size();
    for (cycle = 0; cycle < n + 8; cycle++) begin
      have = cycle < n && !idle[cycle];
      in_valid = have;
      if (have) begin in_last = lastq[cycle]; in_keep = keepq[cycle]; in_data = dataq[cycle]; end
      kill = kill_at >= 0 && cycle >= kill_at;
      clk = 0;
      #1;
      clk = 1;
      #1;
      if (order_valid) $display("%0d O %0d %0d %0d", cycle, order_id, order_qty, order_price);
    end
    $display("R %0d", rejects);
    $finish;
  end
endmodule
