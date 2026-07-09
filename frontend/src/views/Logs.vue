<template>
  <div class="logs-page">
    <div class="page-header">
      <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
      <h1>提醒日志</h1>
      <div class="placeholder"></div>
    </div>

    <div class="logs-container">
      <el-table
        :data="logs"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="created_at" label="记录时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="schedule_title" label="日程标题" min-width="120" />

        <el-table-column prop="scheduled_time" label="计划提醒时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.scheduled_time) }}
          </template>
        </el-table-column>

        <el-table-column prop="sent_at" label="发送时间" width="160">
          <template #default="{ row }">
            {{ row.sent_at ? formatDateTime(row.sent_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="channel" label="渠道" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.channel" size="small">
              {{ getChannelText(row.channel) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { settingsApi } from '../api'

const router = useRouter()

const logs = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 获取日志列表
const fetchLogs = async () => {
  loading.value = true
  try {
    const offset = (currentPage.value - 1) * pageSize.value
    const data = await settingsApi.getReminderLogs(pageSize.value, offset)
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    console.error('获取日志失败', error)
  } finally {
    loading.value = false
  }
}

// 格式化日期时间
const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    'sent': 'success',
    'failed': 'danger',
    'pending': 'info'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'sent': '已发送',
    'failed': '失败',
    'pending': '待发送'
  }
  return texts[status] || status
}

// 获取渠道文本
const getChannelText = (channel) => {
  const texts = {
    'dingtalk': '钉钉',
    'lark': '飞书'
  }
  return texts[channel] || channel
}

// 分页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchLogs()
}

// 页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchLogs()
}

// 返回
const goBack = () => {
  router.push('/')
}

// 监听分页变化
watch([currentPage, pageSize], () => {
  fetchLogs()
})

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.logs-page {
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

.logs-container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 24px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
