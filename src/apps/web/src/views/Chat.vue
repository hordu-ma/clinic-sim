<script setup lang="ts">
import { ref, nextTick, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useUserStore } from "../stores/user";
import {
  getSession,
  getSessionMessages,
  applyTest,
  submitDiagnosis,
} from "../api/session";
import { getAvailableTests, type AvailableTestItem } from "../api/cases";
import { showToast, showSuccessToast, showFailToast } from "vant";

const route = useRoute();
const userStore = useUserStore();
const sessionId = route.params.sessionId as string;

const messages = ref<any[]>([]);
const inputValue = ref("");
const sending = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);

// Action Sheet State
const showActionSheet = ref(false);
const actions = [
  { name: "申请检查", value: "test" },
  { name: "提交诊断", value: "diagnosis" },
];

// Test Application State
const showTestPopup = ref(false);
const availableTests = ref<AvailableTestItem[]>([]);
const sessionDetail = ref<any>(null);

// Diagnosis State
const showDiagnosisDialog = ref(false);
const diagnosisContent = ref("");

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const loadData = async () => {
  try {
    // Load session details first to get case_id
    sessionDetail.value = await getSession(sessionId);

    // Load available tests
    if (sessionDetail.value?.case_id) {
      const testsRes = await getAvailableTests(sessionDetail.value.case_id);
      availableTests.value = testsRes.items || [];
    }

    // Load message history
    const msgs = await getSessionMessages(sessionId);
    messages.value = msgs.map((m: any) => ({
      ...m,
      role: m.role,
    }));
    scrollToBottom();
  } catch (e) {
    showFailToast("加载数据失败");
  }
};

onMounted(() => {
  loadData();
});

const onSelectAction = (action: any) => {
  showActionSheet.value = false;
  if (action.value === "test") {
    showTestPopup.value = true;
  } else if (action.value === "diagnosis") {
    showDiagnosisDialog.value = true;
  }
};

const handleApplyTest = async (testItem: AvailableTestItem) => {
  try {
    const res = await applyTest(sessionId, { test_type: testItem.type });
    messages.value.push({
      role: "assistant",
      content: `[系统] 已申请 ${testItem.name} 检查，结果已生成。`,
    });
    // Add the specific result message if returned, or re-fetch messages
    if (res && res.content) {
      messages.value.push({
        role: "assistant",
        content: res.content,
      });
    } else {
      // Reload messages to get the new test result message from backend
      const msgs = await getSessionMessages(sessionId);
      messages.value = msgs.map((m: any) => ({
        ...m,
        role: m.role,
      }));
    }
    showTestPopup.value = false;
    scrollToBottom();
    showSuccessToast("申请成功");
  } catch (e) {
    showFailToast("申请失败");
  }
};

const handleSubmitDiagnosis = async () => {
  if (!diagnosisContent.value.trim()) {
    showToast("请输入诊断内容");
    return;
  }
  try {
    const res = await submitDiagnosis(sessionId, {
      diagnosis: diagnosisContent.value,
    });
    showDiagnosisDialog.value = false;

    // Show score result
    if (res) {
      let resultMsg = `诊断已提交。\n得分: ${res.total_score}\n评价: ${res.feedback}`;
      messages.value.push({
        role: "system",
        content: resultMsg,
      });
      scrollToBottom();
    }
  } catch (e) {
    showFailToast("提交失败");
  }
};

const sendMessage = async () => {
  if (!inputValue.value.trim() || sending.value) return;

  const content = inputValue.value.trim();
  messages.value.push({
    role: "user",
    content: content,
  });
  inputValue.value = "";
  scrollToBottom();

  sending.value = true;

  // 创建 assistant 消息占位
  const assistantMsg = ref({
    role: "assistant",
    content: "",
  });
  messages.value.push(assistantMsg.value);

  try {
    const response = await fetch("/api/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${userStore.token}`,
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: content,
      }),
    });

    if (!response.ok) {
      assistantMsg.value.content = "请求失败: " + response.statusText;
      return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") break;

          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              assistantMsg.value.content += parsed.content;
              scrollToBottom();
            }
          } catch (e) {
            console.error("Parse error", e);
          }
        }
      }
    }
  } catch (e) {
    assistantMsg.value.content = "网络错误";
  } finally {
    sending.value = false;
    scrollToBottom();
  }
};
</script>

<template>
  <div class="chat-page">
    <van-nav-bar
      title="问诊室"
      left-arrow
      @click-left="$router.back()"
      fixed
      placeholder
      right-text="操作"
      @click-right="showActionSheet = true"
    />

    <div class="message-list" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-item', msg.role]"
      >
        <div class="avatar">
          <template v-if="msg.role === 'user'">医</template>
          <template v-else-if="msg.role === 'system'">系</template>
          <template v-else>患</template>
        </div>
        <div class="content">{{ msg.content }}</div>
      </div>
    </div>

    <div class="input-area">
      <van-field v-model="inputValue" center clearable placeholder="请输入问题">
        <template #button>
          <van-button
            size="small"
            type="primary"
            :loading="sending"
            @click="sendMessage"
            >发送</van-button
          >
        </template>
      </van-field>
    </div>

    <!-- Actions -->
    <van-action-sheet
      v-model:show="showActionSheet"
      :actions="actions"
      @select="onSelectAction"
    />

    <!-- Test Popup -->
    <van-popup
      v-model:show="showTestPopup"
      position="bottom"
      :style="{ height: '50%' }"
      round
    >
      <van-cell-group title="选择检查项目">
        <van-cell
          v-for="item in availableTests"
          :key="item.type"
          :title="item.name"
          is-link
          @click="handleApplyTest(item)"
        />
      </van-cell-group>
    </van-popup>

    <!-- Diagnosis Dialog -->
    <van-dialog
      v-model:show="showDiagnosisDialog"
      title="提交诊断"
      show-cancel-button
      @confirm="handleSubmitDiagnosis"
    >
      <van-field
        v-model="diagnosisContent"
        rows="3"
        autosize
        label="诊断结论"
        type="textarea"
        placeholder="请输入您的诊断结论..."
      />
    </van-dialog>
  </div>
</template>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f7f8fa;
}
.message-item {
  display: flex;
  margin-bottom: 16px;
}
.message-item.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #eee;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}
.message-item.user .avatar {
  background: #1989fa;
  color: #fff;
  margin-left: 8px;
}
.message-item.assistant .avatar {
  background: #ff976a;
  color: #fff;
  margin-right: 8px;
}
.message-item.system {
  justify-content: center;
}
.message-item.system .avatar {
  display: none;
}
.message-item.system .content {
  background: transparent;
  color: #999;
  font-size: 13px;
  max-width: 90%;
  text-align: center;
}
.content {
  max-width: 70%;
  background: #fff;
  padding: 10px;
  border-radius: 8px;
  word-break: break-all;
  white-space: pre-wrap;
  text-align: left;
}
.message-item.user .content {
  background: #e8f3ff;
}
.input-area {
  background: #fff;
  border-top: 1px solid #eee;
}
</style>
