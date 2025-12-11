import React, { createContext, useState, useContext, useEffect } from 'react';

// Criar o contexto de autenticação
const AuthContext = createContext(null);

// Provider do contexto
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Verificar se há token salvo no localStorage ao carregar
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const savedToken = localStorage.getItem('access_token');
        if (savedToken) {
          setToken(savedToken);
          setIsAuthenticated(true);
          // Tentar recuperar dados do utilizador
          await fetchUserData(savedToken);
        } else {
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
        setIsLoading(false);
      }
    };
    checkAuth();
  }, []);

  // Função para buscar dados do utilizador
  const fetchUserData = async (authToken) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/me/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        // Token inválido, limpar
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setToken(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Erro ao buscar dados do utilizador:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Login
  const login = (userData, accessToken, refreshToken) => {
    setUser(userData);
    setToken(accessToken);
    setIsAuthenticated(true);
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  };

  // Logout
  const logout = () => {
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  // Atualizar dados do utilizador
  const updateUser = (userData) => {
    setUser(userData);
  };

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    updateUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook para usar o contexto
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};
