import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate, Outlet, } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import LogsPage from './pages/LogsPage';
import DownloadManagementPage from './pages/DownloadManagementPage';
import LoginPage from './pages/LoginPage';
import Header from './components/Header';
import { useState, useEffect } from 'react';
import { getServers } from './lib/api';
import { Toaster, toast } from 'sonner';
const AppContent = () => {
    const [loading, setLoading] = useState(true);
    const [activePage, setActivePage] = useState('dashboard');
    const location = useLocation();
    const navigate = useNavigate();
    useEffect(() => {
        const page = location.pathname.substring(1);
        if (['dashboard', 'logs', 'settings', 'downloads'].includes(page)) {
            setActivePage(page);
        }
        else {
            setActivePage('dashboard');
        }
    }, [location]);
    useEffect(() => {
        const checkConfiguration = async () => {
            try {
                const serverData = await getServers();
                if (!serverData.servers || serverData.servers.length === 0) {
                    toast.warning('您尚未配置 Plex 服务器。', {
                        description: '请前往设置页面完成配置以使用全部功能。',
                        action: {
                            label: '前往设置',
                            onClick: () => navigate('/settings'),
                        },
                        duration: Infinity, // 保持显示直到用户手动关闭
                        id: 'config-warning',
                    });
                }
            }
            catch (error) {
                console.error("检查配置时出错:", error);
                toast.error("无法加载服务器配置，请稍后重试。");
            }
            finally {
                setLoading(false);
            }
        };
        checkConfiguration();
    }, [navigate]);
    // 当用户导航到设置页面时，取消警告
    useEffect(() => {
        if (activePage === 'settings') {
            toast.dismiss('config-warning');
        }
    }, [activePage]);
    const handleSetupComplete = () => {
        setActivePage('dashboard');
        toast.success('设置已保存！');
    };
    // ... (其余代码保持不变)
    const PageContent = () => {
        switch (activePage) {
            case 'dashboard':
                return _jsx(DashboardPage, {});
            case 'logs':
                return _jsx(LogsPage, {});
            case 'downloads':
                return _jsx(DownloadManagementPage, {});
            case 'settings':
                return _jsx(SettingsPage, { onSetupComplete: handleSetupComplete });
            default:
                return _jsx(DashboardPage, {});
        }
    };
    if (loading) {
        return (_jsx("div", { className: "flex items-center justify-center min-h-screen bg-slate-50", children: _jsx("p", { className: "text-gray-500", children: "\u6B63\u5728\u52A0\u8F7D..." }) }));
    }
    return (_jsxs("div", { className: "min-h-screen bg-slate-50 text-slate-800", children: [_jsx(Header, { activePage: activePage, setActivePage: setActivePage }), _jsx("main", { className: "max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8", children: _jsx(PageContent, {}) })] }));
};
const PrivateRoute = () => {
    const token = localStorage.getItem('token');
    return token ? _jsx(Outlet, {}) : _jsx(Navigate, { to: "/login" });
};
function App() {
    return (_jsxs(Router, { children: [_jsx(Toaster, { position: "bottom-right", richColors: true, expand: true }), _jsxs(Routes, { children: [_jsx(Route, { path: "/login", element: _jsx(LoginPage, {}) }), _jsx(Route, { element: _jsx(PrivateRoute, {}), children: _jsx(Route, { path: "/*", element: _jsx(AppContent, {}) }) })] })] }));
}
export default App;
