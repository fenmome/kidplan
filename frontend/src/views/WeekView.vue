<template>
  <div class="week-view">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <div class="left-actions">
        <el-button-group>
          <el-button @click="changeWeek(-1)">
            <el-icon><ArrowLeft /></el-icon> 上周
          </el-button>
          <el-button @click="changeWeek(0)">本周</el-button>
          <el-button @click="changeWeek(1)">
            下周 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-button-group>
        <span class="week-range">{{ weekRangeText }}</span>
      </div>

      <div class="right-actions">
        <el-button type="success" @click="handleCopyWeek">
          <el-icon><CopyDocument /></el-icon> 复制本周到下周
        </el-button>
        <el-button type="primary" @click="goToSettings">
          <el-icon><Setting /></el-icon> 设置
        </el-button>
        <el-button @click="goToLogs">
          <el-icon><List /></el-icon> 日志
        </el-button>
        <el-button @click="handleLogout">
          <el-icon><SwitchButton /></el-icon> 退出
        </el-button>
      </div>
    </div>

    <!-- 周视图主体 -->
    <div class="calendar-container">
      <!-- 表头 -->
      <div class="calendar-header">
        <div class="time-column">时间</div>
        <div
          v-for="day in weekDates"
          :key="day.weekday"
          class="day-column"
          :class="{ today: isToday(day.date) }"
        >
          <div class="weekday">{{ weekdays[day.weekday - 1] }}</div>
          <div class="date">{{ day.dateStr }}</div>
        </div>
      </div>

      <!-- 时间网格 -->
      <div class="calendar-body">
        <div v-for="hour in timeSlots" :key="hour" class="time-row">
          <!-- 时间标签 -->
          <div class="time-label">{{ formatHour(hour) }}</div>

          <!-- 7天的格子 -->
          <div
            v-for="day in weekDates"
            :key="day.weekday"
            class="time-cell"
            @click="openCreateModal(day.weekday, hour)"
          >
            <!-- 日程块 -->
            <ScheduleBlock
              v-for="schedule in getSchedulesByDayAndHour(day.weekday, hour)"
              :key="schedule.id"
              :schedule="schedule"
              @click.stop="openEditModal(schedule)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 日程编辑弹窗 -->
    <ScheduleModal
      v-model:visible="modalVisible"
      :schedule="editingSchedule"
      :initial-weekday="initialWeekday"
      :initial-start-time="initialStartTime"
      @saved="handleSaved"
      @deleted="handleDeleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, CopyDocument, Setting, List, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useScheduleStore } from '../stores/schedule'
import ScheduleBlock from '../components/ScheduleBlock.vue'
import ScheduleModal from '../components/ScheduleModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()

// 配置项：日程开始时间和结束时间（小时）
const SCHEDULE_CONFIG = {
  startHour: 8,    // 8点开始
  endHour: 22      // 22点结束
}

// 时间槽（8:00 - 22:00）
const timeSlots = Array.from(
  { length: SCHEDULE_CONFIG.endHour - SCHEDULE_CONFIG.startHour + 1 },
  (_, i) => i + SCHEDULE_CONFIG.startHour
)

// 弹窗状态
const modalVisible = ref(false)
const editingSchedule = ref(null)
const initialWeekday = ref(1)
const initialStartTime = ref('08:00')

// 计算属性
const weekDates = computed(() => scheduleStore.weekDates)
const weekdays = computed(() => scheduleStore.weekdays)
const weekRangeText = computed(() => {
  if (weekDates.value.length === 0) return ''
  const start = weekDates.value[0]
  const end = weekDates.value[6]
  return `${start.date.getFullYear()}年${start.dateStr} - ${end.dateStr}`
})

// 是否今天
const isToday = (date) => {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

// 格式化小时
const formatHour = (hour) => {
  return `${hour.toString().padStart(2, '0')}:00`
}

// 获取某天的日程
const getSchedulesByDayAndHour = (weekday, hour) => {
  const schedules = scheduleStore.schedulesByWeekday[weekday] || []
  return schedules.filter(s => {
    const startHour = parseInt(s.start_time.split(':')[0])
    return startHour === hour
  })
}

// 切换周
const changeWeek = (offset) => {
  scheduleStore.setWeekOffset(offset)
  scheduleStore.fetchSchedules()
}

// 打开创建弹窗
const openCreateModal = (weekday, hour) => {
  editingSchedule.value = null
  initialWeekday.value = weekday
  initialStartTime.value = `${hour.toString().padStart(2, '0')}:00`
  modalVisible.value = true
}

// 打开编辑弹窗
const openEditModal = (schedule) => {
  editingSchedule.value = schedule
  modalVisible.value = true
}

// 保存成功
const handleSaved = () => {
  modalVisible.value = false
  scheduleStore.fetchSchedules()
}

// 删除成功
const handleDeleted = () => {
  modalVisible.value = false
  scheduleStore.fetchSchedules()
}

// 复制本周到下周
const handleCopyWeek = async () => {
  try {
    await ElMessageBox.confirm('确定要复制本周所有日程到下周吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const result = await scheduleStore.copyToNextWeek()
    ElMessage.success(`成功复制 ${result.copied_count} 条日程到下周`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('复制失败')
    }
  }
}

// 跳转到设置
const goToSettings = () => {
  router.push('/settings')
}

// 跳转到日志
const goToLogs = () => {
  router.push('/logs')
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// 初始化
onMounted(() => {
  scheduleStore.fetchSchedules()
})
</script>

<style scoped>
.week-view {
  min-height: 100vh;
  background: #f5f7fa;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.left-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.week-range {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.right-actions {
  display: flex;
  gap: 8px;
}

.calendar-container {
  padding: 20px;
  overflow-x: auto;
}

.calendar-header {
  display: flex;
  background: white;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid #e4e7ed;
}

.time-column {
  width: 80px;
  padding: 16px;
  font-weight: 500;
  color: #606266;
  border-right: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.day-column {
  flex: 1;
  min-width: 120px;
  padding: 12px;
  text-align: center;
  border-right: 1px solid #e4e7ed;
}

.day-column:last-child {
  border-right: none;
}

.day-column.today {
  background: #ecf5ff;
}

.day-column.today .weekday {
  color: #409eff;
}

.weekday {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.date {
  font-size: 12px;
  color: #909399;
}

.calendar-body {
  background: white;
  border-radius: 0 0 8px 8px;
}

.time-row {
  display: flex;
  border-bottom: 1px solid #ebeef5;
  min-height: 80px;
}

.time-row:last-child {
  border-bottom: none;
}

.time-label {
  width: 80px;
  padding: 8px;
  font-size: 12px;
  color: #909399;
  border-right: 1px solid #e4e7ed;
  flex-shrink: 0;
  text-align: center;
}

.time-cell {
  flex: 1;
  min-width: 120px;
  border-right: 1px solid #ebeef5;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}

.time-cell:last-child {
  border-right: none;
}

.time-cell:hover {
  background: #f5f7fa;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px;
  }

  .left-actions,
  .right-actions {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .right-actions .el-button {
    padding: 8px 12px;
    font-size: 13px;
  }

  .week-range {
    font-size: 14px;
  }

  .calendar-container {
    padding: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .calendar-header {
    min-width: 600px;
  }

  .calendar-body {
    min-width: 600px;
  }

  .time-column,
  .time-label {
    width: 45px;
    padding: 6px 4px;
    font-size: 11px;
  }

  .day-column {
    min-width: 80px;
    padding: 8px 4px;
  }

  .weekday {
    font-size: 13px;
  }

  .date {
    font-size: 10px;
  }

  .time-cell {
    min-width: 80px;
  }

  .time-row {
    min-height: 60px;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .calendar-header,
  .calendar-body {
    min-width: 520px;
  }

  .day-column {
    min-width: 65px;
  }

  .time-cell {
    min-width: 65px;
  }
}
</style>
