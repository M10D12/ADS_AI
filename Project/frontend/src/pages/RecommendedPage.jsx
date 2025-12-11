import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './RecommendedPage.css';

// ============================================================================
// COMPONENTE: MovieCard
// Card reutilizável para filmes recomendados
// ============================================================================
const MovieCard = ({ movie, onViewDetails }) => {
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
          src={poster || 'https://via.placeholder.com/300x450?text=Sem+Imagem'}
          alt={title}
          className="movie-card-image"
          onError={(e) => {
            e.target.src = 'https://via.placeholder.com/300x450?text=Sem+Imagem';
          }}
        />
        <div className="movie-card-overlay">
          <button
            className="movie-card-button"
            onClick={() => onViewDetails(movie.id)}
            aria-label={`Ver detalhes de ${title}`}
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
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENTE: RecommendedPage
// Página de recomendações personalizadas
// ============================================================================
export default function RecommendedPage() {
  const navigate = useNavigate();

  // ====================================================================
  // ESTADOS
  // ====================================================================

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [recommendationType, setRecommendationType] = useState('personalized');
  const [totalRatings, setTotalRatings] = useState(0);

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

    const response = await fetch(url, {
      headers,
      ...options,
    });

    if (response.status === 401) {
      localStorage.removeItem('access_token');
      const err = new Error('Sessão expirada');
      err.status = 401;
      throw err;
    }

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }

    const text = await response.text();
    try {
      return text ? JSON.parse(text) : null;
    } catch {
      return text;
    }
  }, []);

  /**
   * Carregar recomendações do utilizador
   * GET /api/movies/recommendations/
   */
  const loadRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      const data = await fetchWithAuth('/api/movies/recommendations/');
      
      const results = data?.recommendations ?? data?.results ?? [];
      setRecommendations(results);
      setRecommendationType(data?.recommendation_type || 'personalized');
      setTotalRatings(data?.num_user_ratings || 0);

      // Se não há recomendações
      if (results.length === 0) {
        setError(null); // Não é um erro, apenas sem dados
      }
    } catch (err) {
      if (err.status === 401) {
        navigate('/login');
        return;
      }
      console.error('Erro ao carregar recomendações:', err);
      setError('Erro ao carregar recomendações. Tente novamente mais tarde.');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, navigate]);

  // ====================================================================
  // EFEITOS
  // ====================================================================

  /**
   * Efeito: Carregar recomendações ao montar componente
   */
  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  // ====================================================================
  // MANIPULADORES DE EVENTOS
  // ====================================================================

  const handleViewDetails = (movieId) => {
    navigate(`/movie/${movieId}`);
  };

  const handleRetryLoad = () => {
    loadRecommendations();
  };

  // ====================================================================
  // RENDERIZAÇÃO
  // ====================================================================

  return (
    <div className="recommended-page">
      {/* Header */}
      <header className="recommended-header">
        <div className="recommended-header-container">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Voltar
          </button>
          <h1 className="recommended-title">🎯 Recomendações Personalizadas</h1>
          <p className="recommended-subtitle">
            Filmes sugeridos com base nas suas avaliações
          </p>
        </div>
      </header>

      {/* Mensagens de Feedback */}
      {error && (
        <div className="feedback-container">
          <div className="feedback-error">
            <span>⚠️ {error}</span>
            <button
              className="feedback-action"
              onClick={handleRetryLoad}
              aria-label="Tentar novamente"
            >
              Tentar Novamente
            </button>
          </div>
        </div>
      )}

      {/* Conteúdo Principal */}
      {loading ? (
        /* Loading State */
        <div className="recommended-page loading">
          <div className="loader"></div>
          <p>Carregando suas recomendações...</p>
        </div>
      ) : recommendations.length === 0 ? (
        /* Empty State */
        <div className="recommended-page empty">
          <div className="empty-state">
            <p className="empty-icon">🍿</p>
            <h2>
              {recommendationType === 'cold_start'
                ? 'Avalie alguns filmes para receber recomendações'
                : 'Nenhuma recomendação disponível'}
            </h2>
            <p>
              {recommendationType === 'cold_start'
                ? 'Comece a avaliar filmes com base no seu gosto e receberá sugestões personalizadas especialmente para você. Quanto mais filmes avaliar, melhores serão as recomendações!'
                : 'Tente atualizar sua lista de avaliações ou explore novos géneros.'}
            </p>
            <div className="empty-actions">
              <button
                className="btn btn-primary"
                onClick={() => navigate('/')}
              >
                Explorar o Catálogo
              </button>
              {totalRatings > 0 && totalRatings < 3 && (
                <button
                  className="btn btn-secondary"
                  onClick={() => navigate('/my-ratings')}
                >
                  Ver Minhas Avaliações
                </button>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Recommendations Grid */
        <>
          <div className="recommended-page">
            {/* Info Section */}
            <div className="recommended-info">
              <div className="info-item">
                <span className="info-label">Total de Recomendações:</span>
                <span className="info-value">{recommendations.length}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Tipo:</span>
                <span className="info-value">
                  {recommendationType === 'personalized'
                    ? '🎯 Personalizada'
                    : '📊 Popular'}
                </span>
              </div>
              {totalRatings > 0 && (
                <div className="info-item">
                  <span className="info-label">Suas Avaliações:</span>
                  <span className="info-value">{totalRatings}</span>
                </div>
              )}
            </div>

            {/* Recommendation Description */}
            <div className="recommended-description">
              {recommendationType === 'personalized' ? (
                <p>
                  🎯 Baseado em suas avaliações anteriores, selecionamos filmes que acreditamos
                  que irá gostar. Quanto mais avaliar, mais precisas serão as recomendações!
                </p>
              ) : (
                <p>
                  📊 Avalie mais filmes para receber recomendações mais personalizadas. Enquanto
                  isso, aqui estão os filmes mais populares que você ainda não avaliou.
                </p>
              )}
            </div>

            {/* Movies Grid */}
            <div className="movies-grid">
              {recommendations.map((movie) => (
                <MovieCard
                  key={movie.id}
                  movie={movie}
                  onViewDetails={handleViewDetails}
                />
              ))}
            </div>

            {/* Load More or Refresh */}
            <div className="recommended-actions">
              <button
                className="btn btn-secondary"
                onClick={handleRetryLoad}
              >
                🔄 Atualizar Recomendações
              </button>
            </div>
          </div>
        </>
      )}

      {/* Footer */}
      <footer className="recommended-footer">
        <p>
          © 2024 Plataforma de Filmes. Recomendações calculadas com base em IA.
        </p>
      </footer>
    </div>
  );
}
