import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
const DownloadSettings = ({ settings, onSave, onTestConnection }) => {
    // 使用 useState 来管理表单的本地状态
    const [formData, setFormData] = useState({
        download_path: '',
        preferred_quality: 'high',
        download_lyrics: true,
        auto_download: false,
        max_concurrent_downloads: 3,
        log_retention_days: 30,
        scan_interval_minutes: 30
    });
    const [testResult, setTestResult] = useState(null);
    const [isTesting, setIsTesting] = useState(false);
    // 当外部传入的 settings prop 变化时，更新表单的本地状态
    useEffect(() => {
        if (settings) {
            setFormData(settings);
        }
    }, [settings]);
    // 处理表单输入变化
    const handleChange = (e) => {
        const { name, value, type } = e.target;
        // 特别处理复选框
        const isCheckbox = type === 'checkbox';
        if (isCheckbox) {
            const checkbox = e.target;
            setFormData(prev => ({ ...prev, [name]: checkbox.checked }));
        }
        else {
            // 处理数字输入
            if (name === 'max_concurrent_downloads' || name === 'log_retention_days' || name === 'scan_interval_minutes') {
                setFormData(prev => ({ ...prev, [name]: parseInt(value, 10) || 0 }));
            }
            else {
                setFormData(prev => ({ ...prev, [name]: value }));
            }
        }
    };
    // 处理表单提交
    const handleSubmit = async (e) => {
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
    return (_jsxs("form", { onSubmit: handleSubmit, className: "space-y-6", children: [_jsxs("div", { className: "api-connection-section", children: [_jsx("label", { children: "API 连接测试" }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("button", { type: "button", onClick: handleTestConnection, disabled: isTesting, children: isTesting ? '测试中...' : '测试API连接' })] }), testResult && (_jsx("p", { className: testResult.success ? 'text-green-500' : 'text-red-500', children: testResult.message }))] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "download_path", children: "\u4E0B\u8F7D\u8DEF\u5F84" }), _jsx("input", { id: "download_path", name: "download_path", type: "text", value: formData.download_path, onChange: handleChange })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "preferred_quality", children: "\u9996\u9009\u97F3\u8D28" }), _jsxs("select", { id: "preferred_quality", name: "preferred_quality", value: formData.preferred_quality, onChange: handleChange, children: [_jsx("option", { value: "standard", children: "\u6807\u51C6" }), _jsx("option", { value: "high", children: "\u9AD8\u54C1" }), _jsx("option", { value: "lossless", children: "\u65E0\u635F" })] })] }), _jsxs("div", { className: "grid grid-cols-2 gap-4", children: [_jsxs("div", { className: "flex items-center", children: [_jsx("input", { id: "download_lyrics", name: "download_lyrics", type: "checkbox", checked: formData.download_lyrics, onChange: handleChange }), _jsx("label", { htmlFor: "download_lyrics", className: "ml-2", children: "\u4E0B\u8F7D\u6B4C\u8BCD" })] }), _jsxs("div", { className: "flex items-center", children: [_jsx("input", { id: "auto_download", name: "auto_download", type: "checkbox", checked: formData.auto_download, onChange: handleChange }), _jsx("label", { htmlFor: "auto_download", className: "ml-2", children: "\u81EA\u52A8\u4E0B\u8F7D" })] })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "max_concurrent_downloads", children: "\u6700\u5927\u5E76\u53D1\u4E0B\u8F7D\u6570" }), _jsx("input", { id: "max_concurrent_downloads", name: "max_concurrent_downloads", type: "number", min: "1", max: "10", value: formData.max_concurrent_downloads, onChange: handleChange })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "log_retention_days", children: "\u65E5\u5FD7\u4FDD\u7559\u5929\u6570" }), _jsx("input", { id: "log_retention_days", name: "log_retention_days", type: "number", min: "1", value: formData.log_retention_days, onChange: handleChange })] }), _jsxs("div", { children: [_jsx("label", { htmlFor: "scan_interval_minutes", children: "\u626B\u63CF\u95F4\u9694\uFF08\u5206\u949F\uFF09" }), _jsx("input", { id: "scan_interval_minutes", name: "scan_interval_minutes", type: "number", min: "5", max: "1440", value: formData.scan_interval_minutes, onChange: handleChange }), _jsx("p", { className: "text-sm text-gray-500 mt-1", children: "\u5B9A\u671F\u626B\u63CF\u65B0\u97F3\u4E50\u7684\u95F4\u9694\u65F6\u95F4\uFF0C\u8303\u56F4\uFF1A5-1440\u5206\u949F\uFF081\u5929\uFF09" })] }), _jsx("div", { children: _jsx("button", { type: "submit", children: "\u4FDD\u5B58\u8BBE\u7F6E" }) })] }));
};
export default DownloadSettings;
