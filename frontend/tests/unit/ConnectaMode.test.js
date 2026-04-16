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
