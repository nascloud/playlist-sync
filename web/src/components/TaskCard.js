import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import Button from './Button';
import StatusIndicator from './StatusIndicator';
import TimeDisplay from './TimeDisplay';
import ProgressBar from './ProgressBar';
import IconButton from './IconButton';
import { Eye, EyeOff, RefreshCw, Settings2, Trash2, Music, Users, Calendar, Clock, Share2, AlertTriangle, DownloadCloud } from 'lucide-react';
import { parseExpression } from 'cron-parser';
import cronstrue from 'cronstrue/i18n';
const cronToLabel = (cron) => {
    if (!cron || cron.toLowerCase() === 'off' || cron === '关闭') {
        return '已关闭';
    }
    try {
        // 尝试处理6位带秒的cron表达式
        const parts = cron.split(' ');
        const cronForCronstrue = parts.length === 6 ? parts.slice(1).join(' ') : cron;
        return cronstrue.toString(cronForCronstrue, { locale: "zh_CN" });
    }
    catch (e) {
        return cron; // 如果解析失败，返回原始表达式
    }
};
const NextSyncTimeDisplay = ({ cronExpression }) => {
    try {
        if (!cronExpression || cronExpression.toLowerCase() === 'off' || cronExpression === '关闭') {
            return _jsx("span", { className: "font-semibold text-gray-500", children: "\u5DF2\u5173\u95ED" });
        }
        // 统一处理6位表达式，确保两个库使用相同的输入
        const parts = cronExpression.split(' ');
        const cronToParse = parts.length === 6 ? parts.slice(1).join(' ') : cronExpression;
        // 再次验证表达式，以防万一
        cronstrue.toString(cronToParse, { locale: "zh_CN" });
        const interval = parseExpression(cronToParse, { utc: true });
        const nextDate = interval.next().toDate();
        return _jsx(TimeDisplay, { timeString: nextDate.toISOString() });
    }
    catch (err) {
        console.error(`[Final Attempt] Cron parsing failed for expression: "${cronExpression}"`, err);
        return _jsxs("span", { className: "font-semibold text-red-500 flex items-center gap-1", children: [_jsx(AlertTriangle, { className: "w-4 h-4" }), " \u8868\u8FBE\u5F0F\u65E0\u6548"] });
    }
};
const PlatformLogo = ({ platform }) => {
    // Simple text-based logo for now
    const platformMap = {
        netease: { label: 'N', color: 'bg-red-500' },
        qq: { label: 'Q', color: 'bg-green-500' },
    };
    const { label, color } = platformMap[platform] || { label: '?', color: 'bg-gray-400' };
    return (_jsx("div", { className: `w-6 h-6 ${color} rounded-full flex items-center justify-center text-white text-sm font-bold`, children: label }));
};
const TaskCard = ({ task, servers, isSyncing, isExpanded, unmatchedSongs, syncProgress, onSync, onDelete, onEdit, onToggleExpand, onDownloadAll, onDownloadSingle, }) => {
    const hasCounts = task.total_songs != null && task.matched_songs != null;
    const unmatchedCount = hasCounts ? task.total_songs - task.matched_songs : null;
    const isSyncingLive = syncProgress && syncProgress.status !== 'success' && syncProgress.status !== 'failed' && syncProgress.status !== 'error';
    const server = servers.find(s => s.id === task.server_id);
    return (_jsxs("div", { className: "bg-white rounded-xl shadow-md overflow-hidden transition-all duration-300 hover:shadow-lg", children: [_jsxs("div", { className: "p-6", children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsxs("div", { className: "flex flex-1 min-w-0 items-center gap-3", children: [_jsx(PlatformLogo, { platform: task.platform }), _jsx("h2", { className: "text-xl font-bold text-gray-800 truncate", title: task.name, children: task.name })] }), _jsx(StatusIndicator, { status: isSyncingLive ? syncProgress.status : task.status })] }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-6", children: [_jsxs("div", { className: "md:col-span-2 space-y-3", children: [isSyncingLive ? (_jsxs(_Fragment, { children: [_jsxs("div", { className: "flex items-baseline gap-3 text-sm text-gray-600", children: [_jsx(Users, { className: "w-5 h-5 text-gray-400" }), _jsx("span", { children: "\u540C\u6B65\u8FDB\u5EA6:" }), _jsx("span", { className: "font-semibold text-blue-600", children: syncProgress.message })] }), syncProgress.total != null && syncProgress.progress != null ? (_jsx(ProgressBar, { value: syncProgress.progress, max: syncProgress.total })) : _jsx(ProgressBar, { value: 100, max: 100, className: "opacity-50 animate-pulse" })] })) : (_jsxs(_Fragment, { children: [_jsxs("div", { className: "flex items-baseline gap-3 text-sm text-gray-600", children: [_jsx(Users, { className: "w-5 h-5 text-gray-400" }), _jsx("span", { children: "\u540C\u6B65\u7ED3\u679C:" }), hasCounts ? (_jsxs("span", { className: "font-semibold text-gray-800", children: [task.matched_songs, " / ", task.total_songs, " \u9996"] })) : (_jsx("span", { className: "text-gray-500", children: "\u6682\u65E0\u6570\u636E" }))] }), hasCounts && _jsx(ProgressBar, { value: task.matched_songs, max: task.total_songs })] })), _jsxs("div", { className: "flex items-baseline gap-3 text-sm text-gray-600", children: [_jsx(Calendar, { className: "w-5 h-5 text-gray-400" }), _jsx("span", { children: "\u540C\u6B65\u8BA1\u5212:" }), _jsx("span", { className: "font-semibold text-gray-800", children: cronToLabel(task.cron_schedule) })] }), _jsxs("div", { className: "flex items-baseline gap-3 text-sm text-gray-600", children: [_jsx(Clock, { className: "w-5 h-5 text-gray-400" }), _jsx("span", { children: "\u4E0B\u6B21\u540C\u6B65:" }), _jsx(NextSyncTimeDisplay, { cronExpression: task.cron_schedule })] }), _jsxs("div", { className: "flex items-baseline gap-3 text-sm text-gray-600", children: [_jsx(Share2, { className: "w-5 h-5 text-gray-400" }), _jsx("span", { children: "\u540C\u6B65\u5230:" }), _jsx("span", { className: "font-semibold text-gray-800", children: server ? server.name : '未知服务器' })] }), _jsxs("div", { className: "flex items-baseline gap-3 text-sm text-gray-600", children: [_jsx(Clock, { className: "w-5 h-5 text-gray-400" }), _jsx("span", { children: "\u4E0A\u6B21\u540C\u6B65:" }), _jsx(TimeDisplay, { timeString: task.last_sync_time })] })] }), _jsxs("div", { className: "flex items-center md:justify-end gap-2", children: [_jsx(IconButton, { size: "lg", tooltip: "\u7ACB\u5373\u540C\u6B65", onClick: () => onSync(task.id), disabled: isSyncing, children: _jsx(RefreshCw, { className: `h-5 w-5 ${isSyncing ? 'animate-spin' : ''}` }) }), _jsx(IconButton, { size: "lg", tooltip: "\u7F16\u8F91\u8BA1\u5212", onClick: () => onEdit(task), children: _jsx(Settings2, { className: "h-5 w-5" }) }), _jsx(IconButton, { size: "lg", variant: "danger", tooltip: "\u5220\u9664\u4EFB\u52A1", onClick: () => onDelete(task.id), children: _jsx(Trash2, { className: "h-5 w-5" }) })] })] }), _jsx("div", { className: "mt-4 pt-4 border-t border-gray-100", children: _jsxs("button", { onClick: () => onToggleExpand(task.id), className: "flex items-center justify-center w-full text-sm font-medium text-blue-600 hover:text-blue-800", children: [isExpanded ? _jsx(EyeOff, { className: "w-4 h-4 mr-2" }) : _jsx(Eye, { className: "w-4 h-4 mr-2" }), isExpanded ? '隐藏' : '查看', "\u672A\u5339\u914D\u66F2\u76EE", unmatchedCount !== null && unmatchedCount > 0 && (_jsx("span", { className: "ml-2 bg-red-100 text-red-800 text-xs font-semibold px-2 py-0.5 rounded-full", children: unmatchedCount }))] }) })] }), isExpanded && (_jsxs("div", { className: "px-6 pb-6 bg-gray-50/50", children: [_jsx("h3", { className: "text-md font-semibold text-gray-700 mb-3", children: "\u672A\u5339\u914D\u7684\u6B4C\u66F2:" }), unmatchedCount !== null && unmatchedCount > 0 ? (unmatchedSongs && unmatchedSongs.length > 0 ? (_jsx("div", { className: "grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-2", children: unmatchedSongs.map((song, index) => (_jsxs("div", { className: "flex items-center p-3 bg-white rounded-lg shadow-sm border", children: [_jsx(Music, { className: "w-5 h-5 text-gray-400 mr-3 flex-shrink-0" }), _jsxs("div", { className: "flex-1 min-w-0", children: [_jsx("div", { className: "text-sm font-medium text-gray-900 truncate", children: song.title }), _jsx("div", { className: "text-sm text-gray-500 truncate", children: song.artist })] }), _jsx(IconButton, { size: "sm", tooltip: "\u4E0B\u8F7D\u8FD9\u9996\u6B4C", onClick: () => onDownloadSingle(task, song), children: _jsx(DownloadCloud, { className: "h-4 w-4" }) })] }, index))) })) : (_jsx("p", { className: "text-sm text-gray-500", children: "\u6B63\u5728\u52A0\u8F7D\u672A\u5339\u914D\u6B4C\u66F2\u5217\u8868..." }))) : (_jsx("p", { className: "text-sm text-gray-500", children: "\u592A\u68D2\u4E86\uFF01\u6240\u6709\u6B4C\u66F2\u90FD\u5DF2\u6210\u529F\u5339\u914D\u3002" })), _jsxs("div", { className: "mt-4 flex gap-2", children: [_jsx(Button, { variant: "secondary", size: "sm", onClick: () => onDownloadAll(task), disabled: unmatchedCount === null || unmatchedCount === 0, children: "\u4E00\u952E\u4E0B\u8F7D\u5168\u90E8" }), _jsx(Button, { variant: "secondary", size: "sm", onClick: async () => {
                                    try {
                                        const response = await fetch(`/api/tasks/${task.id}/unmatched/export`, {
                                            headers: {
                                                'Authorization': `Bearer ${localStorage.getItem('token')}`
                                            }
                                        });
                                        if (!response.ok) {
                                            throw new Error('导出失败');
                                        }
                                        // 创建下载链接
                                        const blob = await response.blob();
                                        const url = window.URL.createObjectURL(blob);
                                        const a = document.createElement('a');
                                        a.href = url;
                                        a.download = `unmatched_songs_task_${task.id}.json`;
                                        document.body.appendChild(a);
                                        a.click();
                                        document.body.removeChild(a);
                                        window.URL.revokeObjectURL(url);
                                    }
                                    catch (error) {
                                        console.error('导出失败:', error);
                                        alert('导出失败，请重试');
                                    }
                                }, disabled: unmatchedCount === null || unmatchedCount === 0, children: "\u5BFC\u51FA\u5217\u8868" })] })] }))] }));
};
export default TaskCard;
