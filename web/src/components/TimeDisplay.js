import { jsx as _jsx } from "react/jsx-runtime";
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
export const TimeDisplay = ({ timeString }) => {
    if (!timeString) {
        return _jsx("span", { className: "font-semibold text-gray-500", children: "\u4ECE\u672A" });
    }
    try {
        const date = new Date(timeString);
        const absoluteTime = format(date, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
        const relativeTime = formatDistanceToNow(date, { addSuffix: true, locale: zhCN });
        return _jsx("span", { className: "font-semibold text-gray-800", title: absoluteTime, children: relativeTime });
    }
    catch (e) {
        return _jsx("span", { className: "font-semibold text-red-500", children: "\u65E5\u671F\u65E0\u6548" });
    }
};
export default TimeDisplay;
