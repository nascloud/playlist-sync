// web/src/lib/api.ts
const API_BASE_URL = '/api';
const getHeaders = () => {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
};
export const login = async (password) => {
    const formData = new URLSearchParams();
    formData.append('username', 'user'); // 'username' can be fixed as it's not used for validation
    formData.append('password', password);
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
    });
    if (!response.ok) {
        throw new Error('Login failed');
    }
    return response.json();
};
export const fetchFromApi = async (path, options = {}) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            ...getHeaders(),
            ...options.headers,
        },
    });
    if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        // 尝试解析错误信息，如果失败则使用默认消息
        const errorText = await response.text().catch(() => 'Unauthorized');
        let errorMessage = 'Unauthorized';
        try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
        }
        catch {
            // 如果不是JSON格式，直接使用文本
            errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
    }
    if (!response.ok) {
        // 尝试解析错误信息，如果失败则使用默认消息
        const errorText = await response.text().catch(() => 'An unknown error occurred');
        let errorMessage = 'API request failed';
        try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
        }
        catch {
            // 如果不是JSON格式，直接使用文本
            errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
    }
    return response.json();
};
export const getServers = () => fetchFromApi('/settings');
