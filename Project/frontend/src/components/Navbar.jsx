import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Navbar.css';

// ============================================================================
// COMPONENTE: Navbar
// Barra de navegação com autenticação
// ============================================================================
export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  // ====================================================================
  // ESTADOS
  // ====================================================================

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // ====================================================================
  // FUNÇÕES
  // ====================================================================

  /**
   * Verifica se o utilizador está autenticado
   */
  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
        return;
      }

      setIsAuthenticated(true);
      // Tentar carregar dados do utilizador
      const response = await fetch('/api/auth/me/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user || data);
      } else if (response.status === 401) {
        // Token inválido
        localStorage.removeItem('access_token');
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Erro ao verificar autenticação:', error);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fazer logout
   */
  const handleLogout = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch('/api/auth/logout/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('remembered_email');
      setIsAuthenticated(false);
      setUser(null);
      setShowDropdown(false);
      navigate('/login');
    }
  }, [navigate]);

  // ====================================================================
  // EFEITOS
  // ====================================================================

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Fechar dropdown ao navegar
  useEffect(() => {
    setShowDropdown(false);
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // ====================================================================
  // RENDERIZAÇÃO
  // ====================================================================

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo / Brand */}
        <div className="navbar-brand">
          <button
            className="navbar-logo"
            onClick={() => navigate('/')}
            aria-label="Ir para página inicial"
          >
            🎬 Plataforma de Filmes
          </button>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="navbar-mobile-toggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? '✕' : '☰'}
        </button>

        {/* Navigation Menu */}
        <ul className={`navbar-menu ${mobileMenuOpen ? 'active' : ''}`}>
          <li>
            <button
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
              onClick={() => navigate('/')}
            >
              🏠 Home
            </button>
          </li>

          {/* Links só visíveis se autenticado */}
          {isAuthenticated && (
            <>
              <li>
                <button
                  className={`nav-link ${location.pathname === '/favorites' ? 'active' : ''}`}
                  onClick={() => navigate('/favorites')}
                >
                  ❤️ Favoritos
                </button>
              </li>
              <li>
                <button
                  className={`nav-link ${location.pathname === '/my-ratings' ? 'active' : ''}`}
                  onClick={() => navigate('/my-ratings')}
                >
                  ⭐ Minhas Avaliações
                </button>
              </li>
              <li>
                <button
                  className={`nav-link ${location.pathname === '/recommended' ? 'active' : ''}`}
                  onClick={() => navigate('/recommended')}
                >
                  🎯 Recomendações
                </button>
              </li>
            </>
          )}
        </ul>

        {/* Right Side - Auth Buttons */}
        <div className="navbar-right">
          {!loading && !isAuthenticated ? (
            // Não autenticado
            <div className="auth-buttons">
              <button
                className="btn btn-secondary"
                onClick={() => navigate('/login')}
              >
                Entrar
              </button>
              <button
                className="btn btn-primary"
                onClick={() => navigate('/register')}
              >
                Registar
              </button>
            </div>
          ) : !loading && isAuthenticated ? (
            // Autenticado
            <div className="user-menu">
              <button
                className="user-button"
                onClick={() => setShowDropdown(!showDropdown)}
                aria-label="User menu"
              >
                <span className="user-avatar">👤</span>
                <span className="user-name">{user?.nome || user?.email || 'Utilizador'}</span>
                <span className={`dropdown-arrow ${showDropdown ? 'open' : ''}`}>▼</span>
              </button>

              {/* Dropdown Menu */}
              {showDropdown && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <p className="dropdown-email">{user?.email}</p>
                  </div>

                  <button
                    className="dropdown-item"
                    onClick={() => navigate('/profile')}
                  >
                    ⚙️ Meu Perfil
                  </button>

                  <button
                    className="dropdown-item"
                    onClick={() => navigate('/favorites')}
                  >
                    ❤️ Favoritos
                  </button>

                  <button
                    className="dropdown-item"
                    onClick={() => navigate('/my-ratings')}
                  >
                    ⭐ Minhas Avaliações
                  </button>

                  <button
                    className="dropdown-item"
                    onClick={() => navigate('/recommended')}
                  >
                    🎯 Recomendações
                  </button>

                  <div className="dropdown-divider"></div>

                  <button
                    className="dropdown-item logout"
                    onClick={handleLogout}
                  >
                    🚪 Sair
                  </button>
                </div>
              )}
            </div>
          ) : (
            // Loading
            <div className="loading-state">
              <div className="spinner"></div>
            </div>
          )}
        </div>
      </div>

      {/* Overlay para fechar dropdown ao clicar fora */}
      {showDropdown && (
        <div
          className="dropdown-overlay"
          onClick={() => setShowDropdown(false)}
        ></div>
      )}
    </nav>
  );
}
