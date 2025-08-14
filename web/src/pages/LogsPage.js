import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { fetchFromApi } from '../lib/api';
const LogsPage = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [taskIdFilter, setTaskIdFilter] = useState('');
    const [levelFilter, setLevelFilter] = useState('');
    const [searchFilter, setSearchFilter] = useState('');
    const fetchLogs = async (taskId, level) => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (taskId)
                params.append('task_id', taskId);
            if (level)
                params.append('level', level);
            const url = `/logs?${params.toString()}`;
            const data = await fetchFromApi(url);
            if (data.success) {
                // 如果有搜索关键词，进行前端过滤
                let filteredLogs = data.logs;
                if (searchFilter) {
                    filteredLogs = filteredLogs.filter((log) => log.message.toLowerCase().includes(searchFilter.toLowerCase()));
                }
                setLogs(filteredLogs);
            }
        }
        catch (error) {
            console.error('Failed to fetch logs:', error);
        }
        finally {
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
        const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
        const exportFileDefaultName = `logs-export-${new Date().toISOString().slice(0, 10)}.json`;
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    };
    if (loading) {
        return _jsx("div", { className: "text-center p-8", children: "Loading logs..." });
    }
    return (_jsxs("div", { className: "p-4 sm:p-8", children: [_jsx("h1", { className: "text-3xl font-bold tracking-tight text-gray-900 mb-6", children: "\u6D3B\u52A8\u65E5\u5FD7" }), _jsx("div", { className: "mb-6", children: _jsx("div", { className: "bg-white p-4 rounded-lg shadow-sm", children: _jsxs("div", { className: "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-end", children: [_jsxs("div", { children: [_jsx("label", { htmlFor: "task-id-filter", className: "text-sm font-medium text-gray-700 block mb-1", children: "\u4EFB\u52A1ID" }), _jsx("input", { id: "task-id-filter", type: "text", placeholder: "\u6309\u4EFB\u52A1ID\u7B5B\u9009", value: taskIdFilter, onChange: (e) => setTaskIdFilter(e.target.value), className: "w-full p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "level-filter", className: "text-sm font-medium text-gray-700 block mb-1", children: "\u65E5\u5FD7\u7EA7\u522B" }), _jsxs("select", { id: "level-filter", value: levelFilter, onChange: (e) => setLevelFilter(e.target.value), className: "w-full p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500", children: [_jsx("option", { value: "", children: "\u6240\u6709\u7EA7\u522B" }), _jsx("option", { value: "info", children: "\u4FE1\u606F" }), _jsx("option", { value: "warning", children: "\u8B66\u544A" }), _jsx("option", { value: "error", children: "\u9519\u8BEF" })] })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "search-filter", className: "text-sm font-medium text-gray-700 block mb-1", children: "\u6D88\u606F\u5185\u5BB9" }), _jsx("input", { id: "search-filter", type: "text", placeholder: "\u641C\u7D22\u6D88\u606F...", value: searchFilter, onChange: (e) => setSearchFilter(e.target.value), className: "w-full p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" })] }), _jsxs("div", { className: "flex gap-2", children: [_jsx("button", { onClick: handleFilter, className: "w-full p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition", children: "\u7B5B\u9009" }), _jsx("button", { onClick: handleExport, className: "w-full p-2 bg-gray-700 text-white rounded-md hover:bg-gray-800 transition", children: "\u5BFC\u51FA" })] })] }) }) }), _jsx("div", { className: "bg-white shadow rounded-lg", children: _jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "min-w-full divide-y divide-gray-200", children: [_jsx("thead", { className: "bg-gray-50", children: _jsxs("tr", { children: [_jsx("th", { className: "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "\u65F6\u95F4" }), _jsx("th", { className: "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "\u7EA7\u522B" }), _jsx("th", { className: "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "\u4EFB\u52A1ID" }), _jsx("th", { className: "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "\u6D88\u606F" })] }) }), _jsx("tbody", { className: "bg-white divide-y divide-gray-200", children: logs.map((log) => (_jsxs("tr", { children: [_jsx("td", { className: "px-6 py-4 whitespace-nowrap text-sm text-gray-500", children: format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss') }), _jsx("td", { className: "px-6 py-4 whitespace-nowrap", children: _jsx("span", { className: `px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${log.level === 'error' ? 'bg-red-100 text-red-800' :
                                                    log.level === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                                                        'bg-green-100 text-green-800'}`, children: log.level }) }), _jsx("td", { className: "px-6 py-4 whitespace-nowrap text-sm text-gray-500", children: log.task_id }), _jsx("td", { className: "px-6 py-4 text-sm text-gray-900 break-words max-w-md", children: log.message })] }, log.id))) })] }) }) })] }));
};
export default LogsPage;
