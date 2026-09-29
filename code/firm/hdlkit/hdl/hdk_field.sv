// firm.hdlkit: extract a big-endian field of LEN bytes at byte offset OFF of each frame, on the fly
// (One Quant Book 14, chapter 6). Beats are 8 bytes, byte 0 of a beat in data[63:56]; keep marks valid bytes
// (contiguous from byte 0). The field is registered: field_valid rises the cycle after the beat that completes it.
module hdk_field #(parameter int OFF = 6, parameter int LEN = 4) (
  input  logic        clk,
  input  logic        rst,
  input  logic        beat,          // a beat is accepted this cycle
  input  logic        last,
  input  logic [7:0]  keep,
  input  logic [63:0] data,
  output logic        field_valid,
  output logic [63:0] field
);
  logic [15:0] base;                 // byte position of this beat's byte 0 within the frame
  logic [63:0] acc, acc_next;
  logic        done_next;
  int          pos;

  always_comb begin
    acc_next  = acc;
    done_next = 1'b0;
    for (int i = 0; i < 8; i++) begin
      pos = int'(base) + i;
      if (keep[7 - i] && pos >= OFF && pos < OFF + LEN) begin
        acc_next = (acc_next << 8) | {56'd0, data[63 - 8 * i -: 8]};
        if (pos == OFF + LEN - 1) done_next = 1'b1;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      base        <= '0;
      acc         <= '0;
      field_valid <= 1'b0;
    end else begin
      field_valid <= 1'b0;
      if (beat) begin
        acc  <= last ? '0 : acc_next;
        base <= last ? '0 : base + 16'd8;
        if (done_next) begin
          field       <= acc_next;
          field_valid <= 1'b1;
        end
      end
    end
  end
endmodule
