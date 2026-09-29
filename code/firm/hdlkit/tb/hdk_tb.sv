// firm.hdlkit Icarus testbench for hdk_top: the same stimulus, pattern and output lines as tb/hdk_tb.cpp.
module hdk_tb;
  parameter int OFF = 6;
  parameter int LEN = 4;
  parameter int PIPE = 1;
  logic clk = 0, rst = 1, in_valid = 0, in_ready, in_last = 0, out_ready = 1;
  logic [7:0] in_keep = 0;
  logic [63:0] in_data = 0, thresh, field;
  logic field_valid, crc_valid, cmp_valid, cmp_le;
  logic [31:0] crc;
  hdk_top #(.OFF(OFF), .LEN(LEN), .PIPE(PIPE)) dut (.*);

  bit idle[$];
  bit lastq[$];
  logic [7:0] keepq[$];
  logic [63:0] dataq[$];
  int ready[$];
  initial begin
    int fd, fr, rc, l, n, cycle, next, v;
    string kind, sfile, rfile;
    logic [7:0] k;
    logic [63:0] d;
    bit have, accepted, idle_now;
    if (!$value$plusargs("stim=%s", sfile) || !$value$plusargs("ready=%s", rfile) ||
        !$value$plusargs("thresh=%h", thresh)) $fatal(1, "usage: +stim= +ready= +thresh=");
    fd = $fopen(sfile, "r");
    while ($fscanf(fd, "%s", kind) == 1) begin
      if (kind == "I") begin idle.push_back(1); lastq.push_back(0); keepq.push_back(0); dataq.push_back(0); end
      else begin
        rc = $fscanf(fd, "%d %h %h", l, k, d);
        idle.push_back(0); lastq.push_back(l != 0); keepq.push_back(k); dataq.push_back(d);
      end
    end
    $fclose(fd);
    fr = $fopen(rfile, "r");
    while ($fscanf(fr, "%d", v) == 1) ready.push_back(v);
    $fclose(fr);
    repeat (2) begin clk = 0; #1; clk = 1; #1; end
    rst = 0;
    next = 0;
    n = idle.size();
    for (cycle = 0; cycle < n * 4 + 64; cycle++) begin
      idle_now = next < n && idle[next];
      have = next < n && !idle_now;
      in_valid = have;
      if (have) begin in_last = lastq[next]; in_keep = keepq[next]; in_data = dataq[next]; end
      out_ready = ready[cycle % ready.size()] != 0;
      clk = 0;
      #1;
      accepted = have && in_ready;
      clk = 1;
      #1;
      if (accepted) begin $display("%0d I", cycle); next++; end
      if (idle_now) next++;
      if (field_valid) $display("%0d F %016h", cycle, field);
      if (crc_valid) $display("%0d C %08h", cycle, crc);
      if (cmp_valid) $display("%0d M %0d", cycle, cmp_le);
    end
    $finish;
  end
endmodule
