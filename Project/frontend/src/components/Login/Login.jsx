import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  // Se o utilizador já está autenticado, redirecionar
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Estado dos campos do formulário
  const [formData, setFormData] = useState({
    email: location.state?.email || '',
    password: ''
  });

  // Estados de controle
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [generalSuccess, setGeneralSuccess] = useState(location.state?.message || '');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Validações do frontend
  const validateForm = () => {
    const newErrors = {};

    // Validar email
    if (!formData.email.trim()) {
      newErrors.email = 'O email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    // Validar password
    if (!formData.password) {
      newErrors.password = 'A password é obrigatória';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Atualizar campos do formulário
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Limpar erro do campo quando o utilizador começa a digitar
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    // Limpar erro geral
    if (generalError) {
      setGeneralError('');
    }
  };

  // Enviar formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError('');
    setGeneralSuccess('');

    // Validar formulário
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Chamar API de login
      const result = await authService.login(formData);

      if (result.success) {
        setGeneralSuccess('Login realizado com sucesso! Redirecionando...');
        setFormData({
          email: '',
          password: ''
        });

        // Fazer login no contexto
        login(result.user, result.access_token, result.refresh_token);

        // Se "Remember Me" foi marcado, guardar email
        if (rememberMe) {
          localStorage.setItem('remembered_email', formData.email);
        } else {
          localStorage.removeItem('remembered_email');
        }

        // Redirecionar para página inicial após 1 segundo
        setTimeout(() => {
          navigate('/');
        }, 1000);
      } else {
        setGeneralError(result.error);
      }
    } catch (error) {
      setGeneralError('Erro inesperado ao fazer login. Tente novamente.');
      console.error('Erro ao fazer login:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Carregar email guardado (se existir)
  useEffect(() => {
    const rememberedEmail = localStorage.getItem('remembered_email');
    if (rememberedEmail) {
      setFormData(prev => ({
        ...prev,
        email: rememberedEmail
      }));
      setRememberMe(true);
    }
  }, []);

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="login-title">Bem-vindo</h1>
        <p className="login-subtitle">Faça login para acessar sua conta</p>

        {/* Mensagem de sucesso */}
        {generalSuccess && (
          <div className="alert alert-success">
            <span className="alert-icon">✓</span>
            {generalSuccess}
          </div>
        )}

        {/* Mensagem de erro geral */}
        {generalError && (
          <div className="alert alert-error">
            <span className="alert-icon">✕</span>
            {generalError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form" noValidate>
          {/* Campo Email */}
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="seu.email@exemplo.com"
              className={`form-input ${errors.email ? 'input-error' : ''}`}
              disabled={isLoading}
              required
            />
            {errors.email && (
              <span className="error-message">{errors.email}</span>
            )}
          </div>

          {/* Campo Password */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Insira sua password"
                className={`form-input ${errors.password ? 'input-error' : ''}`}
                disabled={isLoading}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
                aria-label="Mostrar/Ocultar password"
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.password && (
              <span className="error-message">{errors.password}</span>
            )}
          </div>

          {/* Remember Me e Forgot Password */}
          <div className="form-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading}
              />
              <span>Lembrar email</span>
            </label>
            <Link to="/forgot-password" className="forgot-password-link">
              Esqueceu a password?
            </Link>
          </div>

          {/* Botão de Login */}
          <button
            type="submit"
            className="submit-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                A entrar...
              </>
            ) : (
              'Entrar'
            )}
          </button>
        </form>

        {/* Link para Registo */}
        <div className="login-footer">
          <p>
            Não tem conta?{' '}
            <Link to="/register" className="link">
              Registre-se aqui
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
