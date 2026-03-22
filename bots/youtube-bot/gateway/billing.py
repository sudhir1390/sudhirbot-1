import time

PRICE_INPUT_PER_M       = 0.80
PRICE_OUTPUT_PER_M      = 4.00
PRICE_CACHE_WRITE_PER_M = 1.00
PRICE_CACHE_READ_PER_M  = 0.08
USD_TO_INR              = 84.0

def format_bill(session: dict) -> str:
    u = session.get("usage", {})
    if not u or u.get("api_calls", 0) == 0:
        return "No API calls this session — no charges incurred."
    cost_usd = (
        (u.get("input_tokens", 0)       / 1_000_000) * PRICE_INPUT_PER_M
      + (u.get("output_tokens", 0)      / 1_000_000) * PRICE_OUTPUT_PER_M
      + (u.get("cache_write_tokens", 0) / 1_000_000) * PRICE_CACHE_WRITE_PER_M
      + (u.get("cache_read_tokens", 0)  / 1_000_000) * PRICE_CACHE_READ_PER_M
    )
    cost_inr    = cost_usd * USD_TO_INR
    dur         = int(time.time() - session.get("started_at", time.time()))
    total_input = (
        u.get("input_tokens", 0)
      + u.get("cache_write_tokens", 0)
      + u.get("cache_read_tokens", 0)
    )
    return (
        f"Duration: {dur//60}m {dur%60}s , "
        f"Token usage: Total Input: {total_input:,} , "
        f"Total Output: {u.get('output_tokens', 0):,} , "
        f"Cost: INR: \u20b9{cost_inr:.4f}"
    )