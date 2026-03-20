import React, { useState, useEffect } from 'react';
import { cronAPI } from '../api/modules';
import './CronManager.css';

const CronManager = () => {
  const [jobs, setJobs] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  const [formData, setFormData] = useState({
    name: '',
    schedule: '0 2 * * *',
    command: '',
    description: '',
    enabled: true
  });

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const data = await cronAPI.list();
      if (data.success) {
        setJobs(data.jobs);
      }
    } catch (error) {
      console.error('加载定时任务失败:', error);
    }
  };

  const handleCreate = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const result = await cronAPI.create({
        name: formData.name,
        schedule: formData.schedule,
        command: formData.command,
        description: formData.description,
        enabled: formData.enabled
      });

      if (result.success) {
        setMessage({ type: 'success', text: '定时任务创建成功' });
        setShowCreateForm(false);
        loadJobs();
        setFormData({
          name: '',
          schedule: '0 2 * * *',
          command: '',
          description: '',
          enabled: true
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
    if (!confirm('确定要删除此定时任务吗？')) return;

    try {
      const result = await cronAPI.delete(id);
      if (result.success) {
        setMessage({ type: 'success', text: '定时任务已删除' });
        loadJobs();
      } else {
        setMessage({ type: 'error', text: `删除失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `删除失败：${error.message}` });
    }
  };

  const handleRun = async (job) => {
    if (!confirm(`确定要立即执行任务 "${job.name}" 吗？`)) return;

    setLoading(true);
    try {
      const result = await cronAPI.run(job.id);
      if (result.success) {
        setMessage({ type: 'success', text: '任务执行完成' });
        loadJobs();
      } else {
        setMessage({ type: 'error', text: `执行失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `执行失败：${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (job) => {
    try {
      const result = await cronAPI.enable(job.id, !job.enabled);
      if (result.success) {
        setMessage({ type: 'success', text: job.enabled ? '任务已禁用' : '任务已启用' });
        loadJobs();
      } else {
        setMessage({ type: 'error', text: `操作失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `操作失败：${error.message}` });
    }
  };

  const handleViewLogs = async (job) => {
    setLoading(true);
    try {
      const result = await cronAPI.logs(job.id);
      if (result.success) {
        setLogs(result.logs);
        setSelectedJob(job);
        setShowLogs(true);
      } else {
        setMessage({ type: 'error', text: `加载日志失败：${result.error}` });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `加载日志失败：${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const parseCronExpression = (expr) => {
    const parts = expr.split(' ');
    const meanings = [
      '分钟', '小时', '日期', '月份', '星期'
    ];
    return parts.map((p, i) => `${p} (${meanings[i]})`).join(' ');
  };

  return (
    <div className="cron-manager-container">
      <h2>⏰ Cron 定时任务管理</h2>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="toolbar">
        <button className="btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? '取消创建' : '+ 新建任务'}
        </button>
        <button className="btn-secondary" onClick={loadJobs}>
          🔄 刷新
        </button>
      </div>

      {showCreateForm && (
        <div className="create-form">
          <h3>创建定时任务</h3>
          
          <div className="form-group">
            <label>任务名称:</label>
            <input 
              type="text" 
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="例如：每日备份"
            />
          </div>

          <div className="form-group">
            <label>Cron 表达式:</label>
            <input 
              type="text" 
              value={formData.schedule}
              onChange={(e) => setFormData({...formData, schedule: e.target.value})}
              placeholder="0 2 * * *"
            />
            <small className="help-text">
              格式：分 时 日 月 周 | 示例：0 2 * * * (每天 2:00)
            </small>
          </div>

          <div className="form-group">
            <label>执行命令:</label>
            <input 
              type="text" 
              value={formData.command}
              onChange={(e) => setFormData({...formData, command: e.target.value})}
              placeholder="claw-ex backup"
            />
          </div>

          <div className="form-group">
            <label>描述:</label>
            <textarea 
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="任务描述..."
              rows="3"
            />
          </div>

          <div className="form-group checkbox">
            <label>
              <input 
                type="checkbox"
                checked={formData.enabled}
                onChange={(e) => setFormData({...formData, enabled: e.target.checked})}
              />
              启用任务
            </label>
          </div>

          <button className="btn-primary" onClick={handleCreate} disabled={loading}>
            {loading ? '创建中...' : '创建任务'}
          </button>
        </div>
      )}

      {showLogs && selectedJob && (
        <div className="logs-panel">
          <h3>任务日志：{selectedJob.name}
            <button className="btn-close" onClick={() => setShowLogs(false)}>×</button>
          </h3>
          <div className="logs-list">
            {logs.length === 0 ? (
              <p className="empty">暂无执行日志</p>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="log-item">
                  <div className="log-header">
                    <span className="log-time">{new Date(log.timestamp).toLocaleString()}</span>
                    <span className={`log-status ${log.status}`}>
                      {log.status === 'completed' ? '✅' : '❌'} {log.status}
                    </span>
                    <span className="log-duration">耗时：{log.duration?.toFixed(2) || 'N/A'}s</span>
                  </div>
                  {log.output && (
                    <pre className="log-output">{log.output.slice(0, 500)}</pre>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="jobs-list">
        <h3>定时任务 ({jobs.length})</h3>
        
        {jobs.length === 0 ? (
          <p className="empty">暂无定时任务</p>
        ) : (
          <table className="jobs-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>Schedule</th>
                <th>命令</th>
                <th>下次运行</th>
                <th>状态</th>
                <th>执行次数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => (
                <tr key={job.id}>
                  <td>
                    <div className="job-name">{job.name}</div>
                    {job.description && <small className="job-desc">{job.description}</small>}
                  </td>
                  <td>
                    <code>{job.schedule}</code>
                    <small className="help-text">{parseCronExpression(job.schedule)}</small>
                  </td>
                  <td><code className="command">{job.command}</code></td>
                  <td>{job.next_run ? new Date(job.next_run).toLocaleString() : '计算中'}</td>
                  <td>
                    <span className={`status-badge ${job.enabled ? 'enabled' : 'disabled'}`}>
                      {job.enabled ? '🟢 已启用' : '🔴 已禁用'}
                    </span>
                  </td>
                  <td>{job.run_count || 0}</td>
                  <td className="actions">
                    <button className="btn-sm" onClick={() => handleRun(job)}>运行</button>
                    <button className="btn-sm" onClick={() => handleToggle(job)}>
                      {job.enabled ? '禁用' : '启用'}
                    </button>
                    <button className="btn-sm" onClick={() => handleViewLogs(job)}>日志</button>
                    <button className="btn-sm btn-danger" onClick={() => handleDelete(job.id)}>删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="cron-help">
        <h4>Cron 表达式示例</h4>
        <div className="examples">
          <div className="example">
            <code>* * * * *</code>
            <span>每分钟执行</span>
          </div>
          <div className="example">
            <code>0 * * * *</code>
            <span>每小时整点执行</span>
          </div>
          <div className="example">
            <code>0 2 * * *</code>
            <span>每天凌晨 2 点执行</span>
          </div>
          <div className="example">
            <code>0 0 * * 0</code>
            <span>每周日凌晨执行</span>
          </div>
          <div className="example">
            <code>0 0 1 * *</code>
            <span>每月 1 号凌晨执行</span>
          </div>
          <div className="example">
            <code>*/5 * * * *</code>
            <span>每 5 分钟执行</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CronManager;
