<template>
  <el-container style="height: 100vh">
    <el-header style="display: flex; align-items: center; justify-content: space-between; background: #545c64; color: #fff">
      <div style="display: flex; align-items: center; gap: 20px">
        <h2 style="margin: 0">报表系统</h2>
        <el-menu
          :default-active="$route.name"
          mode="horizontal"
          background-color="#545c64"
          text-color="#fff"
          active-text-color="#ffd04b"
          router
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/tasks">任务列表</el-menu-item>
          <el-menu-item index="/approve" v-if="authStore.isApprover || authStore.isAdmin">审批</el-menu-item>
          <el-menu-item index="/admin" v-if="authStore.isAdmin">管理</el-menu-item>
        </el-menu>
      </div>
      <div style="display: flex; align-items: center; gap: 15px">
        <span>{{ authStore.user?.username }} ({{ authStore.user?.roles?.join(', ') }})</span>
        <el-button @click="handleLogout">退出</el-button>
      </div>
    </el-header>
    <el-main style="background: #f0f2f5">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
