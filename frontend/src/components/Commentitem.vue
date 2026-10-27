<script setup>
defineProps({ c: Object })
defineEmits(['reply', 'open'])
</script>

<template>
  <div>
    <div class="card bg-base-100 shadow-sm">
      <div class="bg-base-300 px-3 py-1 text-sm flex gap-2 items-center rounded-t-box">
        <a v-if="c.homepage" :href="c.homepage" target="_blank" rel="noopener noreferrer"
           class="link font-bold" :title="`Open ${c.username}'s home page`">
          {{ c.username }}
        </a>
        <b v-else>{{ c.username }}</b>
        <button type="button" class="btn btn-xs btn-ghost ml-auto" @click="$emit('reply', c)">Reply</button>
      </div>
      <div class="p-3">
        <div class="[&_a]:link [&_code]:font-mono whitespace-pre-wrap" v-html="c.text" />
        <img v-if="c.file_url" :src="c.file_url" :alt="`Attachment from ${c.username}`"
             class="mt-2 max-w-full rounded cursor-zoom-in" @click="$emit('open', c.file_url)">
      </div>
    </div>
    <div v-if="c.children?.length" class="ml-6 mt-2 space-y-2 border-l-2 border-base-300 pl-2">
      <Commentitem v-for="r in c.children" :key="r.id" :c="r"
                   @reply="$emit('reply', $event)" @open="$emit('open', $event)" />
    </div>
  </div>
</template>
