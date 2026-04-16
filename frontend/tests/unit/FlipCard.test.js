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
    await w.trigger('click')
    await w.setProps({ card: { pregunta: 'Nova pregunta', resposta: 'Nova resposta', exemple: '' } })
    expect(w.text()).toContain('Nova pregunta')
    expect(w.text()).not.toContain('Nova resposta')
  })
})
