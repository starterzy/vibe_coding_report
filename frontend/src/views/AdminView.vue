<template>
  <div>
    <h2>系统管理</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="已审核记录" name="approved">
        <el-table :data="approvedRecords" stripe border>
          <el-table-column prop="task_name" label="工作任务" width="150" show-overflow-tooltip />
          <el-table-column prop="measure_content" label="工作措施" min-width="250" show-overflow-tooltip />
          <el-table-column prop="submitter_name" label="填报人" width="100" />
          <el-table-column prop="month" label="月份" width="80">
            <template #default="{ row }">{{ row.month }}月</template>
          </el-table-column>
          <el-table-column prop="current_content" label="本月工作内容" min-width="200" show-overflow-tooltip />
          <el-table-column prop="next_plan" label="下月工作计划" min-width="200" show-overflow-tooltip />
          <el-table-column prop="reviewed_at" label="审核时间" width="160">
            <template #default="{ row }">
              {{ row.reviewed_at ? new Date(row.reviewed_at).toLocaleString() : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../api/report'

const activeTab = ref('approved')
const approvedRecords = ref([])

async function fetchApprovedRecords() {
  try {
    approvedRecords.value = await reportApi.getRecords({ year: 2026, status_filter: 'approved' })
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchApprovedRecords)
</script>
