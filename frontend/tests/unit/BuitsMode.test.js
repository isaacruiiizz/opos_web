import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import BuitsMode from '../../src/components/practice/BuitsMode.vue'

const sentences = [
  { frase: "El ___ és responsable de l'administració", paraules: ['Alcalde'], posicions: [1] },
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
