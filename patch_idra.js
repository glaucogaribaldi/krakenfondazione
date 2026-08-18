const fs = require('fs');
const file = '/home/tre/.openclaw/openclaw.json';
const data = JSON.parse(fs.readFileSync(file));

// Setup del Provider per il nuovo Llama-8B
if (!data.models.providers["fondazione-llm"]) {
  data.models.providers["fondazione-llm"] = {
    baseUrl: "http://100.73.54.72:8081/v1",
    api: "openai-responses",
    models: [{
      id: "llama-8b",
      name: "Llama 3.1 8B (Reporter)",
      api: "openai-responses",
      contextWindow: 65536,
      contextTokens: 60000,
      maxTokens: 8192
    }]
  };
}

// Modifica Agente Fondazione (Llama-8B)
const fondazione = data.agents.list.find(a => a.id === 'fondazione');
if (fondazione) {
  fondazione.model = { primary: "fondazione-llm/llama-8b", fallbacks: [] };
  fondazione.contextTokens = 60000;
  fondazione.identity = { name: "Fondazione Reporter", emoji: "📋" };
}

// Crea Agente Broker (Nemotron 30B)
data.agents.list = data.agents.list.filter(a => a.id !== 'broker');
data.agents.list.push({
  id: "broker",
  name: "broker",
  workspace: "/home/tre/.openclaw/workspace-fondazione",
  agentDir: "/home/tre/.openclaw/agents/broker/agent",
  model: {
    primary: "nemotron/unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
    fallbacks: []
  },
  identity: { name: "Nemo Broker", emoji: "📉" },
  tools: {
    profile: "minimal",
    alsoAllow: [
      "kraken-paper__kraken_paper_balance", "kraken-paper__kraken_ticker",
      "kraken-paper__kraken_ohlc", "kraken-paper__kraken_orderbook", "kraken-paper__kraken_paper_buy",
      "kraken-paper__kraken_paper_sell", "kraken-paper__kraken_paper_orders", "kraken-paper__kraken_paper_cancel",
      "exec", "process"
    ]
  },
  contextTokens: 15360,
  params: { maxTokens: 4096 }
});

fs.writeFileSync(file, JSON.stringify(data, null, 2));
