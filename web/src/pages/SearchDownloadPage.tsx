import React, { useState } from 'react';
import { toast } from 'sonner';
import { fetchFromApi } from '../lib/api';
import Button from '../components/Button';
import Input from '../components/Input';
import { Search, Download } from 'lucide-react';
import { SearchResultItem } from '../types';

const SearchDownloadPage: React.FC = () => {
  // 搜索相关状态
  const [keyword, setKeyword] = useState('');
  const [platform, setPlatform] = useState<'qq' | 'netease' | ''>('');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<Record<string, boolean>>({});
  
  // 分页相关状态
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 10;

  // 执行搜索
  const handleSearch = async () => {
    if (!keyword.trim()) {
      toast.error('请输入搜索关键词');
      return;
    }
    
    setLoading(true);
    try {
      const data = await fetchFromApi(
        `/download/search?keyword=${encodeURIComponent(keyword)}&platform=${platform}&page=${page}&size=${pageSize}`
      );
      
      if (data.success) {
        setSearchResults(data.results);
        setTotal(data.total);
        setPage(data.page);
      } else {
        toast.error(data.message || '搜索失败');
      }
    } catch (error: any) {
      toast.error(error.message || '搜索请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 下载歌曲
  const handleDownload = async (item: SearchResultItem) => {
    setDownloading(prev => ({ ...prev, [item.song_id]: true }));
    try {
      // 这里需要一个任务ID来下载，但在搜索页面我们没有特定的任务
      // 我们可以创建一个特殊的任务或者直接下载
      const data = await fetchFromApi('/download/single', {
        method: 'POST',
        body: JSON.stringify({
          task_id: 0, // 特殊任务ID表示直接下载
          song_id: item.song_id,
          title: item.title,
          artist: item.artist,
          album: item.album,
          platform: item.platform
        }),
      });
      
      if (data.success) {
        toast.success(`《${item.title}》已加入下载队列`);
      } else {
        toast.error(data.message || '下载失败');
      }
    } catch (error: any) {
      toast.error(error.message || '下载请求失败');
    } finally {
      setDownloading(prev => ({ ...prev, [item.song_id]: false }));
    }
  };

  // 处理回车键搜索
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 格式化时长
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-4 sm:p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">搜索下载</h1>
        <p className="mt-2 text-gray-600">搜索并下载您喜欢的音乐</p>
      </header>

      {/* 搜索区域 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-grow">
            <Input
              label="搜索关键词"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="请输入歌曲名、歌手或专辑"
              required
            />
          </div>
          <div className="w-full sm:w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">平台</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value as 'qq' | 'netease' | '')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">全部平台</option>
              <option value="qq">QQ音乐</option>
              <option value="netease">网易云音乐</option>
            </select>
          </div>
          <div className="flex items-end">
            <Button 
              onClick={handleSearch} 
              loading={loading}
              className="w-full sm:w-auto flex items-center gap-2"
            >
              <Search className="h-5 w-5" />
              搜索
            </Button>
          </div>
        </div>
      </div>

      {/* 搜索结果 */}
      {searchResults.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">搜索结果</h2>
            <p className="text-sm text-gray-500 mt-1">
              找到 {total} 首歌曲
            </p>
          </div>
          <ul className="divide-y divide-gray-200">
            {searchResults.map((item) => (
              <li key={`${item.song_id}-${item.platform}`} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <h3 className="text-base font-medium text-gray-900 truncate">{item.title}</h3>
                      {item.platform && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {item.platform === 'qq' ? 'QQ音乐' : item.platform === 'netease' ? '网易云音乐' : item.platform}
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-col sm:flex-row sm:flex-wrap sm:space-x-4">
                      <span className="flex items-center text-sm text-gray-500">
                        {item.artist}
                      </span>
                      {item.album && (
                        <span className="flex items-center text-sm text-gray-500">
                          专辑: {item.album}
                        </span>
                      )}
                      {item.duration && (
                        <span className="flex items-center text-sm text-gray-500">
                          时长: {formatDuration(item.duration)}
                        </span>
                      )}
                      {item.quality && (
                        <span className="flex items-center text-sm text-gray-500">
                          音质: {item.quality}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <Button
                      onClick={() => handleDownload(item)}
                      loading={downloading[item.song_id]}
                      className="flex items-center gap-2"
                    >
                      <Download className="h-4 w-4" />
                      下载
                    </Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          
          {/* 分页 */}
          {total > pageSize && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                显示第 {(page - 1) * pageSize + 1} 到 {Math.min(page * pageSize, total)} 条，共 {total} 条
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => setPage(prev => Math.max(1, prev - 1))}
                  disabled={page === 1}
                  variant="secondary"
                >
                  上一页
                </Button>
                <Button
                  onClick={() => setPage(prev => prev + 1)}
                  disabled={page * pageSize >= total}
                  variant="secondary"
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 无结果提示 */}
      {!loading && searchResults.length === 0 && keyword && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            <Search className="mx-auto h-12 w-12" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">未找到相关结果</h3>
            <p className="mt-1 text-gray-500">请尝试使用其他关键词或平台进行搜索</p>
          </div>
        </div>
      )}

      {/* 初始状态提示 */}
      {!keyword && searchResults.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            <Search className="mx-auto h-12 w-12" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">搜索音乐</h3>
            <p className="mt-1 text-gray-500">请输入关键词开始搜索您喜欢的音乐</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchDownloadPage;