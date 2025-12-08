import React from 'react'
import './MovieCatalog.css'

const MovieCatalog = ({ movies, limit }) => {
  const visibleMovies = limit ? movies.slice(0, limit) : movies

  return (
    <div className="catalog-container">
      {visibleMovies.map((movie, index) => (
        <div key={index} className="movie-card">
          <div className="poster-placeholder"></div>
          {movie.title && <span>{movie.title}</span>}
        </div>
      ))}
    </div>
  )
}

export default MovieCatalog