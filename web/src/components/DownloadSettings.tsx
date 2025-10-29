
import React, { useState, useEffect } from 'react';
import { DownloadSettingsData } from '../types';

// 定义组件的 props
interface DownloadSettingsProps {
  // 从父组件传入的当前设置
  settings: DownloadSettingsData | null;
  // 保存设置后要调用的回调函数
  onSave: (settings: DownloadSettingsData) => Promise<void>;
  // 测试连接的回调函数
  onTestConnection: () => Promise<{ success: boolean; message: string }>;
}

const DownloadSettings: React.FC<DownloadSettingsProps> = ({ settings, onSave, onTestConnection }) => {
  // 使用 useState 来管理表单的本地状态
  const [formData, setFormData] = useState<DownloadSettingsData>({
    download_path: '',
    preferred_quality: 'high',
    download_lyrics: true,
    auto_download: false,
    max_concurrent_downloads: 3,
    log_retention_days: 30,
    scan_interval_minutes: 30
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
        // 处理数字输入
        if (name === 'max_concurrent_downloads' || name === 'log_retention_days' || name === 'scan_interval_minutes') {
            setFormData(prev => ({ ...prev, [name]: parseInt(value, 10) || 0 }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    }
  };

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(formData);
  };

  // 处理测试连接按钮点击
  const handleTestConnection = async () => {
    setIsTesting(true);
    const result = await onTestConnection();
    setTestResult(result);
    setIsTesting(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">下载设置</h2>
      
      {/* API 连接与路径设置卡片 */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-medium mb-4 text-gray-700 flex items-center">
          <span className="mr-2">🌐</span> 连接与路径设置
        </h3>
        
        {/* API 连接测试 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">API 连接测试</label>
          <div className="flex items-center space-x-4">
            <button 
              type="button" 
              onClick={handleTestConnection} 
              disabled={isTesting}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 transition-colors"
            >
              {isTesting ? '测试中...' : '测试API连接'}
            </button>
            {testResult && (
              <p className={`text-sm ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.message}
              </p>
            )}
          </div>
        </div>

        {/* 下载路径 */}
        <div className="mt-4">
          <label htmlFor="download_path" className="block text-sm font-medium text-gray-700 mb-2">
            下载路径
          </label>
          <input
            id="download_path"
            name="download_path"
            type="text"
            value={formData.download_path}
            onChange={handleChange}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="/path/to/downloads"
          />
          <p className="text-xs text-gray-500 mt-1">下载文件的保存位置</p>
        </div>
      </div>

      {/* 音频质量与格式设置卡片 */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-medium mb-4 text-gray-700 flex items-center">
          <span className="mr-2">🎵</span> 音频质量与格式
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 音质选择 */}
          <div>
            <label htmlFor="preferred_quality" className="block text-sm font-medium text-gray-700 mb-2">
              首选音质
            </label>
            <select
              id="preferred_quality"
              name="preferred_quality"
              value={formData.preferred_quality}
              onChange={handleChange}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="standard">标准</option>
              <option value="high">高品</option>
              <option value="lossless">无损</option>
            </select>
          </div>

          {/* 下载歌词 */}
          <div className="flex items-center">
            <input
              id="download_lyrics"
              name="download_lyrics"
              type="checkbox"
              checked={formData.download_lyrics}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="download_lyrics" className="ml-2 block text-sm text-gray-700">
              下载歌词
            </label>
          </div>
        </div>
      </div>

      {/* 下载行为设置卡片 */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-medium mb-4 text-gray-700 flex items-center">
          <span className="mr-2">⚙️</span> 下载行为设置
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 自动下载 */}
          <div className="flex items-center">
            <input
              id="auto_download"
              name="auto_download"
              type="checkbox"
              checked={formData.auto_download}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="auto_download" className="ml-2 block text-sm text-gray-700">
              自动下载新增音乐
            </label>
          </div>

          {/* 并发下载数 */}
          <div>
            <label htmlFor="max_concurrent_downloads" className="block text-sm font-medium text-gray-700 mb-2">
              最大并发下载数
            </label>
            <input
              id="max_concurrent_downloads"
              name="max_concurrent_downloads"
              type="number"
              min="1"
              max="10"
              value={formData.max_concurrent_downloads}
              onChange={handleChange}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">同时下载的歌曲数量，建议设置为3-5</p>
          </div>
        </div>
      </div>

      {/* 维护与调度设置卡片 */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-medium mb-4 text-gray-700 flex items-center">
          <span className="mr-2">🔧</span> 维护与调度
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 日志保留天数 */}
          <div>
            <label htmlFor="log_retention_days" className="block text-sm font-medium text-gray-700 mb-2">
              日志保留天数
            </label>
            <input
              id="log_retention_days"
              name="log_retention_days"
              type="number"
              min="1"
              value={formData.log_retention_days}
              onChange={handleChange}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">系统日志的保留时间（天）</p>
          </div>
          
          {/* 扫描间隔（分钟） */}
          <div>
            <label htmlFor="scan_interval_minutes" className="block text-sm font-medium text-gray-700 mb-2">
              扫描间隔（分钟）
            </label>
            <input
              id="scan_interval_minutes"
              name="scan_interval_minutes"
              type="number"
              min="5"
              max="1440"
              value={formData.scan_interval_minutes}
              onChange={handleChange}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              定期扫描新音乐的间隔时间，范围：5-1440分钟（1天）
            </p>
          </div>
        </div>
      </div>

      {/* 提交按钮 */}
      <div className="flex justify-end pt-4">
        <button 
          type="submit" 
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          保存设置
        </button>
      </div>
    </form>
  );
};

export default DownloadSettings;
