import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { scheduleApi } from '../api'

export const useScheduleStore = defineStore('schedule', () => {
  // State
  const schedules = ref([])
  const currentWeekOffset = ref(0)
  const weekDates = ref([])

  // 星期几名称映射
  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

  // Getters
  const schedulesByWeekday = computed(() => {
    const result = {}
    for (let i = 1; i <= 7; i++) {
      result[i] = schedules.value.filter(s => s.weekday === i)
    }
    return result
  })

  // 计算周日期
  function calculateWeekDates(offset = 0) {
    const dates = []
    const today = new Date()
    const currentDay = today.getDay() || 7 // 将周日(0)转为7
    const monday = new Date(today)
    monday.setDate(today.getDate() - currentDay + 1 + offset * 7)

    for (let i = 0; i < 7; i++) {
      const date = new Date(monday)
      date.setDate(monday.getDate() + i)
      dates.push({
        weekday: i + 1,
        date: date,
        dateStr: `${date.getMonth() + 1}/${date.getDate()}`
      })
    }
    weekDates.value = dates
    return dates
  }

  // Actions
  async function fetchSchedules() {
    const data = await scheduleApi.getList(currentWeekOffset.value)
    schedules.value = data || []
    calculateWeekDates(currentWeekOffset.value)
    return schedules.value
  }

  async function createSchedule(scheduleData) {
    const data = await scheduleApi.create(scheduleData)
    await fetchSchedules()
    return data
  }

  async function updateSchedule(id, scheduleData) {
    const data = await scheduleApi.update(id, scheduleData)
    await fetchSchedules()
    return data
  }

  async function deleteSchedule(id) {
    await scheduleApi.delete(id)
    await fetchSchedules()
  }

  async function copyToNextWeek() {
    const data = await scheduleApi.copyToNextWeek()
    return data
  }

  function setWeekOffset(offset) {
    currentWeekOffset.value = offset
    calculateWeekDates(offset)
  }

  return {
    schedules,
    currentWeekOffset,
    weekDates,
    weekdays,
    schedulesByWeekday,
    fetchSchedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    copyToNextWeek,
    setWeekOffset
  }
})

