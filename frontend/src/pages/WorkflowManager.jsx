/**
 * 工作流编排管理页面
 * 支持工作流列表、创建、运行、状态查看、DAG 可视化
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Space, Modal, Form, Input, Tag, Card, Row, Col,
  Statistic, Progress, message, Divider, Steps, Timeline, Descriptions
} from 'antd';
import {
  PlusOutlined, PlayCircleOutlined, StopOutlined,
  ReloadOutlined, EyeOutlined, DeleteOutlined,
  DeploymentUnitOutlined, CheckCircleOutlined,
  CloseCircleOutlined, SyncOutlined
} from '@ant-design/icons';
import workflowAPI from '../api/workflow';
import { Line } from '@ant-design/charts';

const { TextArea } = Input;

// 状态标签映射
const statusTagMap = {
  pending: { color: 'default', icon: <SyncOutlined spin /> },
  running: { color: 'processing', icon: <SyncOutlined spin /> },
  completed: { color: 'success', icon: <CheckCircleOutlined /> },
  failed: { color: 'error', icon: <CloseCircleOutlined /> },
  stopped: { color: 'warning', icon: <CloseCircleOutlined /> },
  paused: { color: 'warning', icon: <SyncOutlined /> },
};

// 工作流列表页面
const WorkflowList = ({ onRefresh, onView, onRun, onEdit }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const res = await workflowAPI.list();
      if (res.success) {
        setWorkflows(res.workflows || []);
      }
    } catch (error) {
      message.error('加载工作流失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  const columns = [
    {
      title: '工作流名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <a onClick={() => onView(record)}>{text}</a>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
    },
    {
      title: '步骤数',
      key: 'steps',
      width: 80,
      render: (_, record) => record.steps?.length || 0,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text) => text?.slice(0, 19).replace('T', ' '),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<PlayCircleOutlined />}
            onClick={() => onRun(record)}
          >
            运行
          </Button>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => onView(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const handleDelete = async (record) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除工作流 "${record.name}" 吗？`,
      onOk: async () => {
        try {
          const res = await workflowAPI.delete(record.id);
          if (res.success) {
            message.success('删除成功');
            loadWorkflows();
            onRefresh?.();
          } else {
            message.error('删除失败：' + res.error);
          }
        } catch (error) {
          message.error('删除失败：' + error.message);
        }
      },
    });
  };

  return (
    <Card>
      <Table
        columns={columns}
        dataSource={workflows}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

// 创建工作流表单
const CreateWorkflowForm = ({ visible, onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (values) => {
    setSubmitting(true);
    try {
      const res = await workflowAPI.create({
        name: values.name,
        description: values.description,
        steps: values.steps ? JSON.parse(values.steps) : [],
      });
      if (res.success) {
        message.success('创建工作流成功');
        form.resetFields();
        onSuccess?.();
        onCancel();
      } else {
        message.error('创建失败：' + res.error);
      }
    } catch (error) {
      message.error('创建失败：' + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title="创建工作流"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={700}
    >
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item
          name="name"
          label="工作流名称"
          rules={[{ required: true, message: '请输入工作流名称' }]}
        >
          <Input placeholder="例如：数据处理工作流" />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <TextArea rows={3} placeholder="工作流描述" />
        </Form.Item>
        <Form.Item
          name="steps"
          label="步骤定义 (JSON)"
          tooltip="定义工作流的执行步骤，支持 command、api、parallel 等类型"
        >
          <TextArea
            rows={8}
            placeholder={JSON.stringify([
              {
                name: '步骤 1',
                type: 'command',
                command: 'echo "Hello"',
              },
            ], null, 2)}
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={submitting}>
              创建
            </Button>
            <Button onClick={onCancel}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

// 工作流实例列表
const WorkflowInstances = ({ workflowId }) => {
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadInstances = async () => {
    setLoading(true);
    try {
      const res = await workflowAPI.instances(workflowId);
      if (res.success) {
        setInstances(res.instances || []);
      }
    } catch (error) {
      message.error('加载实例失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInstances();
  }, [workflowId]);

  const columns = [
    {
      title: '实例 ID',
      dataIndex: 'instance_id',
      key: 'instance_id',
      render: (text) => text?.slice(0, 20) + '...',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const tagConfig = statusTagMap[status] || { color: 'default', icon: null };
        return (
          <Tag icon={tagConfig.icon} color={tagConfig.color}>
            {status}
          </Tag>
        );
      },
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 180,
      render: (text) => text?.slice(0, 19).replace('T', ' '),
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 180,
      render: (text) => text?.slice(0, 19).replace('T', ' '),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => viewInstance(record)}
          >
            查看
          </Button>
          {record.status === 'running' && (
            <Button
              type="link"
              danger
              icon={<StopOutlined />}
              onClick={() => stopInstance(record)}
            >
              停止
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const viewInstance = (record) => {
    Modal.info({
      title: `实例详情：${record.instance_id}`,
      content: (
        <Descriptions column={1} bordered>
          <Descriptions.Item label="工作流">{record.workflow_name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusTagMap[record.status]?.color}>{record.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {record.started_at?.slice(0, 19).replace('T', ' ')}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {record.completed_at?.slice(0, 19).replace('T', ' ') || '-'}
          </Descriptions.Item>
        </Descriptions>
      ),
      width: 600,
    });
  };

  const stopInstance = async (record) => {
    try {
      const res = await workflowAPI.stop(record.instance_id);
      if (res.success) {
        message.success('已停止实例');
        loadInstances();
      } else {
        message.error('停止失败：' + res.error);
      }
    } catch (error) {
      message.error('停止失败：' + error.message);
    }
  };

  return (
    <Card title="运行实例" style={{ marginTop: 16 }}>
      <Table
        columns={columns}
        dataSource={instances}
        loading={loading}
        rowKey="instance_id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

// DAG 可视化组件
const DAGViewer = ({ workflow }) => {
  const [dagData, setDagData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDAG = async () => {
      if (!workflow?.id) return;
      setLoading(true);
      try {
        const res = await workflowAPI.dag(workflow.id);
        if (res.success) {
          setDagData(res.dag);
        }
      } catch (error) {
        message.error('加载 DAG 失败：' + error.message);
      } finally {
        setLoading(false);
      }
    };
    loadDAG();
  }, [workflow]);

  if (loading) return <div>加载中...</div>;
  if (!dagData) return <div>无 DAG 数据</div>;

  return (
    <Card title="工作流 DAG" style={{ marginTop: 16 }}>
      <div style={{ padding: 20, background: '#f5f5f5', borderRadius: 8 }}>
        <h4>节点：{dagData.nodes?.length || 0}</h4>
        <h4>边：{dagData.edges?.length || 0}</h4>
        <Divider />
        {dagData.nodes?.map((node, idx) => (
          <div key={node.id} style={{ marginBottom: 12 }}>
            <Tag color="blue">{idx + 1}</Tag>
            <strong>{node.label}</strong>
            <Tag style={{ marginLeft: 8 }}>{node.type}</Tag>
            {node.condition && (
              <Tag color="orange" style={{ marginLeft: 8 }}>条件：{node.condition}</Tag>
            )}
            {node.loop && (
              <Tag color="purple" style={{ marginLeft: 8 }}>循环</Tag>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

// 主页面组件
const WorkflowManager = () => {
  const [viewMode, setViewMode] = useState('list'); // list, instances, dag
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [createVisible, setCreateVisible] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleViewWorkflow = (workflow) => {
    setSelectedWorkflow(workflow);
    setViewMode('detail');
  };

  const handleRunWorkflow = async (workflow) => {
    Modal.confirm({
      title: '运行工作流',
      content: `确定要运行工作流 "${workflow.name}" 吗？`,
      onOk: async () => {
        try {
          const res = await workflowAPI.run(workflow.id);
          if (res.success) {
            message.success(res.message);
            setViewMode('instances');
          } else {
            message.error('运行失败：' + res.error);
          }
        } catch (error) {
          message.error('运行失败：' + error.message);
        }
      },
    });
  };

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button
                type={viewMode === 'list' ? 'primary' : 'default'}
                onClick={() => setViewMode('list')}
              >
                工作流列表
              </Button>
              <Button
                type={viewMode === 'instances' ? 'primary' : 'default'}
                onClick={() => setViewMode('instances')}
              >
                运行实例
              </Button>
              <Button
                type={viewMode === 'dag' ? 'primary' : 'default'}
                onClick={() => setViewMode('dag')}
                disabled={!selectedWorkflow}
              >
                DAG 可视化
              </Button>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => setRefreshKey(k => k + 1)}>
                刷新
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateVisible(true)}
              >
                创建工作流
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {viewMode === 'list' && (
        <WorkflowList
          key={refreshKey}
          onView={handleViewWorkflow}
          onRun={handleRunWorkflow}
          onRefresh={() => setRefreshKey(k => k + 1)}
        />
      )}

      {viewMode === 'instances' && (
        <WorkflowInstances workflowId={selectedWorkflow?.id} />
      )}

      {viewMode === 'dag' && selectedWorkflow && (
        <DAGViewer workflow={selectedWorkflow} />
      )}

      {viewMode === 'detail' && selectedWorkflow && (
        <>
          <Card title="工作流详情" style={{ marginBottom: 16 }}>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="名称">{selectedWorkflow.name}</Descriptions.Item>
              <Descriptions.Item label="版本">{selectedWorkflow.version}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedWorkflow.description || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {selectedWorkflow.created_at?.slice(0, 19).replace('T', ' ')}
              </Descriptions.Item>
              <Descriptions.Item label="步骤数">
                {selectedWorkflow.steps?.length || 0}
              </Descriptions.Item>
            </Descriptions>
            <Divider />
            <h4>步骤列表:</h4>
            <Timeline>
              {selectedWorkflow.steps?.map((step, idx) => (
                <Timeline.Item key={idx} dot={<DeploymentUnitOutlined />}>
                  <strong>{step.name || `步骤 ${idx + 1}`}</strong>
                  <div style={{ marginLeft: 24, color: '#666' }}>
                    类型：{step.type || 'command'}
                    {step.command && <div>命令：{step.command}</div>}
                    {step.condition && <div>条件：{step.condition}</div>}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
          <DAGViewer workflow={selectedWorkflow} />
          <WorkflowInstances workflowId={selectedWorkflow.id} />
        </>
      )}

      <CreateWorkflowForm
        visible={createVisible}
        onCancel={() => setCreateVisible(false)}
        onSuccess={() => {
          setCreateVisible(false);
          setViewMode('list');
          setRefreshKey(k => k + 1);
        }}
      />
    </div>
  );
};

export default WorkflowManager;
