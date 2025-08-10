import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { fetchFromApi } from '../lib/api';


type Log = {
  id: number;
  task_id: number;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
};

const LogsPage: React.FC = () => {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [taskIdFilter, setTaskIdFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');

  const fetchLogs = async (taskId?: string, level?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (taskId) params.append('task_id', taskId);
      if (level) params.append('level', level);
      
      const url = `/logs?${params.toString()}`;
      const data = await fetchFromApi(url);
      if (data.success) {
        // 如果有搜索关键词，进行前端过滤
        let filteredLogs = data.logs;
        if (searchFilter) {
          filteredLogs = filteredLogs.filter((log: Log) => 
            log.message.toLowerCase().includes(searchFilter.toLowerCase())
          );
        }
        setLogs(filteredLogs);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleFilter = () => {
    fetchLogs(taskIdFilter, levelFilter);
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(logs, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `logs-export-${new Date().toISOString().slice(0, 10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return <div className="text-center p-8">Loading logs...</div>;
  }

  return (
    <div className="p-4 sm:p-8">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-6">活动日志</h1>
      <div className="mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-end">
            <div>
              <label htmlFor="task-id-filter" className="text-sm font-medium text-gray-700 block mb-1">任务ID</label>
              <input
                id="task-id-filter"
                type="text"
                placeholder="按任务ID筛选"
                value={taskIdFilter}
                onChange={(e) => setTaskIdFilter(e.target.value)}
                className="w-full p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="level-filter" className="text-sm font-medium text-gray-700 block mb-1">日志级别</label>
              <select
                id="level-filter"
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="w-full p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">所有级别</option>
                <option value="info">信息</option>
                <option value="warning">警告</option>
                <option value="error">错误</option>
              </select>
            </div>
            <div>
              <label htmlFor="search-filter" className="text-sm font-medium text-gray-700 block mb-1">消息内容</label>
              <input
                id="search-filter"
                type="text"
                placeholder="搜索消息..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleFilter}
                className="w-full p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
              >
                筛选
              </button>
              <button
                onClick={handleExport}
                className="w-full p-2 bg-gray-700 text-white rounded-md hover:bg-gray-800 transition"
              >
                导出
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-white shadow rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">级别</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">任务ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">消息</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      log.level === 'error' ? 'bg-red-100 text-red-800' :
                      log.level === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {log.level}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{log.task_id}</td>
                  <td className="px-6 py-4 text-sm text-gray-900 break-words max-w-md">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LogsPage;
