import sys
sys.path.append('.')
from modules import finance
query = 'How much is 1000 AED in INR?'
print('Tickers:', finance.extract_tickers(query))
print('Summary:')
print(finance.get_market_data(query)['summary'])
