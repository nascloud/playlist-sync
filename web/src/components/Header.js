import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, List, Settings, Music, DownloadCloud, Search, LogOut } from 'lucide-react';
const navItems = [
    { id: 'dashboard', label: '仪表板', icon: LayoutDashboard, path: '/dashboard' },
    { id: 'search', label: '搜索下载', icon: Search, path: '/search' },
    { id: 'downloads', label: '下载管理', icon: DownloadCloud, path: '/downloads' },
    { id: 'logs', label: '日志', icon: List, path: '/logs' },
    { id: 'settings', label: '设置', icon: Settings, path: '/settings' },
];
const Header = ({ activePage, setActivePage }) => {
    const navigate = useNavigate();
    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };
    const handleNavigation = (path, pageId) => {
        setActivePage(pageId);
        navigate(path);
    };
    return (_jsx("nav", { className: "bg-white/70 backdrop-blur-lg shadow-sm sticky top-0 z-40", style: {
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)'
        }, children: _jsx("div", { className: "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8", children: _jsxs("div", { className: "flex justify-between h-16", children: [_jsx("div", { className: "flex items-center", children: _jsxs("div", { className: "flex-shrink-0 flex items-center gap-2", children: [_jsx(Music, { className: "h-8 w-8 text-blue-600" }), _jsx("span", { className: "text-xl font-bold text-gray-800", children: "Plex Sync" })] }) }), _jsxs("div", { className: "flex items-center space-x-2 sm:space-x-4", children: [navItems.map((item) => (_jsxs("button", { onClick: () => handleNavigation(item.path, item.id), className: `flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${activePage === item.id
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}`, children: [_jsx(item.icon, { className: "h-5 w-5", "aria-hidden": "true" }), _jsx("span", { className: "hidden sm:inline ml-2", children: item.label })] }, item.id))), _jsxs("button", { onClick: handleLogout, className: "flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors", children: [_jsx(LogOut, { className: "h-5 w-5", "aria-hidden": "true" }), _jsx("span", { className: "hidden sm:inline ml-2", children: "\u767B\u51FA" })] })] })] }) }) }));
};
export default Header;
