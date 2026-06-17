#!/usr/bin/env python
"""
Test that the Gradio interface can be built and tested
"""

import sys

print("Building FitFindr Gradio interface...")

from app import build_interface, handle_query
from utils.data_loader import get_example_wardrobe

# Build the interface (doesn't launch it, just builds it)
demo = build_interface()
print(f"✅ Gradio interface built successfully")
print(f"   Interface type: {type(demo)}")

# Test the handle_query function with various inputs
print("\nTesting handle_query function...")

# Test 1: Normal query
result = handle_query("vintage graphic tee under $30", "Example wardrobe")
print(f"\nTest 1: Normal query")
print(f"  Result tuple length: {len(result)}")
print(f"  Panel 1 (listing): {len(result[0])} chars")
print(f"  Panel 2 (outfit): {len(result[1])} chars")
print(f"  Panel 3 (caption): {len(result[2])} chars")

assert len(result) == 3, "Should return 3-tuple"
assert len(result[0]) > 0, "Listing panel should have content"
assert len(result[1]) > 0, "Outfit panel should have content"
assert len(result[2]) > 0, "Caption panel should have content"

# Test 2: Empty query
result = handle_query("", "Example wardrobe")
print(f"\nTest 2: Empty query")
print(f"  Panel 1 (error): {result[0]}")
assert "Please enter" in result[0] or "empty" in result[0].lower(), "Should return error for empty query"

# Test 3: No results
result = handle_query("designer ballgown size XXS under $5", "Example wardrobe")
print(f"\nTest 3: No results query")
print(f"  Panel 1 (error): {result[0][:100]}...")
assert "No listings found" in result[0], "Should return error for no results"
assert result[1] == "", "Outfit panel should be empty"
assert result[2] == "", "Caption panel should be empty"

# Test 4: Empty wardrobe option
result = handle_query("graphic tee under $50", "Empty wardrobe (new user)")
print(f"\nTest 4: Empty wardrobe")
print(f"  Panel 1 (listing): {len(result[0])} chars")
print(f"  Panel 2 (outfit): {len(result[1])} chars")
print(f"  Panel 3 (caption): {len(result[2])} chars")

assert len(result[0]) > 0, "Should have listing"
assert len(result[1]) > 0, "Should have outfit (general advice)"
assert len(result[2]) > 0, "Should have caption"

print("\n" + "="*70)
print("✅ All interface tests passed!")
print("="*70)
print("""
The Gradio interface is ready:
- Builds without errors ✅
- handle_query returns 3 panels ✅
- Empty query shows error ✅
- No results shows error ✅
- Empty wardrobe shows general advice ✅

To launch the interface:
    python app.py

Then visit http://localhost:7860 in your browser.
""")
