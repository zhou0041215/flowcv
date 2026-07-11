<script setup lang="ts">
import { ArrowRight, Play, Sparkles } from "lucide-vue-next"
</script>

<template>
  <section class="home-hero" aria-labelledby="home-hero-title">
    <div class="hero-stage">
      <div class="hero-noise"></div>
      <div class="hero-copy">
        <p class="hero-eyebrow"><Sparkles :size="13" /> AI RESUME WORKSPACE</p>
        <h1 id="home-hero-title">让你的经历，<br><em>更快被看见。</em></h1>
        <p class="hero-lead">从内容梳理、岗位匹配到专业排版，VitaFlow 把每次修改都变成更接近目标岗位的一步。</p>
        <div class="hero-actions">
          <RouterLink to="/resumes" class="hero-button hero-button-dark">开始创建 <ArrowRight :size="17" /></RouterLink>
          <RouterLink to="/templates" class="hero-button hero-button-light"><Play :size="15" fill="currentColor" /> 浏览模板</RouterLink>
        </div>
      </div>

      <div class="resume-flight" aria-label="AI 简历优化效果演示">
        <div class="flight-orbit orbit-one"></div>
        <div class="flight-orbit orbit-two"></div>

        <div class="flight-note note-left">
          <span>表达优化</span>
          <strong>影响力提升 32%</strong>
          <i></i>
        </div>
        <div class="flight-note note-right">
          <span>目标岗位</span>
          <strong>产品设计师</strong>
          <small>匹配度 91%</small>
        </div>

        <div class="paper paper-back-two"></div>
        <div class="paper paper-back-one"></div>
        <article class="paper resume-paper">
          <div class="paper-topline"><span>PROFILE / 2026</span><span>01 PAGE</span></div>
          <header class="paper-header">
            <div><h2>林知远</h2><p>产品设计师 · AI 工具方向</p></div>
            <span class="paper-avatar">LZ</span>
          </header>
          <div class="paper-rule"></div>
          <div class="paper-layout">
            <div class="paper-main">
              <section><h3>核心经历</h3><b></b><i></i><i class="short"></i></section>
              <section><h3>项目成果</h3><b></b><i></i><i></i><p>用户激活率提升 32%</p></section>
            </div>
            <aside><h3>能力</h3><span>产品策略</span><span>交互设计</span><span>数据分析</span></aside>
          </div>
          <div class="paper-scan"><span>AI REVIEWING</span></div>
          <div class="paper-check">✓</div>
        </article>
      </div>

      <div class="hero-cloud cloud-left"></div>
      <div class="hero-cloud cloud-right"></div>
      <div class="hero-cloud cloud-center"></div>
    </div>
  </section>
</template>
