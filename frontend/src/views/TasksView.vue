<template>
  <div class="tasks-container">
    <h2 class="compact-title">工作任务列表</h2>

    <el-form inline class="search-form compact-search">
      <el-form-item label="月份">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="fetchData"
          style="width: 120px"
        />
      </el-form-item>
      <el-form-item label="序号">
        <el-input v-model="searchSequence" placeholder="序号" clearable @input="handleSearch" style="width: 70px" />
      </el-form-item>
      <el-form-item label="目标">
        <el-input v-model="searchTarget" placeholder="搜索目标" clearable @input="handleSearch" style="width: 150px" />
      </el-form-item>
      <el-form-item label="责任人">
        <el-input v-model="searchPersonLiable" placeholder="责任人" clearable @input="handleSearch" style="width: 110px" />
      </el-form-item>
      <el-form-item label="部门">
        <el-input v-model="searchDepartment" placeholder="部门" clearable @input="handleSearch" style="width: 120px" />
      </el-form-item>
      <el-form-item>
        <el-button type="success" @click="handleExport">全表导出</el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="displayData"
      :row-key="getRowKey"
      :span-method="spanMethod"
      stripe
      border
      height="calc(100vh - 130px)"
      class="compact-table"
    >
      <!-- 列0-6: 按 measure 分行，task 内合并 -->
      <el-table-column prop="sequence" label="序号" width="40" align="center" fixed />
      <el-table-column prop="taskName" label="重点工作" width="90" fixed />
      <el-table-column prop="target" label="主要目标任务" min-width="180" fixed />
      <el-table-column label="牵头领导" min-width="35">
        <template #default="{ row }">
          <div class="line-break compact-cell">{{ row.leader }}</div>
        </template>
      </el-table-column>
      <el-table-column label="牵头部门" min-width="35">
        <template #default="{ row }">
          <div class="line-break compact-cell">{{ row.departmentName }}</div>
        </template>
      </el-table-column>
      <el-table-column label="配合部门" min-width="35">
        <template #default="{ row }">
          <div class="line-break compact-cell">{{ row.partnerDepts }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="deadline" label="完成时间" width="40" align="center" />

      <!-- 列7-9: 每 measure 一行 -->
      <el-table-column prop="measureContent" label="年度工作措施" min-width="400" />
      <el-table-column label="责任人" min-width="35">
        <template #default="{ row }">
          <div class="line-break compact-cell">{{ row.personLiable || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="specificMeasures" label="具体举措" min-width="150" />

      <!-- 列10-11: 本月/下月 - 按 task 合并显示 -->
      <el-table-column label="本月工作内容" min-width="300">
        <template #default="{ row }">
          <template v-if="row._isFirstRow">
            <span v-if="authStore.isLeader" class="cell-text">{{ row.currentContent || '-' }}</span>
            <span v-else-if="row.status && row.status !== 'draft'" class="cell-text">{{ row.currentContent || '-' }}</span>
            <el-input
              v-else
              v-model="row.currentContent"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 20 }"
              placeholder="请输入"
              class="fill-input compact-input"
              @change="handleContentChange(row)"
            />
          </template>
        </template>
      </el-table-column>
      <el-table-column label="下月工作计划" min-width="300">
        <template #default="{ row }">
          <template v-if="row._isFirstRow">
            <span v-if="authStore.isLeader" class="cell-text">{{ row.nextPlan || '-' }}</span>
            <span v-else-if="row.status && row.status !== 'draft'" class="cell-text">{{ row.nextPlan || '-' }}</span>
            <el-input
              v-else
              v-model="row.nextPlan"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 20 }"
              placeholder="请输入"
              class="fill-input compact-input"
              @change="handleContentChange(row)"
            />
          </template>
        </template>
      </el-table-column>

      <!-- 列12: 状态 - 按 task 合并 -->
      <el-table-column label="状态" width="70" align="center">
        <template #default="{ row }">
          <template v-if="row._isFirstRow">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </template>
      </el-table-column>

      <!-- 列13: 操作 - 按 task 合并 -->
      <el-table-column v-if="!authStore.isLeader" label="操作" width="140" align="center">
        <template #default="{ row }">
          <template v-if="row._isFirstRow">
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
const records = ref({})  // records[measureId] -> record (旧) / records[taskId] -> record (新)
const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const searchSequence = ref('')
const searchTarget = ref('')
const searchPersonLiable = ref('')
const searchDepartment = ref('')
const loading = ref(false)
const searchVersion = ref(0)
const exportDialogVisible = ref(false)
const selectedColumns = ref(['sequence', 'taskName', 'target', 'leader', 'departmentName', 'partnerDepts', 'deadline', 'measureContent', 'personLiable', 'specificMeasures', 'currentContent', 'nextPlan'])

function getRowKey(row) {
  return `${row.measureId}`
}

const allData = computed(() => {
  const result = []
  tasks.value.forEach(task => {
    const taskRecord = records.value[task.id]  // 按 task_id 获取记录
    task.measures.forEach((measure, measureIndex) => {
      result.push({
        sequence: task.sequence,
        taskId: task.id,
        taskName: task.name,
        target: task.target,
        leader: task.leader || '',
        departmentName: task.department_name || '',
        partnerDepts: task.partner_depts || '',
        deadline: task.deadline || '',
        measureId: measure.id,
        measureContent: measure.content,
        personLiable: measure.person_liable || '',
        specificMeasures: '',
        // 填报内容从 task 级别记录获取
        recordId: taskRecord?.id,
        currentContent: taskRecord?.current_content || '',
        nextPlan: taskRecord?.next_plan || '',
        status: taskRecord?.status || null,
        // 标记是否为该 task 的第一行（用于合并单元格）
        _isFirstRow: measureIndex === 0,
        _modified: false
      })
    })
  })
  return result
})

const displayData = computed(() => {
  searchVersion.value
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
  if (searchPersonLiable.value) {
    const keyword = searchPersonLiable.value.toLowerCase()
    data = data.filter(row => row.personLiable && row.personLiable.toLowerCase().includes(keyword))
  }
  if (searchDepartment.value) {
    const keyword = searchDepartment.value.toLowerCase()
    data = data.filter(row => row.departmentName && row.departmentName.toLowerCase().includes(keyword))
  }
  return data
})

// 用于合并计算的 map
const spanMap = computed(() => {
  const map = {}
  displayData.value.forEach((row, idx) => {
    const key = row.taskId
    if (map[key] === undefined) {
      map[key] = { count: 0, rows: [], firstRow: null }
    }
    map[key].count++
    map[key].rows.push(idx)
    if (row._isFirstRow) {
      map[key].firstRow = idx
    }
  })
  return map
})

// spanMethod: 处理列合并
// columnIndex:
// 0-6: 按 task 合并（task 内所有 measure 行合并）
// 7-9: 每 measure 一行（不合并）
// 10-13: 按 task 合并（第一个 measure 行显示，其余隐藏）
function spanMethod({ row, column, rowIndex, columnIndex }) {
  const taskInfo = spanMap.value[row.taskId]
  if (!taskInfo) return { rowspan: 1, colspan: 1 }

  // 列 0-6 (sequence, taskName, target, leader, department, partner, deadline): 按 task 合并
  if (columnIndex <= 6) {
    if (rowIndex === taskInfo.firstRow) {
      return { rowspan: taskInfo.count, colspan: 1 }
    } else {
      return { rowspan: 0, colspan: 1 }
    }
  }

  // 列 7-9 (measureContent, personLiable, specificMeasures): 每 measure 一行，不合并
  if (columnIndex >= 7 && columnIndex <= 9) {
    return { rowspan: 1, colspan: 1 }
  }

  // 列 10-13 (currentContent, nextPlan, status, actions): 按 task 合并
  if (columnIndex >= 10) {
    if (row._isFirstRow) {
      return { rowspan: taskInfo.count, colspan: 1 }
    } else {
      return { rowspan: 0, colspan: 1 }
    }
  }

  return { rowspan: 1, colspan: 1 }
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
    // records 按 task_id 存储
    const newRecords = {}
    res.forEach(r => {
      newRecords[r.task_id] = r
    })
    records.value = newRecords
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

function handleContentChange(row) {
  row._modified = true
  // 同步更新同 task 的其他行（如果有的话）
  const sameTaskRows = allData.value.filter(r => r.taskId === row.taskId && r.measureId !== row.measureId)
  sameTaskRows.forEach(r => {
    r.currentContent = row.currentContent
    r.nextPlan = row.nextPlan
  })
}

async function saveRow(row) {
  try {
    if (row.recordId) {
      await reportApi.updateRecord(row.recordId, {
        current_content: row.currentContent,
        next_plan: row.nextPlan
      })
    } else {
      const res = await reportApi.createRecord({
        task_id: row.taskId,
        month: selectedMonth.value,
        current_content: row.currentContent,
        next_plan: row.nextPlan
      })
      row.recordId = res.id
      // 同步更新其他行
      allData.value.forEach(r => {
        if (r.taskId === row.taskId) {
          r.recordId = res.id
        }
      })
    }
    ElMessage.success('保存成功')
    fetchRecords()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  }
}

async function submitRow(row) {
  try {
    // 先保存
    if (!row.recordId) {
      const res = await reportApi.createRecord({
        task_id: row.taskId,
        month: selectedMonth.value,
        current_content: row.currentContent,
        next_plan: row.nextPlan
      })
      row.recordId = res.id
      allData.value.forEach(r => {
        if (r.taskId === row.taskId) {
          r.recordId = res.id
        }
      })
    } else {
      await reportApi.updateRecord(row.recordId, {
        current_content: row.currentContent,
        next_plan: row.nextPlan
      })
    }

    // 提交
    await reportApi.submitRecord(row.recordId)
    ElMessage.success('提交成功')
    fetchRecords()
  } catch (e) {
    ElMessage.error('提交失败：' + (e.response?.data?.detail || e.message))
  }
}

function handleSearch() {
  searchVersion.value++
}

async function handleExport() {
  try {
    const response = await reportApi.exportRecords({
      month: selectedMonth.value
    })

    const blob = response
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `任务列表_${selectedMonth.value}.xlsx`
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (e) {
    console.error('Export error:', e)
    ElMessage.error('导出失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(fetchData)
</script>

<style scoped>
.tasks-container {
  height: 100%;
}
.compact-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
}
.search-form {
  margin-bottom: 4px;
}
.search-form .el-form-item {
  margin-bottom: 0;
}
.compact-search .el-input__wrapper,
.compact-search .el-date-editor {
  padding: 0 8px;
}
.line-break {
  white-space: pre-line;
  line-height: 1.3;
}
.compact-cell {
  font-family: "宋体", "SimSun", serif;
  font-size: 12px;
  line-height: 1.3;
}
.cell-text {
  word-break: break-word;
  white-space: normal;
  font-family: "宋体", "SimSun", serif;
  font-size: 12px;
  line-height: 1.3;
}
.fill-input {
  width: 100%;
}
.compact-input {
  display: block;
  width: 100%;
}
.compact-input textarea {
  font-family: "宋体", "SimSun", serif;
  font-size: 12px;
  line-height: 1.3;
  resize: none;
  width: 100%;
  height: 100%;
  min-height: 24px;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: break-word;
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
  padding: 0 2px;
}
.el-table th .cell {
  padding: 0 1px;
  line-height: 1.3;
}
.el-table td {
  border: 1px solid #dcdfe6 !important;
  vertical-align: top;
  padding: 0;
}
.el-table .cell {
  word-break: break-word !important;
  white-space: normal !important;
  border: none !important;
  padding: 0;
  font-family: "宋体", "SimSun", serif;
  line-height: 1.3;
}
.el-table .cell::before {
  display: none;
}
.el-table--border .el-table__cell {
  border-right: 1px solid #dcdfe6;
}
.compact-table .el-input {
  display: block;
  width: 100%;
}
.compact-table .el-input__wrapper {
  padding: 0;
  width: 100%;
}
.compact-table .el-textarea {
  display: block;
  width: 100%;
}
.compact-table .el-textarea__inner {
  padding: 0;
  line-height: 1.3;
  width: 100%;
  display: block;
}
</style>