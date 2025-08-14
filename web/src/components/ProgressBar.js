import { jsx as _jsx } from "react/jsx-runtime";
const ProgressBar = ({ value, max, className }) => {
    const percentage = max > 0 ? (value / max) * 100 : 0;
    return (_jsx("div", { className: `w-full bg-gray-200 rounded-full h-2 ${className}`, children: _jsx("div", { className: "bg-blue-600 h-2 rounded-full transition-all duration-500", style: { width: `${percentage}%` } }) }));
};
export default ProgressBar;
