const fs = require('fs');
const file = '/home/tre/.openclaw/openclaw.json';
const data = JSON.parse(fs.readFileSync(file));

const broker = data.agents.list.find(a => a.id === 'broker');
if (broker && !broker.tools.alsoAllow.includes('cron')) {
  broker.tools.alsoAllow.push('cron');
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
  console.log("Aggiunto tool cron al broker");
} else {
  console.log("Tool cron gia presente o broker non trovato");
}
