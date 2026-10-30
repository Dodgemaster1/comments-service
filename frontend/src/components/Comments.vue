<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import CommentItem from './Commentitem.vue'

const API = '/api'
const tags = ['i', 'strong', 'code', 'a']
const pageSize = 25
const sorts = [
  { k: 'username', l: 'User Name' },
  { k: 'email', l: 'E-mail' },
  { k: 'created_at', l: 'Date' },
]
const blank = () => ({ user_name: '', email: '', home_page: '', text: '', captcha: '' })

const f = reactive(blank())
const file = ref(null)
const parent = ref(null)
const items = ref([])
const page = ref(1)
const totalPages = ref(1)
const ord = ref('-created_at')
const captcha = reactive({ key: '', image: '' })
const error = ref('')
const busy = ref(false)
const preview = ref(false)
const lightbox = ref('')
const ta = ref(null)
const formEl = ref(null)
const liveNotice = ref('')
let socket
let reconnectTimer
let shouldReconnect = true

const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
// Escape everything, then restore only the tags allowed by the backend.
const previewHtml = computed(() => esc(f.text)
  .replace(/&lt;(\/?)(i|strong|code)&gt;/g, '<$1$2>')
  .replace(/&lt;a href=&quot;([^"&]*)&quot;( title=&quot;([^"&]*)&quot;)?&gt;/g, '<a href="$1" title="$3">')
  .replace(/&lt;\/a&gt;/g, '</a>')
  .replace(/\n/g, '<br>'))

async function load() {
  try {
    const response = await fetch(`${API}/comments/?page=${page.value}&page_size=${pageSize}&ordering=${ord.value}`)
    if (!response.ok) throw new Error('Failed to load comments')
    const data = await response.json()
    items.value = Array.isArray(data.page?.object_list) ? data.page.object_list : []
    totalPages.value = Number.isInteger(data.num_pages) ? Math.max(data.num_pages, 1) : 1
    if (page.value > totalPages.value) {
      page.value = totalPages.value
      await load()
    }
  } catch (e) {
    items.value = []
    totalPages.value = 1
    error.value = e.message
  }
}

async function loadCaptcha() {
  const response = await fetch(`${API}/captcha/`)
  if (!response.ok) throw new Error('Failed to load CAPTCHA')
  const data = await response.json()
  captcha.key = data.captcha_key
  captcha.image = data.image_url
}

function connectToComments() {
  if (!shouldReconnect) return
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket = new WebSocket(`${protocol}//${window.location.host}/ws/comments/`)
  socket.onmessage = async event => {
    const message = JSON.parse(event.data)
    if (message.id) {
      liveNotice.value = 'A new comment was posted'
      await load()
    }
  }
  socket.onclose = () => {
    reconnectTimer = window.setTimeout(connectToComments, 2000)
  }
}

function sort(k) {
  ord.value = ord.value === '-' + k ? k : '-' + k
  page.value = 1
  load()
}

function goto(p) {
  if (p < 1 || p > totalPages.value || p === page.value) return
  page.value = p
  load()
}

function openLightbox(src) {
  lightbox.value = src
}

function handleLightboxKeydown(event) {
  if (event.key === 'Escape') lightbox.value = ''
}

function wrap(t) {
  const el = ta.value
  const { selectionStart: s, selectionEnd: e } = el
  const open = t === 'a' ? '<a href="" title="">' : `<${t}>`
  f.text = f.text.slice(0, s) + open + f.text.slice(s, e) + `</${t}>` + f.text.slice(e)
  el.focus()
}

function reply(c) {
  parent.value = c
  formEl.value.scrollIntoView({ behavior: 'smooth' })
}

function formatError(data, status) {
  const details = Array.isArray(data?.detail) ? data.detail : []
  if (details.length) {
    return details.map(detail => {
      if (typeof detail === 'string') return detail
      if (detail && typeof detail.msg === 'string') return detail.msg
      return JSON.stringify(detail)
    }).join('\n')
  }
  if (data && typeof data === 'object') {
    return Object.entries(data).map(([key, value]) => {
      const message = Array.isArray(value)
        ? value.map(item => typeof item === 'object' ? item?.msg ?? JSON.stringify(item) : item).join(', ')
        : typeof value === 'object' ? value?.msg ?? JSON.stringify(value) : value
      return `${key}: ${message}`
    }).join('\n')
  }
  return `Server error (${status})`
}

async function send() {
  error.value = ''
  busy.value = true
  const fd = new FormData()
  fd.append('username', f.user_name)
  fd.append('email', f.email)
  fd.append('text', f.text)
  fd.append('captcha_value', f.captcha)
  if (f.home_page) fd.append('homepage', f.home_page)
  fd.append('captcha_key', captcha.key)
  if (parent.value) fd.append('reply_to', parent.value.id)
  if (file.value) fd.append('file', file.value)
  try {
    const r = await fetch(`${API}/comments/`, { method: 'POST', body: fd })
    if (r.ok) {
      Object.assign(f, blank())
      file.value = null
      parent.value = null
      preview.value = false
      formEl.value.reset()
      await load()
    } else {
      const e = await r.json().catch(() => null)
      error.value = formatError(e, r.status)
    }
  } catch {
    error.value = 'Network error'
  }
  busy.value = false
  await loadCaptcha()
}

watch(lightbox, value => {
  document.body.style.overflow = value ? 'hidden' : ''
})

onMounted(() => {
  load()
  loadCaptcha()
  connectToComments()
  window.addEventListener('keydown', handleLightboxKeydown)
})
onUnmounted(() => {
  shouldReconnect = false
  window.clearTimeout(reconnectTimer)
  socket?.close()
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleLightboxKeydown)
})
</script>

<template>
  <div class="max-w-3xl mx-auto p-4 space-y-4">
    <div v-if="liveNotice" class="alert alert-info py-2">
      {{ liveNotice }}
      <button type="button" class="btn btn-xs ml-auto" @click="liveNotice = ''">Close</button>
    </div>

    <form ref="formEl" class="card bg-base-100 shadow p-4 space-y-2" @submit.prevent="send">
      <div v-if="parent" class="alert py-2">
        Replying to {{ parent.username }}
        <button type="button" class="btn btn-xs" @click="parent = null">Cancel</button>
      </div>

      <div class="grid sm:grid-cols-3 gap-2">
        <input v-model="f.user_name" class="input input-sm w-full" placeholder="User Name *" pattern="[A-Za-z0-9]+" required>
        <input v-model="f.email" type="email" class="input input-sm w-full" placeholder="E-mail *" required>
        <input v-model="f.home_page" type="url" class="input input-sm w-full" placeholder="Home page">
      </div>

      <div class="join">
        <button v-for="t in tags" :key="t" type="button" class="btn btn-xs join-item" @click="wrap(t)">[{{ t }}]</button>
      </div>
      <textarea ref="ta" v-model="f.text" class="textarea w-full" rows="4" placeholder="Text *" required />

      <input type="file" accept=".jpg,.jpeg,.png,.gif,.txt" class="file-input file-input-sm w-full"
             @change="file = $event.target.files[0]">

      <div class="flex items-center gap-2">
        <img v-if="captcha.image" :src="captcha.image" class="h-10 rounded cursor-pointer" title="Refresh" @click="loadCaptcha">
        <input v-model="f.captcha" class="input input-sm w-32" placeholder="CAPTCHA *" pattern="[A-Za-z0-9]+" required>
        <button type="button" class="btn btn-sm ml-auto" @click="preview = !preview">Preview</button>
        <button class="btn btn-primary btn-sm" :disabled="busy">Submit</button>
      </div>

      <div v-if="preview" class="border border-base-300 rounded p-2 [&_a]:link" v-html="previewHtml" />
      <div v-if="error" class="alert alert-error py-2 whitespace-pre-line">{{ error }}</div>
    </form>

    <div class="flex flex-wrap gap-2 items-center text-sm">
      <span class="font-medium">Sort by:</span>
      <button v-for="s in sorts" :key="s.k" type="button" class="btn btn-xs"
              :class="{ 'btn-active': ord.replace('-', '') === s.k }" @click="sort(s.k)">
        {{ s.l }} {{ ord === s.k ? '↑' : ord === '-' + s.k ? '↓' : '' }}
      </button>
    </div>

    <CommentItem v-for="c in items" :key="c.id" :c="c" @reply="reply" @open="openLightbox" />
    <p v-if="!items.length" class="text-center opacity-60">No comments yet</p>

    <div v-if="totalPages > 1" class="flex flex-wrap items-center justify-center gap-2" aria-label="Pagination">
      <button type="button" class="btn btn-sm" :disabled="page === 1" @click="goto(page - 1)">
        Previous
      </button>
      <div class="join">
        <button v-for="p in totalPages" :key="p" type="button" class="btn btn-sm join-item"
                :class="{ 'btn-active': p === page }" :aria-current="p === page ? 'page' : undefined"
                @click="goto(p)">
          {{ p }}
        </button>
      </div>
      <button type="button" class="btn btn-sm" :disabled="page === totalPages" @click="goto(page + 1)">
        Next
      </button>
    </div>

    <Transition name="lightbox">
      <div v-if="lightbox"
           class="lightbox" role="dialog" aria-modal="true" aria-label="Image preview"
           @click.self="lightbox = ''">
        <button type="button" class="lightbox-close" aria-label="Close image preview" @click="lightbox = ''">
          <span aria-hidden="true">&times;</span>
        </button>

        <div class="lightbox-content" @click.stop>
          <div class="lightbox-stage">
            <img :src="lightbox" alt="Image preview" class="lightbox-image">
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>
