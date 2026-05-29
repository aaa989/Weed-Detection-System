<template>
  <div class="qa-page">
    <div class="page-header">
      <h1 class="page-title">AI 智能问答</h1>
      <p class="page-subtitle">关于杂草识别检测的任何问题，都可以问我</p>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="chatContainer">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role === 'user' ? 'user-message' : 'ai-message'"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'assistant'"><ChatDotRound /></el-icon>
            <el-icon v-else><User /></el-icon>
          </div>
          <div class="message-content">
            <div v-if="msg.role === 'assistant'" v-html="formatContent(msg.content)"></div>
            <div v-else>{{ msg.content }}</div>
          </div>
        </div>
        <div v-if="loading" class="message ai-message">
          <div class="message-avatar">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="message-content typing">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="question"
          placeholder="请输入你的问题，例如：如何提高杂草检测的准确率？"
          :rows="3"
          type="textarea"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <el-button
          type="primary"
          class="send-btn"
          :loading="loading"
          :disabled="!question.trim()"
          @click="sendMessage"
        >
          {{ loading ? '思考中' : '发送' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { ChatDotRound, User } from "@element-plus/icons-vue";
import request from "@/utils/request";

const question = ref("");
const loading = ref(false);
const chatContainer = ref(null);

const messages = ref([
  {
    role: "assistant",
    content: "你好！我是杂草识别检测AI助手。我可以帮你解答关于杂草种类识别、病虫害检测、检测结果分析等相关问题。请随时向我提问！",
  },
]);

async function sendMessage() {
  const text = question.value.trim();
  if (!text || loading.value) return;

  messages.value.push({ role: "user", content: text });
  question.value = "";
  loading.value = true;

  await nextTick();
  scrollToBottom();

  try {
    const res = await request({
      url: "/qa/chat",
      method: "post",
      data: {
        messages: messages.value.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      },
      timeout: 60000,
    });

    if (res.success && res.data) {
      messages.value.push({ role: "assistant", content: res.data.content });
    } else {
      ElMessage.error(res.message || "AI服务请求失败");
    }
  } catch (error) {
    console.error("QA请求失败:", error);
    ElMessage.error("AI服务请求失败，请稍后重试");
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
}

function formatContent(text) {
  if (!text) return "";
  return text
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.*?)`/g, "<code>$1</code>");
}

onMounted(() => {
  scrollToBottom();
});
</script>

<style scoped lang="scss">
.qa-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }

  .chat-container {
    flex: 1;
    background-color: #ffffff;
    border-radius: 10px;
    box-shadow: var(--card-shadow);
    display: flex;
    flex-direction: column;
    min-height: 0;

    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;

      .message {
        display: flex;
        margin-bottom: 20px;

        .message-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background-color: var(--primary-color);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          flex-shrink: 0;
        }

        .message-content {
          background-color: #f3f4f6;
          padding: 12px 16px;
          border-radius: 0 12px 12px 12px;
          max-width: 70%;
          line-height: 1.6;
          font-size: 14px;

          :deep(code) {
            background: #e5e7eb;
            padding: 2px 6px;
            border-radius: 4px;
          }

          :deep(strong) {
            color: #1a1a1a;
          }
        }

        &.user-message {
          flex-direction: row-reverse;

          .message-avatar {
            margin-right: 0;
            margin-left: 12px;
            background-color: #60a5fa;
          }

          .message-content {
            background-color: var(--primary-light);
            border-radius: 12px 0 12px 12px;
          }
        }

        .typing {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 16px 20px;

          .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #909399;
            animation: blink 1.4s infinite both;

            &:nth-child(2) {
              animation-delay: 0.2s;
            }
            &:nth-child(3) {
              animation-delay: 0.4s;
            }
          }
        }
      }
    }

    .chat-input {
      padding: 20px;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 12px;

      .send-btn {
        width: 100px;
        height: auto;
      }
    }
  }
}

@keyframes blink {
  0%, 80%, 100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}
</style>
