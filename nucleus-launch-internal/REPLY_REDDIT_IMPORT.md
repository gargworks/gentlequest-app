# Reddit Reply: Adding Existing Projects

**Context:** Reply to r/ClaudeAI user asking about adding existing projects.

**Draft:**

"Great question! Existing projects are exactly why Nucleus was designed. 🧠

**The Simple Way:**
1. `cd your-existing-project`
2. `nucleus-init`

This creates the `.brain/` folder and auto-configures your AI tools (Claude, Cursor, Windsurf) for that specific project. Then you can just ask your AI: 'Scan this project and save our key architectural decisions to my brain.'

**The 'Hyper-Speed' Way:**
We've added a `--scan` flag to the CLI specifically for this! Run:
`nucleus-init --scan`

This will automatically find your `README.md`, ingest the context, and seed your brain's memory before you even start talking to your agent.

It’s live on PyPI now. Give it a spin! 🚀"
