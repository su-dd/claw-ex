/**
 * 404 错误页面
 * 当访问不存在的路由时显示
 */

import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Result
      status="404"
      title="404 - 页面未找到"
      subTitle="抱歉，您访问的页面不存在"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      }
      style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    />
  );
};

export default NotFound;
