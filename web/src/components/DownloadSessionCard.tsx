import React, { useState } from 'react';
import { DownloadSession, DownloadQueueItem } from '../types';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/solid';
import { toast } from 'sonner';
import { fetchFromApi } from '../lib/api';

interface DownloadSessionCardProps {
  session: DownloadSession;
  onUpdate: () => void;
  onViewLogs: (sessionId: number) => void;
}

const apiRequest = async (path: string, method: string, successMessage: string, errorMessage: string) => {
  try {
    const data = await fetchFromApi(path, { method });
    if (data.success) {
      toast.success(successMessage);
      return true;
    } else {
      toast.error(data.message || errorMessage);
      return false;
    }
  } catch (error: any) {
    toast.error(error.message || '请求失败，请检查网络连接。');
    return false;
  }
};

const DownloadSessionCard: React.FC<DownloadSessionCardProps> = ({ session, onUpdate, onViewLogs }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCardClick = () => {
    setIsExpanded(!isExpanded);
  };

  const handlePause = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (await apiRequest(`/api/download/session/${session.id}/pause`, 'POST', '会话已暂停', '暂停失败')) {
      onUpdate();
    }
  };

  const handleResume = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (await apiRequest(`/api/download/session/${session.id}/resume`, 'POST', '会话已恢复', '恢复失败')) {
      onUpdate();
    }
  };

  const handleDelete = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (window.confirm(`确定要删除会话 "${session.task_name || '该会话'}" 吗？此操作不可逆。`)) {
      if (await apiRequest(`/api/download/session/${session.id}`, 'DELETE', '会话已删除', '删除失败')) {
        onUpdate();
      }
    }
  };
  
  const handleViewLogs = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    onViewLogs(session.id);
  };

  const progress = session.total_songs > 0 ? (session.success_count / session.total_songs) * 100 : 0;

  return (
    <div 
      className="bg-white shadow-md rounded-lg p-4 transition-all duration-300"
      onClick={handleCardClick}
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center cursor-pointer">
        <div className="flex-grow">
          <h3 className="text-lg font-bold">{session.task_name || `会话 #${session.id}`}</h3>
          <p className="text-sm text-gray-500">
            {session.created_at ? format(new Date(session.created_at), 'yyyy-MM-dd HH:mm', { locale: zhCN }) : '日期不可用'}
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2.5 my-2">
            <div
              className={`h-2.5 rounded-full ${session.status === 'active' ? 'bg-blue-500' : 'bg-green-500'}`}
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm">
            进度: {session.success_count} / {session.total_songs} | 状态: {session.status}
          </p>
        </div>
        <div className="flex items-center space-x-2 mt-4 sm:mt-0">
          <button onClick={handleViewLogs} className="text-sm bg-gray-500 text-white px-3 py-1 rounded">日志</button>
          {session.status === 'active' && (
            <button onClick={handlePause} className="text-sm bg-yellow-500 text-white px-3 py-1 rounded">暂停</button>
          )}
          {session.status === 'paused' && (
            <button onClick={handleResume} className="text-sm bg-green-500 text-white px-3 py-1 rounded">恢复</button>
          )}
          <button onClick={handleDelete} className="text-sm bg-red-500 text-white px-3 py-1 rounded">删除</button>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-dashed flex justify-center items-center text-sm text-gray-500">
        {isExpanded ? (
          <>
            <ChevronUpIcon className="h-5 w-5 mr-1" />
            <span>点击收起详细信息</span>
          </>
        ) : (
          <>
            <ChevronDownIcon className="h-5 w-5 mr-1" />
            <span>点击展开查看详细信息</span>
          </>
        )}
      </div>
      {isExpanded && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="font-semibold mb-2">歌曲队列:</h4>
          <ul className="space-y-2 text-sm">
            {session.items && session.items.map((item: DownloadQueueItem) => (
              <li key={item.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>{item.title} - {item.artist}</span>
                <span className="font-mono text-xs px-2 py-1 bg-gray-200 rounded">{item.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default DownloadSessionCard;
