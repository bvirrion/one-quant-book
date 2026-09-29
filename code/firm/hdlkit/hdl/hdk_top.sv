// firm.hdlkit: the chapter-6 test top: skid buffer, then field extractor, CRC-32 and comparator on the field.
module hdk_top #(parameter int OFF = 6, parameter int LEN = 4, parameter int PIPE = 1) (
  input  logic        clk,
  input  logic        rst,
  input  logic        in_valid,
  output logic        in_ready,
  input  logic        in_last,
  input  logic [7:0]  in_keep,
  input  logic [63:0] in_data,
  input  logic        out_ready,
  input  logic [63:0] thresh,
  output logic        field_valid,
  output logic [63:0] field,
  output logic        crc_valid,
  output logic [31:0] crc,
  output logic        cmp_valid,
  output logic        cmp_le
);
  logic        s_valid, s_last;
  logic [7:0]  s_keep;
  logic [63:0] s_data;
  logic        beat;

  hdk_skid #(.W(73)) u_skid (.clk, .rst, .in_valid, .in_ready, .in_bits({in_last, in_keep, in_data}),
                             .out_valid(s_valid), .out_ready, .out_bits({s_last, s_keep, s_data}));
  assign beat = s_valid && out_ready;
  hdk_field #(.OFF(OFF), .LEN(LEN)) u_field (.clk, .rst, .beat, .last(s_last), .keep(s_keep), .data(s_data),
                                            .field_valid, .field);
  hdk_crc32 u_crc (.clk, .rst, .beat, .last(s_last), .keep(s_keep), .data(s_data), .crc_valid, .crc);
  hdk_cmp #(.PIPE(PIPE)) u_cmp (.clk, .rst, .in_valid(field_valid), .a(field), .thresh, .out_valid(cmp_valid),
                                .le(cmp_le));
endmodule
