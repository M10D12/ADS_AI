import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

// ============================================================================
// COMPONENTE: MovieCard
// Componente reutilizável para apresentar um filme individual
// ============================================================================
const MovieCard = ({ movie, onViewDetails }) => {
  const posterUrl = movie.poster_url || `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
  const rating = movie.vote_average || 0;
  const genres = movie.genre_ids ? movie.genre_ids.join(', ') : 'N/A';

  return (
    <div className="movie-card">
      <div className="movie-card-poster">
        <img
          src={posterUrl}
          alt={movie.title}
          onError={(e) => {
            e.target.src = 'https://via.placeholder.com/500x750?text=Sem+Imagem';
          }}
        />
        <div className="movie-card-overlay">
          <button
            className="movie-card-button"
            onClick={() => onViewDetails(movie.movie_id || movie.id)}
          >
            Ver Detalhes
          </button>
        </div>
      </div>
      <div className="movie-card-info">
        <h3 className="movie-card-title">{movie.title}</h3>
        <div className="movie-card-meta">
          <span className="movie-rating">⭐ {rating.toFixed(1)}</span>
          <span className="movie-year">
            {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
          </span>
        </div>
        <p className="movie-card-genres">{genres}</p>
      </div>
    </div>
  );
};

// ============================================================================
// COMPONENTE: MoviesGrid
// Grid responsiva de filmes com estado de carregamento e vazio
// ============================================================================
const MoviesGrid = ({ movies, loading, error, title, onViewDetails, emptyMessage }) => {
  if (error) {
    return (
      <div className="section-error">
        <p className="error-icon">⚠️</p>
        <p className="error-message">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="section-loading">
        <div className="loader"></div>
        <p>Carregando {title.toLowerCase()}...</p>
      </div>
    );
  }

  if (!movies || movies.length === 0) {
    return (
      <div className="section-empty">
        <p className="empty-icon">🎬</p>
        <p className="empty-message">{emptyMessage || `Nenhum filme encontrado em ${title.toLowerCase()}`}</p>
      </div>
    );
  }

  return (
    <div className="movies-grid">
      {movies.map((movie) => (
        <MovieCard
          key={movie.movie_id || movie.id}
          movie={movie}
          onViewDetails={onViewDetails}
        />
      ))}
    </div>
  );
};

// ============================================================================
// COMPONENTE: HomePage
// Página principal com trending, catálogo, pesquisa e filtros
// ============================================================================
const HomePage = () => {
  const navigate = useNavigate();

  // ====================================================================
  // ESTADOS - React Hooks
  // ====================================================================

  // Trending Movies
  const [trendingMovies, setTrendingMovies] = useState([]);
  const [trendingLoading, setTrendingLoading] = useState(false);
  const [trendingError, setTrendingError] = useState(null);

  // Catálogo de Filmes
  const [catalogMovies, setCatalogMovies] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState(null);
  const [catalogPage, setCatalogPage] = useState(1);
  const [catalogTotalPages, setCatalogTotalPages] = useState(1);

  // Géneros
  const [genres, setGenres] = useState([]);
  const [genresLoading, setGenresLoading] = useState(false);
  const [genresError, setGenresError] = useState(null);

  // Filtros e Pesquisa
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // UI State
  const [view, setView] = useState('catalog'); // 'catalog', 'search', 'trending'

  // ====================================================================
  // FUNÇÕES DE API
  // ====================================================================

  /**
   * Função para fetch com tratamento de erros
   */
  const fetchAPI = useCallback(async (url, options = {}) => {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Erro de conexão: ${error.message}`);
    }
  }, []);

  /**
   * Carregar filmes em tendência (RF-11)
   * GET /api/movies/trending/?period=week
   */
  const loadTrendingMovies = useCallback(async () => {
    setTrendingLoading(true);
    setTrendingError(null);
    try {
      const data = await fetchAPI('/api/movies/trending/?period=week');
      setTrendingMovies(data.results || []);
    } catch (error) {
      setTrendingError('Não foi possível carregar filmes em tendência. Tente novamente.');
      console.error('Erro ao carregar trending:', error);
    } finally {
      setTrendingLoading(false);
    }
  }, [fetchAPI]);

  /**
   * Carregar catálogo de filmes (RF-04)
   * GET /api/movies/catalogue/?page=X&title=Y&genre_name=Z
   */
  const loadCatalog = useCallback(async (page = 1, title = '', genreName = '') => {
    setCatalogLoading(true);
    setCatalogError(null);
    try {
      let url = `/api/movies/catalogue/?page=${page}`;

      if (title.trim()) {
        url += `&title=${encodeURIComponent(title)}`;
      }

      if (genreName) {
        url += `&genre_name=${encodeURIComponent(genreName)}`;
      }

      const data = await fetchAPI(url);
      setCatalogMovies(data.results || []);
      setCatalogTotalPages(Math.ceil((data.count || 0) / 20)); // Assumindo 20 por página
    } catch (error) {
      setCatalogError('Não foi possível carregar o catálogo. Tente novamente.');
      console.error('Erro ao carregar catálogo:', error);
    } finally {
      setCatalogLoading(false);
    }
  }, [fetchAPI]);

  /**
   * Carregar géneros (RF-03)
   * GET /api/movies/genres/
   */
  const loadGenres = useCallback(async () => {
    setGenresLoading(true);
    setGenresError(null);
    try {
      const data = await fetchAPI('/api/movies/genres/');
      const genresList = data.genres || [];
      setGenres(genresList);
    } catch (error) {
      setGenresError('Não foi possível carregar géneros.');
      console.error('Erro ao carregar géneros:', error);
    } finally {
      setGenresLoading(false);
    }
  }, [fetchAPI]);

  /**
   * Pesquisar filmes por título (US04)
   * GET /api/movies/search/?query=X
   */
  const searchMovies = useCallback(async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      setView('catalog');
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setHasSearched(true);
    try {
      const data = await fetchAPI(`/api/movies/search/?query=${encodeURIComponent(query)}`);
      setSearchResults(data.results || []);
      setView('search');
    } catch (error) {
      setSearchError('Não foi possível pesquisar. Tente novamente.');
      setSearchResults([]);
      console.error('Erro ao pesquisar:', error);
    } finally {
      setSearchLoading(false);
    }
  }, [fetchAPI]);

  /**
   * Filtrar filmes por género (US05)
   */
  const filterByGenre = useCallback(
    async (genreName) => {
      setSelectedGenre(genreName);
      setCatalogPage(1);
      await loadCatalog(1, searchQuery, genreName);
    },
    [searchQuery, loadCatalog]
  );

  // ====================================================================
  // EFEITOS - useEffect
  // ====================================================================

  /**
   * Efeito: Carregar dados iniciais ao montar componente
   */
  useEffect(() => {
    loadTrendingMovies();
    loadCatalog();
    loadGenres();
  }, [loadTrendingMovies, loadCatalog, loadGenres]);

  /**
   * Efeito: Recarregar catálogo quando página muda
   */
  useEffect(() => {
    if (view === 'catalog' && !hasSearched) {
      loadCatalog(catalogPage, searchQuery, selectedGenre);
    }
  }, [catalogPage]);

  // ====================================================================
  // MANIPULADORES DE EVENTOS
  // ====================================================================

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);

    // Limpar search se campo vazio
    if (!value.trim()) {
      setHasSearched(false);
      setView('catalog');
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    searchMovies(searchQuery);
  };

  const handleViewDetails = (movieId) => {
    navigate(`/movie/${movieId}`);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedGenre('');
    setHasSearched(false);
    setView('catalog');
    loadCatalog(1, '', '');
  };

  const handleNextPage = () => {
    if (catalogPage < catalogTotalPages) {
      setCatalogPage(catalogPage + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePreviousPage = () => {
    if (catalogPage > 1) {
      setCatalogPage(catalogPage - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // ====================================================================
  // RENDERIZAÇÃO
  // ====================================================================

  return (
    <div className="home-page">
      {/* ================================================================ */}
      {/* HEADER COM BARRA DE PESQUISA E FILTROS */}
      {/* ================================================================ */}
      <header className="home-header">
        <div className="header-container">
          <h1 className="header-title">🎬 Plataforma de Filmes</h1>
          <p className="header-subtitle">Descubra, pesquise e explore o melhor do cinema</p>

          {/* Barra de Pesquisa */}
          <form className="search-form" onSubmit={handleSearchSubmit}>
            <div className="search-input-wrapper">
              <input
                type="text"
                className="search-input"
                placeholder="🔍 Pesquisar por título..."
                value={searchQuery}
                onChange={handleSearchChange}
              />
              <button type="submit" className="search-button">
                Pesquisar
              </button>
            </div>
          </form>

          {/* Filtro por Género */}
          <div className="filters-container">
            <div className="genre-filter">
              <label htmlFor="genre-select">Filtrar por Género:</label>
              <select
                id="genre-select"
                className="genre-select"
                value={selectedGenre}
                onChange={(e) => filterByGenre(e.target.value)}
                disabled={genresLoading}
              >
                <option value="">Todos os Géneros</option>
                {genres.map((genre) => (
                  <option key={genre.nome} value={genre.nome}>
                    {genre.nome}
                  </option>
                ))}
              </select>
            </div>

            {(searchQuery || selectedGenre) && (
              <button className="clear-filters-button" onClick={handleClearFilters}>
                ✕ Limpar Filtros
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ================================================================ */}
      {/* SEÇÃO DE FILMES EM TENDÊNCIA (RF-11) */}
      {/* ================================================================ */}
      {!hasSearched && view === 'catalog' && (
        <section className="home-section trending-section">
          <div className="section-container">
            <h2 className="section-title">🔥 Filmes em Tendência</h2>
            <MoviesGrid
              movies={trendingMovies.slice(0, 10)} // Mostrar apenas top 10
              loading={trendingLoading}
              error={trendingError}
              title="Trending"
              onViewDetails={handleViewDetails}
              emptyMessage="Nenhum filme em tendência disponível no momento"
            />
          </div>
        </section>
      )}

      {/* ================================================================ */}
      {/* SEÇÃO DE RESULTADOS DE PESQUISA */}
      {/* ================================================================ */}
      {hasSearched && view === 'search' && (
        <section className="home-section search-results-section">
          <div className="section-container">
            <h2 className="section-title">
              Resultados de Pesquisa: "{searchQuery}"
            </h2>
            <MoviesGrid
              movies={searchResults}
              loading={searchLoading}
              error={searchError}
              title="Resultados de Pesquisa"
              onViewDetails={handleViewDetails}
              emptyMessage={`Nenhum filme encontrado para "${searchQuery}"`}
            />
          </div>
        </section>
      )}

      {/* ================================================================ */}
      {/* SEÇÃO DE CATÁLOGO COMPLETO (RF-04) */}
      {/* ================================================================ */}
      {(!hasSearched || view === 'catalog') && (
        <section className="home-section catalog-section">
          <div className="section-container">
            <h2 className="section-title">
              {selectedGenre ? `🎞️ ${selectedGenre}` : '📚 Catálogo Completo'}
            </h2>
            <MoviesGrid
              movies={catalogMovies}
              loading={catalogLoading}
              error={catalogError}
              title="Catálogo"
              onViewDetails={handleViewDetails}
              emptyMessage={
                selectedGenre
                  ? `Nenhum filme encontrado em ${selectedGenre}`
                  : 'Nenhum filme disponível no catálogo'
              }
            />

            {/* Paginação */}
            {!catalogLoading && catalogMovies.length > 0 && (
              <div className="pagination-container">
                <button
                  className="pagination-button"
                  onClick={handlePreviousPage}
                  disabled={catalogPage === 1}
                >
                  ← Anterior
                </button>

                <span className="pagination-info">
                  Página {catalogPage} de {catalogTotalPages}
                </span>

                <button
                  className="pagination-button"
                  onClick={handleNextPage}
                  disabled={catalogPage === catalogTotalPages}
                >
                  Próxima →
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ================================================================ */}
      {/* FOOTER */}
      {/* ================================================================ */}
      <footer className="home-footer">
        <p>© 2024 Plataforma de Filmes. Todos os direitos reservados.</p>
        <p>Dados fornecidos por TMDB API</p>
      </footer>
    </div>
  );
};

export default HomePage;
