# PatchContext：别再把整个仓库塞给 AI

PatchContext 是一个给 coding agent 用的“任务上下文包”生成器。

它解决的问题很直接：你不想把整个仓库都丢给 AI，只想让它先看和这个 issue、这段报错、这个 diff 真正相关的文件。

## 一句话

给一个 issue、失败日志或 git diff，PatchContext 自动选出最该读的文件，并解释每个文件为什么入选。

```bash
pip install patchcontext
patchcontext scan --repo . --issue issue.md --top 12 > context.md
```

生成的 `context.md` 可以直接贴给 Codex、Claude Code、ChatGPT，也可以放进 PR 调试记录里。

## 为什么需要它

AI coding agent 经常不是“缺上下文”，而是“上下文太吵”。

一个真实 bug 可能只涉及 5 到 20 个文件，但我们常常把几百个文件都打包给模型。结果模型读了很多无关代码，关键调用链反而被稀释，最后开始改错地方。

PatchContext 做的是第一遍筛选：

- 从 issue 里抓文件路径、类名、函数名和关键词；
- 从 traceback / CI 日志里抓真正报错的文件；
- 从 git diff 里抓本轮改动涉及的文件；
- 轻量分析 Python / JS / TS import 关系；
- 选中源码文件时，自动带上可能相关的测试邻居；
- 给每个候选文件打分，并写出入选理由。

它不是让 AI “完全理解项目”，而是先把入口收窄，让第一轮阅读更像资深工程师调 bug 的方式。

## 适合什么场景

- 给开源 PR 修 CI：先把失败日志转成上下文包。
- 接一个陌生 issue：先知道该读哪些文件。
- 让 coding agent 修 bug：减少无关文件噪声。
- 做 code review：把 diff 周边文件整理成一个可解释清单。
- 复现用户问题：把 issue 描述和 traceback 合起来生成阅读顺序。

## 和 Repomix / RepoWiki 的区别

Repomix 很适合把整个仓库打包给 LLM。PatchContext 不做 whole-repo packing，它只关心“这个任务需要哪些文件”。

RepoWiki 适合给仓库生成项目文档、模块说明和阅读指南。PatchContext 不写项目文档，它只生成某个 issue / log / diff 的任务上下文。

所以它们不是替代关系：

- 想给整个仓库做长期文档：用 RepoWiki。
- 想把整个仓库交给模型：用 Repomix。
- 想让模型先聚焦这个 bug：用 PatchContext。

## 使用示例

根据 issue 生成：

```bash
patchcontext scan --repo . --issue issue.md --top 12 > context.md
```

根据 pytest 失败日志生成：

```bash
pytest -q 2>&1 | tee pytest.log
patchcontext from-failure --repo . pytest.log
```

根据当前 diff 生成：

```bash
patchcontext from-diff --repo . --base main --format json
```

大仓库里可以跳过超大生成文件，避免它们污染排名：

```bash
patchcontext scan --repo . --issue issue.md --max-file-bytes 100000
```

## 输出长什么样

```markdown
| Rank | File | Score | Why selected |
|---:|---|---:|---|
| 1 | `src/app/sessions.py` | 72.50 | mentioned directly; content matches task terms |
| 2 | `tests/test_sessions.py` | 45.00 | mentioned directly |
```

重点不是分数本身，而是 “Why selected”。如果工具说不清楚为什么选这个文件，那它只是另一个黑盒。

## 设计边界

PatchContext 第一版刻意保持克制：

- 不调用在线 LLM；
- 不上传代码；
- 不做遥测；
- 不启动 LSP；
- 不生成长篇项目文档；
- 不假装排序永远正确。

它应该是一个便宜、确定、能放进 CI 或本地工作流的小工具。

## 开发

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m build
```

## License

MIT
