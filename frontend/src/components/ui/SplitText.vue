<script setup lang="ts">
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import { SplitText as GSAPSplitText } from "gsap/SplitText"
import { computed, onBeforeUnmount, onMounted, ref, watch, type CSSProperties } from "vue"

gsap.registerPlugin(ScrollTrigger, GSAPSplitText)

type SplitType = "chars" | "words" | "lines" | "words, chars"
type TagName = "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "p" | "span"
type EaseFn = (t: number) => number

interface SplitTextElement extends HTMLElement {
  _rbsplitInstance?: GSAPSplitText
}

interface Props {
  text: string
  className?: string
  delay?: number
  duration?: number
  ease?: string | EaseFn
  splitType?: SplitType
  from?: gsap.TweenVars
  to?: gsap.TweenVars
  threshold?: number
  rootMargin?: string
  tag?: TagName
  textAlign?: CSSProperties["textAlign"]
  onLetterAnimationComplete?: () => void
}

const props = withDefaults(defineProps<Props>(), {
  className: "",
  delay: 50,
  duration: 1.25,
  ease: "power3.out",
  splitType: "chars",
  from: () => ({ opacity: 0, y: 40 }),
  to: () => ({ opacity: 1, y: 0 }),
  threshold: 0.1,
  rootMargin: "-100px",
  tag: "p",
  textAlign: "center",
  onLetterAnimationComplete: undefined,
})

const emit = defineEmits<{ "animation-complete": [] }>()
const elRef = ref<SplitTextElement | null>(null)
const fontsLoaded = ref(false)
const animationCompleted = ref(false)
const onCompleteRef = ref(props.onLetterAnimationComplete)

watch(() => props.onLetterAnimationComplete, (callback) => {
  onCompleteRef.value = callback
})

const scrollTriggerStart = computed(() => {
  const startPct = (1 - props.threshold) * 100
  const match = /^(-?\d+(?:\.\d+)?)(px|em|rem|%)?$/.exec(props.rootMargin || "")
  const value = match ? parseFloat(match[1]) : 0
  const unit = match ? match[2] || "px" : "px"
  const sign = value === 0 ? "" : value < 0 ? `-=${Math.abs(value)}${unit}` : `+=${value}${unit}`
  return `top ${startPct}%${sign}`
})

const elStyle = computed<CSSProperties>(() => ({
  textAlign: props.textAlign,
  wordWrap: "break-word",
  willChange: "transform, opacity",
}))

const elClass = computed(() => [
  "split-parent overflow-hidden inline-block whitespace-normal",
  props.className,
].filter(Boolean).join(" "))

function assignTargets(instance: GSAPSplitText): Element[] {
  if (props.splitType.includes("chars") && instance.chars?.length) return instance.chars
  if (props.splitType.includes("words") && instance.words?.length) return instance.words
  if (props.splitType.includes("lines") && instance.lines?.length) return instance.lines
  return instance.chars ?? instance.words ?? instance.lines ?? []
}

function destroyInstance(): void {
  const element = elRef.value
  if (!element) return
  ScrollTrigger.getAll().forEach((trigger) => {
    if (trigger.trigger === element) trigger.kill()
  })
  try {
    element._rbsplitInstance?.revert()
  } catch {
    // The source element may already have been removed during route changes.
  }
  element._rbsplitInstance = undefined
}

function completeAnimation(): void {
  animationCompleted.value = true
  onCompleteRef.value?.()
  emit("animation-complete")
}

function initAnimation(): void {
  const element = elRef.value
  if (!element || !props.text || !fontsLoaded.value || animationCompleted.value) return

  destroyInstance()

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    gsap.set(element, { ...props.to, clearProps: "transform" })
    completeAnimation()
    return
  }

  const splitInstance = new GSAPSplitText(element, {
    type: props.splitType,
    smartWrap: true,
    autoSplit: props.splitType === "lines",
    linesClass: "split-line",
    wordsClass: "split-word",
    charsClass: "split-char",
    reduceWhiteSpace: false,
    onSplit: (instance: GSAPSplitText) => gsap.fromTo(
      assignTargets(instance),
      { ...props.from },
      {
        ...props.to,
        duration: props.duration,
        ease: props.ease,
        stagger: props.delay / 1000,
        scrollTrigger: {
          trigger: element,
          start: scrollTriggerStart.value,
          once: true,
          fastScrollEnd: true,
          anticipatePin: 0.4,
        },
        onComplete: completeAnimation,
        willChange: "transform, opacity",
        force3D: true,
      },
    ),
  })

  element._rbsplitInstance = splitInstance
}

onMounted(() => {
  if (document.fonts.status === "loaded") {
    fontsLoaded.value = true
  } else {
    document.fonts.ready.then(() => {
      fontsLoaded.value = true
    })
  }
})

watch(fontsLoaded, (loaded) => {
  if (loaded) initAnimation()
})

watch(
  () => [
    props.text,
    props.delay,
    props.duration,
    props.ease,
    props.splitType,
    JSON.stringify(props.from),
    JSON.stringify(props.to),
    props.threshold,
    props.rootMargin,
    fontsLoaded.value,
  ],
  () => {
    if (!fontsLoaded.value) return
    animationCompleted.value = false
    initAnimation()
  },
)

onBeforeUnmount(destroyInstance)
</script>

<template>
  <component :is="tag" ref="elRef" :class="elClass" :style="elStyle">{{ text }}</component>
</template>
