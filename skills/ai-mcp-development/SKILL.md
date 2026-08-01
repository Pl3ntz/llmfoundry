---
name: ai-mcp-development
description: Build Model Context Protocol (MCP) servers and clients, stdio/HTTP transport, tools, resources, prompts, and auth. Use when creating or integrating MCP servers for agents.
---

# AI MCP Development

Build MCP servers that agents can actually use well.

## MCP model

```
Agent ←→ MCP client ←→ MCP server (tools, resources, prompts)
```

Three primitives:
- **Tools**, actions the agent calls (do things)
- **Resources**, data the agent reads (context)
- **Prompts**, reusable interaction templates

## Server setup

- **stdio transport**, subprocess, for local tools. Command + args.
- **HTTP/SSE transport**, remote, for shared services. URL + optional auth.
- SDKs: official MCP SDKs per language (TypeScript, Python, etc.).

```ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({ name: "my-tools", version: "1.0.0" });

server.tool(
  "search_docs",
  { query: z.string(), limit: z.number().optional() },
  async ({ query, limit }) => ({
    content: [{ type: "text", text: JSON.stringify(await searchDocs(query, limit)) }],
  })
);

await server.connect(new StdioServerTransport());
```

## Tool design for agents

- **One tool = one clear action.** Narrow beats broad.
- **Name = verb + noun** (`search_docs`, `create_ticket`, not `process`).
- **Description = purpose + when + returns**, this is the agent's contract.
- **Input schema explicit** (zod/json-schema), optional fields optional.
- **Return structured data**, not prose, agents parse it.
- Return errors as structured results, not thrown exceptions where the agent must guess.

## Resources

- Expose data as resources with URI scheme + MIME type.
- List via resource templates; keep templates shallow.
- Authentication/authorization per resource when sensitive.

## Auth

- Local stdio servers: env-based secrets.
- Remote servers: OAuth (Dynamic Client Registration, RFC 7591) or bearer tokens.
- Never bake secrets into tool results.

## Validation

1. Server starts, registers tools/resources
2. Each tool call returns the documented shape
3. Errors are structured and recoverable
4. Test through a real MCP client, not just raw invoke

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| One giant tool | Narrow, single-action tools |
| Vague description | Purpose + when + returns |
| Return prose | Return structured data |
| Throw everything | Structured errors + recoverable paths |
| Secret in result | Redact, use env/auth |

## Verification

- Tools register and respond to schema-valid calls
- Invalid input returns a helpful structured error
- Resource templates list and resolve
- Server works through the configured transport
