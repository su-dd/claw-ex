/**
 * Agent 配置管理页面
 * 功能：Agent 列表、配置查看/编辑、配置验证、备份恢复
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Card,
  Space,
  Tag,
  message,
  Modal,
  Tree,
  Select,
  Form,
  Input,
  InputNumber,
  Switch,
  Divider,
  Empty,
  Popconfirm,
} from 'antd';
import {
  ReloadOutlined,
  EditOutlined,
  CheckOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { agentAPI } from '../api';

const { TextArea } = Input;

const AgentConfig = () => {
  const [loading, setLoading] = useState(false);
  const [agentList, setAgentList] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [configData, setConfigData] = useState(null);
  const [configFile, setConfigFile] = useState('models.json');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isBackupModalOpen, setIsBackupModalOpen] = useState(false);
  const [backupList, setBackupList] = useState([]);
  const [editingData, setEditingData] = useState(null);
  const [form] = Form.useForm();

  // 加载 Agent 列表
  const loadAgentList = async () => {
    setLoading(true);
    try {
      const data = await agentAPI.list();
      setAgentList(data || []);
    } catch (error) {
      message.error(`加载 Agent 列表失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgentList();
  }, []);

  // 加载 Agent 配置
  const loadAgentConfig = async (agentName, file = 'models.json') => {
    try {
      const data = await agentAPI.getConfig(agentName, file);
      setConfigData(data);
      setSelectedAgent(agentName);
      setConfigFile(file);
    } catch (error) {
      message.error(`加载配置失败：${error.message}`);
      setConfigData(null);
    }
  };

  // 验证配置
  const handleValidate = async () => {
    if (!selectedAgent) return;
    
    try {
      const result = await agentAPI.validate(selectedAgent, configFile);
      message.success(result.message || '配置验证通过');
    } catch (error) {
      message.error(`配置验证失败：${error.message}`);
    }
  };

  // 打开编辑对话框
  const handleEdit = () => {
    if (!configData) return;
    setEditingData(JSON.parse(JSON.stringify(configData)));
    setIsEditModalOpen(true);
  };

  // 保存配置
  const handleSaveConfig = async (values) => {
    if (!selectedAgent) return;

    try {
      await agentAPI.updateConfig(selectedAgent, configFile, values);
      message.success('配置已保存');
      setIsEditModalOpen(false);
      loadAgentConfig(selectedAgent, configFile);
    } catch (error) {
      message.error(`保存配置失败：${error.message}`);
    }
  };

  // 打开备份列表
  const handleShowBackups = async () => {
    if (!selectedAgent) return;

    try {
      const data = await agentAPI.getBackups(selectedAgent);
      setBackupList(data || []);
      setIsBackupModalOpen(true);
    } catch (error) {
      message.error(`加载备份列表失败：${error.message}`);
    }
  };

  // 恢复备份
  const handleRestore = async (backupFile) => {
    if (!selectedAgent) return;

    try {
      await agentAPI.restore(selectedAgent, backupFile);
      message.success('配置已恢复');
      setIsBackupModalOpen(false);
      loadAgentConfig(selectedAgent, configFile);
    } catch (error) {
      message.error(`恢复配置失败：${error.message}`);
    }
  };

  // 渲染配置树
  const renderConfigTree = (data, parentKey = '') => {
    if (!data || typeof data !== 'object') {
      return [];
    }

    return Object.entries(data).map(([key, value]) => {
      const nodeKey = parentKey ? `${parentKey}.${key}` : key;
      
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return {
          title: <strong>{key}</strong>,
          key: nodeKey,
          children: renderConfigTree(value, nodeKey),
        };
      } else {
        let displayValue = value;
        let isSensitive = false;
        
        // 敏感字段判断
        const sensitiveKeys = ['key', 'secret', 'token', 'password', 'api_key', 'apikey'];
        if (sensitiveKeys.some((k) => key.toLowerCase().includes(k))) {
          displayValue = '••••••••';
          isSensitive = true;
        }

        return {
          title: (
            <Space>
              <span>{key}:</span>
              <Tag color={isSensitive ? 'red' : 'default'}>
                {isSensitive ? '🔒 敏感' : typeof value}
              </Tag>
              <span style={{ color: '#666' }}>{displayValue}</span>
            </Space>
          ),
          key: nodeKey,
          isLeaf: true,
        };
      }
    });
  };

  // 表格列定义
  const columns = [
    {
      title: 'Agent 名称',
      dataIndex: 'name',
      key: 'name',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '配置文件',
      key: 'config',
      render: (_, record) => (
        <Space>
          {record.has_models && <Tag color="blue">models.json</Tag>}
          {record.has_auth && <Tag color="green">auth-profiles.json</Tag>}
        </Space>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record) => (
        <Tag color={record.has_models || record.has_auth ? 'success' : 'default'}>
          {record.has_models || record.has_auth ? '已配置' : '未配置'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            onClick={() => loadAgentConfig(record.name, record.has_models ? 'models.json' : 'auth-profiles.json')}
          >
            查看配置
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="Agent 配置管理"
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadAgentList}>
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={agentList}
          rowKey="name"
          loading={loading}
          pagination={{ pageSize: 10 }}
          onRow={(record) => ({
            onClick: () => loadAgentConfig(record.name, record.has_models ? 'models.json' : 'auth-profiles.json'),
            style: { cursor: 'pointer' },
          })}
        />
      </Card>

      {/* 配置查看区域 */}
      {configData && (
        <Card
          title={`${selectedAgent} - ${configFile}`}
          style={{ marginTop: 16 }}
          extra={
            <Space>
              <Select
                value={configFile}
                onChange={(file) => loadAgentConfig(selectedAgent, file)}
                style={{ width: 150 }}
              >
                <Select.Option value="models.json">models.json</Select.Option>
                <Select.Option value="auth-profiles.json">auth-profiles.json</Select.Option>
              </Select>
              <Button icon={<EditOutlined />} onClick={handleEdit}>
                编辑
              </Button>
              <Button icon={<CheckOutlined />} onClick={handleValidate}>
                验证
              </Button>
              <Button icon={<HistoryOutlined />} onClick={handleShowBackups}>
                备份历史
              </Button>
            </Space>
          }
        >
          <Tree
            treeData={renderConfigTree(configData)}
            defaultExpandAll
            showLine
          />
        </Card>
      )}

      {/* 编辑配置对话框 */}
      <Modal
        title={`编辑配置 - ${configFile}`}
        open={isEditModalOpen}
        onCancel={() => setIsEditModalOpen(false)}
        onOk={() => form.submit()}
        width={800}
        destroyOnClose
      >
        {editingData && (
          <DynamicForm
            data={editingData}
            form={form}
            onFinish={handleSaveConfig}
          />
        )}
      </Modal>

      {/* 备份历史对话框 */}
      <Modal
        title="备份历史"
        open={isBackupModalOpen}
        onCancel={() => setIsBackupModalOpen(false)}
        footer={null}
        width={600}
      >
        {backupList.length > 0 ? (
          <Table
            dataSource={backupList}
            rowKey="file"
            pagination={{ pageSize: 5 }}
            columns={[
              {
                title: '备份文件',
                dataIndex: 'file',
                key: 'file',
              },
              {
                title: '操作',
                key: 'action',
                render: (_, record) => (
                  <Popconfirm
                    title="确定要恢复此备份吗？"
                    onConfirm={() => handleRestore(record.file)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button type="primary" size="small">
                      恢复
                    </Button>
                  </Popconfirm>
                ),
              },
            ]}
          />
        ) : (
          <Empty description="暂无备份" />
        )}
      </Modal>
    </div>
  );
};

// 动态表单组件（用于编辑配置）
const DynamicForm = ({ data, form, onFinish }) => {
  const renderFields = (obj, prefix = '') => {
    return Object.entries(obj).map(([key, value]) => {
      const fieldName = prefix ? `${prefix}.${key}` : key;
      
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return (
          <React.Fragment key={fieldName}>
            <Divider orientation="left">{key}</Divider>
            {renderFields(value, fieldName)}
          </React.Fragment>
        );
      }

      // 敏感字段不显示编辑
      const sensitiveKeys = ['key', 'secret', 'token', 'password', 'api_key', 'apikey'];
      const isSensitive = sensitiveKeys.some((k) => key.toLowerCase().includes(k));

      if (isSensitive) {
        return null;
      }

      let fieldComponent;
      if (typeof value === 'boolean') {
        fieldComponent = <Switch />;
      } else if (typeof value === 'number') {
        fieldComponent = <InputNumber style={{ width: '100%' }} />;
      } else if (typeof value === 'string' && value.length > 100) {
        fieldComponent = <TextArea rows={4} />;
      } else {
        fieldComponent = <Input />;
      }

      return (
        <Form.Item
          key={fieldName}
          name={fieldName}
          label={key}
          initialValue={value}
        >
          {fieldComponent}
        </Form.Item>
      );
    });
  };

  return <Form form={form} layout="vertical" onFinish={onFinish}>{renderFields(data)}</Form>;
};

export default AgentConfig;
