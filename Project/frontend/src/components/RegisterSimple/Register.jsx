import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../Register/Register.css';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    password: '',
    password_confirm: ''
  });

  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [generalSuccess, setGeneralSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.nome.trim()) {
      newErrors.nome = 'O nome é obrigatório';
    } else if (formData.nome.trim().length < 2) {
      newErrors.nome = 'O nome deve ter pelo menos 2 caracteres';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'O email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!formData.password) {
      newErrors.password = 'A password é obrigatória';
    } else if (formData.password.length < 6) {
      newErrors.password = 'A password deve ter pelo menos 6 caracteres';
    }

    if (!formData.password_confirm) {
      newErrors.password_confirm = 'A confirmação de password é obrigatória';
    } else if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = 'As passwords não coincidem';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    if (generalError) {
      setGeneralError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError('');
    setGeneralSuccess('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nome: formData.nome,
          email: formData.email,
          password: formData.password,
          password_confirm: formData.password_confirm
        })
      });

      const data = await response.json();

      if (response.ok) {
        setGeneralSuccess('Registo realizado com sucesso! Redirecionando...');
        setTimeout(() => {
          navigate('/login', { 
            state: { email: formData.email }
          });
        }, 1500);
      } else {
        setGeneralError(data.error || 'Erro ao registar');
      }
    } catch (error) {
      setGeneralError('Erro de conexão com o servidor');
      console.error('Erro:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-box">
        <h1 className="register-title">Criar Conta</h1>
        <p className="register-subtitle">Registe-se para começar</p>

        {generalSuccess && (
          <div className="alert alert-success">
            <span className="alert-icon">✓</span>
            {generalSuccess}
          </div>
        )}

        {generalError && (
          <div className="alert alert-error">
            <span className="alert-icon">✕</span>
            {generalError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="register-form" noValidate>
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
            {errors.nome && <span className="error-message">{errors.nome}</span>}
          </div>

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
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

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
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

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
              >
                {showPasswordConfirm ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.password_confirm && <span className="error-message">{errors.password_confirm}</span>}
          </div>

          <button type="submit" className="submit-button" disabled={isLoading}>
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
