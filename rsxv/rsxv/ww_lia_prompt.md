# LIA-UPSTREAM judge instructions (AGENTS.md §11.15) — fixed before any data is read

You receive a task given to a multi-agent system, the correct final answer, and the system's full conversation log as
numbered steps (step index, agent name, content). The system failed: its final answer is wrong.

Find the decisive error by tracing the failure's lineage backwards, as the RSX-V Observer and LIA do:
1. Start from the final wrong answer. Ask which earlier step's output it relies on.
2. Walk upstream along that chain of reliance. At each step decide: is this step's own content correct given its inputs
   (healthy), or does it introduce a new mistake (a fault), or does it only carry forward a mistake made earlier?
3. The decisive error is the EARLIEST step that introduces a mistake which is carried forward, step by step, into the
   final wrong answer (first-failure parent rule). A mistake that is later corrected, or that the final answer does not
   rely on, is not decisive. A step that only repeats or relays an earlier mistake is not decisive; follow it upstream.
4. The responsible agent is the agent who wrote that step.

Return exactly one JSON object, nothing else: {"id": ..., "agent": "<agent name as in the log>", "step": <integer step index>}
