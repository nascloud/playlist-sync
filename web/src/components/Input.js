import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { memo } from 'react';
const Input = ({ label, error, className = '', id, name, ...props }) => {
    const inputId = id || name;
    const baseClasses = 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2';
    const errorClasses = 'border-red-500 focus:ring-red-500';
    const defaultClasses = 'border-gray-300 focus:ring-blue-500';
    return (_jsxs("div", { className: "mb-4", children: [_jsx("label", { htmlFor: inputId, className: "block text-sm font-medium text-gray-700 mb-1", children: label }), _jsx("input", { id: inputId, name: name, className: `${baseClasses} ${error ? errorClasses : defaultClasses} ${className}`, ...props }), error && _jsx("p", { className: "mt-1 text-sm text-red-500", children: error })] }));
};
export default memo(Input);
