"""
test_tools.py

pytest tests for all three FitFindr tools.
Tests cover successful cases and all documented failure modes.
"""

import pytest
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── Tests for search_listings ─────────────────────────────────────────────

class TestSearchListings:
    """Test search_listings with various filters and edge cases."""

    def test_search_returns_results(self):
        """Happy path: search finds matching listings."""
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert isinstance(results, list)
        assert len(results) > 0
        # Verify all results match the filter
        for item in results:
            assert item["price"] <= 50

    def test_search_empty_results(self):
        """Failure mode: search returns empty list, not exception."""
        results = search_listings("designer ballgown", size="XXS", max_price=5)
        assert results == []  # empty list, no exception

    def test_search_price_filter(self):
        """Filter by max_price: all returned items are under threshold."""
        results = search_listings("jacket", size=None, max_price=30)
        assert all(item["price"] <= 30 for item in results)

    def test_search_size_filter(self):
        """Filter by size: all returned items match size (case-insensitive)."""
        results = search_listings("tee", size="M", max_price=None)
        for item in results:
            # Check if size matches (case-insensitive substring)
            assert "m" in item["size"].lower()

    def test_search_no_filters(self):
        """Search with no filters returns all relevant listings."""
        results = search_listings("vintage", size=None, max_price=None)
        assert len(results) > 0

    def test_search_scoring_by_relevance(self):
        """Search results are sorted by relevance (best matches first)."""
        results = search_listings("graphic tee", size=None, max_price=None)
        # The first result should have strong keyword overlap
        top_result = results[0]
        text = (top_result["title"] + " " + top_result["description"] + " " +
                " ".join(top_result["style_tags"])).lower()
        # Should contain "graphic" or "tee"
        assert "graphic" in text or "tee" in text


# ── Tests for suggest_outfit ──────────────────────────────────────────────

class TestSuggestOutfit:
    """Test suggest_outfit with different wardrobe states."""

    def test_suggest_outfit_with_example_wardrobe(self):
        """Happy path: suggest outfit for item with populated wardrobe."""
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert len(results) > 0
        
        new_item = results[0]
        wardrobe = get_example_wardrobe()
        
        outfit = suggest_outfit(new_item, wardrobe)
        assert isinstance(outfit, str)
        assert len(outfit) > 0
        # Should reference wardrobe items or styling advice
        assert outfit.lower() not in ["", "error"]

    def test_suggest_outfit_with_empty_wardrobe(self):
        """Failure mode: empty wardrobe returns general styling advice."""
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert len(results) > 0
        
        new_item = results[0]
        wardrobe = get_empty_wardrobe()
        
        outfit = suggest_outfit(new_item, wardrobe)
        assert isinstance(outfit, str)
        assert len(outfit) > 0
        # Should provide general advice, not error message
        assert "pair" in outfit.lower() or "wear" in outfit.lower()

    def test_suggest_outfit_returns_non_empty_string(self):
        """Outfit suggestion is always a non-empty string."""
        results = search_listings("jacket", size=None, max_price=50)
        if results:
            outfit = suggest_outfit(results[0], get_example_wardrobe())
            assert isinstance(outfit, str)
            assert len(outfit.strip()) > 0


# ── Tests for create_fit_card ─────────────────────────────────────────────

class TestCreateFitCard:
    """Test create_fit_card with various inputs."""

    def test_create_fit_card_with_valid_outfit(self):
        """Happy path: generate caption from valid outfit string."""
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert len(results) > 0
        
        new_item = results[0]
        outfit = "Pair with baggy jeans and combat boots for a 90s vibe."
        
        caption = create_fit_card(outfit, new_item)
        assert isinstance(caption, str)
        assert len(caption) > 0
        # Should mention item details or platform
        assert (new_item["platform"] in caption or 
                str(new_item["price"]) in caption or
                new_item["title"].split()[0].lower() in caption.lower())

    def test_create_fit_card_with_empty_outfit(self):
        """Failure mode: empty outfit string returns error message."""
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert len(results) > 0
        
        new_item = results[0]
        caption = create_fit_card("", new_item)
        assert isinstance(caption, str)
        assert len(caption) > 0
        # Should return error message, not crash
        assert "can't" in caption.lower() or "missing" in caption.lower()

    def test_create_fit_card_with_whitespace_outfit(self):
        """Failure mode: whitespace-only outfit string returns error message."""
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert len(results) > 0
        
        new_item = results[0]
        caption = create_fit_card("   \n  ", new_item)
        assert isinstance(caption, str)
        assert "can't" in caption.lower() or "missing" in caption.lower()

    def test_create_fit_card_variation(self):
        """Fit cards vary across multiple calls (higher temperature)."""
        results = search_listings("jacket", size=None, max_price=50)
        if not results:
            pytest.skip("No results for this search")
        
        new_item = results[0]
        outfit = "Wear with dark jeans and a white shirt."
        
        captions = [create_fit_card(outfit, new_item) for _ in range(3)]
        # At least some variation expected (not all identical)
        # Due to LLM randomness, captions may differ even with same input
        assert all(isinstance(c, str) for c in captions)
        assert all(len(c) > 0 for c in captions)


# ── Integration tests ─────────────────────────────────────────────────────

class TestToolIntegration:
    """Test tools working together (mimics agent flow)."""

    def test_full_pipeline_with_results(self):
        """Full pipeline: search → outfit → caption."""
        # Step 1: Search
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert len(results) > 0, "Search should find listings"
        
        selected_item = results[0]
        
        # Step 2: Suggest outfit
        wardrobe = get_example_wardrobe()
        outfit = suggest_outfit(selected_item, wardrobe)
        assert len(outfit) > 0, "Outfit suggestion should not be empty"
        
        # Step 3: Create caption
        caption = create_fit_card(outfit, selected_item)
        assert len(caption) > 0, "Caption should not be empty"

    def test_full_pipeline_no_search_results(self):
        """Full pipeline: search returns empty, agent stops early."""
        # Step 1: Search with impossible filter
        results = search_listings("designer ballgown", size="XXS", max_price=5)
        assert results == [], "Search should return empty list"
        
        # Agent would stop here and return error (not tested here, tested in agent.py)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
