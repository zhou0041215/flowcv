<script setup lang="ts">
import { ArrowRight, Check } from "lucide-vue-next"
import SplitText from "@/components/ui/SplitText.vue"
</script>

<template>
  <section class="workflow-wrap" aria-labelledby="workflow-title">
    <div class="workflow-panel">
      <div class="workflow-copy">
        <p class="section-kicker">从空白到可投递</p>
        <SplitText
          id="workflow-title"
          text="把复杂的求职准备，收进一个工作台。"
          tag="h2"
          class-name="workflow-split-title"
          split-type="chars"
          :delay="45"
          :duration="0.7"
          ease="power3.out"
          :from="{ opacity: 0, y: 54, rotateX: -12 }"
          :to="{ opacity: 1, y: 0, rotateX: 0 }"
          :threshold="0.16"
          root-margin="-40px"
          text-align="left"
        />
        <p>选择模板、整理经历、接受 AI 建议，然后带着一份经得起追问的简历出发。</p>
        <RouterLink to="/resumes" class="workflow-button">免费创建简历 <ArrowRight :size="18" /></RouterLink>
      </div>
      <div class="workflow-journey">
        <div class="workflow-journey-head"><span>DELIVERY PATH / 03</span><strong>从资料到投递</strong></div>
        <ol class="workflow-steps">
          <li><span>01</span><div><strong>建立职业档案</strong><p>导入旧简历，或从一张空白纸开始。</p></div><Check :size="17" /></li>
          <li><span>02</span><div><strong>让 AI 读懂岗位</strong><p>对照 JD 找出缺口，不错过关键能力。</p></div><Check :size="17" /></li>
          <li><span>03</span><div><strong>确认并投递</strong><p>逐条接受修改，导出清晰稳定的文件。</p></div><Check :size="17" /></li>
        </ol>
      </div>
    </div>
  </section>
</template>
