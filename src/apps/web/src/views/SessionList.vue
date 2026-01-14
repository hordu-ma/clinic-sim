<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getSessions, type Session } from '../api/session';
import { showFailToast } from 'vant';

const router = useRouter();
const sessions = ref<Session[]>([]);
const loading = ref(false);

const loadSessions = async () => {
  loading.value = true;
  try {
    sessions.value = await getSessions();
  } catch (error) {
    showFailToast('加载历史会话失败');
  } finally {
    loading.value = false;
  }
};

const goToChat = (sessionId: string) => {
  router.push(`/chat/${sessionId}`);
};

onMounted(() => {
  loadSessions();
});
</script>

<template>
  <div class="session-list-page">
    <van-nav-bar title="历史会话" left-arrow @click-left="$router.back()" />
    
    <div class="list-container">
        <van-empty v-if="!loading && sessions.length === 0" description="暂无历史会话" />
        
        <van-cell-group v-else>
            <van-cell 
                v-for="session in sessions" 
                :key="session.id"
                :title="`会话 ${session.id.slice(0, 8)}...`"
                :label="`状态: ${session.status} | 创建时间: ${new Date(session.created_at).toLocaleString()}`"
                is-link
                @click="goToChat(session.id)"
            />
        </van-cell-group>
    </div>
  </div>
</template>

<style scoped>
.session-list-page {
  background: #f7f8fa;
  min-height: 100vh;
}
</style>
