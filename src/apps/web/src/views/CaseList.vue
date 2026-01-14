<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { getCaseList, type CaseListItem } from "../api/cases";
import { createSession } from "../api/session";
import { showLoadingToast, showFailToast } from "vant";

const router = useRouter();
const cases = ref<CaseListItem[]>([]);
const loading = ref(false);
const finished = ref(false);

const onLoad = async () => {
  if (cases.value.length > 0) {
    finished.value = true;
    loading.value = false;
    return;
  }

  try {
    // 后端返回数组，不是 { items: [...] }
    const res = await getCaseList();
    cases.value = res;
    finished.value = true;
  } catch (e) {
    console.error(e);
    showFailToast("加载病例失败");
  } finally {
    loading.value = false;
  }
};

const onSelectCase = async (item: CaseListItem) => {
  const toast = showLoadingToast({
    message: "创建会话中...",
    forbidClick: true,
  });

  try {
    const res = await createSession({ case_id: item.id });
    toast.close();
    router.push(`/chat/${res.id}`);
  } catch (e) {
    toast.close();
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
