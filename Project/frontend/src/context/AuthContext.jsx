import { createContext, useState, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [accessToken, setAccessToken] = useState(localStorage.getItem('accessToken'));
    const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'));
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem('user');
        return savedUser ? JSON.parse(savedUser) : null;
    })

    const saveAuth = async (access, refresh) => {
        setAccessToken(access);
        setRefreshToken(refresh);
        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        try {
            const response = await axios.get('/api/login/user_info/');
            setUser(response.data);
            localStorage.setItem('user', JSON.stringify(response.data));
        } catch (error) {
            console.error('Erro ao buscar user:', error);
        }
    }

    const clearAuth = () => {
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        delete axios.defaults.headers.common['Authorization'];
    }

    const value = {
        accessToken,
        refreshToken,
        user,
        saveAuth,
        clearAuth,
        isAuthenticated: !!accessToken
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    return context;
}
