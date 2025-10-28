import React, { useState, useEffect, useCallback } from 'react';
import { fetchFromApi } from '../lib/api';
import Button from '../components/Button';
import ServerModal from '../components/ServerModal';
import DownloadSettings from '../components/DownloadSettings';
import { toast } from 'sonner';
import { DownloadSettingsData } from '../types';

interface Server {
  id: number;
  name: string;
  server_type: string;
  url: string;
}

type ServerFormData = Omit<Server, 'id'> & { id?: number; token?: string };

const SettingsPage: React.FC<{ onSetupComplete: () => void }> = ({ onSetupComplete }) => {
  const [servers, setServers] = useState<Server[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingServer, setEditingServer] = useState<Server | null>(null);
  const [activeTab, setActiveTab] = useState('servers');
  const [downloadSettings, setDownloadSettings] = useState<DownloadSettingsData | null>(null);


  const fetchServers = useCallback(async () => {
    try {
      const data = await fetchFromApi('/settings');
      setServers(data.success ? data.servers : []);
    } catch (error) {
      toast.error('获取服务器列表失败。');
    }
  }, []);

  const fetchDownloadSettings = useCallback(async () => {
    try {
      const data = await fetchFromApi('/download/download-settings');
      setDownloadSettings(data);
    } catch (error: any) {
      toast.error(error.message || '获取下载设置失败。');
    }
  }, []);

  useEffect(() => {
    fetchServers();
    fetchDownloadSettings();
  }, [fetchServers, fetchDownloadSettings]);

  const handleOpenModal = (server: Server | null = null) => {
    setEditingServer(server);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingServer(null);
  };

  const handleSave = async (serverData: ServerFormData) => {
    const isEditing = !!serverData.id;
    const path = isEditing ? `/settings/${serverData.id}` : '/settings';
    const method = isEditing ? 'PUT' : 'POST';
    
    const { token, ...payload } = serverData;
    const body: { [key: string]: any } = payload;
    if (token) {
        body.token = token;
    }

    try {
      const data = await fetchFromApi(path, { method, body: JSON.stringify(body) });
      if (data.success) {
        toast.success(data.message);
        fetchServers();
        handleCloseModal();
        if (!isEditing) onSetupComplete();
      } else {
        toast.error(data.message || '保存失败。');
      }
    } catch (error: any) {
      toast.error(error.message || '保存服务器失败。');
    }
  };

  const handleDelete = async (serverId: number) => {
    if (window.confirm('确定要删除此服务器吗？')) {
      try {
        const data = await fetchFromApi(`/settings/${serverId}`, { method: 'DELETE' });
        if (data.success) {
          toast.success(data.message);
          fetchServers();
        } else {
          toast.error(data.message || '删除失败。');
        }
      } catch (error: any) {
        toast.error(error.message || '删除服务器失败。');
      }
    }
  };

  const handleSaveDownloadSettings = async (data: DownloadSettingsData) => {
    try {
      const result = await fetchFromApi('/download/download-settings', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      setDownloadSettings(result);
      toast.success('下载设置已保存。');
    } catch (error: any) {
      toast.error(error.message || '保存下载设置失败。');
    }
  };

  const handleTestDownloadConnection = async () => {
    try {
      return await fetchFromApi('/download/download-settings/test-api', {
        method: 'POST',
        body: JSON.stringify({}),
      });
    } catch (error: any) {
      return { success: false, message: error.message || '请求失败，请检查网络连接。' };
    }
  };

  const handleTestConnection = async (server: Server) => {
    toast.info(`正在测试服务器 "${server.name}"...`);
    try {
      const data = await fetchFromApi(`/settings/${server.id}/test`, { method: 'POST' });
      if (data.success) {
        toast.success(`服务器 "${server.name}" 连接成功!`);
      } else {
        toast.error(`服务器 "${server.name}" 连接失败: ${data.message}`);
      }
    } catch (error: any) {
      toast.error(error.message || '测试连接失败。');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">设置</h1>
        {activeTab === 'servers' && (
          <Button onClick={() => handleOpenModal()}>添加服务器</Button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('servers')}
            className={`${
              activeTab === 'servers'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            服务器设置
          </button>
          <button
            onClick={() => setActiveTab('downloads')}
            className={`${
              activeTab === 'downloads'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            下载设置
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'servers' && (
          <div className="bg-white shadow rounded-lg">
            <ul className="divide-y divide-gray-200">
              {servers.map((server) => (
                <li key={server.id} className="p-4 flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{server.name} <span className="text-sm text-gray-500 capitalize">({server.server_type})</span></p>
                    <p className="text-sm text-gray-600">{server.url}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleTestConnection(server)}>测试</Button>
                    <Button variant="outline" size="sm" onClick={() => handleOpenModal(server)}>编辑</Button>
                    <Button variant="danger" size="sm" onClick={() => handleDelete(server.id)}>删除</Button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === 'downloads' && (
          <div className="bg-white shadow rounded-lg p-6">
            <DownloadSettings
              settings={downloadSettings}
              onSave={handleSaveDownloadSettings}
              onTestConnection={handleTestDownloadConnection}
            />
          </div>
        )}
      </div>

      {isModalOpen && (
        <ServerModal
          isOpen={isModalOpen}
          server={editingServer}
          onClose={handleCloseModal}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default SettingsPage;
