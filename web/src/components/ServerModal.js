import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import Button from './Button';
import Input from './Input';
import Modal from './Modal';
const ServerModal = ({ isOpen, onClose, onSave, server }) => {
    const [formData, setFormData] = useState({
        name: server?.name || '',
        server_type: server?.server_type || 'plex',
        url: server?.url || '',
        token: '',
        ...(server && { id: server.id }),
    });
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        await onSave(formData);
    };
    return (_jsx(Modal, { isOpen: isOpen, title: server ? '编辑服务器' : '添加服务器', onClose: onClose, children: _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4", children: [_jsx(Input, { name: "name", label: "\u540D\u79F0", value: formData.name, onChange: handleChange, required: true }), _jsxs("div", { children: [_jsx("label", { htmlFor: "server_type", className: "block text-sm font-medium text-gray-700", children: "\u670D\u52A1\u5668\u7C7B\u578B" }), _jsxs("select", { name: "server_type", value: formData.server_type, onChange: handleChange, className: "mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md", children: [_jsx("option", { value: "plex", children: "Plex" }), _jsx("option", { value: "jellyfin", children: "Jellyfin" }), _jsx("option", { value: "emby", children: "Emby" })] })] }), _jsx(Input, { name: "url", label: "URL", value: formData.url, onChange: handleChange, placeholder: "http://192.168.1.100:32400", required: true }), _jsx(Input, { name: "token", label: "Token", type: "password", value: formData.token || '', onChange: handleChange, placeholder: server ? '留空则不修改' : '', required: !server }), _jsxs("div", { className: "flex justify-end gap-2 pt-4", children: [_jsx(Button, { type: "button", variant: "outline", onClick: onClose, children: "\u53D6\u6D88" }), _jsx(Button, { type: "submit", children: "\u4FDD\u5B58" })] })] }) }));
};
export default ServerModal;
