<template>
  <el-dialog
    :title="isEdit ? '编辑日程' : '新建日程'"
    v-model="dialogVisible"
    :width="dialogWidth"
    :close-on-click-modal="false"
  >
    <el-form :model="form" :rules="rules" ref="formRef" :label-width="labelWidth">
      <el-form-item label="标题" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入日程标题"
          maxlength="100"
        />
      </el-form-item>

      <el-form-item label="星期" prop="weekday">
        <el-select
          v-model="form.weekday"
          placeholder="选择星期"
          style="width: 100%"
        >
          <el-option
            v-for="(name, index) in weekdays"
            :key="index + 1"
            :label="name"
            :value="index + 1"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="时间" required>
        <el-col :span="11">
          <el-form-item prop="start_time">
            <el-time-select
              v-model="form.start_time"
              :max-time="form.end_time"
              placeholder="开始时间"
              start="08:00"
              step="00:15"
              end="22:00"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="2" class="time-separator">-</el-col>
        <el-col :span="11">
          <el-form-item prop="end_time">
            <el-time-select
              v-model="form.end_time"
              :min-time="form.start_time"
              placeholder="结束时间"
              start="08:00"
              step="00:15"
              end="22:30"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-form-item>

      <el-form-item label="启用提醒">
        <el-switch v-model="form.reminder_enabled" />
      </el-form-item>

      <el-form-item label="提前提醒" v-if="form.reminder_enabled">
        <el-input-number
          v-model="form.reminder_minutes"
          :min="1"
          :max="120"
          controls-position="right"
        />
        <span class="input-suffix">分钟</span>
      </el-form-item>

      <el-divider content-position="left">重复设置</el-divider>

      <el-form-item label="每周重复">
        <el-switch v-model="form.is_recurring" />
        <span class="switch-tip">开启后可通过"复制本周到下周"批量创建</span>
      </el-form-item>

      <el-form-item label="截止日期" v-if="form.is_recurring">
        <el-date-picker
          v-model="form.end_date"
          type="date"
          placeholder="选择截止日期（可选）"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
        <div class="form-tip">设置后，超过此日期将不再复制和提醒</div>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="3"
          placeholder="可选填"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button
          v-if="isEdit"
          type="danger"
          @click="handleDelete"
          :loading="deleteLoading"
        >
          删除
        </el-button>
        <div class="right-buttons">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saveLoading">
            保存
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useScheduleStore } from "../stores/schedule";

const props = defineProps({
  visible: Boolean,
  schedule: Object,
  initialWeekday: {
    type: Number,
    default: 1,
  },
  initialStartTime: {
    type: String,
    default: "08:00",
  },
});

const emit = defineEmits(["update:visible", "saved", "deleted"]);

const scheduleStore = useScheduleStore();
const formRef = ref(null);
const saveLoading = ref(false);
const deleteLoading = ref(false);

const weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

// 是否编辑模式
const isEdit = computed(() => !!props.schedule);

// 弹窗显示控制
const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit("update:visible", val),
});

// 移动端适配
const dialogWidth = computed(() => {
  return window.innerWidth <= 768 ? '90%' : '520px'
});

const labelWidth = computed(() => {
  return window.innerWidth <= 768 ? '80px' : '120px'
});

// 表单数据
const form = ref({
  title: "",
  weekday: 1,
  start_time: "08:00",
  end_time: "09:00",
  remark: "",
  reminder_enabled: true,
  reminder_minutes: 10,
  is_recurring: false,
  end_date: null,
});

// 表单验证规则
const rules = {
  title: [
    { required: true, message: "请输入标题", trigger: "blur" },
    { max: 100, message: "最多100个字符", trigger: "blur" },
  ],
  weekday: [{ required: true, message: "请选择星期", trigger: "change" }],
  start_time: [
    { required: true, message: "请选择开始时间", trigger: "change" },
  ],
  end_time: [
    { required: true, message: "请选择结束时间", trigger: "change" },
    {
      validator: (rule, value, callback) => {
        if (value && form.value.start_time && value <= form.value.start_time) {
          callback(new Error("结束时间必须晚于开始时间"));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
};

// 重置表单函数（必须在watch之前定义）
const resetForm = () => {
  // 计算默认结束时间（开始时间+1小时）
  const startParts = props.initialStartTime.split(":");
  const endHour = parseInt(startParts[0]) + 1;
  const endTime = `${endHour.toString().padStart(2, "0")}:${startParts[1]}`;

  form.value = {
    title: "",
    weekday: props.initialWeekday,
    start_time: props.initialStartTime,
    end_time: endTime,
    remark: "",
    reminder_enabled: true,
    reminder_minutes: 10,
    is_recurring: false,
    end_date: null,
  };
};

// 监听schedule变化，初始化表单
watch(
  () => props.schedule,
  (newVal) => {
    if (newVal) {
      form.value = {
        title: newVal.title,
        weekday: newVal.weekday,
        start_time: newVal.start_time,
        end_time: newVal.end_time,
        remark: newVal.remark || "",
        reminder_enabled: newVal.reminder_enabled,
        reminder_minutes: newVal.reminder_minutes,
        is_recurring: newVal.is_recurring || false,
        end_date: newVal.end_date || null,
      };
    } else {
      resetForm();
    }
  },
  { immediate: true },
);

// 监听visible变化，初始化默认值
watch(
  () => props.visible,
  (newVal) => {
    if (newVal && !props.schedule) {
      resetForm();
    }
  },
);

// 保存
const handleSave = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      // 检查时间冲突
      const hasConflict = scheduleStore.hasTimeConflict(
        form.value.weekday,
        form.value.start_time,
        form.value.end_time,
        isEdit.value ? props.schedule.id : null,
      );

      if (hasConflict) {
        ElMessage.error("该时间段与其他日程有冲突，请选择其他时间");
        return;
      }

      saveLoading.value = true;
      try {
        // 处理数据
        const data = {
          ...form.value,
          end_date: form.value.is_recurring
            ? form.value.end_date || null
            : null,
        };

        if (isEdit.value) {
          await scheduleStore.updateSchedule(props.schedule.id, data);
          ElMessage.success("更新成功");
        } else {
          await scheduleStore.createSchedule(data);
          ElMessage.success("创建成功");
        }
        emit("saved");
      } catch (error) {
        ElMessage.error("保存失败");
      } finally {
        saveLoading.value = false;
      }
    }
  });
};

// 删除
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm("确定要删除这个日程吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    deleteLoading.value = true;
    try {
      await scheduleStore.deleteSchedule(props.schedule.id);
      ElMessage.success("删除成功");
      emit("deleted");
    } catch (error) {
      ElMessage.error("删除失败");
    } finally {
      deleteLoading.value = false;
    }
  } catch (error) {
    // 用户取消
  }
};
</script>

<style scoped>
.time-separator {
  text-align: center;
  line-height: 32px;
  color: #909399;
}

.input-suffix {
  margin-left: 8px;
  color: #606266;
}

.switch-tip {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.right-buttons {
  display: flex;
  gap: 12px;
}
</style>
