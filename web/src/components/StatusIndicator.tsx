import React, { memo } from 'react';

type StatusIndicatorProps = {
  status: 'success' | 'syncing' | 'error' | 'idle' | 'failed' | 'pending' | 'queued' | 'parsing' | 'matching' | 'importing';
};

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  const statusConfig = {
    success: { color: 'bg-green-500', text: '成功' },
    syncing: { color: 'bg-blue-500', text: '同步中' },
    parsing: { color: 'bg-blue-400', text: '解析中' },
    matching: { color: 'bg-blue-400', text: '匹配中' },
    importing: { color: 'bg-blue-400', text: '导入中' },
    queued: { color: 'bg-purple-500', text: '排队中' },
    failed: { color: 'bg-red-700', text: '失败' },
    error: { color: 'bg-red-500', text: '错误' },
    pending: { color: 'bg-yellow-500', text: '待处理' },
    idle: { color: 'bg-gray-500', text: '待机' },
  };

  const { color, text } = statusConfig[status] || statusConfig.idle; // Fallback to idle

  return (
    <div className="flex items-center">
      <span className={`w-3 h-3 rounded-full mr-2 ${color}`}></span>
      <span>{text}</span>
    </div>
  );
};

export default memo(StatusIndicator);