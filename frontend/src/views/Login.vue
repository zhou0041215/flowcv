<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue"
import { useRouter, useRoute, RouterLink } from "vue-router"
import { useUserStore } from "@/stores/user"
import {
  registerApi,
  resetPasswordApi,
  sendPasswordResetCodeApi,
  sendVerificationCodeApi,
  getUserAgreementApi,
} from "@/api/auth"
import Button from "@/components/ui/button/Button.vue"
import Input from "@/components/ui/input/Input.vue"
import Label from "@/components/ui/label/Label.vue"
import BrandLogo from "@/components/common/BrandLogo.vue"
import { ArrowRight, Check, ShieldCheck, X } from "lucide-vue-next"

const router = useRouter()
const route = useRoute()
const user = useUserStore()

const isRegister = ref(false)
const isForgotPassword = ref(false)
const agreed = ref(true)
const showAgreementModal = ref(false)
const userAgreementContent = ref("")
const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

const loginEmail = ref("")
const loginPassword = ref("")
const loginError = ref("")
const loginSuccess = ref("")

const regForm = ref({ username: "", email: "", password: "", verification_code: "" })
const regError = ref("")
const regSuccess = ref("")
const codeSeconds = ref(0)
const sendingCode = ref(false)
let countdownTimer: number | undefined

const resetForm = ref({ email: "", verification_code: "", new_password: "" })
const resetError = ref("")
const resetSuccess = ref("")
const resetCodeSeconds = ref(0)
const sendingResetCode = ref(false)
let resetCountdownTimer: number | undefined

onMounted(async () => {
  if (route.path === "/register") isRegister.value = true
  try {
    const res = await getUserAgreementApi()
    userAgreementContent.value = res.user_agreement
  } catch (e) {
    console.error("Failed to load user agreement", e)
  }
})

watch(() => route.path, (newPath) => {
  isRegister.value = newPath === "/register"
  if (isRegister.value) isForgotPassword.value = false
})

function toggleMode(targetPath: string) {
  isForgotPassword.value = false
  router.push(targetPath)
}

function showForgotPassword() {
  loginError.value = ""
  loginSuccess.value = ""
  resetError.value = ""
  resetSuccess.value = ""
  resetForm.value.email = loginEmail.value.trim()
  isForgotPassword.value = true
}

function backToLogin() {
  isForgotPassword.value = false
  resetError.value = ""
  resetSuccess.value = ""
}

async function handleLogin() {
  try {
    loginError.value = ""
    loginSuccess.value = ""
    if (!agreed.value) throw new Error("请先阅读并同意用户协议")
    if (!emailPattern.test(loginEmail.value.trim())) throw new Error("请输入正确的邮箱地址")
    if (!loginPassword.value) throw new Error("请输入密码")
    await user.login(loginEmail.value, loginPassword.value)
    router.push("/resumes")
  } catch (e: any) {
    loginError.value = e.message
  }
}

async function sendCode() {
  try {
    regError.value = ""
    regSuccess.value = ""
    if (!emailPattern.test(regForm.value.email.trim())) throw new Error("请输入正确的邮箱地址")
    sendingCode.value = true
    await sendVerificationCodeApi(regForm.value.email)
    regSuccess.value = "验证码已发送，如果没有收到请检查垃圾邮件"
    codeSeconds.value = 60
    countdownTimer = window.setInterval(() => {
      codeSeconds.value -= 1
      if (codeSeconds.value <= 0 && countdownTimer) {
        window.clearInterval(countdownTimer)
        countdownTimer = undefined
      }
    }, 1000)
  } catch (e: any) {
    regError.value = e.message
  } finally {
    sendingCode.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) window.clearInterval(countdownTimer)
  if (resetCountdownTimer) window.clearInterval(resetCountdownTimer)
})

async function handleRegister() {
  try {
    regError.value = ""
    regSuccess.value = ""
    if (!agreed.value) throw new Error("请先阅读并同意用户协议")
    if (regForm.value.username.trim().length < 2) throw new Error("用户名至少需要 2 个字符")
    if (!emailPattern.test(regForm.value.email.trim())) throw new Error("请输入正确的邮箱地址")
    if (regForm.value.password.length < 6) throw new Error("密码至少需要 6 个字符")
    if (!/^\d{6}$/.test(regForm.value.verification_code)) throw new Error("请输入 6 位邮箱验证码")
    await registerApi(regForm.value)
    loginEmail.value = regForm.value.email
    loginPassword.value = regForm.value.password
    regForm.value = { username: "", email: "", password: "", verification_code: "" }
    router.push("/login")
  } catch (e: any) {
    regError.value = e.message
  }
}

async function sendResetCode() {
  try {
    resetError.value = ""
    resetSuccess.value = ""
    if (!emailPattern.test(resetForm.value.email.trim())) throw new Error("请输入正确的邮箱地址")
    sendingResetCode.value = true
    await sendPasswordResetCodeApi(resetForm.value.email)
    resetSuccess.value = "验证码已发送，如果没有收到请检查垃圾邮件"
    resetCodeSeconds.value = 60
    resetCountdownTimer = window.setInterval(() => {
      resetCodeSeconds.value -= 1
      if (resetCodeSeconds.value <= 0 && resetCountdownTimer) {
        window.clearInterval(resetCountdownTimer)
        resetCountdownTimer = undefined
      }
    }, 1000)
  } catch (e: any) {
    resetError.value = e.message
  } finally {
    sendingResetCode.value = false
  }
}

async function handleResetPassword() {
  try {
    resetError.value = ""
    resetSuccess.value = ""
    const email = resetForm.value.email.trim()
    if (!emailPattern.test(email)) throw new Error("请输入正确的邮箱地址")
    if (!/^\d{6}$/.test(resetForm.value.verification_code)) throw new Error("请输入 6 位邮箱验证码")
    if (resetForm.value.new_password.length < 6) throw new Error("新密码至少需要 6 个字符")
    await resetPasswordApi({
      email,
      verification_code: resetForm.value.verification_code,
      new_password: resetForm.value.new_password,
    })
    loginEmail.value = email
    loginPassword.value = ""
    loginSuccess.value = "密码已重置，请使用新密码登录"
    resetForm.value = { email: "", verification_code: "", new_password: "" }
    isForgotPassword.value = false
  } catch (e: any) {
    resetError.value = e.message
  }
}
</script>

<template>
  <div id="vita-auth-page" class="auth-page">
    <div class="auth-grid" aria-hidden="true"></div>
    <header class="auth-topbar">
      <RouterLink to="/" class="brand-link" aria-label="返回 FlowCV 首页">
        <BrandLogo size="sm" />
      </RouterLink>
      <div class="workspace-status"><span class="status-light"></span>AI RESUME WORKSPACE</div>
    </header>

    <main class="auth-layout">
      <section class="story-panel" aria-labelledby="auth-story-title">
        <div class="story-copy">
          <p class="story-eyebrow"><span>表达，不止是排版</span></p>
          <h1 id="auth-story-title" class="story-title">让每一段经历，<span>都落在关键位置。</span></h1>
          <p class="story-description">FlowCV 把内容梳理、岗位匹配和专业排版放进同一张工作台，让你的简历更准确，也更有分量。</p>
        </div>

        <div class="resume-lab" aria-label="AI 正在校订一份简历的动态示意">
          <div class="folio-shadow folio-shadow-one"></div>
          <div class="folio-shadow folio-shadow-two"></div>
          <article class="resume-sheet">
            <div class="sheet-meta"><span>PROFILE / 2026</span><span>01 PAGE</span></div>
            <div class="sheet-heading">
              <div><p>林知远</p><span>产品设计师 · AI 工具方向</span></div>
              <div class="sheet-avatar">LZ</div>
            </div>
            <div class="sheet-rule"></div>
            <div class="sheet-columns">
              <div class="sheet-main">
                <section>
                  <p class="sheet-label">核心经历</p>
                  <div class="sheet-line line-long"></div><div class="sheet-line line-medium"></div><div class="sheet-line line-long"></div>
                </section>
                <section>
                  <p class="sheet-label">项目成果</p>
                  <div class="sheet-line line-long"></div><div class="sheet-line line-short"></div>
                  <div class="sheet-highlight">用户激活率提升 32%</div>
                </section>
              </div>
              <aside class="sheet-side"><p class="sheet-label">能力</p><span>产品策略</span><span>交互设计</span><span>数据分析</span></aside>
            </div>
            <div class="scan-line" aria-hidden="true"><span>AI REVIEWING</span></div>
            <div class="ai-annotation"><span class="annotation-mark">✓</span><div><strong>表达已校准</strong><small>突出动作、方法与结果</small></div></div>
          </article>
          <div class="lab-rail" aria-hidden="true">
            <span class="rail-label">校订进度</span>
            <div class="rail-item is-active"><i></i><span>内容</span><b>完成</b></div>
            <div class="rail-item is-active"><i></i><span>表达</span><b>完成</b></div>
            <div class="rail-item"><i></i><span>岗位</span><b>分析中</b></div>
          </div>
        </div>
        <div class="story-footer"><span>内容编辑</span><i></i><span>AI 优化</span><i></i><span>PDF / Word 导出</span></div>
      </section>

      <section class="auth-zone" aria-label="账号登录与注册">
        <div class="mobile-brand">
          <RouterLink to="/" class="brand-link" aria-label="返回 FlowCV 首页"><BrandLogo size="sm" /></RouterLink>
        </div>
        <div class="auth-card">
          <div class="auth-flip" :class="{ flipped: isRegister, 'is-reset': isForgotPassword }">
            <div class="flipper">
              <section class="panel-face front">
                <div class="form-heading">
                  <p>{{ isForgotPassword ? "ACCOUNT RECOVERY" : "SECURE ACCESS" }}</p>
                  <h2>{{ isForgotPassword ? "重新设置密码" : "继续你的简历" }}</h2>
                  <span>{{ isForgotPassword ? "验证邮箱后即可设置新密码。" : "登录后，继续编辑、优化和投递准备。" }}</span>
                </div>

                <form v-if="!isForgotPassword" class="auth-form" @submit.prevent="handleLogin">
                  <div class="field-block"><Label class="field-label">邮箱</Label><Input v-model="loginEmail" type="email" autocomplete="email" placeholder="name@example.com" class="auth-input" /></div>
                  <div class="field-block">
                    <div class="field-row"><Label class="field-label">密码</Label><button type="button" class="text-action" @click="showForgotPassword">忘记密码</button></div>
                    <Input v-model="loginPassword" type="password" autocomplete="current-password" placeholder="输入登录密码" class="auth-input" />
                  </div>
                  <div class="agreement-row">
                    <button type="button" class="agreement-check" :class="{ checked: agreed }" :aria-pressed="agreed" aria-label="同意用户协议" @click="agreed = !agreed"><Check v-if="agreed" class="h-3 w-3 stroke-[3]" /></button>
                    <span>我已阅读并同意 <button type="button" @click="showAgreementModal = true">用户协议与隐私政策</button></span>
                  </div>
                  <p v-if="loginError" class="form-message error-message">{{ loginError }}</p>
                  <p v-if="loginSuccess" class="form-message success-message">{{ loginSuccess }}</p>
                  <Button type="submit" class="primary-action">进入工作台 <ArrowRight class="h-4 w-4" /></Button>
                </form>

                <form v-else class="auth-form reset-form" @submit.prevent="handleResetPassword">
                  <div class="field-block"><Label class="field-label">注册邮箱</Label><Input v-model="resetForm.email" type="email" autocomplete="email" placeholder="name@example.com" class="auth-input" /></div>
                  <div class="field-block">
                    <Label class="field-label">邮箱验证码</Label>
                    <div class="code-row"><Input v-model="resetForm.verification_code" inputmode="numeric" maxlength="6" placeholder="6 位验证码" class="auth-input" /><Button type="button" variant="outline" class="code-button" :disabled="sendingResetCode || resetCodeSeconds > 0" @click="sendResetCode">{{ resetCodeSeconds > 0 ? `${resetCodeSeconds}s` : (sendingResetCode ? "发送中" : "发送验证码") }}</Button></div>
                  </div>
                  <div class="field-block"><Label class="field-label">新密码</Label><Input v-model="resetForm.new_password" type="password" autocomplete="new-password" placeholder="至少 6 个字符" class="auth-input" /></div>
                  <p v-if="resetError" class="form-message error-message">{{ resetError }}</p>
                  <p v-if="resetSuccess" class="form-message success-message">{{ resetSuccess }}</p>
                  <Button type="submit" class="primary-action">保存新密码 <ArrowRight class="h-4 w-4" /></Button>
                  <button type="button" class="secondary-action" @click="backToLogin">返回登录</button>
                </form>

                <div v-if="!isForgotPassword" class="mode-switch"><span>第一次使用 FlowCV？</span><button type="button" @click="toggleMode('/register')">创建账号</button></div>
              </section>

              <section class="panel-face back">
                <div class="form-heading"><p>CREATE WORKSPACE</p><h2>建立你的简历档案</h2><span>从一份可持续更新的职业档案开始。</span></div>
                <form class="auth-form register-form" @submit.prevent="handleRegister">
                  <div class="field-block"><Label class="field-label">用户名</Label><Input v-model="regForm.username" autocomplete="name" placeholder="如何称呼你" class="auth-input" /></div>
                  <div class="field-block"><Label class="field-label">邮箱</Label><Input v-model="regForm.email" type="email" autocomplete="email" placeholder="name@example.com" class="auth-input" /></div>
                  <div class="field-block"><Label class="field-label">密码</Label><Input v-model="regForm.password" type="password" autocomplete="new-password" placeholder="至少 6 个字符" class="auth-input" /></div>
                  <div class="field-block">
                    <Label class="field-label">邮箱验证码</Label>
                    <div class="code-row"><Input v-model="regForm.verification_code" inputmode="numeric" maxlength="6" placeholder="6 位验证码" class="auth-input" /><Button type="button" variant="outline" class="code-button" :disabled="sendingCode || codeSeconds > 0" @click="sendCode">{{ codeSeconds > 0 ? `${codeSeconds}s` : (sendingCode ? "发送中" : "发送验证码") }}</Button></div>
                  </div>
                  <div class="agreement-row compact-agreement">
                    <button type="button" class="agreement-check" :class="{ checked: agreed }" :aria-pressed="agreed" aria-label="同意用户协议" @click="agreed = !agreed"><Check v-if="agreed" class="h-3 w-3 stroke-[3]" /></button>
                    <span>我已阅读并同意 <button type="button" @click="showAgreementModal = true">用户协议与隐私政策</button></span>
                  </div>
                  <p v-if="regError" class="form-message error-message">{{ regError }}</p>
                  <p v-if="regSuccess" class="form-message success-message">{{ regSuccess }}</p>
                  <Button type="submit" class="primary-action">创建账号 <ArrowRight class="h-4 w-4" /></Button>
                </form>
                <div class="mode-switch"><span>已经拥有账号？</span><button type="button" @click="toggleMode('/login')">直接登录</button></div>
              </section>
            </div>
          </div>
        </div>

        <div class="security-note"><ShieldCheck class="h-4 w-4" /><span>你的简历内容仅用于当前工作台，不会公开展示。</span></div>
        <div class="mobile-footer"><span>&copy; 2026 FlowCV</span></div>
      </section>
    </main>

    <div v-if="showAgreementModal" class="agreement-modal" role="dialog" aria-modal="true" aria-labelledby="agreement-title">
      <div class="agreement-card">
        <div class="agreement-header">
          <div><p>LEGAL / PRIVACY</p><h3 id="agreement-title">用户协议与隐私政策</h3></div>
          <button type="button" aria-label="关闭协议" @click="showAgreementModal = false"><X class="h-5 w-5" /></button>
        </div>
        <div class="agreement-content" v-html="userAgreementContent || '暂无协议内容'"></div>
        <div class="agreement-footer"><Button class="primary-action agreement-confirm" @click="showAgreementModal = false; agreed = true">我已阅读并同意</Button></div>
      </div>
    </div>
  </div>
</template>

<style scoped src="./Login.css"></style>
