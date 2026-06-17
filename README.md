# FitFindr — Thrifted Fashion Agent

An AI-powered agent that helps you find secondhand fashion pieces and get outfit suggestions based on your existing wardrobe.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key (get one free at console.groq.com)
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Run the Gradio interface
python app.py

# 4. Open http://localhost:7860 in your browser
```

## Overview

FitFindr is a **multi-step AI agent** that demonstrates how to build complex workflows combining search, LLM reasoning, and creative generation. The agent:

1. **Searches** a dataset of 40 mock secondhand listings by keyword, size, and price
2. **Suggests outfits** by combining the new item with your wardrobe using an LLM
3. **Creates fit cards** — Instagram-style captions for your thrifted finds

### The Planning Loop

```
User Query
    ↓
Parse: extract description, size, max_price using regex
    ↓
Call search_listings() → get matching items
    ↓
IF empty results:
  → Return error message (agent stops early)
ELSE:
  → Call suggest_outfit() with top result + wardrobe
  → Call create_fit_card() with outfit suggestion
  → Return all three outputs
    ↓
User sees: listing + styling advice + caption
```

**Key insight:** The agent branches on search results. If nothing matches, it stops and tells the user what to try instead, rather than crashing or producing meaningless output.

## Tool Inventory

### Tool 1: search_listings(description, size, max_price) → list[dict]

Finds secondhand items matching keywords, optional size, and optional price ceiling.

**Example:**
```python
results = search_listings("vintage graphic tee", size="M", max_price=30)
# Returns: [
#   {"title": "Graphic Tee — 2003 Tour Bootleg...", "price": 24, ...},
#   {"title": "Faded Band Tee", "price": 28, ...},
#   ...
# ]
```

**How it works:**
- Loads listings, filters by price & size
- Scores each by keyword overlap (title, description, style_tags, colors)
- Returns sorted by relevance; empty list if no matches

---

### Tool 2: suggest_outfit(new_item, wardrobe) → str

Suggests 1-2 complete styled outfits combining the new item with existing wardrobe pieces.

**Example:**
```python
results = search_listings("graphic tee", None, 50)
outfit = suggest_outfit(results[0], wardrobe=get_example_wardrobe())
# Returns: "Pair this black vintage band tee with your baggy jeans — 
# the boxy fit is perfect for 90s grunge. Add your combat boots 
# or chunky sneakers to complete the look."
```

**How it works:**
- Calls Groq LLM with different prompts for empty vs. populated wardrobes
- For empty wardrobe: provides general styling advice
- For populated wardrobe: references specific pieces by name
- Temperature: 0.7 for balanced creativity

---

### Tool 3: create_fit_card(outfit, new_item) → str

Generates an Instagram/TikTok-style caption for the thrifted find.

**Example:**
```python
caption = create_fit_card(outfit, new_item)
# Returns: "thrifted this faded band tee off depop for $24 and the 
# vibe is immaculate 🖤 pairs perfectly with my baggy jeans and 
# chunky sneakers. full grunge fit 🎸"
```

**How it works:**
- Guards against empty outfit input (returns error message, never crashes)
- Calls LLM with high temperature (0.85) for variation
- Each call produces different output (authentic social media feel)

## Error Handling

### Failure Mode 1: No Search Results

**When:** User searches for something that doesn't exist (e.g., "designer ballgown size XXS under $5")

**Agent does:** Returns error message immediately, doesn't call suggest_outfit or create_fit_card

**User sees:** 
```
"No listings found matching 'designer ballgown' in size XXS under $5. 
Try searching for items in a different size, raising your budget, or 
using broader keywords (e.g., 'dress' instead of 'ballgown')."
```

**Why this matters:** Agent stops early and provides actionable feedback instead of crashing or producing hallucinations.

### Failure Mode 2: Empty Wardrobe

**When:** User has no existing wardrobe items to style with

**Agent does:** Calls suggest_outfit() which detects empty wardrobe and prompts LLM for general advice

**User sees:**
```
"This graphic tee has a grunge vibe. Pair it with baggy jeans and combat 
boots for an edgy 90s look. You could also layer it under a denim or 
leather jacket."
```

**Why this matters:** Agent gracefully degrades. Always provides useful output, never crashes with exceptions.

### Failure Mode 3: Missing Outfit Input

**When:** create_fit_card() receives empty outfit string

**Agent does:** Returns descriptive error message (never raises exception)

**User sees:**
```
"Can't generate a fit card — the outfit suggestion is missing. Please try the search again."
```

**Why this matters:** All error paths are strings, never Python exceptions. Errors flow cleanly through the UI.

## Query Parsing

The agent uses **regex** (not LLM) to extract parameters:

```python
# User query: "vintage graphic tee under $30, size M"
# Regex extracts:
#   - description: "vintage graphic tee"
#   - max_price: 30.0  (matches "under $30")
#   - size: "M"         (matches "size M")

# Supported patterns:
#   "under $30", "$50", "up to $40"  →  max_price
#   "size M", "sz S/M", "size W28"   →  size
#   Rest of text                     →  description
```

**Why regex instead of LLM?** It's deterministic, fast (no API call), cheaper, and sufficient for common patterns.

## State Management

All state lives in a single `session` dict:

```python
session = {
    "query": "vintage graphic tee under $30",
    "parsed": {
        "description": "vintage graphic tee",
        "size": None,
        "max_price": 30.0,
    },
    "search_results": [...],           # From search_listings()
    "selected_item": {...},            # Top result
    "wardrobe": {...},                 # Input from user
    "outfit_suggestion": "Pair with...", # From suggest_outfit()
    "fit_card": "thrifted this...",    # From create_fit_card()
    "error": None,                     # Set if interaction ends early
}
```

**Why one dict?** It's the single source of truth. Each tool reads and writes only what it needs. No re-fetching or re-processing. Makes debugging straightforward.

## Testing

### Run all tests

```bash
pytest tests/test_tools.py -v
```

### Test without LLM (search & error path only)

```bash
python test_search.py                # Test search_listings
python test_agent_noqa.py            # Test no-results error path
```

### Manual testing in Python

```python
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# Test 1: Search
results = search_listings("vintage graphic tee", size=None, max_price=50)
print(f"Found {len(results)} results")

# Test 2: Outfit (empty wardrobe)
outfit = suggest_outfit(results[0], get_empty_wardrobe())
print(f"Outfit: {outfit}")

# Test 3: Caption
caption = create_fit_card(outfit, results[0])
print(f"Caption: {caption}")

# Test 4: No results path
no_results = search_listings("designer ballgown", size="XXS", max_price=5)
print(f"No results: {len(no_results) == 0}")  # Should be True
```

## Project Structure

```
ai201-project2-fitfindr-starter/
├── tools.py                 # Three tools: search, outfit, caption
├── agent.py                 # Planning loop + query parsing
├── app.py                   # Gradio web interface
├── planning.md              # Complete specification (read this!)
├── tests/
│   └── test_tools.py       # Comprehensive pytest tests
├── utils/
│   └── data_loader.py      # Helper functions for data
├── data/
│   ├── listings.json       # 40 mock secondhand listings
│   └── wardrobe_schema.json  # Wardrobe schema + example
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Example Interactions

### Happy Path: Vintage Tee Search

```
User: "I'm looking for a vintage graphic tee under $30. 
I mostly wear baggy jeans and chunky sneakers."

[Parse] → description="vintage graphic tee", max_price=30.0

[Search] → Found 3 listings:
  1. "Graphic Tee — 2003 Tour Bootleg..." $24
  2. "Y2K Baby Tee — Butterfly Print" $18
  3. "Faded Band Tee" $28

[Selected] → Top result: Graphic Tee for $24

[Outfit] → "Pair this black vintage band tee with your baggy jeans 
for that relaxed 90s grunge vibe. Add your chunky white sneakers 
or black combat boots. This is total early 2000s nostalgia."

[Caption] → "thrifted this faded band tee off depop for $24 and 
honestly it was made for my wide-legs 🖤 full look in my stories"

User sees: Listing + Outfit idea + Fit card ✅
```

### Error Path: Impossible Query

```
User: "designer ballgown size XXS under $5"

[Parse] → description="designer ballgown", size="XXS", max_price=5.0

[Search] → Found 0 listings

[Error] → "No listings found matching 'designer ballgown' in size XXS 
under $5. Try searching for items in a different size, raising your 
budget, or using broader keywords (e.g., 'dress' instead of 'ballgown')."

User sees: Error message, outfit and caption panels are empty
Agent stops here — doesn't crash ✅
```

## AI Tool Usage

### Tool 1 (search_listings): Implemented directly, no AI

Used keyword scoring algorithm (deterministic, fast, no LLM call).

### Tool 2 (suggest_outfit): Groq LLM

Prompt depends on wardrobe state:
- **Empty wardrobe:** "What types of pieces pair well with [item]?"
- **Populated wardrobe:** "Given [wardrobe list], suggest outfits with [new item]"

Temperature: 0.7

### Tool 3 (create_fit_card): Groq LLM

Prompt: "Write a casual 2-4 sentence Instagram caption mentioning [price, platform, vibe]"

Temperature: 0.85 (higher for more variation)

## Extending FitFindr

**Future enhancements:**
- Rerank search results using LLM for semantic relevance
- Support multi-item outfit suggestions from the catalog
- Remember user style preferences across sessions
- Accept item photos and auto-tag colors/style/condition
- Integrate with real platforms (Depop, Poshmark APIs)
- Add image generation for outfit mockups

## Architecture Highlights

✅ **Modular tools:** Each tool is independent and testable  
✅ **Single session dict:** One source of truth for all state  
✅ **Early error handling:** Agent stops and communicates clearly when something fails  
✅ **Regex-based parsing:** Fast, deterministic, no LLM overhead  
✅ **Graceful degradation:** Empty wardrobe → general advice (not crash)  
✅ **Comprehensive tests:** All failure modes covered  
✅ **Clean web UI:** Gradio interface with example queries  

## Troubleshooting

**"Invalid API Key"** → Check `.env` file has valid key from console.groq.com

**No search results** → This is expected for very specific queries. Try broader keywords.

**Slow LLM responses** → Normal (1-3 seconds per request). Groq is fast but not instant.

**Tests fail** → Run `pytest tests/test_tools.py -v` to see details

## Summary

FitFindr demonstrates a complete multi-tool agent with:
- **Query parsing** (regex, no LLM overhead)
- **Modular tools** (search, styling, generation)
- **State management** (single session dict)
- **Careful error handling** (early returns, graceful degradation)
- **Comprehensive testing** (unit tests + failure modes)
- **Clean web interface** (Gradio with examples)

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**

**Step 1 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Step 2 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Step 3 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Final output to user:**

---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | | |
| `suggest_outfit` | | |
| `create_fit_card` | | |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**

**One divergence from your spec, and why:**

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
