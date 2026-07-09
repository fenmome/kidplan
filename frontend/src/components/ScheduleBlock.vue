<template>
  <div
    class="schedule-block"
    :class="[
      weekdayClass,
      { 'no-reminder': !schedule.reminder_enabled }
    ]"
    :style="blockStyle"
  >
    <div class="schedule-title">{{ schedule.title }}</div>
    <div class="schedule-time">{{ schedule.start_time }} - {{ schedule.end_time }}</div>
    <el-icon v-if="!schedule.reminder_enabled" class="no-reminder-icon">
      <Mute />
    </el-icon>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Mute } from '@element-plus/icons-vue'

const props = defineProps({
  schedule: {
    type: Object,
    required: true
  }
})

// 根据星期几返回对应的CSS类
const weekdayClass = computed(() => {
  const weekday = props.schedule.weekday || 1
  return `weekday-${weekday}`
})

// 计算日程块高度和位置
const blockStyle = computed(() => {
  const startParts = props.schedule.start_time.split(':')
  const endParts = props.schedule.end_time.split(':')

  const startHour = parseInt(startParts[0])
  const startMin = parseInt(startParts[1])
  const endHour = parseInt(endParts[0])
  const endMin = parseInt(endParts[1])

  // 检测是否是移动端
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768
  const hourHeight = isMobile ? 60 : 80 // 移动端每小时60px，桌面端80px

  // 计算持续时间（分钟）
  const duration = (endHour - startHour) * 60 + (endMin - startMin)
  const height = Math.max(duration * (hourHeight / 60), isMobile ? 30 : 40)

  // 计算顶部偏移（如果有分钟偏移）
  const topOffset = startMin * (hourHeight / 60)

  return {
    height: `${height}px`,
    top: `${topOffset}px`
  }
})
</script>

<style scoped>
.schedule-block {
  position: absolute;
  left: 4px;
  right: 4px;
  border-radius: 6px;
  padding: 6px 8px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.schedule-block:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 每天不同的颜色 - 周一到周日 */
.weekday-1 {
  background: #3b82f6; /* 周一 - 蓝色 */
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}
.weekday-1:hover {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.weekday-2 {
  background: #10b981; /* 周二 - 绿色 */
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
}
.weekday-2:hover {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.weekday-3 {
  background: #f59e0b; /* 周三 - 琥珀色 */
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);
}
.weekday-3:hover {
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.weekday-4 {
  background: #f97316; /* 周四 - 橙色 */
  box-shadow: 0 2px 4px rgba(249, 115, 22, 0.3);
}
.weekday-4:hover {
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.4);
}

.weekday-5 {
  background: #ec4899; /* 周五 - 粉色 */
  box-shadow: 0 2px 4px rgba(236, 72, 153, 0.3);
}
.weekday-5:hover {
  box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4);
}

.weekday-6 {
  background: #8b5cf6; /* 周六 - 紫色 */
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
}
.weekday-6:hover {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.weekday-7 {
  background: #ef4444; /* 周日 - 红色 */
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
}
.weekday-7:hover {
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

/* 禁用提醒时显示灰色（优先级最高） */
.schedule-block.no-reminder {
  background: #9ca3af !important;
  box-shadow: 0 2px 4px rgba(156, 163, 175, 0.3) !important;
}

.schedule-block.no-reminder:hover {
  box-shadow: 0 4px 12px rgba(156, 163, 175, 0.4) !important;
}

.schedule-title {
  font-weight: 500;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.schedule-time {
  font-size: 11px;
  opacity: 0.9;
}

.no-reminder-icon {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 12px;
  opacity: 0.7;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .schedule-block {
    left: 2px;
    right: 2px;
    border-radius: 4px;
    padding: 4px 5px;
    font-size: 11px;
  }

  .schedule-title {
    font-size: 11px;
    margin-bottom: 1px;
  }

  .schedule-time {
    font-size: 9px;
  }

  .no-reminder-icon {
    top: 2px;
    right: 2px;
    font-size: 10px;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .schedule-block {
    padding: 3px 4px;
    font-size: 10px;
  }

  .schedule-title {
    font-size: 10px;
  }

  .schedule-time {
    font-size: 8px;
  }
}
</style>
