<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useUserStore } from "../stores/user";
import {
  getSession,
  applyTest,
  submitDiagnosis,
  type SessionDetail,
  type DiagnosisSubmitResponse,
} from "../api/session";
import { getAvailableTests, type AvailableTestItem } from "../api/cases";
import { showToast, showSuccessToast, showFailToast, showDialog } from "vant";
import type { MessageItem } from "../types";

const route = useRoute();
const userStore = useUserStore();

// Session ID 从路由获取，后端是 int 类型
const sessionId = computed(() => Number(route.params.sessionId));

// UI State
const messages = ref<MessageItem[]>([]);
const inputValue = ref("");
const sending = ref(false);
const loadingData = ref(true);
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
const sessionDetail = ref<SessionDetail | null>(null);

// Diagnosis State
const showDiagnosisDialog = ref(false);
const diagnosisContent = ref("");

// Session status
const isSessionEnded = computed(() => {
  return sessionDetail.value?.status !== "in_progress";
});

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const loadData = async () => {
  loadingData.value = true;
  try {
    // Load session details (includes messages)
    const detail = await getSession(sessionId.value);
    sessionDetail.value = detail;

    // Map messages - role 类型断言为 MessageItem 兼容类型
    messages.value = detail.messages.map((m) => ({
      ...m,
      role: m.role as "user" | "assistant" | "system",
    }));

    // Load available tests
    if (detail.case_id) {
      const testsRes = await getAvailableTests(detail.case_id);
      availableTests.value = testsRes.items || [];
    }

    scrollToBottom();
  } catch (e) {
    showFailToast("加载数据失败");
    console.error(e);
  } finally {
    loadingData.value = false;
  }
};

onMounted(() => {
  loadData();
});

const onSelectAction = (action: { name: string; value: string }) => {
  showActionSheet.value = false;
  if (isSessionEnded.value) {
    showToast("会话已结束，无法进行此操作");
    return;
  }
  if (action.value === "test") {
    showTestPopup.value = true;
  } else if (action.value === "diagnosis") {
    showDiagnosisDialog.value = true;
  }
};

const handleApplyTest = async (testItem: AvailableTestItem) => {
  try {
    const res = await applyTest(sessionId.value, { test_type: testItem.type });

    // 显示检查结果
    const resultStr = Object.entries(res.result || {})
      .map(([k, v]) => `${k}: ${v}`)
      .join("; ");

    messages.value.push({
      id: Date.now(),
      role: "system",
      content: `[检查结果] ${res.test_name}:\n${resultStr || "无异常"}`,
      tokens: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    });

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
    const res: DiagnosisSubmitResponse = await submitDiagnosis(
      sessionId.value,
      {
        diagnosis: diagnosisContent.value,
      },
    );
    showDiagnosisDialog.value = false;

    // Update session status
    if (sessionDetail.value) {
      sessionDetail.value.status = res.status;
    }

    // Show score result in dialog
    const score = res.score;
    await showDialog({
      title: "评分结果",
      message: `
总分: ${score.total_score.toFixed(1)} 分

问诊完整性: ${score.dimensions.interview_completeness.toFixed(1)}
检查合理性: ${score.dimensions.test_appropriateness.toFixed(1)}
诊断准确性: ${score.dimensions.diagnosis_accuracy.toFixed(1)}

覆盖关键点: ${score.scoring_details.key_points_covered.join(", ") || "无"}
标准诊断: ${score.scoring_details.standard_diagnosis}
      `.trim(),
      confirmButtonText: "确定",
    });

    // Add system message
    messages.value.push({
      id: Date.now(),
      role: "system",
      content: `[诊断提交] 总分: ${score.total_score.toFixed(1)} 分`,
      tokens: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    });
    scrollToBottom();
  } catch (e) {
    showFailToast("提交失败");
  }
};

const sendMessage = async () => {
  if (!inputValue.value.trim() || sending.value) return;

  if (isSessionEnded.value) {
    showToast("会话已结束，无法发送消息");
    return;
  }

  const content = inputValue.value.trim();

  // Optimistic UI: add user message
  messages.value.push({
    id: Date.now(),
    role: "user",
    content: content,
    tokens: null,
    latency_ms: null,
    created_at: new Date().toISOString(),
  });
  inputValue.value = "";
  scrollToBottom();

  sending.value = true;

  // Create placeholder for assistant response
  const assistantMsgIndex = messages.value.length;
  messages.value.push({
    id: Date.now() + 1,
    role: "assistant",
    content: "",
    tokens: null,
    latency_ms: null,
    created_at: new Date().toISOString(),
  });

  try {
    const response = await fetch("/api/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        Authorization: `Bearer ${userStore.token}`,
      },
      body: JSON.stringify({
        session_id: sessionId.value,
        message: content,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => null);
      const errMsg = errData?.detail || response.statusText || "请求失败";
      const assistantMsg = messages.value[assistantMsgIndex];
      if (assistantMsg) {
        assistantMsg.content = "请求失败: " + errMsg;
      }
      showFailToast(errMsg);
      return;
    }

    if (!response.body) {
      const assistantMsg = messages.value[assistantMsgIndex];
      if (assistantMsg) {
        assistantMsg.content = "响应体为空，请稍后重试";
      }
      showFailToast("响应体为空，请稍后重试");
      return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let shouldStop = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (!data) continue;
          if (data === "[DONE]") {
            shouldStop = true;
            break;
          }

          try {
            const parsed = JSON.parse(data);
            if (parsed.error) {
              const assistantMsg = messages.value[assistantMsgIndex];
              if (assistantMsg) {
                assistantMsg.content = parsed.error;
              }
              showFailToast(parsed.error);
              shouldStop = true;
              break;
            }

            // system event (e.g. test results)
            if (parsed.role === "system" && parsed.content) {
              messages.value.push({
                id: Date.now(),
                role: "system",
                content: parsed.content,
                tokens: null,
                latency_ms: null,
                created_at: new Date().toISOString(),
              });
              scrollToBottom();
            } else if (parsed.content) {
              const assistantMsg = messages.value[assistantMsgIndex];
              if (assistantMsg) {
                assistantMsg.content += parsed.content;
                scrollToBottom();
              }
            }
            if (parsed.done) {
              shouldStop = true;
              break;
            }
          } catch (e) {
            // Ignore parse errors for partial chunks
          }
        }
      }

      if (shouldStop) break;
    }
  } catch (e) {
    const assistantMsg = messages.value[assistantMsgIndex];
    if (assistantMsg) assistantMsg.content = "网络错误，请重试";
    showFailToast("网络错误，请重试");
  } finally {
    sending.value = false;
    scrollToBottom();
  }
};
</script>

<template>
  <div class="chat-page">
    <van-nav-bar
      :title="sessionDetail?.case_title || '问诊室'"
      left-arrow
      @click-left="$router.back()"
      fixed
      placeholder
    >
      <template #right>
        <van-icon name="ellipsis" size="20" @click="showActionSheet = true" />
      </template>
    </van-nav-bar>

    <!-- Session status banner -->
    <van-notice-bar
      v-if="isSessionEnded"
      color="#1989fa"
      background="#ecf9ff"
      left-icon="info-o"
    >
      会话已{{
        sessionDetail?.status === "submitted" ? "提交" : "评分"
      }}，仅供查看
    </van-notice-bar>

    <!-- Loading -->
    <van-loading v-if="loadingData" class="loading-center" size="24px" vertical>
      加载中...
    </van-loading>

    <div v-else class="message-list" ref="messagesContainer">
      <van-empty v-if="messages.length === 0" description="开始问诊吧" />
      <div
        v-for="(msg, index) in messages"
        :key="msg.id || index"
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

    <div class="input-area" v-if="!isSessionEnded">
      <van-field
        v-model="inputValue"
        center
        clearable
        placeholder="请输入问题"
        @keyup.enter="sendMessage"
      >
        <template #button>
          <van-button
            size="small"
            type="primary"
            :loading="sending"
            :disabled="sending || !inputValue.trim()"
            @click="sendMessage"
          >
            发送
          </van-button>
        </template>
      </van-field>
    </div>

    <!-- Actions -->
    <van-action-sheet
      v-model:show="showActionSheet"
      :actions="actions"
      cancel-text="取消"
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
        <van-empty
          v-if="availableTests.length === 0"
          description="暂无可用检查"
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
  background: #e8f4f8;
}

.loading-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 18px 14px 26px;
}

.message-item {
  display: flex;
  margin-bottom: 22px;
  opacity: 0;
  animation: msgAppear 0.45s ease-out forwards;
}

@keyframes msgAppear {
  0% {
    opacity: 0;
    transform: translateX(-12px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
  animation: msgAppearRight 0.45s ease-out forwards;
}

@keyframes msgAppearRight {
  0% {
    opacity: 0;
    transform: translateX(12px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
  color: #475569;
}

.message-item.user .avatar {
  background: #0369a1;
  color: #e0f2fe;
  margin-left: 11px;
  border: 2px solid #7dd3fc;
}

.message-item.assistant .avatar {
  background: #ea580c;
  color: #ffedd5;
  margin-right: 11px;
  border: 2px solid #fed7aa;
}

.message-item.system {
  justify-content: center;
}

.message-item.system .avatar {
  display: none;
}

.message-item.system .content {
  background: #f1f5f9;
  color: #64748b;
  font-size: 12px;
  max-width: 82%;
  text-align: center;
  padding: 9px 16px;
  border-radius: 14px;
  border: 1px dashed #cbd5e1;
}

.content {
  max-width: 70%;
  background: #ffffff;
  padding: 13px 17px;
  border-radius: 6px 16px 16px 16px;
  word-break: break-word;
  white-space: pre-wrap;
  text-align: left;
  line-height: 1.6;
  font-size: 14.5px;
  border-left: 3px solid #fbbf24;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.12),
    0 1px 2px rgba(0, 0, 0, 0.08);
}

.message-item.user .content {
  background: #0c4a6e;
  color: #e0f2fe;
  border-left: 3px solid #38bdf8;
  border-radius: 16px 6px 16px 16px;
}

.input-area {
  background: #ffffff;
  border-top: 2px solid #cbd5e1;
  padding: 13px 15px;
}

.input-area :deep(.van-field) {
  border-radius: 22px;
  border: 2px solid #cbd5e1;
  background: #f8fafc;
  padding: 9px 18px;
}

.input-area :deep(.van-field:focus-within) {
  border-color: #0284c7;
  background: #ffffff;
}

.input-area :deep(.van-field__control) {
  font-size: 14.5px;
}

.input-area :deep(.van-button--primary) {
  border-radius: 18px;
  padding: 9px 22px;
  background: #0369a1;
  border: none;
  font-weight: 600;
}

.input-area :deep(.van-button--primary:active) {
  background: #075985;
}
</style>
