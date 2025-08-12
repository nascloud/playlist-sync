import React from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export const TimeDisplay: React.FC<{ timeString: string | null }> = ({ timeString }) => {
  if (!timeString) {
    return <span className="font-semibold text-gray-500">从未</span>;
  }
  try {
    const date = new Date(timeString);
    const absoluteTime = format(date, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
    const relativeTime = formatDistanceToNow(date, { addSuffix: true, locale: zhCN });
    return <span className="font-semibold text-gray-800" title={absoluteTime}>{relativeTime}</span>;
  } catch (e) {
    return <span className="font-semibold text-red-500">日期无效</span>;
  }
};

export default TimeDisplay;