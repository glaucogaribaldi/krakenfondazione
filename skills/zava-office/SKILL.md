---
name: zava-office
description: Use when Giacomo wants to search, retrieve, update, or analyze Ufficio Zava memory entities (People 360, organizations, projects, open loops).
---

You are integrated with the Ufficio Zava database on the VPS.
You must use the custom CLI utility `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh` to perform any operations requested by the user.

## Commands available in your CLI:

1. **List all people:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh people`

2. **Retrieve a Person 360 profile (by ID or display name):**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh person "<id_or_name>"`

3. **Add a new canonical person:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh add-person "<display_name>" [email] [phone] [domain]`

4. **List all organizations:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh organizations`

5. **List all projects:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh projects`

6. **List all open loops:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh open-loops`

7. **Add a new open loop:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh add-open-loop "<owner_id>" "<title>" "<description>" "<type_PROMISE_or_REQUEST_or_FOLLOW_UP_or_DEADLINE>"`

8. **Add a fact/evidence:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh add-fact "<subject_type>" "<subject_id>" "<predicate>" "<truth_state>" "<confidence>" "<json_data>"`

9. **Execute an integrated search across entities:**
   `/home/tre/.openclaw/workspace/zavapublicoffice/services/zava-office-cli.sh search "<query>"`

## Design Principles:
- Always prefer reading from the CLI when Giacomo asks about a person, company, project, or commitment.
- Mark facts as `FACT` when you have direct evidence, or `INFERENCE` when you are deducing them.
- If Giacomo reports a new open loop, use `add-open-loop` to store it permanently in the database so it never gets lost.
