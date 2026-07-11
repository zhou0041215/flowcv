<script setup lang="ts">
import AppLayout from "@/components/layout/AppLayout.vue"
import HeroSection from "@/components/home/HeroSection.vue"
import FeatureSection from "@/components/home/FeatureSection.vue"
import TemplateShowcase from "@/components/home/TemplateShowcase.vue"
import WorkflowSection from "@/components/home/WorkflowSection.vue"
</script>

<template>
  <AppLayout>
    <main id="vita-home" class="vita-home">
      <HeroSection />
      <FeatureSection />
      <TemplateShowcase />
      <WorkflowSection />

      <footer class="home-footer">
        <div class="footer-brand">
          <span class="footer-mark">FC</span>
          <div><strong>FlowCV</strong><small>让经历流向更好的机会</small></div>
        </div>
        <div class="footer-links">
          <RouterLink to="/templates">模板中心</RouterLink>
          <RouterLink to="/help">使用帮助</RouterLink>
          <a href="https://github.com/zhou0041215/fuzzy-broccoli" target="_blank" rel="noopener noreferrer">GitHub</a>
        </div>
      </footer>
    </main>
  </AppLayout>
</template>

<style src="./Home.css"></style>
