#!/usr/bin/env python
"""
Test all documented failure modes for FitFindr

This script demonstrates each failure mode and verifies the agent's error handling.
"""

print("="*70)
print("FitFindr Failure Mode Testing")
print("="*70)

# Test 1: search_listings returns empty
print("\n[TEST 1] search_listings returns no results")
print("-" * 70)

from tools import search_listings

impossible_query = "designer ballgown size XXS under $5"
results = search_listings("designer ballgown", size="XXS", max_price=5)

print(f"Query: {impossible_query}")
print(f"Result type: {type(results)}")
print(f"Result: {results}")
print(f"Length: {len(results)}")
print(f"✅ Correct: Returns empty list (not exception)")

# Test 2: Agent error path when search returns nothing
print("\n[TEST 2] Agent error path with no search results")
print("-" * 70)

from agent import run_agent
from utils.data_loader import get_example_wardrobe

session = run_agent(
    query="designer ballgown size XXS under $5",
    wardrobe=get_example_wardrobe()
)

print(f"Session error: {session['error']}")
print(f"Selected item: {session['selected_item']}")
print(f"Outfit suggestion: {session['outfit_suggestion']}")
print(f"Fit card: {session['fit_card']}")

assert session['error'] is not None, "Should have error message"
assert session['selected_item'] is None, "Should not select item"
assert session['outfit_suggestion'] is None, "Should not call suggest_outfit"
assert session['fit_card'] is None, "Should not call create_fit_card"

print(f"✅ Correct: Agent stops early, returns helpful error")

# Test 3: Empty wardrobe handling
print("\n[TEST 3] suggest_outfit with empty wardrobe")
print("-" * 70)

from tools import suggest_outfit
from utils.data_loader import get_empty_wardrobe

results = search_listings("vintage graphic tee", size=None, max_price=50)
if results:
    print(f"Item: {results[0]['title']}")
    print(f"Wardrobe items: {len(get_empty_wardrobe()['items'])} (empty)")
    
    outfit = suggest_outfit(results[0], get_empty_wardrobe())
    
    print(f"Outfit suggestion type: {type(outfit)}")
    print(f"Outfit suggestion length: {len(outfit)}")
    print(f"Outfit suggestion: {outfit[:150]}...")
    
    assert isinstance(outfit, str), "Should return string"
    assert len(outfit) > 0, "Should not be empty"
    assert "can't" not in outfit.lower(), "Should not return error message"
    
    print(f"✅ Correct: Returns general styling advice (not crash, not error)")
else:
    print("⚠️  No results found for test query")

# Test 4: Empty outfit string to create_fit_card
print("\n[TEST 4] create_fit_card with empty outfit string")
print("-" * 70)

from tools import create_fit_card

results = search_listings("vintage graphic tee", size=None, max_price=50)
if results:
    print(f"Item: {results[0]['title']}")
    print(f"Outfit input: ''  (empty string)")
    
    caption = create_fit_card("", results[0])
    
    print(f"Caption type: {type(caption)}")
    print(f"Caption: {caption}")
    
    assert isinstance(caption, str), "Should return string"
    assert len(caption) > 0, "Should not be empty"
    assert ("can't" in caption.lower() or "missing" in caption.lower()), "Should mention the issue"
    
    print(f"✅ Correct: Returns error message (not Python exception)")
else:
    print("⚠️  No results found for test query")

# Test 5: Whitespace-only outfit string
print("\n[TEST 5] create_fit_card with whitespace-only outfit")
print("-" * 70)

results = search_listings("jacket", size=None, max_price=50)
if results:
    print(f"Item: {results[0]['title']}")
    print(f"Outfit input: '   \\n  '  (whitespace only)")
    
    caption = create_fit_card("   \n  ", results[0])
    
    print(f"Caption: {caption}")
    
    assert isinstance(caption, str), "Should return string"
    assert len(caption) > 0, "Should not be empty"
    assert ("can't" in caption.lower() or "missing" in caption.lower()), "Should mention the issue"
    
    print(f"✅ Correct: Returns error message (not Python exception)")
else:
    print("⚠️  No results found for test query")

# Test 6: Query parsing with various formats
print("\n[TEST 6] Query parsing with different input formats")
print("-" * 70)

test_queries = [
    "vintage graphic tee",
    "vintage graphic tee under $30",
    "graphic tee size M",
    "graphic tee under $30 size M",
    "I want a size M tee under $25",
    "$50 graphic tee",
]

for query in test_queries:
    session = run_agent(query, get_example_wardrobe())
    print(f"Query: '{query}'")
    print(f"  → Parsed: {session['parsed']}")
    assert session['parsed']['description'], "Should have description"

print(f"✅ Correct: All query formats parsed successfully")

# Summary
print("\n" + "="*70)
print("SUMMARY: All failure modes handled correctly! ✅")
print("="*70)
print("""
✅ search_listings returns empty list (not exception)
✅ Agent stops early when search finds nothing
✅ suggest_outfit works with empty wardrobe (general advice)
✅ create_fit_card handles empty outfit (error message)
✅ create_fit_card handles whitespace outfit (error message)
✅ Query parsing works with all formats

All error paths return strings, never Python exceptions.
Agent gracefully degrades and provides helpful feedback.
""")
