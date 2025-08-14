import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { fetchFromApi } from '../lib/api';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input from '../components/Input';
import CronGenerator from '../components/CronGenerator';
import TaskCard from '../components/TaskCard';
import { PlusCircle } from 'lucide-react';
const DashboardPage = () => {
    const [tasks, setTasks] = useState([]);
    const [servers, setServers] = useState([]);
    const [loading, setLoading] = useState(true);
    // Modals state
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    // Form and async state
    const [playlistUrl, setPlaylistUrl] = useState('');
    const [platform, setPlatform] = useState('netease');
    const [selectedServerId, setSelectedServerId] = useState(null);
    const [addModalError, setAddModalError] = useState('');
    const [newPlaylistName, setNewPlaylistName] = useState('');
    const [isAdding, setIsAdding] = useState(false);
    const [editingTask, setEditingTask] = useState(null);
    const [newSyncSchedule, setNewSyncSchedule] = useState('');
    const [taskAutoDownload, setTaskAutoDownload] = useState(false);
    const [syncingTaskId, setSyncingTaskId] = useState(null);
    // Preview state
    const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
    const [previewData, setPreviewData] = useState(null);
    // Expandable row state
    const [expandedTaskId, setExpandedTaskId] = useState(null);
    const [unmatchedSongs, setUnmatchedSongs] = useState({});
    const [syncProgress, setSyncProgress] = useState({});
    const fetchInitialData = useCallback(async () => {
        setLoading(true);
        try {
            const [tasksData, settingsData] = await Promise.all([
                fetchFromApi('/tasks'),
                fetchFromApi('/settings')
            ]);
            if (tasksData.success) {
                setTasks(tasksData.tasks);
            }
            if (settingsData.success && settingsData.servers.length > 0) {
                setServers(settingsData.servers);
            }
        }
        catch (error) {
            console.error('Failed to fetch initial data:', error);
        }
        finally {
            setLoading(false);
        }
    }, []);
    const fetchTasksOnly = useCallback(async () => {
        try {
            const data = await fetchFromApi('/tasks');
            if (data.success) {
                setTasks(data.tasks);
            }
        }
        catch (error) {
            console.error('Failed to fetch tasks:', error);
        }
    }, []);
    useEffect(() => {
        fetchInitialData();
    }, [fetchInitialData]);
    useEffect(() => {
        if (servers.length > 0 && selectedServerId === null) {
            setSelectedServerId(servers[0].id);
        }
    }, [servers]);
    useEffect(() => {
        const interval = setInterval(fetchTasksOnly, 5000);
        return () => clearInterval(interval);
    }, [fetchTasksOnly]);
    const handleOpenAddModal = () => {
        setPlaylistUrl('');
        setPlatform('netease');
        setAddModalError('');
        setIsAddModalOpen(true);
    };
    const handleCloseAddModal = useCallback(() => {
        setIsAddModalOpen(false);
    }, []);
    const handleCloseEditModal = useCallback(() => {
        setIsEditModalOpen(false);
    }, []);
    const handleAddPlaylist = async () => {
        if (!playlistUrl) {
            setAddModalError('请输入歌单 URL。');
            return;
        }
        if (!selectedServerId) {
            setAddModalError('请选择一个服务器。');
            return;
        }
        setAddModalError('');
        setIsAdding(true);
        try {
            // 第一步：预览歌单信息
            const previewData = await fetchFromApi('/preview-playlist', {
                method: 'POST',
                body: JSON.stringify({
                    playlist_url: playlistUrl,
                    platform: platform
                }),
            });
            // 预览成功，显示歌单信息并确认添加
            setPreviewData(previewData);
            setIsPreviewModalOpen(true);
            setIsAdding(false);
        }
        catch (err) {
            setAddModalError(err.message || '无法连接到后端服务。');
            setIsAdding(false);
        }
    };
    const handleConfirmAddPlaylist = async () => {
        if (!previewData || !selectedServerId)
            return;
        setIsAdding(true);
        setIsPreviewModalOpen(false);
        try {
            // 创建同步任务（传递预览数据以避免重复解析）
            const createData = await fetchFromApi('/tasks', {
                method: 'POST',
                body: JSON.stringify({
                    name: newPlaylistName || previewData.title, // 使用用户输入的名称或歌单标题
                    playlist_url: playlistUrl,
                    platform: platform,
                    server_id: selectedServerId,
                    cron_schedule: '0 2 * * *', // Default to daily
                    preview_data: previewData // 传递预览数据以避免重复解析
                }),
            });
            if (createData.id) {
                // 成功创建任务
                setIsAddModalOpen(false);
                setNewPlaylistName('');
                setPlaylistUrl('');
                setPreviewData(null);
                fetchInitialData();
                // 显示成功提示
                toast.success(`成功添加歌单 "${createData.name}" 到同步列表！`);
            }
            else {
                // 处理创建任务时的错误
                let errorMsg = '添加任务失败，请重试。';
                if (createData.detail) {
                    if (typeof createData.detail === 'string') {
                        errorMsg = createData.detail;
                    }
                    else if (Array.isArray(createData.detail)) {
                        errorMsg = createData.detail.map((e) => `${e.loc.join('.')} - ${e.msg}`).join('; ');
                    }
                }
                setAddModalError(errorMsg);
            }
        }
        catch (err) {
            setAddModalError(err.message || '无法连接到后端服务。');
        }
        finally {
            setIsAdding(false);
        }
    };
    const handleDeleteTask = async (taskId) => {
        if (window.confirm('您确定要删除这个任务吗？')) {
            try {
                const data = await fetchFromApi(`/tasks/${taskId}`, { method: 'DELETE' });
                if (data.success) {
                    // Manually filter out the deleted task from the state
                    setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
                }
                else {
                    console.error('Failed to delete task');
                }
            }
            catch (error) {
                console.error('Error deleting task:', error);
            }
        }
    };
    const handleOpenEditModal = (task) => {
        setEditingTask(task);
        setNewSyncSchedule(task.cron_schedule);
        setTaskAutoDownload(task.auto_download || false);
        setIsEditModalOpen(true);
    };
    const handleUpdateTask = async () => {
        if (!editingTask)
            return;
        await fetchFromApi(`/tasks/${editingTask.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                cron_schedule: newSyncSchedule,
                auto_download: taskAutoDownload
            }),
        });
        setIsEditModalOpen(false);
        fetchTasksOnly();
    };
    const handleSyncTask = (taskId) => {
        setSyncingTaskId(taskId);
        setSyncProgress(prev => ({ ...prev, [taskId]: { status: 'starting', message: '正在连接...' } }));
        const eventSource = new EventSource(`/api/tasks/${taskId}/sync/stream?token=${localStorage.getItem('token')}`);
        eventSource.addEventListener('progress', (event) => {
            try {
                const progressData = JSON.parse(event.data);
                setSyncProgress(prev => ({ ...prev, [taskId]: progressData }));
            }
            catch (e) {
                console.error("Failed to parse progress event", e);
            }
        });
        eventSource.addEventListener('error', (event) => {
            console.error('EventSource failed:', event);
            setSyncProgress(prev => ({
                ...prev,
                [taskId]: { status: 'failed', message: '连接错误，同步中断' }
            }));
            eventSource.close();
            // 在短暂延迟后清除状态，并刷新列表
            setTimeout(() => {
                setSyncingTaskId(null);
                setSyncProgress(prev => {
                    const newProgress = { ...prev };
                    delete newProgress[taskId];
                    return newProgress;
                });
                fetchInitialData();
            }, 5000);
        });
        eventSource.addEventListener('close', () => {
            eventSource.close();
            setSyncingTaskId(null);
            // 在短暂延迟后清除状态，并刷新列表
            setTimeout(() => {
                setSyncProgress(prev => {
                    const newProgress = { ...prev };
                    delete newProgress[taskId];
                    return newProgress;
                });
                fetchInitialData();
            }, 2000);
        });
    };
    const fetchUnmatchedSongs = async (taskId) => {
        try {
            const data = await fetchFromApi(`/tasks/${taskId}/unmatched`);
            if (data.success) {
                setUnmatchedSongs(prev => ({
                    ...prev,
                    [taskId]: data.unmatched_songs
                }));
            }
        }
        catch (error) {
            console.error(`Failed to fetch unmatched songs for task ${taskId}:`, error);
        }
    };
    const toggleExpandRow = (taskId) => {
        const isOpening = expandedTaskId !== taskId;
        setExpandedTaskId(isOpening ? taskId : null);
        // 如果是展开操作，则总是获取最新的未匹配列表
        if (isOpening) {
            fetchUnmatchedSongs(taskId);
        }
    };
    const handleDownloadAll = async (task) => {
        try {
            const result = await fetchFromApi('/download/all-missing', {
                method: 'POST',
                body: JSON.stringify({ task_id: task.id }),
            });
            if (result.success) {
                toast.success(`已为任务 "${task.name}" 创建批量下载会话。`);
            }
            else {
                toast.error(`批量下载失败: ${result.message || '未知错误'}`);
            }
        }
        catch (error) {
            toast.error('请求批量下载失败，请检查网络连接。');
        }
    };
    const handleDownloadSingle = async (task, song) => {
        try {
            toast.info(`正在将《${song.title}》加入下载队列...`);
            const result = await fetchFromApi('/download/single', {
                method: 'POST',
                body: JSON.stringify({
                    task_id: task.id,
                    song_id: song.song_id,
                    title: song.title,
                    artist: song.artist,
                    album: song.album,
                }),
            });
            if (result.success) {
                toast.success(`《${song.title}》已成功加入下载队列。`);
            }
            else {
                toast.error(`下载《${song.title}》失败: ${result.message || '未知错误'}`);
            }
        }
        catch (error) {
            toast.error('请求下载失败，请检查网络连接。');
        }
    };
    if (loading) {
        // You can implement a skeleton loader here for better UX
        return _jsx("div", { className: "text-center p-8 text-gray-500", children: "\u6B63\u5728\u52A0\u8F7D\u4EFB\u52A1..." });
    }
    return (_jsxs("div", { className: "p-4 sm:p-8", children: [_jsxs("header", { className: "flex justify-between items-center mb-8", children: [_jsx("h1", { className: "text-3xl font-bold tracking-tight text-gray-900", children: "\u540C\u6B65\u4EFB\u52A1" }), _jsxs(Button, { onClick: handleOpenAddModal, className: "flex items-center gap-2 flex-shrink-0 whitespace-nowrap", children: [_jsx(PlusCircle, { className: "h-5 w-5" }), _jsx("span", { className: "whitespace-nowrap", children: "\u6DFB\u52A0\u6B4C\u5355" })] })] }), tasks.length > 0 ? (_jsx("div", { className: "grid grid-cols-1 xl:grid-cols-2 gap-6", children: tasks.map((task) => (_jsx(TaskCard, { task: task, servers: servers, isSyncing: syncingTaskId === task.id || !!syncProgress[task.id] || ['syncing', 'matching', 'importing', 'queued'].includes(task.status), isExpanded: expandedTaskId === task.id, unmatchedSongs: unmatchedSongs[task.id] || [], syncProgress: syncProgress[task.id], onSync: handleSyncTask, onDelete: handleDeleteTask, onEdit: handleOpenEditModal, onToggleExpand: toggleExpandRow, onDownloadAll: handleDownloadAll, onDownloadSingle: handleDownloadSingle }, task.id))) })) : (_jsxs("div", { className: "text-center py-20 border-2 border-dashed border-gray-300 rounded-lg bg-white", children: [_jsx("h3", { className: "text-lg font-medium text-gray-900", children: "\u6CA1\u6709\u540C\u6B65\u4EFB\u52A1" }), _jsx("p", { className: "mt-1 text-sm text-gray-500", children: "\u70B9\u51FB\u53F3\u4E0A\u89D2\u7684\u201C\u6DFB\u52A0\u6B4C\u5355\u201D\u6765\u5F00\u59CB\u4F60\u7684\u7B2C\u4E00\u4E2A\u540C\u6B65\u4EFB\u52A1\u5427\uFF01" })] })), _jsxs(Modal, { isOpen: isAddModalOpen, onClose: handleCloseAddModal, title: "\u6DFB\u52A0\u65B0\u6B4C\u5355", children: [_jsxs("div", { className: "space-y-4", children: [_jsx(Input, { id: "playlist-name", label: "\u6B4C\u5355\u540D\u79F0 (\u53EF\u9009)", value: newPlaylistName, onChange: (e) => setNewPlaylistName(e.target.value), placeholder: "\u672A\u586B\u5199\u5219\u4F7F\u7528\u6E90\u6B4C\u5355\u6807\u9898" }), _jsx(Input, { id: "playlist-url", label: "\u6B4C\u5355 URL", value: playlistUrl, onChange: (e) => setPlaylistUrl(e.target.value), placeholder: "\u8BF7\u8F93\u5165\u6B4C\u5355\u7684\u5206\u4EAB\u94FE\u63A5", required: true }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-700", children: "\u5E73\u53F0" }), _jsxs("select", { value: platform, onChange: (e) => setPlatform(e.target.value), className: "mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md", children: [_jsx("option", { value: "netease", children: "\u7F51\u6613\u4E91\u97F3\u4E50" }), _jsx("option", { value: "qq", children: "QQ\u97F3\u4E50" })] })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "server-select", className: "block text-sm font-medium text-gray-700 mt-4", children: "\u540C\u6B65\u5230\u670D\u52A1\u5668" }), _jsx("select", { id: "server-select", value: selectedServerId ?? '', onChange: (e) => setSelectedServerId(Number(e.target.value)), disabled: servers.length === 0, className: "mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md", children: servers.length > 0 ? (servers.map(server => (_jsxs("option", { value: server.id, children: [server.name, " (", server.server_type, ")"] }, server.id)))) : (_jsx("option", { disabled: true, children: loading ? '正在加载服务器...' : '未找到服务器，请先在设置中添加' })) })] })] }), addModalError && _jsx("p", { className: "text-red-500 text-sm mt-2", children: addModalError }), _jsxs("div", { className: "flex justify-end gap-4 mt-6", children: [_jsx(Button, { variant: "secondary", onClick: handleCloseAddModal, children: "\u53D6\u6D88" }), _jsx(Button, { onClick: handleAddPlaylist, loading: isAdding, children: "\u6DFB\u52A0" })] })] }), _jsxs(Modal, { isOpen: isPreviewModalOpen, onClose: () => setIsPreviewModalOpen(false), title: "\u786E\u8BA4\u6B4C\u5355\u4FE1\u606F", children: [previewData && (_jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "bg-gray-50 p-4 rounded-lg", children: [_jsx("h3", { className: "block text-sm font-medium text-gray-700", children: "\u6B4C\u5355\u6807\u9898" }), _jsx("p", { className: "mt-1 text-lg font-medium text-gray-900", children: previewData.title })] }), _jsxs("div", { className: "bg-gray-50 p-4 rounded-lg", children: [_jsx("h3", { className: "block text-sm font-medium text-gray-700", children: "\u6B4C\u66F2\u6570\u91CF" }), _jsxs("p", { className: "mt-1 text-lg font-medium text-gray-900", children: [previewData.track_count, " \u9996"] })] }), _jsx("p", { className: "text-sm text-gray-500", children: "\u8BF7\u786E\u8BA4\u4EE5\u4E0A\u6B4C\u5355\u4FE1\u606F\u662F\u5426\u6B63\u786E\uFF0C\u786E\u8BA4\u540E\u5C06\u6DFB\u52A0\u5230\u540C\u6B65\u5217\u8868\u3002" })] })), _jsxs("div", { className: "flex justify-end gap-4 mt-6", children: [_jsx(Button, { variant: "secondary", onClick: () => setIsPreviewModalOpen(false), children: "\u53D6\u6D88" }), _jsx(Button, { onClick: handleConfirmAddPlaylist, loading: isAdding, children: "\u786E\u8BA4\u6DFB\u52A0" })] })] }), _jsxs(Modal, { isOpen: isEditModalOpen, onClose: handleCloseEditModal, title: "\u7F16\u8F91\u4EFB\u52A1", children: [_jsxs("div", { children: [_jsx("label", { htmlFor: "sync-schedule", className: "block text-sm font-medium text-gray-700", children: "\u540C\u6B65\u8BA1\u5212" }), _jsx(CronGenerator, { value: newSyncSchedule, onChange: setNewSyncSchedule })] }), _jsxs("div", { className: "mt-4 flex items-center", children: [_jsx("input", { id: "auto-download-checkbox", type: "checkbox", checked: taskAutoDownload, onChange: (e) => setTaskAutoDownload(e.target.checked), className: "h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" }), _jsx("label", { htmlFor: "auto-download-checkbox", className: "ml-2 block text-sm text-gray-900", children: "\u540C\u6B65\u540E\u81EA\u52A8\u4E0B\u8F7D\u7F3A\u5931\u6B4C\u66F2" })] }), _jsxs("div", { className: "flex justify-end gap-4 mt-6", children: [_jsx(Button, { variant: "secondary", onClick: () => setIsEditModalOpen(false), children: "\u53D6\u6D88" }), _jsx(Button, { onClick: handleUpdateTask, children: "\u4FDD\u5B58" })] })] })] }));
};
export default DashboardPage;
