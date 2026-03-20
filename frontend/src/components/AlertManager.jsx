import React, { useState, useEffect } from 'react';
import { alertAPI } from '../api/modules';
import './AlertManager.css';

const AlertManager = () => {
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  const [formData, setFormData] = useState({
    name: '',
    metric: 'cpu',
    operator: 'gt',
    threshold: 80,
    channel: 'feishu',
    webhook_url: '',
    severity: 'medium',
    cooldown_minutes: 15
  });

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const data = await alertAPI.list();
      if (data.success) {
        setAlerts(data.alerts);
      }
    } catch (error) {
      console.error('加载告警规则失败:', error);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await alertAPI.history();
      if (data.success) {
        setHistory(data.history);
        setShowHistory(true);
      }
    } catch (error) {
      console.error('加载告警历史失败:', error);
    }
  };

  const handleCreate = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const channelConfig = {};
      if (formData.channel === 'feishu') {
        channelConfig.webhook_url = formData.webhook_url;
      } else if (formData.channel === 'webhook') {
        channelConfig.url = formData.webhook_url;
      } else if (formData.channel === 'email') {
        channelConfig.to = formData.webhook_url;
      }

      const result = await alertAPI.create({
        name: formData.name,
        metric: formData.metric,
        operator: formData.operator,
        threshold: parseFloat(formData.threshold),
        channel: formData.channel,
        channel_config: channelConfig,
        severity: formData.severity,
        cooldown_minutes: parseInt(formData.cooldown_minutes)
      });

      if (result.success) {
        setMessage({ type: 'success', text: '告警规则创建成功' });
        setShowCreateForm(false);
        loadAlerts();
        setFormData({
          name: '',
          metric: 'cpu',
          operator: 'gt',
          threshold: 80,
          channel: 'feishu',
          webhook_url: '',
          severity: 'medium',
          cooldown_minutes: 15
        });
      } else {
        setMessage({ type: 'error', text: `创建失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `创建失败：${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('确定要删除此告警规则吗？')) return;

    try {
      const result = await alertAPI.delete(id);
      if (result.success) {
        setMessage({ type: 'success', text: '告警规则已删除' });
        loadAlerts();
      } else {
        setMessage({ type: 'error', text: `删除失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `删除失败：${error.message}` });
    }
  };

  const handleTest = async (alert) => {
    try {
      const result = await alertAPI.test({
        channel: alert.channel,
        config: alert.channel_config,
        message: `测试告警：${alert.name}`
      });

      if (result.success) {
        setMessage({ type: 'success', text: '测试通知发送成功' });
      } else {
        setMessage({ type: 'error', text: `测试失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `测试失败：${error.message}` });
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: '#28a745',
      medium: '#ffc107',
      high: '#fd7e14',
      critical: '#dc3545'
    };
    return colors[severity] || '#6c757d';
  };

  return (
    <div className="alert-manager-container">
      <h2>🔔 警告通知管理</h2>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="toolbar">
        <button className="btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? '取消创建' : '+ 新建告警'}
        </button>
        <button className="btn-secondary" onClick={loadHistory}>
          📜 历史记录
        </button>
        <button className="btn-secondary" onClick={loadAlerts}>
          🔄 刷新
        </button>
      </div>

      {showCreateForm && (
        <div className="create-form">
          <h3>创建告警规则</h3>
          
          <div className="form-group">
            <label>名称:</label>
            <input 
              type="text" 
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="例如：CPU 高负载"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>监控指标:</label>
              <select value={formData.metric} onChange={(e) => setFormData({...formData, metric: e.target.value})}>
                <option value="cpu">CPU 使用率</option>
                <option value="memory">内存使用率</option>
                <option value="disk">磁盘使用率</option>
                <option value="task_failure">任务失败次数</option>
                <option value="session_count">会话数量</option>
              </select>
            </div>

            <div className="form-group">
              <label>操作符:</label>
              <select value={formData.operator} onChange={(e) => setFormData({...formData, operator: e.target.value})}>
                <option value="gt">大于 (&gt;)</option>
                <option value="lt">小于 (&lt;)</option>
                <option value="eq">等于 (=)</option>
                <option value="gte">大于等于 (≥)</option>
                <option value="lte">小于等于 (≤)</option>
              </select>
            </div>

            <div className="form-group">
              <label>阈值:</label>
              <input 
                type="number" 
                value={formData.threshold}
                onChange={(e) => setFormData({...formData, threshold: e.target.value})}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>通知渠道:</label>
              <select value={formData.channel} onChange={(e) => setFormData({...formData, channel: e.target.value})}>
                <option value="feishu">飞书</option>
                <option value="webhook">Webhook</option>
                <option value="email">邮件</option>
              </select>
            </div>

            <div className="form-group">
              <label>严重性:</label>
              <select value={formData.severity} onChange={(e) => setFormData({...formData, severity: e.target.value})}>
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="critical">严重</option>
              </select>
            </div>

            <div className="form-group">
              <label>冷却时间 (分钟):</label>
              <input 
                type="number" 
                value={formData.cooldown_minutes}
                onChange={(e) => setFormData({...formData, cooldown_minutes: e.target.value})}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Webhook URL / 邮箱:</label>
            <input 
              type="text" 
              value={formData.webhook_url}
              onChange={(e) => setFormData({...formData, webhook_url: e.target.value})}
              placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
            />
          </div>

          <button className="btn-primary" onClick={handleCreate} disabled={loading}>
            {loading ? '创建中...' : '创建告警'}
          </button>
        </div>
      )}

      {showHistory && (
        <div className="history-panel">
          <h3>告警历史 
            <button className="btn-close" onClick={() => setShowHistory(false)}>×</button>
          </h3>
          <div className="history-list">
            {history.length === 0 ? (
              <p className="empty">暂无历史记录</p>
            ) : (
              history.slice(-20).reverse().map((entry, idx) => (
                <div key={idx} className="history-item">
                  <span className="time">{new Date(entry.triggered_at).toLocaleString()}</span>
                  <span className="rule">{entry.rule_name}</span>
                  <span className="metric">{entry.metric}: {entry.value}</span>
                  <span className={`status ${entry.status}`}>{entry.status === 'sent' ? '✓' : '✗'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="alerts-list">
        <h3>告警规则 ({alerts.length})</h3>
        
        {alerts.length === 0 ? (
          <p className="empty">暂无告警规则</p>
        ) : (
          <table className="alerts-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>指标</th>
                <th>条件</th>
                <th>渠道</th>
                <th>严重性</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map(alert => (
                <tr key={alert.id}>
                  <td>{alert.name}</td>
                  <td>{alert.metric}</td>
                  <td>{alert.operator} {alert.threshold}</td>
                  <td>{alert.channel}</td>
                  <td>
                    <span 
                      className="severity-badge"
                      style={{backgroundColor: getSeverityColor(alert.severity)}}
                    >
                      {alert.severity}
                    </span>
                  </td>
                  <td>{alert.enabled ? '🟢' : '🔴'}</td>
                  <td className="actions">
                    <button className="btn-sm" onClick={() => handleTest(alert)}>测试</button>
                    <button className="btn-sm btn-danger" onClick={() => handleDelete(alert.id)}>删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AlertManager;
