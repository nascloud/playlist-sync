import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useCallback } from 'react';
import { fetchFromApi } from '../lib/api';
import Button from '../components/Button';
import ServerModal from '../components/ServerModal';
import DownloadSettings from '../components/DownloadSettings';
import { toast } from 'sonner';
const SettingsPage = ({ onSetupComplete }) => {
    const [servers, setServers] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingServer, setEditingServer] = useState(null);
    const [activeTab, setActiveTab] = useState('servers');
    const [downloadSettings, setDownloadSettings] = useState(null);
    const fetchServers = useCallback(async () => {
        try {
            const data = await fetchFromApi('/settings');
            setServers(data.success ? data.servers : []);
        }
        catch (error) {
            toast.error('获取服务器列表失败。');
        }
    }, []);
    const fetchDownloadSettings = useCallback(async () => {
        try {
            const data = await fetchFromApi('/download/download-settings');
            setDownloadSettings(data);
        }
        catch (error) {
            toast.error(error.message || '获取下载设置失败。');
        }
    }, []);
    useEffect(() => {
        fetchServers();
        fetchDownloadSettings();
    }, [fetchServers, fetchDownloadSettings]);
    const handleOpenModal = (server = null) => {
        setEditingServer(server);
        setIsModalOpen(true);
    };
    const handleCloseModal = () => {
        setIsModalOpen(false);
        setEditingServer(null);
    };
    const handleSave = async (serverData) => {
        const isEditing = !!serverData.id;
        const path = isEditing ? `/settings/${serverData.id}` : '/settings';
        const method = isEditing ? 'PUT' : 'POST';
        const { token, ...payload } = serverData;
        const body = payload;
        if (token) {
            body.token = token;
        }
        try {
            const data = await fetchFromApi(path, { method, body: JSON.stringify(body) });
            if (data.success) {
                toast.success(data.message);
                fetchServers();
                handleCloseModal();
                if (!isEditing)
                    onSetupComplete();
            }
            else {
                toast.error(data.message || '保存失败。');
            }
        }
        catch (error) {
            toast.error(error.message || '保存服务器失败。');
        }
    };
    const handleDelete = async (serverId) => {
        if (window.confirm('确定要删除此服务器吗？')) {
            try {
                const data = await fetchFromApi(`/settings/${serverId}`, { method: 'DELETE' });
                if (data.success) {
                    toast.success(data.message);
                    fetchServers();
                }
                else {
                    toast.error(data.message || '删除失败。');
                }
            }
            catch (error) {
                toast.error(error.message || '删除服务器失败。');
            }
        }
    };
    const handleSaveDownloadSettings = async (data) => {
        try {
            const result = await fetchFromApi('/download/download-settings', {
                method: 'POST',
                body: JSON.stringify(data),
            });
            setDownloadSettings(result);
            toast.success('下载设置已保存。');
        }
        catch (error) {
            toast.error(error.message || '保存下载设置失败。');
        }
    };
    const handleTestDownloadConnection = async () => {
        try {
            return await fetchFromApi('/download/download-settings/test-api', {
                method: 'POST',
                body: JSON.stringify({}),
            });
        }
        catch (error) {
            return { success: false, message: error.message || '请求失败，请检查网络连接。' };
        }
    };
    const handleTestConnection = async (server) => {
        toast.info(`正在测试服务器 "${server.name}"...`);
        try {
            const data = await fetchFromApi(`/settings/${server.id}/test`, { method: 'POST' });
            if (data.success) {
                toast.success(`服务器 "${server.name}" 连接成功!`);
            }
            else {
                toast.error(`服务器 "${server.name}" 连接失败: ${data.message}`);
            }
        }
        catch (error) {
            toast.error(error.message || '测试连接失败。');
        }
    };
    return (_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between items-center mb-6", children: [_jsx("h1", { className: "text-3xl font-bold", children: "\u8BBE\u7F6E" }), activeTab === 'servers' && (_jsx(Button, { onClick: () => handleOpenModal(), children: "\u6DFB\u52A0\u670D\u52A1\u5668" }))] }), _jsx("div", { className: "border-b border-gray-200", children: _jsxs("nav", { className: "-mb-px flex space-x-8", "aria-label": "Tabs", children: [_jsx("button", { onClick: () => setActiveTab('servers'), className: `${activeTab === 'servers'
                                ? 'border-indigo-500 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`, children: "\u670D\u52A1\u5668\u8BBE\u7F6E" }), _jsx("button", { onClick: () => setActiveTab('downloads'), className: `${activeTab === 'downloads'
                                ? 'border-indigo-500 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`, children: "\u4E0B\u8F7D\u8BBE\u7F6E" })] }) }), _jsxs("div", { className: "mt-6", children: [activeTab === 'servers' && (_jsx("div", { className: "bg-white shadow rounded-lg", children: _jsx("ul", { className: "divide-y divide-gray-200", children: servers.map((server) => (_jsxs("li", { className: "p-4 flex justify-between items-center", children: [_jsxs("div", { children: [_jsxs("p", { className: "font-semibold", children: [server.name, " ", _jsxs("span", { className: "text-sm text-gray-500 capitalize", children: ["(", server.server_type, ")"] })] }), _jsx("p", { className: "text-sm text-gray-600", children: server.url })] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx(Button, { variant: "outline", size: "sm", onClick: () => handleTestConnection(server), children: "\u6D4B\u8BD5" }), _jsx(Button, { variant: "outline", size: "sm", onClick: () => handleOpenModal(server), children: "\u7F16\u8F91" }), _jsx(Button, { variant: "danger", size: "sm", onClick: () => handleDelete(server.id), children: "\u5220\u9664" })] })] }, server.id))) }) })), activeTab === 'downloads' && (_jsx("div", { className: "bg-white shadow rounded-lg p-6", children: _jsx(DownloadSettings, { settings: downloadSettings, onSave: handleSaveDownloadSettings, onTestConnection: handleTestDownloadConnection }) }))] }), isModalOpen && (_jsx(ServerModal, { isOpen: isModalOpen, server: editingServer, onClose: handleCloseModal, onSave: handleSave }))] }));
};
export default SettingsPage;
