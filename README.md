# PatentsWithCode

Turn software patents into interactive demos. Enter a search term like "pull to refresh" or "pinch to zoom," and the system finds the relevant patent, extracts the core invention, generates implementation specs, writes the code, and renders it as a working component you can interact with.

## How It Works

1. **Patent Search** - User enters query → MCP searches Google Patents/USPTO for matching patent
2. **Spec Generation** - Groq LLM reads patent PDF → generates <500 word technical specification focused on core patented interaction
3. **Code Generation** - Claude Code in E2B environment converts spec → single React component (frontend-only, no APIs, <30 second demo)
4. **Sandbox Execution** - E2B runs generated code in isolated environment
5. **Display** - User sees interactive component demonstrating the patent

Generated specs and code are cached in Supabase to avoid regenerating popular patents.

## Tech Stack

- **Frontend**: Next.js (TypeScript)
- **LLM (specs)**: open-sourced LLM served via Groq
- **Coding Agent**: Claude Code via E2B
- **Sandbox**: E2B
- **Database**: Supabase
- **Patent Access**: Docker MCP Hub (public patent databases)

## Project Structure

```
/app                 # Next.js app router
/components          # React components
/lib
  /mcp              # Patent search integration
  /groq             # Spec generation
  /e2b              # Sandbox + Claude Code execution
  /supabase         # Database client
/public              # Static assets
```

## Setup

```bash
# Install dependencies
npm install

# Environment variables (.env.local)
GROQ_API_KEY=
E2B_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
MCP_HUB_CONFIG=

# Run development server
npm run dev
```

## Limitations

- Demos are simplified - they show the core patented interaction, not full commercial implementations
- Single React component only - no backend, external APIs, or multi-file architectures
- Patent legalese is reduced to essential technical concepts for implementation
- Not all patents are feasible to demo (hardware-dependent, backend-heavy systems)
- Educational/research purposes only

## Notes

All patents (expired and active) are included. The project visualizes publicly available patent documents as interactive demos to make technical innovations more accessible. Generated code is not production-ready and exists solely to illustrate patented concepts.