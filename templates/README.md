# anywhere-clash-rules

同一套分流规则，两个客户端各复制一条链接导入。

- **源文件**：[`anywhere/*.arrs`](anywhere/) — Anywhere 规则集，只改这里
- **生成文件**：[`clash/*.yaml`](clash/) — Clash Verge / Mihomo `rule-providers`，由脚本自动转换，不要手改

改 `.arrs` 并 push 到 `main` 后，GitHub Action 会重新生成 YAML 和本页链接表，两边规则保持同步。

## 复制链接

`AI-luodi-proxy` 含 `google.com` / `gmail.com` / `x.com`，是 Anywhere 里绑「AI 落地节点」用的桶。Clash Verge 不要把它整组丢进 `🤖 AI服务`，否则会抢走谷歌和社交流量。

<!-- BEGIN:LINKS -->
<!-- END:LINKS -->

第三方（不是本仓库维护）：[chikacya AI.arrs](https://raw.githubusercontent.com/chikacya/anywhere-rules/main/rules/common/AI.arrs) 给 Anywhere 用。Clash Verge 更建议用 [VPSDance/ai-proxy-rules](https://github.com/VPSDance/ai-proxy-rules)。

## Anywhere

1. 打开规则集 → 添加订阅
2. 粘贴上表 **Anywhere `.arrs`** 列的链接
3. 按「建议策略」把该规则集指到直连或某个节点

## Clash Verge

Clash Verge **不能**直接订阅 `.arrs`。用上表 **Clash Verge `.yaml`** 列，写进全局扩展脚本的 `rule-providers`：

```js
const mine = (id) => ({
  type: "http",
  behavior: "classical",
  format: "yaml",
  url: `https://raw.githubusercontent.com/Songxiaor/anywhere-clash-rules/main/clash/${id}.yaml`,
  path: `./ruleset/songxiaor/${id}.yaml`,
  interval: 86400,
});
```

规则顺序：更具体的名单在前。直连类放在 Loyalsoldier / GEOIP,CN 之前，代理类放在 `MATCH` 之前。

```text
RULE-SET,China-App-direct,全局直连
RULE-SET,Apple-download-direct,全局直连
RULE-SET,Overseas-Dev-Tools-proxy,节点选择
```

## 本地转换

```bash
python3 scripts/convert.py          # 从 anywhere/*.arrs 生成 clash/*.yaml
python3 scripts/convert.py --check  # 检查是否同步
```

只编辑 `anywhere/*.arrs`。生成物由脚本和 CI 负责。
