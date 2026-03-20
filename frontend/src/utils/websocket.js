/**
 * WebSocket 连接管理
 * 用于实时监控任务状态
 */

class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectTimer = null;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
    this.isConnected = false;
  }

  /**
   * 连接 WebSocket
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.clearReconnectTimer();
        this.emit('connect');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message:', data);
          this.emit('message', data);
          
          // 根据事件类型触发特定监听器
          if (data.event) {
            this.emit(`event:${data.event}`, data.data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.isConnected = false;
        this.emit('disconnect');
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.clearReconnectTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * 安排重连
   */
  scheduleReconnect() {
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      this.connect();
    }, this.reconnectDelay);
  }

  /**
   * 清除重连定时器
   */
  clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 发送消息
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, message not sent:', data);
    }
  }

  /**
   * 订阅事件
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * 取消订阅
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket listener for event ${event}:`, error);
        }
      });
    }
  }

  /**
   * 订阅会话监控
   */
  subscribeSession(sessionId) {
    this.send({
      action: 'subscribe',
      session_id: sessionId,
    });
  }

  /**
   * 取消订阅会话
   */
  unsubscribeSession(sessionId) {
    this.send({
      action: 'unsubscribe',
      session_id: sessionId,
    });
  }
}

// 创建单例实例
let wsManager = null;

export const getWebSocketManager = (url = 'ws://localhost:8000/ws') => {
  if (!wsManager) {
    wsManager = new WebSocketManager(url);
  }
  return wsManager;
};

export default WebSocketManager;
