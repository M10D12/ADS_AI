// authService.js - Centralizar chamadas à API de autenticação

const API_URL = 'http://localhost:8000/api/auth';

export const authService = {
  /**
   * Registar novo utilizador
   * @param {Object} userData - {nome, email, password, password_confirm}
   * @returns {Promise<Object>} - {user, token, refresh_token}
   */
  register: async (userData) => {
    try {
      const response = await fetch(`${API_URL}/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nome: userData.nome,
          email: userData.email,
          password: userData.password,
          password_confirm: userData.password_confirm
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro ao registar');
      }

      return {
        success: true,
        user: data.user,
        message: data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Erro de rede ao registar'
      };
    }
  },

  /**
   * Login utilizador
   * @param {Object} credentials - {email, password}
   * @returns {Promise<Object>} - {user, access_token, refresh_token}
   */
  login: async (credentials) => {
    try {
      const response = await fetch(`${API_URL}/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Email ou password inválidos');
      }

      return {
        success: true,
        user: data.user,
        access_token: data.access_token,
        refresh_token: data.refresh_token
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Erro de rede ao fazer login'
      };
    }
  },

  /**
   * Logout utilizador
   * @returns {Promise<Object>}
   */
  logout: async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro ao fazer logout');
      }

      // Limpar tokens locais
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      return {
        success: true,
        message: data.message
      };
    } catch (error) {
      // Mesmo com erro, limpar tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      return {
        success: false,
        error: error.message || 'Erro ao fazer logout'
      };
    }
  },

  /**
   * Obter dados do utilizador atual
   * @returns {Promise<Object>}
   */
  getCurrentUser: async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        return { success: false, error: 'Sem token de autenticação' };
      }

      const response = await fetch(`${API_URL}/me/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro ao buscar utilizador');
      }

      return {
        success: true,
        user: data.user
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Erro de rede'
      };
    }
  },

  /**
   * Atualizar perfil do utilizador
   * @param {Object} updateData - {nome, password}
   * @returns {Promise<Object>}
   */
  updateProfile: async (updateData) => {
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/me/update/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro ao atualizar perfil');
      }

      return {
        success: true,
        user: data.user,
        message: data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Erro ao atualizar perfil'
      };
    }
  }
};
