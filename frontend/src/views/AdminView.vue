<template>
  <div>
    <h2>系统管理</h2>
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
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
          <el-table-column prop="task_sequence" label="序号" width="70" />
          <el-table-column prop="task_name" label="工作任务" min-width="200" show-overflow-tooltip />
          <el-table-column prop="measure_content" label="工作措施" min-width="400" show-overflow-tooltip />
          <el-table-column prop="submitter_name" label="填报人" width="120" />
          <el-table-column prop="month" label="月份" width="120" />
          <el-table-column prop="current_progress" label="完成进度" width="100">
            <template #default="{ row }">{{ row.current_progress || 0 }}%</template>
          </el-table-column>
          <el-table-column prop="current_content" label="本月工作内容" min-width="280" show-overflow-tooltip />
          <el-table-column prop="next_plan" label="下月工作计划" min-width="280" show-overflow-tooltip />
          <el-table-column prop="reviewed_at" label="审核时间" width="180">
            <template #default="{ row }">
              {{ row.reviewed_at ? new Date(row.reviewed_at).toLocaleString() : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-form inline class="search-form">
          <el-form-item>
            <el-button type="primary" @click="openUserDialog()">新增用户</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="users" stripe border v-loading="loading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="phone" label="手机号" width="140" />
          <el-table-column prop="roles" label="角色" width="120">
            <template #default="{ row }">
              <el-tag v-for="role in row.roles" :key="role" size="small" type="info">{{ roleText(role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="departments" label="部门" min-width="200">
            <template #default="{ row }">
              <span>{{ row.departments.join(', ') || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="approver_sequences" label="可审批序号" width="150">
            <template #default="{ row }">
              <span>{{ row.approver_sequences?.join(', ') || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="openUserDialog(row)">编辑</el-button>
              <el-button v-if="row.is_active" type="danger" size="small" @click="toggleUserStatus(row)">停用</el-button>
              <el-button v-else type="success" size="small" @click="toggleUserStatus(row)">启用</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="userDialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="600px">
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="userForm.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item :label="isEdit ? '新密码' : '密码'" :required="!isEdit">
          <el-input v-model="userForm.password" type="password" show-password :placeholder="isEdit ? '不修改请留空' : ''" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="userForm.phone" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="userForm.roles" multiple @change="onRolesChange">
            <el-option label="填报者" value="filler" />
            <el-option label="审批者" value="approver" />
            <el-option label="领导层" value="leader" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="userForm.department_ids" multiple placeholder="选择部门">
            <el-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="userForm.roles.includes('approver')" label="可审批序号">
          <el-select v-model="userForm.approver_sequence_ids" multiple placeholder="选择可审批的序号" style="width: 100%">
            <el-option v-for="seq in sequences" :key="seq" :label="`序号 ${seq}`" :value="seq" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../api/report'
import { userApi } from '../api/user'
import { ElMessage } from 'element-plus'

const activeTab = ref('approved')
const selectedMonth = ref(new Date().toISOString().slice(0, 7))
const approvedRecords = ref([])

const users = ref([])
const departments = ref([])
const sequences = ref([])
const loading = ref(false)
const userDialogVisible = ref(false)
const isEdit = ref(false)
const userForm = ref({
  id: null,
  username: '',
  password: '',
  phone: '',
  roles: [],
  department_ids: [],
  approver_sequence_ids: []
})

function roleText(role) {
  const map = { filler: '填报者', approver: '审批者', leader: '领导层', admin: '管理员' }
  return map[role] || role
}

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

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await userApi.getUsers()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchDepartments() {
  try {
    departments.value = await userApi.getDepartments()
  } catch (e) {
    console.error(e)
  }
}

async function fetchSequences() {
  try {
    const tasks = await reportApi.getTasks()
    sequences.value = tasks.map(t => t.sequence).sort((a, b) => a - b)
  } catch (e) {
    console.error(e)
  }
}

function onRolesChange() {
  if (!userForm.value.roles.includes('approver')) {
    userForm.value.approver_sequence_ids = []
  }
}

function openUserDialog(user = null) {
  if (sequences.value.length === 0) fetchSequences()
  if (user) {
    isEdit.value = true
    userForm.value = {
      id: user.id,
      username: user.username,
      password: '',
      phone: user.phone || '',
      roles: [...user.roles],
      department_ids: [],
      approver_sequence_ids: [...(user.approver_sequences || [])]
    }
  } else {
    isEdit.value = false
    userForm.value = {
      id: null,
      username: '',
      password: '',
      phone: '',
      roles: ['filler'],
      department_ids: [],
      approver_sequence_ids: []
    }
  }
  userDialogVisible.value = true
}

async function saveUser() {
  if (!userForm.value.username || (!isEdit.value && !userForm.value.password)) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  try {
    if (isEdit.value) {
      const data = {}
      if (userForm.value.password) data.password = userForm.value.password
      if (userForm.value.phone !== undefined) data.phone = userForm.value.phone
      if (userForm.value.roles.length) data.roles = userForm.value.roles
      if (userForm.value.department_ids.length) data.department_ids = userForm.value.department_ids
      if (userForm.value.approver_sequence_ids.length) data.approver_sequence_ids = userForm.value.approver_sequence_ids
      await userApi.updateUser(userForm.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await userApi.createUser(userForm.value)
      ElMessage.success('创建成功')
    }
    userDialogVisible.value = false
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function toggleUserStatus(user) {
  try {
    if (user.is_active) {
      await userApi.deleteUser(user.id)
      ElMessage.success('已停用')
    } else {
      await userApi.activateUser(user.id)
      ElMessage.success('已启用')
    }
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

function handleTabChange(tab) {
  if (tab === 'users') {
    fetchUsers()
    fetchDepartments()
  }
}

onMounted(() => {
  fetchApprovedRecords()
})
</script>

<style scoped>
.search-form {
  margin-bottom: 15px;
}
</style>
