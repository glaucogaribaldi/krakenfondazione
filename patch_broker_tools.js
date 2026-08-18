const fs = require('fs');
const file = '/home/tre/.openclaw/openclaw.json';
const data = JSON.parse(fs.readFileSync(file));

const broker = data.agents.list.find(a => a.id === 'broker');
if (broker) {
  const tools = broker.tools.alsoAllow;
  if (!tools.includes('read')) tools.push('read'); // Serve per fargli leggere il suo CSV e auto-apprendere
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
  console.log("Aggiunto tool read al broker per auto-apprendimento da CSV");
} else {
  console.log("Broker non trovato");
}
