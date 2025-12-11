import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './FavoritesPage.css';

// ============================================================================
// COMPONENTE: MovieCard
// Card reutilizável para filmes
// ============================================================================
const MovieCard = ({ movie, onViewDetails, extraActions }) => {
  const poster =
    movie.poster_url ||
    (movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : null);
  const title = movie.title || movie.name || 'Sem título';
  const rating = movie.vote_average ?? movie.tmdb_rating ?? movie.rating ?? 0;
  const genres =
    (movie.genres && Array.isArray(movie.genres) ? movie.genres.join(', ') : null) ||
    (movie.genre_ids ? movie.genre_ids.join(', ') : '—');

  return (
    <div className="movie-card">
      <div className="movie-card-poster">
        <img
          src={poster || 'https://via.placeholder.com/500x750?text=Sem+Imagem'}
          alt={title}
          onError={(e) => {
            e.target.src = 'https://via.placeholder.com/500x750?text=Sem+Imagem';
          }}
        />
        <div className="movie-card-overlay">
          <button
            className="movie-card-button"
            onClick={() => onViewDetails(movie.movie_id ?? movie.id)}
          >
            Ver Detalhes
          </button>
        </div>
      </div>

      <div className="movie-card-info">
        <h3 className="movie-card-title">{title}</h3>
        <div className="movie-card-meta">
          <span className="movie-rating">⭐ {Number(rating).toFixed(1)}</span>
        </div>
        <p className="movie-card-genres">{genres}</p>

        <div className="movie-card-actions">{extraActions}</div>
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENTE: FavoritesPage
// Página de filmes favoritos
// ============================================================================
export default function FavoritesPage() {
  const navigate = useNavigate();

  // ====================================================================
  // ESTADOS
  // ====================================================================

  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingIds, setRemovingIds] = useState(new Set());
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

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

    // Alguns endpoints retornam vazio (204)
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : null;
    } catch {
      return text;
    }
  }, []);

  /**
   * Carregar lista de favoritos
   * GET /api/movies/favorites/
   */
  const loadFavorites = useCallback(async () => {
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      const data = await fetchWithAuth('/api/movies/favorites/');
      const results = data?.results ?? data ?? [];
      setFavorites(results);
    } catch (err) {
      if (err.status === 401) {
        navigate('/login');
        return;
      }
      console.error('Erro ao carregar favoritos:', err);
      setError('Erro ao carregar favoritos. Tente novamente mais tarde.');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, navigate]);

  /**
   * Remover um filme dos favoritos
   * DELETE /api/movies/favorites/remove/?movie_id=<id>
   */
  const removeFavorite = useCallback(
    async (movieId) => {
      // Confirmar remoção
      if (!window.confirm('Tem a certeza que deseja remover este filme dos favoritos?')) {
        return;
      }

      // Guardar estado anterior para rollback
      const previous = favorites.slice();

      // Optimistic update: remover imediatamente do estado
      setFavorites((prev) => prev.filter((m) => (m.movie_id ?? m.id) !== movieId));
      setRemovingIds((s) => new Set(s).add(movieId));
      setError(null);

      try {
        // Fazer DELETE request com query param
        const token = localStorage.getItem('access_token');
        const url = `/api/movies/favorites/remove/?movie_id=${encodeURIComponent(movieId)}`;

        const res = await fetch(url, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        });

        if (res.status === 401) {
          localStorage.removeItem('access_token');
          navigate('/login');
          return;
        }

        if (!res.ok) {
          // Rollback em caso de erro
          setFavorites(previous);
          const text = await res.text();
          console.error('Erro a remover favorito:', text || res.statusText);
          setError('Não foi possível remover o favorito. Tente novamente.');
          return;
        }

        // Sucesso!
        setSuccessMessage('Filme removido dos favoritos!');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        console.error('Erro na remoção:', err);
        setFavorites(previous);
        setError('Erro de rede. Tente novamente.');
      } finally {
        setRemovingIds((s) => {
          const copy = new Set(s);
          copy.delete(movieId);
          return copy;
        });
      }
    },
    [favorites, navigate]
  );

  // ====================================================================
  // EFEITOS
  // ====================================================================

  /**
   * Efeito: Carregar favoritos ao montar componente
   */
  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  // ====================================================================
  // MANIPULADORES DE EVENTOS
  // ====================================================================

  const handleViewDetails = (movieId) => {
    navigate(`/movie/${movieId}`);
  };

  // ====================================================================
  // RENDERIZAÇÃO
  // ====================================================================

  return (
    <div className="favorites-page">
      {/* Header */}
      <header className="favorites-header">
        <div className="favorites-header-container">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Voltar
          </button>
          <h1 className="favorites-title">❤️ Meus Favoritos</h1>
          <p className="favorites-subtitle">Os filmes que guardou para ver mais tarde</p>
        </div>
      </header>

      {/* Mensagens de feedback */}
      {error && (
        <div className="feedback-container">
          <div className="feedback-error">
            <span className="feedback-icon">⚠️</span>
            <span>{error}</span>
            <button className="feedback-close" onClick={() => setError(null)}>
              ✕
            </button>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="feedback-container">
          <div className="feedback-success">
            <span className="feedback-icon">✓</span>
            <span>{successMessage}</span>
          </div>
        </div>
      )}

      {/* Conteúdo Principal */}
      <main className="favorites-content">
        {loading ? (
          // Estado de Carregamento
          <div className="loading-state">
            <div className="loader"></div>
            <p>Carregando seus favoritos...</p>
          </div>
        ) : favorites.length === 0 ? (
          // Estado Vazio
          <div className="empty-state">
            <p className="empty-icon">🎬</p>
            <h2>Nenhum filme favorito</h2>
            <p>Ainda não tem filmes adicionados aos favoritos.</p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              Explorar o Catálogo
            </button>
          </div>
        ) : (
          // Grid de Filmes
          <>
            <div className="favorites-info">
              <p>Total de favoritos: <strong>{favorites.length}</strong></p>
            </div>

            <div className="movies-grid">
              {favorites.map((movie) => {
                const movieId = movie.movie_id ?? movie.id;
                const removing = removingIds.has(movieId);

                const extraActions = (
                  <button
                    className={`remove-button ${removing ? 'removing' : ''}`}
                    onClick={() => removeFavorite(movieId)}
                    disabled={removing}
                  >
                    {removing ? 'Removendo...' : '✕ Remover'}
                  </button>
                );

                return (
                  <MovieCard
                    key={movieId}
                    movie={movie}
                    onViewDetails={handleViewDetails}
                    extraActions={extraActions}
                  />
                );
              })}
            </div>

            {/* Botão para recarregar manualmente */}
            <div className="reload-container">
              <button className="btn btn-secondary" onClick={loadFavorites}>
                Recarregar Favoritos
              </button>
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="favorites-footer">
        <p>© 2024 Plataforma de Filmes. Dados fornecidos por TMDB API</p>
      </footer>
    </div>
  );
}
