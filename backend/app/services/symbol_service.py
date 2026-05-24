from typing import List, Optional

from app.config.settings import DEFAULT_SYMBOLS

def get_supported_symbols(query: Optional[str] = None) -> List[dict]:
    """Return list of supported symbols, optionally filtered by search query."""
    # Build dictionary structure since config only has string arrays
    symbols_data = [
        {"symbol": s, "description": s, "type": "stock"} 
        for s in DEFAULT_SYMBOLS
    ]
    
    if query:
        q_lower = query.lower()
        symbols_data = [
            s for s in symbols_data
            if q_lower in s["symbol"].lower() or q_lower in s["description"].lower()
        ]
    return symbols_data
