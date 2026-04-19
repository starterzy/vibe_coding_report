<template>
  <div>
    <h2>审批管理</h2>
    <el-form inline>
      <el-form-item label="月份">
        <el-select v-model="selectedMonth" @change="fetchRecords">
          <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="statusFilter" @change="fetchRecords">
          <el-option label="全部" value="" />
          <el-option label="已提交" value="submitted" />
          <el-option label="已审核" value="approved" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table :data="records" stripe border>
      <el-table-column prop="task_name" label="工作任务" width="150" show-overflow-tooltip />
      <el-table-column prop="measure_content" label="工作措施" min-width="250" show-overflow-tooltip />
      <el-table-column prop="submitter_name" label="填报人" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="current_content" label="本月工作内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="next_plan" label="下月工作计划" min-width="200" show-overflow-tooltip />
      <el-table-column prop="submitted_at" label="提交时间" width="160">
        <template #default="{ row }">
          {{ row.submitted_at ? new Date(row.submitted_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'submitted'">
            <el-button type="success" size="small" @click="approveRecord(row)">审核通过</el-button>
          </template>
          <template v-else-if="row.status === 'approved'">
            <span style="color: #67c23a">已审核</span>
            <br />
            <span style="font-size: 12px; color: #999">审核人: {{ row.reviewer_name }}</span>
          </template>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../api/report'
import { ElMessage } from 'element-plus'

const selectedMonth = ref(new Date().getMonth() + 1)
const statusFilter = ref('')
const records = ref([])

function statusType(status) {
  const map = { draft: 'info', submitted: 'warning', approved: 'success' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { draft: '草稿', submitted: '已提交', approved: '已审核' }
  return map[status] || status
}

async function fetchRecords() {
  try {
    const params = { month: selectedMonth.value, year: 2026, status_filter: statusFilter.value }
    records.value = await reportApi.getRecords(params)
  } catch (e) {
    console.error(e)
  }
}

async function approveRecord(row) {
  try {
    await reportApi.approveRecord(row.id)
    ElMessage.success('审核通过')
    fetchRecords()
  } catch (e) {
    ElMessage.error('审核失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(fetchRecords)
</script>
