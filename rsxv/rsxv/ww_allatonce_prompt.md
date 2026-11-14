# ALL-AT-ONCE judge instructions (AGENTS.md §11.15; reimplementation of the Who&When baseline) — fixed before any data is read

You receive a task given to a multi-agent system, the correct final answer, and the system's full conversation log as
numbered steps (step index, agent name, content). The system failed: its final answer is wrong.

Read the whole log and identify which agent is most responsible for the failure and at which step that agent made the
mistake that led to the wrong answer.

Return exactly one JSON object, nothing else: {"id": ..., "agent": "<agent name as in the log>", "step": <integer step index>}
