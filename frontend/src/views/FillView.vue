<template>
  <div>
    <h2>月度填报</h2>
    <el-form inline>
      <el-form-item label="月份">
        <el-select v-model="selectedMonth" @change="fetchRecords">
          <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table :data="records" stripe border>
      <el-table-column prop="task_name" label="工作任务" width="150" show-overflow-tooltip />
      <el-table-column prop="measure_content" label="工作措施" min-width="300" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="current_content" label="本月工作内容" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status !== 'draft'">{{ row.current_content || '-' }}</span>
          <el-input
            v-else
            v-model="row.current_content"
            type="textarea"
            rows="2"
            placeholder="请输入本月工作内容"
          />
        </template>
      </el-table-column>
      <el-table-column prop="next_plan" label="下月工作计划" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status !== 'draft'">{{ row.next_plan || '-' }}</span>
          <el-input
            v-else
            v-model="row.next_plan"
            type="textarea"
            rows="2"
            placeholder="请输入下月工作计划"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'draft'">
            <el-button type="primary" size="small" @click="saveRecord(row)">保存</el-button>
            <el-button type="success" size="small" @click="submitRecord(row)">提交</el-button>
          </template>
          <template v-else-if="row.status === 'submitted'">
            <span style="color: #909399">已提交，待审批</span>
          </template>
          <template v-else>
            <span style="color: #67c23a">已审核</span>
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
    records.value = await reportApi.getRecords({ month: selectedMonth.value, year: 2026 })
  } catch (e) {
    console.error(e)
  }
}

async function saveRecord(row) {
  try {
    if (row.id) {
      await reportApi.updateRecord(row.id, {
        current_content: row.current_content,
        next_plan: row.next_plan
      })
    } else {
      await reportApi.createRecord({
        measure_id: row.measure_id,
        month: selectedMonth.value,
        current_content: row.current_content,
        next_plan: row.next_plan
      })
    }
    ElMessage.success('保存成功')
    fetchRecords()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  }
}

async function submitRecord(row) {
  try {
    if (!row.id) {
      await reportApi.createRecord({
        measure_id: row.measure_id,
        month: selectedMonth.value,
        current_content: row.current_content,
        next_plan: row.next_plan
      })
    }
    await reportApi.submitRecord(row.id)
    ElMessage.success('提交成功')
    fetchRecords()
  } catch (e) {
    ElMessage.error('提交失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(fetchRecords)
</script>
