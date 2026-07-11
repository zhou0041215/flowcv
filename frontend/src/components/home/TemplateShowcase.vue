<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, computed } from "vue"
import { ArrowRight } from "lucide-vue-next"
import { listTemplatesApi, type TemplateItem } from "@/api/template"
import TemplatePreview from "@/components/templates/TemplatePreview.vue"
import ScrollFloat from "@/components/ui/ScrollFloat.vue"

const templates = ref<TemplateItem[]>([])
const templateTrackRef = ref<HTMLElement | null>(null)
const isPaused = ref(false)
const isDragging = ref(false)
let dragStartX = 0
let dragStartScrollLeft = 0
let dragDistance = 0
let animationId: number | null = null
let scrollPos = 0
const scrollSpeed = 0.25

const displayTemplates = computed(() => {
  if (!templates.value.length) return []
  return [...templates.value.slice(0, 8), ...templates.value.slice(0, 8)]
})

function startAutoScroll() {
  const track = templateTrackRef.value
  if (!track) return
  const halfWidth = track.scrollWidth / 2

  function step() {
    if (!isPaused.value && !isDragging.value && track) {
      scrollPos += scrollSpeed
      if (scrollPos >= halfWidth) scrollPos = 0
      track.scrollLeft = scrollPos
    }
    animationId = requestAnimationFrame(step)
  }
  animationId = requestAnimationFrame(step)
}

function startTemplateDrag(event: MouseEvent) {
  if (event.button !== 0) return
  const track = templateTrackRef.value
  if (!track) return
  event.preventDefault()
  isDragging.value = true
  dragStartX = event.clientX
  dragStartScrollLeft = track.scrollLeft
  dragDistance = 0
}

function moveTemplateDrag(event: MouseEvent) {
  if (!isDragging.value) return
  const track = templateTrackRef.value
  if (!track) return
  event.preventDefault()
  dragDistance = event.clientX - dragStartX
  track.scrollLeft = dragStartScrollLeft - dragDistance
  scrollPos = track.scrollLeft
}

function endTemplateDrag() {
  if (!isDragging.value) return
  isDragging.value = false
  scrollPos = templateTrackRef.value?.scrollLeft || 0
}

function preventTemplateClick(event: MouseEvent) {
  if (Math.abs(dragDistance) < 6) return
  event.preventDefault()
  event.stopPropagation()
  dragDistance = 0
}

onMounted(async () => {
  try {
    templates.value = await listTemplatesApi()
  } catch {
    templates.value = []
  }
  await nextTick()
  if (templates.value.length) startAutoScroll()
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
})
</script>

<template>
  <section class="home-section template-section" aria-labelledby="template-title">
    <div class="section-heading template-heading">
      <div>
        <p class="section-kicker">为内容留出呼吸感</p>
        <ScrollFloat
          id="template-title"
          container-class-name="template-scroll-title"
          text-class-name="home-scroll-float-text"
          :animation-duration="0.85"
          ease="power3.out"
          scroll-start="top bottom-=8%"
          scroll-end="center center+=14%"
          :stagger="0.028"
        >专业，不必千篇一律。</ScrollFloat>
      </div>
      <RouterLink to="/templates">查看全部模板 <ArrowRight :size="17" /></RouterLink>
    </div>

    <div class="template-stage" :class="{ 'has-live-templates': templates.length }">
      <div
        ref="templateTrackRef"
        class="template-track"
        :class="{ 'is-dragging': isDragging }"
        aria-label="拖动浏览简历模板"
        @mouseenter="isPaused = true"
        @mouseleave="isPaused = false"
        @mousedown="startTemplateDrag"
        @mousemove="moveTemplateDrag"
        @mouseup="endTemplateDrag"
        @dragstart.prevent
      >
        <template v-if="templates.length">
          <RouterLink v-for="(item, index) in displayTemplates" :key="`${item.template_id}-${index}`" to="/templates" class="template-card" :class="`template-card-${index % 3 + 1}`" @click="preventTemplateClick">
            <div class="template-preview"><TemplatePreview :html="item.preview_html" /></div>
            <div class="template-caption"><span>{{ item.name }}</span><small>{{ item.category }}</small></div>
          </RouterLink>
        </template>
        <template v-else>
          <RouterLink v-for="(name, index) in ['清晰叙事', '专业极简', '技术聚焦']" :key="name" to="/templates" class="template-card template-placeholder" :class="`template-card-${index + 1}`" @click="preventTemplateClick">
            <div class="placeholder-paper"><b></b><i></i><i></i><h3></h3><p></p><p></p><h3></h3><p></p><p></p></div>
            <div class="template-caption"><span>{{ name }}</span><small>ATS FRIENDLY</small></div>
          </RouterLink>
        </template>
      </div>
    </div>
  </section>
</template>
