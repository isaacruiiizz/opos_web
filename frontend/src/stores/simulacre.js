import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generateSimulacre, evaluateSimulacre, saveSimulacre, fetchLastSimulacre, fetchRoundState } from '../api/client.js'

const STORAGE_KEY = 'opos_simulacre_v1'
const RESULTS_KEY = 'opos_simulacre_results_v1'

function loadSavedResults() {
  try {
    const raw = localStorage.getItem(RESULTS_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function saveResults(data) {
  try { localStorage.setItem(RESULTS_KEY, JSON.stringify(data)) } catch {}
}

function clearSavedResults() {
  try { localStorage.removeItem(RESULTS_KEY) } catch {}
}

function loadDraft() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function saveDraft(data) {
  try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data)) } catch {}
}

function clearDraft() {
  try { sessionStorage.removeItem(STORAGE_KEY) } catch {}
}

export const useSimulacreStore = defineStore('simulacre', () => {
  const questions = ref([])
  const answers = ref({})        // { questionId: { value, correct, points_earned } }
  const timeRemaining = ref(7200) // 2h en segons
  const generating = ref(false)
  const evaluating = ref(false)
  const error = ref(null)
  const results = ref(loadSavedResults())  // resultat final un cop avaluat
  const lastResult = ref(null)   // últim resultat desat a BD
  const phase = ref('idle')      // 'idle' | 'exam' | 'evaluating' | 'results'
  const topicsUsed = ref([])       // temes usats a la generació actual
  const roundState = ref(null)     // { round, pending, total, covered }

  const totalQuestions = computed(() => questions.value.length)
  const answeredCount = computed(() => Object.keys(answers.value).length)
  const testQuestions = computed(() => questions.value.filter(q => q.tipus === 'test'))
  const openQuestions = computed(() => questions.value.filter(q => q.tipus !== 'test'))

  async function loadLastResult() {
    try {
      lastResult.value = await fetchLastSimulacre()
    } catch {}
  }

  async function loadRoundState() {
    try {
      roundState.value = await fetchRoundState()
    } catch {}
  }

  async function startGeneration() {
    const draft = loadDraft()
    if (draft && draft.questions && draft.timeRemaining > 0) {
      questions.value = draft.questions
      answers.value = draft.answers || {}
      timeRemaining.value = draft.timeRemaining
      phase.value = 'exam'
      return
    }

    generating.value = true
    error.value = null
    try {
      const data = await generateSimulacre()
      questions.value = data.questions
      topicsUsed.value = data.topics_used || []
      answers.value = {}
      timeRemaining.value = 7200
      phase.value = 'exam'
      persistDraft()
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error generant el simulacre. Torna a intentar-ho.'
    } finally {
      generating.value = false
    }
  }

  function answerTest(questionId, optionKey) {
    const q = questions.value.find(q => q.id === questionId)
    if (!q || answers.value[questionId]) return
    const correct = optionKey === q.correcta
    const points_earned = correct ? q.punts : (q.penalitza ? -(q.punts / 3) : 0)
    answers.value = {
      ...answers.value,
      [questionId]: { value: optionKey, correct, points_earned }
    }
    persistDraft()
  }

  function answerOpen(questionId, text) {
    answers.value = {
      ...answers.value,
      [questionId]: { value: text, correct: null, points_earned: null }
    }
    persistDraft()
  }

  function persistDraft() {
    saveDraft({
      questions: questions.value,
      answers: answers.value,
      timeRemaining: timeRemaining.value,
    })
  }

  function tickTimer() {
    if (timeRemaining.value > 0) {
      timeRemaining.value--
      if (timeRemaining.value % 30 === 0) persistDraft()
    }
  }

  async function submitExam() {
    phase.value = 'evaluating'
    evaluating.value = true
    error.value = null

    let testCorrect = 0
    let testTotal = 0
    let testPoints = 0
    let testMaxPoints = 0

    for (const q of testQuestions.value) {
      const ans = answers.value[q.id]
      testTotal++
      testMaxPoints += q.punts
      if (ans) {
        testPoints += ans.points_earned
        if (ans.correct) testCorrect++
      }
    }

    const openAnswers = openQuestions.value.map(q => ({
      id: q.id,
      enunciat: q.enunciat,
      resposta_usuari: answers.value[q.id]?.value || '',
      resposta_model: q.resposta_model || '',
      rubrica: q.rubrica || '',
      punts: q.punts,
    }))

    let evaluations = []
    try {
      const data = await evaluateSimulacre(openAnswers)
      evaluations = data.evaluations || []
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error avaluant les respostes. Torna a intentar-ho.'
      phase.value = 'exam'
      evaluating.value = false
      return
    }

    let breusScore = 0
    let breusTotal = 0
    let supositScore = 0
    let supositTotal = 0

    const evalMap = {}
    for (const ev of evaluations) evalMap[ev.id] = ev

    const updatedAnswers = { ...answers.value }
    for (const q of openQuestions.value) {
      const ev = evalMap[q.id]
      const factor = ev ? ev.factor : 0
      const earned = q.punts * factor
      if (q.tipus === 'breu') {
        breusScore += earned
        breusTotal += q.punts
      } else {
        supositScore += earned
        supositTotal += q.punts
      }
      if (updatedAnswers[q.id]) {
        updatedAnswers[q.id] = { ...updatedAnswers[q.id], points_earned: earned, evaluation: ev }
      }
    }
    answers.value = updatedAnswers

    const totalEarned = testPoints + breusScore + supositScore
    const totalMax = testMaxPoints + breusTotal + supositTotal
    const score = totalMax > 0 ? Math.round((totalEarned / totalMax) * 100) / 10 : 0
    const passed = score >= 5.0
    const timeTaken = 7200 - timeRemaining.value

    results.value = {
      score,
      passed,
      timeTaken,
      testCorrect,
      testTotal,
      breusScore: Math.round(breusScore * 100) / 100,
      breusTotal: Math.round(breusTotal * 100) / 100,
      supositScore: Math.round(supositScore * 100) / 100,
      supositTotal: Math.round(supositTotal * 100) / 100,
      questions: questions.value,
      answers: answers.value,
    }

    try {
      await saveSimulacre({
        score,
        passed,
        time_taken_seconds: timeTaken,
        q_test_correct: testCorrect,
        q_test_total: testTotal,
        q_breus_score: breusScore,
        q_breus_total: breusTotal,
        q_suposit_score: supositScore,
        q_suposit_total: supositTotal,
        topics_used: topicsUsed.value,
      })
      lastResult.value = { score, passed, date: new Date().toISOString() }
    } catch {}

    clearDraft()
    saveResults(results.value)
    phase.value = 'results'
    evaluating.value = false
  }

  async function reEvaluate() {
    if (!results.value) return
    evaluating.value = true
    error.value = null
    const qs = results.value.questions.filter(q => q.tipus !== 'test')
    const openAnswers = qs.map(q => ({
      id: q.id,
      enunciat: q.enunciat,
      resposta_usuari: results.value.answers[q.id]?.value || '',
      resposta_model: q.resposta_model || '',
      rubrica: q.rubrica || '',
      punts: q.punts,
    }))
    let evaluations = []
    try {
      const data = await evaluateSimulacre(openAnswers)
      evaluations = data.evaluations || []
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error reavaluant. Torna a intentar-ho.'
      evaluating.value = false
      return
    }
    const evalMap = {}
    for (const ev of evaluations) evalMap[ev.id] = ev
    const updatedAnswers = { ...results.value.answers }
    let breusScore = 0, breusTotal = 0, supositScore = 0, supositTotal = 0
    for (const q of qs) {
      const ev = evalMap[q.id]
      const factor = ev ? ev.factor : (updatedAnswers[q.id]?.evaluation?.factor ?? 0)
      const earned = q.punts * factor
      if (q.tipus === 'breu') { breusScore += earned; breusTotal += q.punts }
      else { supositScore += earned; supositTotal += q.punts }
      if (updatedAnswers[q.id] && ev) {
        updatedAnswers[q.id] = { ...updatedAnswers[q.id], points_earned: earned, evaluation: ev }
      }
    }
    const testPoints = results.value.questions
      .filter(q => q.tipus === 'test')
      .reduce((s, q) => s + (results.value.answers[q.id]?.points_earned || 0), 0)
    const testMaxPoints = results.value.questions
      .filter(q => q.tipus === 'test')
      .reduce((s, q) => s + q.punts, 0)
    const totalEarned = testPoints + breusScore + supositScore
    const totalMax = testMaxPoints + breusTotal + supositTotal
    const score = totalMax > 0 ? Math.round((totalEarned / totalMax) * 100) / 10 : 0
    results.value = {
      ...results.value,
      score,
      passed: score >= 5.0,
      breusScore: Math.round(breusScore * 100) / 100,
      breusTotal: Math.round(breusTotal * 100) / 100,
      supositScore: Math.round(supositScore * 100) / 100,
      supositTotal: Math.round(supositTotal * 100) / 100,
      answers: updatedAnswers,
    }
    saveResults(results.value)
    evaluating.value = false
  }

  function reset() {
    questions.value = []
    answers.value = {}
    timeRemaining.value = 7200
    results.value = null
    error.value = null
    phase.value = 'idle'
    clearDraft()
    clearSavedResults()
  }

  return {
    questions, answers, timeRemaining, generating, evaluating, error,
    results, lastResult, phase,
    totalQuestions, answeredCount, testQuestions, openQuestions,
    loadLastResult, loadRoundState, startGeneration, answerTest, answerOpen,
    tickTimer, submitExam, reEvaluate, reset, persistDraft,
    topicsUsed, roundState,
  }
})
