import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ChevronDownIcon, ChevronUpIcon, ArrowPathIcon } from '@heroicons/react/24/solid';
import { toast } from 'sonner';
import { fetchFromApi } from '../lib/api';
const apiRequest = async (path, method, successMessage, errorMessage) => {
    try {
        const data = await fetchFromApi(path, { method });
        if (data.success) {
            toast.success(successMessage);
            return true;
        }
        else {
            toast.error(data.message || errorMessage);
            return false;
        }
    }
    catch (error) {
        toast.error(error.message || '请求失败，请检查网络连接。');
        return false;
    }
};
const DownloadSessionCard = ({ session, onUpdate, onViewLogs }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const handleRetryItem = async (itemId) => {
        try {
            const data = await fetchFromApi(`/download/session/item/${itemId}/retry`, { method: 'POST' });
            if (data.success) {
                toast.success(data.message);
                onUpdate();
            }
            else {
                toast.error(data.message || '重试失败');
            }
        }
        catch (error) {
            toast.error(error.message || '请求失败，请检查网络连接。');
        }
    };
    const handleCardClick = () => {
        setIsExpanded(!isExpanded);
    };
    const handlePause = async (e) => {
        e.stopPropagation();
        if (await apiRequest(`/download/session/${session.id}/pause`, 'POST', '会话已暂停', '暂停失败')) {
            onUpdate();
        }
    };
    const handleResume = async (e) => {
        e.stopPropagation();
        if (await apiRequest(`/download/session/${session.id}/resume`, 'POST', '会话已恢复', '恢复失败')) {
            onUpdate();
        }
    };
    const handleDelete = async (e) => {
        e.stopPropagation();
        if (window.confirm(`确定要删除会话 "${session.task_name || '该会话'}" 吗？此操作不可逆。`)) {
            if (await apiRequest(`/download/session/${session.id}`, 'DELETE', '会话已删除', '删除失败')) {
                onUpdate();
            }
        }
    };
    const handleViewLogs = (e) => {
        e.stopPropagation();
        onViewLogs(session.id);
    };
    const handleRetryFailed = async (e) => {
        e.stopPropagation();
        try {
            const data = await fetchFromApi(`/download/session/${session.id}/retry-failed`, { method: 'POST' });
            if (data.success) {
                toast.success(data.message);
                onUpdate();
            }
            else {
                toast.error(data.message || '重试失败');
            }
        }
        catch (error) {
            toast.error(error.message || '请求失败，请检查网络连接。');
        }
    };
    const progress = session.total_songs > 0 ? (session.success_count / session.total_songs) * 100 : 0;
    return (_jsxs("div", { className: "bg-white shadow-md rounded-lg p-4 transition-all duration-300", onClick: handleCardClick, children: [_jsxs("div", { className: "flex flex-col sm:flex-row justify-between items-start sm:items-center cursor-pointer", children: [_jsxs("div", { className: "flex-grow", children: [_jsx("h3", { className: "text-lg font-bold", children: session.task_name || `会话 #${session.id}` }), _jsx("p", { className: "text-sm text-gray-500", children: session.created_at ? format(new Date(session.created_at), 'yyyy-MM-dd HH:mm', { locale: zhCN }) : '日期不可用' }), _jsx("div", { className: "w-full bg-gray-200 rounded-full h-2.5 my-2", children: _jsx("div", { className: `h-2.5 rounded-full ${session.status === 'active' ? 'bg-blue-500' : 'bg-green-500'}`, style: { width: `${progress}%` } }) }), _jsxs("p", { className: "text-sm", children: ["\u8FDB\u5EA6: ", session.success_count, " \u6210\u529F, ", session.failed_count, " \u5931\u8D25, ", session.total_songs, " \u603B\u8BA1 | \u72B6\u6001: ", session.status] })] }), _jsxs("div", { className: "flex items-center space-x-2 mt-4 sm:mt-0", children: [_jsx("button", { onClick: handleViewLogs, className: "text-sm bg-gray-500 text-white px-3 py-1 rounded", children: "\u65E5\u5FD7" }), session.status === 'active' && (_jsx("button", { onClick: handlePause, className: "text-sm bg-yellow-500 text-white px-3 py-1 rounded", children: "\u6682\u505C" })), session.status === 'paused' && (_jsx("button", { onClick: handleResume, className: "text-sm bg-green-500 text-white px-3 py-1 rounded", children: "\u6062\u590D" })), session.failed_count > 0 && (_jsxs("button", { onClick: handleRetryFailed, className: "text-sm bg-blue-500 text-white px-3 py-1 rounded flex items-center", children: [_jsx(ArrowPathIcon, { className: "h-4 w-4 mr-1" }), "\u91CD\u8BD5\u5931\u8D25(", session.failed_count, ")"] })), _jsx("button", { onClick: handleDelete, className: "text-sm bg-red-500 text-white px-3 py-1 rounded", children: "\u5220\u9664" })] })] }), _jsx("div", { className: "mt-2 pt-2 border-t border-dashed flex justify-center items-center text-sm text-gray-500", children: isExpanded ? (_jsxs(_Fragment, { children: [_jsx(ChevronUpIcon, { className: "h-5 w-5 mr-1" }), _jsx("span", { children: "\u70B9\u51FB\u6536\u8D77\u8BE6\u7EC6\u4FE1\u606F" })] })) : (_jsxs(_Fragment, { children: [_jsx(ChevronDownIcon, { className: "h-5 w-5 mr-1" }), _jsx("span", { children: "\u70B9\u51FB\u5C55\u5F00\u67E5\u770B\u8BE6\u7EC6\u4FE1\u606F" })] })) }), isExpanded && (_jsxs("div", { className: "mt-4 pt-4 border-t", children: [_jsx("h4", { className: "font-semibold mb-2", children: "\u6B4C\u66F2\u961F\u5217:" }), _jsx("ul", { className: "space-y-2 text-sm", children: session.items && session.items.map((item) => (_jsxs("li", { className: "flex justify-between items-center p-2 bg-gray-50 rounded", children: [_jsxs("span", { className: "flex-1", children: [item.title, " - ", item.artist] }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("span", { className: `font-mono text-xs px-2 py-1 rounded ${item.status === 'success' ? 'bg-green-200 text-green-800' :
                                                item.status === 'failed' ? 'bg-red-200 text-red-800' :
                                                    item.status === 'pending' ? 'bg-yellow-200 text-yellow-800' :
                                                        item.status === 'downloading' ? 'bg-blue-200 text-blue-800' :
                                                            'bg-gray-200 text-gray-800'}`, children: item.status }), item.status === 'failed' && (_jsxs("button", { onClick: (e) => {
                                                e.stopPropagation();
                                                handleRetryItem(item.id);
                                            }, className: "text-xs bg-blue-500 text-white px-2 py-1 rounded flex items-center hover:bg-blue-600", children: [_jsx(ArrowPathIcon, { className: "h-3 w-3 mr-1" }), "\u91CD\u8BD5"] }))] })] }, item.id))) })] }))] }));
};
export default DownloadSessionCard;
