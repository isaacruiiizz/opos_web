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
