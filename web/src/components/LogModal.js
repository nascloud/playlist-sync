import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { fetchFromApi } from '../lib/api';
const LogModal = ({ isOpen, onClose, sessionId }) => {
    const [logs, setLogs] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    useEffect(() => {
        if (isOpen && sessionId !== null) {
            const fetchLogs = async () => {
                setIsLoading(true);
                setError(null);
                try {
                    const data = await fetchFromApi(`/download/session/${sessionId}/logs`);
                    setLogs(data.logs || '暂无日志内容。');
                }
                catch (err) {
                    setError(err.message);
                }
                finally {
                    setIsLoading(false);
                }
            };
            fetchLogs();
        }
    }, [isOpen, sessionId]);
    return (_jsx(Transition, { appear: true, show: isOpen, as: Fragment, children: _jsxs(Dialog, { as: "div", className: "relative z-10", onClose: onClose, children: [_jsx(Transition.Child, { as: Fragment, enter: "ease-out duration-300", enterFrom: "opacity-0", enterTo: "opacity-100", leave: "ease-in duration-200", leaveFrom: "opacity-100", leaveTo: "opacity-0", children: _jsx("div", { className: "fixed inset-0 bg-black bg-opacity-25" }) }), _jsx("div", { className: "fixed inset-0 overflow-y-auto", children: _jsx("div", { className: "flex min-h-full items-center justify-center p-4 text-center", children: _jsx(Transition.Child, { as: Fragment, enter: "ease-out duration-300", enterFrom: "opacity-0 scale-95", enterTo: "opacity-100 scale-100", leave: "ease-in duration-200", leaveFrom: "opacity-100 scale-100", leaveTo: "opacity-0 scale-95", children: _jsxs(Dialog.Panel, { className: "w-full max-w-3xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all", children: [_jsxs(Dialog.Title, { as: "h3", className: "text-lg font-medium leading-6 text-gray-900", children: ["\u4E0B\u8F7D\u4F1A\u8BDD #", sessionId, " \u65E5\u5FD7"] }), _jsx("div", { className: "mt-4", children: _jsx("pre", { className: "whitespace-pre-wrap bg-gray-100 p-4 rounded-md text-sm text-gray-700 max-h-96 overflow-y-auto", children: isLoading ? '正在加载日志...' : error ? `错误: ${error}` : logs }) }), _jsx("div", { className: "mt-4", children: _jsx("button", { type: "button", className: "inline-flex justify-center rounded-md border border-transparent bg-blue-100 px-4 py-2 text-sm font-medium text-blue-900 hover:bg-blue-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2", onClick: onClose, children: "\u5173\u95ED" }) })] }) }) }) })] }) }));
};
export default LogModal;
