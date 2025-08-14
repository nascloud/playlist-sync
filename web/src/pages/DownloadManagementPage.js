import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import DownloadSessionCard from '../components/DownloadSessionCard';
import LogModal from '../components/LogModal'; // 引入 LogModal 组件
import { fetchFromApi } from '../lib/api';
const DownloadManagementPage = () => {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isLogModalOpen, setIsLogModalOpen] = useState(false);
    const [selectedSessionId, setSelectedSessionId] = useState(null);
    const handleOpenLogModal = (sessionId) => {
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
            }
            else {
                toast.error('获取下载状态失败。');
            }
        }
        catch (error) {
            console.error('Failed to fetch download status:', error);
            toast.error('无法连接到服务器以获取下载状态。');
        }
        finally {
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
                }
                else {
                    toast.error(data.message || '清除失败。');
                }
            }
            catch (error) {
                toast.error('请求失败，请检查网络连接。');
            }
        }
    };
    if (loading) {
        return _jsx("div", { className: "text-center p-8", children: "\u6B63\u5728\u52A0\u8F7D\u4E0B\u8F7D\u72B6\u6001..." });
    }
    return (_jsxs("div", { className: "p-4 sm:p-8", children: [_jsxs("div", { className: "flex justify-between items-center mb-6", children: [_jsx("h1", { className: "text-3xl font-bold", children: "\u4E0B\u8F7D\u7BA1\u7406" }), _jsx("button", { onClick: handleClearCompleted, className: "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors", children: "\u6E05\u9664\u5DF2\u5B8C\u6210" })] }), _jsx("div", { className: "space-y-4", children: sessions.map(session => (_jsx(DownloadSessionCard, { session: session, onUpdate: fetchStatus, onViewLogs: handleOpenLogModal }, session.id))) }), _jsx(LogModal, { isOpen: isLogModalOpen, onClose: handleCloseLogModal, sessionId: selectedSessionId })] }));
};
export default DownloadManagementPage;
