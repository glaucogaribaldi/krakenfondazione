const fs = require('fs');
const file = '/home/tre/.openclaw/openclaw.json';
const data = JSON.parse(fs.readFileSync(file));

// Rimuove i vecchi agenti
data.agents.list = data.agents.list.filter(a => a.id === 'main');

// Aggiunge il nuovo agente "fondazione"
data.agents.list.push({
  id: "fondazione",
  name: "fondazione",
  workspace: "/home/tre/.openclaw/workspace-fondazione",
  agentDir: "/home/tre/.openclaw/agents/fondazione/agent",
  model: {
    primary: "nemotron/unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
    fallbacks: []
  },
  identity: {
    name: "Nemo Fondazione",
    emoji: "🐋"
  },
  tools: {
    profile: "minimal",
    alsoAllow: [
      "web_fetch", "kraken-paper__kraken_paper_balance", "kraken-paper__kraken_ticker",
      "kraken-paper__kraken_ohlc", "kraken-paper__kraken_orderbook", "kraken-paper__kraken_paper_buy",
      "kraken-paper__kraken_paper_sell", "kraken-paper__kraken_paper_orders", "kraken-paper__kraken_paper_cancel",
      "kraken-paper__kraken_workspace_status", "read", "write", "exec", "process", "canvas"
    ]
  },
  contextTokens: 32768,
  params: { maxTokens: 4096 }
});

// Aggiunge l'account Telegram dedicato
if (!data.channels.telegram.accounts) data.channels.telegram.accounts = {};
data.channels.telegram.accounts["nemofondazione"] = {
  name: "Fondazione Trading Bot",
  botToken: "8684305386:AAHXhxuiVKMK0XFFdikoh2JEswbpUI4z8kc",
  dmPolicy: "open",
  allowFrom: ["*"],
  groupAllowFrom: ["*"]
};

// Aggiorna i binding: cancella quelli vecchi e lega Telegram a "fondazione"
if (!data.bindings) data.bindings = [];
data.bindings = data.bindings.filter(b => b.agentId !== 'nemotron-trader' && b.agentId !== 'architetto-gemini');
data.bindings.push({
  agentId: "fondazione",
  match: {
    channel: "telegram",
    accountId: "nemofondazione"
  }
});

fs.writeFileSync(file, JSON.stringify(data, null, 2));
