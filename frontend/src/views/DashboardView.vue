<template>
  <div>
    <h2>欢迎使用报表系统</h2>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card>
          <template #header>任务总数</template>
          <div style="font-size: 30px; text-align: center">{{ stats.totalTasks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>本月已填报</template>
          <div style="font-size: 30px; text-align: center">{{ stats.filledThisMonth }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>待审批</template>
          <div style="font-size: 30px; text-align: center">{{ stats.pendingApproval }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>已完成</template>
          <div style="font-size: 30px; text-align: center">{{ stats.approved }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>当前月份填报状态</template>
      <el-table :data="monthlyStats" stripe>
        <el-table-column prop="month" label="月份" width="100" />
        <el-table-column prop="total" label="总措施数" width="120" />
        <el-table-column prop="draft" label="草稿" width="100" />
        <el-table-column prop="submitted" label="已提交" width="100" />
        <el-table-column prop="approved" label="已审核" width="100" />
        <el-table-column label="进度">
          <template #default="{ row }">
            <el-progress :percentage="row.total ? Math.round(row.approved / row.total * 100) : 0" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { reportApi } from '../api/report'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const tasks = ref([])
const records = ref([])

const stats = computed(() => {
  const totalMeasures = tasks.value.reduce((sum, t) => sum + t.measures.length, 0)
  const currentMonth = new Date().getMonth() + 1
  const filledThisMonth = records.value.filter(r => r.month === currentMonth && r.status !== 'draft').length
  const pendingApproval = records.value.filter(r => r.status === 'submitted').length
  const approved = records.value.filter(r => r.status === 'approved').length
  return { totalTasks: tasks.value.length, filledThisMonth, pendingApproval, approved }
})

const monthlyStats = computed(() => {
  const months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  return months.map(m => {
    const monthRecords = records.value.filter(r => r.month === m)
    return {
      month: `${m}月`,
      total: tasks.value.reduce((sum, t) => sum + t.measures.length, 0),
      draft: monthRecords.filter(r => r.status === 'draft').length,
      submitted: monthRecords.filter(r => r.status === 'submitted').length,
      approved: monthRecords.filter(r => r.status === 'approved').length
    }
  })
})

onMounted(async () => {
  try {
    tasks.value = await reportApi.getTasks()
    records.value = await reportApi.getRecords({ year: 2026 })
  } catch (e) {
    console.error(e)
  }
})
</script>
