# Tools

Various tools and MCPs for agent use.

## Available MCP Servers

`code-mcp`

Includes the following tools: 
- `ls`
- `glob` - Uses ripgrep file listing.
- `grep` - Uses ripgrep. Includes 2 lines before and 2 lines after the result as context.
- `read` - Reads a file with numbered lines. Limits output to 500 lines by default.
- `edit` - Edits a file with several fallback matching strategies based on `codemcp` from ezyang [[link](https://github.com/ezyang/codemcp)].
- `replace_regex` - Replaces text w a regex pattern.
- `write` - Writes full file content.

Differences from `modelcontextprotocol/servers/filesystem` [[link](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)]:
- `filesystem` does not have grep.
- `filesystem` uses a slow, recursive pattern match instead of ripgrep or even glob.
- `filesystem` is 800 lines of typescript code. `code-mcp` is 200 lines and super easy to extend.

`git-mcp`

Contains basic git commands for managing repositories. 

Differences from `github/github-mcp-server` [[link](https://github.com/github/github-mcp-server)]: 
- GH requires an entire Docker installation.
- `git-mcp` is <150 loc and extensible. It doesn't contain extensive permission options, so be sure to only operate in trusted sandboxes and scope your GH tokens correctly. 

`docs-mcp`

Contains basic commands for editing Google Docs.

TODO(cadentj): List some differences.

*Main difference is that, Google's default cli and api tools suck. They only give you append at the bottom of a doc options, in a TERRIBLE rich text format. If you don't know what that's like, check out Lexical [[link](https://playground.lexical.dev/)]. This is verbose and hard to make concise edits to.*