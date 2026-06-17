#!/usr/bin/env python
"""Test the planning loop - no results path (doesn't need LLM)"""

from agent import run_agent
from utils.data_loader import get_example_wardrobe

print("=== Test: No results path ===")
session = run_agent(
    query="designer ballgown size XXS under $5",
    wardrobe=get_example_wardrobe(),
)

print(f"Parsed query: {session['parsed']}")
print(f"Search results found: {len(session['search_results'])}")
print(f"Selected item: {session['selected_item']}")
print(f"Outfit suggestion: {session['outfit_suggestion']}")
print(f"Fit card: {session['fit_card']}")
print(f"\nError message:\n{session['error']}")

# Verify the error path worked correctly
assert session['error'] is not None, "Should have error message"
assert session['selected_item'] is None, "Should not have selected item"
assert session['outfit_suggestion'] is None, "Should not have outfit suggestion"
assert session['fit_card'] is None, "Should not have fit card"
assert len(session['search_results']) == 0, "Should have no search results"

print("\n✅ No-results path test passed!")
