import React, { useState } from 'react';
import './SearchFilters.css';

const SearchFilters = ({ onSearch }) => {
  const [filters, setFilters] = useState({
    texto: '',
    genero: '',
    rating: 0
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    const newFilters = {
      ...filters,
      [name]: value
    };
    setFilters(newFilters);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(filters);
  };

  return (
    <form className="filter-container" onSubmit={handleSubmit}>
      
      <div className="filter-group">
        <label htmlFor="texto">Pesquisar Título</label>
        <input
          type="text"
          id="texto"
          name="texto"
          className="custom-input"
          placeholder="Ex: Matrix, Aventura..."
          value={filters.texto}
          onChange={handleChange}
        />
      </div>

      <div className="filter-group">
        <label htmlFor="genero">Género</label>
        <select
          id="genero"
          name="genero"
          className="custom-select"
          value={filters.genero}
          onChange={handleChange}
        >
          <option value="">Todos</option>
          <option value="acao">Ação</option>
          <option value="comedia">Comédia</option>
          <option value="drama">Drama</option>
          <option value="sci-fi">Ficção Científica</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="rating">Rating Mínimo: {filters.rating}</label>
        <div className="range-wrapper">
          <input
            type="range"
            id="rating"
            name="rating"
            min="0"
            max="5"
            step="0.5"
            className="custom-range"
            value={filters.rating}
            onChange={handleChange}
          />
          <span className="rating-value">{filters.rating}</span>
        </div>
      </div>

      <button type="submit" className="search-btn">
        Filtrar
      </button>

    </form>
  );
};

export default SearchFilters;