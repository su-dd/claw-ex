/**
 * 任务监控面板
 * 功能：会话列表、实时监控、会话详情、统计卡片
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Statistic,
  Row,
  Col,
  Modal,
  Descriptions,
  Switch,
  message,
  Empty,
} from 'antd';
import {
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { monitorAPI } from '../api';
import { getWebSocketManager } from '../utils/websocket';

const MonitorPanel = () => {
  const [loading, setLoading] = useState(false);
  const [sessionList, setSessionList] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [realtimeEnabled, setRealtimeEnabled] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    tokens: 0,
    cost: 0,
  });

  const wsManager = React.useRef(null);

  // 加载会话列表
  const loadSessionList = useCallback(async () => {
    setLoading(true);
    try {
      const data = await monitorAPI.list();
      setSessionList(data || []);
      
      // 计算统计
      const total = data?.length || 0;
      const active = data?.filter((s) => s.status === 'active' || s.status === 'running')?.length || 0;
      const tokens = data?.reduce((sum, s) => sum + (s.tokens_used || 0), 0) || 0;
      const cost = data?.reduce((sum, s) => sum + (s.cost || 0), 0) || 0;
      
      setStats({ total, active, tokens, cost });
    } catch (error) {
      message.error(`加载会话列表失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessionList();
  }, [loadSessionList]);

  // 实时监控
  useEffect(() => {
    if (realtimeEnabled) {
      // 连接 WebSocket
      wsManager.current = getWebSocketManager();
      
      wsManager.current.on('connect', () => {
        console.log('WebSocket connected for monitoring');
      });

      wsManager.current.on('event:session_update', (data) => {
        console.log('Session update received:', data);
        loadSessionList();
      });

      wsManager.current.on('message', (data) => {
        console.log('WebSocket message:', data);
        if (data.type === 'session_update') {
          loadSessionList();
        }
      });

      wsManager.current.connect();

      // 轮询备份（如果 WebSocket 不可用）
      const pollInterval = setInterval(() => {
        if (!wsManager.current?.isConnected) {
          loadSessionList();
        }
      }, 10000);

      return () => {
        clearInterval(pollInterval);
        if (wsManager.current) {
          wsManager.current.disconnect();
        }
      };
    }
  }, [realtimeEnabled, loadSessionList]);

  // 查看会话详情
  const handleViewDetail = async (sessionId) => {
    try {
      const detail = await monitorAPI.detail(sessionId);
      setSelectedSession(detail);
      setIsDetailModalOpen(true);
    } catch (error) {
      message.error(`加载会话详情失败：${error.message}`);
    }
  };

  // 状态标签渲染
  const renderStatus = (status) => {
    const statusMap = {
      active: { color: 'success', icon: <CheckCircleOutlined />, text: '活跃' },
      running: { color: 'processing', icon: <SyncOutlined spin />, text: '运行中' },
      pending: { color: 'warning', icon: <ClockCircleOutlined />, text: '等待中' },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
      cancelled: { color: 'default', icon: <CloseCircleOutlined />, text: '已取消' },
    };

    const config = statusMap[status] || { color: 'default', icon: null, text: status };
    return (
      <Tag icon={config.icon} color={config.color}>
        {config.text}
      </Tag>
    );
  };

  // 表格列定义
  const columns = [
    {
      title: '会话 ID',
      dataIndex: 'session_id',
      key: 'session_id',
      render: (text) => <code>{text}</code>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => renderStatus(status),
    },
    {
      title: '任务',
      dataIndex: 'task',
      key: 'task',
      ellipsis: true,
    },
    {
      title: '进展',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => `${progress || 0}%`,
    },
    {
      title: 'Tokens',
      dataIndex: 'tokens_used',
      key: 'tokens_used',
      render: (tokens) => tokens?.toLocaleString() || '0',
    },
    {
      title: '成本',
      dataIndex: 'cost',
      key: 'cost',
      render: (cost) => `¥${cost?.toFixed(4) || '0.0000'}`,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.session_id)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总会话数"
              value={stats.total}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃会话"
              value={stats.active}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Token 消耗"
              value={stats.tokens}
              suffix="tokens"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总成本"
              value={stats.cost}
              precision={4}
              prefix="¥"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 会话列表 */}
      <Card
        title="会话监控"
        extra={
          <Space>
            <Space>
              <span>实时监控:</span>
              <Switch
                checked={realtimeEnabled}
                onChange={setRealtimeEnabled}
                checkedChildren="开"
                unCheckedChildren="关"
              />
            </Space>
            <Button icon={<ReloadOutlined />} onClick={loadSessionList}>
              刷新
            </Button>
          </Space>
        }
      >
        {sessionList.length > 0 ? (
          <Table
            columns={columns}
            dataSource={sessionList}
            rowKey="session_id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            size="middle"
          />
        ) : (
          <Empty description="暂无会话" />
        )}
      </Card>

      {/* 会话详情对话框 */}
      <Modal
        title="会话详情"
        open={isDetailModalOpen}
        onCancel={() => setIsDetailModalOpen(false)}
        footer={null}
        width={800}
      >
        {selectedSession && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="会话 ID">
              <code>{selectedSession.session_id}</code>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {renderStatus(selectedSession.status)}
            </Descriptions.Item>
            <Descriptions.Item label="任务" span={2}>
              {selectedSession.task}
            </Descriptions.Item>
            <Descriptions.Item label="进展">
              {selectedSession.progress || 0}%
            </Descriptions.Item>
            <Descriptions.Item label="Tokens 消耗">
              {selectedSession.tokens_used?.toLocaleString() || '0'}
            </Descriptions.Item>
            <Descriptions.Item label="成本">
              ¥{selectedSession.cost?.toFixed(4) || '0.0000'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {selectedSession.created_at}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedSession.updated_at}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>
              {selectedSession.notes || '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default MonitorPanel;
