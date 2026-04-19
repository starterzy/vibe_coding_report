<template>
  <div>
    <h2>工作任务列表</h2>
    <el-table :data="tasks" stripe border row-key="id" default-expand-all>
      <el-table-column prop="sequence" label="序号" width="60" />
      <el-table-column prop="name" label="重点工作" width="150" />
      <el-table-column prop="target" label="主要目标任务" min-width="300" show-overflow-tooltip />
      <el-table-column prop="leader" label="牵头领导" width="120" />
      <el-table-column prop="department_name" label="牵头部门" width="150" />
      <el-table-column prop="partner_depts" label="配合部门" width="120" />
      <el-table-column prop="deadline" label="完成时间" width="100" />
      <el-table-column label="年度工作措施" min-width="400">
        <template #default="{ row }">
          <div v-for="m in row.measures" :key="m.id" style="margin: 5px 0; padding: 5px; background: #f5f7fa; border-radius: 4px">
            <strong>{{ m.person_liable || '待指定' }}：</strong>{{ m.content }}
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../api/report'

const tasks = ref([])

onMounted(async () => {
  try {
    tasks.value = await reportApi.getTasks()
  } catch (e) {
    console.error(e)
  }
})
</script>
