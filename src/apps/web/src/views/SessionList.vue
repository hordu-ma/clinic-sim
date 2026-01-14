<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getSessions, type SessionListItem } from "../api/session";
import { showFailToast } from "vant";

const router = useRouter();
const sessions = ref<SessionListItem[]>([]);
const loading = ref(false);

const loadSessions = async () => {
  loading.value = true;
  try {
    const res = await getSessions();
    sessions.value = res.items;
  } catch (error) {
    showFailToast("加载历史会话失败");
  } finally {
    loading.value = false;
  }
};

const goToChat = (sessionId: number) => {
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
      <van-empty
        v-if="!loading && sessions.length === 0"
        description="暂无历史会话"
      />

      <van-cell-group v-else>
        <van-cell
          v-for="session in sessions"
          :key="session.id"
          :title="session.case_title"
          :label="`状态: ${session.status} | ${new Date(
            session.started_at
          ).toLocaleString()}`"
          is-link
          @click="goToChat(session.id)"
        >
          <template #value>
            <van-tag
              :type="session.status === 'in_progress' ? 'primary' : 'success'"
            >
              {{
                session.status === "in_progress"
                  ? "进行中"
                  : session.status === "submitted"
                  ? "已提交"
                  : "已评分"
              }}
            </van-tag>
          </template>
        </van-cell>
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
