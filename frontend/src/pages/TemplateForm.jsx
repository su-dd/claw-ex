/**
 * 模板创建/编辑页面
 * 功能：创建新模板或编辑现有模板，支持变量自动提取
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  message,
  Alert,
  Typography,
  Row,
  Col,
  Tag,
} from 'antd';
import { ArrowLeftOutlined, SaveOutlined, SyncOutlined } from '@ant-design/icons';
import { templateAPI } from '../api/template';

const { TextArea } = Input;
const { Title, Text } = Typography;

const TemplateForm = () => {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [isEdit, setIsEdit] = useState(!!templateId);
  const [extractedVars, setExtractedVars] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isEdit && templateId) {
      loadTemplate();
    }
  }, [templateId]);

  const loadTemplate = async () => {
    setLoading(true);
    try {
      const data = await templateAPI.get(templateId);
      if (!data) {
        setError('模板不存在');
        return;
      }
      form.setFieldsValue({
        id: data.id,
        name: data.name,
        description: data.description,
        category: data.category,
        content: data.content ? JSON.stringify(data.content, null, 2) : '',
      });
      // 提取变量
      extractVariables(data.content ? JSON.stringify(data.content, null, 2) : '');
    } catch (error) {
      setError(`加载模板失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 从 JSON 内容中提取变量
  const extractVariables = (content) => {
    const regex = /\{([a-zA-Z_][a-zA-Z0-9_]*)(?::[^}]*)?\}/g;
    const vars = new Set();
    let match;
    while ((match = regex.exec(content)) !== null) {
      vars.add(match[1]);
    }
    setExtractedVars(Array.from(vars));
  };

  const handleContentChange = (e) => {
    const content = e.target.value;
    extractVariables(content);
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      let content;
      try {
        content = JSON.parse(values.content || '{}');
      } catch (e) {
        message.error('模板内容必须是有效的 JSON 格式');
        setLoading(false);
        return;
      }

      if (isEdit) {
        await templateAPI.update(templateId, {
          name: values.name,
          description: values.description,
          category: values.category,
          content,
          variables: extractedVars,
        });
        message.success(`模板 "${values.name || templateId}" 更新成功`);
      } else {
        await templateAPI.create({
          id: values.id,
          name: values.name,
          description: values.description,
          category: values.category,
          content,
          variables: extractedVars,
        });
        message.success(`模板 "${values.name || values.id}" 创建成功`);
      }
      navigate(`/templates/${values.id || templateId}`);
    } catch (error) {
      message.error(`${isEdit ? '更新' : '创建'}模板失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <Alert
        type="error"
        message={error}
        action={
          <Button type="primary" onClick={() => navigate('/templates')}>
            返回模板列表
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/templates')}>
              返回
            </Button>
            <span>{isEdit ? '编辑模板' : '创建模板'}</span>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          disabled={loading}
        >
          {!isEdit && (
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
              <Input placeholder="例如：dev-env, prod-agent" disabled={isEdit} />
            </Form.Item>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="名称">
                <Input placeholder="模板名称（可选）" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="category" label="分类">
                <Select placeholder="选择分类（可选）">
                  <Select.Option value="env">环境配置</Select.Option>
                  <Select.Option value="agent">Agent 配置</Select.Option>
                  <Select.Option value="general">通用</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="模板描述（可选）" />
          </Form.Item>

          <Form.Item
            name="content"
            label="模板内容（JSON 格式）"
            rules={[{ required: true, message: '请输入模板内容' }]}
            extra={
              <Space wrap>
                <Text type="secondary">
                  使用 {'{'}VAR_NAME{'}'} 或 {'{'}VAR_NAME:default{'}'} 格式定义变量
                </Text>
                {extractedVars.length > 0 && (
                  <>
                    <SyncOutlined spin={false} />
                    <Text type="secondary">自动提取到变量：</Text>
                    {extractedVars.map((v) => (
                      <Tag key={v} color="orange">
                        {v}
                      </Tag>
                    ))}
                  </>
                )}
              </Space>
            }
          >
            <TextArea
              rows={15}
              placeholder={`{
  "database": {
    "host": "{DB_HOST:localhost}",
    "port": "{DB_PORT:5432}"
  },
  "api_url": "{API_BASE_URL}"
}`}
              onChange={handleContentChange}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={loading}
              >
                {isEdit ? '保存修改' : '创建模板'}
              </Button>
              <Button onClick={() => navigate('/templates')}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default TemplateForm;
