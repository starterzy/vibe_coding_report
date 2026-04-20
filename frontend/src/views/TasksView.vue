<template>
  <div class="tasks-container">
    <h2>工作任务列表</h2>

    <el-form inline class="search-form">
      <el-form-item label="月份">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="fetchData"
        />
      </el-form-item>
      <el-form-item label="序号">
        <el-input v-model="searchSequence" placeholder="输入序号" clearable @input="handleSearch" style="width: 100px" />
      </el-form-item>
      <el-form-item label="目标任务">
        <el-input v-model="searchTarget" placeholder="搜索目标任务" clearable @input="handleSearch" style="width: 200px" />
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="displayData"
      :row-key="getRowKey"
      :span-method="spanMethod"
      stripe
      border
      height="calc(100vh - 220px)"
    >
      <el-table-column prop="sequence" label="序号" width="70" align="center" fixed />
      <el-table-column prop="taskName" label="重点工作" width="120" fixed />
      <el-table-column prop="target" label="主要目标任务" min-width="450" fixed />
      <el-table-column label="牵头领导" min-width="150">
        <template #default="{ row }">
          <div class="line-break">{{ row.leader }}</div>
        </template>
      </el-table-column>
      <el-table-column label="牵头部门" min-width="220">
        <template #default="{ row }">
          <div class="line-break">{{ row.departmentName }}</div>
        </template>
      </el-table-column>
      <el-table-column label="配合部门" min-width="200">
        <template #default="{ row }">
          <div class="line-break">{{ row.partnerDepts }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="deadline" label="完成时间" width="100" align="center" />
      <el-table-column prop="measureContent" label="年度工作措施" min-width="450" />
      <el-table-column label="责任人" min-width="120">
        <template #default="{ row }">
          <div class="line-break">{{ row.personLiable || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="specificMeasures" label="具体举措" min-width="180" />
      <el-table-column label="本月工作内容" min-width="280">
        <template #default="{ row }">
          <span v-if="authStore.isLeader" class="cell-text">{{ row.currentContent || '-' }}</span>
          <span v-else-if="row.status && row.status !== 'draft'" class="cell-text">{{ row.currentContent || '-' }}</span>
          <el-input
            v-else
            v-model="row.currentContent"
            type="textarea"
            :rows="2"
            placeholder="请输入"
            class="fill-input"
          />
        </template>
      </el-table-column>
      <el-table-column label="下月工作计划" min-width="280">
        <template #default="{ row }">
          <span v-if="authStore.isLeader" class="cell-text">{{ row.nextPlan || '-' }}</span>
          <span v-else-if="row.status && row.status !== 'draft'" class="cell-text">{{ row.nextPlan || '-' }}</span>
          <el-input
            v-else
            v-model="row.nextPlan"
            type="textarea"
            :rows="2"
            placeholder="请输入"
            class="fill-input"
          />
        </template>
      </el-table-column>
      <el-table-column label="完成进度" width="120" align="center">
        <template #default="{ row }">
          <span v-if="authStore.isLeader">{{ row.currentProgress || 0 }}%</span>
          <span v-else-if="row.status && row.status !== 'draft'">{{ row.currentProgress || 0 }}%</span>
          <el-input-number
            v-else
            v-model="row.currentProgress"
            :min="0"
            :max="100"
            size="small"
            controls-position="right"
            style="width: 80px"
          />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
<el-table-column v-if="!authStore.isLeader" label="操作" width="160" align="center">
        <template #default="{ row }">
          <template v-if="!row.status || row.status === 'draft'">
            <el-button type="primary" size="small" @click="saveRow(row)">保存</el-button>
            <el-button type="success" size="small" @click="submitRow(row)">提交</el-button>
          </template>
          <template v-else-if="row.status === 'submitted'">
            <span style="color: #909399; font-size: 12px">待审批</span>
          </template>
          <template v-else>
            <span style="color: #67c23a; font-size: 12px">已审核</span>
          </template>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { reportApi } from '../api/report'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const tasks = ref([])
const records = ref({})
const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const searchSequence = ref('')
const searchTarget = ref('')
const loading = ref(false)

function getRowKey(row) {
  return `${row.sequence}`
}

const allData = computed(() => {
  const result = []
  tasks.value.forEach(task => {
    task.measures.forEach(measure => {
      const record = records.value[measure.id]
      result.push({
        sequence: task.sequence,
        taskName: task.name,
        target: task.target,
        leader: task.leader || '',
        departmentName: task.department_name || '',
        partnerDepts: task.partner_depts || '',
        deadline: task.deadline || '',
        measureId: measure.id,
        measureContent: measure.content,
        personLiable: '',
        specificMeasures: '',
        recordId: record?.id,
        currentContent: record?.current_content || '',
        nextPlan: record?.next_plan || '',
        currentProgress: record?.current_progress || 0,
        status: record?.status || null,
        _target: task.target
      })
    })
  })
  return result
})

const displayData = computed(() => {
  let data = allData.value
  if (searchSequence.value) {
    const seq = parseInt(searchSequence.value)
    if (!isNaN(seq)) {
      data = data.filter(row => row.sequence === seq)
    }
  }
  if (searchTarget.value) {
    const keyword = searchTarget.value.toLowerCase()
    data = data.filter(row => row.target.toLowerCase().includes(keyword))
  }
  return data
})

const spanMap = computed(() => {
  const map = {}
  displayData.value.forEach((row, idx) => {
    const key = row.sequence
    if (map[key] === undefined) {
      map[key] = { count: 0, rows: [] }
    }
    map[key].count++
    map[key].rows.push(idx)
  })
  return map
})

function spanMethod({ row, column, rowIndex, columnIndex }) {
  if (columnIndex > 6) return { rowspan: 1, colspan: 1 }

  const key = row.sequence
  const info = spanMap.value[key]
  if (!info) return

  if (rowIndex === info.rows[0]) {
    return { rowspan: info.count, colspan: 1 }
  } else {
    return { rowspan: 0, colspan: 1 }
  }
}

function statusType(status) {
  const map = { draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { draft: '草稿', submitted: '已提交', approved: '已审核', rejected: '已退回' }
  return map[status] || '未填报'
}

async function fetchTasks() {
  try {
    tasks.value = await reportApi.getTasks()
  } catch (e) {
    console.error(e)
  }
}

async function fetchRecords() {
  try {
    const res = await reportApi.getRecords({ month: selectedMonth.value })
    records.value = {}
    res.forEach(r => {
      console.log(r)
      records.value[r.measure_id] = r
    })
  } catch (e) {
    console.error(e)
  }
}

async function fetchData() {
  loading.value = true
  try {
    await Promise.all([fetchTasks(), fetchRecords()])
  } finally {
    loading.value = false
  }
}

async function saveRow(row) {
  try {
    if (row.recordId) {
      await reportApi.updateRecord(row.recordId, {
        current_content: row.currentContent,
        next_plan: row.nextPlan,
        current_progress: row.currentProgress
      })
    } else {
      const res = await reportApi.createRecord({
        measure_id: row.measureId,
        month: selectedMonth.value,
        current_content: row.currentContent,
        next_plan: row.nextPlan,
        current_progress: row.currentProgress
      })
      row.recordId = res.id
    }
    ElMessage.success('保存成功')
    fetchRecords()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  }
}

async function submitRow(row) {
  try {
    if (!row.recordId) {
      const res = await reportApi.createRecord({
        measure_id: row.measureId,
        month: selectedMonth.value,
        current_content: row.currentContent,
        next_plan: row.nextPlan,
        current_progress: row.currentProgress
      })
      row.recordId = res.id
    }
    await reportApi.submitRecord(row.recordId)
    ElMessage.success('提交成功')
    fetchRecords()
  } catch (e) {
    ElMessage.error('提交失败：' + (e.response?.data?.detail || e.message))
  }
}

function handleSearch() {
}

onMounted(fetchData)
</script>

<style scoped>
.tasks-container {
  height: 100%;
}
.search-form {
  margin-bottom: 15px;
}
.line-break {
  white-space: pre-line;
  line-height: 1.5;
}
.cell-text {
  word-break: break-word;
  white-space: normal;
}
.fill-input {
  width: 100%;
}
</style>

<style>
.el-table .cell {
  word-break: break-word !important;
  white-space: normal !important;
}
.el-table td {
  vertical-align: top;
}
</style>
