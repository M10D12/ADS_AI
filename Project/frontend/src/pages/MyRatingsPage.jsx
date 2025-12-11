import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './MyRatingsPage.css';

// ============================================================================
// COMPONENTE: RatingControl
// Componente interactivo para modificar ratings
// ============================================================================
const RatingControl = ({ currentRating, movieId, onUpdate, isUpdating }) => {
  const [editMode, setEditMode] = useState(false);
  const [selectedRating, setSelectedRating] = useState(currentRating || 0);
  const [hoveredRating, setHoveredRating] = useState(0);

  const handleUpdate = async () => {
    if (selectedRating === currentRating) {
      setEditMode(false);
      return;
    }

    if (selectedRating === 0) {
      alert('Selecione uma classificação');
      return;
    }

    await onUpdate(movieId, selectedRating);
    setEditMode(false);
  };

  if (!editMode) {
    return (
      <div className="rating-control">
        <div className="rating-display">
          <span className="rating-label">Sua avaliação:</span>
          <span className="rating-value">⭐ {currentRating || 0}</span>
        </div>
        <button
          className="edit-rating-button"
          onClick={() => {
            setSelectedRating(currentRating);
            setEditMode(true);
          }}
          disabled={isUpdating}
        >
          {isUpdating ? 'Atualizando...' : 'Editar'}
        </button>
      </div>
    );
  }

  return (
    <div className="rating-control editing">
      <div className="stars-container">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
          <button
            key={star}
            className={`star-button ${
              (hoveredRating || selectedRating) >= star ? 'filled' : ''
            }`}
            onClick={() => setSelectedRating(star)}
            onMouseEnter={() => setHoveredRating(star)}
            onMouseLeave={() => setHoveredRating(0)}
            disabled={isUpdating}
            aria-label={`Avaliar com ${star} estrela${star !== 1 ? 's' : ''}`}
          >
            ⭐
          </button>
        ))}
      </div>

      {selectedRating > 0 && (
        <p className="selected-rating-text">
          Você está avaliando com <strong>{selectedRating}</strong> estrela{selectedRating !== 1 ? 's' : ''}
        </p>
      )}

      <div className="rating-control-buttons">
        <button
          className="btn btn-primary"
          onClick={handleUpdate}
          disabled={isUpdating || selectedRating === 0}
        >
          {isUpdating ? 'Salvando...' : 'Salvar'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => setEditMode(false)}
          disabled={isUpdating}
        >
          Cancelar
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENTE: RatingCard
// Card para cada filme avaliado
// ============================================================================
const RatingCard = ({ movie, onUpdate, onRemove, isUpdating, isRemoving }) => {
  const poster =
    movie.poster_url ||
    (movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null);
  const title = movie.title || movie.name || 'Sem título';
  const userRating = movie.user_rating || movie.rating || 0;
  const averageRating = movie.tmdb_rating || movie.vote_average || 0;
  const genres =
    (movie.genres && Array.isArray(movie.genres) ? movie.genres.join(', ') : null) ||
    (movie.genre_ids ? movie.genre_ids.join(', ') : '—');

  return (
    <div className="rating-card">
      {/* Poster */}
      <div className="rating-card-poster">
        <img
          src={poster || 'https://via.placeholder.com/300x450?text=Sem+Imagem'}
          alt={title}
          onError={(e) => {
            e.target.src = 'https://via.placeholder.com/300x450?text=Sem+Imagem';
          }}
        />
        <div className="rating-card-overlay">
          <button
            className="remove-rating-button"
            onClick={() => {
              if (window.confirm(`Tem a certeza que deseja remover a avaliação de "${title}"?`)) {
                onRemove(movie.id);
              }
            }}
            disabled={isRemoving}
            aria-label="Remover avaliação"
          >
            {isRemoving ? '...' : '✕'}
          </button>
        </div>
      </div>

      {/* Informações */}
      <div className="rating-card-content">
        <h3 className="rating-card-title">{title}</h3>

        {/* Géneros */}
        <p className="rating-card-genres">{genres}</p>

        {/* Ratings */}
        <div className="ratings-comparison">
          <div className="rating-item">
            <span className="rating-label">Sua avaliação</span>
            <span className="rating-value user-rating">⭐ {userRating}</span>
          </div>
          <div className="rating-item">
            <span className="rating-label">Média global</span>
            <span className="rating-value average-rating">⭐ {Number(averageRating).toFixed(1)}</span>
          </div>
        </div>

        {/* Rating Control */}
        <RatingControl
          currentRating={userRating}
          movieId={movie.id}
          onUpdate={onUpdate}
          isUpdating={isUpdating}
        />
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENTE: MyRatingsPage
// Página de avaliações do utilizador
// ============================================================================
export default function MyRatingsPage() {
  const navigate = useNavigate();

  // ====================================================================
  // ESTADOS
  // ====================================================================

  const [ratings, setRatings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [updatingIds, setUpdatingIds] = useState(new Set());
  const [removingIds, setRemovingIds] = useState(new Set());

  // ====================================================================
  // FUNÇÕES DE API
  // ====================================================================

  /**
   * Função helper para fetch com autenticação
   */
  const fetchWithAuth = useCallback(async (url, options = {}) => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      const err = new Error('Não autenticado');
      err.status = 401;
      throw err;
    }

    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    };

    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
      localStorage.removeItem('access_token');
      const err = new Error('Sessão expirada');
      err.status = 401;
      throw err;
    }

    if (!res.ok) {
      throw new Error(`Erro ${res.status}: ${res.statusText}`);
    }

    const text = await res.text();
    try {
      return text ? JSON.parse(text) : null;
    } catch {
      return text;
    }
  }, []);

  /**
   * Carregar avaliações do utilizador
   * GET /api/movies/my_rated/
   */
  const loadRatings = useCallback(async () => {
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      const data = await fetchWithAuth('/api/movies/my_rated/');
      const results = data?.results ?? data ?? [];
      setRatings(results);
    } catch (err) {
      if (err.status === 401) {
        navigate('/login');
        return;
      }
      console.error('Erro ao carregar avaliações:', err);
      setError('Erro ao carregar avaliações. Tente novamente mais tarde.');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, navigate]);

  /**
   * Atualizar avaliação
   * PUT /api/movies/update_rating/
   */
  const updateRating = useCallback(
    async (movieId, newRating) => {
      setUpdatingIds((prev) => new Set(prev).add(movieId));
      setError(null);

      try {
        const data = await fetchWithAuth('/api/movies/update_rating/', {
          method: 'PUT',
          body: JSON.stringify({
            movie_id: movieId,
            rating: newRating,
          }),
        });

        // Atualizar o estado local
        setRatings((prev) =>
          prev.map((movie) =>
            movie.id === movieId ? { ...movie, user_rating: newRating } : movie
          )
        );

        setSuccessMessage('Avaliação atualizada com sucesso!');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        console.error('Erro ao atualizar avaliação:', err);
        setError('Erro ao atualizar avaliação. Tente novamente.');
      } finally {
        setUpdatingIds((prev) => {
          const copy = new Set(prev);
          copy.delete(movieId);
          return copy;
        });
      }
    },
    [fetchWithAuth]
  );

  /**
   * Remover avaliação
   * DELETE /api/movies/delete_rating/?movie_id=<id>
   */
  const removeRating = useCallback(
    async (movieId) => {
      setRemovingIds((prev) => new Set(prev).add(movieId));
      setError(null);

      const previousRatings = ratings.slice();

      // Optimistic update
      setRatings((prev) => prev.filter((m) => m.id !== movieId));

      try {
        await fetchWithAuth(`/api/movies/delete_rating/?movie_id=${movieId}`, {
          method: 'DELETE',
        });

        setSuccessMessage('Avaliação removida com sucesso!');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        // Rollback em caso de erro
        setRatings(previousRatings);
        console.error('Erro ao remover avaliação:', err);
        setError('Erro ao remover avaliação. Tente novamente.');
      } finally {
        setRemovingIds((prev) => {
          const copy = new Set(prev);
          copy.delete(movieId);
          return copy;
        });
      }
    },
    [ratings, fetchWithAuth]
  );

  // ====================================================================
  // EFEITOS
  // ====================================================================

  /**
   * Efeito: Carregar avaliações ao montar componente
   */
  useEffect(() => {
    loadRatings();
  }, [loadRatings]);

  // ====================================================================
  // RENDERIZAÇÃO
  // ====================================================================

  return (
    <div className="my-ratings-page">
      {/* Header */}
      <header className="my-ratings-header">
        <div className="my-ratings-header-container">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Voltar
          </button>
          <h1 className="my-ratings-title">⭐ Minhas Avaliações</h1>
          <p className="my-ratings-subtitle">Filme que você avaliou</p>
        </div>
      </header>

      {/* Mensagens de Feedback */}
      {error && (
        <div className="feedback-container">
          <div className="feedback-error">
            <span>✕ {error}</span>
            <button onClick={() => setError(null)} className="feedback-close">
              ×
            </button>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="feedback-container">
          <div className="feedback-success">
            <span>✓ {successMessage}</span>
          </div>
        </div>
      )}

      {/* Conteúdo Principal */}
      <div className="my-ratings-content">
        {loading ? (
          /* Loading State */
          <div className="loading-container">
            <div className="loader"></div>
            <p>Carregando avaliações...</p>
          </div>
        ) : ratings.length === 0 ? (
          /* Empty State */
          <div className="empty-state">
            <p className="empty-icon">⭐</p>
            <h2>Nenhuma avaliação ainda</h2>
            <p>Avalie filmes para vê-los aqui e acompanhar sua avaliação.</p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              Explorar o Catálogo
            </button>
          </div>
        ) : (
          /* Ratings Grid */
          <>
            <div className="my-ratings-info">
              <p>Total de filmes avaliados: <strong>{ratings.length}</strong></p>
            </div>

            <div className="ratings-grid">
              {ratings.map((movie) => (
                <RatingCard
                  key={movie.id}
                  movie={movie}
                  onUpdate={updateRating}
                  onRemove={removeRating}
                  isUpdating={updatingIds.has(movie.id)}
                  isRemoving={removingIds.has(movie.id)}
                />
              ))}
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <footer className="my-ratings-footer">
        <p>© 2024 Plataforma de Filmes. Dados fornecidos por TMDB API</p>
      </footer>
    </div>
  );
}
