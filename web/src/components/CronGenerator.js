import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
const CronGenerator = ({ value, onChange }) => {
    // 解析现有的cron表达式
    const parseCron = (cron) => {
        const parts = cron.split(' ');
        if (parts.length >= 5) {
            return {
                minute: parts[0],
                hour: parts[1],
                dayOfMonth: parts[2],
                month: parts[3],
                dayOfWeek: parts[4]
            };
        }
        return {
            minute: '*',
            hour: '*',
            dayOfMonth: '*',
            month: '*',
            dayOfWeek: '*'
        };
    };
    const [cronParts, setCronParts] = useState(parseCron(value || '0 2 * * *'));
    const [preset, setPreset] = useState('custom');
    const [error, setError] = useState('');
    // 预设选项
    const presets = [
        { value: 'hourly', label: '每小时', cron: '0 * * * *' },
        { value: 'daily', label: '每日', cron: '0 2 * * *' },
        { value: 'weekly', label: '每周', cron: '0 2 * * 0' },
        { value: 'monthly', label: '每月', cron: '0 2 1 * *' },
        { value: 'custom', label: '自定义' }
    ];
    // 当外部传入的value变化时，同步内部状态
    useEffect(() => {
        const matchedPreset = presets.find(p => p.cron === value);
        setPreset(matchedPreset ? matchedPreset.value : 'custom');
        setCronParts(parseCron(value || '0 2 * * *'));
    }, [value]);
    // 当预设改变时，调用onChange更新外部状态
    const handlePresetChange = (e) => {
        const presetValue = e.target.value;
        setPreset(presetValue);
        const selectedPreset = presets.find(p => p.value === presetValue);
        if (selectedPreset && selectedPreset.cron) {
            onChange(selectedPreset.cron);
        }
    };
    const handlePartChange = (part, value) => {
        setCronParts(prev => ({
            ...prev,
            [part]: value
        }));
        setPreset('custom');
    };
    // 验证cron表达式各部分是否有效
    const isValidCronPart = (part, field) => {
        // 允许的字符：数字、逗号、连字符、星号、斜杠
        const validChars = /^[\d*,\-\/]+$/;
        // 特殊处理：星期字段还允许0-7的数字（0和7都表示星期日）
        if (field === 'dayOfWeek') {
            const numericParts = part.split(/[*,\-\/]/);
            for (const num of numericParts) {
                if (num !== '' && (isNaN(parseInt(num)) || parseInt(num) < 0 || parseInt(num) > 7)) {
                    if (num !== '*')
                        return false;
                }
            }
            return true;
        }
        // 其他字段的基本验证
        if (part === '*' || part === '?' || part === '')
            return true;
        if (!validChars.test(part))
            return false;
        // 数字范围验证
        const numericParts = part.split(/[*,\-\/]/);
        for (const num of numericParts) {
            if (num !== '' && isNaN(parseInt(num))) {
                if (num !== '*')
                    return false;
            }
        }
        // 根据字段类型检查数值范围
        switch (field) {
            case 'minute':
                for (const num of numericParts) {
                    if (num !== '' && !isNaN(parseInt(num)) && (parseInt(num) < 0 || parseInt(num) > 59)) {
                        return false;
                    }
                }
                break;
            case 'hour':
                for (const num of numericParts) {
                    if (num !== '' && !isNaN(parseInt(num)) && (parseInt(num) < 0 || parseInt(num) > 23)) {
                        return false;
                    }
                }
                break;
            case 'dayOfMonth':
                for (const num of numericParts) {
                    if (num !== '' && !isNaN(parseInt(num)) && (parseInt(num) < 1 || parseInt(num) > 31)) {
                        return false;
                    }
                }
                break;
            case 'month':
                for (const num of numericParts) {
                    if (num !== '' && !isNaN(parseInt(num)) && (parseInt(num) < 1 || parseInt(num) > 12)) {
                        return false;
                    }
                }
                break;
        }
        return true;
    };
    const handlePartBlur = () => {
        const cron = `${cronParts.minute} ${cronParts.hour} ${cronParts.dayOfMonth} ${cronParts.month} ${cronParts.dayOfWeek}`;
        // 验证每个部分
        const isMinuteValid = isValidCronPart(cronParts.minute, 'minute');
        const isHourValid = isValidCronPart(cronParts.hour, 'hour');
        const isDayOfMonthValid = isValidCronPart(cronParts.dayOfMonth, 'dayOfMonth');
        const isMonthValid = isValidCronPart(cronParts.month, 'month');
        const isDayOfWeekValid = isValidCronPart(cronParts.dayOfWeek, 'dayOfWeek');
        const isValid = isMinuteValid && isHourValid && isDayOfMonthValid && isMonthValid && isDayOfWeekValid;
        // 设置错误信息
        if (!isMinuteValid) {
            setError('分钟字段格式不正确 (有效范围: 0-59)');
        }
        else if (!isHourValid) {
            setError('小时字段格式不正确 (有效范围: 0-23)');
        }
        else if (!isDayOfMonthValid) {
            setError('日期字段格式不正确 (有效范围: 1-31)');
        }
        else if (!isMonthValid) {
            setError('月份字段格式不正确 (有效范围: 1-12)');
        }
        else if (!isDayOfWeekValid) {
            setError('星期字段格式不正确 (有效范围: 0-7, 0和7都表示星期日)');
        }
        else {
            setError('');
        }
        // 如果表达式有效且与当前值不同，则更新
        if (isValid && cron !== value) {
            onChange(cron);
        }
    };
    return (_jsxs("div", { className: "space-y-4", children: [_jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-700 mb-1", children: "\u9884\u8BBE\u9009\u9879" }), _jsx("select", { value: preset, onChange: handlePresetChange, className: "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500", children: presets.map(p => (_jsx("option", { value: p.value, children: p.label }, p.value))) })] }), _jsxs("div", { className: "grid grid-cols-5 gap-2", children: [_jsxs("div", { children: [_jsx("label", { className: "block text-xs font-medium text-gray-700 mb-1", children: "\u5206\u949F" }), _jsx("input", { type: "text", value: cronParts.minute, onChange: (e) => handlePartChange('minute', e.target.value), onBlur: handlePartBlur, className: "w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500", placeholder: "*" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-xs font-medium text-gray-700 mb-1", children: "\u5C0F\u65F6" }), _jsx("input", { type: "text", value: cronParts.hour, onChange: (e) => handlePartChange('hour', e.target.value), onBlur: handlePartBlur, className: "w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500", placeholder: "*" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-xs font-medium text-gray-700 mb-1", children: "\u65E5" }), _jsx("input", { type: "text", value: cronParts.dayOfMonth, onChange: (e) => handlePartChange('dayOfMonth', e.target.value), onBlur: handlePartBlur, className: "w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500", placeholder: "*" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-xs font-medium text-gray-700 mb-1", children: "\u6708" }), _jsx("input", { type: "text", value: cronParts.month, onChange: (e) => handlePartChange('month', e.target.value), onBlur: handlePartBlur, className: "w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500", placeholder: "*" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-xs font-medium text-gray-700 mb-1", children: "\u661F\u671F" }), _jsx("input", { type: "text", value: cronParts.dayOfWeek, onChange: (e) => handlePartChange('dayOfWeek', e.target.value), onBlur: handlePartBlur, className: "w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500", placeholder: "*" })] })] }), error && (_jsx("div", { className: "text-sm text-red-600 mt-2", children: _jsx("p", { children: error }) })), _jsxs("div", { className: "text-sm text-gray-600", children: [_jsxs("p", { className: "font-medium", children: ["Cron\u8868\u8FBE\u5F0F: ", value] }), _jsx("p", { className: "mt-1", children: "\u683C\u5F0F: \u5206\u949F \u5C0F\u65F6 \u65E5 \u6708 \u661F\u671F" }), _jsx("p", { className: "mt-1", children: "\u793A\u4F8B: \"0 2 * * *\" \u8868\u793A\u6BCF\u5929\u51CC\u66682\u70B9\u6267\u884C" })] })] }));
};
export default CronGenerator;
