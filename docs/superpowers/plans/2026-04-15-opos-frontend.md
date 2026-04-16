# OPOS Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mobile-first Vue 3 SPA with four study tabs (Apunts, Flashcards, Pràctica, Progrés), dark/light theme, and full integration with the FastAPI backend.

**Architecture:** Vite + Vue 3 Composition API, Pinia for state, Vue Router for tabs, Tailwind for styling. API calls centralized in `src/api/client.js`. All components in `src/components/` organized by feature domain.

**Tech Stack:** Vue 3, Vite 5, Tailwind CSS 3, Pinia, Vue Router 4, Axios, marked.js, highlight.js, Fabric.js 5, Vitest, Vue Test Utils

---

## File Structure

```
/opt/opos-frontend/           (or local: C:\dev\opos-frontend\)
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── vitest.config.js
├── src/
│   ├── main.js               # App mount, Pinia, Router
│   ├── App.vue               # Root: Navbar + Drawer + RouterView + BottomTabBar
│   ├── router/
│   │   └── index.js          # 4 routes: /apunts, /flash, /practica, /progres
│   ├── stores/
│   │   ├── topics.js         # Pinia: topic list, active topic, progress
│   │   └── ui.js             # Pinia: theme (dark/light), drawer open/close
│   ├── api/
│   │   └── client.js         # Axios instance + typed API functions
│   ├── views/
│   │   ├── ApuntsView.vue    # Tab: 📖 Apunts — topic content + annotations + drawing
│   │   ├── FlashcardsView.vue # Tab: 🃏 Flash — Leitner deck + card review
│   │   ├── PracticaView.vue  # Tab: 🎯 Pràctica — mode selector + exercise
│   │   └── ProgresView.vue   # Tab: 📊 Progrés — charts + exam readiness
│   └── components/
│       ├── layout/
│       │   ├── Navbar.vue         # Top bar: ☰ | title | active topic | 🌙/☀️
│       │   ├── BottomTabBar.vue   # 4 thumb-zone tabs
│       │   └── TopicDrawer.vue    # Overlay topic list with progress dots
│       ├── apunts/
│       │   ├── TopicContent.vue   # Rendered markdown (marked.js + highlight.js)
│       │   ├── SectionIndex.vue   # Collapsible h2/h3/h4 jump links
│       │   ├── AnnotationLayer.vue # Text selection → color picker + note
│       │   └── DrawingCanvas.vue  # Fabric.js canvas overlay
│       ├── flashcards/
│       │   ├── FlipCard.vue       # Flip animation + front/back
│       │   └── LeitnerDeck.vue    # Due-card queue + "Sabia"/"No sabia" controls
│       ├── practice/
│       │   ├── ModeSelector.vue   # 5 exercise type buttons
│       │   ├── TestMode.vue       # Multiple choice (10 Q)
│       │   ├── BreusMode.vue      # Short answer (5 Q) + Gemini evaluation
│       │   ├── SupositMode.vue    # Practical case + evaluation
│       │   ├── ConnectaMode.vue   # Drag-and-drop term matching
│       │   └── BuitsMode.vue      # Fill-in-the-blanks auto-correction
│       └── progres/
│           ├── ProgressBar.vue    # Reusable bar with label + %
│           └── ExamReadiness.vue  # Gemini readiness + priority topics
└── tests/
    ├── setup.js
    ├── unit/
    │   ├── stores.test.js
    │   ├── FlipCard.test.js
    │   ├── TestMode.test.js
    │   ├── BuitsMode.test.js
    │   └── ConnectaMode.test.js
    └── api/
        └── client.test.js
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `package.json`, `vite.config.js`, `tailwind.config.js`, `postcss.config.js`, `index.html`, `src/main.js`, `src/App.vue`, `vitest.config.js`, `tests/setup.js`

- [ ] **Step 1: Scaffold the project**

```bash
# Run on the machine where you'll develop (Windows or Oracle server)
npm create vite@latest opos-frontend -- --template vue
cd opos-frontend
npm install
npm install -D tailwindcss@3 postcss autoprefixer vitest @vue/test-utils jsdom
npm install pinia vue-router@4 axios marked highlight.js fabric
npx tailwindcss init -p
```

- [ ] **Step 2: Configure tailwind.config.js**

Replace content with:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',
        surface: {
          light: '#FFFFFF',
          dark: '#1E1E2E',
        }
      }
    }
  },
  plugins: [],
}
```

- [ ] **Step 3: Configure vite.config.js**

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  },
  build: {
    outDir: 'dist'  // Docker copies dist/ into nginx image
  }
})
```

- [ ] **Step 4: Configure vitest.config.js**

```js
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.js'],
    globals: true,
  }
})
```

- [ ] **Step 5: Create tests/setup.js**

```js
import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'

config.global.plugins = [createPinia()]
```

- [ ] **Step 6: Create src/main.js**

```js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import './style.css'

createApp(App).use(createPinia()).use(router).mount('#app')
```

- [ ] **Step 7: Create src/style.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-bg: #ffffff;
  --color-text: #111827;
  --color-surface: #f9fafb;
  --color-border: #e5e7eb;
}
.dark {
  --color-bg: #1e1e2e;
  --color-text: #cdd6f4;
  --color-surface: #181825;
  --color-border: #313244;
}
body {
  background-color: var(--color-bg);
  color: var(--color-text);
}
```

- [ ] **Step 8: Create stub App.vue**

```vue
<template>
  <div class="min-h-screen flex flex-col">
    <Navbar />
    <TopicDrawer />
    <main class="flex-1 overflow-y-auto pb-16">
      <RouterView />
    </main>
    <BottomTabBar />
  </div>
</template>

<script setup>
import Navbar from './components/layout/Navbar.vue'
import BottomTabBar from './components/layout/BottomTabBar.vue'
import TopicDrawer from './components/layout/TopicDrawer.vue'
import { useUiStore } from './stores/ui.js'
const ui = useUiStore()
</script>
```

- [ ] **Step 9: Create src/router/index.js**

```js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/apunts' },
  { path: '/apunts', component: () => import('../views/ApuntsView.vue') },
  { path: '/flash', component: () => import('../views/FlashcardsView.vue') },
  { path: '/practica', component: () => import('../views/PracticaView.vue') },
  { path: '/progres', component: () => import('../views/ProgresView.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
```

- [ ] **Step 10: Create 4 stub view files**

Create each with minimal content:
```vue
<!-- src/views/ApuntsView.vue -->
<template><div class="p-4">Apunts</div></template>
```
(same pattern for FlashcardsView.vue, PracticaView.vue, ProgresView.vue)

- [ ] **Step 11: Verify dev server starts**

```bash
npm run dev
```
Expected: server starts at `http://localhost:5173`, no console errors, blank page with "Apunts" text.

- [ ] **Step 12: Commit**

```bash
git init && git add .
git commit -m "feat: Vue 3 + Vite + Tailwind scaffold with routing and stub views"
```

---

## Task 2: API Client + Stores

**Files:**
- Create: `src/api/client.js`
- Create: `src/stores/topics.js`
- Create: `src/stores/ui.js`
- Test: `tests/unit/stores.test.js`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/stores.test.js`:
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUiStore } from '../../src/stores/ui.js'
import { useTopicsStore } from '../../src/stores/topics.js'
import * as client from '../../src/api/client.js'

beforeEach(() => { setActivePinia(createPinia()) })

describe('uiStore', () => {
  it('starts with system theme preference', () => {
    const ui = useUiStore()
    expect(['dark', 'light']).toContain(ui.theme)
  })

  it('toggleTheme switches dark/light', () => {
    const ui = useUiStore()
    ui.theme = 'light'
    ui.toggleTheme()
    expect(ui.theme).toBe('dark')
    ui.toggleTheme()
    expect(ui.theme).toBe('light')
  })

  it('drawer starts closed', () => {
    const ui = useUiStore()
    expect(ui.drawerOpen).toBe(false)
  })

  it('openDrawer / closeDrawer work', () => {
    const ui = useUiStore()
    ui.openDrawer()
    expect(ui.drawerOpen).toBe(true)
    ui.closeDrawer()
    expect(ui.drawerOpen).toBe(false)
  })
})

describe('topicsStore', () => {
  it('fetches topics from API', async () => {
    const mockTopics = [
      { id: 'general_1', title: 'Tema 1', bloc: 'general', number: 1, overall_pct: 0 }
    ]
    vi.spyOn(client, 'fetchTopics').mockResolvedValue(mockTopics)
    const store = useTopicsStore()
    await store.loadTopics()
    expect(store.topics).toHaveLength(1)
    expect(store.topics[0].id).toBe('general_1')
  })

  it('setActiveTopic updates activeTopicId', () => {
    const store = useTopicsStore()
    store.setActiveTopic('general_2')
    expect(store.activeTopicId).toBe('general_2')
  })

  it('generalTopics and especificTopics getters filter correctly', () => {
    const store = useTopicsStore()
    store.topics = [
      { id: 'general_1', bloc: 'general', overall_pct: 50 },
      { id: 'especific_1', bloc: 'especific', overall_pct: 0 },
    ]
    expect(store.generalTopics).toHaveLength(1)
    expect(store.especificTopics).toHaveLength(1)
  })
})
```

- [ ] **Step 2: Run tests — expect failure**

```bash
npm run test -- --reporter=verbose
```
Expected: `Cannot find module '../../src/api/client.js'`

- [ ] **Step 3: Create src/api/client.js**

```js
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const fetchTopics = async () => (await api.get('/topics')).data
export const fetchTopicContent = async (id) => (await api.get(`/topics/${id}/content`)).data
export const fetchAnnotations = async (id) => (await api.get(`/topics/${id}/annotations`)).data
export const saveAnnotation = async (id, payload) => (await api.post(`/topics/${id}/annotations`, payload)).data
export const deleteAnnotation = async (annId) => api.delete(`/annotations/${annId}`)
export const fetchDrawing = async (id) => (await api.get(`/topics/${id}/drawings`)).data
export const saveDrawing = async (id, canvas_json) => (await api.post(`/topics/${id}/drawings`, { canvas_json })).data
export const fetchFlashcards = async (id) => (await api.get(`/topics/${id}/flashcards`)).data
export const createFlashcard = async (id, payload) => (await api.post(`/topics/${id}/flashcards`, payload)).data
export const generateFlashcards = async (id) => (await api.post(`/topics/${id}/flashcards/generate`)).data
export const reviewFlashcard = async (cardId, knew_it) => (await api.post(`/flashcards/${cardId}/review`, { knew_it })).data
export const generatePractice = async (id, mode) => (await api.post(`/topics/${id}/practice/${mode}/generate`)).data
export const evaluateAnswer = async (payload) => (await api.post('/practice/evaluate', payload)).data
export const saveSession = async (payload) => (await api.post('/practice/sessions', payload)).data
export const fetchProgress = async () => (await api.get('/progress')).data
export const fetchExamReadiness = async () => (await api.get('/progress/exam-readiness')).data
export const runPdfAnalysis = async () => (await api.post('/pdf/analyze')).data
export const fetchPdfAnalysis = async () => (await api.get('/pdf/analysis')).data
export const fetchConfig = async () => (await api.get('/config')).data
export const saveConfig = async (key, value) => (await api.post('/config', { key, value })).data
```

- [ ] **Step 4: Create src/stores/ui.js**

```js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const systemPrefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  const theme = ref(systemPrefersDark ? 'dark' : 'light')
  const drawerOpen = ref(false)

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  function openDrawer() { drawerOpen.value = true }
  function closeDrawer() { drawerOpen.value = false }

  // Apply theme on init
  document.documentElement.classList.toggle('dark', theme.value === 'dark')

  return { theme, drawerOpen, toggleTheme, openDrawer, closeDrawer }
})
```

- [ ] **Step 5: Create src/stores/topics.js**

```js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchTopics } from '../api/client.js'

export const useTopicsStore = defineStore('topics', () => {
  const topics = ref([])
  const activeTopicId = ref('general_1')

  const generalTopics = computed(() => topics.value.filter(t => t.bloc === 'general'))
  const especificTopics = computed(() => topics.value.filter(t => t.bloc === 'especific'))
  const activeTopic = computed(() => topics.value.find(t => t.id === activeTopicId.value))

  async function loadTopics() {
    topics.value = await fetchTopics()
    if (!activeTopicId.value && topics.value.length) {
      activeTopicId.value = topics.value[0].id
    }
  }

  function setActiveTopic(id) {
    activeTopicId.value = id
  }

  function updateTopicProgress(id, overall_pct) {
    const t = topics.value.find(t => t.id === id)
    if (t) t.overall_pct = overall_pct
  }

  return { topics, activeTopicId, activeTopic, generalTopics, especificTopics,
           loadTopics, setActiveTopic, updateTopicProgress }
})
```

- [ ] **Step 6: Run tests — expect pass**

```bash
npm run test -- --reporter=verbose
```
Expected: 8 tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/api/client.js src/stores/ui.js src/stores/topics.js tests/unit/stores.test.js tests/setup.js vitest.config.js
git commit -m "feat: API client (all endpoints) + Pinia stores for topics and UI state"
```

---

## Task 3: Layout Components

**Files:**
- Create: `src/components/layout/Navbar.vue`
- Create: `src/components/layout/BottomTabBar.vue`
- Create: `src/components/layout/TopicDrawer.vue`

- [ ] **Step 1: Create src/components/layout/Navbar.vue**

```vue
<template>
  <header class="fixed top-0 left-0 right-0 z-40 h-14 flex items-center
                 px-3 gap-3 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
    <!-- Hamburger -->
    <button @click="ui.openDrawer()"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-xl">
      ☰
    </button>
    <!-- Title -->
    <span class="font-bold text-primary text-lg">OPOS C1</span>
    <!-- Active topic name (truncated) -->
    <span v-if="topics.activeTopic"
          class="flex-1 text-sm text-gray-500 dark:text-gray-400 truncate">
      {{ topics.activeTopic.title }}
    </span>
    <span v-else class="flex-1" />
    <!-- Theme toggle -->
    <button @click="ui.toggleTheme()"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-xl">
      {{ ui.theme === 'dark' ? '☀️' : '🌙' }}
    </button>
  </header>
  <!-- Spacer so content doesn't hide under fixed header -->
  <div class="h-14" />
</template>

<script setup>
import { useUiStore } from '../../stores/ui.js'
import { useTopicsStore } from '../../stores/topics.js'
const ui = useUiStore()
const topics = useTopicsStore()
</script>
```

- [ ] **Step 2: Create src/components/layout/BottomTabBar.vue**

```vue
<template>
  <nav class="fixed bottom-0 left-0 right-0 z-40 h-16 flex
              bg-[var(--color-surface)] border-t border-[var(--color-border)]">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to"
      class="flex-1 flex flex-col items-center justify-center gap-0.5 text-xs
             text-gray-500 dark:text-gray-400 transition-colors
             [&.router-link-active]:text-primary [&.router-link-active]:font-semibold">
      <span class="text-2xl leading-none">{{ tab.icon }}</span>
      <span>{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup>
const tabs = [
  { to: '/apunts',   icon: '📖', label: 'Apunts'   },
  { to: '/flash',    icon: '🃏', label: 'Flash'     },
  { to: '/practica', icon: '🎯', label: 'Pràctica'  },
  { to: '/progres',  icon: '📊', label: 'Progrés'   },
]
</script>
```

- [ ] **Step 3: Create src/components/layout/TopicDrawer.vue**

```vue
<template>
  <!-- Backdrop -->
  <Transition name="fade">
    <div v-if="ui.drawerOpen"
         class="fixed inset-0 z-50 bg-black/40"
         @click="ui.closeDrawer()" />
  </Transition>
  <!-- Drawer panel -->
  <Transition name="slide">
    <aside v-if="ui.drawerOpen"
           class="fixed top-0 left-0 bottom-0 z-50 w-72
                  bg-[var(--color-surface)] border-r border-[var(--color-border)]
                  overflow-y-auto flex flex-col">
      <div class="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
        <span class="font-bold text-lg">Temari</span>
        <button @click="ui.closeDrawer()" class="text-2xl p-1">✕</button>
      </div>

      <!-- Bloc General -->
      <section class="p-2">
        <p class="text-xs font-semibold uppercase text-gray-400 px-2 py-1">Bloc General</p>
        <TopicItem v-for="t in topics.generalTopics" :key="t.id" :topic="t"
                   @select="selectTopic(t.id)" />
      </section>

      <!-- Bloc Específic -->
      <section class="p-2">
        <p class="text-xs font-semibold uppercase text-gray-400 px-2 py-1">Bloc Específic</p>
        <TopicItem v-for="t in topics.especificTopics" :key="t.id" :topic="t"
                   @select="selectTopic(t.id)" />
      </section>
    </aside>
  </Transition>
</template>

<script setup>
import { useUiStore } from '../../stores/ui.js'
import { useTopicsStore } from '../../stores/topics.js'
import { useRouter } from 'vue-router'

const ui = useUiStore()
const topics = useTopicsStore()
const router = useRouter()

function selectTopic(id) {
  topics.setActiveTopic(id)
  ui.closeDrawer()
  router.push('/apunts')
}

// Inline sub-component to avoid extra file
</script>

<!-- TopicItem inline component -->
<script>
const TopicItem = {
  props: ['topic'],
  emits: ['select'],
  template: `
    <button @click="$emit('select')"
      class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm
             hover:bg-primary/10 transition-colors"
      :class="{ 'bg-primary/10 text-primary font-medium': isActive }">
      <span class="text-base" :title="progressLabel">{{ dot }}</span>
      <span class="truncate">Tema {{ topic.number }}: {{ topic.title }}</span>
    </button>
  `,
  computed: {
    isActive() {
      return useTopicsStore().activeTopicId === this.topic.id
    },
    dot() {
      const p = this.topic.overall_pct
      if (p >= 80) return '✓'
      if (p >= 40) return '◑'
      return '○'
    },
    progressLabel() { return `${Math.round(this.topic.overall_pct)}%` }
  }
}
export default { components: { TopicItem } }
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-active, .slide-leave-active { transition: transform 0.25s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(-100%); }
</style>
```

- [ ] **Step 4: Wire stores into App.vue — load topics on mount**

Update `src/App.vue`:
```vue
<template>
  <div :class="{ dark: ui.theme === 'dark' }" class="min-h-screen flex flex-col
       bg-[var(--color-bg)] text-[var(--color-text)]">
    <Navbar />
    <TopicDrawer />
    <main class="flex-1 overflow-y-auto pb-16 pt-0">
      <RouterView />
    </main>
    <BottomTabBar />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Navbar from './components/layout/Navbar.vue'
import BottomTabBar from './components/layout/BottomTabBar.vue'
import TopicDrawer from './components/layout/TopicDrawer.vue'
import { useUiStore } from './stores/ui.js'
import { useTopicsStore } from './stores/topics.js'

const ui = useUiStore()
const topics = useTopicsStore()
onMounted(() => topics.loadTopics())
</script>
```

- [ ] **Step 5: Verify in browser**

```bash
npm run dev
```
Open `http://localhost:5173`:
- Navbar shows ☰, "OPOS C1", 🌙
- Bottom bar shows 4 tabs, active tab highlighted in blue
- Clicking ☰ opens drawer with "Temari" header
- Clicking outside closes drawer
- Clicking 🌙 toggles dark mode

- [ ] **Step 6: Commit**

```bash
git add src/App.vue src/components/layout/
git commit -m "feat: Navbar, BottomTabBar, TopicDrawer with dark mode and topic navigation"
```

---

## Task 4: Apunts Tab — Content Rendering + Section Index

**Files:**
- Modify: `src/views/ApuntsView.vue`
- Create: `src/components/apunts/TopicContent.vue`
- Create: `src/components/apunts/SectionIndex.vue`

- [ ] **Step 1: Create src/components/apunts/SectionIndex.vue**

```vue
<template>
  <details class="mb-4 border border-[var(--color-border)] rounded-lg">
    <summary class="px-4 py-2 cursor-pointer font-semibold text-sm select-none">
      Índex del tema ▾
    </summary>
    <nav class="px-4 pb-3 space-y-0.5">
      <a v-for="h in headings" :key="h.anchor"
         :href="`#${h.anchor}`"
         :style="{ paddingLeft: `${(h.level - 2) * 12}px` }"
         class="block text-sm text-primary hover:underline py-0.5 truncate">
        {{ h.text }}
      </a>
    </nav>
  </details>
</template>

<script setup>
defineProps({ headings: { type: Array, default: () => [] } })
</script>
```

- [ ] **Step 2: Create src/components/apunts/TopicContent.vue**

```vue
<template>
  <div class="px-4 pb-8">
    <SectionIndex :headings="headings" />
    <div ref="contentEl"
         class="prose prose-sm dark:prose-invert max-w-none
                [&_code]:bg-gray-100 dark:[&_code]:bg-gray-800
                [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:p-3"
         v-html="renderedHtml" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import SectionIndex from './SectionIndex.vue'

const props = defineProps({
  content: { type: String, default: '' },
  headings: { type: Array, default: () => [] }
})

// Configure marked with highlight.js
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true,
})

// Add heading IDs for anchor navigation
const renderer = new marked.Renderer()
renderer.heading = (text, level) => {
  const anchor = text.toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
  return `<h${level} id="${anchor}" class="scroll-mt-16">${text}</h${level}>`
}
marked.use({ renderer })

const renderedHtml = computed(() => marked.parse(props.content || ''))
</script>
```

- [ ] **Step 3: Update src/views/ApuntsView.vue**

```vue
<template>
  <div>
    <!-- Mode toggle toolbar -->
    <div class="sticky top-0 z-30 flex items-center gap-2 px-4 py-2
                bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <button @click="mode = 'text'"
              :class="mode === 'text' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors">
        ✏️ Text
      </button>
      <button @click="mode = 'draw'"
              :class="mode === 'draw' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors">
        🖊️ Dibuix
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center h-48">
      <span class="text-gray-400 animate-pulse">Carregant tema…</span>
    </div>

    <!-- Content area -->
    <div v-else class="relative">
      <TopicContent v-show="mode === 'text'"
                    :content="topicData?.content"
                    :headings="topicData?.headings || []" />
      <DrawingCanvas v-if="mode === 'draw'"
                     :topic-id="topics.activeTopicId" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { fetchTopicContent } from '../api/client.js'
import TopicContent from '../components/apunts/TopicContent.vue'
import DrawingCanvas from '../components/apunts/DrawingCanvas.vue'

const topics = useTopicsStore()
const topicData = ref(null)
const loading = ref(false)
const mode = ref('text')

async function loadContent(id) {
  if (!id) return
  loading.value = true
  try {
    topicData.value = await fetchTopicContent(id)
  } finally {
    loading.value = false
  }
}

watch(() => topics.activeTopicId, loadContent, { immediate: true })
</script>
```

- [ ] **Step 4: Verify in browser**

With backend running (`uvicorn main:app --port 8000 --reload`):
- Open a topic from the drawer
- Content renders with styled headings and code blocks
- Clicking "Índex del tema" expands the section index
- Clicking a section link scrolls to it

- [ ] **Step 5: Commit**

```bash
git add src/views/ApuntsView.vue src/components/apunts/TopicContent.vue src/components/apunts/SectionIndex.vue
git commit -m "feat: Apunts tab with markdown rendering, syntax highlighting, collapsible section index"
```

---

## Task 5: Annotations (Text Highlight Layer)

**Files:**
- Create: `src/components/apunts/AnnotationLayer.vue`

The annotation layer is a transparent overlay that detects text selection and shows a color picker. It does not reposition elements — it just intercepts `mouseup`/`touchend` events on the content div.

- [ ] **Step 1: Create src/components/apunts/AnnotationLayer.vue**

```vue
<template>
  <div ref="wrapEl" class="relative" @mouseup="onSelectionEnd" @touchend="onSelectionEnd">
    <!-- Slot: the actual topic content sits here -->
    <slot />

    <!-- Color picker popover (appears near selection) -->
    <Transition name="fade">
      <div v-if="picker.visible"
           :style="{ top: picker.y + 'px', left: picker.x + 'px' }"
           class="fixed z-50 flex items-center gap-2 bg-white dark:bg-gray-800
                  border border-gray-200 dark:border-gray-700 shadow-lg
                  rounded-xl px-3 py-2">
        <button v-for="c in colors" :key="c.name"
                @click="applyAnnotation(c.name)"
                :class="c.bg"
                class="w-7 h-7 rounded-full border-2 border-white shadow hover:scale-110 transition-transform"
                :title="c.name" />
        <button @click="picker.visible = false"
                class="ml-1 text-gray-400 hover:text-gray-600 text-lg">✕</button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { saveAnnotation } from '../../api/client.js'

const props = defineProps({ topicId: String })

const colors = [
  { name: 'yellow', bg: 'bg-yellow-300' },
  { name: 'blue',   bg: 'bg-blue-300'   },
  { name: 'green',  bg: 'bg-green-300'  },
]

const wrapEl = ref(null)
const picker = reactive({ visible: false, x: 0, y: 0 })
let lastSelection = null

function onSelectionEnd(e) {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !sel.toString().trim()) return
  lastSelection = sel.toString().trim()
  const range = sel.getRangeAt(0)
  const rect = range.getBoundingClientRect()
  picker.x = Math.min(rect.left, window.innerWidth - 180)
  picker.y = rect.bottom + 8
  picker.visible = true
}

async function applyAnnotation(color) {
  if (!lastSelection || !props.topicId) return
  picker.visible = false
  await saveAnnotation(props.topicId, {
    selected_text: lastSelection,
    color,
  })
  window.getSelection()?.removeAllRanges()
  lastSelection = null
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
```

- [ ] **Step 2: Wrap TopicContent in AnnotationLayer inside ApuntsView.vue**

In `ApuntsView.vue`, replace the `<TopicContent>` tag:
```vue
<AnnotationLayer v-show="mode === 'text'" :topic-id="topics.activeTopicId">
  <TopicContent :content="topicData?.content" :headings="topicData?.headings || []" />
</AnnotationLayer>
```

Add the import at top of `<script setup>`:
```js
import AnnotationLayer from '../components/apunts/AnnotationLayer.vue'
```

- [ ] **Step 3: Verify in browser**

- Select text in a topic → yellow/blue/green buttons appear
- Clicking a color saves the annotation (check Network tab → POST /api/topics/.../annotations returns 201)
- Clicking ✕ dismisses without saving

- [ ] **Step 4: Commit**

```bash
git add src/components/apunts/AnnotationLayer.vue src/views/ApuntsView.vue
git commit -m "feat: text annotation layer — select text, pick color, save to backend"
```

---

## Task 6: Drawing Canvas (Fabric.js)

**Files:**
- Create: `src/components/apunts/DrawingCanvas.vue`

- [ ] **Step 1: Create src/components/apunts/DrawingCanvas.vue**

```vue
<template>
  <div class="relative w-full" :style="{ height: canvasHeight + 'px' }">
    <!-- Toolbar -->
    <div class="sticky top-0 z-10 flex items-center gap-2 px-4 py-2
                bg-[var(--color-surface)] border-b border-[var(--color-border)] flex-wrap">
      <!-- Tool buttons -->
      <button v-for="tool in tools" :key="tool.id"
              @click="setTool(tool.id)"
              :class="activeTool === tool.id ? 'ring-2 ring-primary' : ''"
              class="px-2 py-1 rounded text-sm bg-gray-100 dark:bg-gray-800 hover:bg-primary/20">
        {{ tool.label }}
      </button>
      <!-- Color picker -->
      <input type="color" v-model="strokeColor" class="w-8 h-8 rounded cursor-pointer border-0 p-0" />
      <!-- Stroke width -->
      <input type="range" min="1" max="20" v-model.number="strokeWidth" class="w-20" />
      <!-- Save + Clear -->
      <button @click="saveCanvas" class="ml-auto text-sm text-primary font-medium">Desar</button>
      <button @click="clearCanvas" class="text-sm text-red-500">Esborrar tot</button>
    </div>
    <!-- Canvas element -->
    <canvas ref="canvasEl" class="w-full touch-none" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { fabric } from 'fabric'
import { fetchDrawing, saveDrawing } from '../../api/client.js'

const props = defineProps({ topicId: String })

const canvasEl = ref(null)
const canvasHeight = ref(window.innerHeight - 160)
let fc = null   // Fabric.Canvas instance

const tools = [
  { id: 'pen',    label: '✏️ Ploma' },
  { id: 'circle', label: '⭕ Cercle' },
  { id: 'arrow',  label: '↗ Fletxa' },
  { id: 'eraser', label: '🧹 Goma'  },
]
const activeTool = ref('pen')
const strokeColor = ref('#e63946')
const strokeWidth = ref(3)

function setTool(toolId) {
  activeTool.value = toolId
  if (!fc) return
  if (toolId === 'pen') {
    fc.isDrawingMode = true
    fc.freeDrawingBrush.color = strokeColor.value
    fc.freeDrawingBrush.width = strokeWidth.value
  } else if (toolId === 'eraser') {
    fc.isDrawingMode = true
    fc.freeDrawingBrush.color = '#ffffff'
    fc.freeDrawingBrush.width = strokeWidth.value * 4
  } else {
    fc.isDrawingMode = false
  }
}

function initCanvas() {
  if (!canvasEl.value) return
  fc = new fabric.Canvas(canvasEl.value, {
    width: canvasEl.value.parentElement.clientWidth,
    height: canvasHeight.value,
    backgroundColor: 'transparent',
  })
  fc.isDrawingMode = true
  fc.freeDrawingBrush.color = strokeColor.value
  fc.freeDrawingBrush.width = strokeWidth.value

  // Click handlers for shape tools
  fc.on('mouse:down', onMouseDown)
  fc.on('mouse:up', onMouseUp)
  fc.on('mouse:move', onMouseMove)
}

let drawing = false
let startPoint = null
let activeShape = null

function onMouseDown(opt) {
  if (fc.isDrawingMode) return
  drawing = true
  startPoint = fc.getPointer(opt.e)
}

function onMouseMove(opt) {
  if (!drawing || fc.isDrawingMode) return
  const ptr = fc.getPointer(opt.e)
  if (activeShape) fc.remove(activeShape)
  if (activeTool.value === 'circle') {
    const rx = Math.abs(ptr.x - startPoint.x) / 2
    const ry = Math.abs(ptr.y - startPoint.y) / 2
    activeShape = new fabric.Ellipse({
      left: Math.min(ptr.x, startPoint.x), top: Math.min(ptr.y, startPoint.y),
      rx, ry, fill: 'transparent',
      stroke: strokeColor.value, strokeWidth: strokeWidth.value,
    })
  } else if (activeTool.value === 'arrow') {
    activeShape = new fabric.Line(
      [startPoint.x, startPoint.y, ptr.x, ptr.y],
      { stroke: strokeColor.value, strokeWidth: strokeWidth.value, selectable: true }
    )
  }
  if (activeShape) fc.add(activeShape)
  fc.renderAll()
}

function onMouseUp() {
  drawing = false
  activeShape = null
  startPoint = null
}

async function loadCanvas(topicId) {
  if (!fc || !topicId) return
  const data = await fetchDrawing(topicId)
  fc.clear()
  if (data?.canvas_json && data.canvas_json !== '{}') {
    fc.loadFromJSON(data.canvas_json, () => fc.renderAll())
  }
}

async function saveCanvas() {
  if (!fc || !props.topicId) return
  await saveDrawing(props.topicId, JSON.stringify(fc.toJSON()))
}

function clearCanvas() {
  if (!fc) return
  fc.clear()
  saveCanvas()
}

watch(strokeColor, c => {
  if (fc?.isDrawingMode) fc.freeDrawingBrush.color = c
})
watch(strokeWidth, w => {
  if (fc?.isDrawingMode) fc.freeDrawingBrush.width = w
})
watch(() => props.topicId, loadCanvas)

onMounted(async () => {
  initCanvas()
  await loadCanvas(props.topicId)
})

onUnmounted(() => {
  if (fc) { fc.dispose(); fc = null }
})
</script>
```

- [ ] **Step 2: Test in browser**

Switch to "🖊️ Dibuix" mode:
- Draw with the pen tool → freehand strokes appear
- Switch to circle tool → click-drag draws ellipses
- Switch to arrow → click-drag draws lines
- Goma (eraser) removes strokes
- "Desar" button saves to backend (check Network tab → POST 200)
- Reload page, switch to Dibuix → drawing reloads

- [ ] **Step 3: Commit**

```bash
git add src/components/apunts/DrawingCanvas.vue
git commit -m "feat: Fabric.js drawing canvas with pen, circle, arrow, eraser, save/load"
```

---

## Task 7: Flashcards Tab

**Files:**
- Create: `src/components/flashcards/FlipCard.vue`
- Create: `src/components/flashcards/LeitnerDeck.vue`
- Modify: `src/views/FlashcardsView.vue`
- Test: `tests/unit/FlipCard.test.js`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/FlipCard.test.js`:
```js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import FlipCard from '../../src/components/flashcards/FlipCard.vue'

describe('FlipCard', () => {
  const card = { pregunta: 'Que és el Ple?', resposta: "L'òrgan de govern", exemple: 'Aprova el pressupost' }

  it('shows front (pregunta) initially', () => {
    const w = mount(FlipCard, { props: { card } })
    expect(w.text()).toContain('Que és el Ple?')
    expect(w.text()).not.toContain("L'òrgan de govern")
  })

  it('shows back (resposta) after click', async () => {
    const w = mount(FlipCard, { props: { card } })
    await w.trigger('click')
    expect(w.text()).toContain("L'òrgan de govern")
  })

  it('resets to front when card prop changes', async () => {
    const w = mount(FlipCard, { props: { card } })
    await w.trigger('click')   // flip to back
    await w.setProps({ card: { pregunta: 'Nova pregunta', resposta: 'Nova resposta', exemple: '' } })
    expect(w.text()).toContain('Nova pregunta')
    expect(w.text()).not.toContain('Nova resposta')
  })
})
```

- [ ] **Step 2: Run test — expect failure**

```bash
npm run test -- tests/unit/FlipCard.test.js
```
Expected: `Cannot find module '../../src/components/flashcards/FlipCard.vue'`

- [ ] **Step 3: Create src/components/flashcards/FlipCard.vue**

```vue
<template>
  <div class="perspective-1000 w-full max-w-sm mx-auto h-52 cursor-pointer"
       @click="flipped = !flipped">
    <div class="relative w-full h-full transition-transform duration-500"
         :class="{ 'rotate-y-180': flipped }"
         style="transform-style: preserve-3d;">
      <!-- Front -->
      <div class="absolute inset-0 rounded-2xl flex flex-col items-center justify-center
                  p-6 bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700"
           style="backface-visibility: hidden;">
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2">Concepte</p>
        <p class="text-center font-medium text-lg">{{ card.pregunta }}</p>
      </div>
      <!-- Back -->
      <div class="absolute inset-0 rounded-2xl flex flex-col items-center justify-center
                  p-6 bg-primary/5 dark:bg-primary/10 shadow-xl border border-primary/20"
           style="backface-visibility: hidden; transform: rotateY(180deg);">
        <p class="text-xs font-semibold uppercase text-primary/70 mb-2">Definició</p>
        <p class="text-center font-medium">{{ card.resposta }}</p>
        <p v-if="card.exemple" class="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center italic">
          {{ card.exemple }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ card: Object })
const flipped = ref(false)
watch(() => props.card, () => { flipped.value = false })
</script>

<style scoped>
.perspective-1000 { perspective: 1000px; }
.rotate-y-180 { transform: rotateY(180deg); }
</style>
```

- [ ] **Step 4: Run test — expect pass**

```bash
npm run test -- tests/unit/FlipCard.test.js
```
Expected: 3 tests pass.

- [ ] **Step 5: Create src/components/flashcards/LeitnerDeck.vue**

```vue
<template>
  <div class="px-4 py-6 flex flex-col items-center gap-6">
    <!-- No cards state -->
    <div v-if="!dueCards.length" class="text-center py-12">
      <p class="text-4xl mb-3">🎉</p>
      <p class="font-semibold text-lg">Cap targeta per avui!</p>
      <p class="text-gray-500 text-sm mt-1">Torna demà o genera noves targetes.</p>
      <button @click="$emit('generate')"
              class="mt-4 px-5 py-2 bg-primary text-white rounded-xl text-sm font-medium">
        Generar targetes amb IA
      </button>
    </div>

    <!-- Card review -->
    <template v-else>
      <div class="w-full text-center text-sm text-gray-400 mb-1">
        {{ current + 1 }} / {{ dueCards.length }} — Caixa {{ dueCards[current].leitner_box }}
      </div>
      <FlipCard :card="dueCards[current]" />
      <div class="flex gap-4 mt-4 w-full max-w-sm">
        <button @click="review(false)"
                class="flex-1 py-3 rounded-2xl bg-red-100 dark:bg-red-900/30
                       text-red-600 dark:text-red-400 font-semibold text-sm hover:bg-red-200">
          ✗ No sabia
        </button>
        <button @click="review(true)"
                class="flex-1 py-3 rounded-2xl bg-green-100 dark:bg-green-900/30
                       text-green-600 dark:text-green-400 font-semibold text-sm hover:bg-green-200">
          ✓ Sabia
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FlipCard from './FlipCard.vue'
import { reviewFlashcard } from '../../api/client.js'

const props = defineProps({ cards: { type: Array, default: () => [] } })
const emit = defineEmits(['generate', 'reviewed'])

const today = new Date().toISOString().split('T')[0]
const dueCards = computed(() =>
  props.cards.filter(c => c.next_review <= today)
)
const current = ref(0)

async function review(knew) {
  const card = dueCards.value[current.value]
  await reviewFlashcard(card.id, knew)
  emit('reviewed', card.id)
  if (current.value < dueCards.value.length - 1) {
    current.value++
  }
}
</script>
```

- [ ] **Step 6: Update src/views/FlashcardsView.vue**

```vue
<template>
  <div>
    <!-- Topic selector strip -->
    <div class="overflow-x-auto flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button v-for="t in topics.topics" :key="t.id"
              @click="selectTopic(t.id)"
              :class="activeTopic === t.id ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap">
        T{{ t.number }}
      </button>
    </div>

    <!-- Action bar: generate + add manual -->
    <div class="flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button @click="generateCards"
              class="flex-1 py-2 bg-primary/10 text-primary rounded-xl text-sm font-medium hover:bg-primary/20">
        ✨ Generar amb IA
      </button>
      <button @click="showForm = !showForm"
              class="px-4 py-2 border border-[var(--color-border)] rounded-xl text-sm font-medium hover:border-primary">
        + Manual
      </button>
    </div>

    <!-- Manual creation form -->
    <div v-if="showForm" class="px-4 py-3 space-y-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <input v-model="newCard.pregunta" placeholder="Terme / Pregunta"
             class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] text-sm
                    bg-[var(--color-bg)] focus:outline-none focus:border-primary" />
      <input v-model="newCard.resposta" placeholder="Definició / Resposta"
             class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] text-sm
                    bg-[var(--color-bg)] focus:outline-none focus:border-primary" />
      <input v-model="newCard.exemple" placeholder="Exemple (opcional)"
             class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] text-sm
                    bg-[var(--color-bg)] focus:outline-none focus:border-primary" />
      <button @click="addCard" :disabled="!newCard.pregunta || !newCard.resposta"
              class="w-full py-2 bg-primary text-white rounded-xl text-sm font-semibold
                     disabled:opacity-50 disabled:cursor-not-allowed">
        Afegir targeta
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <span class="animate-spin text-2xl">⏳</span>
    </div>
    <LeitnerDeck v-else :cards="cards" @generate="generateCards" @reviewed="reload" />
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { fetchFlashcards, generateFlashcards, createFlashcard } from '../api/client.js'
import LeitnerDeck from '../components/flashcards/LeitnerDeck.vue'

const topics = useTopicsStore()
const activeTopic = ref(topics.activeTopicId)
const cards = ref([])
const loading = ref(false)
const showForm = ref(false)
const newCard = reactive({ pregunta: '', resposta: '', exemple: '' })

async function loadCards(id) {
  loading.value = true
  try { cards.value = await fetchFlashcards(id) }
  finally { loading.value = false }
}

async function generateCards() {
  loading.value = true
  try { cards.value = await generateFlashcards(activeTopic.value) }
  finally { loading.value = false }
}

async function addCard() {
  await createFlashcard(activeTopic.value, { ...newCard })
  newCard.pregunta = ''; newCard.resposta = ''; newCard.exemple = ''
  showForm.value = false
  await reload()
}

async function reload() {
  cards.value = await fetchFlashcards(activeTopic.value)
}

function selectTopic(id) { activeTopic.value = id }
watch(activeTopic, loadCards, { immediate: true })
</script>
```

- [ ] **Step 7: Run tests + browser verify**

```bash
npm run test -- tests/unit/FlipCard.test.js
```
Expected: 3 tests pass.

Browser: open Flash tab → select a topic → "Generar amb IA" → cards load → click card to flip → mark Sabia/No sabia → counter advances. Click "+ Manual" → form appears → fill pregunta/resposta → "Afegir targeta" → card appears in deck.

- [ ] **Step 8: Commit**

```bash
git add src/components/flashcards/ src/views/FlashcardsView.vue tests/unit/FlipCard.test.js
git commit -m "feat: Flashcards tab — flip animation, Leitner deck, Gemini generation, manual card creation"
```

---

## Task 8: Practice Tab — Test + Breus Modes

**Files:**
- Create: `src/components/practice/ModeSelector.vue`
- Create: `src/components/practice/TestMode.vue`
- Create: `src/components/practice/BreusMode.vue`
- Modify: `src/views/PracticaView.vue`
- Test: `tests/unit/TestMode.test.js`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/TestMode.test.js`:
```js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import TestMode from '../../src/components/practice/TestMode.vue'

const questions = [
  { pregunta: 'Que és el Ple?',
    opcions: { A: 'Òrgan executiu', B: 'Òrgan legislatiu', C: 'Tresoreria', D: 'Jutjat' },
    correcta: 'B', explicacio: 'El Ple és el màxim òrgan.' }
]

describe('TestMode', () => {
  it('renders the first question', () => {
    const w = mount(TestMode, { props: { questions, topicId: 'general_1' } })
    expect(w.text()).toContain('Que és el Ple?')
    expect(w.text()).toContain('Òrgan executiu')
  })

  it('shows 4 options', () => {
    const w = mount(TestMode, { props: { questions, topicId: 'general_1' } })
    const buttons = w.findAll('[data-option]')
    expect(buttons).toHaveLength(4)
  })

  it('marks correct answer green on selection', async () => {
    const w = mount(TestMode, { props: { questions, topicId: 'general_1' } })
    await w.find('[data-option="B"]').trigger('click')
    expect(w.find('[data-option="B"]').classes()).toContain('bg-green-100')
  })

  it('marks wrong answer red on selection', async () => {
    const w = mount(TestMode, { props: { questions, topicId: 'general_1' } })
    await w.find('[data-option="A"]').trigger('click')
    expect(w.find('[data-option="A"]').classes()).toContain('bg-red-100')
  })
})
```

- [ ] **Step 2: Run test — expect failure**

```bash
npm run test -- tests/unit/TestMode.test.js
```
Expected: `Cannot find module '../../src/components/practice/TestMode.vue'`

- [ ] **Step 3: Create src/components/practice/ModeSelector.vue**

```vue
<template>
  <div class="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3">
    <button v-for="m in modes" :key="m.id"
            @click="$emit('select', m.id)"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl
                   bg-[var(--color-surface)] border border-[var(--color-border)]
                   hover:border-primary hover:bg-primary/5 transition-colors">
      <span class="text-3xl">{{ m.icon }}</span>
      <span class="text-sm font-semibold">{{ m.label }}</span>
      <span class="text-xs text-gray-400 text-center">{{ m.desc }}</span>
    </button>
  </div>
</template>

<script setup>
defineEmits(['select'])
const modes = [
  { id: 'test',     icon: '☑️', label: 'Test',         desc: '10 preguntes, 4 opcions' },
  { id: 'breus',    icon: '✍️', label: 'Breus',        desc: '5 preguntes curtes' },
  { id: 'suposit',  icon: '🏛️', label: 'Supòsit',      desc: 'Cas pràctic real' },
  { id: 'connecta', icon: '🔗', label: 'Connecta',     desc: 'Relaciona conceptes' },
  { id: 'buits',    icon: '📝', label: 'Omple buits',  desc: 'Completa les frases' },
]
</script>
```

- [ ] **Step 4: Create src/components/practice/TestMode.vue**

```vue
<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <!-- Score summary (after finish) -->
    <div v-if="finished" class="text-center py-6">
      <p class="text-5xl mb-3">{{ scoreEmoji }}</p>
      <p class="text-3xl font-bold text-primary">{{ score }}/10</p>
      <p class="text-gray-500 mt-1">{{ correctCount }} de {{ questions.length }} correctes</p>
      <button @click="$emit('done', score)" class="mt-6 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>

    <!-- Question -->
    <template v-else>
      <div class="mb-3 flex items-center justify-between text-sm text-gray-400">
        <span>Pregunta {{ current + 1 }} de {{ questions.length }}</span>
        <span class="font-semibold text-primary">{{ correctCount }} ✓</span>
      </div>
      <p class="text-base font-semibold mb-5 leading-snug">
        {{ questions[current].pregunta }}
      </p>
      <div class="space-y-3">
        <button v-for="(text, key) in questions[current].opcions" :key="key"
                :data-option="key"
                @click="answer(key)"
                :disabled="answered"
                :class="optionClass(key)"
                class="w-full text-left px-4 py-3 rounded-2xl border text-sm
                       transition-colors disabled:cursor-default font-medium">
          <span class="font-bold mr-2">{{ key }}.</span>{{ text }}
        </button>
      </div>
      <!-- Explanation -->
      <div v-if="answered" class="mt-4 p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-sm">
        {{ questions[current].explicacio }}
      </div>
      <button v-if="answered" @click="next"
              class="w-full mt-4 py-3 bg-primary text-white rounded-2xl font-semibold">
        {{ current < questions.length - 1 ? 'Següent' : 'Veure resultat' }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ questions: Array, topicId: String })
const emit = defineEmits(['done'])

const current = ref(0)
const answered = ref(false)
const selected = ref(null)
const results = ref([])
const finished = ref(false)

const correctCount = computed(() => results.value.filter(r => r).length)
const score = computed(() => parseFloat((correctCount.value / props.questions.length * 10).toFixed(1)))
const scoreEmoji = computed(() => score.value >= 7 ? '🎉' : score.value >= 5 ? '👍' : '📚')

function answer(key) {
  if (answered.value) return
  selected.value = key
  answered.value = true
  results.value.push(key === props.questions[current.value].correcta)
}

function optionClass(key) {
  if (!answered.value) return 'border-[var(--color-border)] hover:border-primary hover:bg-primary/5'
  const isCorrect = key === props.questions[current.value].correcta
  const isSelected = key === selected.value
  if (isCorrect) return 'border-green-400 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
  if (isSelected && !isCorrect) return 'border-red-400 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
  return 'border-[var(--color-border)] opacity-50'
}

function next() {
  if (current.value < props.questions.length - 1) {
    current.value++
    answered.value = false
    selected.value = null
  } else {
    finished.value = true
  }
}
</script>
```

- [ ] **Step 5: Run test — expect pass**

```bash
npm run test -- tests/unit/TestMode.test.js
```
Expected: 4 tests pass.

- [ ] **Step 6: Create src/components/practice/BreusMode.vue**

```vue
<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <!-- Results view -->
    <div v-if="evaluated.length">
      <h2 class="font-bold text-lg mb-4">Resultats</h2>
      <div v-for="(r, i) in evaluated" :key="i"
           class="mb-4 p-4 rounded-2xl border border-[var(--color-border)]">
        <p class="font-semibold text-sm mb-1">{{ r.pregunta }}</p>
        <p class="text-xs text-gray-500 mb-2">La teva resposta: {{ r.resposta }}</p>
        <div class="flex items-center gap-2">
          <span :class="r.eval.puntuacio >= 7 ? 'text-green-600' : r.eval.puntuacio >= 5 ? 'text-yellow-600' : 'text-red-600'"
                class="font-bold text-lg">{{ r.eval.puntuacio }}/10</span>
          <span class="text-xs text-gray-500 flex-1">{{ r.eval.feedback }}</span>
        </div>
      </div>
      <p class="text-center font-bold text-xl mt-4 text-primary">
        Mitjana: {{ avgScore }}/10
      </p>
      <button @click="$emit('done', parseFloat(avgScore))"
              class="w-full mt-4 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>

    <!-- Question form -->
    <div v-else>
      <div v-if="loading" class="text-center py-12 text-gray-400 animate-pulse">
        L'IA avalua les respostes…
      </div>
      <template v-else>
        <div class="mb-3 text-sm text-gray-400">Pregunta {{ current + 1 }} de {{ questions.length }}</div>
        <p class="font-semibold mb-3">{{ questions[current].pregunta }}</p>
        <textarea v-model="answers[current]" rows="5"
                  placeholder="Escriu la teva resposta aquí..."
                  class="w-full rounded-2xl border border-[var(--color-border)] p-3 text-sm
                         bg-[var(--color-surface)] resize-none focus:outline-none focus:border-primary" />
        <div class="flex gap-3 mt-3">
          <button v-if="current > 0" @click="current--"
                  class="px-4 py-2 rounded-xl border border-[var(--color-border)] text-sm">
            ← Anterior
          </button>
          <button v-if="current < questions.length - 1" @click="current++"
                  class="flex-1 px-4 py-3 bg-primary/10 text-primary rounded-2xl text-sm font-medium">
            Següent →
          </button>
          <button v-else @click="submitAll"
                  class="flex-1 px-4 py-3 bg-primary text-white rounded-2xl text-sm font-semibold">
            Avaluar amb IA
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { evaluateAnswer } from '../../api/client.js'

const props = defineProps({ questions: Array, topicId: String })
const emit = defineEmits(['done'])

const current = ref(0)
const answers = ref(props.questions.map(() => ''))
const evaluated = ref([])
const loading = ref(false)

const avgScore = computed(() => {
  if (!evaluated.value.length) return 0
  const sum = evaluated.value.reduce((a, r) => a + r.eval.puntuacio, 0)
  return (sum / evaluated.value.length).toFixed(1)
})

async function submitAll() {
  loading.value = true
  try {
    const evals = await Promise.all(
      props.questions.map((q, i) =>
        evaluateAnswer({
          topic_id: props.topicId,
          mode: 'breus',
          pregunta: q.pregunta,
          resposta_usuari: answers.value[i] || '(sense resposta)',
          resposta_model: q.resposta_model || '',
        })
      )
    )
    evaluated.value = props.questions.map((q, i) => ({
      pregunta: q.pregunta,
      resposta: answers.value[i],
      eval: evals[i],
    }))
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 7: Update src/views/PracticaView.vue**

```vue
<template>
  <div>
    <!-- Topic selector strip -->
    <div class="overflow-x-auto flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button v-for="t in topics.topics" :key="t.id"
              @click="activeTopic = t.id"
              :class="activeTopic === t.id ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap">
        T{{ t.number }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <span class="animate-spin text-3xl">⏳</span>
    </div>

    <!-- Mode selector -->
    <ModeSelector v-else-if="!activeMode" @select="startMode" />

    <!-- Exercise components -->
    <TestMode v-else-if="activeMode === 'test' && questions.length"
              :questions="questions" :topic-id="activeTopic"
              @done="finishSession" />
    <BreusMode v-else-if="activeMode === 'breus' && questions.length"
               :questions="questions" :topic-id="activeTopic"
               @done="finishSession" />
    <SupositMode v-else-if="activeMode === 'suposit' && suposit"
                 :suposit="suposit" :topic-id="activeTopic"
                 @done="finishSession" />
    <ConnectaMode v-else-if="activeMode === 'connecta' && questions.length"
                  :pairs="questions" :topic-id="activeTopic"
                  @done="finishSession" />
    <BuitsMode v-else-if="activeMode === 'buits' && questions.length"
               :sentences="questions" :topic-id="activeTopic"
               @done="finishSession" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { generatePractice, saveSession } from '../api/client.js'
import ModeSelector from '../components/practice/ModeSelector.vue'
import TestMode from '../components/practice/TestMode.vue'
import BreusMode from '../components/practice/BreusMode.vue'
import SupositMode from '../components/practice/SupositMode.vue'
import ConnectaMode from '../components/practice/ConnectaMode.vue'
import BuitsMode from '../components/practice/BuitsMode.vue'

const topics = useTopicsStore()
const activeTopic = ref(topics.activeTopicId)
const activeMode = ref(null)
const questions = ref([])
const suposit = ref(null)
const loading = ref(false)

async function startMode(mode) {
  activeMode.value = mode
  loading.value = true
  try {
    const data = await generatePractice(activeTopic.value, mode)
    if (mode === 'suposit') { suposit.value = data }
    else { questions.value = data }
  } finally { loading.value = false }
}

async function finishSession(score) {
  await saveSession({
    topic_id: activeTopic.value,
    mode: activeMode.value,
    score,
    questions_json: JSON.stringify(questions.value),
    answers_json: '[]',
    feedback_json: '{}',
  })
  topics.updateTopicProgress(activeTopic.value, score * 10)
  activeMode.value = null
  questions.value = []
  suposit.value = null
}

watch(activeTopic, () => {
  activeMode.value = null
  questions.value = []
})
</script>
```

- [ ] **Step 8: Run tests + browser verify**

```bash
npm run test -- tests/unit/TestMode.test.js
```
Expected: 4 tests pass.

Browser: Pràctica tab → select a topic → choose "Test" → questions load → answer → see feedback → finish → score saved.

- [ ] **Step 9: Commit**

```bash
git add src/components/practice/ src/views/PracticaView.vue tests/unit/TestMode.test.js
git commit -m "feat: Practice tab with ModeSelector, TestMode, BreusMode; session save and progress update"
```

---

## Task 9: Practice — Supòsit, Connecta, Buits Modes

**Files:**
- Create: `src/components/practice/SupositMode.vue`
- Create: `src/components/practice/ConnectaMode.vue`
- Create: `src/components/practice/BuitsMode.vue`
- Test: `tests/unit/BuitsMode.test.js`, `tests/unit/ConnectaMode.test.js`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/BuitsMode.test.js`:
```js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import BuitsMode from '../../src/components/practice/BuitsMode.vue'

const sentences = [
  { frase: 'El ___ és responsable de l\'administració', paraules: ['Alcalde'], posicions: [1] },
  { frase: 'La ___ aprova els pressupostos', paraules: ['Ple'], posicions: [1] },
]

describe('BuitsMode', () => {
  it('renders input fields for blanks', () => {
    const w = mount(BuitsMode, { props: { sentences, topicId: 'general_1' } })
    expect(w.findAll('input[type="text"]').length).toBe(2)
  })

  it('marks correct answer on check', async () => {
    const w = mount(BuitsMode, { props: { sentences, topicId: 'general_1' } })
    const inputs = w.findAll('input[type="text"]')
    await inputs[0].setValue('Alcalde')
    await w.find('[data-check]').trigger('click')
    expect(w.find('[data-result-0]').classes()).toContain('text-green-600')
  })

  it('marks wrong answer on check', async () => {
    const w = mount(BuitsMode, { props: { sentences, topicId: 'general_1' } })
    const inputs = w.findAll('input[type="text"]')
    await inputs[0].setValue('Wrong')
    await w.find('[data-check]').trigger('click')
    expect(w.find('[data-result-0]').classes()).toContain('text-red-600')
  })
})
```

Create `tests/unit/ConnectaMode.test.js`:
```js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import ConnectaMode from '../../src/components/practice/ConnectaMode.vue'

const pairs = [
  { terme: 'Alcalde', definicio: 'Cap del govern municipal' },
  { terme: 'Ple', definicio: 'Màxim òrgan de govern' },
]

describe('ConnectaMode', () => {
  it('renders all terms', () => {
    const w = mount(ConnectaMode, { props: { pairs, topicId: 'general_1' } })
    expect(w.text()).toContain('Alcalde')
    expect(w.text()).toContain('Ple')
  })

  it('renders all definitions', () => {
    const w = mount(ConnectaMode, { props: { pairs, topicId: 'general_1' } })
    expect(w.text()).toContain('Cap del govern municipal')
  })
})
```

- [ ] **Step 2: Run tests — expect failure**

```bash
npm run test -- tests/unit/BuitsMode.test.js tests/unit/ConnectaMode.test.js
```
Expected: `Cannot find module` errors.

- [ ] **Step 3: Create src/components/practice/SupositMode.vue**

```vue
<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <!-- Evaluation result -->
    <div v-if="evalResult" class="space-y-4">
      <div class="p-4 rounded-2xl border border-[var(--color-border)]">
        <p class="text-xs text-gray-400 mb-1">Puntuació</p>
        <p class="text-3xl font-bold"
           :class="evalResult.puntuacio >= 7 ? 'text-green-600' : 'text-yellow-600'">
          {{ evalResult.puntuacio }}/10
        </p>
      </div>
      <div class="p-4 rounded-2xl bg-green-50 dark:bg-green-900/20 text-sm">
        <p class="font-semibold mb-1 text-green-700 dark:text-green-400">Encerts</p>
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(e, i) in evalResult.encerts" :key="i">{{ e }}</li>
        </ul>
      </div>
      <div v-if="evalResult.mancances.length" class="p-4 rounded-2xl bg-red-50 dark:bg-red-900/20 text-sm">
        <p class="font-semibold mb-1 text-red-700 dark:text-red-400">Mancances</p>
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(m, i) in evalResult.mancances" :key="i">{{ m }}</li>
        </ul>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-300">{{ evalResult.feedback }}</p>
      <button @click="$emit('done', evalResult.puntuacio)"
              class="w-full py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>

    <!-- Exercise form -->
    <div v-else>
      <div v-if="loading" class="text-center py-12 text-gray-400 animate-pulse">L'IA avalua…</div>
      <template v-else>
        <div class="p-4 rounded-2xl bg-blue-50 dark:bg-blue-900/20 mb-4">
          <p class="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2">Supòsit pràctic</p>
          <p class="text-sm font-medium">{{ suposit.enunciat }}</p>
          <p v-if="suposit.context" class="text-xs text-gray-500 mt-2 italic">
            Context: {{ suposit.context }}
          </p>
          <p class="text-xs text-gray-400 mt-2">Dificultat: {{ suposit.dificultat }}</p>
        </div>
        <p class="text-xs text-gray-400 mb-2">Escriu la teva resposta raonada:</p>
        <textarea v-model="resposta" rows="8"
                  placeholder="Desenvolupa la teva resposta..."
                  class="w-full rounded-2xl border border-[var(--color-border)] p-3 text-sm
                         bg-[var(--color-surface)] resize-none focus:outline-none focus:border-primary" />
        <button @click="submit" :disabled="!resposta.trim()"
                class="w-full mt-4 py-3 bg-primary text-white rounded-2xl font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed">
          Avaluar amb IA
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { evaluateAnswer } from '../../api/client.js'

const props = defineProps({ suposit: Object, topicId: String })
const emit = defineEmits(['done'])

const resposta = ref('')
const evalResult = ref(null)
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    evalResult.value = await evaluateAnswer({
      topic_id: props.topicId,
      mode: 'suposit',
      pregunta: props.suposit.enunciat,
      resposta_usuari: resposta.value,
      resposta_model: (props.suposit.punts_clau_resposta || []).join('; '),
    })
  } finally { loading.value = false }
}
</script>
```

- [ ] **Step 4: Create src/components/practice/ConnectaMode.vue**

```vue
<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <div v-if="finished" class="text-center py-8">
      <p class="text-5xl mb-3">{{ score === total ? '🎉' : '💪' }}</p>
      <p class="text-2xl font-bold text-primary">{{ score }}/{{ total }} correctes</p>
      <button @click="$emit('done', score / total * 10)"
              class="mt-6 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
    <div v-else class="grid grid-cols-2 gap-3">
      <!-- Terms column -->
      <div class="space-y-2">
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2 text-center">Termes</p>
        <button v-for="(t, i) in shuffledTermes" :key="'t'+i"
                @click="selectTerm(i)"
                :class="termClass(i)"
                class="w-full px-3 py-2 rounded-xl border text-sm font-medium text-left transition-colors">
          {{ t.terme }}
        </button>
      </div>
      <!-- Definitions column -->
      <div class="space-y-2">
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2 text-center">Definicions</p>
        <button v-for="(d, i) in shuffledDefs" :key="'d'+i"
                @click="selectDef(i)"
                :class="defClass(i)"
                class="w-full px-3 py-2 rounded-xl border text-xs text-left transition-colors">
          {{ d.definicio }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
const props = defineProps({ pairs: Array, topicId: String })
const emit = defineEmits(['done'])

const shuffledTermes = ref([])
const shuffledDefs = ref([])
const selectedTerm = ref(null)
const matched = ref({})  // termIndex → defIndex
const score = ref(0)
const total = computed(() => props.pairs.length)
const finished = computed(() => Object.keys(matched.value).length === total.value)

function shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5) }

onMounted(() => {
  shuffledTermes.value = shuffle(props.pairs)
  shuffledDefs.value = shuffle(props.pairs)
})

function selectTerm(i) {
  if (matched.value[i] !== undefined) return
  selectedTerm.value = i
}

function selectDef(defIdx) {
  if (selectedTerm.value === null) return
  const tIdx = selectedTerm.value
  // Check if the terme's correct definition matches the selected def
  const terme = shuffledTermes.value[tIdx]
  const def = shuffledDefs.value[defIdx]
  const isMatch = terme.terme === def.terme  // same original pair
  matched.value[tIdx] = { defIdx, correct: isMatch }
  if (isMatch) score.value++
  selectedTerm.value = null
}

function termClass(i) {
  if (i === selectedTerm.value) return 'border-primary bg-primary/10'
  const m = matched.value[i]
  if (m === undefined) return 'border-[var(--color-border)] hover:border-primary'
  return m.correct ? 'border-green-400 bg-green-100 dark:bg-green-900/20' : 'border-red-400 bg-red-100 dark:bg-red-900/20'
}

function defClass(defIdx) {
  const used = Object.values(matched.value).find(m => m.defIdx === defIdx)
  if (!used) return 'border-[var(--color-border)] hover:border-primary'
  return used.correct ? 'border-green-400 bg-green-100 dark:bg-green-900/20' : 'border-red-400 bg-red-100 dark:bg-red-900/20'
}
</script>
```

- [ ] **Step 5: Create src/components/practice/BuitsMode.vue**

```vue
<template>
  <div class="px-4 py-6 max-w-lg mx-auto space-y-4">
    <div v-for="(s, i) in sentences" :key="i"
         class="p-3 rounded-xl border border-[var(--color-border)] space-y-2">
      <!-- Input form (before check) -->
      <div v-if="!checked">
        <p class="text-sm text-gray-500">{{ s.frase.replace('___', '[   ]') }}</p>
        <input type="text" v-model="answers[i]"
               placeholder="Escriu aquí..."
               class="w-full mt-1 px-3 py-1.5 rounded-lg border border-[var(--color-border)]
                      text-sm bg-[var(--color-surface)] focus:outline-none focus:border-primary" />
      </div>
      <!-- Result (after check) -->
      <div v-else>
        <p class="text-sm" v-html="renderResult(s, answers[i])" />
        <span :data-result-0="i === 0 || undefined"
              :class="isCorrect(s, answers[i]) ? 'text-green-600' : 'text-red-600'"
              class="text-xs font-semibold mt-1 block">
          {{ isCorrect(s, answers[i]) ? '✓ Correcte' : `✗ Correcta: ${s.paraules[0]}` }}
        </span>
      </div>
    </div>

    <button v-if="!checked" data-check @click="checked = true"
            class="w-full py-3 bg-primary text-white rounded-2xl font-semibold">
      Comprovar
    </button>
    <div v-else class="text-center pt-2">
      <p class="font-bold text-xl text-primary">{{ correctCount }}/{{ sentences.length }} correctes</p>
      <button @click="$emit('done', correctCount / sentences.length * 10)"
              class="mt-4 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ sentences: Array, topicId: String })
const emit = defineEmits(['done'])

const answers = ref(props.sentences.map(() => ''))
const checked = ref(false)

const isCorrect = (s, answer) =>
  answer?.toLowerCase().trim() === s.paraules[0]?.toLowerCase()

const correctCount = computed(() =>
  props.sentences.filter((s, i) => isCorrect(s, answers.value[i])).length
)

function renderResult(s, answer) {
  const correct = s.paraules[0]
  const right = isCorrect(s, answer)
  const colored = right
    ? `<strong class="text-green-600">${answer}</strong>`
    : `<strong class="text-red-600">${answer || '(buit)'}</strong> <span class="text-gray-400">(${correct})</span>`
  return s.frase.replace('___', colored)
}
</script>
```

- [ ] **Step 6: Run tests — expect pass**

```bash
npm run test -- tests/unit/BuitsMode.test.js tests/unit/ConnectaMode.test.js
```

Expected: 5 tests pass total. The `data-result-0` attribute renders on the `<span>` inside the `v-else` (results) branch, which is active once `checked` is true after clicking `[data-check]`.

- [ ] **Step 7: Commit**

```bash
git add src/components/practice/SupositMode.vue src/components/practice/ConnectaMode.vue \
        src/components/practice/BuitsMode.vue tests/unit/BuitsMode.test.js tests/unit/ConnectaMode.test.js
git commit -m "feat: SupositMode (eval via Gemini), ConnectaMode (drag-match), BuitsMode (fill-in-blanks)"
```

---

## Task 10: Progrés Tab

**Files:**
- Create: `src/components/progres/ProgressBar.vue`
- Create: `src/components/progres/ExamReadiness.vue`
- Modify: `src/views/ProgresView.vue`

- [ ] **Step 1: Create src/components/progres/ProgressBar.vue**

```vue
<template>
  <div class="space-y-1">
    <div class="flex justify-between items-center text-sm">
      <span class="truncate font-medium" :title="label">{{ label }}</span>
      <span class="text-xs font-semibold ml-2 flex-shrink-0"
            :class="pct >= 80 ? 'text-green-600' : pct >= 40 ? 'text-yellow-600' : 'text-gray-400'">
        {{ Math.round(pct) }}%
      </span>
    </div>
    <div class="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
      <div class="h-full rounded-full transition-all duration-500"
           :class="pct >= 80 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-400' : 'bg-gray-300'"
           :style="{ width: pct + '%' }" />
    </div>
  </div>
</template>
<script setup>
defineProps({ label: String, pct: { type: Number, default: 0 } })
</script>
```

- [ ] **Step 2: Create src/components/progres/ExamReadiness.vue**

```vue
<template>
  <div class="p-4 rounded-2xl border border-[var(--color-border)] space-y-4">
    <div v-if="loading" class="text-center py-6 text-gray-400 animate-pulse">
      L'IA analitza el teu progrés…
    </div>
    <template v-else-if="data">
      <!-- Readiness headline -->
      <div class="text-center">
        <p class="text-xs uppercase text-gray-400 mb-1">Preparació estimada</p>
        <p class="text-4xl font-bold"
           :class="data.readiness_pct >= 70 ? 'text-green-600' : data.readiness_pct >= 50 ? 'text-yellow-600' : 'text-red-500'">
          {{ data.readiness_pct }}%
        </p>
        <p class="text-lg font-semibold mt-1">Nota estimada: {{ data.nota_estimada }}/10</p>
        <p class="text-sm text-primary font-medium mt-1">
          📅 Examen el {{ data.exam_date }} — resten {{ data.dies_restants }} dies
        </p>
      </div>
      <!-- Priority topics -->
      <div>
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2">Temes prioritaris</p>
        <div class="space-y-1">
          <div v-for="(t, i) in data.temes_prioritaris" :key="i"
               class="flex items-center gap-2 text-sm">
            <span class="text-primary font-bold">{{ i + 1 }}.</span>
            <span>{{ t }}</span>
          </div>
        </div>
      </div>
      <!-- Advice -->
      <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-sm">
        <p class="font-semibold text-blue-700 dark:text-blue-300 mb-1">Consell</p>
        <p class="text-gray-700 dark:text-gray-300">{{ data.consell_estudi }}</p>
      </div>
    </template>
    <div v-else class="text-center py-4">
      <button @click="load"
              class="px-5 py-2.5 bg-primary text-white rounded-xl text-sm font-medium">
        Analitzar amb IA
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { fetchExamReadiness } from '../../api/client.js'
const loading = ref(false)
const data = ref(null)
async function load() {
  loading.value = true
  try { data.value = await fetchExamReadiness() }
  finally { loading.value = false }
}
</script>
```

- [ ] **Step 3: Update src/views/ProgresView.vue**

```vue
<template>
  <div class="px-4 py-6 space-y-6 pb-20">
    <div v-if="loading" class="text-center py-12 text-gray-400 animate-pulse">Carregant progrés…</div>
    <template v-else-if="progress">
      <!-- Global % -->
      <div class="text-center">
        <p class="text-xs uppercase text-gray-400 mb-1">Progrés global</p>
        <p class="text-5xl font-bold text-primary">{{ progress.overall_pct }}%</p>
      </div>

      <!-- Bloc bars -->
      <div class="space-y-3">
        <ProgressBar label="Bloc General" :pct="progress.general_pct" />
        <ProgressBar label="Bloc Específic" :pct="progress.especific_pct" />
      </div>

      <!-- Per-topic breakdown -->
      <div>
        <p class="font-semibold text-sm uppercase text-gray-400 mb-3">Per tema</p>
        <div class="space-y-2">
          <ProgressBar v-for="t in progress.topics" :key="t.topic_id"
                       :label="`T${t.topic_id.split('_')[1]} ${t.title || ''}`"
                       :pct="t.overall_pct" />
        </div>
      </div>

      <!-- Exam readiness (Gemini) -->
      <ExamReadiness />

      <!-- History -->
      <div v-if="progress.history.length">
        <p class="font-semibold text-sm uppercase text-gray-400 mb-3">Últimes sessions</p>
        <div class="space-y-2">
          <div v-for="(h, i) in progress.history" :key="i"
               class="flex items-center justify-between text-sm p-3
                      rounded-xl border border-[var(--color-border)]">
            <span class="truncate text-gray-600 dark:text-gray-400">
              {{ h.topic_id }} · {{ h.mode }}
            </span>
            <span class="font-bold text-primary ml-2">{{ h.score }}/10</span>
          </div>
        </div>
      </div>

      <!-- PDF analysis trigger -->
      <button @click="runPdf" :disabled="pdfLoading"
              class="w-full py-3 border border-[var(--color-border)] rounded-2xl text-sm
                     font-medium text-gray-600 dark:text-gray-400 hover:border-primary
                     hover:text-primary disabled:opacity-50">
        {{ pdfLoading ? 'Analitzant temari…' : '🔍 Analitzar cobertura del temari oficial' }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchProgress, runPdfAnalysis } from '../api/client.js'
import ProgressBar from '../components/progres/ProgressBar.vue'
import ExamReadiness from '../components/progres/ExamReadiness.vue'

const progress = ref(null)
const loading = ref(false)
const pdfLoading = ref(false)

async function load() {
  loading.value = true
  try { progress.value = await fetchProgress() }
  finally { loading.value = false }
}

async function runPdf() {
  pdfLoading.value = true
  try { await runPdfAnalysis() }
  finally { pdfLoading.value = false }
}

onMounted(load)
</script>
```

- [ ] **Step 4: Verify in browser**

Open Progrés tab:
- Global % bar shows
- Per-topic bars show (all 0% if no sessions done)
- "Analitzar amb IA" button calls Gemini and shows readiness report
- "Analitzar cobertura" calls PDF analysis endpoint

- [ ] **Step 5: Commit**

```bash
git add src/components/progres/ src/views/ProgresView.vue
git commit -m "feat: Progrés tab with progress bars, exam readiness (Gemini), history, PDF analysis trigger"
```

---

## Task 11: Build + Dockerfile

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `frontend/.dockerignore`

- [ ] **Step 1: Run full test suite**

```bash
npm run test
```
Expected: all unit tests pass (FlipCard, TestMode, BuitsMode, ConnectaMode, stores).

- [ ] **Step 2: Verify production build**

```bash
npm run build
```
Expected: `dist/` contains `index.html` + `assets/`. No build errors.

- [ ] **Step 3: Create frontend/nginx.conf**

```nginx
server {
    listen 80;
    server_name _;

    # Proxy /api/* to FastAPI backend (docker-compose service name: "backend")
    location /api/ {
        proxy_pass         http://backend:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # SPA fallback: all other routes serve index.html
    location / {
        root   /usr/share/nginx/html;
        index  index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 4: Create frontend/Dockerfile**

```dockerfile
# Stage 1: build Vue app
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 5: Create frontend/.dockerignore**

```
node_modules/
dist/
.env
*.local
```

- [ ] **Step 6: Verify docker build succeeds**

From the `frontend/` directory:
```bash
docker build -t opos-frontend .
```
Expected: `Successfully built ...` — two stages complete without errors.

- [ ] **Step 7: Final commit**

```bash
git add Dockerfile nginx.conf .dockerignore
git commit -m "feat: multi-stage Dockerfile (Node build + nginx serve) with API proxy config"
```
