import React, { useState } from 'react';
import Button from './Button';
import Input from './Input';
import Modal from './Modal';

interface Server {
  id: number;
  name: string;
  server_type: string;
  url: string;
}

type ServerFormData = Omit<Server, 'id'> & { id?: number; token?: string };

interface ServerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (serverData: ServerFormData) => Promise<void>;
  server: Server | null;
}

const ServerModal: React.FC<ServerModalProps> = ({ isOpen, onClose, onSave, server }) => {
  const [formData, setFormData] = useState<ServerFormData>({
    name: server?.name || '',
    server_type: server?.server_type || 'plex',
    url: server?.url || '',
    token: '',
    ...(server && { id: server.id }),
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(formData);
  };

  return (
    <Modal isOpen={isOpen} title={server ? '编辑服务器' : '添加服务器'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input name="name" label="名称" value={formData.name} onChange={handleChange} required />
        <div>
          <label htmlFor="server_type" className="block text-sm font-medium text-gray-700">服务器类型</label>
          <select name="server_type" value={formData.server_type} onChange={handleChange} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
            <option value="plex">Plex</option>
            <option value="jellyfin">Jellyfin</option>
            <option value="emby">Emby</option>
          </select>
        </div>
        <Input name="url" label="URL" value={formData.url} onChange={handleChange} placeholder="http://192.168.1.100:32400" required />
        <Input name="token" label="Token" type="password" value={formData.token || ''} onChange={handleChange} placeholder={server ? '留空则不修改' : ''} required={!server} />
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onClose}>取消</Button>
          <Button type="submit">保存</Button>
        </div>
      </form>
    </Modal>
  );
};

export default ServerModal;
