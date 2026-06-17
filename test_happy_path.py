#!/usr/bin/env python
"""
Complete end-to-end test of FitFindr showing the full happy path

Demonstrates: query parsing → search → outfit suggestion → fit card generation
"""

print("="*70)
print("FitFindr End-to-End Happy Path Test")
print("="*70)

from agent import run_agent
from utils.data_loader import get_example_wardrobe

# The complete query from the planning.md walkthrough
user_query = "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers."

print(f"\nUser Query: {user_query}")
print("-" * 70)

# Run the full agent
session = run_agent(user_query, get_example_wardrobe())

# Display the results step by step
print("\n[STEP 1] Query Parsing")
print(f"  Description: '{session['parsed']['description']}'")
print(f"  Size: {session['parsed']['size']}")
print(f"  Max Price: ${session['parsed']['max_price']}")

print("\n[STEP 2] Search Results")
print(f"  Total matches: {len(session['search_results'])}")
if session['search_results']:
    for i, item in enumerate(session['search_results'][:3], 1):
        print(f"  {i}. {item['title']} — ${item['price']} ({item['platform']})")

print("\n[STEP 3] Item Selection")
if session['selected_item']:
    item = session['selected_item']
    print(f"  Selected: {item['title']}")
    print(f"  Price: ${item['price']}")
    print(f"  Platform: {item['platform']}")
    print(f"  Condition: {item['condition']}")
    print(f"  Size: {item['size']}")
    print(f"  Category: {item['category']}")
    print(f"  Colors: {', '.join(item['colors'])}")
    print(f"  Style: {', '.join(item['style_tags'][:3])}...")

print("\n[STEP 4] Outfit Suggestion (with user's wardrobe)")
if session['outfit_suggestion']:
    outfit = session['outfit_suggestion']
    print(f"  Suggestion ({len(outfit)} chars):")
    # Print with line wrapping
    for line in outfit.split('\n'):
        print(f"    {line}")

print("\n[STEP 5] Fit Card Generation")
if session['fit_card']:
    caption = session['fit_card']
    print(f"  Caption ({len(caption)} chars):")
    # Print with line wrapping
    for line in caption.split('\n'):
        print(f"    {line}")

print("\n[FINAL STATE] Session Dict")
print(f"  Error: {session['error']}")
print(f"  Search results count: {len(session['search_results'])}")
print(f"  Selected item ID: {session['selected_item']['id'] if session['selected_item'] else 'None'}")
print(f"  Outfit suggestion length: {len(session['outfit_suggestion']) if session['outfit_suggestion'] else 0}")
print(f"  Fit card length: {len(session['fit_card']) if session['fit_card'] else 0}")

# Verify success
assert session['error'] is None, "Should have no error"
assert session['selected_item'] is not None, "Should have selected item"
assert len(session['outfit_suggestion']) > 0, "Should have outfit suggestion"
assert len(session['fit_card']) > 0, "Should have fit card"

print("\n" + "="*70)
print("✅ FULL HAPPY PATH SUCCESSFUL")
print("="*70)
print(f"""
The complete flow worked:
1. Parsed natural language query into structured parameters
2. Searched and found {len(session['search_results'])} matching items
3. Selected top result: {session['selected_item']['title']}
4. Generated outfit suggestions referencing specific wardrobe pieces
5. Created an authentic Instagram-style caption

The session contains everything needed to display all three output panels.
""")
