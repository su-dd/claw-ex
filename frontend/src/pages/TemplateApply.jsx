/**
 * 模板应用页面
 * 功能：应用模板到目标配置，支持变量替换可视化编辑
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  message,
  Alert,
  Typography,
  Row,
  Col,
  Tag,
  Divider,
  Modal,
  Steps,
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { templateAPI } from '../api/template';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

const TemplateApply = () => {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [template, setTemplate] = useState(null);
  const [error, setError] = useState(null);
  const [previewResult, setPreviewResult] = useState(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    loadTemplate();
  }, [templateId]);

  const loadTemplate = async () => {
    setLoading(true);
    try {
      const data = await templateAPI.get(templateId);
      if (!data) {
        setError('模板不存在');
        return;
      }
      setTemplate(data);
    } catch (error) {
      setError(`加载模板失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleVariableChange = (varName, value) => {
    const currentVars = form.getFieldValue('variables') || {};
    form.setFieldsValue({
      variables: {
        ...currentVars,
        [varName]: value,
      },
    });
  };

  const handlePreview = async () => {
    const values = form.getFieldsValue();
    if (!values.target_path) {
      message.error('请输入目标路径');
      setCurrentStep(1);
      return;
    }

    setLoading(true);
    try {
      const result = await templateAPI.preview(templateId, values.variables || {});
      setPreviewResult(result);
      setIsPreviewModalOpen(true);
      message.success('预览成功');
    } catch (error) {
      message.error(`预览失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    const values = form.getFieldsValue();
    if (!values.target_path) {
      message.error('请输入目标路径');
      setCurrentStep(1);
      return;
    }

    setLoading(true);
    try {
      const result = await templateAPI.apply(templateId, values.target_path, values.variables || {});
      message.success(`模板已应用到 ${values.target_path}`);
      navigate(`/templates/${templateId}`);
    } catch (error) {
      message.error(`应用模板失败：${error.message}`);
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
            <span>应用模板：{template.name || template.id}</span>
          </Space>
        }
      >
        <Steps
          current={currentStep}
          onChange={setCurrentStep}
          items={[
            {
              title: '选择目标',
              description: '指定目标配置文件路径',
            },
            {
              title: '变量替换',
              description: '填写变量值',
            },
            {
              title: '预览并应用',
              description: '确认并应用模板',
            },
          ]}
          style={{ marginBottom: 24 }}
        />

        <Form form={form} layout="vertical">
          {/* 步骤 1：目标路径 */}
          <div style={{ display: currentStep === 0 ? 'block' : 'none' }}>
            <Form.Item
              name="target_path"
              label="目标配置文件路径"
              rules={[{ required: true, message: '请输入目标路径' }]}
              extra="例如：~/.openclaw/envs/dev.json 或 /path/to/config.json"
            >
              <Input
                placeholder="~/.openclaw/envs/dev.json"
                size="large"
                onPressEnter={() => setCurrentStep(1)}
              />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" onClick={() => setCurrentStep(1)}>
                  下一步：变量替换
                </Button>
              </Space>
            </Form.Item>
          </div>

          {/* 步骤 2：变量替换 */}
          <div style={{ display: currentStep === 1 ? 'block' : 'none' }}>
            <Divider orientation="left">变量替换</Divider>
            {template.variables && template.variables.length > 0 ? (
              <Row gutter={16}>
                {template.variables.map((varName) => (
                  <Col span={12} key={varName} style={{ marginBottom: 16 }}>
                    <Form.Item
                      label={
                        <Space>
                          <Tag color="orange">{varName}</Tag>
                        </Space>
                      }
                      name={['variables', varName]}
                      extra={`在模板中使用：{'{'}${varName}{'}'} 或 {'{'}${varName}:default{'}'}`}
                    >
                      <Input
                        placeholder={`输入 ${varName} 的值`}
                        onChange={(e) => handleVariableChange(varName, e.target.value)}
                      />
                    </Form.Item>
                  </Col>
                ))}
              </Row>
            ) : (
              <Alert type="info" message="此模板没有变量，无需替换" />
            )}

            <Form.Item>
              <Space>
                <Button onClick={() => setCurrentStep(0)}>上一步</Button>
                <Button type="primary" onClick={() => setCurrentStep(2)}>
                  下一步：预览
                </Button>
              </Space>
            </Form.Item>
          </div>

          {/* 步骤 3：预览并应用 */}
          <div style={{ display: currentStep === 2 ? 'block' : 'none' }}>
            <Divider orientation="left">确认应用</Divider>
            <Alert
              type="info"
              message={
                <div>
                  <p>
                    <strong>模板：</strong>
                    {template.name || template.id}
                  </p>
                  <p>
                    <strong>目标路径：</strong>
                    {form.getFieldValue('target_path')}
                  </p>
                  <p>
                    <strong>变量数量：</strong>
                    {Object.keys(form.getFieldValue('variables') || {}).length} /{' '}
                    {template.variables?.length || 0}
                  </p>
                </div>
              }
              style={{ marginBottom: 16 }}
            />

            <Form.Item>
              <Space>
                <Button onClick={() => setCurrentStep(1)}>上一步</Button>
                <Button
                  onClick={handlePreview}
                  loading={loading}
                  disabled={!form.getFieldValue('target_path')}
                >
                  预览
                </Button>
                <Button
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  onClick={handleApply}
                  loading={loading}
                  disabled={!form.getFieldValue('target_path')}
                >
                  确认应用
                </Button>
              </Space>
            </Form.Item>
          </div>
        </Form>
      </Card>

      {/* 预览对话框 */}
      <Modal
        title="预览结果"
        open={isPreviewModalOpen}
        onCancel={() => setIsPreviewModalOpen(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setIsPreviewModalOpen(false)}>
            关闭
          </Button>,
        ]}
      >
        {previewResult && (
          <div>
            <Paragraph
              copyable={{
                text: typeof previewResult === 'string' ? previewResult : JSON.stringify(previewResult, null, 2),
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
                {typeof previewResult === 'string'
                  ? previewResult
                  : JSON.stringify(previewResult, null, 2)}
              </pre>
            </Paragraph>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TemplateApply;
