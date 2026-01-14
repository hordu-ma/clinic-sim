<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { getCaseList } from "../api/cases";
import { createSession } from "../api/session";
import { showLoadingToast } from "vant";

const router = useRouter();
const cases = ref<any[]>([]);
const loading = ref(false);
const finished = ref(false);

const onLoad = async () => {
  if (cases.value.length > 0) return;

  try {
    const res: any = await getCaseList();
    cases.value = res.items || [];
    finished.value = true;
  } catch (e) {
    console.error(e);
    // finished.value = true // Avoid infinite loop on error
    loading.value = false;
  } finally {
    loading.value = false;
  }
};

const onSelectCase = async (item: any) => {
  const toast = showLoadingToast({
    message: "创建会话中...",
    forbidClick: true,
  });

  try {
    const res: any = await createSession({ case_id: item.id });
    toast.close();
    router.push(`/chat/${res.id}`); // 注意：后端返回 session_id 字段可能是 id 或 session_id，需确认。这里假设是 id based on Model
  } catch (e) {
    // error handled in interceptor
  }
};
</script>

<template>
  <div class="case-list-page">
    <van-nav-bar
      title="病例列表"
      right-text="历史会话"
      @click-right="$router.push('/sessions')"
    />

    <van-list
      v-model:loading="loading"
      :finished="finished"
      finished-text="没有更多了"
      @load="onLoad"
    >
      <div
        v-for="item in cases"
        :key="item.id"
        class="case-card"
        @click="onSelectCase(item)"
      >
        <div class="case-title">{{ item.title }}</div>
        <div class="case-tags">
          <van-tag type="primary">{{ item.department }}</van-tag>
          <van-tag plain type="danger" style="margin-left: 5px">{{
            item.difficulty
          }}</van-tag>
        </div>
      </div>
    </van-list>
  </div>
</template>

<style scoped>
.case-list-page {
  background: #f7f8fa;
  min-height: 100vh;
}
.case-card {
  background: #fff;
  padding: 16px;
  margin: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.case-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #323233;
}
</style>
