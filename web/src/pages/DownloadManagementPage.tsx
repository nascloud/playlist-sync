
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { DownloadSession } from '../types';
import DownloadSessionCard from '../components/DownloadSessionCard';
import LogModal from '../components/LogModal'; // 引入 LogModal 组件
import { fetchFromApi } from '../lib/api';


const DownloadManagementPage: React.FC = () => {
  const [sessions, setSessions] = useState<DownloadSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  const handleOpenLogModal = (sessionId: number) => {
    setSelectedSessionId(sessionId);
    setIsLogModalOpen(true);
  };

  const handleCloseLogModal = () => {
    setIsLogModalOpen(false);
    setSelectedSessionId(null);
  };


  const fetchStatus = useCallback(async () => {
    try {
      const data = await fetchFromApi('/download/status');
      if (data.success) {
        setSessions(data.sessions);
      } else {
        toast.error('获取下载状态失败。');
      }
    } catch (error) {
      console.error('Failed to fetch download status:', error);
      toast.error('无法连接到服务器以获取下载状态。');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus(); // Initial fetch
    const intervalId = setInterval(fetchStatus, 5000); // 轮询间隔可以适当加长

    return () => clearInterval(intervalId); // Cleanup on component unmount
  }, [fetchStatus]);
  
  const handleClearCompleted = async () => {
    if (window.confirm('确定要清除所有已完成的下载会话吗？这将从列表中移除所有已完成的任务卡片，但不会删除已下载的文件。')) {
      try {
        const data = await fetchFromApi('/download/clear-completed', { method: 'POST' });
        if (data.success) {
          toast.success('已成功清除所有已完成的下载会话。');
          fetchStatus(); // 刷新列表
        } else {
          toast.error(data.message || '清除失败。');
        }
      } catch (error) {
        toast.error('请求失败，请检查网络连接。');
      }
    }
  };
  
  if (loading) {
    return <div className="text-center p-8">正在加载下载状态...</div>;
  }

  return (
    <div className="p-4 sm:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">下载管理</h1>
        <button
          onClick={handleClearCompleted}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors"
        >
          清除已完成
        </button>
      </div>
      
      <div className="space-y-4">
        {sessions.map(session => (
          <DownloadSessionCard
            key={session.id}
            session={session}
            onUpdate={fetchStatus}
            onViewLogs={handleOpenLogModal}
          />
        ))}
      </div>
      
      <LogModal 
        isOpen={isLogModalOpen}
        onClose={handleCloseLogModal}
        sessionId={selectedSessionId}
      />
    </div>
  );
};

export default DownloadManagementPage;
