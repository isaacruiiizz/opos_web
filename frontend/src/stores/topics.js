import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchTopics } from '../api/client.js'

export const useTopicsStore = defineStore('topics', () => {
  const topics = ref([])
  const activeTopicId = ref('general_1')

  const generalTopics = computed(() => topics.value.filter(t => t.bloc === 'general'))
  const especificTopics = computed(() => topics.value.filter(t => t.bloc === 'especific'))
  const importantsTopics = computed(() => topics.value.filter(t => t.bloc === 'importants'))
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

  return { topics, activeTopicId, activeTopic, generalTopics, especificTopics, importantsTopics,
           loadTopics, setActiveTopic, updateTopicProgress }
})
