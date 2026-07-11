<script setup lang="ts">
import { ArrowUpRight, BriefcaseBusiness, FileCheck2, WandSparkles } from "lucide-vue-next"
import ScrollFloat from "@/components/ui/ScrollFloat.vue"
</script>

<template>
  <section class="home-section feature-section" aria-labelledby="feature-title">
    <div class="section-heading feature-heading">
      <p class="section-kicker">一份持续成长的职业档案</p>
      <ScrollFloat
        id="feature-title"
        container-class-name="feature-scroll-title"
        text-class-name="home-scroll-float-text"
        :animation-duration="0.9"
        ease="power3.out"
        scroll-start="top bottom-=8%"
        scroll-end="center center+=12%"
        :stagger="0.022"
      >不是替你包装，而是帮你找到真正有价值的表达。</ScrollFloat>
      <p>每一次建议都能追溯、比较和选择。你始终掌握简历内容，AI 负责把信息整理得更准确。</p>
    </div>

    <div class="feature-grid">
      <article class="feature-card feature-ai">
        <div class="feature-card-head"><span class="feature-icon"><WandSparkles :size="19" /></span><b>AI 表达教练</b><ArrowUpRight :size="20" /></div>
        <div class="diff-window">
          <div class="diff-toolbar"><span></span><span></span><span></span><small>正在优化 · 项目经历</small></div>
          <p class="diff-before"><del>负责产品需求和页面设计，配合团队完成项目。</del></p>
          <p class="diff-after">主导核心流程重构，推动设计与研发协作，使任务完成效率提升 <strong>38%</strong>。</p>
          <div class="diff-actions"><button>保留原文</button><button>应用建议</button></div>
        </div>
      </article>

      <article class="feature-card feature-match">
        <div class="feature-card-head"><span class="feature-icon"><BriefcaseBusiness :size="19" /></span><b>岗位匹配分析</b><ArrowUpRight :size="20" /></div>
        <div class="match-score"><strong>91</strong><span>%</span><i></i></div>
        <p>已覆盖 8 项关键要求</p>
        <div class="match-tags"><span>用户研究</span><span>产品策略</span><span>数据分析</span></div>
      </article>

      <article class="feature-card feature-export">
        <div class="feature-card-head"><span class="feature-icon"><FileCheck2 :size="19" /></span><b>多端一致导出</b><ArrowUpRight :size="20" /></div>
        <div class="export-stack"><span>PDF</span><span>WORD</span><span>LINK</span></div>
        <p>预览、PDF 与 Word 保持同一套版式语言。</p>
      </article>
    </div>
  </section>
</template>
