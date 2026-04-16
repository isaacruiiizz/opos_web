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
