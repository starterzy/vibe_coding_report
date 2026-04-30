<template>
  <div>
    <h2 class="compact-title">审批管理</h2>
    <el-form inline class="search-form">
      <el-form-item label="月份">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="fetchRecords"
          style="width: 120px"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="statusFilter" @change="fetchRecords">
          <el-option label="全部" value="" />
          <el-option label="已提交" value="submitted" />
          <el-option label="已审核" value="approved" />
          <el-option label="已退回" value="rejected" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table :data="records" stripe border height="calc(100vh - 180px)" class="compact-table">
      <el-table-column prop="task_sequence" label="序号" width="60" align="center" />
      <el-table-column prop="task_target" label="主要目标任务" min-width="200" show-overflow-tooltip />
      <el-table-column prop="submitter_name" label="填报人" width="100" align="center" />
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="本月工作内容" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status === 'approved'" class="cell-text">{{ row.current_content || '-' }}</span>
          <el-input
            v-else
            v-model="row.current_content"
            type="textarea"
            :rows="2"
            placeholder="请输入"
            class="compact-input"
            @change="row._modified = true"
          />
        </template>
      </el-table-column>
      <el-table-column label="下月工作计划" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status === 'approved'" class="cell-text">{{ row.next_plan || '-' }}</span>
          <el-input
            v-else
            v-model="row.next_plan"
            type="textarea"
            :rows="2"
            placeholder="请输入"
            class="compact-input"
            @change="row._modified = true"
          />
        </template>
      </el-table-column>
      <el-table-column prop="submitted_at" label="提交时间" width="160">
        <template #default="{ row }">
          {{ row.submitted_at ? new Date(row.submitted_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right" align="center">
        <template #default="{ row }">
          <template v-if="row.status === 'submitted'">
            <el-button type="success" size="small" @click="approveRecord(row)">通过</el-button>
            <el-button type="danger" size="small" @click="rejectRecord(row)">退回</el-button>
          </template>
          <template v-else-if="row.status === 'approved'">
            <span style="color: #67c23a">已审核</span>
            <br />
            <span style="font-size: 11px; color: #999">审核人: {{ row.reviewer_name }}</span>
          </template>
          <template v-else-if="row.status === 'rejected'">
            <span style="color: #f56c6c">已退回</span>
          </template>
          <template v-else>
            <span style="color: #909399">草稿</span>
          </template>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../api/report'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const statusFilter = ref('')
const records = ref([])

function statusType(status) {
  const map = { draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { draft: '草稿', submitted: '已提交', approved: '已审核', rejected: '已退回' }
  return map[status] || status
}

async function fetchRecords() {
  try {
    const params = { month: selectedMonth.value }
    if (statusFilter.value) {
      params.status_filter = statusFilter.value
    }
    let allRecords = await reportApi.getRecords(params)
    // 审批者只能看到自己有权限审批的记录
    if (authStore.isApprover && !authStore.isAdmin) {
      const sequences = authStore.user?.approver_sequences || []
      allRecords = allRecords.filter(r => sequences.includes(r.task_sequence))
    }
    records.value = allRecords
  } catch (e) {
    console.error(e)
  }
}

async function approveRecord(row) {
  try {
    // 如果有修改，先保存再审核
    if (row._modified) {
      await reportApi.updateRecord(row.id, {
        current_content: row.current_content,
        next_plan: row.next_plan
      })
      row._modified = false
    }
    await reportApi.approveRecord(row.id)
    ElMessage.success('审核通过')
    fetchRecords()
  } catch (e) {
    ElMessage.error('审核失败：' + (e.response?.data?.detail || e.message))
  }
}

async function rejectRecord(row) {
  try {
    await reportApi.rejectRecord(row.id)
    ElMessage.success('已退回')
    fetchRecords()
  } catch (e) {
    ElMessage.error('退回失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(fetchRecords)
</script>

<style scoped>
.compact-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}
.search-form {
  margin-bottom: 8px;
}
.cell-text {
  word-break: break-word;
  white-space: normal;
  font-family: "宋体", "SimSun", serif;
  font-size: 12px;
}
.compact-input textarea {
  font-family: "宋体", "SimSun", serif;
  font-size: 12px;
  line-height: 1.3;
  resize: none;
}
</style>

<style>
.el-table {
  border: 1px solid #dcdfe6;
  font-family: "宋体", "SimSun", serif;
  font-size: 12px;
}
.el-table th {
  background-color: #f5f7fa !important;
  border: 1px solid #dcdfe6;
  padding: 2px 4px;
}
.el-table td {
  border: 1px solid #dcdfe6 !important;
  vertical-align: top;
  padding: 2px 4px;
}
.el-table .cell {
  word-break: break-word !important;
  white-space: normal !important;
  border: none !important;
  padding: 2px 4px;
  font-family: "宋体", "SimSun", serif;
}
.el-table--border .el-table__cell {
  border-right: 1px solid #dcdfe6;
}
</style>