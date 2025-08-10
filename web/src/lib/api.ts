// web/src/lib/api.ts
const API_BASE_URL = '/api';

const getHeaders = () => {
    const token = localStorage.getItem('token');
    const headers: { [key: string]: string } = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
};

export const login = async (password: string) => {
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

export const fetchFromApi = async (path: string, options: RequestInit = {}) => {
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
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'An unknown error occurred' }));
        throw new Error(errorData.message || 'API request failed');
    }

    return response.json();
};

export const getServers = () => fetchFromApi('/settings');

