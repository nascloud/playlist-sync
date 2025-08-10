import {
    BrowserRouter as Router,
    Routes,
    Route,
    Navigate,
    useLocation,
    useNavigate,
    Outlet,
} from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import LogsPage from './pages/LogsPage';
import DownloadManagementPage from './pages/DownloadManagementPage';
import LoginPage from './pages/LoginPage';
import Header from './components/Header';
import { useState, useEffect } from 'react';
import { getServers } from './lib/api';
import { Toaster, toast } from 'sonner';

type Page = 'dashboard' | 'logs' | 'settings' | 'downloads';


const AppContent = () => {
    const [loading, setLoading] = useState(true);
    const [activePage, setActivePage] = useState<Page>('dashboard');
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        const page = location.pathname.substring(1) as Page;
        if (['dashboard', 'logs', 'settings', 'downloads'].includes(page)) {
            setActivePage(page);
        } else {
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
            } catch (error) {
                console.error("检查配置时出错:", error);
                toast.error("无法加载服务器配置，请稍后重试。");
            } finally {
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
                return <DashboardPage />;
            case 'logs':
                return <LogsPage />;
            case 'downloads':
                return <DownloadManagementPage />;
            case 'settings':
                return <SettingsPage onSetupComplete={handleSetupComplete} />;
            default:
                return <DashboardPage />;
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-slate-50">
                <p className="text-gray-500">正在加载...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 text-slate-800">
            <Header activePage={activePage} setActivePage={setActivePage} />
            <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                <PageContent />
            </main>
        </div>
    );
};

const PrivateRoute = () => {
    const token = localStorage.getItem('token');
    return token ? <Outlet /> : <Navigate to="/login" />;
};

function App() {
    return (
        <Router>
            <Toaster position="bottom-right" richColors expand={true} />
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route element={<PrivateRoute />}>
                    <Route path="/*" element={<AppContent />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
