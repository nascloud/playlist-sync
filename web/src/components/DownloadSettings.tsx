
import React, { useState, useEffect } from 'react';
import { DownloadSettingsData } from '../types';

// 定义组件的 props
interface DownloadSettingsProps {
  // 从父组件传入的当前设置
  settings: DownloadSettingsData | null;
  // 保存设置后要调用的回调函数
  onSave: (settings: DownloadSettingsData) => Promise<void>;
  // 测试连接的回调函数
  onTestConnection: (apiKey: string) => Promise<{ success: boolean; message: string }>;
}

const DownloadSettings: React.FC<DownloadSettingsProps> = ({ settings, onSave, onTestConnection }) => {
  // 使用 useState 来管理表单的本地状态
  const [formData, setFormData] = useState<DownloadSettingsData>({
    api_key: '',
    download_path: '',
    preferred_quality: 'high',
    download_lyrics: true,
    auto_download: false,
    max_concurrent_downloads: 3,
  });
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // 当外部传入的 settings prop 变化时，更新表单的本地状态
  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  // 处理表单输入变化
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    // 特别处理复选框
    const isCheckbox = type === 'checkbox';
    if (isCheckbox) {
        const checkbox = e.target as HTMLInputElement;
        setFormData(prev => ({ ...prev, [name]: checkbox.checked }));
    } else {
        setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(formData);
  };

  // 处理测试连接按钮点击
  const handleTestConnection = async () => {
    if (!formData.api_key) {
      setTestResult({ success: false, message: '请输入API Key后再测试' });
      return;
    }
    setIsTesting(true);
    const result = await onTestConnection(formData.api_key);
    setTestResult(result);
    setIsTesting(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* API Key 输入 */}
      <div className="api-key-section">
        <label htmlFor="api_key">API Key</label>
        <div className="flex items-center space-x-2">
          <input
            id="api_key"
            name="api_key"
            type="password"
            value={formData.api_key || ''}
            onChange={handleChange}
            placeholder="输入您的下载API Key"
            className="flex-grow"
          />
          <button type="button" onClick={handleTestConnection} disabled={isTesting}>
            {isTesting ? '测试中...' : '测试连接'}
          </button>
        </div>
        {testResult && (
          <p className={testResult.success ? 'text-green-500' : 'text-red-500'}>
            {testResult.message}
          </p>
        )}
      </div>

      {/* 下载路径 */}
      <div>
        <label htmlFor="download_path">下载路径</label>
        <input
          id="download_path"
          name="download_path"
          type="text"
          value={formData.download_path}
          onChange={handleChange}
        />
      </div>

      {/* 音质选择 */}
      <div>
        <label htmlFor="preferred_quality">首选音质</label>
        <select
          id="preferred_quality"
          name="preferred_quality"
          value={formData.preferred_quality}
          onChange={handleChange}
        >
          <option value="standard">标准</option>
          <option value="high">高品</option>
          <option value="lossless">无损</option>
        </select>
      </div>

      {/* 其他选项 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center">
          <input
            id="download_lyrics"
            name="download_lyrics"
            type="checkbox"
            checked={formData.download_lyrics}
            onChange={handleChange}
          />
          <label htmlFor="download_lyrics" className="ml-2">下载歌词</label>
        </div>
        <div className="flex items-center">
          <input
            id="auto_download"
            name="auto_download"
            type="checkbox"
            checked={formData.auto_download}
            onChange={handleChange}
          />
          <label htmlFor="auto_download" className="ml-2">自动下载</label>
        </div>
      </div>
      
      {/* 并发下载数 */}
      <div>
          <label htmlFor="max_concurrent_downloads">最大并发下载数</label>
          <input
            id="max_concurrent_downloads"
            name="max_concurrent_downloads"
            type="number"
            min="1"
            max="10"
            value={formData.max_concurrent_downloads}
            onChange={handleChange}
          />
      </div>

      {/* 提交按钮 */}
      <div>
        <button type="submit">保存设置</button>
      </div>
    </form>
  );
};

export default DownloadSettings;
