/**
 * 数据统计仪表板页面
 * Agent 使用统计、任务统计、会话统计
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Table, Tag, Space, Button, DatePicker,
  Statistic, Progress, Tabs, Select, Divider, Descriptions,
  message, Empty, Tooltip
} from 'antd';
import {
  Bar, Line, Pie
} from '@ant-design/charts';
import {
  DashboardOutlined, TeamOutlined,
  FileTextOutlined, ClockCircleOutlined,
  CheckCircleOutlined, CloseCircleOutlined,
  DownloadOutlined, ReloadOutlined,
  RiseOutlined, FallOutlined
} from '@ant-design/icons';
import statsAPI from '../api/stats';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

// 统计卡片组件
const StatCard = ({ title, value, suffix, icon, trend, color = 'blue' }) => (
  <Card>
    <Statistic
      title={title}
      value={value}
      suffix={suffix}
      prefix={icon}
      valueStyle={{ color }}
    />
    {trend && (
      <div style={{ marginTop: 8, fontSize: 12, color: trend > 0 ? '#52c41a' : '#ff4d4f' }}>
        {trend > 0 ? <RiseOutlined /> : <FallOutlined />}
        {Math.abs(trend)}% 较昨日
      </div>
    )}
  </Card>
);

// Agent 统计页面
const AgentStats = ({ dateRange }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agentId, setAgentId] = useState(null);

  const loadStats = async () => {
    setLoading(true);
    try {
      const days = dateRange?.[0] && dateRange?.[1]
        ? dateRange[1].diff(dateRange[0], 'day')
        : 30;
      const res = await statsAPI.agent(agentId, days);
      if (res.success) {
        setStats(res.data);
      }
    } catch (error) {
      message.error('加载统计失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [dateRange, agentId]);

  if (loading) return <div>加载中...</div>;
  if (!stats) return <Empty description="暂无数据" />;

  const summary = stats.summary || {};
  const agents = stats.agents || [];

  // Agent 调用趋势图数据
  const trendData = agents.slice(0, 5).map(agent => ({
    type: agent.agent_id?.split(':')[1] || agent.agent_id,
    调用次数: agent.total_calls,
    成功: agent.successful_calls,
  }));

  const trendConfig = {
    data: trendData,
    isGroup: true,
    xField: 'type',
    yField: 'value',
    seriesField: 'type',
    label: {
      position: 'middle',
      style: { fill: '#000', opacity: 0.6 },
    },
  };

  const columns = [
    {
      title: 'Agent ID',
      dataIndex: 'agent_id',
      key: 'agent_id',
      render: (text) => (
        <a onClick={() => setAgentId(text)}>{text}</a>
      ),
    },
    {
      title: '模型',
      dataIndex: 'model_id',
      key: 'model_id',
      ellipsis: true,
    },
    {
      title: '总调用',
      dataIndex: 'total_calls',
      key: 'total_calls',
      sorter: (a, b) => a.total_calls - b.total_calls,
    },
    {
      title: '成功率',
      key: 'success_rate',
      render: (_, record) => (
        <Progress
          percent={record.success_rate}
          strokeColor={record.success_rate >= 90 ? '#52c41a' : '#faad14'}
          size="small"
        />
      ),
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration_ms',
      key: 'avg_duration_ms',
      render: (ms) => `${ms} ms`,
    },
    {
      title: '总 Tokens',
      dataIndex: 'total_tokens',
      key: 'total_tokens',
    },
  ];

  return (
    <div>
      {/* 汇总统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <StatCard
            title="Agent 总数"
            value={summary.total_agents || 0}
            icon={<TeamOutlined />}
            color="#1890ff"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="总调用次数"
            value={summary.total_calls || 0}
            icon={<ClockCircleOutlined />}
            color="#52c41a"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="整体成功率"
            value={summary.overall_success_rate || 0}
            suffix="%"
            icon={<CheckCircleOutlined />}
            color={(summary.overall_success_rate || 0) >= 90 ? '#52c41a' : '#faad14'}
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="总 Tokens"
            value={summary.total_tokens_used || 0}
            icon={<FileTextOutlined />}
            color="#722ed1"
          />
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card title="Agent 调用排行">
            {agents.length > 0 ? (
              <Bar
                data={agents.slice(0, 10).map(a => ({
                  type: a.agent_id?.split(':').slice(-1)[0] || a.agent_id,
                  value: a.total_calls,
                }))}
                xField="value"
                yField="type"
                seriesField="type"
                legend={false}
                label={{
                  position: 'right',
                  style: { fill: '#000' },
                }}
              />
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="成功率分布">
            {agents.length > 0 ? (
              <Pie
                data={agents.map(a => ({
                  type: a.success_rate >= 90 ? '优秀 (≥90%)' :
                        a.success_rate >= 70 ? '良好 (70-90%)' :
                        '需优化 (<70%)',
                  value: 1,
                })).reduce((acc, cur) => {
                  const existing = acc.find(i => i.type === cur.type);
                  if (existing) existing.value += 1;
                  else acc.push(cur);
                  return acc;
                }, [])}
                angleField="value"
                colorField="type"
                radius={0.8}
                label={{
                  type: 'outer',
                  content: '{name} {percentage}',
                }}
              />
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 详细列表 */}
      <Card title="Agent 详情">
        <Table
          columns={columns}
          dataSource={agents}
          rowKey="agent_id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

// 任务统计页面
const TaskStats = ({ dateRange }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStats = async () => {
    setLoading(true);
    try {
      const days = dateRange?.[0] && dateRange?.[1]
        ? dateRange[1].diff(dateRange[0], 'day')
        : 30;
      const res = await statsAPI.task(null, days);
      if (res.success) {
        setStats(res.data);
      }
    } catch (error) {
      message.error('加载统计失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [dateRange]);

  if (loading) return <div>加载中...</div>;
  if (!stats) return <Empty description="暂无数据" />;

  const summary = stats.summary || {};
  const tasks = stats.tasks || [];

  const columns = [
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
    },
    {
      title: '总事件',
      dataIndex: 'total_events',
      key: 'total_events',
      sorter: (a, b) => a.total_events - b.total_events,
    },
    {
      title: '完成数',
      dataIndex: 'completed_count',
      key: 'completed_count',
      render: (text) => <span style={{ color: '#52c41a' }}>{text}</span>,
    },
    {
      title: '失败数',
      dataIndex: 'failed_count',
      key: 'failed_count',
      render: (text) => <span style={{ color: '#ff4d4f' }}>{text}</span>,
    },
    {
      title: '成功率',
      key: 'success_rate',
      render: (_, record) => (
        <Progress
          percent={record.success_rate}
          strokeColor={record.success_rate >= 90 ? '#52c41a' : '#ff4d4f'}
          size="small"
        />
      ),
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration_ms',
      key: 'avg_duration_ms',
      render: (ms) => `${ms} ms`,
    },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <StatCard
            title="任务总数"
            value={summary.total_tasks || 0}
            icon={<FileTextOutlined />}
            color="#1890ff"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="总事件数"
            value={summary.total_events || 0}
            icon={<ClockCircleOutlined />}
            color="#52c41a"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="完成数"
            value={summary.total_completed || 0}
            icon={<CheckCircleOutlined />}
            color="#52c41a"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="成功率"
            value={summary.overall_success_rate || 0}
            suffix="%"
            icon={<DashboardOutlined />}
            color={(summary.overall_success_rate || 0) >= 90 ? '#52c41a' : '#faad14'}
          />
        </Col>
      </Row>

      <Card title="任务详情">
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

// 会话统计页面
const SessionStats = ({ dateRange }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStats = async () => {
    setLoading(true);
    try {
      const days = dateRange?.[0] && dateRange?.[1]
        ? dateRange[1].diff(dateRange[0], 'day')
        : 30;
      const res = await statsAPI.session(null, days, false);
      if (res.success) {
        setStats(res.data);
      }
    } catch (error) {
      message.error('加载统计失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [dateRange]);

  if (loading) return <div>加载中...</div>;
  if (!stats) return <Empty description="暂无数据" />;

  const summary = stats.summary || {};
  const sessions = stats.sessions || [];

  const columns = [
    {
      title: '会话 ID',
      dataIndex: 'session_id',
      key: 'session_id',
      render: (text) => text?.slice(0, 25) + '...',
    },
    {
      title: 'Agent',
      dataIndex: 'agent_id',
      key: 'agent_id',
      render: (text) => text?.split(':').slice(-2).join(':'),
    },
    {
      title: '渠道',
      dataIndex: 'channel',
      key: 'channel',
      render: (text) => <Tag>{text || 'unknown'}</Tag>,
    },
    {
      title: '消息数',
      dataIndex: 'messages_count',
      key: 'messages_count',
      sorter: (a, b) => a.messages_count - b.messages_count,
    },
    {
      title: '状态',
      key: 'is_active',
      render: (_, record) => (
        <Tag color={record.is_active ? 'green' : 'default'}>
          {record.is_active ? '活跃' : '非活跃'}
        </Tag>
      ),
    },
    {
      title: '最后活跃',
      dataIndex: 'last_event',
      key: 'last_event',
      render: (text) => text?.slice(0, 19).replace('T', ' '),
    },
  ];

  // 渠道分布图数据
  const channelData = Object.entries(summary.channel_distribution || {}).map(([name, value]) => ({
    type: name,
    value,
  }));

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <StatCard
            title="会话总数"
            value={summary.total_sessions || 0}
            icon={<TeamOutlined />}
            color="#1890ff"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="活跃会话"
            value={summary.active_sessions || 0}
            icon={<CheckCircleOutlined />}
            color="#52c41a"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="非活跃会话"
            value={summary.inactive_sessions || 0}
            icon={<CloseCircleOutlined />}
            color="#ff4d4f"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="总消息数"
            value={summary.total_messages || 0}
            icon={<FileTextOutlined />}
            color="#722ed1"
          />
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card title="渠道分布">
            {channelData.length > 0 ? (
              <Pie
                data={channelData}
                angleField="value"
                colorField="type"
                radius={0.8}
                label={{
                  type: 'outer',
                  content: '{name} {percentage}',
                }}
              />
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="活跃会话排行">
            {sessions.filter(s => s.is_active).slice(0, 10).length > 0 ? (
              <Bar
                data={sessions
                  .filter(s => s.is_active)
                  .slice(0, 10)
                  .map(s => ({
                    type: s.session_id?.slice(-8),
                    value: s.messages_count,
                  }))}
                xField="value"
                yField="type"
                seriesField="type"
                legend={false}
                label={{
                  position: 'right',
                  style: { fill: '#000' },
                }}
              />
            ) : (
              <Empty description="暂无活跃会话" />
            )}
          </Card>
        </Col>
      </Row>

      <Card title="会话列表">
        <Table
          columns={columns}
          dataSource={sessions}
          rowKey="session_id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

// 主页面组件
const StatsDashboard = () => {
  const [dateRange, setDateRange] = useState([dayjs().subtract(30, 'day'), dayjs()]);
  const [activeTab, setActiveTab] = useState('agent');

  const handleExport = async (type) => {
    try {
      const days = dateRange?.[0] && dateRange?.[1]
        ? dateRange[1].diff(dateRange[0], 'day')
        : 30;
      const res = await statsAPI.export(type, 'csv', `./${type}_stats.csv`, days);
      if (res.success) {
        message.success(res.message);
      } else {
        message.error('导出失败：' + res.error);
      }
    } catch (error) {
      message.error('导出失败：' + error.message);
    }
  };

  const tabItems = [
    {
      key: 'agent',
      label: 'Agent 统计',
      children: <AgentStats dateRange={dateRange} />,
    },
    {
      key: 'task',
      label: '任务统计',
      children: <TaskStats dateRange={dateRange} />,
    },
    {
      key: 'session',
      label: '会话统计',
      children: <SessionStats dateRange={dateRange} />,
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <span>统计周期：</span>
              <RangePicker
                value={dateRange}
                onChange={setDateRange}
                style={{ width: 250 }}
              />
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
                刷新
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={() => handleExport(activeTab)}
              >
                导出 CSV
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
    </div>
  );
};

export default StatsDashboard;
