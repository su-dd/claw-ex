import React, { useState, useEffect } from 'react';
import { exportAPI, importAPI } from '../api/modules';
import './ExportImport.css';

const ExportImport = () => {
  const [activeTab, setActiveTab] = useState('export');
  const [exportType, setExportType] = useState('agent');
  const [exportFormat, setExportFormat] = useState('json');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [outputPath, setOutputPath] = useState('');
  const [importFile, setImportFile] = useState('');
  const [overwrite, setOverwrite] = useState(false);
  const [exportable, setExportable] = useState({ agents: [], templates: [], env_config: false });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadExportable();
  }, []);

  const loadExportable = async () => {
    try {
      const data = await exportAPI.listExportable();
      if (data.success) {
        setExportable(data);
        if (data.agents.length > 0) {
          setSelectedAgent(data.agents[0]);
        }
        if (data.templates.length > 0) {
          setSelectedTemplate(data.templates[0]);
        }
      }
    } catch (error) {
      console.error('加载可导出项目失败:', error);
    }
  };

  const handleExport = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      let params = {
        type: exportType,
        format: exportFormat,
        output_path: outputPath || `./export-${Date.now()}.${exportFormat}`
      };

      if (exportType === 'agent') {
        params.agent_name = selectedAgent;
      } else if (exportType === 'template') {
        params.template_name = selectedTemplate;
      }

      const result = await exportAPI.export(params);
      
      if (result.success) {
        setMessage({ type: 'success', text: `导出成功：${result.output}` });
      } else {
        setMessage({ type: 'error', text: `导出失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `导出失败：${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const result = await importAPI.import({
        input_path: importFile,
        overwrite: overwrite
      });

      if (result.success) {
        setMessage({ type: 'success', text: '导入成功' });
        loadExportable();
      } else {
        setMessage({ type: 'error', text: `导入失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `导入失败：${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="export-import-container">
      <h2>📦 导入导出管理</h2>

      <div className="tabs">
        <button 
          className={activeTab === 'export' ? 'active' : ''}
          onClick={() => setActiveTab('export')}
        >
          导出
        </button>
        <button 
          className={activeTab === 'import' ? 'active' : ''}
          onClick={() => setActiveTab('import')}
        >
          导入
        </button>
      </div>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {activeTab === 'export' && (
        <div className="export-panel">
          <div className="form-group">
            <label>导出类型:</label>
            <select value={exportType} onChange={(e) => setExportType(e.target.value)}>
              <option value="agent">Agent 配置</option>
              <option value="template">模板</option>
              <option value="env">环境配置</option>
              <option value="all">全部</option>
            </select>
          </div>

          {exportType === 'agent' && (
            <div className="form-group">
              <label>选择 Agent:</label>
              <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
                {exportable.agents.map(agent => (
                  <option key={agent} value={agent}>{agent}</option>
                ))}
              </select>
            </div>
          )}

          {exportType === 'template' && (
            <div className="form-group">
              <label>选择模板:</label>
              <select value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)}>
                {exportable.templates.map(template => (
                  <option key={template} value={template}>{template}</option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group">
            <label>文件格式:</label>
            <select value={exportFormat} onChange={(e) => setExportFormat(e.target.value)}>
              <option value="json">JSON</option>
              <option value="yaml">YAML</option>
            </select>
          </div>

          <div className="form-group">
            <label>输出路径:</label>
            <input 
              type="text" 
              value={outputPath}
              onChange={(e) => setOutputPath(e.target.value)}
              placeholder="./export.json"
            />
          </div>

          <button className="btn-primary" onClick={handleExport} disabled={loading}>
            {loading ? '导出中...' : '开始导出'}
          </button>
        </div>
      )}

      {activeTab === 'import' && (
        <div className="import-panel">
          <div className="form-group">
            <label>导入文件:</label>
            <input 
              type="text" 
              value={importFile}
              onChange={(e) => setImportFile(e.target.value)}
              placeholder="./backup.json"
            />
          </div>

          <div className="form-group checkbox">
            <label>
              <input 
                type="checkbox"
                checked={overwrite}
                onChange={(e) => setOverwrite(e.target.checked)}
              />
              覆盖已存在的配置
            </label>
          </div>

          <button className="btn-primary" onClick={handleImport} disabled={loading}>
            {loading ? '导入中...' : '开始导入'}
          </button>
        </div>
      )}

      <div className="info-panel">
        <h3>可导出项目</h3>
        <div className="info-grid">
          <div className="info-item">
            <strong>Agents:</strong> {exportable.agents.length} 个
          </div>
          <div className="info-item">
            <strong>模板:</strong> {exportable.templates.length} 个
          </div>
          <div className="info-item">
            <strong>环境配置:</strong> {exportable.env_config ? '✓' : '✗'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportImport;
