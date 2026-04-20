# Simulacre d'Examen — Design Spec
**Data:** 2026-04-20
**Examen objectiu:** Prova teòrico-pràctica C1 Informàtica — Ajuntament de Maçanet de la Selva

---

## 1. Resum

Nou mode "Simulacre d'Examen" dins la pestanya Pràctica de l'app OPOS C1. Genera 40 preguntes mixtes (resposta alternativa, breus, supòsits) exclusivament dels 30 temes de la secció "Temes a tenir en compte" (`bloc: importants`). Simula les condicions reals de l'examen: cronòmetre de 2 hores, nota /10, aprovat amb mínim 5. Cada test és diferent i l'IA inventa preguntes que van més enllà dels apunts.

---

## 2. Context de l'examen real (Edicte Maçanet — Base 9.1.2)

- **Tipus d'exercici:** Teòrico-pràctic (fins a 20 punts, repartit en 2 proves de 10 pts cadascuna)
- **Format:** Preguntes de resposta alternativa i/o breus i/o supòsits pràctics
- **Temps:** Màxim 2 hores per exercici
- **Aprovació:** Mínim 5/10 per superar cada prova

El simulacre reprodueix **una** de les dues proves.

---

## 3. Arquitectura

### 3.1 Ubicació en la UI

La pestanya Pràctica té dues zones:

```
📋 Pràctica
├── Targeta "Simulacre d'Examen" [NOU — part superior, color ambre]
│    └── Botó "Iniciar Simulacre" + últim resultat
│
└── [Selector de tema] + Modes per tema [EXISTENT]
```

La targeta és sempre visible, independent del tema actiu.

### 3.2 Flux de generació (una sola crida compacta)

```
Usuari → "Iniciar Simulacre"
    │
    ▼
Backend extreu els Flash-Check de tots 30 temes "importants"
(~1.200 tokens de context compacte)
    │
    ▼
Una sola crida a Groq amb:
  - Llista de 30 temes (títol + resum Flash-Check)
  - Instruccions: generar 40 preguntes mixtes, variades,
    inventar preguntes que apliquin coneixements al context
    municipal real, seed aleatòria per garantir variació
    │
    ▼ (~3.500 tokens total — dins del límit 6K TPM de Groq)
    │
    ▼
Backend rep 40 preguntes en JSON, les barreja i les retorna
    │
    ▼
Frontend inicia cronòmetre 2h i mostra la primera pregunta
```

### 3.3 Flux d'avaluació

```
Usuari finalitza (o s'acaba el temps)
    │
    ▼
Tipo test → autocorrecció instantània (ja feta pregunta per pregunta)
    │
    ▼
Breus + Supòsits → enviament al backend
    │
    Si ≤10 respostes obertes: 1 crida a Groq (~2.500 tokens)
    Si >10 respostes obertes: 2 crides seqüencials amb 15s de delay
    │
    ▼
Frontend rep puntuació + comentari per cada resposta oberta
    │
    ▼
Càlcul nota final → pantalla de resultats
```

---

## 4. Estructura de preguntes

### 4.1 Distribució (l'IA decideix, dins d'aquests rangs)

| Tipus | Rang | Avaluació |
|---|---|---|
| Resposta alternativa (4 opcions) | 15–25 | Immediata al clicar (autocorrecció) |
| Resposta breu (1–3 frases) | 10–18 | IA al final amb rúbrica |
| Supòsit pràctic (cas + resposta) | 2–5 | IA al final amb rúbrica |
| **Total** | **40** | |

### 4.2 Esquema JSON de cada pregunta

```json
{
  "id": 1,
  "tema": "importants_3",
  "tema_titol": "Interoperabilitat",
  "tipus": "test" | "breu" | "suposit",
  "dificultat": "baixa" | "mitjana" | "alta",
  "punts": 0.25,
  "enunciat": "...",
  "opcions": ["A) ...", "B) ...", "C) ...", "D) ..."],  // solo per tipus test
  "resposta_correcta": "A",  // solo per tipus test
  "explicacio": "...",  // per tots
  "rubrica": "..."  // per breus i supòsits: criteris de puntuació
}
```

### 4.3 Criteris estrictes per al prompt de l'IA

- Inventar preguntes que **apliquin** els conceptes a situacions reals de l'Ajuntament de Maçanet (no només reproduir els apunts)
- Cada pregunta ha de cobrir un tema diferent — distribuir equitativament entre els 30
- Les respostes alternatives han de tenir 3 distractors plausibles (no obviament incorrectes)
- Rúbrica de breus i supòsits: puntuar per conceptes clau presents, no per coincidència literal de paraules
- Penalització tipo test: resposta incorrecta resta 1/3 del valor de la pregunta (com en oposicions reals)

---

## 5. Sistema de puntuació

```
Nota final = (punts_test_nets + punts_breus + punts_suposits) / total_possible × 10

Punts tipo test nets:
  correcta → +punts_pregunta
  incorrecta → -punts_pregunta / 3
  en blanc → 0

Punts breus/supòsits (IA):
  0 = resposta incorrecta o absent
  0.5× = parcialment correcta (alguns conceptes clau)
  1× = correcta (conceptes clau presents, argumentació coherent)

Aprovat: nota ≥ 5.0
```

---

## 6. UI — Detall de pantalles

### 6.1 Targeta d'inici (dins PracticaView.vue)

- Color ambre/taronja per distingir-se dels modes normals (blaus)
- Mostra l'últim resultat si existeix: nota, aprovat/suspès, data
- Botó "Iniciar Simulacre" → loading spinner mentre genera (pot trigar 10–20s)

### 6.2 Pantalla d'examen (SimulacreView.vue — full screen)

- **Navbar fixa:** `Pregunta X/40` | `⏱ 1:43:21` (cronòmetre descendent, vermell quan queden <15min)
- Una pregunta per pantalla
- **Tipo test:** 4 botons → al clicar mostra ✓/✗ + explicació breu (no es pot canviar)
- **Breus/supòsits:** textarea amb autoguardat mentre s'escriu
- Índex de preguntes (lateral o modal): punts de color per estat (pendent/resposta/correcta/incorrecta)
- Navegació: "← Anterior" / "Següent →" + botó "Finalitzar" (amb confirmació si hi ha preguntes sense respondre)
- En arribar a 0:00 → enviament automàtic

### 6.3 Pantalla de resultats (SimulacreResults.vue)

- Nota gran i visual: barra de progrés, ✓ APROVAT / ✗ SUSPÈS
- Desglossament: tipo test X/Y correctes, breus X.X/Y punts, supòsits X.X/Y punts
- Temps emprat
- Botó "Veure correcció detallada" → llista totes les preguntes amb resposta donada, correcta i comentari IA
- Botó "Nou simulacre"

---

## 7. Backend — Nous endpoints i serveis

### 7.1 Endpoints (backend/routers/simulacre.py — fitxer nou)

```
POST /api/simulacre/generate
  → Extreu Flash-Check dels 30 temes importants
  → Crida a Groq per generar 40 preguntes
  → Retorna llista de preguntes JSON

POST /api/simulacre/evaluate
  → Rep: llista de {pregunta, resposta_usuari}
  → Crida a Groq per avaluar breus/supòsits (en 1 o 2 lots)
  → Retorna: {score, max_score, comment} per cada resposta

POST /api/simulacre/save
  → Desa resultat a SQLite
  → Retorna: ok

GET /api/simulacre/last
  → Retorna l'últim resultat desat
```

### 7.2 Nova taula SQLite: `simulacre_results`

```sql
CREATE TABLE simulacre_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT DEFAULT (datetime('now')),
  score REAL,
  passed INTEGER,
  time_taken_seconds INTEGER,
  q_test_correct INTEGER,
  q_test_total INTEGER,
  q_breus_score REAL,
  q_breus_total REAL,
  q_suposit_score REAL,
  q_suposit_total REAL
);
```

### 7.3 Nous mètodes al servei Groq (backend/services/groq_client.py)

```python
async def generate_simulacre(flash_checks: list[dict], seed: str) -> list[dict]:
    # Un prompt compacte amb els 30 Flash-Check + instruccions
    # Retorna 40 preguntes en JSON

async def evaluate_simulacre_answers(answers_batch: list[dict]) -> list[dict]:
    # Avalua breus i supòsits amb rúbrica
    # Si >10 respostes, fa 2 crides seqüencials amb asyncio.sleep(15)
```

### 7.4 Extractor de Flash-Check (backend/services/markdown_parser.py)

Nou helper `extract_flash_check(topic_content)` que extreu el bloc "Resum de conceptes clau (Flash-Check)" de cada tema. Mantén el context compacte per respectar el límit de 6K TPM de Groq.

---

## 8. Frontend — Fitxers nous i modificats

| Fitxer | Canvi |
|---|---|
| `frontend/src/views/PracticaView.vue` | Afegir targeta SimulacreCard a dalt |
| `frontend/src/components/practice/SimulacreCard.vue` | Targeta d'inici (nova) |
| `frontend/src/views/SimulacreView.vue` | Pantalla completa d'examen (nova) |
| `frontend/src/components/practice/SimulacreResults.vue` | Pantalla de resultats (nova) |
| `frontend/src/stores/simulacre.js` | Estat: preguntes, respostes, cronòmetre, resultats (nou) |
| `frontend/src/api/client.js` | Afegir crides als nous endpoints |
| `frontend/src/router/index.js` | Ruta `/simulacre` per a SimulacreView |

---

## 9. Limitacions i gestió d'errors

- **Groq 6K TPM:** Generació en 1 crida compacta (~3.500 tokens). Avaluació en lots de ≤10 respostes amb 15s entre lots si cal.
- **Fallada de generació:** Mostrar error i permetre reintentar. No iniciar el cronòmetre fins que les preguntes estiguin carregades.
- **Tancament accidental:** El store persisteix les respostes fins al moment (localStorage o sessionStorage). Si l'usuari torna, es pot reprendre.
- **JSON malformat de l'IA:** El backend valida l'estructura de cada pregunta i descarta/regenera les malformades.
