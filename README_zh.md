# json2vault

把任意 JSON 数据转换成结构化的 Obsidian 知识库。

[English](README.md)

```
JSON（任意来源）  ──>  json2vault  ──>  Obsidian Vault
                                         ├── notes/
                                         ├── index.md
                                         ├── tags.md
                                         └── media_manifest.json
```

## 为什么用这个

你可能有各种来源的收藏和笔记数据 — 社交媒体导出、API 返回、浏览器书签、RSS 阅读器。它们都是 JSON，但格式各不相同。json2vault 把它们统一转换成 Obsidian 可以直接打开的 vault，带有 YAML frontmatter、标签索引和媒体引用。

**零依赖** — 纯 Python 标准库，`pip install` 即可使用。

## 快速开始

```bash
pip install json2vault
```

```bash
# 自动检测格式，构建 vault
json2vault build -i my_data.json -o ./my-vault

# 在 Obsidian 中打开 → "Open folder as vault" → 选择 my-vault/
```

就这么简单。

## 支持的格式

| Adapter | 来源 | 自动检测 |
|---------|------|----------|
| `xhs` | 小红书 / RedNote 收藏 | ✅ |
| `twitter` | Twitter/X 数据导出 | ✅ |
| `weibo` | 微博帖子/收藏 | ✅ |
| `pocket` | Pocket 稍后阅读 | ✅ |
| `generic` | 任何带 title/content 字段的 JSON | ✅ |
| `universal` | json2vault 自有格式 | ✅ |

json2vault 会自动检测 JSON 格式并选择合适的 adapter。也可以手动指定：

```bash
json2vault build -i data.json -o ./vault --adapter xhs
```

### 自定义格式

如果你的 JSON 有 `title`、`content`、`date`、`tags`、`url` 等常见字段名，`generic` adapter 会自动处理，不需要写任何代码。

如果字段名完全不同，可以先转换成 json2vault 的通用格式：

```json
{
  "json2vault_version": "1",
  "notes": [
    {
      "id": "1",
      "title": "我的笔记",
      "content": "笔记内容",
      "tags": ["标签1", "标签2"],
      "date": "2024-01-15",
      "source_url": "https://example.com"
    }
  ]
}
```

## CLI 命令

```bash
# 构建 vault
json2vault build -i data.json -o ./vault

# 检查 JSON 格式（不生成文件）
json2vault check -i data.json

# 列出所有 adapter
json2vault adapters

# 创建 Karpathy 知识库骨架
json2vault init-kb -o ./my-knowledge-base
```

## 输出结构

```
my-vault/
├── .obsidian/       # Vault 配置（自动创建）
├── index.md         # 主索引
├── tags.md          # 标签索引（按频率排序）
├── notes/
│   ├── 笔记标题.md
│   └── ...
└── media_manifest.json  # 媒体下载清单（URL → 本地路径）
```

每个 Markdown 笔记包含：YAML frontmatter（标题、作者、日期、来源、标签、自定义元数据）、正文、媒体引用（`![[media/...]]`）、元数据 footer。

## Karpathy 知识库

json2vault 还可以创建一个 [Karpathy 风格的 LLM 知识库](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)骨架：

```bash
json2vault init-kb -o ./my-kb
```

这会创建：

```
my-kb/
├── raw/         # 不可变的原始数据
├── wiki/        # LLM 维护的知识 wiki
│   ├── entities/
│   ├── concepts/
│   ├── comparisons/
│   └── synthesis/
├── schema/      # LLM 行为规则
└── logs/        # 操作日志
```

工作流：用 `json2vault build` 把 JSON 转成 vault → 放到 `raw/` → 让 LLM 执行 ingest（读原始数据、更新 wiki 页面）→ 用 query 查询 → 用 lint 检查健康度。

## 设计哲学

- **零依赖** — 只用 Python 标准库，不引入任何第三方包
- **Adapter 模式** — 每种数据源一个 adapter，互不干扰，易于扩展
- **不碰网络** — json2vault 只做本地格式转换，不发任何网络请求
- **媒体清单** — 生成 `media_manifest.json`（URL → 本地路径映射），下载交给用户自己处理

## 环境要求

- Python 3.10+
- 无第三方依赖

## 许可证

MIT
