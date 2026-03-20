/**
 * 403 禁止访问页面
 * 当用户没有权限访问时显示
 */

import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';

const Forbidden = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  return (
    <Result
      status="403"
      title="403 - 禁止访问"
      subTitle="抱歉，您没有权限访问此页面"
      extra={
        <Button type="primary" onClick={() => navigate(from || '/')}>
          返回上一页
        </Button>
      }
      style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    />
  );
};

export default Forbidden;
