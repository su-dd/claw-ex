/**
 * 模板详情页面
 * 功能：展示模板详细信息、变量列表、内容预览
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tag,
  Space,
  Button,
  message,
  Spin,
  Alert,
  Typography,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  PlayCircleOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { templateAPI } from '../api/template';

const { Title, Text } = Typography;
const { Paragraph } = Typography;

const TemplateDetail = () => {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [template, setTemplate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTemplate();
  }, [templateId]);

  const loadTemplate = async () => {
    setLoading(true);
    try {
      const data = await templateAPI.get(templateId);
      if (!data) {
        setError('模板不存在');
      } else {
        setTemplate(data);
      }
    } catch (error) {
      setError(`加载模板失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载模板详情..." />
      </div>
    );
  }

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

  if (!template) {
    return (
      <Alert
        type="warning"
        message="模板不存在"
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
            <span>{template.name || template.id}</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<EditOutlined />}
              onClick={() => navigate(`/templates/${templateId}/edit`)}
            >
              编辑
            </Button>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => navigate(`/templates/${templateId}/apply`)}
            >
              应用模板
            </Button>
            <Button icon={<ExportOutlined />} onClick={handleExport}>
              导出
            </Button>
          </Space>
        }
      >
        <Descriptions bordered column={2}>
          <Descriptions.Item label="模板 ID">{template.id}</Descriptions.Item>
          <Descriptions.Item label="名称">{template.name || '-'}</Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>
            {template.description || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="分类">
            <Tag color={template.category === 'env' ? 'green' : template.category === 'agent' ? 'blue' : 'default'}>
              {template.category || 'general'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {template.created_at ? template.created_at.slice(0, 19).replace('T', ' ') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {template.updated_at ? template.updated_at.slice(0, 19).replace('T', ' ') : '-'}
          </Descriptions.Item>
        </Descriptions>

        <Divider orientation="left">模板变量</Divider>
        {template.variables && template.variables.length > 0 ? (
          <Space wrap>
            {template.variables.map((v) => (
              <Tag key={v} color="orange" style={{ fontSize: 14 }}>
                {v}
              </Tag>
            ))}
          </Space>
        ) : (
          <Text type="secondary">无变量</Text>
        )}

        {template.content && (
          <>
            <Divider orientation="left">模板内容</Divider>
            <Card type="inner" title="JSON 预览">
              <Paragraph
                copyable={{
                  text: JSON.stringify(template.content, null, 2),
                  tooltips: ['复制', '已复制'],
                }}
              >
                <pre
                  style={{
                    background: '#f5f5f5',
                    padding: 16,
                    borderRadius: 4,
                    overflow: 'auto',
                    maxHeight: 500,
                  }}
                >
                  {JSON.stringify(template.content, null, 2)}
                </pre>
              </Paragraph>
            </Card>
          </>
        )}

        {template.content_error && (
          <Alert
            type="error"
            message="模板内容加载失败"
            description={template.content_error}
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    </div>
  );
};

export default TemplateDetail;
