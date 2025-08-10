import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, List, Settings, Music, DownloadCloud, LogOut } from 'lucide-react';

type Page = 'dashboard' | 'logs' | 'settings' | 'downloads';

interface HeaderProps {
    activePage: Page;
    setActivePage: (page: Page) => void;
}

const navItems = [
    { id: 'dashboard', label: '仪表板', icon: LayoutDashboard, path: '/dashboard' },
    { id: 'downloads', label: '下载', icon: DownloadCloud, path: '/downloads' },
    { id: 'logs', label: '日志', icon: List, path: '/logs' },
    { id: 'settings', label: '设置', icon: Settings, path: '/settings' },
] as const;

const Header: React.FC<HeaderProps> = ({ activePage, setActivePage }) => {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };
    
    const handleNavigation = (path: string, pageId: Page) => {
        setActivePage(pageId);
        navigate(path);
    };

    return (
        <nav className="bg-white/70 backdrop-blur-lg shadow-sm sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <div className="flex-shrink-0 flex items-center gap-2">
                            <Music className="h-8 w-8 text-blue-600" />
                            <span className="text-xl font-bold text-gray-800">Plex Sync</span>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2 sm:space-x-4">
                        {navItems.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => handleNavigation(item.path, item.id)}
                                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                    activePage === item.id
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                                }`}
                            >
                                <item.icon className="h-5 w-5" aria-hidden="true" />
                                <span className="hidden sm:inline ml-2">{item.label}</span>
                            </button>
                        ))}
                        <button
                            onClick={handleLogout}
                            className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
                        >
                            <LogOut className="h-5 w-5" aria-hidden="true" />
                            <span className="hidden sm:inline ml-2">登出</span>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Header;
