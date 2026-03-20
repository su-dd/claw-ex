/**
 * 日志搜索 - 支持多条件过滤
 */

import React, { useState } from 'react';
import { Table, Tag, Form, Input, Select, Button, Space, Typography, Alert, Card } from 'antd';
import { SearchOutlined, ClearOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

const LogSearch = () => {
  const [form] = Form.useForm();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const levelColors = {
    DEBUG: 'default',
    INFO: 'blue',
    WARNING: 'orange',
    ERROR: 'red',
  };

  const handleSearch = async (values) => {
    setLoading(true);
    setSearched(true);
    try {
      const params = new URLSearchParams({
        keyword: values.keyword || '',
        limit: values.limit || 100,
      });

      if (values.level && values.level !== 'ALL') {
        params.append('level', values.level);
      }
      if (values.source) {
        params.append('source', values.source);
      }
      if (values.start_time) {
        params.append('start_time', values.start_time);
      }
      if (values.end_time) {
        params.append('end_time', values.end_time);
      }

      const response = await fetch(`http://localhost:8000/api/logs/search?${params}`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
    setLogs([]);
    setSearched(false);
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
      <Title level={4}>🔍 日志搜索</Title>

      <Card style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleSearch}
        >
          <Form.Item name="keyword" label="关键词">
            <Input placeholder="搜索关键词" style={{ width: 200 }} />
          </Form.Item>

          <Form.Item name="level" label="级别">
            <Select style={{ width: 120 }} allowClear>
              <Option value="ALL">全部级别</Option>
              <Option value="DEBUG">DEBUG</Option>
              <Option value="INFO">INFO</Option>
              <Option value="WARNING">WARNING</Option>
              <Option value="ERROR">ERROR</Option>
            </Select>
          </Form.Item>

          <Form.Item name="source" label="来源">
            <Input placeholder="日志来源" style={{ width: 150 }} />
          </Form.Item>

          <Form.Item name="start_time" label="开始时间">
            <Input type="datetime-local" style={{ width: 180 }} />
          </Form.Item>

          <Form.Item name="end_time" label="结束时间">
            <Input type="datetime-local" style={{ width: 180 }} />
          </Form.Item>

          <Form.Item name="limit" label="数量" initialValue={100}>
            <Select style={{ width: 100 }}>
              <Option value={50}>50</Option>
              <Option value={100}>100</Option>
              <Option value={200}>200</Option>
              <Option value={500}>500</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>
                搜索
              </Button>
              <Button onClick={handleReset} icon={<ClearOutlined />}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {searched && logs.length === 0 && !loading && (
        <Alert
          message="未找到匹配的日志"
          description="请尝试调整搜索条件"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {logs.length > 0 && (
        <Alert
          message={`找到 ${logs.length} 条匹配的日志`}
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
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

export default LogSearch;
