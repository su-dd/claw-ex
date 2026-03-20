/**
 * 批量操作面板 - 支持多选 + 批量执行
 */

import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  Form,
  Card,
  Typography,
  Tag,
  Modal,
  message as msg,
  Progress,
} from 'antd';
import {
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

const BatchOperations = () => {
  const [form] = Form.useForm();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRows, setSelectedRows] = useState([]);
  const [jobModalVisible, setJobModalVisible] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);

  const statusColors = {
    running: 'processing',
    completed: 'success',
    failed: 'error',
    pending: 'warning',
  };

  const handleBatchStart = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/batch/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pattern: values.pattern || 'agent:*',
          filter: values.filter,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        msg.success(`批量启动成功：${data.affected} 个 Agent`);
        fetchJobs();
      }
    } catch (error) {
      console.error('批量启动失败:', error);
      msg.error('批量启动失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchStop = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/batch/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pattern: values.pattern || 'task:*',
          ids: values.ids ? values.ids.split(',') : [],
        }),
      });

      if (response.ok) {
        const data = await response.json();
        msg.success(`批量停止成功：${data.affected} 个任务`);
        fetchJobs();
      }
    } catch (error) {
      console.error('批量停止失败:', error);
      msg.error('批量停止失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchRun = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/batch/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow: values.workflow || 'default',
          parallel: values.parallel || false,
          targets: values.targets ? values.targets.split(',') : [],
        }),
      });

      if (response.ok) {
        const data = await response.json();
        msg.success(`批量执行启动：${data.job_id}`);
        fetchJobs();
      }
    } catch (error) {
      console.error('批量执行失败:', error);
      msg.error('批量执行失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    // 模拟获取任务列表
    setJobs([
      {
        job_id: 'batch-001',
        status: 'completed',
        created_at: '2026-03-20T10:00:00',
        total: 10,
        completed: 10,
        failed: 0,
        type: 'start',
      },
      {
        job_id: 'batch-002',
        status: 'running',
        created_at: '2026-03-20T11:00:00',
        total: 20,
        completed: 15,
        failed: 0,
        type: 'run',
      },
    ]);
  };

  const viewJobStatus = async (jobId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/batch/status/${jobId}`);
      if (response.ok) {
        const data = await response.json();
        setCurrentJob(data.job);
        setJobModalVisible(true);
      }
    } catch (error) {
      console.error('获取任务状态失败:', error);
      msg.error('获取任务状态失败');
    }
  };

  const columns = [
    {
      title: '任务 ID',
      dataIndex: 'job_id',
      key: 'job_id',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const typeMap = {
          start: '批量启动',
          stop: '批量停止',
          run: '批量执行',
        };
        return typeMap[type] || type;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={statusColors[status] || 'default'}>
          {status}
        </Tag>
      ),
    },
    {
      title: '进度',
      key: 'progress',
      render: (_, record) => (
        <Progress
          percent={Math.round((record.completed / record.total) * 100)}
          status={record.failed > 0 ? 'exception' : record.status === 'running' ? 'active' : 'normal'}
        />
      ),
    },
    {
      title: '总数/完成/失败',
      key: 'counts',
      render: (_, record) => `${record.total} / ${record.completed} / ${record.failed}`,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => text?.slice(0, 19) || '',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          onClick={() => viewJobStatus(record.job_id)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>⚡ 批量操作</Title>

      <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }} size="large">
        {/* 批量启动 */}
        <Card title="批量启动 Agent" size="small">
          <Form
            form={form}
            layout="inline"
            onFinish={handleBatchStart}
          >
            <Form.Item name="pattern" label="匹配模式" initialValue="agent:*">
              <Input placeholder="如：agent:*" style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="filter" label="过滤条件">
              <Input placeholder="如：dept=gongbu" style={{ width: 200 }} />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<PlayCircleOutlined />}
                loading={loading}
              >
                批量启动
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {/* 批量停止 */}
        <Card title="批量停止任务" size="small">
          <Form
            form={form}
            layout="inline"
            onFinish={handleBatchStop}
          >
            <Form.Item name="pattern" label="匹配模式" initialValue="task:*">
              <Input placeholder="如：task:*" style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="ids" label="指定 ID">
              <Input placeholder="多个 ID 用逗号分隔" style={{ width: 250 }} />
            </Form.Item>
            <Form.Item>
              <Button
                danger
                htmlType="submit"
                icon={<StopOutlined />}
                loading={loading}
              >
                批量停止
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {/* 批量执行工作流 */}
        <Card title="批量执行工作流" size="small">
          <Form
            form={form}
            layout="inline"
            onFinish={handleBatchRun}
          >
            <Form.Item name="workflow" label="工作流" initialValue="default">
              <Input placeholder="工作流名称" style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="parallel" label="并行执行" valuePropName="checked">
              <Select style={{ width: 100 }}>
                <Option value={true}>是</Option>
                <Option value={false}>否</Option>
              </Select>
            </Form.Item>
            <Form.Item name="targets" label="目标列表">
              <Input placeholder="多个目标用逗号分隔" style={{ width: 200 }} />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<ThunderboltOutlined />}
                loading={loading}
              >
                批量执行
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Space>

      <Card title="批量任务历史" size="small">
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="job_id"
          pagination={false}
        />
      </Card>

      {/* 任务详情弹窗 */}
      <Modal
        title="批量任务详情"
        open={jobModalVisible}
        onCancel={() => setJobModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setJobModalVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {currentJob && (
          <div>
            <p><strong>任务 ID:</strong> {currentJob.job_id}</p>
            <p><strong>状态:</strong> <Tag color={statusColors[currentJob.status]}>{currentJob.status}</Tag></p>
            <p><strong>创建时间:</strong> {currentJob.created_at}</p>
            <p><strong>进度:</strong></p>
            <Progress
              percent={Math.round((currentJob.completed / currentJob.total) * 100)}
              status={currentJob.failed > 0 ? 'exception' : 'normal'}
            />
            <p><strong>总数:</strong> {currentJob.total}</p>
            <p><strong>已完成:</strong> {currentJob.completed}</p>
            <p><strong>失败:</strong> {currentJob.failed}</p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default BatchOperations;
