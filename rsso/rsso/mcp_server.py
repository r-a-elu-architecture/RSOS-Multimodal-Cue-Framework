"""RSOS planner over the Model Context Protocol (spec/LINX_MCP.md). Four tools and one prompt, stdio.

    pip install "mcp>=2"            # the official MCP Python SDK (not needed by the rest of RSSO)
    python -m rsso.mcp_server       # run from rsso/; then add it to any MCP client as a stdio server

Example client entry (Claude Desktop and others):
    {"mcpServers": {"rsos": {"command": "python3", "args": ["-m", "rsso.mcp_server"], "cwd": "<repo>/rsso"}}}
"""
from __future__ import annotations

from typing import Any

from . import linx_mcp as L

TOOLS = {
    "propose_plan": "Build an RSOS practice plan from the assistant's proposal (states, cues, frames, contexts) after the "
                    "session self-check, in one call. Codes, programs and schedule are computed by the planner. Returns a compact "
                    "proposal (detail 'full' for the complete programs) for the person or their practitioner to approve, "
                    "or no plan with the session's messages and what is allowed now.",
    "session_check": "Run the RSOS session self-check (intensity, sleep, medication, substances, practical concerns, earlier "
                     "experience, a practitioner's screening result) and return the session state, its messages and what is "
                     "allowed now.",
    "check_frame": "Score a frame sentence: scope (broad or narrow), process or trait, wording flags and a suggested rewrite.",
    "tacton": "Return the pulse pattern (on and off times in ms) of an RSOS vibration code such as '..-'.",
}
PROMPT = ("linx_intake", "How an assistant fills an RSOS intake: self-check first, propose states and cues, the planner "
                         "computes the rest, the person approves.")


def build():
    from mcp.server.mcpserver import MCPServer
    app = MCPServer(name="rsos-planner", version="1",
                    instructions="RSOS research and development framework; not a medical device. Propose only: the "
                                 "planner computes, the session check gates, the person approves.")

    @app.tool(name="propose_plan", description=TOOLS["propose_plan"])
    def propose_plan(intake: dict[str, Any], check: dict[str, Any], detail: str = "summary") -> dict[str, Any]:
        return L.propose_plan(intake, check, detail)

    @app.tool(name="session_check", description=TOOLS["session_check"])
    def session_check(answers: dict[str, Any]) -> dict[str, Any]:
        return L.session_check(answers)

    @app.tool(name="check_frame", description=TOOLS["check_frame"])
    def check_frame(text: str, mode: str = "associated", believability: float | None = None) -> dict[str, Any]:
        return L.check_frame(text, mode, believability)

    @app.tool(name="tacton", description=TOOLS["tacton"])
    def tacton(code: str) -> dict[str, Any]:
        return L.tacton(code)

    @app.prompt(name=PROMPT[0], description=PROMPT[1])
    def linx_intake() -> str:
        return L.INTAKE_PROMPT

    return app


if __name__ == "__main__":
    build().run("stdio")
