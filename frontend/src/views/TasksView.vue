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
      :data="filteredTasks"
      stripe
      border
      height="calc(100vh - 220px)"
      :span-method="spanMethod"
    >
      <el-table-column prop="sequence" label="序号" width="60" />
      <el-table-column prop="taskName" label="重点工作" width="120" show-overflow-tooltip />
      <el-table-column prop="target" label="主要目标任务" min-width="300" show-overflow-tooltip />
      <el-table-column prop="leader" label="牵头领导" width="100" show-overflow-tooltip />
      <el-table-column prop="departmentName" label="牵头部门" width="150" show-overflow-tooltip />
      <el-table-column prop="partnerDepts" label="配合部门" width="120" show-overflow-tooltip />
      <el-table-column prop="deadline" label="完成时间" width="80" />
      <el-table-column prop="measureContent" label="年度工作措施" min-width="350" show-overflow-tooltip />
      <el-table-column prop="personLiable" label="责任人" width="100" />
      <el-table-column prop="specificMeasures" label="具体举措" width="150" />
      <el-table-column label="本月工作内容" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status && row.status !== 'draft'">{{ row.currentContent || '-' }}</span>
          <el-input
            v-else
            v-model="row.currentContent"
            type="textarea"
            rows="2"
            placeholder="请输入"
          />
        </template>
      </el-table-column>
      <el-table-column label="下月工作计划" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status && row.status !== 'draft'">{{ row.nextPlan || '-' }}</span>
          <el-input
            v-else
            v-model="row.nextPlan"
            type="textarea"
            rows="2"
            placeholder="请输入"
          />
        </template>
      </el-table-column>
      <el-table-column label="完成进度" width="120">
        <template #default="{ row }">
          <span v-if="row.status && row.status !== 'draft'">{{ row.currentProgress || 0 }}%</span>
          <el-input-number
            v-else
            v-model="row.currentProgress"
            :min="0"
            :max="100"
            size="small"
            controls-position="right"
            style="width: 100%"
          />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
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
import { ElMessage } from 'element-plus'

const tasks = ref([])
const records = ref({})
const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const searchSequence = ref('')
const searchTarget = ref('')

const tableData = computed(() => {
  const result = []
  tasks.value.forEach(task => {
    task.measures.forEach(measure => {
      const record = records.value[measure.id]
      result.push({
        sequence: task.sequence,
        taskName: task.name,
        target: task.target,
        leader: task.leader,
        departmentName: task.department_name,
        partnerDepts: task.partner_depts,
        deadline: task.deadline,
        measureId: measure.id,
        measureContent: measure.content,
        personLiable: '',  // 暂时为空
        specificMeasures: '',  // 暂时为空
        recordId: record?.id,
        currentContent: record?.current_content || record?.currentContent || '',
        nextPlan: record?.next_plan || record?.nextPlan || '',
        currentProgress: record?.current_progress ?? record?.currentProgress ?? 0,
        status: record?.status || null
      })
    })
  })
  return result
})

const filteredTasks = computed(() => {
  let data = tableData.value
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

// 合并序号、重点工作、主要目标任务列
const spanMethod = ({ row, columnIndex }) => {
  // columnIndex: 0=序号, 1=重点工作, 2=目标任务, 3=牵头领导...
  if (columnIndex === 0 || columnIndex === 1 || columnIndex === 2) {
    const sameSeqRows = tableData.value.filter(r => r.sequence === row.sequence)
    const firstIdx = tableData.value.indexOf(sameSeqRows[0])
    const currentIdx = tableData.value.indexOf(row)
    const rowSpan = sameSeqRows.length

    if (currentIdx === firstIdx) {
      return { rowspan: rowSpan, colspan: 1 }
    }
    return { rowspan: 0, colspan: 1 }
  }
}

function statusType(status) {
  const map = { draft: 'info', submitted: 'warning', approved: 'success' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { draft: '草稿', submitted: '已提交', approved: '已审核' }
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
      records.value[r.measure_id] = r
    })
  } catch (e) {
    console.error(e)
  }
}

async function fetchData() {
  await Promise.all([fetchTasks(), fetchRecords()])
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
  // computed will auto-update
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
</style>
