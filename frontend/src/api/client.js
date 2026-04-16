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
export const resetProgress = async () => api.delete('/progress')
export const fetchAIModels = async () => (await api.get('/ai/models')).data
export const fetchAIStatus = async () => (await api.get('/ai/status')).data
export const setAIModel = async (model) => (await api.post('/ai/model', { model })).data
