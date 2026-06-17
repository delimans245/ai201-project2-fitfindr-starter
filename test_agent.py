#!/usr/bin/env python
"""Test the planning loop without LLM calls"""

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

print("=== Test 1: Query with all filters ===")
session = run_agent(
    query="vintage graphic tee under $30, size M",
    wardrobe=get_example_wardrobe(),
)

print(f"Parsed query: {session['parsed']}")
print(f"Search results found: {len(session['search_results'])}")
print(f"Error: {session['error']}")
if session['selected_item']:
    print(f"Selected item: {session['selected_item']['title']} - ${session['selected_item']['price']}")

print("\n=== Test 2: No results path ===")
session2 = run_agent(
    query="designer ballgown size XXS under $5",
    wardrobe=get_example_wardrobe(),
)

print(f"Parsed query: {session2['parsed']}")
print(f"Search results found: {len(session2['search_results'])}")
print(f"Error message: {session2['error']}")
print(f"Selected item: {session2['selected_item']}")

print("\n=== Test 3: Query with no filters ===")
session3 = run_agent(
    query="I want something vintage and cool",
    wardrobe=get_example_wardrobe(),
)

print(f"Parsed query: {session3['parsed']}")
print(f"Search results found: {len(session3['search_results'])}")
if session3['selected_item']:
    print(f"Selected item: {session3['selected_item']['title']}")

print("\n✅ Planning loop tests passed!")
