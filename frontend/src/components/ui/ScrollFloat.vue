<template>
  <h2 ref="containerRef" :class="`my-5 overflow-hidden ${containerClassName}`">
    <span :class="`inline-block text-[clamp(1.6rem,8vw,10rem)] leading-[1.5] font-black text-center ${textClassName}`">
      <span v-for="(char, index) in splitText" :key="index" class="inline-block scroll-float-char">
        {{ char }}
      </span>
    </span>
  </h2>
</template>

<script setup lang="ts">
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import { computed, nextTick, onMounted, onUnmounted, useSlots, useTemplateRef, watch, type Ref } from "vue"

gsap.registerPlugin(ScrollTrigger)

interface ScrollFloatProps {
  scrollContainerRef?: Ref<HTMLElement | null> | HTMLElement | null
  containerClassName?: string
  textClassName?: string
  animationDuration?: number
  ease?: string
  scrollStart?: string
  scrollEnd?: string
  stagger?: number
}

const props = withDefaults(defineProps<ScrollFloatProps>(), {
  scrollContainerRef: null,
  containerClassName: "",
  textClassName: "",
  animationDuration: 1,
  ease: "back.inOut(2)",
  scrollStart: "center bottom+=50%",
  scrollEnd: "bottom bottom-=40%",
  stagger: 0.03,
})

const slots = useSlots()
const containerRef = useTemplateRef<HTMLHeadingElement>("containerRef")

const text = computed(() => {
  const nodes = slots.default?.() ?? []
  return nodes.map((node) => typeof node.children === "string" ? node.children : "").join("")
})

const splitText = computed(() => text.value.split("").map((char) => char === " " ? "\u00A0" : char))

function resolveScroller(scrollerRef: ScrollFloatProps["scrollContainerRef"]): HTMLElement | Window {
  if (!scrollerRef) return window
  if (scrollerRef instanceof HTMLElement) return scrollerRef
  return scrollerRef.value ?? window
}

let tween: gsap.core.Tween | null = null
let context: gsap.Context | null = null

function cleanup() {
  tween?.scrollTrigger?.kill()
  tween?.kill()
  tween = null
  context?.revert()
  context = null
}

async function createAnimation() {
  await nextTick()
  const element = containerRef.value
  if (!element) return

  const charElements = element.querySelectorAll(".scroll-float-char")
  cleanup()

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    gsap.set(charElements, { opacity: 1, yPercent: 0, scaleX: 1, scaleY: 1 })
    return
  }

  const scroller = resolveScroller(props.scrollContainerRef)
  context = gsap.context(() => {
    tween = gsap.fromTo(
      charElements,
      {
        willChange: "opacity, transform",
        opacity: 0,
        yPercent: 120,
        scaleY: 2.3,
        scaleX: 0.7,
        transformOrigin: "50% 0%",
      },
      {
        duration: props.animationDuration,
        ease: props.ease,
        opacity: 1,
        yPercent: 0,
        scaleY: 1,
        scaleX: 1,
        stagger: props.stagger,
        scrollTrigger: {
          trigger: element,
          scroller,
          start: props.scrollStart,
          end: props.scrollEnd,
          scrub: true,
        },
      },
    )
  }, element)

  requestAnimationFrame(() => ScrollTrigger.refresh())
}

onMounted(async () => {
  await nextTick()
  await createAnimation()
})

watch(
  () => [props.animationDuration, props.ease, props.scrollStart, props.scrollEnd, props.stagger],
  createAnimation,
)

watch(
  () => {
    const value = props.scrollContainerRef
    if (!value) return null
    if (value instanceof HTMLElement) return value
    return value.value
  },
  createAnimation,
)

onUnmounted(cleanup)
</script>
