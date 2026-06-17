"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    all_listings = load_listings()
    
    # Filter by price and size
    filtered = []
    for listing in all_listings:
        # Price filter
        if max_price is not None and listing["price"] > max_price:
            continue
        
        # Size filter (case-insensitive substring match)
        if size is not None:
            listing_size = listing["size"].lower()
            size_lower = size.lower()
            if size_lower not in listing_size:
                continue
        
        filtered.append(listing)
    
    # Score listings by keyword overlap
    description_keywords = set(description.lower().split())
    
    scored = []
    for listing in filtered:
        # Combine all text fields for matching
        searchable_text = (
            listing["title"].lower() + " " +
            listing["description"].lower() + " " +
            " ".join(listing["style_tags"]).lower() + " " +
            " ".join(listing["colors"]).lower() + " " +
            (listing["brand"].lower() if listing["brand"] else "")
        )
        
        searchable_keywords = set(searchable_text.split())
        
        # Calculate overlap score
        overlap = len(description_keywords & searchable_keywords)
        
        if overlap > 0:
            scored.append((overlap, listing))
    
    # Sort by score (highest first)
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Return just the listings (without scores)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()
    
    # Check if wardrobe is empty
    wardrobe_items = wardrobe.get("items", [])
    
    if not wardrobe_items:
        # Empty wardrobe: ask for general styling advice
        prompt = f"""You are a fashion stylist. A user is considering buying this thrifted item:

Item: {new_item['title']}
Description: {new_item['description']}
Category: {new_item['category']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}

They have an empty wardrobe and are just starting to build their closet.
Suggest 1-2 outfit ideas for this item, describing what types of pieces would pair well (don't reference specific wardrobe items).
Focus on the vibe and styling (e.g., "pair with baggy jeans and combat boots for a grunge look").
Keep your response to 2-3 sentences."""

    else:
        # Non-empty wardrobe: suggest specific outfit combinations
        wardrobe_text = "\n".join(
            f"- {item['name']} (category: {item['category']}, colors: {', '.join(item['colors'])})"
            for item in wardrobe_items
        )
        
        prompt = f"""You are a fashion stylist. A user is considering buying this thrifted item:

Item: {new_item['title']}
Description: {new_item['description']}
Category: {new_item['category']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}

Their existing wardrobe contains:
{wardrobe_text}

Suggest 1-2 complete outfit combinations using the new item and specific pieces from their wardrobe (by name).
Explain how the pieces work together and what vibe they create.
Keep your response to 3-4 sentences."""

    # Call the LLM
    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300,
    )
    
    response = message.choices[0].message.content.strip()
    
    # Ensure non-empty response
    if not response:
        response = "I can't suggest a specific outfit right now. Try adding some items to your wardrobe first!"
    
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against empty outfit
    if not outfit or not outfit.strip():
        return "Can't generate a fit card — the outfit suggestion is missing. Please try the search again."
    
    client = _get_groq_client()
    
    prompt = f"""You are a fashion influencer writing an Instagram or TikTok caption for an OOTD (outfit of the day) post.

The thrifted item you just scored:
- Name: {new_item['title']}
- Price: ${new_item['price']}
- Platform: {new_item['platform']}
- Condition: {new_item['condition']}

How you styled it:
{outfit}

Write a casual, authentic 2-4 sentence caption that:
1. Mentions where you thrifted it (platform) and the price naturally (once each)
2. References the outfit vibe and specific styling choices
3. Feels like a real person sharing their thrift find, not a product description
4. Can include casual language, emojis, or personality

Just write the caption, nothing else."""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.85,  # Higher temperature for variation
        max_tokens=200,
    )
    
    response = message.choices[0].message.content.strip()
    
    return response if response else "This thrifted piece is a vibe! 🖤"
