/**
 * 任务管理页面
 * 功能：任务列表、创建任务、更新任务状态、任务详情
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Card,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  InputNumber,
  DatePicker,
  Descriptions,
  Empty,
} from 'antd';
import {
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { taskAPI } from '../api';

const { TextArea } = Input;

const TaskManager = () => {
  const [loading, setLoading] = useState(false);
  const [taskList, setTaskList] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [filters, setFilters] = useState({});
  const [createForm] = Form.useForm();
  const [updateForm] = Form.useForm();

  // 加载任务列表
  const loadTaskList = async (filterParams = {}) => {
    setLoading(true);
    try {
      const data = await taskAPI.list(filterParams);
      setTaskList(data || []);
    } catch (error) {
      message.error(`加载任务列表失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTaskList(filters);
  }, []);

  // 创建任务
  const handleCreate = async (values) => {
    try {
      const data = {
        ...values,
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : null,
      };
      await taskAPI.create(data);
      message.success('任务创建成功');
      setIsCreateModalOpen(false);
      createForm.resetFields();
      loadTaskList(filters);
    } catch (error) {
      message.error(`创建任务失败：${error.message}`);
    }
  };

  // 更新任务状态
  const handleUpdate = async (taskId, values) => {
    try {
      await taskAPI.update(taskId, values);
      message.success('任务已更新');
      setIsUpdateModalOpen(false);
      updateForm.resetFields();
      loadTaskList(filters);
    } catch (error) {
      message.error(`更新任务失败：${error.message}`);
    }
  };

  // 删除任务
  const handleDelete = async (taskId) => {
    try {
      await taskAPI.delete(taskId);
      message.success('任务已删除');
      loadTaskList(filters);
    } catch (error) {
      message.error(`删除任务失败：${error.message}`);
    }
  };

  // 查看任务详情
  const handleViewDetail = async (taskId) => {
    try {
      const detail = await taskAPI.detail(taskId);
      setSelectedTask(detail);
      setIsDetailModalOpen(true);
    } catch (error) {
      message.error(`加载任务详情失败：${error.message}`);
    }
  };

  // 打开更新对话框
  const handleOpenUpdate = (task) => {
    updateForm.setFieldsValue({
      status: task.status,
      priority: task.priority,
      notes: task.notes,
    });
    setSelectedTask(task);
    setIsUpdateModalOpen(true);
  };

  // 状态标签渲染
  const renderStatus = (status) => {
    const statusMap = {
      todo: { color: 'default', text: '待办' },
      doing: { color: 'processing', text: '进行中' },
      review: { color: 'warning', text: '审核中' },
      done: { color: 'success', text: '已完成' },
      blocked: { color: 'error', text: '阻塞' },
      cancelled: { color: 'default', text: '已取消' },
    };

    const config = statusMap[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 优先级标签渲染
  const renderPriority = (priority) => {
    const priorityMap = {
      1: { color: 'success', text: '低' },
      2: { color: 'default', text: '中' },
      3: { color: 'warning', text: '高' },
      4: { color: 'error', text: '紧急' },
    };

    const config = priorityMap[priority] || { color: 'default', text: priority };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 筛选处理
  const handleFilter = () => {
    loadTaskList(filters);
  };

  // 表格列定义
  const columns = [
    {
      title: '任务 ID',
      dataIndex: 'id',
      key: 'id',
      render: (text) => <code>{text}</code>,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => renderStatus(status),
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (dept) => dept || '-',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => renderPriority(priority),
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      key: 'due_date',
      render: (date) => date || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenUpdate(record)}
          >
            更新
          </Button>
          <Popconfirm
            title="确定要删除此任务吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button danger type="link" size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="任务管理"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsCreateModalOpen(true)}
            >
              创建任务
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => loadTaskList(filters)}>
              刷新
            </Button>
          </Space>
        }
      >
        {/* 筛选栏 */}
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 120 }}
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Select.Option value="todo">待办</Select.Option>
            <Select.Option value="doing">进行中</Select.Option>
            <Select.Option value="review">审核中</Select.Option>
            <Select.Option value="done">已完成</Select.Option>
            <Select.Option value="blocked">阻塞</Select.Option>
          </Select>
          <Select
            placeholder="部门筛选"
            allowClear
            style={{ width: 120 }}
            onChange={(value) => setFilters({ ...filters, department: value })}
          >
            <Select.Option value="shangshu">尚书省</Select.Option>
            <Select.Option value="gongbu">工部</Select.Option>
            <Select.Option value="libu">吏部</Select.Option>
            <Select.Option value="hubu">户部</Select.Option>
          </Select>
          <Button onClick={handleFilter}>筛选</Button>
        </Space>

        {taskList.length > 0 ? (
          <Table
            columns={columns}
            dataSource={taskList}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty description="暂无任务" />
        )}
      </Card>

      {/* 创建任务对话框 */}
      <Modal
        title="创建新任务"
        open={isCreateModalOpen}
        onCancel={() => {
          setIsCreateModalOpen(false);
          createForm.resetFields();
        }}
        onOk={() => createForm.submit()}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="任务标题" />
          </Form.Item>
          <Form.Item name="description" label="任务描述">
            <TextArea rows={4} placeholder="任务详细描述" />
          </Form.Item>
          <Form.Item name="department" label="部门">
            <Select placeholder="选择部门">
              <Select.Option value="shangshu">尚书省</Select.Option>
              <Select.Option value="gongbu">工部</Select.Option>
              <Select.Option value="libu">吏部</Select.Option>
              <Select.Option value="hubu">户部</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={2}>
            <Select>
              <Select.Option value={1}>低</Select.Option>
              <Select.Option value={2}>中</Select.Option>
              <Select.Option value={3}>高</Select.Option>
              <Select.Option value={4}>紧急</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="due_date" label="截止日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务详情对话框 */}
      <Modal
        title="任务详情"
        open={isDetailModalOpen}
        onCancel={() => setIsDetailModalOpen(false)}
        footer={null}
        width={700}
      >
        {selectedTask && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="任务 ID">
              <code>{selectedTask.id}</code>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {renderStatus(selectedTask.status)}
            </Descriptions.Item>
            <Descriptions.Item label="标题" span={2}>
              {selectedTask.title}
            </Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {selectedTask.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="部门">{selectedTask.department || '-'}</Descriptions.Item>
            <Descriptions.Item label="优先级">
              {renderPriority(selectedTask.priority)}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">{selectedTask.created_at}</Descriptions.Item>
            <Descriptions.Item label="截止日期">{selectedTask.due_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>
              {selectedTask.notes || '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 更新任务对话框 */}
      <Modal
        title={`更新任务 - ${selectedTask?.id}`}
        open={isUpdateModalOpen}
        onCancel={() => {
          setIsUpdateModalOpen(false);
          updateForm.resetFields();
        }}
        onOk={() => updateForm.submit()}
        destroyOnClose
      >
        <Form form={updateForm} layout="vertical" onFinish={(values) => handleUpdate(selectedTask?.id, values)}>
          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value="todo">待办</Select.Option>
              <Select.Option value="doing">进行中</Select.Option>
              <Select.Option value="review">审核中</Select.Option>
              <Select.Option value="done">已完成</Select.Option>
              <Select.Option value="blocked">阻塞</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select>
              <Select.Option value={1}>低</Select.Option>
              <Select.Option value={2}>中</Select.Option>
              <Select.Option value={3}>高</Select.Option>
              <Select.Option value={4}>紧急</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={4} placeholder="更新备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TaskManager;
