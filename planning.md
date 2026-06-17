# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock secondhand listings dataset by keyword description, optional size filter, and optional max price. Returns a ranked list of the best matching items sorted by relevance to the description.

**Input parameters:**
- `description` (str): Keywords describing what the user is looking for (e.g., "vintage graphic tee", "black boots", "oversized flannel").
- `size` (str | None): Size string to filter by (e.g., "M", "S/M", "W28", "XL"), or None to skip size filtering. Matching is case-insensitive and substring-based.
- `max_price` (float | None): Maximum price threshold (inclusive), or None to skip price filtering.

**What it returns:**
A list of listing dicts sorted by relevance (highest first). Each dict contains: id, title, description, category, style_tags (list), size, condition, price (float), colors (list), brand (str or None), platform (str). Returns an empty list if nothing matches — does NOT raise an exception.

**What happens if it fails or returns nothing:**
If search_listings returns an empty list, the agent sets session["error"] to a message telling the user what failed and what to try: "No listings found matching 'designer ballgown' in size XXS under $5. Try searching for items in a different size, raising your budget, or using broader keywords (e.g., 'dress' instead of 'ballgown')." The agent then returns the session early without calling suggest_outfit or create_fit_card.

---

### Tool 2: suggest_outfit

**What it does:**
Given a thrifted item the user is considering and their existing wardrobe, suggests 1–2 complete styled outfits that incorporate the new item. Uses the LLM to synthesize styling advice based on colors, style tags, and wardrobe composition.

**Input parameters:**
- `new_item` (dict): A listing dict representing the secondhand item being considered. Contains: id, title, description, category, style_tags (list), size, condition, price, colors (list), brand, platform.
- `wardrobe` (dict): The user's wardrobe dict with an 'items' key containing a list of wardrobe item dicts. Each item has: id, name, category, colors, style_tags, notes (optional). May be empty — must be handled gracefully.

**What it returns:**
A non-empty string containing outfit suggestions. The response should reference specific pieces from the wardrobe (by name) and explain how to combine them with the new item. If the wardrobe is empty, the LLM provides general styling advice (e.g., "This graphic tee has a grunge vibe. Pair it with baggy jeans, combat boots, and a black jacket for an edgy 90s look. Tuck the front corner slightly for shape.").

**What happens if it fails or returns nothing:**
If the wardrobe is empty, the agent calls suggest_outfit() which provides general styling ideas rather than empty or error output. The LLM is instructed to give actionable advice even without a wardrobe list. If the LLM returns an empty response (extremely unlikely but guarded against), the agent returns a fallback message: "I can't suggest a specific outfit right now. Try adding some items to your wardrobe first!"

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, shareable outfit caption (2–4 sentences) in the style of an Instagram or TikTok post. Incorporates the item name, price, platform, and the outfit styling suggestion into an authentic, casual voice.

**Input parameters:**
- `outfit` (str): The outfit suggestion string from suggest_outfit(). Contains styling advice and specific pieces.
- `new_item` (dict): The listing dict for the thrifted item. Contains: id, title, description, category, style_tags, size, condition, price, colors, brand, platform.

**What it returns:**
A 2–4 sentence string usable as an Instagram/TikTok caption. The caption should feel authentic and casual (like a real OOTD post), mention the item name, price, and platform exactly once each, capture the outfit vibe with specific styling language, and produce different outputs on different calls (using higher LLM temperature for variation).

Example: "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤 full look in my stories"

**What happens if it fails or returns nothing:**
If the outfit string is empty or whitespace-only, create_fit_card returns a descriptive error message string: "Can't generate a fit card — the outfit suggestion is missing. Please try the search again." This prevents the agent from crashing and provides actionable feedback to the user.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

The agent follows a sequential, conditional planning loop:

1. **Parse the query:** Extract description, size, and max_price from the user's natural language query using regex and string parsing.
2. **Call search_listings()** with the parsed parameters. Store results in session["search_results"].
3. **Check if results are empty:** If session["search_results"] is an empty list, set session["error"] to an actionable error message (see Tool 1 failure mode) and return the session immediately. The agent does NOT proceed to suggest_outfit with empty input.
4. **If results found:** Select the top result (index 0) and store it in session["selected_item"].
5. **Call suggest_outfit()** with session["selected_item"] and session["wardrobe"]. Store the response in session["outfit_suggestion"].
6. **Call create_fit_card()** with session["outfit_suggestion"] and session["selected_item"]. Store the response in session["fit_card"].
7. **Return the session** with all fields populated. If session["error"] is None, the interaction succeeded.

The key decision branch: if search_listings returns empty results, the loop terminates early. Otherwise, it always proceeds through all three tools in sequence.

---

## State Management

**How does information from one tool get passed to the next?**

All state is stored in a single session dict initialized in run_agent(). The session dict is structured as:

```python
session = {
    "query": str,                 # original user query
    "parsed": {                   # extracted from query parsing
        "description": str,
        "size": str | None,
        "max_price": float | None,
    },
    "search_results": list[dict], # list of matching listings
    "selected_item": dict | None, # top result from search_results
    "wardrobe": dict,             # user's wardrobe (input parameter)
    "outfit_suggestion": str | None, # output from suggest_outfit
    "fit_card": str | None,       # output from create_fit_card
    "error": str | None,          # set if interaction ends early
}
```

**Data flow between tools:**
- After search_listings(), session["search_results"] becomes input for the item selection step.
- session["selected_item"] (the top search result) is passed to suggest_outfit().
- session["outfit_suggestion"] (output from suggest_outfit) is passed to create_fit_card() along with session["selected_item"].
- Each tool reads and writes only the specific fields it needs; no re-parsing or re-fetching occurs between calls.

This ensures one source of truth for all state and guarantees each tool receives exactly what the previous tool produced.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query (empty list returned) | Set session["error"] to: "No listings found matching '[description]' in size [size] under $[max_price]. Try searching for items in a different size, raising your budget, or using broader keywords (e.g., 'dress' instead of 'ballgown')." Return session early without calling suggest_outfit or create_fit_card. |
| suggest_outfit | Wardrobe is empty (session["wardrobe"]["items"] is []) | Call the LLM with a prompt asking for general styling advice instead of outfit combinations. Return styling suggestions (e.g., "Pair with baggy jeans and combat boots for a grunge look") rather than raising an exception or returning empty string. |
| create_fit_card | Outfit input is empty or whitespace-only | Return a descriptive error message string: "Can't generate a fit card — the outfit suggestion is missing. Please try the search again." Do not raise an exception. |

---

## Architecture

```mermaid
flowchart TD
    A["👤 User Query<br/>(e.g., 'vintage graphic tee<br/>under $30, size M')"] -->|input| B["🔄 Planning Loop"]
    
    B -->|Step 1: Parse| C["Parse Query<br/>Extract: description,<br/>size, max_price"]
    C -->|Store in session| D["Session State"]
    
    D -->|Step 2: Call| E["🔍 search_listings<br/>(description, size, max_price)"]
    E -->|Returns results[]| F{"Results<br/>Empty?"}
    
    F -->|Yes| G["⚠️ ERROR PATH<br/>Set session['error']<br/>= helpful message"]
    G -->|Return session| H["Return to User"]
    H -->|Display| I["❌ Error message<br/>(empty outfit & fit card panels)"]
    
    F -->|No| J["✅ SUCCESS PATH<br/>session['selected_item']<br/>= results0"]
    J -->|Step 3: Call| K["👗 suggest_outfit<br/>(selected_item, wardrobe)"]
    K -->|Returns outfit_string| L["Store in session<br/>['outfit_suggestion']"]
    
    L -->|Step 4: Call| M["✨ create_fit_card<br/>(outfit_string, selected_item)"]
    M -->|Returns caption_string| N["Store in session<br/>['fit_card']"]
    
    N -->|Step 5: Return| H
    H -->|Display| O["📦 Listing<br/>👗 Outfit idea<br/>✨ Fit card"]
    
    D -->|"Contains: query,<br/>parsed params,<br/>search results,<br/>selected item,<br/>wardrobe,<br/>outfit suggestion,<br/>fit card,<br/>error message"| P["Session Dict<br/>(Single Source of Truth)"]
```

**Key points:**
- The planning loop reads and writes exclusively to the session dict (one source of truth).
- After search_listings(), the loop checks if results are empty. If yes, it terminates early with an error message.
- If results exist, the loop proceeds sequentially through suggest_outfit and create_fit_card.
- Each tool receives exactly what the previous tool produced (no re-processing or re-fetching).
- The error path short-circuits before calling suggest_outfit or create_fit_card with empty input.

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

For each tool, I will:

1. **search_listings():** Provide Claude with the Tool 1 spec block (what it does, input parameters, return value, failure mode) from planning.md and ask it to implement the function. I'll provide the requirements:
   - Use load_listings() from utils/data_loader.py for data loading (don't re-implement)
   - Filter by size (case-insensitive substring match) and max_price if provided
   - Score listings by keyword overlap with description
   - Return listings sorted by score (highest first), empty list if no matches
   Before running, I'll verify the code filters on all three parameters and handles the empty-results case. Then I'll test with 3 queries: one that matches multiple items, one that matches nothing, and one that tests price/size filtering.

2. **suggest_outfit():** Provide Claude with Tool 2 spec and the tool stub, ask it to:
   - Check if wardrobe['items'] is empty
   - If empty: prompt the LLM to provide general styling advice
   - If not empty: format wardrobe items and ask the LLM to suggest outfit combinations
   - Call Groq's llama-3.3-70b-versatile with GROQ_API_KEY
   - Return the LLM response as a string
   Before running, I'll verify it handles both empty and non-empty wardrobe cases. I'll test with get_empty_wardrobe() and get_example_wardrobe().

3. **create_fit_card():** Provide Claude with Tool 3 spec and ask it to:
   - Guard against empty or whitespace-only outfit string
   - Build a prompt asking the LLM for a 2–4 sentence Instagram-style caption
   - Use temperature setting to ensure variation across calls
   - Return the LLM response
   Before running, I'll verify the caption feels authentic (not a product description). I'll run it 3 times on the same input and confirm outputs differ.

**Milestone 4 — Planning loop and state management:**

I will provide Claude with:
- The agent diagram (from Architecture section above)
- The Planning Loop and State Management sections from planning.md
Ask it to implement run_agent() following the numbered steps and conditional logic I described.
Before running, I'll verify:
- The code branches on search_listings() result
- It stores values in session dict
- It doesn't call all three tools unconditionally
- It returns session early when search_listings returns empty list

I will also ask Claude to help implement handle_query() in app.py by providing:
- The TODO steps in the function
- The handle_query function signature
Before running, I'll verify it calls run_agent() correctly and maps session fields to output strings.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1: Parse the query**
The planning loop extracts the key parameters:
- description: "vintage graphic tee"
- size: None (not specified)
- max_price: 30.0

**Step 2: Call search_listings()**
Call: `search_listings(description="vintage graphic tee", size=None, max_price=30.0)`
Result: Returns a list of 3 matching listings, sorted by relevance. Top result:
```
{
  "id": "lst_006",
  "title": "Graphic Tee — 2003 Tour Bootleg Style",
  "description": "Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.",
  "category": "tops",
  "style_tags": ["graphic tee", "vintage", "grunge", "streetwear", "band tee"],
  "size": "L",
  "condition": "good",
  "price": 24.00,
  "colors": ["black"],
  "brand": null,
  "platform": "depop"
}
```
Session["search_results"] = [this item, ...], session["selected_item"] = this item

**Step 3: Call suggest_outfit()**
Call: `suggest_outfit(new_item=selected_item, wardrobe=get_example_wardrobe())`
The LLM receives the graphic tee details and the user's 10 wardrobe items (baggy jeans, chunky sneakers, etc.)
Result: 
```
"Pair this black vintage band tee with your dark wash baggy jeans — the boxy fit is perfect for that relaxed 90s grunge vibe. 
Throw on your black combat boots or chunky white sneakers to complete the look. Tuck the front corner slightly for a bit of shape, 
and add your black crossbody bag. This is total early 2000s nostalgia."
```
Session["outfit_suggestion"] = this response

**Step 4: Call create_fit_card()**
Call: `create_fit_card(outfit=session["outfit_suggestion"], new_item=selected_item)`
The LLM receives the outfit suggestion and item details, asked to generate a casual Instagram-style caption.
Result:
```
"thrifted this faded band tee off depop for $24 and the vibe is immaculate 🖤 pairs perfectly with my baggy jeans 
and chunky sneakers, feel like i just stepped out of 2003. full grunge fit 🎸"
```
Session["fit_card"] = this response

**Final output to user:**

The Gradio interface displays:
- **Panel 1 (Listing):** "Graphic Tee — 2003 Tour Bootleg Style | $24 | Depop | Condition: good | Size: L | Style: vintage, grunge, band tee | Colors: black" (formatted nicely)
- **Panel 2 (Outfit idea):** "Pair this black vintage band tee with your dark wash baggy jeans..." (full outfit suggestion)
- **Panel 3 (Fit card):** "thrifted this faded band tee off depop for $24..." (Instagram caption)

The user reads the suggestion, sees the exact match between what the outfit panel recommended and how it appears in the fit card, and can now make an informed purchase decision with styling ideas already in mind.
