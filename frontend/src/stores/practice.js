import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import { generatePractice } from '../api/client.js'

const STORAGE_KEY = 'opos_practice_v1'

function saveToStorage(cache, progress) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      cache: { ...cache },
      progress: { ...progress },
    }))
  } catch {}
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { cache: {}, progress: {} }
    return JSON.parse(raw)
  } catch {}
  return { cache: {}, progress: {} }
}

export const usePracticeStore = defineStore('practice', () => {
  const stored = loadFromStorage()

  // Generated content: `${topicId}__${mode}` → questions[] | suposit{}
  const cache = reactive({ ...stored.cache })
  // Currently generating: key → true
  const generating = reactive({})
  // Error messages: key → string
  const errors = reactive({})
  // Ready but not yet opened: key → true
  const ready = reactive({})
  // Per-topic mode progress badges: topicId → { mode → progressObj }
  const progress = reactive({ ...stored.progress })

  // On load: mark cached items as ready only if no in-progress state saved
  for (const k of Object.keys(stored.cache || {})) {
    const [topicId, mode] = k.split('__')
    if (!stored.progress?.[topicId]?.[mode]) {
      ready[k] = true
    }
  }

  const anyGenerating = computed(() => Object.keys(generating).length > 0)
  const anyReady = computed(() => Object.keys(ready).length > 0)

  const key = (topicId, mode) => `${topicId}__${mode}`

  function getContent(topicId, mode) {
    return cache[key(topicId, mode)] ?? null
  }

  function isGenerating(topicId, mode) {
    return !!generating[key(topicId, mode)]
  }

  function isReady(topicId, mode) {
    return !!ready[key(topicId, mode)]
  }

  function getError(topicId, mode) {
    return errors[key(topicId, mode)] ?? null
  }

  function markSeen(topicId, mode) {
    delete ready[key(topicId, mode)]
  }

  function clearError(topicId, mode) {
    delete errors[key(topicId, mode)]
  }

  function clearContent(topicId, mode) {
    const k = key(topicId, mode)
    delete cache[k]
    delete ready[k]
    delete errors[k]
    saveToStorage(cache, progress)
  }

  function getProgress(topicId) {
    return progress[topicId] ?? {}
  }

  function setProgress(topicId, mode, progressObj) {
    progress[topicId] = { ...(progress[topicId] || {}), [mode]: progressObj }
    saveToStorage(cache, progress)
  }

  function clearProgress(topicId, mode) {
    if (!progress[topicId]) return
    const p = { ...progress[topicId] }
    delete p[mode]
    progress[topicId] = p
    saveToStorage(cache, progress)
  }

  async function requestNotifications() {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  function sendNotification(mode) {
    const names = {
      test: 'Test', breus: 'Preguntes breus',
      suposit: 'Supòsit pràctic', connecta: 'Connecta', buits: 'Omple buits',
    }
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('OPOS Estudi — Pràctica llesta', {
        body: `${names[mode] || mode} generat. Torna a Pràctica per comenzar!`,
        icon: '/favicon.ico',
      })
    }
  }

  async function generate(topicId, mode) {
    const k = key(topicId, mode)
    if (cache[k] || generating[k]) return
    generating[k] = true
    delete errors[k]
    try {
      const data = await generatePractice(topicId, mode)
      cache[k] = data
      ready[k] = true
      saveToStorage(cache, progress)
      sendNotification(mode)
    } catch (e) {
      errors[k] = e.response?.data?.detail || 'Error generant la pràctica. Torna a intentar-ho.'
    } finally {
      delete generating[k]
    }
  }

  return {
    anyGenerating, anyReady,
    getContent, isGenerating, isReady, getError,
    markSeen, clearError, clearContent,
    getProgress, setProgress, clearProgress,
    requestNotifications, generate,
  }
})
