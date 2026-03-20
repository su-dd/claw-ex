/**
 * 日志查看器 - 支持实时刷新
 */

import React, { useState, useEffect, useRef } from 'react';
import { Table, Tag, Space, Button, Select, Input, Switch, Typography, Spin, Alert } from 'antd';
import {
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

const LogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [lines, setLines] = useState(100);
  const intervalRef = useRef(null);

  const levelColors = {
    DEBUG: 'default',
    INFO: 'blue',
    WARNING: 'orange',
    ERROR: 'red',
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        lines: lines.toString(),
      });
      if (levelFilter !== 'ALL') {
        params.append('level', levelFilter);
      }

      const response = await fetch(`http://localhost:8000/api/logs/tail?${params}`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('获取日志失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();

    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 2000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, levelFilter, lines]);

  const handleExport = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/logs/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          output_path: 'logs_export.log',
          level: levelFilter !== 'ALL' ? levelFilter : null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`日志导出成功：${data.path} (${data.count} 条)`);
      }
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败');
    }
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (text) => text?.slice(0, 19) || '',
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level) => (
        <Tag color={levelColors[level] || 'default'}>{level}</Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>📜 日志查看器</Title>
        <Space>
          <Select
            value={levelFilter}
            onChange={setLevelFilter}
            style={{ width: 120 }}
          >
            <Option value="ALL">全部级别</Option>
            <Option value="DEBUG">DEBUG</Option>
            <Option value="INFO">INFO</Option>
            <Option value="WARNING">WARNING</Option>
            <Option value="ERROR">ERROR</Option>
          </Select>

          <Select
            value={lines}
            onChange={setLines}
            style={{ width: 100 }}
          >
            <Option value={50}>50 行</Option>
            <Option value={100}>100 行</Option>
            <Option value={200}>200 行</Option>
            <Option value={500}>500 行</Option>
          </Select>

          <Switch
            checkedChildren="自动刷新"
            unCheckedChildren="手动刷新"
            checked={autoRefresh}
            onChange={setAutoRefresh}
          />

          <Button
            icon={<ReloadOutlined />}
            onClick={fetchLogs}
            loading={loading}
          >
            刷新
          </Button>

          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            导出
          </Button>
        </Space>
      </div>

      {autoRefresh && (
        <Alert
          message="实时刷新已开启"
          description="日志将每 2 秒自动刷新"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          icon={<PlayCircleOutlined />}
        />
      )}

      <Table
        columns={columns}
        dataSource={logs}
        rowKey={(record) => record.timestamp + record.message}
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        scroll={{ y: 500 }}
      />
    </div>
  );
};

export default LogViewer;
