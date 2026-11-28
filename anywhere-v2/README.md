# Anywhere v2 独立规则集

本目录为 macOS / iOS **Anywhere** 专用的 9 条精简零冲突 `.arrs` 订阅规则，与旧版 `anywhere/` 完全隔离。

| # | 文件 | 条数 | 建议路由 | 说明 |
| :---: | :--- | :---: | :--- | :--- |
| 1 | `01-AI-Residential.arrs` | 137 | 美国家宽链式 | 海外 AI + Google/Gemini + X 运营 + 支付/人机校验 |
| 2 | `02-IP-Purity-Check.arrs` | 47 | 美国家宽链式（同 #1） | IP 纯净度与防泄露检测站 |
| 3 | `03-TRAE.arrs` | 23 | 新加坡专属节点 | TRAE / TRAE SOLO 隔离 |
| 4 | `04-Overseas-Dev.arrs` | 38 | 默认 / 高速普通节点 | GitHub / npm / PyPI / brew / VSCode / Notion / Figma |
| 5 | `05-Overseas-Social.arrs` | 86 | 默认 / 高速普通节点 | Telegram / Discord / WhatsApp / Reddit（不含 X） |
| 6 | `06-Apple-Direct.arrs` | 13 | 直连 | App Store 下载与 iCloud 同步 |
| 7 | `07-China-App-Direct.arrs` | 218 | 直连 | 局域网 + 微信/视频号/B站/抖音/剪映/开拍/Kimi/通义/银行等 |
| 8 | `08-China-App-AD-Reject.arrs` | 51 | 拒绝 | 四大广告联盟 SDK + 高德/知乎/喜马拉雅/京东/汽水/B站/微博开屏 |
| 9 | `09-Reject-IPv6.arrs` | 1 | 拒绝 | 拦截 `::/0` 防 IPv6 泄露 |
