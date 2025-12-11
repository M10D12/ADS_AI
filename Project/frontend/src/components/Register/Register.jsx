import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import './Register.css';

const Register = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  // Estado dos campos do formulário
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    password: '',
    password_confirm: ''
  });

  // Estados de controle
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [generalSuccess, setGeneralSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);

  // Validações do frontend
  const validateForm = () => {
    const newErrors = {};

    // Validar nome
    if (!formData.nome.trim()) {
      newErrors.nome = 'O nome é obrigatório';
    } else if (formData.nome.trim().length < 2) {
      newErrors.nome = 'O nome deve ter pelo menos 2 caracteres';
    } else if (formData.nome.length > 512) {
      newErrors.nome = 'O nome não pode exceder 512 caracteres';
    }

    // Validar email
    if (!formData.email.trim()) {
      newErrors.email = 'O email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    } else if (formData.email.length > 512) {
      newErrors.email = 'O email não pode exceder 512 caracteres';
    }

    // Validar password
    if (!formData.password) {
      newErrors.password = 'A password é obrigatória';
    } else if (formData.password.length < 6) {
      newErrors.password = 'A password deve ter pelo menos 6 caracteres';
    } else if (formData.password.length > 512) {
      newErrors.password = 'A password não pode exceder 512 caracteres';
    }

    // Validar confirmação de password
    if (!formData.password_confirm) {
      newErrors.password_confirm = 'A confirmação de password é obrigatória';
    } else if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = 'As passwords não coincidem';
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
      // Chamar API de registo
      const result = await authService.register(formData);

      if (result.success) {
        setGeneralSuccess('Registo realizado com sucesso! Redirecionando...');
        setFormData({
          nome: '',
          email: '',
          password: '',
          password_confirm: ''
        });

        // Fazer login automaticamente após registo
        // Opcionalmente, pode-se fazer login com as credenciais fornecidas
        // Por enquanto, apenas redirecionar para login
        setTimeout(() => {
          navigate('/login', { 
            state: { email: formData.email, message: 'Registo realizado com sucesso! Faça login com suas credenciais.' }
          });
        }, 1500);
      } else {
        setGeneralError(result.error);
      }
    } catch (error) {
      setGeneralError('Erro inesperado ao registar. Tente novamente.');
      console.error('Erro ao registar:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-box">
        <h1 className="register-title">Criar Conta</h1>
        <p className="register-subtitle">Registe-se para começar a usar nossa plataforma</p>

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

        <form onSubmit={handleSubmit} className="register-form" noValidate>
          {/* Campo Nome */}
          <div className="form-group">
            <label htmlFor="nome" className="form-label">Nome Completo</label>
            <input
              type="text"
              id="nome"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              placeholder="João Silva"
              className={`form-input ${errors.nome ? 'input-error' : ''}`}
              disabled={isLoading}
              required
            />
            {errors.nome && (
              <span className="error-message">{errors.nome}</span>
            )}
          </div>

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
                placeholder="Mínimo 6 caracteres"
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

          {/* Campo Confirmação de Password */}
          <div className="form-group">
            <label htmlFor="password_confirm" className="form-label">Confirmar Password</label>
            <div className="password-input-wrapper">
              <input
                type={showPasswordConfirm ? 'text' : 'password'}
                id="password_confirm"
                name="password_confirm"
                value={formData.password_confirm}
                onChange={handleChange}
                placeholder="Repita a password"
                className={`form-input ${errors.password_confirm ? 'input-error' : ''}`}
                disabled={isLoading}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                disabled={isLoading}
                aria-label="Mostrar/Ocultar password"
              >
                {showPasswordConfirm ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.password_confirm && (
              <span className="error-message">{errors.password_confirm}</span>
            )}
          </div>

          {/* Botão de Registo */}
          <button
            type="submit"
            className="submit-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                A registar...
              </>
            ) : (
              'Registar'
            )}
          </button>
        </form>

        {/* Link para Login */}
        <div className="register-footer">
          <p>
            Já tem conta?{' '}
            <Link to="/login" className="link">
              Faça Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
