/**
 * claw-ex React UI 主应用
 * 完善路由配置：添加路由守卫、错误页面、优化导航
 */

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
  TemplateOutlined,
  FileSearchOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import EnvManager from './pages/EnvManager';
import AgentConfig from './pages/AgentConfig';
import MonitorPanel from './pages/MonitorPanel';
import TaskManager from './pages/TaskManager';
import TemplateList from './pages/TemplateList';
import TemplateDetail from './pages/TemplateDetail';
import TemplateForm from './pages/TemplateForm';
import TemplateApply from './pages/TemplateApply';
import LogViewer from './pages/LogViewer';
import LogSearch from './pages/LogSearch';
import BatchOperations from './pages/BatchOperations';
import NotFound from './pages/NotFound';
import Forbidden from './pages/Forbidden';
import RouteGuard from './components/RouteGuard';
import './App.css';

const { Header, Sider, Content } = Layout;

// 主布局组件（带侧边栏）
const MainLayout = ({ children, selectedKey }) => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: 'monitor',
      icon: <DashboardOutlined />,
      label: '任务监控',
      path: '/',
    },
    {
      key: 'env',
      icon: <EnvironmentOutlined />,
      label: '环境管理',
      path: '/env',
    },
    {
      key: 'agent',
      icon: <SettingOutlined />,
      label: 'Agent 配置',
      path: '/agent',
    },
    {
      key: 'task',
      icon: <FileTextOutlined />,
      label: '任务管理',
      path: '/task',
    },
    {
      key: 'logs',
      icon: <FileSearchOutlined />,
      label: '日志中心',
      path: '/logs',
      children: [
        { key: 'log-viewer', label: '日志查看', path: '/logs/viewer' },
        { key: 'log-search', label: '日志搜索', path: '/logs/search' },
      ],
    },
    {
      key: 'batch',
      icon: <ThunderboltOutlined />,
      label: '批量操作',
      path: '/batch',
    },
    {
      key: 'templates',
      icon: <TemplateOutlined />,
      label: '模板管理',
      path: '/templates',
    },
  ];

  // 根据当前路径确定选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path.startsWith('/templates')) return 'templates';
    if (path.startsWith('/logs')) return 'logs';
    if (path.startsWith('/batch')) return 'batch';
    if (path.startsWith('/env')) return 'env';
    if (path.startsWith('/agent')) return 'agent';
    if (path.startsWith('/task')) return 'task';
    return 'monitor';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" style={{ boxShadow: '2px 0 8px rgba(0,0,0,0.1)' }}>
        <div className="logo">
          <h2>🐾 claw-ex</h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems.map(item => ({
            ...item,
            onClick: () => navigate(item.path),
          }))}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer }}>
          <h2 style={{ margin: 0, lineHeight: '64px' }}>
            {menuItems.find((item) => item.key === getSelectedKey())?.label || 'claw-ex'}
          </h2>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 280,
          }}
        >
          <RouteGuard>{children}</RouteGuard>
        </Content>
      </Layout>
    </Layout>
  );
};

// 带布局的路由组件
const LayoutRoute = ({ children, selectedKey }) => (
  <MainLayout selectedKey={selectedKey}>
    {children}
  </MainLayout>
);

const App = () => {
  return (
    <Router>
      <Routes>
        {/* 首页 - 任务监控 */}
        <Route
          path="/"
          element={<LayoutRoute selectedKey="monitor"><MonitorPanel /></LayoutRoute>}
        />

        {/* 环境管理路由 */}
        <Route
          path="/env"
          element={<LayoutRoute selectedKey="env"><EnvManager /></LayoutRoute>}
        />

        {/* Agent 配置路由 */}
        <Route
          path="/agent"
          element={<LayoutRoute selectedKey="agent"><AgentConfig /></LayoutRoute>}
        />

        {/* 任务管理路由 */}
        <Route
          path="/task"
          element={<LayoutRoute selectedKey="task"><TaskManager /></LayoutRoute>}
        />

        {/* 日志中心路由组 */}
        <Route
          path="/logs/viewer"
          element={<LayoutRoute selectedKey="logs"><LogViewer /></LayoutRoute>}
        />
        <Route
          path="/logs/search"
          element={<LayoutRoute selectedKey="logs"><LogSearch /></LayoutRoute>}
        />

        {/* 批量操作路由 */}
        <Route
          path="/batch"
          element={<LayoutRoute selectedKey="batch"><BatchOperations /></LayoutRoute>}
        />

        {/* 模板管理路由组 */}
        <Route
          path="/templates"
          element={<LayoutRoute selectedKey="templates"><TemplateList /></LayoutRoute>}
        />
        <Route
          path="/templates/:templateId"
          element={<LayoutRoute selectedKey="templates"><TemplateDetail /></LayoutRoute>}
        />
        <Route
          path="/templates/:templateId/edit"
          element={<LayoutRoute selectedKey="templates"><TemplateForm /></LayoutRoute>}
        />
        <Route
          path="/templates/create"
          element={<LayoutRoute selectedKey="templates"><TemplateForm /></LayoutRoute>}
        />
        <Route
          path="/templates/:templateId/apply"
          element={<LayoutRoute selectedKey="templates"><TemplateApply /></LayoutRoute>}
        />

        {/* 错误页面 */}
        <Route
          path="/403"
          element={<Forbidden />}
        />
        <Route
          path="/404"
          element={<NotFound />}
        />
        
        {/* 通配符路由 - 所有未匹配的路由重定向到 404 */}
        <Route
          path="*"
          element={<NotFound />}
        />
      </Routes>
    </Router>
  );
};

export default App;
