# The clarity bar

The user rejected a sample of harvest titles as not understandable, then called these 50 "much better on the
clarity side". They are the standard for how complete and plain a question must be. Their answers were
computed but are not printed here. They set clarity, not difficulty: the user wants the riddles to reach well
above many of these.

Do not assume any of them will appear in the book as written. A chapter may use one if it fits, like any
other question, with a full answer and tests.

## Probability, riddles and betting
1. You roll two fair six-sided dice and multiply the results. What is the expected value of the product?
2. A bag holds 100 coins: 99 are fair and one has heads on both sides. You draw one at random and flip 10 heads in a row. What is the probability it's the two-headed coin?
3. You turn over a shuffled 52-card deck one card at a time. On average, at which position does the second ace appear?
4. An ant starts at one corner of a cube. At each step it walks along one of the three edges at that corner, chosen at random. On average, how many steps until it reaches the diagonally opposite corner?
5. A drawer holds 4 black and 4 white socks. You take out 4 at random. What is the probability you get exactly two of each colour?
6. You and a friend take turns rolling a die, and you go first. The first to roll a six wins. What is your probability of winning?
7. You keep rolling a die and adding the results until your total is 1,000 or more. Which final total is most likely, and roughly what is its probability?
8. A fair coin is flipped until either heads-heads-tails or tails-heads-heads appears as three consecutive flips. You win if heads-heads-tails comes first. What is your probability of winning?
9. 100 passengers board a plane with 100 assigned seats, in order. The first ignores their ticket and sits in a random seat. Each later passenger takes their own seat if it's free, and otherwise a random free seat. What is the probability the last passenger gets their own seat?
10. You stand at position 3 on a line numbered 0 to 10. Each step moves you one place left or right with equal probability, and you stop on reaching 0 or 10. What is the probability you end at 10, and how many steps do you take on average?
11. You draw random numbers, each uniform between 0 and 1, until their total exceeds 1. On average, how many numbers do you draw?
12. One of 1,000 bottles is poisoned. A test strip dipped in any mix of bottles shows positive the next day if the mix contains poison. All strips must be dipped today. What is the smallest number of strips that identifies the bottle, and how do you use them?
13. Two ropes each burn in exactly one hour, but unevenly along their length. Using only these ropes and a lighter, how do you measure 45 minutes?
14. There are 100 coins on a table. Two players take turns removing 1, 2 or 3 coins, and whoever takes the last coin wins. Do you want to go first or second, and how do you play?
15. You roll a die and receive its value in dollars. After seeing the roll, you may reject it and roll once more, but then you must keep the second result. What is this game worth? What if you may roll up to three times?
16. You can repeatedly make a bet that you win with probability 60%: you gain your stake if you win and lose it if you don't. What fixed fraction of your money should you bet each time to make your wealth grow fastest over the long run?

## Statistics, regression and machine learning
17. You flip a coin 100 times and get 60 heads. Is the coin fair? Show your calculation and state your conclusion.
18. You fit a straight line predicting y from x and get slope b1. You then fit a line predicting x from y and get slope b2. Is b2 equal to 1/b1? What does the product b1 x b2 equal?
19. You copy every row of a dataset, making it twice as long, and refit the same linear regression. What happens to the coefficients and to their standard errors? Why does this matter when your observations overlap in time?
20. Three random variables all have the same correlation rho with one another. What is the lowest possible value of rho, and why can't it go lower?
21. A strategy earns an average of 0.1% per trading day, with a daily standard deviation of 1%. Taking the Sharpe ratio as average return divided by standard deviation, with 252 trading days a year, what is its annual Sharpe ratio? With four years of data, roughly how uncertain is that estimate?
22. Tanks carry serial numbers 1 to N, and N is unknown. You capture five at random, numbered 14, 36, 61, 73 and 92. What is your estimate of N, and why not simply 92?
23. A model predicting whether a stock rises tomorrow scores 60% accuracy when tested by randomly splitting the rows into five groups, but only 50% in live trading. What are the most likely causes, and how should you have tested it?
24. You average the predictions of 100 models. Each prediction has variance 1, and each pair has correlation 0.3. What is the variance of the average? What would it be with 10,000 models, and what does this tell you?

## Markets, options, risk and crypto
25. A stock trades at $100, pays no dividends, and interest rates are zero. A one-year call option, the right to buy at $100, costs $10. What must a one-year put option, the right to sell at $100, cost? Explain why.
26. Three call options on the same stock with the same expiry are priced as follows: the right to buy at $90 costs $12, at $100 costs $7, and at $110 costs $1. Can you make a riskless profit? Give the trades.
27. You own a call option on 100 shares. For each $1 move in the stock, the option's value changes by $0.50 per share. How many shares must you sell short so that small moves leave your wealth unchanged? Why will you need to trade again later?
28. A stock trades at $100 with a volatility of 20%, meaning the standard deviation of its yearly return. Interest rates are zero. Without a calculator, estimate the price of a one-year option to buy it at $100.
29. An option pays $1 if a stock finishes above $100 at expiry and nothing otherwise. How can you approximate it using ordinary call options? Why is it hard to hedge when the stock is close to $100 just before expiry?
30. You own $10 million of a bond whose price falls about 8% for each 1 percentage point rise in yields. Yields rise by 0.25 points. What is your approximate loss, and is that estimate slightly too high or too low?
31. You hold $100 million of a stock index. Daily returns are normally distributed with mean zero and standard deviation 1%. What daily loss is exceeded on only 1% of days? Give one reason this number could mislead you.
32. Two stocks have annual volatilities of 20% and 30%, and their correlation is 0.5. You put half your money in each. What is the volatility of your portfolio?
33. A stock is worth either $90 or $110, with equal probability. Of the people trading with you, 20% know the true value, and the rest buy or sell at random with equal chance. Each trades one share. What is the lowest price at which you can offer to sell without losing money on average?
34. A perpetual future is a contract that tracks Bitcoin's price and never expires. When it trades above the spot price, buyers pay sellers a fee called funding every eight hours. You own 1 Bitcoin at $60,000 and sell one perpetual against it. If funding stays at 0.01% every eight hours, what do you earn in a year, and what are the main risks?
35. An automated exchange holds 100 ETH and $200,000 in a pool, and always keeps the product of the two amounts constant. Ignoring fees, what does it cost to buy 10 ETH? Why is your average price above the starting price of $2,000?
36. A researcher tests 100 variants of a strategy on three years of data, and the best has an annual Sharpe ratio of 1.5. If none has a real edge, how high would you expect the best one to be by luck alone? What would you check before trading it?

## Code and systems
37. What does a Python function `def f(x, items=[])` that appends x to items and returns items give for `f(1)` followed by `print(f(2))`, and why?
38. You're given a list of daily prices and may buy once, then sell once on a later day. Write a function that returns the largest possible profit, using a single pass through the list.
39. Given an array of n numbers and a window size k, return the maximum of every k consecutive numbers. Your solution must run in time proportional to n, regardless of k.
40. Design a cache with a fixed capacity that discards the item used longest ago when it's full. Both reading and inserting an item must take constant time on average. Which data structures do you use?
41. A market receives buy and sell orders, each with a price, a quantity and an ID. Design a data structure that can add an order, cancel an order by ID, and return the highest buy and lowest sell prices. State the time each operation takes.
42. What is wrong with C++ code that takes `int& first = v[0];` from a `std::vector<int>`, calls `v.push_back(4);` and prints `first`, and what might it print?
43. Two threads each increment their own counter, with no locks and no shared variables. The program runs much slower when the two counters sit next to each other in one struct than when they are far apart in memory. Why, and how do you fix it?
44. Two threads each run `count = count + 1` a million times, with no lock, starting from zero. Why can the final value be less than two million? Give two ways to fix it.
45. With double-precision numbers, `(1e16 + 1) - 1e16` gives 0, but `(1e16 - 1e16) + 1` gives 1. Why? How would you accurately sum a list of numbers of very different sizes?
46. A table `trades` has columns `symbol`, `trade_date`, `price` and `quantity`. Write a SQL query giving, for each symbol and day, the volume-weighted average price, defined as the sum of price x quantity divided by the sum of quantity. Include only symbol-days with more than 100 trades.
47. A service receives one million price updates per second across 10,000 symbols. Clients ask for any symbol's average price over the last 60 seconds and need an answer within a millisecond. Design it: how do you store the data, and what happens when a server crashes?

## Final round
48. Explain to a friend with no finance background what a market maker does, how it makes money, and how it can lose money.
49. Describe a project whose result disappointed you. What did you expect, what happened, and what would you do differently?
50. A live strategy you own has lost money three days in a row, each loss larger than any in its backtest. What do you check, in what order, and what would make you turn it off?
