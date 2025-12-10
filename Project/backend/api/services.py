"""
Serviços para integração com APIs externas.

Requisito RF-12: Integração com TMDB API
Requisito RNF-01: Performance e Tempo de Resposta
"""

import requests
from django.conf import settings
from typing import Optional, Dict, Any


class TMDBService:
    """
    Serviço para comunicação com a TMDB API.
    
    Requisito RF-12: API de Terceiros (TMDB)
    Requisito RNF-01: Timeout de 10 segundos
    """
    
    BASE_URL = "https://api.themoviedb.org/3"
    TIMEOUT = 10  # segundos (RNF-01)
    
    @staticmethod
    def fetch_movies(
        page: int = 1,
        title: Optional[str] = None,
        genre_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Busca filmes da TMDB API com suporte a pesquisa e filtros.
        
        Requisito RF-04: Explorar Catálogo
        Requisito RF-05: Pesquisa e Filtro
        Requisito US04: Pesquisa por Título
        Requisito US05: Filtragem por Género
        
        Args:
            page: Número da página (default: 1)
            title: Termo de pesquisa para título (opcional)
            genre_id: ID do género para filtro (opcional)
        
        Returns:
            Dict contendo:
                - total_results: Total de resultados
                - total_pages: Total de páginas
                - page: Página atual
                - results: Lista de filmes
        
        Raises:
            requests.exceptions.RequestException: Erro na comunicação com TMDB
        """
        api_key = settings.TMDB_API_KEY
        
        # Validar API key
        if not api_key:
            raise ValueError("TMDB_API_KEY não configurada")
        
        # Validar página
        if page < 1:
            page = 1
        
        # Determinar endpoint baseado nos parâmetros
        if title:
            # US04: Pesquisa por título
            endpoint = f"{TMDBService.BASE_URL}/search/movie"
            params = {
                'api_key': api_key,
                'query': title,
                'page': page,
                'language': 'en-US'
            }
            
            # Adicionar filtro de género se especificado
            if genre_id:
                params['with_genres'] = genre_id
        
        elif genre_id:
            # US05: Filtragem por género (usar discover)
            endpoint = f"{TMDBService.BASE_URL}/discover/movie"
            params = {
                'api_key': api_key,
                'with_genres': genre_id,
                'page': page,
                'language': 'en-US',
                'sort_by': 'popularity.desc'
            }
        
        else:
            # RF-04: Catálogo principal (filmes populares)
            endpoint = f"{TMDBService.BASE_URL}/movie/popular"
            params = {
                'api_key': api_key,
                'page': page,
                'language': 'en-US'
            }
        
        # Fazer requisição com timeout (RNF-01)
        response = requests.get(
            endpoint,
            params=params,
            timeout=TMDBService.TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Normalizar resposta
        return {
            'total_results': data.get('total_results', 0),
            'total_pages': data.get('total_pages', 0),
            'page': data.get('page', page),
            'results': data.get('results', [])
        }
    
    @staticmethod
    def fetch_genres() -> Dict[str, Any]:
        """
        Busca lista de géneros da TMDB.
        
        Requisito RF-05: Pesquisa e Filtro
        Requisito US05: Filtragem por Género
        
        Returns:
            Dict contendo lista de géneros
        """
        api_key = settings.TMDB_API_KEY
        
        if not api_key:
            raise ValueError("TMDB_API_KEY não configurada")
        
        endpoint = f"{TMDBService.BASE_URL}/genre/movie/list"
        params = {
            'api_key': api_key,
            'language': 'en-US'
        }
        
        response = requests.get(
            endpoint,
            params=params,
            timeout=TMDBService.TIMEOUT
        )
        response.raise_for_status()
        
        return response.json()


# Instância única do serviço
tmdb_service = TMDBService()
