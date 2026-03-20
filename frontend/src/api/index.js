/**
 * claw-ex React UI API 封装
 * 基于 axios 的 API 调用封装
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    const message = error.response?.data?.error || error.message || '请求失败';
    return Promise.reject(new Error(message));
  }
);

// ============ 环境管理 API ============

export const envAPI = {
  /** 列出所有环境 */
  list: async () => {
    const response = await apiClient.get('/api/env/list');
    return response;
  },

  /** 创建新环境 */
  create: async (name, description = '') => {
    const response = await apiClient.post('/api/env/create', { name, description });
    return response;
  },

  /** 切换环境 */
  switch: async (envName) => {
    const response = await apiClient.post('/api/env/switch', { name: envName });
    return response;
  },

  /** 删除环境 */
  delete: async (envName) => {
    const response = await apiClient.delete(`/api/env/${envName}`);
    return response;
  },

  /** 获取环境详情 */
  info: async (envName) => {
    const response = await apiClient.get(`/api/env/${envName}`);
    return response;
  },
};

// ============ Agent 配置 API ============

export const agentAPI = {
  /** 列出所有 Agent */
  list: async () => {
    const response = await apiClient.get('/api/agent/list');
    return response;
  },

  /** 获取 Agent 配置 */
  getConfig: async (agentName, configFile = 'models.json') => {
    const response = await apiClient.get(`/api/agent/${agentName}/config/${configFile}`);
    return response;
  },

  /** 更新 Agent 配置 */
  updateConfig: async (agentName, configFile, data) => {
    const response = await apiClient.put(`/api/agent/${agentName}/config/${configFile}`, data);
    return response;
  },

  /** 验证 Agent 配置 */
  validate: async (agentName, configFile) => {
    const response = await apiClient.post(`/api/agent/${agentName}/validate`, { config_file: configFile });
    return response;
  },

  /** 获取配置备份列表 */
  getBackups: async (agentName) => {
    const response = await apiClient.get(`/api/agent/${agentName}/backup`);
    return response;
  },

  /** 恢复配置备份 */
  restore: async (agentName, backupFile) => {
    const response = await apiClient.post(`/api/agent/${agentName}/restore`, { backup_file: backupFile });
    return response;
  },
};

// ============ 任务监控 API ============

export const monitorAPI = {
  /** 获取会话列表 */
  list: async () => {
    const response = await apiClient.get('/api/monitor/list');
    return response;
  },

  /** 获取会话详情 */
  detail: async (sessionId) => {
    const response = await apiClient.get(`/api/monitor/${sessionId}`);
    return response;
  },
};

// ============ 任务管理 API ============

export const taskAPI = {
  /** 获取任务列表 */
  list: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.department) params.append('department', filters.department);
    
    const queryString = params.toString();
    const url = queryString ? `/api/task/list?${queryString}` : '/api/task/list';
    
    const response = await apiClient.get(url);
    return response;
  },

  /** 创建任务 */
  create: async (data) => {
    const response = await apiClient.post('/api/task/create', data);
    return response;
  },

  /** 更新任务 */
  update: async (taskId, data) => {
    const response = await apiClient.put(`/api/task/${taskId}`, data);
    return response;
  },

  /** 获取任务详情 */
  detail: async (taskId) => {
    const response = await apiClient.get(`/api/task/${taskId}`);
    return response;
  },

  /** 删除任务 */
  delete: async (taskId) => {
    const response = await apiClient.delete(`/api/task/${taskId}`);
    return response;
  },
};

export default apiClient;
