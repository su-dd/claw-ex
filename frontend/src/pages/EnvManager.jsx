/**
 * 环境管理页面
 * 功能：环境列表、创建环境、切换环境、删除环境
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Space,
  Tag,
  message,
  Popconfirm,
  Card,
  Empty,
} from 'antd';
import { PlusOutlined, SwitcherOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { envAPI } from '../api';

const EnvManager = () => {
  const [loading, setLoading] = useState(false);
  const [envList, setEnvList] = useState([]);
  const [currentEnv, setCurrentEnv] = useState('');
  const [defaultEnv, setDefaultEnv] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  // 加载环境列表
  const loadEnvList = async () => {
    setLoading(true);
    try {
      const data = await envAPI.list();
      setEnvList(data || []);
      
      // 查找当前环境和默认环境
      const current = data.find((env) => env.current);
      const defaultE = data.find((env) => env.default);
      
      setCurrentEnv(current?.name || '');
      setDefaultEnv(defaultE?.name || '');
    } catch (error) {
      message.error(`加载环境列表失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEnvList();
  }, []);

  // 创建环境
  const handleCreate = async (values) => {
    try {
      await envAPI.create(values.name, values.description);
      message.success(`环境 "${values.name}" 创建成功`);
      setIsCreateModalOpen(false);
      form.resetFields();
      loadEnvList();
    } catch (error) {
      message.error(`创建环境失败：${error.message}`);
    }
  };

  // 切换环境
  const handleSwitch = async (envName) => {
    try {
      await envAPI.switch(envName);
      message.success(`已切换到环境 "${envName}"`);
      loadEnvList();
    } catch (error) {
      message.error(`切换环境失败：${error.message}`);
    }
  };

  // 删除环境
  const handleDelete = async (envName) => {
    try {
      await envAPI.delete(envName);
      message.success(`环境 "${envName}" 已删除`);
      loadEnvList();
    } catch (error) {
      message.error(`删除环境失败：${error.message}`);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '环境名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <strong>{text}</strong>
          {record.current && <Tag color="green">当前</Tag>}
          {record.default && <Tag color="blue">默认</Tag>}
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {!record.current && (
            <Button
              type="primary"
              size="small"
              icon={<SwitcherOutlined />}
              onClick={() => handleSwitch(record.name)}
            >
              切换
            </Button>
          )}
          {!record.current && !record.default && (
            <Popconfirm
              title="确定要删除此环境吗？"
              onConfirm={() => handleDelete(record.name)}
              okText="确定"
              cancelText="取消"
            >
              <Button danger size="small" icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="环境管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadEnvList}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsCreateModalOpen(true)}
            >
              创建环境
            </Button>
          </Space>
        }
      >
        {envList.length > 0 ? (
          <Table
            columns={columns}
            dataSource={envList}
            rowKey="name"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty description="暂无环境，请创建新环境" />
        )}
      </Card>

      {/* 创建环境对话框 */}
      <Modal
        title="创建新环境"
        open={isCreateModalOpen}
        onCancel={() => {
          setIsCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="环境名称"
            rules={[
              { required: true, message: '请输入环境名称' },
              { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和连字符' },
            ]}
          >
            <Input placeholder="例如：dev, prod, test" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="环境描述（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EnvManager;
