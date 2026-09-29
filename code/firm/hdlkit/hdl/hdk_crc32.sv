// firm.hdlkit: CRC-32 (IEEE 802.3 polynomial, reflected, initial and final value 0xFFFFFFFF) over each frame,
// up to 8 bytes per beat (One Quant Book 14, chapter 6). crc_valid rises the cycle after the last beat.
module hdk_crc32 (
  input  logic        clk,
  input  logic        rst,
  input  logic        beat,
  input  logic        last,
  input  logic [7:0]  keep,
  input  logic [63:0] data,
  output logic        crc_valid,
  output logic [31:0] crc
);
  logic [31:0] state, next;

  function automatic logic [31:0] step(input logic [31:0] c, input logic [7:0] b);
    logic [31:0] x;
    x = c ^ {24'd0, b};
    for (int k = 0; k < 8; k++) x = x[0] ? ((x >> 1) ^ 32'hEDB88320) : (x >> 1);
    return x;
  endfunction

  always @(*) begin                  // always @(*): Icarus 11 limits always_comb with selects
    next = state;
    for (int i = 0; i < 8; i++)
      if (keep[7 - i]) next = step(next, data[63 - 8 * i -: 8]);
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      state     <= 32'hFFFFFFFF;
      crc_valid <= 1'b0;
    end else begin
      crc_valid <= 1'b0;
      if (beat) begin
        if (last) begin
          crc       <= ~next;
          crc_valid <= 1'b1;
          state     <= 32'hFFFFFFFF;
        end else begin
          state <= next;
        end
      end
    end
  end
endmodule
