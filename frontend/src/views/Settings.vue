<template>
  <div class="settings-page">
    <div class="page-header">
      <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
      <h1>系统设置</h1>
      <div class="placeholder"></div>
    </div>

    <div class="settings-container">
      <el-form
        :model="form"
        ref="formRef"
        label-width="160px"
        class="settings-form"
      >
        <el-divider content-position="left">提醒设置</el-divider>

        <el-form-item label="默认提前提醒时长">
          <el-input-number
            v-model="form.default_reminder_minutes"
            :min="1"
            :max="120"
            controls-position="right"
          />
          <span class="input-suffix">分钟</span>
        </el-form-item>

        <el-form-item label="消息前缀文本">
          <el-input
            v-model="form.message_prefix"
            placeholder="可选，如：[KidPlan]"
            maxlength="100"
            show-word-limit
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            添加在消息开头的文本，可用于机器人关键词过滤
          </div>
        </el-form-item>

        <el-divider content-position="left">通知渠道</el-divider>

        <el-form-item label="钉钉机器人 Webhook">
          <el-input
            v-model="form.dingtalk_webhook"
            type="textarea"
            :rows="2"
            placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
          />
          <div class="webhook-actions">
            <el-button
              type="primary"
              size="small"
              :loading="testLoading.dingtalk"
              :disabled="!form.dingtalk_webhook"
              @click="handleTest('dingtalk')"
            >
              <el-icon><Promotion /></el-icon>
              发送测试消息
            </el-button>
          </div>
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            在钉钉群设置中添加机器人，复制Webhook地址
          </div>
        </el-form-item>

        <el-form-item label="飞书机器人 Webhook">
          <el-input
            v-model="form.lark_webhook"
            type="textarea"
            :rows="2"
            placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
          />
          <div class="webhook-actions">
            <el-button
              type="primary"
              size="small"
              :loading="testLoading.lark"
              :disabled="!form.lark_webhook"
              @click="handleTest('lark')"
            >
              <el-icon><Promotion /></el-icon>
              发送测试消息
            </el-button>
          </div>
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            在飞书群设置中添加机器人，复制Webhook地址
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="handleSave" :loading="loading">
            保存设置
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, InfoFilled, Promotion } from '@element-plus/icons-vue'
import { settingsApi } from '../api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const testLoading = ref({
  dingtalk: false,
  lark: false
})

const form = ref({
  default_reminder_minutes: 10,
  message_prefix: '',
  dingtalk_webhook: '',
  lark_webhook: ''
})

// 获取当前设置
const fetchSettings = async () => {
  try {
    const data = await settingsApi.get()
    form.value = {
      default_reminder_minutes: data.default_reminder_minutes || 10,
      message_prefix: data.message_prefix || '',
      dingtalk_webhook: data.dingtalk_webhook || '',
      lark_webhook: data.lark_webhook || ''
    }
  } catch (error) {
    ElMessage.error('获取设置失败')
  }
}

// 保存设置
const handleSave = async () => {
  loading.value = true
  try {
    await settingsApi.update({
      default_reminder_minutes: form.value.default_reminder_minutes,
      message_prefix: form.value.message_prefix || null,
      dingtalk_webhook: form.value.dingtalk_webhook || null,
      lark_webhook: form.value.lark_webhook || null
    })
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

// 测试webhook
const handleTest = async (channel) => {
  const webhook = channel === 'dingtalk' ? form.value.dingtalk_webhook : form.value.lark_webhook

  if (!webhook) {
    ElMessage.warning('请先填写Webhook地址')
    return
  }

  testLoading.value[channel] = true
  try {
    const data = await settingsApi.testWebhook(
      channel,
      webhook,
      form.value.message_prefix
    )
    if (data.success) {
      ElMessage.success('测试消息发送成功，请检查群组消息')
    } else {
      ElMessage.error(`发送失败: ${data.response || '未知错误'}`)
    }
  } catch (error) {
    ElMessage.error('测试发送失败')
  } finally {
    testLoading.value[channel] = false
  }
}

// 返回
const goBack = () => {
  router.push('/')
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.placeholder {
  width: 60px;
}

.settings-container {
  max-width: 800px;
  margin: 24px auto;
  padding: 0 24px;
}

.settings-form {
  background: white;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.input-suffix {
  margin-left: 8px;
  color: #606266;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.webhook-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
</style>
