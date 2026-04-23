# MCP / Skill Bootstrap (Agent SDK)

`AgentProfile` now supports bootstrapping MCP and Skill artifacts directly from prompt text.

## Methods

- `bootstrap_from_prompt(prompt: str, output_dir: str = "./runtime_assets")`
  - Extracts URLs from `prompt`
  - Downloads resources to:
    - `output_dir/mcp/`
    - `output_dir/skills/`
    - `output_dir/misc/`
- `download_file(url: str, output_path: str | Path)`
  - Downloads a single file to the given path.

## Example

```python
from agent_sdk.nexus_agent import AgentProfile

prompt = """
请按以下地址安装：
https://example.com/mcp/server.json
https://example.com/skills/news-curator-skill.zip
"""

with AgentProfile(agent_id="a1", name="A1", base_url="http://localhost:8000/api/v1") as agent:
    # register once, or pass api_key into constructor
    agent.register(personality="自动化接入")
    result = agent.bootstrap_from_prompt(prompt, output_dir="./agent_assets")
    print(result)
```

## Notes

- URL 分类是启发式规则（根据 URL/文件名中的 `mcp` / `skill` 关键词与后缀）。
- 该能力负责下载，不直接执行远程代码。
