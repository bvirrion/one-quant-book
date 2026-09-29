// firm.hdlkit: is a 64-bit value at most a threshold? With PIPE = 0 one registered stage compares all 64 bits;
// with PIPE = 1 a first stage compares four 16-bit slices and a second combines them, so each stage has fewer
// levels of logic and the design can close timing at a higher clock, one cycle later (One Quant Book 14, ch. 6).
module hdk_cmp #(parameter int PIPE = 1) (
  input  logic        clk,
  input  logic        rst,
  input  logic        in_valid,
  input  logic [63:0] a,
  input  logic [63:0] thresh,
  output logic        out_valid,
  output logic        le
);
  if (PIPE == 0) begin : g_flat
    always_ff @(posedge clk) begin
      out_valid <= rst ? 1'b0 : in_valid;
      le        <= a <= thresh;
    end
  end else begin : g_two
    logic [3:0] lt, eq;
    logic       v1;
    always_ff @(posedge clk) begin
      v1        <= rst ? 1'b0 : in_valid;
      out_valid <= rst ? 1'b0 : v1;
      for (int s = 0; s < 4; s++) begin
        lt[s] <= a[16 * s +: 16] < thresh[16 * s +: 16];
        eq[s] <= a[16 * s +: 16] == thresh[16 * s +: 16];
      end
      // most significant slice decides unless equal, and so on down
      le <= lt[3] | (eq[3] & (lt[2] | (eq[2] & (lt[1] | (eq[1] & (lt[0] | eq[0]))))));
    end
  end
endmodule
