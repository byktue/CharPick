<template>
  <div class="charpick-app">
    <div class="panel control-panel">
      <h2>🛠️ 提取配置</h2>
      <div class="form-group">
        <label>选择小说：</label>
        <select v-model="selectedFile">
          <option v-for="f in files" :key="f" :value="f">{{ f }}</option>
        </select>
      </div>
      
      <div class="form-group">
        <label>逻辑模板：</label>
        <div class="template-btns">
          <button v-for="t in templates" :key="t.name" @click="currentPrompt = t.prompt">
            {{ t.name }}
          </button>
        </div>
      </div>
      
      <textarea v-model="currentPrompt" rows="8" placeholder="输入 Prompt..."></textarea>
      <button class="primary-btn" @click="runTask" :disabled="!selectedFile">
        🚀 开始批量提取
      </button>

      <div class="log-section">
        <h3>📟 实时终端日志</h3>
        <div class="log-box" ref="logBoxRef">
          <div v-for="(log, idx) in logs" :key="idx" class="log-line">
            {{ log }}
          </div>
          <div v-if="logs.length === 0" class="log-empty">等待任务启动...</div>
        </div>
      </div>
    </div>

    <div class="panel info-panel">
      <h2>🧠 提取结构定义</h2>
      <div class="example-box">
        <div class="section">
          <span class="label">Few-shot 示例</span>
          <p>{{ example.text }}</p>
        </div>
        <div class="section">
          <span class="label">JSON 结构预览</span>
          <pre>{{ JSON.stringify(example.attributes, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue';
import axios from 'axios';

const files = ref([]);
const selectedFile = ref('');
const currentPrompt = ref('提取本章角色的 role behavior (行为) 及 speech (对白)。');
const logs = ref([]);
const logBoxRef = ref(null);
let eventSource = null;
const templates = [
  { name: '言行提取', prompt: '提取本章角色的 role behavior (行为) 及 speech (对白)。' },
  { name: '剧情梗概', prompt: '提取本章的核心 plot_summary 和时间线。' },
  { name: '人设分析', prompt: '基于本章内容，分析主要角色的性格关键词、动机和潜在情绪。' }
];

const example = {
  text: "石野大喊：‘我不信！’，他紧握拳头看向镜子。",
  attributes: { 
    characters: [
      { name: "石野", role_behavior: "握拳看向镜子", speech: "\"我不信！\"" }
    ] 
  }
};

onMounted(async () => {
  try {
    const res = await axios.get('http://localhost:8000/files');
    files.value = res.data;
    if (files.value.length > 0) selectedFile.value = files.value[0];
    
    // 初始化日志连接
    connectLogs();
  } catch (e) {
    console.error("无法连接后端:", e);
    logs.value.push("❌ 错误: 无法连接后端服务，请确认 uvicorn 是否运行。");
  }
});

onUnmounted(() => {
  if (eventSource) eventSource.close();
});

const connectLogs = () => {
  // 建立 SSE 连接
  eventSource = new EventSource('http://localhost:8000/logs');
  
  eventSource.onmessage = (event) => {
    // 收到日志后加入数组
    logs.value.push(event.data);
    // 自动滚动到底部
    nextTick(() => {
      if (logBoxRef.value) {
        logBoxRef.value.scrollTop = logBoxRef.value.scrollHeight;
      }
    });
  };

  eventSource.onerror = () => {
    // 可以在这里处理重连逻辑，或者忽略暂时性断开
    // eventSource.close();
  };
};

const runTask = async () => {
  logs.value = []; // 清空旧日志
  try {
    await axios.post('http://localhost:8000/start-extraction', {
      file_name: selectedFile.value,
      prompt: currentPrompt.value
    });
    // 不需要 alert 了，日志会显示开始
  } catch (error) {
    alert('启动失败: ' + error.message);
  }
};
</script>

<style scoped>
.charpick-app { display: flex; gap: 20px; padding: 20px; font-family: 'Segoe UI', sans-serif; background: #f4f4f9; height: 100vh; box-sizing: border-box; }
.panel { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
.control-panel { flex: 4; } /* 左侧稍微宽一点 */
.info-panel { flex: 3; }

h2, h3 { margin-top: 0; color: #333; }
.form-group { margin-bottom: 15px; }
label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-family: inherit; box-sizing: border-box;}
textarea { resize: vertical; }

.template-btns { display: flex; gap: 8px; flex-wrap: wrap; }
.template-btns button { padding: 6px 12px; background: #e0e0e0; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; transition: background 0.2s; }
.template-btns button:hover { background: #d0d0d0; }

.primary-btn { margin-top: 10px; width: 100%; padding: 12px; background: #42b883; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; transition: background 0.2s; }
.primary-btn:hover { background: #3aa876; }
.primary-btn:disabled { background: #ccc; cursor: not-allowed; }

/* 日志框样式 */
.log-section { margin-top: 20px; flex-grow: 1; display: flex; flex-direction: column; min-height: 0; /* 允许 flex 子项滚动 */ }
.log-box { 
  background: #1e1e1e; 
  color: #00ff00; /* 黑客风绿字 */
  padding: 15px; 
  border-radius: 8px; 
  font-family: 'Consolas', 'Monaco', monospace; 
  font-size: 13px; 
  overflow-y: auto; 
  flex-grow: 1; 
  border: 1px solid #333;
}
.log-line { margin-bottom: 4px; white-space: pre-wrap; word-break: break-all; line-height: 1.4; }
.log-empty { color: #666; font-style: italic; }

.example-box { background: #fafafa; border: 1px dashed #ccc; padding: 15px; border-radius: 8px; }
.label { font-weight: bold; color: #888; font-size: 12px; display: block; margin-bottom: 5px; text-transform: uppercase; }
.section { margin-bottom: 15px; }
pre { background: #272822; color: #f8f8f2; padding: 10px; border-radius: 6px; overflow-x: auto; margin: 0; }
</style>
