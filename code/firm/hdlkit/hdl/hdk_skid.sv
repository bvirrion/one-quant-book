// firm.hdlkit: a skid buffer on a valid/ready stream (One Quant Book 14, chapter 6).
// The upstream sees a registered ready; when the downstream stalls, the one beat already in flight is kept in the
// skid register instead of being lost. Output is registered: one cycle of latency, full throughput.
module hdk_skid #(parameter int W = 73) (
  input  logic         clk,
  input  logic         rst,
  input  logic         in_valid,
  output logic         in_ready,
  input  logic [W-1:0] in_bits,
  output logic         out_valid,
  input  logic         out_ready,
  output logic [W-1:0] out_bits
);
  logic         skid_valid;
  logic [W-1:0] skid_bits;

  always_ff @(posedge clk) begin
    if (rst) begin
      out_valid  <= 1'b0;
      skid_valid <= 1'b0;
      in_ready   <= 1'b1;
    end else begin
      if (out_ready || !out_valid) begin
        // the output register is free: fill it from the skid register first, else from the input
        if (skid_valid) begin
          out_bits   <= skid_bits;
          out_valid  <= 1'b1;
          skid_valid <= 1'b0;
        end else begin
          out_bits  <= in_bits;
          out_valid <= in_valid && in_ready;
        end
        in_ready <= 1'b1;
      end else if (in_valid && in_ready) begin
        // the output is stalled and a beat arrives: keep it, and stop accepting
        skid_bits  <= in_bits;
        skid_valid <= 1'b1;
        in_ready   <= 1'b0;
      end
    end
  end
endmodule
