/**
 * Clash Verge 全局扩展脚本
 * 来源：https://github.com/Songxiaor/anywhere-clash-rules
 *
 * 用法：订阅页 → 全局扩展脚本 → 整份粘贴保存。
 * 先导入带节点的订阅；无节点时会报错。
 * Cursor / Claude 桌面版需要 TUN。
 */

const PACK = "https://testingcf.jsdelivr.net/gh/Songxiaor/anywhere-clash-rules@main/clash";

const domesticNameservers = [
  "https://dns.alidns.com/dns-query",
  "https://doh.pub/dns-query",
  "https://doh.360.cn/dns-query",
];

const foreignNameservers = [
  "https://1.1.1.1/dns-query",
  "https://1.0.0.1/dns-query",
];

const dnsConfig = {
  enable: true,
  listen: "0.0.0.0:1053",
  ipv6: true,
  "use-system-hosts": false,
  "cache-algorithm": "arc",
  "enhanced-mode": "fake-ip",
  "fake-ip-range": "198.18.0.1/16",
  "fake-ip-filter": ["+.lan", "+.local", "+.msftconnecttest.com", "+.msftncsi.com"],
  "default-nameserver": ["223.5.5.5", "119.29.29.29", "1.1.1.1", "8.8.8.8"],
  nameserver: [...domesticNameservers, ...foreignNameservers],
  "proxy-server-nameserver": [...domesticNameservers, ...foreignNameservers],
  "nameserver-policy": {
    "geosite:private,cn,geolocation-cn": domesticNameservers,
    "geosite:google,youtube,telegram,gfw,geolocation-!cn": foreignNameservers,
  },
};

const pack = (id, behavior) => ({
  type: "http",
  behavior,
  format: "yaml",
  url: `${PACK}/${id}.yaml`,
  path: `./ruleset/songxiaor/${id}.yaml`,
  interval: 86400,
});

const ruleProviders = {
  "trae": pack("trae", "domain"),
  "ai": pack("ai", "classical"),
  "bytedance": pack("bytedance", "classical"),
  "dev": pack("dev", "domain"),
  "social": pack("social", "classical"),
  "stream": pack("stream", "classical"),
  "reject": pack("reject", "domain"),
  "direct": pack("direct", "classical"),
  "proxy": pack("proxy", "domain"),
};

const rules = [
  "RULE-SET,trae,🤖 TRAE",
  "RULE-SET,ai,🤖 AI服务,no-resolve",
  "RULE-SET,bytedance,🎵 字节跳动",
  "RULE-SET,dev,🛠️ 开发者",
  "RULE-SET,social,💬 通讯社交,no-resolve",
  "RULE-SET,stream,📺 流媒体",
  "RULE-SET,reject,广告过滤",
  "RULE-SET,direct,全局直连,no-resolve",
  "RULE-SET,proxy,节点选择",
  "GEOIP,LAN,全局直连,no-resolve",
  "GEOIP,CN,全局直连,no-resolve",
  "MATCH,漏网之鱼",
];

const icon = (name) =>
  `https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/${name}.svg`;

const groupBaseOption = {
  interval: 300,
  timeout: 3000,
  url: "https://www.google.com/generate_204",
  lazy: true,
  "max-failed-times": 3,
  hidden: false,
};

const selectWithNodes = (name, extra, iconName) => ({
  ...groupBaseOption,
  name,
  type: "select",
  proxies: extra,
  "include-all": true,
  icon: icon(iconName),
});

function main(config) {
  const proxyCount = config?.proxies?.length ?? 0;
  const proxyProviderCount =
    typeof config?.["proxy-providers"] === "object"
      ? Object.keys(config["proxy-providers"]).length
      : 0;
  if (proxyCount === 0 && proxyProviderCount === 0) {
    throw new Error("配置文件中未找到任何代理，请先导入带节点的订阅");
  }

  config["dns"] = dnsConfig;
  config["proxy-groups"] = [
    selectWithNodes("节点选择", ["延迟选优", "故障转移"], "adjust"),
    {
      ...groupBaseOption,
      name: "延迟选优",
      type: "url-test",
      tolerance: 100,
      "include-all": true,
      icon: icon("speed"),
    },
    {
      ...groupBaseOption,
      name: "故障转移",
      type: "fallback",
      "include-all": true,
      icon: icon("ambulance"),
    },
    selectWithNodes("🤖 TRAE", ["节点选择", "延迟选优", "故障转移", "全局直连"], "chatgpt"),
    selectWithNodes("🤖 AI服务", ["节点选择", "延迟选优", "故障转移", "全局直连"], "chatgpt"),
    selectWithNodes("🎵 字节跳动", ["节点选择", "延迟选优", "故障转移", "全局直连"], "youtube"),
    selectWithNodes("🛠️ 开发者", ["节点选择", "延迟选优", "故障转移", "全局直连"], "link"),
    selectWithNodes("💬 通讯社交", ["节点选择", "延迟选优", "故障转移", "全局直连"], "telegram"),
    selectWithNodes("📺 流媒体", ["节点选择", "延迟选优", "故障转移", "全局直连"], "youtube"),
    {
      ...groupBaseOption,
      name: "广告过滤",
      type: "select",
      proxies: ["REJECT", "DIRECT"],
      icon: icon("bug"),
    },
    {
      ...groupBaseOption,
      name: "全局直连",
      type: "select",
      proxies: ["DIRECT", "节点选择", "延迟选优"],
      icon: icon("link"),
    },
    selectWithNodes("漏网之鱼", ["节点选择", "延迟选优", "全局直连"], "fish"),
  ];
  config["rule-providers"] = ruleProviders;
  config["rules"] = rules;
  return config;
}
