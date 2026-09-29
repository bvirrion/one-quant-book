// firm.hwtrade: a hardware trigger on the exchange simulator's feed (One Quant Book 14, chapter 7).
// Input: MoldUDP64 packets (the UDP payload), 8 bytes a beat, byte 0 in data[63:56], `last` on a packet's final beat.
// Stage 1 (parse): a byte-serial state machine, unrolled over the beat's 8 lanes, walks the 20-byte header and each
//   length-prefixed message; at the last byte of an add-order message ('A', 36 bytes) for instrument LOC on the sell
//   side at a price at most `thresh` (a register software writes), it registers a trigger with the order's size and
//   price. A message is at least 14 bytes with its prefix, so a beat completes at most one message.
// Stage 2 (risk): rejects sizes above `max_qty`, drops everything while `kill` is set, and rations orders with a
//   token bucket (BURST tokens, one more every REFILL cycles).
// Stage 3 (template): patches client order id, size and price into the order template and presents the order.
module hwt_trigger #(parameter int LOC = 1, parameter int BURST = 4, parameter int REFILL = 64) (
  input  logic        clk,
  input  logic        rst,
  input  logic        in_valid,
  input  logic        in_last,
  input  logic [7:0]  in_keep,
  input  logic [63:0] in_data,
  input  logic [31:0] thresh,
  input  logic [31:0] max_qty,
  input  logic        kill,
  output logic        order_valid,
  output logic [31:0] order_id,
  output logic [31:0] order_qty,
  output logic [31:0] order_price,
  output logic [15:0] rejects
);
  // parse state, carried from byte to byte
  logic [15:0] ppos, mlen, mpos;
  logic [1:0]  lstate;               // 0 header, 1 length high byte, 2 length low byte, 3 message body
  logic [7:0]  mtype, mside;
  logic [15:0] mloc;
  logic [31:0] mqty, mprice;
  // next-state values computed over the beat's lanes
  logic [15:0] n_ppos, n_mlen, n_mpos;
  logic [1:0]  n_lstate;
  logic [7:0]  n_mtype, n_mside, b;
  logic [15:0] n_mloc;
  logic [31:0] n_mqty, n_mprice;
  logic        n_trig;
  logic [31:0] n_tqty, n_tprice;

  always @(*) begin
    {n_ppos, n_mlen, n_mpos, n_lstate} = {ppos, mlen, mpos, lstate};
    {n_mtype, n_mside, n_mloc, n_mqty, n_mprice} = {mtype, mside, mloc, mqty, mprice};
    n_trig = 1'b0;
    n_tqty = '0;
    n_tprice = '0;
    for (int i = 0; i < 8; i++) begin
      if (in_keep[7 - i]) begin
        b = in_data[63 - 8 * i -: 8];
        case (n_lstate)
          2'd0: if (n_ppos == 16'd19) n_lstate = 2'd1;
          2'd1: begin n_mlen[15:8] = b; n_lstate = 2'd2; end
          2'd2: begin n_mlen[7:0] = b; n_mpos = '0; n_lstate = 2'd3; end
          default: begin
            if (n_mpos == 16'd0) n_mtype = b;
            if (n_mpos == 16'd1) n_mloc[15:8] = b;
            if (n_mpos == 16'd2) n_mloc[7:0] = b;
            if (n_mpos == 16'd19) n_mside = b;
            if (n_mpos >= 16'd20 && n_mpos <= 16'd23) n_mqty = {n_mqty[23:0], b};
            if (n_mpos >= 16'd32 && n_mpos <= 16'd35) n_mprice = {n_mprice[23:0], b};
            if (n_mpos + 16'd1 == n_mlen) begin
              if (n_mtype == "A" && n_mlen == 16'd36 && n_mloc == LOC[15:0] && n_mside == "S"
                  && n_mprice <= thresh) begin
                n_trig = 1'b1;
                n_tqty = n_mqty;
                n_tprice = n_mprice;
              end
              n_lstate = 2'd1;
            end
            n_mpos = n_mpos + 16'd1;
          end
        endcase
        n_ppos = n_ppos + 16'd1;
      end
    end
  end

  // stage registers
  logic        trig;
  logic [31:0] tqty, tprice;
  logic [15:0] tokens, since;
  logic        pass;
  logic [31:0] pqty, pprice, next_id;

  always_ff @(posedge clk) begin
    if (rst) begin
      {ppos, mlen, mpos, lstate} <= '0;
      {mtype, mside, mloc, mqty, mprice} <= '0;
      trig <= 1'b0;
      pass <= 1'b0;
      order_valid <= 1'b0;
      tokens <= 16'(BURST);
      since <= '0;
      next_id <= 32'd1;
      rejects <= '0;
    end else begin
      // stage 1: parse the beat
      trig <= 1'b0;
      if (in_valid) begin
        {mlen, mpos, lstate} <= {n_mlen, n_mpos, n_lstate};
        {mtype, mside, mloc, mqty, mprice} <= {n_mtype, n_mside, n_mloc, n_mqty, n_mprice};
        ppos <= in_last ? 16'd0 : n_ppos;
        if (in_last) lstate <= 2'd0;
        trig <= n_trig;
        tqty <= n_tqty;
        tprice <= n_tprice;
      end
      // stage 2: risk, with the token bucket refilled every REFILL cycles
      pass <= 1'b0;
      if (since + 16'd1 == 16'(REFILL)) begin
        since <= '0;
        if (tokens < 16'(BURST)) tokens <= tokens + 16'd1;
      end else begin
        since <= since + 16'd1;
      end
      if (trig) begin
        if (kill || tqty > max_qty || tokens == 16'd0) begin
          rejects <= rejects + 16'd1;
        end else begin
          pass <= 1'b1;
          pqty <= tqty;
          pprice <= tprice;
          tokens <= tokens - 16'd1
                    + ((since + 16'd1 == 16'(REFILL) && tokens < 16'(BURST)) ? 16'd1 : 16'd0);
        end
      end
      // stage 3: the order template, patched
      order_valid <= pass && !kill;
      if (pass) begin
        order_id <= next_id;
        order_qty <= pqty;
        order_price <= pprice;
        if (!kill) next_id <= next_id + 32'd1;
      end
    end
  end
endmodule
