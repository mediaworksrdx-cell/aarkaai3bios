text = """A stock might rise after reporting lower earnings due to several reasons:

1. Market sentiment: If the market is generally bullish and investors are optimistic about the company's future prospects, even if they have reported lower earnings, it may lead to a positive reaction in the stock price.
2. Analysts' expectations: If analysts were expecting lower earnings or had already factored them into their estimates, reporting lower earnings might not significantly impact the stock price.
3. Industry trends: The company's industry may be experiencing strong growth or recovery, which could offset any negative effects of lower earnings on individual companies within that sector.
4. Positive news: If there are other positive developments related to the company, such as a new product launch, acquisition, or strategic partnership, it might outweigh the impact of lower earnings and lead to an increase in stock price.
5. Investor sentiment: If investors believe the company's management team is capable of turning things around, they may be more willing to invest in the stock despite lower earnings, leading to an upward trend in the stock price.
6. Market conditions: Factors such as rising interest rates or a shift towards lower-risk investments could potentially cause stocks to fall across the board and result in stock losses for individual companies, including those with lower-than-expected earnings.
7. Investor psychology: Investors may be more willing to take risks on a company that has reported lower earnings if they believe it is undervalued compared to its competitors or industry peers.
8. """

import re
words = re.findall(r'\b\w+\b', text.lower())
n = len(words)
print("Total words:", n)

window_size = 15
last_window = words[-window_size:]
print("Last window:", last_window)

found = False
for i in range(n - 2 * window_size):
    if words[i:i+window_size] == last_window:
        print(f"Match found at index {i}:")
        print(words[i:i+window_size])
        found = True

if not found:
    print("No match found in the printed text.")
