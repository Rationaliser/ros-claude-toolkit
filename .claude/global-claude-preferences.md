# ~/.claude/CLAUDE.md — Global Preferences
# Applies to ALL Claude Code sessions across all projects.

## Who I Am
- Vedant — M.Eng. Robotics, Deggendorf Institute of Technology, Germany
- Building ros-claude-toolkit (ROS 2 + MCP + safety layer, professor-sponsored)
- Also building Valentiz (B2B agentic outreach, Claude + n8n + Airtable)
- Two peer-reviewed publications: Springer (RL autoscaling), IEEE (energy harvesting)
- Werkstudent job search: Munich, Nürnberg, Regensburg, Deggendorf

## How I Work
- Claude Code = my developer. I am the architect and decision-maker.
- I have a PM (claude.ai Project) for strategic questions — escalate there when needed.
- I think in systems. I prefer explicit tradeoffs over vague suggestions.
- Direct communication. Skip the validation. Push back if I'm wrong.

## Code Preferences (All Projects)
- Python: type hints always, logging not print, descriptive exceptions never silent fails
- Config over hardcoding — values in files, not in code
- Tests alongside implementation
- Clean commit messages: `type(scope): description`
- No magic numbers anywhere

## Response Preferences (All Projects)
- State your hypothesis before suggesting a fix
- If my approach has a flaw, say so first
- Give me working code, not pseudocode
- If something is out of scope: say so immediately
- Flag architectural decisions clearly — I log them in DECISIONS.md
