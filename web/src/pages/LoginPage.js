import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// web/src/pages/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../lib/api';
import { toast } from 'sonner';
const LoginPage = () => {
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await login(password);
            localStorage.setItem('token', response.data.access_token);
            toast.success('登录成功');
            navigate('/');
        }
        catch (error) {
            toast.error('登录失败，密码错误');
            console.error('Login failed', error);
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx("div", { className: "flex items-center justify-center min-h-screen bg-gray-100", children: _jsxs("div", { className: "w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md", children: [_jsx("h1", { className: "text-2xl font-bold text-center", children: "\u767B\u5F55" }), _jsxs("form", { onSubmit: handleLogin, className: "space-y-6", children: [_jsxs("div", { children: [_jsx("label", { htmlFor: "password", className: "block text-sm font-medium text-gray-700", children: "\u5BC6\u7801" }), _jsx("input", { id: "password", type: "password", value: password, onChange: (e) => setPassword(e.target.value), required: true, className: "w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" })] }), _jsx("button", { type: "submit", disabled: loading, className: "w-full px-4 py-2 font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400", children: loading ? '登录中...' : '登录' })] })] }) }));
};
export default LoginPage;
