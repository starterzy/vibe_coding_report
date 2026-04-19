<template>
  <div>
    <h2>系统管理</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="已审核记录" name="approved">
        <el-form inline class="search-form">
          <el-form-item label="月份">
            <el-date-picker
              v-model="selectedMonth"
              type="month"
              format="YYYY-MM"
              value-format="YYYY-MM"
              placeholder="选择月份"
              @change="fetchApprovedRecords"
            />
          </el-form-item>
        </el-form>

        <el-table :data="approvedRecords" stripe border>
          <el-table-column prop="task_sequence" label="序号" width="60" />
          <el-table-column prop="task_name" label="工作任务" width="150" show-overflow-tooltip />
          <el-table-column prop="measure_content" label="工作措施" min-width="250" show-overflow-tooltip />
          <el-table-column prop="submitter_name" label="填报人" width="100" />
          <el-table-column prop="month" label="月份" width="100" />
          <el-table-column prop="current_progress" label="完成进度" width="100">
            <template #default="{ row }">{{ row.current_progress || 0 }}%</template>
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
const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const approvedRecords = ref([])

async function fetchApprovedRecords() {
  try {
    approvedRecords.value = await reportApi.getRecords({
      month: selectedMonth.value,
      status_filter: 'approved'
    })
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchApprovedRecords)
</script>

<style scoped>
.search-form {
  margin-bottom: 15px;
}
</style>
