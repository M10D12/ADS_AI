from functools import cache
import math
from django.shortcuts import render
from django.db import models
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from math import log
from django.db.models import Count, Avg
from .models import AtividadeUsuario, Filme, Genero, Usuario, HistoricoVisualizacao, Favorito
from .services import tmdb_service
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password,check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone



from .serializers import (
    UsuarioSerializer, FilmeSerializer, GeneroSerializer,
    AtividadeUsuarioSerializer, FavoriteSerializer, WatchLaterSerializer,
    ReviewSerializer, HistoryItemSerializer
)

# Create your views here.
# Aqui criamos as views (endpoints). Usamos o serializer correspondente a cada modelo que assim temos a informação formatada em JSON que o frontend aceita bem.



# ============================================================================
# AUTENTICAÇÃO E REGISTO - RF-01 (Registo) e RF-02 (Autenticação)
# ============================================================================

@api_view(['POST'])
def register(request):
    data = request.data
    
    # Validação 1: Campos obrigatórios
    required_fields = ['nome', 'email', 'password', 'password_confirm']
    for field in required_fields:
        if field not in data or not data[field]:
            return Response(
                {"error": f"Campo '{field}' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    password_confirm = data.get('password_confirm', '')
    
    # Validação 2: Comprimento do nome
    if len(nome) < 2:
        return Response(
            {"error": "Nome deve ter pelo menos 2 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(nome) > 512:
        return Response(
            {"error": "Nome não pode exceder 512 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validação 3: Formato de email
    if '@' not in email or '.' not in email:
        return Response(
            {"error": "Email inválido"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(email) > 512:
        return Response(
            {"error": "Email não pode exceder 512 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validação 4: Comprimento da password
    if len(password) < 6:
        return Response(
            {"error": "A password deve ter pelo menos 6 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(password) > 512:
        return Response(
            {"error": "A password não pode exceder 512 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validação 5: Confirmação de password
    if password != password_confirm:
        return Response(
            {"error": "As passwords não coincidem"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validação 6: Email único
    if Usuario.objects.filter(email=email).exists():
        return Response(
            {"error": "Este email já está registado no sistema"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Criar utilizador com password hasheada
        password_hash = make_password(password)
        
        usuario = Usuario.objects.create(
            nome=nome,
            email=email,
            password_hash=password_hash
        )
        
        return Response({
            "message": "Utilizador registado com sucesso",
            "user": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao registar utilizador", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def login(request):
   
    
    data = request.data
    
    # Validação 1: Campos obrigatórios
    if "email" not in data or not data.get("email"):
        return Response(
            {"error": "Email é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if "password" not in data or not data.get("password"):
        return Response(
            {"error": "Password é obrigatória"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    # Validação 2: Email vazio ou muito curto
    if not email or len(email) < 3:
        return Response(
            {"error": "Email ou password inválidos"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validação 3: Password vazia
    if not password or len(password) < 1:
        return Response(
            {"error": "Email ou password inválidos"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Buscar utilizador por email
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # NÃO revelar se o email existe (segurança contra enumeração de emails)
        return Response(
            {"error": "Email ou password inválidos"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Verificar password de forma segura
    if not check_password(password, usuario.password_hash):
        # NÃO revelar que a password está errada especificamente
        return Response(
            {"error": "Email ou password inválidos"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Gerar tokens JWT (requer rest_framework_simplejwt)
        refresh = RefreshToken.for_user(usuario)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        return Response({
            "message": "Login realizado com sucesso",
            "user": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email
            },
            "access_token": access_token,
            "refresh_token": refresh_token
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao gerar tokens de autenticação", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
 
    
    try:
        # Se rest_framework_simplejwt estiver configurado com blacklist
        # o token será automaticamente invalidado na próxima utilização
        # Por enquanto, apenas confirmamos o logout bem-sucedido
        
        user = request.user
        
        return Response({
            "message": "Logout realizado com sucesso",
            "user_id": user.id,
            "user_name": user.nome
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao fazer logout", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):

    
    user = request.user
    
    try:
        return Response({
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao obter dados do utilizador", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_me_update(request):

    
    user = request.user
    data = request.data
    
    try:
        updated_fields = {}
        
        # ====================================================================
        # Validação e Atualização do Nome
        # ====================================================================
        
        if "nome" in data:
            nome = data.get("nome", "").strip()
            
            # Validação: comprimento mínimo
            if len(nome) < 2:
                return Response(
                    {"error": "Nome deve ter pelo menos 2 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validação: comprimento máximo
            if len(nome) > 512:
                return Response(
                    {"error": "Nome não pode exceder 512 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.nome = nome
            updated_fields['nome'] = nome
        
        # ====================================================================
        # Validação e Atualização de Password (Segura)
        # ====================================================================
        
        if "password" in data or "password_confirm" in data:
            password = data.get("password", "")
            password_confirm = data.get("password_confirm", "")
            
            # Validação: campos obrigatórios quando um é fornecido
            if ("password" in data and "password_confirm" not in data) or \
               ("password_confirm" in data and "password" not in data):
                return Response(
                    {"error": "Deve fornecer password e password_confirm simultaneamente"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validação: não permitir password vazia
            if not password or not password_confirm:
                return Response(
                    {"error": "Password não pode ser vazia"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validação: comprimento mínimo
            if len(password) < 6:
                return Response(
                    {"error": "A password deve ter pelo menos 6 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validação: comprimento máximo
            if len(password) > 512:
                return Response(
                    {"error": "A password não pode exceder 512 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validação: concordância de passwords
            if password != password_confirm:
                return Response(
                    {"error": "As passwords não coincidem"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Aplicar hash seguro
            user.password_hash = make_password(password)
            updated_fields['password_changed'] = True
        
        # ====================================================================
        # Proteção: Email não pode ser alterado
        # ====================================================================
        
        if "email" in data:
            return Response(
                {"error": "Email não pode ser alterado. Contacte o suporte se necessário."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ====================================================================
        # Proteção: Campos protegidos não podem ser alterados
        # ====================================================================
        
        protected_fields = ['id', 'created_at', 'updated_at', 'password_hash', 'is_authenticated']
        for field in protected_fields:
            if field in data:
                return Response(
                    {"error": f"Campo '{field}' não pode ser alterado"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # ====================================================================
        # Se nenhum campo foi alterado, retornar erro
        # ====================================================================
        
        if not updated_fields:
            return Response(
                {"error": "Nenhum campo foi fornecido para atualização"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ====================================================================
        # Salvar alterações
        # ====================================================================
        
        user.save()
        
        return Response({
            "message": "Perfil atualizado com sucesso",
            "user": {
                "id": user.id,
                "nome": user.nome,
                "email": user.email,
                "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao atualizar perfil", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# Aliases para compatibilidade com URLs antigas
# ============================================================================

def UserInfo(request):
    """Alias para compatibilidade - redireciona para user_me"""
    return user_me(request)


def UpdateProfile(request):
    """Alias para compatibilidade - redireciona para user_me_update"""
    return user_me_update(request)



def tmdb_request(endpoint, params=None):
    base_url = "https://api.themoviedb.org/3"
    if params is None:
        params = {}
    params['api_key'] = settings.TMDB_API_KEY
    response = requests.get(f"{base_url}/{endpoint}", params=params)
    return response.json()  


@api_view(['GET'])
def search_movies(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return Response(
            {"error": "O parâmetro 'query' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validação: comprimento máximo da query
    if len(query) > 512:
        return Response(
            {"error": "Query não pode exceder 512 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obter página
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    if page < 1:
        page = 1
    
    # ====================================================================
    # Pesquisar na TMDB API
    # ====================================================================
    
    try:
        params = {
            'query': query,
            'page': page,
            'api_key': settings.TMDB_API_KEY
        }
        
        response = requests.get(
            'https://api.themoviedb.org/3/search/movie',
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # ====================================================================
        # Processar e cachear resultados
        # ====================================================================
        
        results = data.get('results', [])
        
        # Salvar filmes na base de dados (cache)
        for movie in results:
            tmdb_id = movie.get('id')
            if not tmdb_id:
                continue
            
            # Tentar descarregar poster
            poster_path = movie.get('poster_path')
            capa_bin = b""
            
            if poster_path:
                try:
                    img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    img_resp = requests.get(img_url, timeout=5)
                    if img_resp.status_code == 200:
                        capa_bin = img_resp.content
                except:
                    pass
            
            # Extrair ano de lançamento
            release_date = movie.get('release_date', '')
            ano_lancamento = None
            if release_date:
                try:
                    ano_lancamento = int(release_date.split('-')[0])
                except (ValueError, IndexError):
                    ano_lancamento = None
            
            # Criar ou atualizar filme
            Filme.objects.update_or_create(
                id=tmdb_id,
                defaults={
                    'nome': movie.get('title', ''),
                    'descricao': movie.get('overview', ''),
                    'poster_path': poster_path,
                    'rating_tmdb': movie.get('vote_average'),
                    'ano_lancamento': ano_lancamento,
                    'capa': capa_bin if capa_bin else None,
                }
            )
            
            # Associar géneros
            for genre_id in movie.get('genre_ids', []):
                genero_nome = get_genre_name_from_id(genre_id)
                if genero_nome:
                    genero, _ = Genero.objects.get_or_create(
                        nome=genero_nome,
                        defaults={'descricao': ''}
                    )
                    filme = Filme.objects.get(id=tmdb_id)
                    filme.generos.add(genero)
        
        # ====================================================================
        # Retornar Resposta
        # ====================================================================
        
        return Response({
            "total": data.get('total_results', 0),
            "page": data.get('page', page),
            "total_pages": data.get('total_pages', 1),
            "results": results
        }, status=status.HTTP_200_OK)
    
    except requests.exceptions.Timeout:
        return Response(
            {"error": "Timeout ao conectar à TMDB API"},
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Erro ao conectar à TMDB API", "detail": str(e)},
            status=status.HTTP_502_BAD_GATEWAY
        )
    except Exception as e:
        return Response(
            {"error": "Erro ao pesquisar filmes", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_genre_name_from_id(genre_id):
    """Mapear ID de género TMDB para nome."""
    genre_map = {
        28: "Action",
        12: "Adventure",
        16: "Animation",
        35: "Comedy",
        80: "Crime",
        99: "Documentary",
        18: "Drama",
        10751: "Family",
        14: "Fantasy",
        36: "History",
        27: "Horror",
        10402: "Music",
        9648: "Mystery",
        10749: "Romance",
        878: "Science Fiction",
        10770: "TV Movie",
        53: "Thriller",
        10752: "War",
        37: "Western"
    }
    return genre_map.get(genre_id)


# ============================================================================
# Endpoint adicional: Pesquisa TMDB (fallback para filmes não em cache)
# ============================================================================

@api_view(['GET'])
def search_movies_tmdb(request):
 
    query = request.GET.get('query', '').strip()
    if not query:
        return Response(
            {"error": "O parâmetro 'query' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        data = tmdb_request("search/movie", params={"query": query})
        return Response(data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao pesquisar na TMDB", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['GET'])
def trending_movies(request):
    
    # ====================================================================
    # Validação de Parâmetros
    # ====================================================================
    
    period = request.GET.get('period', 'week').lower().strip()
    if period not in ['day', 'week']:
        period = 'week'
    
    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    # ====================================================================
    # Validação da API Key
    # ====================================================================
    
    api_key = settings.TMDB_API_KEY
    if not api_key or api_key == "":
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": "API key da TMDB não configurada"
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # ====================================================================
    # Chamada à API da TMDB
    # ====================================================================
    
    try:
        # Construir URL do endpoint trending
        url = f"https://api.themoviedb.org/3/trending/movie/{period}"
        
        params = {
            'api_key': api_key,
            'page': page,
            'language': 'en-US'  # TMDB padrão é en-US
        }
        
        # Fazer pedido com timeout de 10 segundos
        response = requests.get(
            url,
            params=params,
            timeout=10
        )
        response.raise_for_status()  # Lançar erro se status != 2xx
        
        data = response.json()
        
        # ====================================================================
        # Validação da Resposta
        # ====================================================================
        
        if 'results' not in data:
            return Response(
                {
                    "total": 0,
                    "page": page,
                    "total_pages": 1,
                    "period": period,
                    "results": []
                },
                status=status.HTTP_200_OK
            )
        
        # ====================================================================
        # Retornar Resposta Formatada
        # ====================================================================
        
        return Response(
            {
                "total": data.get('total_results', 0),
                "page": data.get('page', page),
                "total_pages": data.get('total_pages', 1),
                "period": period,
                "results": data.get('results', [])
            },
            status=status.HTTP_200_OK
        )
    
    except requests.exceptions.Timeout:
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": "Timeout na ligação à TMDB (mais de 10 segundos)"
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    except requests.exceptions.ConnectionError:
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": "Erro de conexão com a TMDB"
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    except requests.exceptions.HTTPError as e:
        # Erro HTTP (401, 403, 404, 500, etc.)
        if e.response.status_code == 401:
            detail = "API key da TMDB inválida ou expirada"
        elif e.response.status_code == 403:
            detail = "Acesso negado à API da TMDB"
        elif e.response.status_code == 429:
            detail = "Rate limit da TMDB excedido"
        else:
            detail = f"Erro HTTP {e.response.status_code} da TMDB"
        
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": detail
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    except requests.exceptions.RequestException as e:
        # Qualquer outro erro de requests
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": "Erro ao conectar à API da TMDB"
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    except ValueError:
        # Erro ao fazer parse do JSON
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": "Resposta inválida da TMDB"
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    except Exception as e:
        # Erro inesperado
        return Response(
            {
                "error": "Erro ao obter filmes trending",
                "detail": "Erro interno do servidor"
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['GET'])
def movie_details(request, movie_id):
   

    user = request.user if request.user.is_authenticated else None

    # Procura 1º na BD LOCAL
    try:
        filme = Filme.objects.prefetch_related("generos").get(id=movie_id)

        # estado do utilizador (default)
        rating_user = None
        favorito = False
        visto = False
        ver_mais_tarde = False

        if user:
            atividade = AtividadeUsuario.objects.filter(usuario=user, filme=filme).first()
            if atividade:
                rating_user = atividade.rating
                favorito = atividade.favorito
                visto = atividade.visto
                ver_mais_tarde = atividade.ver_mais_tarde

        return Response({
            "id": filme.id,
            "title": filme.nome,
            "overview": filme.descricao,
            "genres": [g.nome for g in filme.generos.all()],
            "tmdb_rating": filme.rating_tmdb,
            "poster_url": f"https://image.tmdb.org/t/p/w500{filme.poster_path}" if filme.poster_path else None,

            # user info
            "rating_user": rating_user,
            "favorito": favorito,
            "visto": visto,
            "ver_mais_tarde": ver_mais_tarde,

            "source": "database"
        })

    except Filme.DoesNotExist:
        pass  # não está na BD → avançar para TMDB

    # Procura no tmdb
    data = tmdb_request(f"movie/{movie_id}")

    if "id" not in data:
        return Response({"error": "Filme não encontrado na TMDB"}, status=404)

    titulo = data.get("title")
    descricao = data.get("overview")
    generos_tmdb = data.get("genres", [])
    poster_path = data.get("poster_path")
    tmdb_rating = data.get("vote_average")

    # guarda na bd
    capa_bin = b""

    if poster_path:
        img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        try:
            img_resp = requests.get(img_url)
            if img_resp.status_code == 200:
                capa_bin = img_resp.content
        except:
            pass

    filme = Filme.objects.create(
        id=movie_id,
        nome=titulo,
        descricao=descricao,
        rating_tmdb=tmdb_rating,
        capa=capa_bin,
        poster_path=poster_path
    )

    # guardar géneros
    for g in generos_tmdb:
        genre, _ = Genero.objects.get_or_create(
            nome=g["name"],
            defaults={"descricao": ""}
        )
        filme.generos.add(genre)

    rating_user = None
    favorito = False
    visto = False
    ver_mais_tarde = False

    if user:
        atividade = AtividadeUsuario.objects.filter(usuario=user, filme=filme).first()
        if atividade:
            rating_user = atividade.rating
            favorito = atividade.favorito
            visto = atividade.visto
            ver_mais_tarde = atividade.ver_mais_tarde

    return Response({
        "id": filme.id,
        "title": filme.nome,
        "overview": filme.descricao,
        "genres": [g.nome for g in filme.generos.all()],
        "tmdb_rating": filme.rating_tmdb,
        "poster_url": f"https://image.tmdb.org/t/p/w500{filme.poster_path}" if filme.poster_path else None,
        "rating_user": rating_user,
        "favorito": favorito,
        "visto": visto,
        "ver_mais_tarde": ver_mais_tarde,

        "source": "tmdb_cached"
    })


# ============================================================================
# SISTEMA DE AVALIAÇÕES - RF-04 (Avaliações) e US07 (Avaliar Filme)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_movie(request):
    user = request.user
    
    if 'movie_id' not in request.data:
        return Response(
            {"error": "O parâmetro 'movie_id' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if 'rating' not in request.data:
        return Response(
            {"error": "O parâmetro 'rating' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie_id = int(request.data.get('movie_id'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if movie_id <= 0:
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número positivo"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rating = int(request.data.get('rating'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'rating' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not (0 <= rating <= 10):
        return Response(
            {"error": "Rating deve estar entre 0 e 10"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    atividade, created = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={'rating': rating}
    )
    
    rating_average = filme.get_rating_medio_usuarios()
    total_ratings = filme.get_numero_avaliacoes()
    
    response_data = {
        "message": "Avaliação registada com sucesso" if created else "Avaliação atualizada com sucesso",
        "movie_id": filme.id,
        "movie_title": filme.nome,
        "rating": rating,
        "rating_average": rating_average,
        "total_ratings": total_ratings,
        "created": created
    }
    
    response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    
    return Response(response_data, status=response_status)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_rating(request):
    user = request.user
    
    if 'movie_id' not in request.data:
        return Response(
            {"error": "O parâmetro 'movie_id' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if 'rating' not in request.data:
        return Response(
            {"error": "O parâmetro 'rating' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie_id = int(request.data.get('movie_id'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if movie_id <= 0:
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número positivo"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rating = int(request.data.get('rating'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'rating' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not (0 <= rating <= 10):
        return Response(
            {"error": "Rating deve estar entre 0 e 10"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme=filme)
    except AtividadeUsuario.DoesNotExist:
        return Response(
            {"error": "Não existe avaliação anterior para este filme"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    atividade.rating = rating
    atividade.save(update_fields=['rating', 'updated_at'])
    
    rating_average = filme.get_rating_medio_usuarios()
    total_ratings = filme.get_numero_avaliacoes()
    
    response_data = {
        "message": "Avaliação atualizada com sucesso",
        "movie_id": filme.id,
        "movie_title": filme.nome,
        "rating": rating,
        "rating_average": rating_average,
        "total_ratings": total_ratings,
        "updated_at": atividade.updated_at.isoformat() if atividade.updated_at else None
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_rating(request):
    user = request.user
    
    # Obter movie_id do corpo do pedido ou de query parameter
    movie_id = None
    
    if request.data and 'movie_id' in request.data:
        movie_id = request.data.get('movie_id')
    elif 'movie_id' in request.GET:
        movie_id = request.GET.get('movie_id')
    
    if movie_id is None:
        return Response(
            {"error": "O parâmetro 'movie_id' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie_id = int(movie_id)
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if movie_id <= 0:
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número positivo"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme=filme)
    except AtividadeUsuario.DoesNotExist:
        return Response(
            {"error": "Não existe avaliação para este filme"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if atividade.rating is None:
        return Response(
            {"error": "Não existe avaliação para este filme"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Guardar dados antes da eliminação para a resposta
    old_rating = atividade.rating
    
    # Remover o rating (manter o registo de atividade caso existam outras interações)
    atividade.rating = None
    atividade.save(update_fields=['rating', 'updated_at'])
    
    # Recalcular a média do filme após remoção
    rating_average = filme.get_rating_medio_usuarios()
    total_ratings = filme.get_numero_avaliacoes()
    
    response_data = {
        "message": "Avaliação removida com sucesso",
        "movie_id": filme.id,
        "movie_title": filme.nome,
        "removed_rating": old_rating,
        "rating_average": rating_average,
        "total_ratings": total_ratings,
        "deleted_at": atividade.updated_at.isoformat() if atividade.updated_at else None
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_rated_movies(request):
    user = request.user
    
    try:
        atividades = (
            AtividadeUsuario.objects
            .filter(usuario=user, rating__isnull=False)
            .select_related('filme')
            .prefetch_related('filme__generos')
            .order_by('-updated_at')
        )
        
        results = []
        for atividade in atividades:
            try:
                filme = atividade.filme
                results.append({
                    "id": filme.id,
                    "title": filme.nome,
                    "overview": filme.descricao,
                    "genres": [g.nome for g in filme.generos.all()],
                    "poster_path": filme.poster_path,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{filme.poster_path}" if filme.poster_path else None,
                    "tmdb_rating": filme.rating_tmdb,
                    "user_rating": atividade.rating,
                    "release_date": filme.ano_lancamento,
                    "rated_at": atividade.updated_at.isoformat() if atividade.updated_at else None
                })
            except Exception:
                continue
        
        return Response({
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao obter filmes avaliados"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_genres(request):
    try:
        genres = (
            Genero.objects
            .all()
            .order_by('nome')
            .distinct()
        )
        
        genre_list = [
            {
                'nome': g.nome,
                'descricao': g.descricao or ''
            }
            for g in genres
        ]
        
        return Response({
            'total': len(genre_list),
            'genres': genre_list
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': 'Erro ao obter géneros', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# FAVORITOS - RF-08 (Lista Pessoal de Favoritos)
# ============================================================================

class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestão de favoritos do utilizador.
    
    Requisito RF-08: Favoritos / Watchlist
    Requisito RNF-04: Segurança e Autenticação (IsAuthenticated)
    
    Endpoints:
        - GET /api/favorites/       - Lista todos os favoritos do utilizador autenticado
        - POST /api/favorites/      - Adiciona um filme aos favoritos (body: {"movie_id": <id>})
        - DELETE /api/favorites/<id>/ - Remove um favorito específico
    
    Características:
        - Apenas utilizadores autenticados podem aceder (IsAuthenticated)
        - Filtra automaticamente por utilizador autenticado (get_queryset)
        - Ordenado por data de adição (descendente - mais recentes primeiro)
        - Define automaticamente o utilizador na criação (perform_create)
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna apenas os favoritos do utilizador autenticado.
        Ordenados por data de adição (descendente - RF-09).
        
        Requisito RF-08: Filtragem por utilizador
        Requisito RF-09: Ordenação por data de adição
        """
        return Favorito.objects.filter(
            usuario=self.request.user
        ).select_related('filme').order_by('-data_adicao')
    
    def perform_create(self, serializer):
        """
        Define o utilizador autenticado ao criar um favorito.
        Garante que o campo 'user' é definido corretamente (RF-08).
        
        Requisito RF-08: Associação automática ao utilizador autenticado
        """
        movie_id = serializer.validated_data.pop('movie_id')
        filme = Filme.objects.get(id=movie_id)
        serializer.save(usuario=self.request.user, filme=filme)


# ============================================================================
# CATÁLOGO DE FILMES - RF-04 (Explorar Catálogo) e RF-05 (Pesquisa/Filtro)
# ============================================================================

class StandardResultsPagination(PageNumberPagination):
    """
    Paginação padrão para resultados de catálogo.
    
    Requisito RF-04: Explorar Catálogo
    Requisito RNF-01: Performance (limitar resultados por página)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class MovieCatalogueView(APIView):
    """
    Endpoint para explorar o catálogo de filmes com pesquisa e filtros.
    
    Requisito RF-04: Explorar Catálogo
    Requisito RF-05: Pesquisa e Filtro
    Requisito RF-12: Integração com API Externa (TMDB)
    Requisito RNF-01: Performance e Tempo de Resposta
    Requisito US04: Pesquisa por Título
    Requisito US05: Filtragem por Género
    
    GET /api/movies/catalogue/
    
    Query Parameters:
        - page (int, opcional): Número da página (default: 1)
        - title (str, opcional): Termo de pesquisa para título (US04)
        - genre_id (int, opcional): ID do género para filtro (US05)
    
    Autenticação: Não requerida (AllowAny) - RF-04
    
    Response (HTTP 200 - Sucesso):
    {
        "count": 15000,
        "next": "http://localhost:8000/api/movies/catalogue/?page=2",
        "previous": null,
        "results": [
            {
                "movie_id": 438,
                "title": "Dune",
                "overview": "Paul Atreides, a brilliant...",
                "poster_path": "/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
                "poster_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
                "backdrop_path": "/wfrfLo3pXp0FsMPv1vjdMqjqMvh.jpg",
                "release_date": "2021-09-15",
                "vote_average": 7.8,
                "vote_count": 8500,
                "genre_ids": [878, 12, 28],
                "original_language": "en",
                "popularity": 500.5
            },
            ...
        ]
    }
    
    Response (HTTP 400 - Parâmetros inválidos):
    {
        "error": "Parâmetro 'page' deve ser um número inteiro positivo"
    }
    
    Response (HTTP 503 - Erro TMDB):
    {
        "error": "Erro ao conectar à API da TMDB",
        "detail": "Timeout excedido"
    }
    
    Características:
        - Acesso público (sem autenticação)
        - Suporta paginação manual via TMDB
        - Pesquisa por título (US04)
        - Filtro por género (US05)
        - Timeout de 10 segundos (RNF-01)
        - Formato de resposta paginado (DRF-style)
    """
    
    permission_classes = [AllowAny]
    pagination_class = StandardResultsPagination
    
    def get(self, request):
        """
        Método GET para obter catálogo de filmes com suporte a pesquisa e filtros.
        
        Requisito RF-04: Explorar Catálogo
        Requisito RF-05: Pesquisa e Filtro
        """
        # ====================================================================
        # Extrair e validar parâmetros de query
        # ====================================================================
        
        # Página (default: 1)
        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            return Response(
                {"error": "Parâmetro 'page' deve ser um número inteiro positivo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Título para pesquisa (US04)
        title = request.query_params.get('title', '').strip()
        if title and len(title) > 512:
            return Response(
                {"error": "Parâmetro 'title' não pode exceder 512 caracteres"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Genre ID ou Genre Name para filtro (US05)
        genre_id = request.query_params.get('genre_id', None)
        genre_name = request.query_params.get('genre_name', None)
        
        # Mapeamento de nomes de géneros para IDs da TMDB
        GENRE_NAME_TO_ID = {
            'Action': 28,
            'Adventure': 12,
            'Animation': 16,
            'Comedy': 35,
            'Crime': 80,
            'Documentary': 99,
            'Drama': 18,
            'Family': 10751,
            'Fantasy': 14,
            'History': 36,
            'Horror': 27,
            'Music': 10402,
            'Mystery': 9648,
            'Romance': 10749,
            'Science Fiction': 878,
            'TV Movie': 10770,
            'Thriller': 53,
            'War': 10752,
            'Western': 37
        }
        
        # Se foi fornecido nome do género, converter para ID
        if genre_name and not genre_id:
            genre_id = GENRE_NAME_TO_ID.get(genre_name)
            if not genre_id:
                return Response(
                    {"error": f"Género '{genre_name}' não reconhecido"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar genre_id se fornecido diretamente
        if genre_id:
            try:
                genre_id = int(genre_id)
                if genre_id < 1:
                    raise ValueError("Genre ID deve ser positivo")
            except (ValueError, TypeError):
                return Response(
                    {"error": "Parâmetro 'genre_id' deve ser um número inteiro positivo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # ====================================================================
        # Chamar serviço TMDB (RF-12)
        # ====================================================================
        
        try:
            # Buscar filmes via serviço (RNF-01: timeout de 10s)
            tmdb_data = tmdb_service.fetch_movies(
                page=page,
                title=title if title else None,
                genre_id=genre_id
            )
            
            # Extrair dados da resposta
            total_results = tmdb_data.get('total_results', 0)
            total_pages = tmdb_data.get('total_pages', 0)
            current_page = tmdb_data.get('page', page)
            results = tmdb_data.get('results', [])
            
        except requests.exceptions.Timeout:
            return Response(
                {
                    "error": "Erro ao conectar à API da TMDB",
                    "detail": "Timeout excedido (mais de 10 segundos)"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except requests.exceptions.ConnectionError:
            return Response(
                {
                    "error": "Erro ao conectar à API da TMDB",
                    "detail": "Erro de conexão"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else 500
            
            if status_code == 401:
                detail = "API key da TMDB inválida ou expirada"
            elif status_code == 404:
                detail = "Recurso não encontrado na TMDB"
            elif status_code == 429:
                detail = "Rate limit da TMDB excedido"
            else:
                detail = f"Erro HTTP {status_code} da TMDB"
            
            return Response(
                {
                    "error": "Erro ao obter dados da TMDB",
                    "detail": detail
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            return Response(
                {
                    "error": "Erro ao processar catálogo de filmes",
                    "detail": "Erro interno do servidor"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # ====================================================================
        # Formatar resultados (RF-04)
        # ====================================================================
        
        formatted_results = []
        
        for movie in results:
            # Construir URL do poster
            poster_path = movie.get('poster_path')
            poster_url = None
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            
            # Construir objeto de filme formatado
            formatted_movie = {
                'movie_id': movie.get('id'),
                'title': movie.get('title', ''),
                'overview': movie.get('overview', ''),
                'poster_path': poster_path,
                'poster_url': poster_url,
                'backdrop_path': movie.get('backdrop_path'),
                'release_date': movie.get('release_date'),
                'vote_average': movie.get('vote_average'),
                'vote_count': movie.get('vote_count'),
                'genre_ids': movie.get('genre_ids', []),
                'original_language': movie.get('original_language'),
                'popularity': movie.get('popularity'),
            }
            
            formatted_results.append(formatted_movie)
        
        # ====================================================================
        # Construir resposta paginada (formato DRF)
        # ====================================================================
        
        # Construir URLs de navegação
        base_url = request.build_absolute_uri(request.path)
        
        # Query parameters para manter nos links
        query_params = {}
        if title:
            query_params['title'] = title
        if genre_id:
            query_params['genre_id'] = genre_id
        
        # URL da próxima página
        next_url = None
        if current_page < total_pages:
            next_params = query_params.copy()
            next_params['page'] = current_page + 1
            next_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in next_params.items())}"
        
        # URL da página anterior
        previous_url = None
        if current_page > 1:
            prev_params = query_params.copy()
            prev_params['page'] = current_page - 1
            previous_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in prev_params.items())}"
        
        # Resposta paginada (formato DRF)
        response_data = {
            'count': total_results,
            'next': next_url,
            'previous': previous_url,
            'results': formatted_results
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


# ============================================================================
# HISTÓRICO DE VISUALIZAÇÕES - RF-09 (Histórico de Interação)
# ============================================================================

class HistoryWatchedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar histórico de visualizações do utilizador.
    
    Requisito RF-09: Histórico de Interação
    Requisito RNF-04: Segurança e Autenticação (IsAuthenticated)
    
    Endpoints:
        - GET /api/history/watched/ - Lista todos os filmes vistos pelo utilizador
    
    Características:
        - Apenas leitura (ReadOnlyModelViewSet)
        - Apenas utilizadores autenticados podem aceder
        - Filtra automaticamente por utilizador autenticado
        - Ordenado por data de visualização (descendente)
    """
    serializer_class = HistoryItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        """
        Retorna apenas o histórico do utilizador autenticado.
        Ordenado por data de visualização (descendente).
        
        Requisito RF-09: Filtragem por utilizador e ordenação
        """
        return HistoricoVisualizacao.objects.filter(
            usuario=self.request.user
        ).select_related('filme').prefetch_related('filme__generos').order_by('-data_visualizacao')


# ============================================================================
# WATCH LATER / VER MAIS TARDE - RF-08 (Watchlist)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_watch_later(request):
    """
    Adiciona um filme à lista Ver Mais Tarde.
    
    Requisito RF-08: Watchlist
    
    POST /api/movies/watch_later/add/
    Body: {"movie_id": <id>}
    """
    user = request.user
    
    if 'movie_id' not in request.data:
        return Response(
            {"error": "O parâmetro 'movie_id' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie_id = int(request.data.get('movie_id'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if movie_id <= 0:
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número positivo"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    atividade, created = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={'ver_mais_tarde': True}
    )
    
    return Response({
        "message": "Filme adicionado à lista Ver Mais Tarde" if created else "Lista Ver Mais Tarde atualizada",
        "movie_id": filme.id,
        "movie_title": filme.nome,
        "created": created
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_watch_later(request):
    """
    Remove um filme da lista Ver Mais Tarde.
    
    Requisito RF-08: Watchlist
    
    POST /api/movies/watch_later/remove/
    Body: {"movie_id": <id>}
    """
    user = request.user
    
    if 'movie_id' not in request.data:
        return Response(
            {"error": "O parâmetro 'movie_id' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie_id = int(request.data.get('movie_id'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme=filme)
        atividade.ver_mais_tarde = False
        atividade.save(update_fields=['ver_mais_tarde', 'updated_at'])
        
        return Response({
            "message": "Filme removido da lista Ver Mais Tarde",
            "movie_id": filme.id,
            "movie_title": filme.nome
        }, status=status.HTTP_200_OK)
    
    except AtividadeUsuario.DoesNotExist:
        return Response(
            {"error": "Filme não está na lista Ver Mais Tarde"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_watch_later(request):
    """
    Lista todos os filmes na lista Ver Mais Tarde do utilizador.
    
    Requisito RF-08: Watchlist
    
    GET /api/movies/watch_later/
    """
    user = request.user
    
    try:
        atividades = (
            AtividadeUsuario.objects
            .filter(usuario=user, ver_mais_tarde=True)
            .select_related('filme')
            .prefetch_related('filme__generos')
            .order_by('-updated_at')
        )
        
        results = []
        for atividade in atividades:
            try:
                filme = atividade.filme
                results.append({
                    "id": filme.id,
                    "title": filme.nome,
                    "overview": filme.descricao,
                    "genres": [g.nome for g in filme.generos.all()],
                    "poster_path": filme.poster_path,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{filme.poster_path}" if filme.poster_path else None,
                    "tmdb_rating": filme.rating_tmdb,
                    "added_at": atividade.updated_at.isoformat() if atividade.updated_at else None
                })
            except Exception:
                continue
        
        return Response({
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao obter lista Ver Mais Tarde"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# REVIEWS / COMENTÁRIOS - RF-04 (Avaliações e Reviews)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_review(request):
    """
    Adiciona ou atualiza um review de um filme.
    
    Requisito RF-04: Avaliações e Reviews
    
    POST /api/movies/reviews/add/
    Body: {"movie_id": <id>, "review": "<texto>"}
    """
    user = request.user
    
    if 'movie_id' not in request.data:
        return Response(
            {"error": "O parâmetro 'movie_id' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if 'review' not in request.data:
        return Response(
            {"error": "O parâmetro 'review' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie_id = int(request.data.get('movie_id'))
    except (ValueError, TypeError):
        return Response(
            {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    review_text = request.data.get('review', '').strip()
    
    if not review_text:
        return Response(
            {"error": "Review não pode estar vazia"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(review_text) > 2000:
        return Response(
            {"error": "Review não pode exceder 2000 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    atividade, created = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={'review': review_text}
    )
    
    return Response({
        "message": "Review adicionado com sucesso" if created else "Review atualizado com sucesso",
        "movie_id": filme.id,
        "movie_title": filme.nome,
        "review": review_text,
        "created": created
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
def list_reviews(request, movie_id):
    """
    Lista todos os reviews de um filme específico.
    
    Requisito RF-04: Avaliações e Reviews
    
    GET /api/movies/<movie_id>/reviews/
    """
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        atividades = (
            AtividadeUsuario.objects
            .filter(filme=filme, review__isnull=False)
            .exclude(review='')
            .select_related('usuario')
            .order_by('-updated_at')
        )
        
        reviews = []
        for atividade in atividades:
            reviews.append({
                "id": atividade.id,
                "user": {
                    "id": atividade.usuario.id,
                    "nome": atividade.usuario.nome
                },
                "review": atividade.review,
                "rating": atividade.rating,
                "created_at": atividade.created_at.isoformat() if atividade.created_at else None,
                "updated_at": atividade.updated_at.isoformat() if atividade.updated_at else None
            })
        
        return Response({
            "movie_id": filme.id,
            "movie_title": filme.nome,
            "total": len(reviews),
            "reviews": reviews
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao obter reviews"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, movie_id):
    """
    Remove o review do utilizador de um filme.
    
    Requisito RF-04: Avaliações e Reviews
    
    DELETE /api/movies/<movie_id>/reviews/delete/
    """
    user = request.user
    
    try:
        filme = Filme.objects.get(id=movie_id)
    except Filme.DoesNotExist:
        return Response(
            {"error": "Filme não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme=filme)
        
        if not atividade.review:
            return Response(
                {"error": "Não existe review para este filme"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_review = atividade.review
        atividade.review = None
        atividade.save(update_fields=['review', 'updated_at'])
        
        return Response({
            "message": "Review removido com sucesso",
            "movie_id": filme.id,
            "movie_title": filme.nome,
            "removed_review": old_review
        }, status=status.HTTP_200_OK)
    
    except AtividadeUsuario.DoesNotExist:
        return Response(
            {"error": "Não existe review para este filme"},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================================
# SISTEMA DE RECOMENDAÇÕES - RF-10 (Motor de Recomendação)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_movie_recommendations(request):
    """
    Retorna recomendações personalizadas de filmes baseadas no histórico do utilizador.
    
    Requisito RF-10: Motor de Recomendação
    Requisito RF-11: Tendências/Populares (fallback)
    
    GET /api/movies/recommendations/
    
    Lógica:
    - >= 3 avaliações positivas (>7.5): recomendações por género
    - < 3 avaliações positivas: filmes populares (fallback)
    """
    user = request.user
    
    try:
        # Buscar avaliações positivas (rating > 7.5)
        high_ratings = AtividadeUsuario.objects.filter(
            usuario=user,
            rating__gt=7.5
        ).select_related('filme').prefetch_related('filme__generos')
        
        num_high_ratings = high_ratings.count()
        
        # Obter IDs de filmes já avaliados (para exclusão)
        filmes_avaliados_ids = AtividadeUsuario.objects.filter(
            usuario=user,
            rating__isnull=False
        ).values_list('filme_id', flat=True)
        
        if num_high_ratings >= 3:
            # Extrair géneros dos filmes bem avaliados
            generos_ids = set()
            for atividade in high_ratings:
                for genero in atividade.filme.generos.all():
                    generos_ids.add(genero.nome)
            
            if generos_ids:
                # Filmes com géneros similares, excluindo já avaliados
                filmes_recomendados = (
                    Filme.objects
                    .filter(generos__nome__in=generos_ids)
                    .exclude(id__in=filmes_avaliados_ids)
                    .prefetch_related('generos')
                    .distinct()
                    .order_by('-rating_tmdb')[:20]
                )
            else:
                filmes_recomendados = Filme.objects.none()
        else:
            # Fallback: filmes populares
            filmes_recomendados = (
                Filme.objects
                .exclude(id__in=filmes_avaliados_ids)
                .filter(rating_tmdb__isnull=False)
                .prefetch_related('generos')
                .order_by('-rating_tmdb')[:20]
            )
        
        # Serializar resultados
        results = []
        for filme in filmes_recomendados:
            results.append({
                "id": filme.id,
                "title": filme.nome,
                "overview": filme.descricao,
                "genres": [g.nome for g in filme.generos.all()],
                "poster_path": filme.poster_path,
                "poster_url": f"https://image.tmdb.org/t/p/w500{filme.poster_path}" if filme.poster_path else None,
                "tmdb_rating": filme.rating_tmdb,
                "user_rating_average": filme.get_rating_medio_usuarios()
            })
        
        return Response({
            "num_user_ratings": num_high_ratings,
            "recommendation_type": "personalized" if num_high_ratings >= 3 else "popular",
            "total": len(results),
            "recommendations": results
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao gerar recomendações"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# FAVORITOS - Endpoints customizados para frontend
# Usa AtividadeUsuario.favorito em vez de modelo Favorito
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_favorites(request):
    """
    Listar todos os favoritos do utilizador autenticado.
    
    GET /api/movies/favorites/
    
    Response (HTTP 200):
    {
        "total": 5,
        "results": [
            {
                "id": 438,
                "movie_id": 438,
                "title": "Dune",
                "overview": "...",
                "poster_path": "/...",
                "poster_url": "https://image.tmdb.org/t/p/w500/...",
                "tmdb_rating": 7.8,
                "genres": ["Science Fiction", "Adventure"],
                "added_at": "2024-12-11T10:30:00Z"
            }
        ]
    }
    """
    try:
        user = request.user
        
        # Obter todas as atividades do utilizador que têm favorito=True
        atividades = (
            AtividadeUsuario.objects
            .filter(usuario=user, favorito=True)
            .select_related('filme')
            .prefetch_related('filme__generos')
            .order_by('-data_adicao_favoritos')
        )
        
        results = []
        for atividade in atividades:
            try:
                filme = atividade.filme
                results.append({
                    "id": filme.id,
                    "movie_id": filme.id,
                    "title": filme.nome,
                    "overview": filme.descricao,
                    "poster_path": filme.poster_path,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{filme.poster_path}" if filme.poster_path else None,
                    "backdrop_path": filme.poster_path,  # Fallback
                    "tmdb_rating": filme.rating_tmdb,
                    "genres": [g.nome for g in filme.generos.all()],
                    "genre_ids": list(filme.generos.all().values_list('nome', flat=True)),
                    "release_date": filme.ano_lancamento,
                    "vote_average": filme.rating_tmdb,
                    "added_at": atividade.data_adicao_favoritos.isoformat() if atividade.data_adicao_favoritos else atividade.updated_at.isoformat()
                })
            except Exception as e:
                print(f"Erro ao processar filme {atividade.filme_id}: {e}")
                continue
        
        return Response({
            "total": len(results),
            "results": results
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao listar favoritos", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_favorites(request):
    """
    Adicionar um filme aos favoritos do utilizador.
    
    POST /api/movies/favorites/add/
    
    Request Body:
    {
        "movie_id": 438
    }
    
    Response (HTTP 201):
    {
        "message": "Filme adicionado aos favoritos",
        "movie_id": 438,
        "added_at": "2024-12-11T10:30:00Z"
    }
    """
    try:
        user = request.user
        movie_id = request.data.get('movie_id')
        
        # Validação
        if not movie_id:
            return Response(
                {"error": "O parâmetro 'movie_id' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            movie_id = int(movie_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if movie_id <= 0:
            return Response(
                {"error": "O parâmetro 'movie_id' deve ser um número positivo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obter ou criar o filme
        try:
            filme = Filme.objects.get(id=movie_id)
        except Filme.DoesNotExist:
            return Response(
                {"error": "Filme não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obter ou criar a atividade do utilizador
        atividade, created = AtividadeUsuario.objects.get_or_create(
            usuario=user,
            filme=filme,
            defaults={
                'favorito': True,
                'data_adicao_favoritos': timezone.now() if True else None
            }
        )
        
        # Se já existe, apenas marcar como favorito
        if not created and not atividade.favorito:
            atividade.favorito = True
            atividade.data_adicao_favoritos = timezone.now()
            atividade.save(update_fields=['favorito', 'data_adicao_favoritos', 'updated_at'])
        
        return Response({
            "message": "Filme adicionado aos favoritos com sucesso",
            "movie_id": filme.id,
            "added_at": atividade.data_adicao_favoritos.isoformat() if atividade.data_adicao_favoritos else None
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao adicionar filme aos favoritos", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_favorites(request):
    """
    Remover um filme dos favoritos do utilizador.
    
    DELETE /api/movies/favorites/remove/?movie_id=<id>
    
    Query Parameters:
        - movie_id (int, obrigatório): ID do filme a remover
    
    Response (HTTP 200):
    {
        "message": "Filme removido dos favoritos",
        "movie_id": 438
    }
    """
    try:
        user = request.user
        
        # Obter movie_id do corpo ou query param
        movie_id = request.data.get('movie_id') if request.data else None
        if not movie_id:
            movie_id = request.query_params.get('movie_id')
        
        # Validação
        if not movie_id:
            return Response(
                {"error": "O parâmetro 'movie_id' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            movie_id = int(movie_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "O parâmetro 'movie_id' deve ser um número inteiro"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if movie_id <= 0:
            return Response(
                {"error": "O parâmetro 'movie_id' deve ser um número positivo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obter o filme
        try:
            filme = Filme.objects.get(id=movie_id)
        except Filme.DoesNotExist:
            return Response(
                {"error": "Filme não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obter a atividade do utilizador
        try:
            atividade = AtividadeUsuario.objects.get(usuario=user, filme=filme)
        except AtividadeUsuario.DoesNotExist:
            return Response(
                {"error": "Filme não está nos favoritos"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remover do favoritos
        if not atividade.favorito:
            return Response(
                {"error": "Filme não está nos favoritos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        atividade.favorito = False
        atividade.data_adicao_favoritos = None
        atividade.save(update_fields=['favorito', 'data_adicao_favoritos', 'updated_at'])
        
        return Response({
            "message": "Filme removido dos favoritos com sucesso",
            "movie_id": filme.id
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": "Erro ao remover filme dos favoritos", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
