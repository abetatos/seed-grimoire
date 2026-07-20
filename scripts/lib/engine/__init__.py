"""World-state engine: structured JSON state mutated only by scripts, replayed
and queried in pure stdlib. The LLM never edits the store; it reads *computed*
Markdown views (see render.py) and proposes mutations that skills apply via CLI.

Why this exists: the spatial-temporal contract of the story (where everyone is
at every moment, who can speak, who can overhear) was previously free Markdown
validated after the fact. Here it is derived: impossible states (teleports,
backward clocks, impossible witnesses) are unrepresentable, not bugs to catch.
"""
