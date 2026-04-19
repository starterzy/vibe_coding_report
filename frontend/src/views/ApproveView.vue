<template>
  <div>
    <h2>审批管理</h2>
    <el-form inline class="search-form">
      <el-form-item label="月份">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="fetchRecords"
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

    <el-table :data="records" stripe border height="calc(100vh - 220px)">
      <el-table-column prop="task_sequence" label="序号" width="60" align="center" />
      <el-table-column prop="task_name" label="工作任务" min-width="150" show-overflow-tooltip />
      <el-table-column prop="measure_content" label="工作措施" min-width="300" show-overflow-tooltip />
      <el-table-column prop="submitter_name" label="填报人" width="100" align="center" />
      <el-table-column prop="current_progress" label="进度" width="80" align="center">
        <template #default="{ row }">{{ row.current_progress || 0 }}%</template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="本月工作内容" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status === 'approved'" class="cell-text">{{ row.current_content || '-' }}</span>
          <el-input
            v-else
            v-model="row.current_content"
            type="textarea"
            rows="2"
            placeholder="请输入"
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
            rows="2"
            placeholder="请输入"
          />
        </template>
      </el-table-column>
      <el-table-column prop="submitted_at" label="提交时间" width="160">
        <template #default="{ row }">
          {{ row.submitted_at ? new Date(row.submitted_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="{ row }">
          <template v-if="row.status === 'submitted'">
            <el-button type="success" size="small" @click="approveRecord(row)">通过</el-button>
            <el-button type="danger" size="small" @click="rejectRecord(row)">退回</el-button>
          </template>
          <template v-else-if="row.status === 'approved'">
            <span style="color: #67c23a">已审核</span>
            <br />
            <span style="font-size: 12px; color: #999">审核人: {{ row.reviewer_name }}</span>
          </template>
          <template v-else-if="row.status === 'rejected'">
            <span style="color: #f56c6c">已退回</span>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="rejectDialogVisible" title="退回记录" width="400px">
      <el-form>
        <el-form-item label="退回原因">
          <el-input v-model="rejectReason" type="textarea" rows="3" placeholder="请输入退回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认退回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../api/report'
import { ElMessage } from 'element-plus'

const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const statusFilter = ref('')
const records = ref([])
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const currentRejectRow = ref(null)

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

function rejectRecord(row) {
  currentRejectRow.value = row
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

async function confirmReject() {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入退回原因')
    return
  }
  try {
    await reportApi.rejectRecord(currentRejectRow.value.id, { reason: rejectReason.value })
    ElMessage.success('已退回')
    rejectDialogVisible.value = false
    fetchRecords()
  } catch (e) {
    ElMessage.error('退回失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(fetchRecords)
</script>

<style scoped>
.search-form {
  margin-bottom: 15px;
}
.cell-text {
  word-break: break-word;
  white-space: normal;
}
</style>
