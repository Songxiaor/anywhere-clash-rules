# anywhere-clash-rules

一套给 Clash / Clash Verge / Mihomo 用的完整分流。把下面 **9 条 YAML** 全部加上（或直接粘贴 `clash-verge.js`），不需要再去找 Loyalsoldier、ACL4SSR、VPSDance。

官方大陆白名单、广告、GFW、海外 AI 域名已经按类型融进对应规则包。

Anywhere 用户继续用 [`anywhere/*.arrs`](anywhere/)，和 Clash 包独立维护，**不会自动同步**。要更新 Clash 包时在本机运行 `python3 scripts/build.py` 再提交。

## 九条规则（按匹配顺序）

越靠前越优先。AI / TRAE / 开发者 会盖过后面的国内直连和 GFW 列表。

<!-- BEGIN:LINKS -->
<!-- END:LINKS -->

| 包 | 里面有什么 |
| --- | --- |
| `trae` | TRAE / TRAE SOLO |
| `ai` | Cursor、Claude、ChatGPT、Gemini、Grok、Copilot；已去掉 `google.com` / `x.com` 整站 |
| `bytedance` | 抖音、字节跳动（策略组里可改直连） |
| `dev` | GitHub、npm、PyPI、Hugging Face、Notion、Figma |
| `social` | Telegram、Discord、WhatsApp、X、Instagram、WebRTC STUN |
| `stream` | YouTube、Netflix、Disney+、Spotify、TikTok 国际版 |
| `reject` | 广告与追踪 |
| `direct` | 国内 App、国内 AI、Apple 下载/iCloud、局域网、CN IP |
| `proxy` | GFW、Google 其余、非 CN 后缀 |

## Clash Verge（推荐）

打开 [clash-verge.js](clash-verge.js)，全选复制，粘贴到 **订阅 → 全局扩展脚本**，保存。再启用带节点的订阅。

脚本会拉取上面 9 个 YAML，建好策略组，按表里的顺序分流。Cursor / Claude 桌面版请开 TUN。

## 其他 Clash / Mihomo 客户端

在配置里加 9 个 `rule-providers`，`rules` 顺序与上表一致。`reject` / `proxy` / `trae` / `dev` 用 `behavior: domain`，其余用 `classical`。不要漏加，也不要打乱顺序。

## 维护

```bash
python3 scripts/build.py
```

分类定义在 [`categories.json`](categories.json)。构建时会拉取 Loyalsoldier / VPSDance / blackmatrix7 并与 `anywhere/*.arrs` 合并去重。
