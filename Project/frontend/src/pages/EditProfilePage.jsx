import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './EditProfilePage.css';

// ============================================================================
// COMPONENTE: EditProfilePage
// Página para editar o perfil do utilizador
// ============================================================================
export default function EditProfilePage() {
  const navigate = useNavigate();
  const { user, token, updateUser, isAuthenticated, isLoading } = useAuth();

  // ====================================================================
  // ESTADOS
  // ====================================================================

  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [errors, setErrors] = useState({});
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // ====================================================================
  // EFEITOS
  // ====================================================================

  // Verificar autenticação e carregar dados do utilizador
  useEffect(() => {
    // Aguardar carregamento do auth
    if (isLoading) {
      return;
    }

    // Se não autenticado, redirecionar para login
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // Carregar dados do utilizador no formulário
    if (user) {
      setFormData(prev => ({
        ...prev,
        nome: user.nome || '',
        email: user.email || ''
      }));
    }
  }, [isAuthenticated, isLoading, user, navigate]);

  // ====================================================================
  // HANDLERS
  // ====================================================================

  /**
   * Handle input changes
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Limpar erro do campo ao digitar
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Limpar mensagem ao editar
    if (message.text) {
      setMessage({ type: '', text: '' });
    }
  };

  /**
   * Toggle password visibility
   */
  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  /**
   * Validar formulário
   */
  const validateForm = () => {
    const newErrors = {};

    // Validar nome
    if (!formData.nome.trim()) {
      newErrors.nome = 'O nome é obrigatório';
    } else if (formData.nome.trim().length < 2) {
      newErrors.nome = 'O nome deve ter pelo menos 2 caracteres';
    }

    // Validar email
    if (!formData.email.trim()) {
      newErrors.email = 'O email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    // Se está a alterar password, validar campos de password
    if (formData.newPassword || formData.confirmPassword || formData.currentPassword) {
      if (!formData.currentPassword) {
        newErrors.currentPassword = 'Digite a password atual para alterá-la';
      }

      if (!formData.newPassword) {
        newErrors.newPassword = 'Digite a nova password';
      } else if (formData.newPassword.length < 6) {
        newErrors.newPassword = 'A password deve ter pelo menos 6 caracteres';
      }

      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Confirme a nova password';
      } else if (formData.newPassword !== formData.confirmPassword) {
        newErrors.confirmPassword = 'As passwords não coincidem';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submit
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validar formulário
    if (!validateForm()) {
      setMessage({
        type: 'error',
        text: 'Por favor, corrija os erros no formulário'
      });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // Preparar dados para envio
      const updateData = {
        nome: formData.nome.trim(),
        email: formData.email.trim()
      };

      // Adicionar campos de password se fornecidos
      if (formData.currentPassword && formData.newPassword) {
        updateData.current_password = formData.currentPassword;
        updateData.new_password = formData.newPassword;
        updateData.confirm_password = formData.confirmPassword;
      }

      // Enviar requisição
      const response = await fetch('http://localhost:8000/api/auth/me/update/', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      const data = await response.json();

      if (response.ok) {
        // Atualizar contexto do utilizador
        if (data.user) {
          updateUser(data.user);
        }

        setMessage({
          type: 'success',
          text: data.message || 'Perfil atualizado com sucesso!'
        });

        // Limpar campos de password
        setFormData(prev => ({
          ...prev,
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }));

        // Redirecionar após 2 segundos
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        // Tratar erros específicos do servidor
        if (data.errors) {
          setErrors(data.errors);
        }

        setMessage({
          type: 'error',
          text: data.error || 'Erro ao atualizar perfil'
        });
      }
    } catch (error) {
      console.error('Erro ao atualizar perfil:', error);
      setMessage({
        type: 'error',
        text: 'Erro de conexão. Tente novamente.'
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Cancelar e voltar
   */
  const handleCancel = () => {
    navigate(-1);
  };

  // ====================================================================
  // RENDER
  // ====================================================================

  // Mostrar loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="edit-profile-page">
        <div className="edit-profile-container">
          <div className="edit-profile-header">
            <h1>A carregar...</h1>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="edit-profile-page">
      <div className="edit-profile-container">
        <div className="edit-profile-header">
          <h1>Editar Perfil</h1>
          <p>Atualize as suas informações pessoais</p>
        </div>

        {message.text && (
          <div className={`edit-profile-message ${message.type}`}>
            {message.type === 'success' ? '✓' : '⚠'} {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="edit-profile-form">
          {/* INFORMAÇÕES PESSOAIS */}
          <div className="form-section">
            <h2 className="section-title">Informações Pessoais</h2>

            {/* Nome */}
            <div className="form-group">
              <label htmlFor="nome">
                Nome Completo <span className="required">*</span>
              </label>
              <input
                type="text"
                id="nome"
                name="nome"
                value={formData.nome}
                onChange={handleChange}
                className={errors.nome ? 'error' : ''}
                placeholder="Digite o seu nome"
                disabled={loading}
              />
              {errors.nome && <span className="error-message">{errors.nome}</span>}
            </div>

            {/* Email */}
            <div className="form-group">
              <label htmlFor="email">
                Email <span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={errors.email ? 'error' : ''}
                placeholder="seu.email@exemplo.com"
                disabled={loading}
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>
          </div>

          {/* ALTERAR PASSWORD */}
          <div className="form-section">
            <h2 className="section-title">Alterar Password</h2>
            <p className="section-description">
              Deixe em branco se não deseja alterar a password
            </p>

            {/* Password Atual */}
            <div className="form-group">
              <label htmlFor="currentPassword">Password Atual</label>
              <div className="password-input-wrapper">
                <input
                  type={showPasswords.current ? 'text' : 'password'}
                  id="currentPassword"
                  name="currentPassword"
                  value={formData.currentPassword}
                  onChange={handleChange}
                  className={errors.currentPassword ? 'error' : ''}
                  placeholder="Digite a password atual"
                  disabled={loading}
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => togglePasswordVisibility('current')}
                  tabIndex="-1"
                >
                  {showPasswords.current ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              {errors.currentPassword && (
                <span className="error-message">{errors.currentPassword}</span>
              )}
            </div>

            {/* Nova Password */}
            <div className="form-group">
              <label htmlFor="newPassword">Nova Password</label>
              <div className="password-input-wrapper">
                <input
                  type={showPasswords.new ? 'text' : 'password'}
                  id="newPassword"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleChange}
                  className={errors.newPassword ? 'error' : ''}
                  placeholder="Digite a nova password"
                  disabled={loading}
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => togglePasswordVisibility('new')}
                  tabIndex="-1"
                >
                  {showPasswords.new ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              {errors.newPassword && (
                <span className="error-message">{errors.newPassword}</span>
              )}
            </div>

            {/* Confirmar Password */}
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirmar Nova Password</label>
              <div className="password-input-wrapper">
                <input
                  type={showPasswords.confirm ? 'text' : 'password'}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={errors.confirmPassword ? 'error' : ''}
                  placeholder="Confirme a nova password"
                  disabled={loading}
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => togglePasswordVisibility('confirm')}
                  tabIndex="-1"
                >
                  {showPasswords.confirm ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              {errors.confirmPassword && (
                <span className="error-message">{errors.confirmPassword}</span>
              )}
            </div>
          </div>

          {/* BOTÕES DE AÇÃO */}
          <div className="form-actions">
            <button
              type="button"
              onClick={handleCancel}
              className="btn-cancel"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-save"
              disabled={loading}
            >
              {loading ? 'A guardar...' : 'Guardar Alterações'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
