<template>
  <div class="relative w-full" :style="{ height: canvasHeight + 'px' }">
    <div class="sticky top-0 z-10 flex items-center gap-2 px-4 py-2
                bg-[var(--color-surface)] border-b border-[var(--color-border)] flex-wrap">
      <button v-for="tool in tools" :key="tool.id"
              @click="setTool(tool.id)"
              :class="activeTool === tool.id ? 'ring-2 ring-primary' : ''"
              class="px-2 py-1 rounded text-sm bg-gray-100 dark:bg-gray-800 hover:bg-primary/20">
        {{ tool.label }}
      </button>
      <input type="color" v-model="strokeColor" class="w-8 h-8 rounded cursor-pointer border-0 p-0" />
      <input type="range" min="1" max="20" v-model.number="strokeWidth" class="w-20" />
      <button @click="saveCanvas" class="ml-auto text-sm text-primary font-medium">Desar</button>
      <button @click="clearCanvas" class="text-sm text-red-500">Esborrar tot</button>
    </div>
    <canvas ref="canvasEl" class="w-full touch-none" style="background: transparent" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Canvas, Ellipse, Line, PencilBrush } from 'fabric'
import { fetchDrawing, saveDrawing } from '../../api/client.js'

const props = defineProps({ topicId: String })

const canvasEl = ref(null)
const canvasHeight = ref(window.innerHeight - 160)
let fc = null

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
  const width = canvasEl.value.parentElement?.clientWidth || 400
  fc = new Canvas(canvasEl.value, {
    width,
    height: canvasHeight.value,
    backgroundColor: '',
  })
  fc.freeDrawingBrush = new PencilBrush(fc)
  fc.isDrawingMode = true
  fc.freeDrawingBrush.color = strokeColor.value
  fc.freeDrawingBrush.width = strokeWidth.value
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
  // fabric v7: event has scenePoint with x/y
  startPoint = opt.scenePoint || { x: opt.e.offsetX, y: opt.e.offsetY }
}

function onMouseMove(opt) {
  if (!drawing || fc.isDrawingMode) return
  const ptr = opt.scenePoint || { x: opt.e.offsetX, y: opt.e.offsetY }
  if (activeShape) fc.remove(activeShape)
  if (activeTool.value === 'circle') {
    const rx = Math.abs(ptr.x - startPoint.x) / 2
    const ry = Math.abs(ptr.y - startPoint.y) / 2
    activeShape = new Ellipse({
      left: Math.min(ptr.x, startPoint.x), top: Math.min(ptr.y, startPoint.y),
      rx, ry, fill: 'transparent',
      stroke: strokeColor.value, strokeWidth: strokeWidth.value,
    })
  } else if (activeTool.value === 'arrow') {
    activeShape = new Line(
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
  try {
    const data = await fetchDrawing(topicId)
    fc.clear()
    if (data?.canvas_json && data.canvas_json !== '{}') {
      await fc.loadFromJSON(data.canvas_json)
      fc.renderAll()
    }
  } catch (e) {
    // Topic has no drawing yet — that's OK
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
  if (fc?.isDrawingMode && fc.freeDrawingBrush) fc.freeDrawingBrush.color = c
})
watch(strokeWidth, w => {
  if (fc?.isDrawingMode && fc.freeDrawingBrush) fc.freeDrawingBrush.width = w
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
