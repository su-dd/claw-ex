/**
 * claw-ex React UI 主应用
 */

import React, { useState } from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import EnvManager from './pages/EnvManager';
import AgentConfig from './pages/AgentConfig';
import MonitorPanel from './pages/MonitorPanel';
import TaskManager from './pages/TaskManager';
import './App.css';

const { Header, Sider, Content } = Layout;

const App = () => {
  const [selectedKey, setSelectedKey] = useState('monitor');
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const menuItems = [
    {
      key: 'monitor',
      icon: <DashboardOutlined />,
      label: '任务监控',
    },
    {
      key: 'env',
      icon: <EnvironmentOutlined />,
      label: '环境管理',
    },
    {
      key: 'agent',
      icon: <SettingOutlined />,
      label: 'Agent 配置',
    },
    {
      key: 'task',
      icon: <FileTextOutlined />,
      label: '任务管理',
    },
  ];

  const renderPage = () => {
    switch (selectedKey) {
      case 'monitor':
        return <MonitorPanel />;
      case 'env':
        return <EnvManager />;
      case 'agent':
        return <AgentConfig />;
      case 'task':
        return <TaskManager />;
      default:
        return <MonitorPanel />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" style={{ boxShadow: '2px 0 8px rgba(0,0,0,0.1)' }}>
        <div className="logo">
          <h2>🐾 claw-ex</h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer }}>
          <h2 style={{ margin: 0, lineHeight: '64px' }}>
            {menuItems.find((item) => item.key === selectedKey)?.label}
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
          {renderPage()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
