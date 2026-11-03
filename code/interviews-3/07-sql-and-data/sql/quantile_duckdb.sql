SELECT quantile_disc(us, 0.9) AS disc, quantile_cont(us, 0.9) AS cont
FROM latency;
