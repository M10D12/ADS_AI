import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './MovieDetailsPage.css';

// ============================================================================
// COMPONENTE: RatingSection
// Seção de avaliação do filme
// ============================================================================
const RatingSection = ({
  userRating,
  movieId,
  onRatingSubmit,
  onRatingUpdate,
  onRatingDelete,
  isLoading,
  isAuthenticated,
  averageRating,
}) => {
  const [selectedRating, setSelectedRating] = useState(userRating || 0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [feedbackType, setFeedbackType] = useState(''); // 'success', 'error'

  const handleStarClick = (rating) => {
    setSelectedRating(rating);
  };

  const handleStarHover = (rating) => {
    setHoveredRating(rating);
  };

  const handleSubmitRating = async () => {
    if (!isAuthenticated) {
      setFeedbackMessage('Faça login para avaliar este filme');
      setFeedbackType('error');
      return;
    }

    if (selectedRating === 0) {
      setFeedbackMessage('Selecione uma classificação');
      setFeedbackType('error');
      return;
    }

    setIsSubmitting(true);
    setFeedbackMessage('');

    try {
      if (userRating) {
        // Atualizar avaliação existente
        await onRatingUpdate(movieId, selectedRating);
        setFeedbackMessage('Avaliação atualizada com sucesso!');
      } else {
        // Criar nova avaliação
        await onRatingSubmit(movieId, selectedRating);
        setFeedbackMessage('Avaliação enviada com sucesso!');
      }
      setFeedbackType('success');
      setTimeout(() => setFeedbackMessage(''), 3000);
    } catch (error) {
      setFeedbackMessage('Erro ao enviar avaliação');
      setFeedbackType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRating = async () => {
    if (!window.confirm('Tem a certeza que deseja remover a sua avaliação?')) {
      return;
    }

    setIsSubmitting(true);
    setFeedbackMessage('');

    try {
      await onRatingDelete(movieId);
      setSelectedRating(0);
      setFeedbackMessage('Avaliação removida com sucesso!');
      setFeedbackType('success');
      setTimeout(() => setFeedbackMessage(''), 3000);
    } catch (error) {
      setFeedbackMessage('Erro ao remover avaliação');
      setFeedbackType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="rating-section">
        <h3 className="rating-title">Avaliação</h3>
        <p className="rating-login-prompt">
          Faça <a href="/login">login</a> para avaliar este filme
        </p>
        {averageRating > 0 && (
          <div className="average-rating-display">
            <span className="rating-label">Classificação Média:</span>
            <span className="rating-value">⭐ {averageRating.toFixed(1)}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rating-section">
      <h3 className="rating-title">Sua Avaliação</h3>

      <div className="stars-container">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
          <button
            key={star}
            className={`star-button ${
              (hoveredRating || selectedRating) >= star ? 'filled' : ''
            }`}
            onClick={() => handleStarClick(star)}
            onMouseEnter={() => handleStarHover(star)}
            onMouseLeave={() => setHoveredRating(0)}
            disabled={isSubmitting}
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

      <div className="rating-buttons">
        <button
          className="btn btn-primary"
          onClick={handleSubmitRating}
          disabled={isSubmitting || selectedRating === 0}
        >
          {isSubmitting ? 'Enviando...' : userRating ? 'Atualizar Avaliação' : 'Enviar Avaliação'}
        </button>

        {userRating && (
          <button
            className="btn btn-secondary"
            onClick={handleDeleteRating}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Removendo...' : 'Remover Avaliação'}
          </button>
        )}
      </div>

      {feedbackMessage && (
        <div className={`feedback-message feedback-${feedbackType}`}>
          {feedbackType === 'success' ? '✓' : '✕'} {feedbackMessage}
        </div>
      )}

      {averageRating > 0 && (
        <div className="average-rating-display">
          <span className="rating-label">Classificação Média:</span>
          <span className="rating-value">⭐ {averageRating.toFixed(1)}</span>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// COMPONENTE: FavoriteButton
// Botão para adicionar/remover dos favoritos
// ============================================================================
const FavoriteButton = ({
  isFavorite,
  movieId,
  onToggleFavorite,
  isLoading,
  isAuthenticated,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState('');

  const handleToggleFavorite = async () => {
    if (!isAuthenticated) {
      setFeedbackMessage('Faça login para adicionar aos favoritos');
      setTimeout(() => setFeedbackMessage(''), 3000);
      return;
    }

    setIsSubmitting(true);
    try {
      await onToggleFavorite(movieId, isFavorite);
      setFeedbackMessage(
        isFavorite ? 'Removido dos favoritos' : 'Adicionado aos favoritos'
      );
      setTimeout(() => setFeedbackMessage(''), 2000);
    } catch (error) {
      setFeedbackMessage('Erro ao atualizar favoritos');
      setTimeout(() => setFeedbackMessage(''), 3000);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="favorite-button-container">
      <button
        className={`favorite-button ${isFavorite ? 'active' : ''}`}
        onClick={handleToggleFavorite}
        disabled={isSubmitting || isLoading || !isAuthenticated}
        aria-label={isFavorite ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
      >
        {isFavorite ? '❤️' : '🤍'} {isFavorite ? 'Remover' : 'Adicionar'} aos Favoritos
      </button>
      {feedbackMessage && <span className="favorite-feedback">{feedbackMessage}</span>}
    </div>
  );
};

// ============================================================================
// COMPONENTE: MovieDetailsPage
// Página completa de detalhes do filme
// ============================================================================
const MovieDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // ====================================================================
  // ESTADOS - React Hooks
  // ====================================================================

  const [movie, setMovie] = useState(null);
  const [movieLoading, setMovieLoading] = useState(true);
  const [movieError, setMovieError] = useState(null);

  const [userRating, setUserRating] = useState(null);
  const [isFavorite, setIsFavorite] = useState(false);

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loadingFavorites, setLoadingFavorites] = useState(false);

  // ====================================================================
  // FUNÇÕES DE API
  // ====================================================================

  const fetchAPI = useCallback(async (url, options = {}) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      };

      const response = await fetch(url, {
        headers,
        ...options,
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          setIsAuthenticated(false);
          throw new Error('Sessão expirada. Faça login novamente.');
        }
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Erro de conexão: ${error.message}`);
    }
  }, []);

  /**
   * Carregar detalhes do filme
   * GET /api/movies/<id>/
   */
  const loadMovieDetails = useCallback(async () => {
    setMovieLoading(true);
    setMovieError(null);
    try {
      const data = await fetchAPI(`/api/movies/${id}/`);
      setMovie(data);
    } catch (error) {
      setMovieError('Não foi possível carregar os detalhes do filme.');
      console.error('Erro ao carregar filme:', error);
    } finally {
      setMovieLoading(false);
    }
  }, [id, fetchAPI]);

  /**
   * Carregar favoritos do utilizador
   * GET /api/movies/favorites/
   */
  const loadUserFavorites = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsAuthenticated(false);
        return;
      }

      setIsAuthenticated(true);
      setLoadingFavorites(true);

      const data = await fetchAPI('/api/movies/favorites/');
      const favorites = data.results || [];
      const isFav = favorites.some(fav => fav.movie_id == id);
      setIsFavorite(isFav);

      // Carregar avaliação do utilizador
      const ratedMovies = await fetchAPI('/api/movies/my_rated/');
      const userRate = ratedMovies.results?.find(r => r.movie_id == id);
      if (userRate) {
        setUserRating(userRate.rating);
      }
    } catch (error) {
      console.error('Erro ao carregar favoritos:', error);
      setIsAuthenticated(false);
    } finally {
      setLoadingFavorites(false);
    }
  }, [id, fetchAPI]);

  /**
   * Avaliar filme
   * POST /api/movies/rate/
   */
  const submitRating = useCallback(
    async (movieId, rating) => {
      const data = await fetchAPI('/api/movies/rate/', {
        method: 'POST',
        body: JSON.stringify({
          movie_id: movieId,
          rating: rating,
        }),
      });
      setUserRating(rating);
      return data;
    },
    [fetchAPI]
  );

  /**
   * Atualizar avaliação
   * PUT /api/movies/update_rating/
   */
  const updateRating = useCallback(
    async (movieId, rating) => {
      const data = await fetchAPI('/api/movies/update_rating/', {
        method: 'PUT',
        body: JSON.stringify({
          movie_id: movieId,
          rating: rating,
        }),
      });
      setUserRating(rating);
      return data;
    },
    [fetchAPI]
  );

  /**
   * Remover avaliação
   * DELETE /api/movies/delete_rating/
   */
  const deleteRating = useCallback(
    async (movieId) => {
      await fetchAPI(`/api/movies/delete_rating/?movie_id=${movieId}`, {
        method: 'DELETE',
      });
      setUserRating(null);
    },
    [fetchAPI]
  );

  /**
   * Adicionar ou remover dos favoritos
   */
  const toggleFavorite = useCallback(
    async (movieId, currentlyFavorite) => {
      if (currentlyFavorite) {
        await fetchAPI('/api/movies/favorites/remove/', {
          method: 'DELETE',
          body: JSON.stringify({ movie_id: movieId }),
        });
      } else {
        await fetchAPI('/api/movies/favorites/add/', {
          method: 'POST',
          body: JSON.stringify({ movie_id: movieId }),
        });
      }
      setIsFavorite(!currentlyFavorite);
    },
    [fetchAPI]
  );

  // ====================================================================
  // EFEITOS - useEffect
  // ====================================================================

  /**
   * Efeito: Carregar detalhes do filme ao montar componente
   */
  useEffect(() => {
    loadMovieDetails();
  }, [id, loadMovieDetails]);

  /**
   * Efeito: Carregar favoritos e avaliações do utilizador
   */
  useEffect(() => {
    loadUserFavorites();
  }, [id, loadUserFavorites]);

  // ====================================================================
  // RENDERIZAÇÃO
  // ====================================================================

  // Estado de Carregamento
  if (movieLoading) {
    return (
      <div className="movie-details-page loading">
        <div className="loader"></div>
        <p>Carregando detalhes do filme...</p>
      </div>
    );
  }

  // Estado de Erro
  if (movieError || !movie) {
    return (
      <div className="movie-details-page error">
        <div className="error-container">
          <p className="error-icon">⚠️</p>
          <h2>Erro ao carregar filme</h2>
          <p>{movieError || 'Filme não encontrado'}</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            ← Voltar à Página Principal
          </button>
        </div>
      </div>
    );
  }

  const posterUrl = movie.poster_url || `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
  const backdropUrl = movie.backdrop_url || `https://image.tmdb.org/t/p/w1280${movie.backdrop_path}`;
  const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';
  const genresList = movie.genre_ids ? movie.genre_ids.join(', ') : 'N/A';

  return (
    <div className="movie-details-page">
      {/* ================================================================ */}
      {/* BACKDROP */}
      {/* ================================================================ */}
      <div className="movie-backdrop" style={{ backgroundImage: `url(${backdropUrl})` }}>
        <div className="backdrop-overlay"></div>
      </div>

      {/* ================================================================ */}
      {/* CONTEÚDO PRINCIPAL */}
      {/* ================================================================ */}
      <div className="movie-content">
        {/* Back Button */}
        <button className="back-button" onClick={() => navigate('/')}>
          ← Voltar
        </button>

        <div className="movie-main">
          {/* Poster */}
          <div className="movie-poster-container">
            <img
              src={posterUrl}
              alt={movie.title}
              className="movie-poster"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/500x750?text=Sem+Imagem';
              }}
            />
          </div>

          {/* Informações */}
          <div className="movie-info">
            <h1 className="movie-title">{movie.title}</h1>

            {/* Meta Info */}
            <div className="movie-meta">
              <span className="meta-item">
                📅 {releaseYear}
              </span>
              <span className="meta-item">
                ⭐ {movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}
              </span>
              <span className="meta-item">
                🎬 {genresList}
              </span>
            </div>

            {/* Sinopse */}
            <div className="movie-overview">
              <h3>Sinopse</h3>
              <p>
                {movie.overview || 'Nenhuma sinopse disponível para este filme.'}
              </p>
            </div>

            {/* Detalhes Adicionais */}
            <div className="movie-details">
              {movie.original_language && (
                <div className="detail-item">
                  <span className="detail-label">Idioma Original:</span>
                  <span className="detail-value">{movie.original_language.toUpperCase()}</span>
                </div>
              )}
              {movie.popularity && (
                <div className="detail-item">
                  <span className="detail-label">Popularidade:</span>
                  <span className="detail-value">{movie.popularity.toFixed(0)}</span>
                </div>
              )}
              {movie.vote_count && (
                <div className="detail-item">
                  <span className="detail-label">Número de Votos:</span>
                  <span className="detail-value">{movie.vote_count}</span>
                </div>
              )}
            </div>

            {/* Botão Favorito */}
            <FavoriteButton
              isFavorite={isFavorite}
              movieId={id}
              onToggleFavorite={toggleFavorite}
              isLoading={loadingFavorites}
              isAuthenticated={isAuthenticated}
            />
          </div>
        </div>

        {/* Seção de Avaliação */}
        <div className="movie-section">
          <RatingSection
            userRating={userRating}
            movieId={id}
            onRatingSubmit={submitRating}
            onRatingUpdate={updateRating}
            onRatingDelete={deleteRating}
            isLoading={movieLoading}
            isAuthenticated={isAuthenticated}
            averageRating={movie.vote_average}
          />
        </div>
      </div>

      {/* ================================================================ */}
      {/* FOOTER */}
      {/* ================================================================ */}
      <footer className="movie-footer">
        <p>© 2024 Plataforma de Filmes. Dados fornecidos por TMDB API</p>
      </footer>
    </div>
  );
};

export default MovieDetailsPage;
