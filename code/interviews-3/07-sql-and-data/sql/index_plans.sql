CREATE TABLE trades (symbol TEXT, ts BIGINT, price DOUBLE);
CREATE INDEX by_symbol_ts ON trades (symbol, ts);

-- Query A
SELECT price FROM trades WHERE symbol = 'AAA' AND ts >= 100;
-- Query B
SELECT price FROM trades WHERE ts >= 100;
-- Query C
SELECT price FROM trades WHERE symbol = 'AAA' ORDER BY ts;
-- Query D
SELECT price FROM trades WHERE symbol = 'AAA' ORDER BY price;
-- Query E
SELECT price FROM trades WHERE substr(symbol, 1, 1) = 'A';
