# 任务列表导出功能设计

## 概述

为任务列表页面添加 Excel 导出功能，支持用户选择要导出的列，仅导出已提交状态的记录。

## 功能详情

### 功能入口
- 在任务列表页面（TasksView.vue）工具栏区域添加"导出"按钮

### 交互流程
1. 用户点击"导出"按钮，弹出导出对话框（el-dialog）
2. 对话框标题为"导出任务列表"
3. 显示可选列的复选框列表（el-checkbox-group），默认全选
4. 用户选择要导出的列，点击"确认"按钮
5. 系统生成 Excel 文件并触发浏览器下载

### 导出规则
- **筛选条件**: 只导出 `status === 'submitted'` 的已提交记录
- **固定排除**: 填报人、状态两列始终不导出
- **可选列（默认全选）**:
  - 序号 (sequence)
  - 重点工作 (taskName)
  - 主要目标任务 (target)
  - 牵头领导 (leader)
  - 牵头部门 (departmentName)
  - 配合部门 (partnerDepts)
  - 完成时间 (deadline)
  - 年度工作措施 (measureContent)
  - 责任人 (personLiable)
  - 具体举措 (specificMeasures)
  - 本月工作内容 (currentContent)
  - 下月工作计划 (nextPlan)

## 技术方案

### 依赖
- 前端库: `xlsx` (SheetJS) - 用于生成 Excel 文件

### 实现位置
- 前端: `frontend/src/views/TasksView.vue`
- API: 复用现有的 `/api/report/records?status_filter=submitted` 获取已提交记录

### Excel 生成逻辑
1. 调用 API 获取当月已提交记录
2. 根据用户选择的列过滤数据
3. 使用 xlsx 库构建工作表
4. 设置列宽自适应
5. 触发文件下载，文件名格式: `任务列表_YYYY-MM.xlsx`

## UI 设计

### 导出按钮
- 位置: 搜索表单右侧
- 样式: 使用 `el-button`，type="success"

### 导出对话框
- 宽度: 500px
- 内容:
  - 标题: "导出任务列表"
  - 复选框区域: 每行显示 3 个选项，共 4 行
  - 底部按钮: "取消" 和 "确认"

## 文件变更

1. `frontend/src/views/TasksView.vue` - 添加导出按钮和对话框
2. `frontend/package.json` - 添加 xlsx 依赖
