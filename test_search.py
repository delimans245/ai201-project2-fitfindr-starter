#!/usr/bin/env python
from tools import search_listings

results = search_listings('vintage graphic tee', size=None, max_price=50)
print(f'Found {len(results)} results')
if results:
    print(f'Top result: {results[0]["title"]} - ${results[0]["price"]}')
    
# Test empty results
empty_results = search_listings('designer ballgown', size='XXS', max_price=5)
print(f'Empty search found {len(empty_results)} results (expected 0)')

# Test price filter
price_filtered = search_listings('jacket', size=None, max_price=30)
print(f'Price filtered: {len(price_filtered)} results, all under $30')
if price_filtered:
    for item in price_filtered:
        assert item['price'] <= 30, f"Item {item['title']} is ${item['price']}, should be <= 30"
print('All price filters passed!')
