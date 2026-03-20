/**
 * 模板列表页面
 * 功能：模板列表展示、搜索、创建、删除、导出
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  message,
  Popconfirm,
  Card,
  Empty,
  Input,
  Select,
  Modal,
  Form,
  Input as AntInput,
  Upload,
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined,
  ExportOutlined,
  ImportOutlined,
  EyeOutlined,
  EditOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { templateAPI } from '../api/template';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;
const { TextArea } = AntInput;

const TemplateList = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [importFile, setImportFile] = useState(null);

  // 加载模板列表
  const loadTemplates = async () => {
    setLoading(true);
    try {
      const data = await templateAPI.list();
      setTemplates(data || []);
    } catch (error) {
      message.error(`加载模板列表失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  // 创建模板
  const handleCreate = async (values) => {
    try {
      let content;
      try {
        content = JSON.parse(values.content || '{}');
      } catch (e) {
        message.error('模板内容必须是有效的 JSON 格式');
        return;
      }

      await templateAPI.create({
        id: values.id,
        name: values.name,
        description: values.description,
        category: values.category,
        content,
      });
      message.success(`模板 "${values.name}" 创建成功`);
      setIsCreateModalOpen(false);
      form.resetFields();
      loadTemplates();
    } catch (error) {
      message.error(`创建模板失败：${error.message}`);
    }
  };

  // 删除模板
  const handleDelete = async (templateId) => {
    try {
      await templateAPI.delete(templateId);
      message.success(`模板 "${templateId}" 已删除`);
      loadTemplates();
    } catch (error) {
      message.error(`删除模板失败：${error.message}`);
    }
  };

  // 导出模板
  const handleExport = async (templateId) => {
    try {
      const result = await templateAPI.export(templateId);
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${templateId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success(`模板 "${templateId}" 已导出`);
    } catch (error) {
      message.error(`导出模板失败：${error.message}`);
    }
  };

  // 导入模板
  const handleImport = async () => {
    if (!importFile) {
      message.error('请选择要导入的文件');
      return;
    }
    try {
      await templateAPI.import(importFile);
      message.success('模板导入成功');
      setIsImportModalOpen(false);
      setImportFile(null);
      loadTemplates();
    } catch (error) {
      message.error(`导入模板失败：${error.message}`);
    }
  };

  // 过滤模板
  const filteredTemplates = templates.filter((t) => {
    const matchSearch =
      !searchText ||
      t.id.toLowerCase().includes(searchText.toLowerCase()) ||
      (t.name && t.name.toLowerCase().includes(searchText.toLowerCase())) ||
      (t.description && t.description.toLowerCase().includes(searchText.toLowerCase()));
    const matchCategory = !categoryFilter || t.category === categoryFilter;
    return matchSearch && matchCategory;
  });

  // 获取所有分类
  const categories = [...new Set(templates.map((t) => t.category).filter(Boolean))];

  // 表格列定义
  const columns = [
    {
      title: '模板 ID',
      dataIndex: 'id',
      key: 'id',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category) => (
        <Tag color={category === 'env' ? 'green' : category === 'agent' ? 'blue' : 'default'}>
          {category || 'general'}
        </Tag>
      ),
    },
    {
      title: '变量',
      dataIndex: 'variables',
      key: 'variables',
      render: (variables) => (
        <Space wrap>
          {(variables || []).slice(0, 3).map((v) => (
            <Tag key={v} color="orange">
              {v}
            </Tag>
          ))}
          {(variables || []).length > 3 && (
            <Tag color="default">+{(variables || []).length - 3}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (time) => (time ? time.slice(0, 19).replace('T', ' ') : '-'),
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
            onClick={() => navigate(`/templates/${record.id}`)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/templates/${record.id}/edit`)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => navigate(`/templates/${record.id}/apply`)}
          >
            应用
          </Button>
          <Button
            type="link"
            size="small"
            icon={<ExportOutlined />}
            onClick={() => handleExport(record.id)}
          >
            导出
          </Button>
          <Popconfirm
            title="确定要删除此模板吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button danger size="small" icon={<DeleteOutlined />}>
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
        title="模板管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadTemplates}>
              刷新
            </Button>
            <Button
              icon={<ImportOutlined />}
              onClick={() => setIsImportModalOpen(true)}
            >
              导入
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsCreateModalOpen(true)}
            >
              创建模板
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索模板 ID、名称或描述"
            allowClear
            style={{ width: 300 }}
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Select
            placeholder="全部分类"
            allowClear
            style={{ width: 150 }}
            value={categoryFilter}
            onChange={setCategoryFilter}
          >
            {categories.map((cat) => (
              <Select.Option key={cat} value={cat}>
                {cat}
              </Select.Option>
            ))}
          </Select>
        </Space>

        {filteredTemplates.length > 0 ? (
          <Table
            columns={columns}
            dataSource={filteredTemplates}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty
            description={searchText || categoryFilter ? '暂无匹配的模板' : '暂无模板，请创建或导入模板'}
          />
        )}
      </Card>

      {/* 创建模板对话框 */}
      <Modal
        title="创建新模板"
        open={isCreateModalOpen}
        onCancel={() => {
          setIsCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={700}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="id"
            label="模板 ID"
            rules={[
              { required: true, message: '请输入模板 ID' },
              {
                pattern: /^[a-zA-Z][a-zA-Z0-9_-]*$/,
                message: '只能以字母开头，包含字母、数字、下划线和连字符',
              },
            ]}
          >
            <Input placeholder="例如：dev-env, prod-agent" />
          </Form.Item>
          <Form.Item name="name" label="名称">
            <Input placeholder="模板名称（可选）" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="模板描述（可选）" />
          </Form.Item>
          <Form.Item name="category" label="分类">
            <Select placeholder="选择分类（可选）">
              <Select.Option value="env">环境配置</Select.Option>
              <Select.Option value="agent">Agent 配置</Select.Option>
              <Select.Option value="general">通用</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="content"
            label="模板内容（JSON 格式，使用 {VAR_NAME} 作为变量）"
            rules={[{ required: true, message: '请输入模板内容' }]}
          >
            <TextArea
              rows={10}
              placeholder={`{
  "database": {
    "host": "{DB_HOST:localhost}",
    "port": "{DB_PORT:5432}"
  },
  "api_url": "{API_BASE_URL}"
}`}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入模板对话框 */}
      <Modal
        title="导入模板"
        open={isImportModalOpen}
        onCancel={() => {
          setIsImportModalOpen(false);
          setImportFile(null);
        }}
        onOk={handleImport}
        destroyOnClose
      >
        <Upload.Dragger
          name="file"
          accept=".json"
          beforeUpload={(file) => {
            setImportFile(file);
            return false;
          }}
          onRemove={() => setImportFile(null)}
          maxCount={1}
        >
          <p className="ant-upload-drag-icon">
            <ImportOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽模板文件到此处上传</p>
          <p className="ant-upload-hint">仅支持 JSON 格式的模板文件</p>
        </Upload.Dragger>
        {importFile && (
          <div style={{ marginTop: 16 }}>
            <p>已选择文件：{importFile.name}</p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TemplateList;
