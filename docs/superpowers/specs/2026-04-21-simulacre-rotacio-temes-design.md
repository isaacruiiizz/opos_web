# Simulacre: Rotació de Temes i No Repetició de Preguntes

**Data:** 2026-04-21  
**Estat:** Aprovat

---

## Resum

Redisseny del mòdul de simulacre d'examen per:
1. Canviar el format a 15 preguntes (10 test + 3 breus + 2 suposits)
2. Implementar rotació sistemàtica de temes per garantir cobertura completa
3. Evitar repetició de conceptes gràcies a una blacklist per tema
4. Millorar la qualitat del prompt aprofitant el canvi a Llama 4 Scout (30K TPM)
5. Avaluació de respostes obertes en una sola crida sense delays

---

## Model d'IA

**Canvi:** `llama-3.3-70b-versatile` → `meta-llama/llama-4-scout-17b-16e-instruct`

- Llama 4 Scout és generació Llama 4 (MoE), qualitat superior a Llama 3.3 en benchmarks
- **30.000 TPM** al free tier de Groq vs 6.000 anteriors (5x més pressupost)
- Permet prompts més rics, respostes més detallades i avaluació en una sola crida

Pressupost de tokens per operació:
- Generació: ~1.400 input + ~2.500 output = ~3.900 tokens
- Avaluació (5 respostes): ~3.500 tokens total
- Marge còmode dins 30K TPM per minut

---

## Format de l'examen

| Tipus | Quantitat | Punts/pregunta | Total |
|-------|-----------|----------------|-------|
| test  | 10        | 0.25 (penalitza -1/3) | 2.5 pts |
| breu  | 3         | 0.5            | 1.5 pts |
| suposit | 2       | 1.0            | 2.0 pts |
| **TOTAL** | **15** |              | **6.0 pts** |

---

## Base de dades

### Taula `simulacre_state` (una sola fila, id=1)

```sql
CREATE TABLE IF NOT EXISTS simulacre_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    current_round INTEGER NOT NULL DEFAULT 1,
    pending_topics TEXT NOT NULL DEFAULT '[]'
);
```

- `current_round`: ronda activa, s'incrementa quan `pending_topics` queda buit
- `pending_topics`: JSON array d'enters amb els `topic_num` pendents de la ronda actual

### Taula `simulacre_topic_concepts` (una fila per tema)

```sql
CREATE TABLE IF NOT EXISTS simulacre_topic_concepts (
    topic_num INTEGER PRIMARY KEY,
    topic_titol TEXT NOT NULL,
    round_number INTEGER NOT NULL DEFAULT 0,
    concepts_used TEXT NOT NULL DEFAULT '[]'
);
```

- `round_number`: ronda en què es van usar els conceptes (permet detectar conceptes obsolets)
- `concepts_used`: JSON array de strings, màx 10 paraules clau per tema

### Lògica de ronda

1. Quan `pending_topics` queda buit: `current_round++`, reset `pending_topics` a tots els `topic_num` dels temes importants, buidar `concepts_used` de tots els temes
2. Mai s'eliminen files de `simulacre_topic_concepts`, simplement es sobreescriuen

---

## Backend

### `POST /api/simulacre/generate` — lògica ampliada

```
1. Carrega simulacre_state (current_round, pending_topics)
2. Si simulacre_state no existeix o pending_topics buit → inicialitza nova ronda
3. Tria fins a 10 temes de pending_topics (o tots si n'hi ha menys)
4. Carrega concepts_used per cada tema seleccionat
5. Construeix prompt de generació
6. Crida Llama 4 Scout → genera 15 preguntes JSON
7. Extreu conceptes de les preguntes i actualitza simulacre_topic_concepts a DB (commit immediat)
8. Retorna { questions, topics_used: [int], round: int }
```

El camp `topics_used` al response el guarda el store i l'envia al save quan l'examen acaba.

### Extracció de conceptes (al generate, sense crida extra a IA)

Per cada pregunta generada s'extreuen fins a 3 paraules significatives de l'`enunciat` (tokenització simple, excloent stopwords catalanes). Les paraules s'agrupen per `tema_num` i s'escriuen immediatament a `simulacre_topic_concepts`. Quan la llista supera 10 paraules per tema, es descarten les més antigues (FIFO).

Stopwords a excloure: `el la els les de d i a en per amb que un una uns unes es al del dels és ha han ser hi ho també però quan com si`.

### `POST /api/simulacre/save` — camp addicional

Nou camp al body (l'únic afegit):
```json
{ "topics_used": [3, 7, 12, ...] }
```

Lògica posterior al guardar:
```
1. Per cada topic_num a topics_used: eliminar de pending_topics
2. Si pending_topics queda buit: current_round++, reset pending_topics (tots els temes), buidar concepts_used
3. Guardar resultat com sempre
```

Els conceptes ja s'han actualitzat al generate; el save només gestiona la rotació de temes.

---

## Prompt de generació

```
Ets un tribunal d'oposicions C1 informàtica d'un ajuntament català petit 
(Maçanet de la Selva, ~10.000h). Genera un examen realista de 15 preguntes 
en format JSON array.

DISTRIBUCIÓ OBLIGATÒRIA: exactament 10 test + 3 breu + 2 suposit.

TEMES A COBRIR (usa TOTS, reparteix les preguntes entre ells):
{temes_text}

CONCEPTES JA USATS (no repeteixis cap d'aquests per al tema corresponent):
{blacklist_text}

REGLES DE QUALITAT:
- test: cas pràctic real d'ajuntament, no teoria abstracta. 4 opcions plausibles 
  (A/B/C/D), una clarament correcta. explicacio explica per qué la correcta és 
  correcta i per qué les altres no.
- breu: pregunta que exigeix explicar un procediment o decisió tècnica concreta. 
  resposta_model de 3-5 frases amb els punts clau. rubrica: llista de 3-4 
  conceptes que s'han d'esmentar.
- suposit: incident o projecte TIC real a l'ajuntament amb context detallat. 
  resposta_model estructurada en passos numerats. rubrica: criteris de valoració.
- Dificultat: 4 preguntes baixa, 8 mitjana, 3 alta (repartit entre tipus).
- Aplica normativa vigent (ENS, RGPD, LOPDGDD, Llei 39/2015) quan sigui rellevant.
- Seed de variació: {seed}

FORMAT (array JSON de exactament 15 objectes, sense text extra):
[
  {"id":1,"tema_num":3,"tema_titol":"...","tipus":"test","punts":0.25,
   "dificultat":"mitjana","enunciat":"...","opcions":{"A":"...","B":"...","C":"...","D":"..."},
   "correcta":"B","explicacio":"...","penalitza":true},
  {"id":2,"tema_num":7,"tema_titol":"...","tipus":"breu","punts":0.5,
   "dificultat":"alta","enunciat":"...","opcions":null,"correcta":null,
   "resposta_model":"...","rubrica":"Mencionar: X, Y, Z","explicacio":"...","penalitza":false},
  {"id":3,"tema_num":12,"tema_titol":"...","tipus":"suposit","punts":1.0,
   "dificultat":"alta","enunciat":"...","opcions":null,"correcta":null,
   "resposta_model":"...","rubrica":"Valorar: X, Y, Z","explicacio":"...","penalitza":false}
]
```

---

## Prompt d'avaluació

Aprofitant 30K TPM, avaluació de les 5 respostes obertes en una sola crida:

```
Ets un corrector estricte d'oposicions C1 informàtica. Avalua les 5 respostes.

ESCALA DE FACTORS:
- 0.0: absent, en blanc, o completament incorrecte
- 0.25: esmentats alguns conceptes però amb errors importants o molt incomplet
- 0.5: parcial, menciona conceptes clau però falta coherència o algun punt important
- 0.75: bona resposta amb algun punt menor que falta
- 1.0: correcta i completa, menciona tots els conceptes de la rúbrica

REGLES:
- Llegeix la resposta sencera de l'usuari. Valora el que ha escrit, no el que no ha escrit.
- Si l'usuari menciona conceptes correctes però amb paraules pròpies, reconeix-los.
- NO atribueixis coneixements no escrits explícitament per l'usuari.
- comentari: 1-2 frases explicant el factor. Màx 30 paraules.
- encerts/mancances: màx 3 items cadascun.

{items_text}

Respon ÚNICAMENT JSON array (sense text extra):
[{"id":1,"factor":0.75,"encerts":["X","Y"],"mancances":["Z"],"comentari":"..."}]
```

User answers truncated to 1500 chars each to stay within token budget.

---

## Frontend

### `simulacre.js` store

- `startGeneration`: guarda `topics_used` i `round` del response al store (nous camps reactius)
- `submitExam` / `saveSimulacre`: envia `topics_used` al backend (el backend ja té els conceptes)

### Indicador de progrés de ronda

A `PracticaView.vue` (panell de simulacre), afegir una línia de text:
```
Ronda 2 · 4 de 12 temes coberts
```

Dades provinents d'un nou endpoint `GET /api/simulacre/round-state`.

---

## Nous endpoints

| Mètode | Path | Descripció |
|--------|------|------------|
| GET | `/api/simulacre/round-state` | Retorna `{ round, pending, total_topics }` |

---

## Migració DB

Al startup del backend (a `database.py` o `main.py`): crear les dues taules noves si no existeixen. No afecta taules existents.

---

## Canvis de fitxers

| Fitxer | Tipus de canvi |
|--------|----------------|
| `backend/database.py` | Crear taules noves al startup |
| `backend/routers/simulacre.py` | Lògica de ronda, nou endpoint round-state, save ampliat |
| `backend/services/gemini.py` | Canvi model, prompts nous, avaluació sense batch |
| `frontend/src/stores/simulacre.js` | Enviar topics_used/new_concepts al save |
| `frontend/src/views/PracticaView.vue` | Indicador de ronda |
