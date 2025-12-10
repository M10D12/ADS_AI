from functools import cache
import math
from django.shortcuts import render
from django.db import models
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from math import log
from django.db.models import Count, Avg
from .models import AtividadeUsuario, Filme, Genero, Usuario
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password,check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination



from .serializers import (
    UsuarioSerializer, FilmeSerializer, GeneroSerializer,
    AtividadeUsuarioSerializer
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
            "user": {
                "id": user.id,
                "nome": user.nome,
                "email": user.email,
                "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
            }
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


# #Rate Movie
# #ADD RATING A UM FILME DA TMDB E GUARDA NA BD 
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def rate_tmdb_movie(request):
#     user = request.user
#     data = request.data

#     if "tmdb_id" not in data or "rating" not in data:
#         return Response({"error": "tmdb_id e rating são obrigatórios"}, status=400)

#     tmdb_id = data["tmdb_id"]
#     rating = int(data["rating"])

#     if not (1 <= rating <= 10):
#         return Response({"error": "Rating deve estar entre 1 e 10"}, status=400)

#     # procura filme na TMDB
#     tmdb_data = tmdb_request(f"movie/{tmdb_id}")
#     if "id" not in tmdb_data:
#         return Response({"error": "Filme não encontrado na TMDB"}, status=404)

#     titulo = tmdb_data.get("title", "Sem título")
#     descricao = tmdb_data.get("overview", "")
#     generos_tmdb = tmdb_data.get("genres", [])
#     poster_path = tmdb_data.get("poster_path")

    
#     capa_bin = b""
#     if poster_path:
#         img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
#         img_resp = requests.get(img_url)
#         if img_resp.status_code == 200:
#             capa_bin = img_resp.content

#     # Criar filme na BD
#     filme, created = Filme.objects.get_or_create(
#         id=tmdb_id,
#         defaults={
#             "nome": titulo,
#             "descricao": descricao,
#             "rating": None,
#             "capa": capa_bin,
#             "poster_path": poster_path,
#         }
#     )

#     # Guardar géneros
#     for g in generos_tmdb:
#         genre, _ = Genero.objects.get_or_create(
#             nome=g["name"],
#             defaults={"descricao": ""}
#         )
#         filme.generos.add(genre)

#     # Atualizar rating do user
#     atividade, created_act = AtividadeUsuario.objects.update_or_create(
#         usuario=user,
#         filme=filme,
#         defaults={"rating": rating}
#     )

#     return Response({
#         "message": "Rating registado" if created_act else "Rating atualizado",
#         "filme": filme.nome,
#         "rating": rating
#     })

# #My Rated Movies
# #ENDPOINT PARA OBTER A LISTA DE FILMES AVALIADOS PELO USER
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def my_rated_movies(request):
#     user = request.user

#     atividades = (
#         AtividadeUsuario.objects
#         .filter(usuario=user, rating__isnull=False)
#         .select_related("filme")
#         .prefetch_related("filme__generos")
#     )

#     resultado = [
#         serialize_movie(atividade.filme, atividade)
#         for atividade in atividades
#     ]

#     return Response({"filmes": resultado})



# #Editar o rating
# @api_view(["PUT"])
# @permission_classes([IsAuthenticated])
# def update_rating(request, tmdb_id):
#     user = request.user
#     data = request.data

#     if "rating" not in data:
#         return Response({"error": "rating é obrigatório"}, status=400)

#     rating = int(data["rating"])

#     if not (1 <= rating <= 10):
#         return Response({"error": "Rating deve estar entre 1 e 10"}, status=400)

#     try:
#         filme = Filme.objects.get(id=tmdb_id)
#     except Filme.DoesNotExist:
#         return Response({"error": "Filme não encontrado"}, status=404)

#     atividade, _ = AtividadeUsuario.objects.update_or_create(
#         usuario=user,
#         filme=filme,
#         defaults={"rating": rating}
#     )

#     return Response({
#         "message": "Rating atualizado",
#         "filme": filme.nome,
#         "rating": rating
#     })


# #Delete Rating
# @api_view(["DELETE"])
# @permission_classes([IsAuthenticated])
# def delete_rating(request, tmdb_id):
#     user = request.user

#     try:
#         atividade = AtividadeUsuario.objects.get(usuario=user, filme__id=tmdb_id)
#     except AtividadeUsuario.DoesNotExist:
#         return Response({"error": "Este filme não tem rating registado pelo user"}, status=404)

#     atividade.rating = None
#     atividade.save()

#     return Response({"message": "Rating removido com sucesso"})




# #Filtragem de movies por género 

# #Disponibiliza todos os generos que estão no TMDB
# @api_view(["GET"])
# def get_genres(request):
#     """
#     Devolve todos os géneros disponíveis na TMDB para que o frontend
#     possa criar filtros por género.
#     """
#     try:
#         response = tmdb_request("genre/movie/list")
#         genres = response.get("genres", [])

#         # Apenas devolvemos id + nome, limpo
#         return Response({
#             "total": len(genres),
#             "genres": genres
#         })

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)




# #marcar e desmarcar filmes vistos

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def mark_watched(request):
#     user = request.user
#     tmdb_id = request.data.get("tmdb_id")

#     if not tmdb_id:
#         return Response({"error": "tmdb_id é obrigatório"}, status=400)

#     filme, _ = Filme.objects.get_or_create(id=tmdb_id)

#     atividade, _ = AtividadeUsuario.objects.update_or_create(
#         usuario=user,
#         filme=filme,
#         defaults={"visto": True}
#     )

#     return Response({"message": "Filme marcado como visto"})

# #######################################################################################

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def unmark_watched(request):
#     user = request.user
#     tmdb_id = request.data.get("tmdb_id")

#     if not tmdb_id:
#         return Response({"error": "tmdb_id é obrigatório"}, status=400)

#     try:
#         atividade = AtividadeUsuario.objects.get(usuario=user, filme_id=tmdb_id)
#         atividade.visto = False
#         atividade.save()
#     except AtividadeUsuario.DoesNotExist:
#         return Response({"error": "Filme não estava marcado como visto"}, status=404)

#     return Response({"message": "Filme removido dos vistos"})

# @permission_classes([IsAuthenticated])
# def list_favorites(request):
#     user = request.user

#     atividades = (
#         AtividadeUsuario.objects
#         .filter(usuario=user, favorito=True)
#         .select_related("filme")
#     )

#     filmes = [
#         serialize_movie(a.filme, a)
#         for a in atividades
#     ]

#     return Response({"favorites": filmes})



# @api_view(["GET"])
# def movies_catalog(request):
#     page = int(request.GET.get("page", 1))
#     page_size = int(request.GET.get("page_size", 10))

#     # Calcular offsets
#     start = (page - 1) * page_size
#     end = start + page_size

#     # Buscar total
#     total_filmes = Filme.objects.count()

#     # Buscar filmes paginados
#     filmes = Filme.objects.all().order_by("id")[start:end]

#     filmes_formatados = [
#         {
#             "tmdb_id": f.id,
#             "titulo": f.nome,
#             "descricao": f.descricao,
#             "poster_url": tmdb_image_url(f.poster_path),
#             "rating_tmdb": f.rating,   # rating guardado do TMDB
#             "generos": [g.nome for g in f.generos.all()],
#         }
#         for f in filmes
#     ]

#     return Response({
#         "page": page,
#         "page_size": page_size,
#         "total_results": total_filmes,
#         "filmes": filmes_formatados
#     })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def history(request):
#     user = request.user

#     atividades = (
#         AtividadeUsuario.objects
#         .filter(usuario=user)
#         .select_related("filme")
#     )

#     resultado = []

#     for a in atividades:
#         filme_data = serialize_movie(a.filme, a)

#         filme_data["tipo"] = (
#             "rating" if a.rating is not None else
#             "visto" if a.visto else
#             "favorito" if a.favorito else
#             "ver_mais_tarde" if a.ver_mais_tarde else
#             "atividade"
#         )

#         resultado.append(filme_data)

#     return Response({
#         "total": len(resultado),
#         "history": resultado
#     })




# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def add_watch_later(request):
#     user = request.user
#     tmdb_id = request.data.get("tmdb_id")

#     if not tmdb_id:
#         return Response({"error": "tmdb_id é obrigatório"}, status=400)

#     filme, _ = Filme.objects.get_or_create(id=tmdb_id)

#     atividade, _ = AtividadeUsuario.objects.update_or_create(
#         usuario=user,
#         filme=filme,
#         defaults={"ver_mais_tarde": True}
#     )

#     return Response({"message": "Adicionado à lista Ver Mais Tarde"})


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def remove_watch_later(request):
#     user = request.user
#     tmdb_id = request.data.get("tmdb_id")

#     if not tmdb_id:
#         return Response({"error": "tmdb_id é obrigatório"}, status=400)

#     try:
#         atividade = AtividadeUsuario.objects.get(usuario=user, filme_id=tmdb_id)
#         atividade.ver_mais_tarde = False
#         atividade.save()
#     except AtividadeUsuario.DoesNotExist:
#         return Response({"error": "Filme não estava na lista Ver Mais Tarde"}, status=404)

#     return Response({"message": "Removido da lista Ver Mais Tarde"})


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def list_watch_later(request):
#     user = request.user

#     atividades = (
#         AtividadeUsuario.objects
#         .filter(usuario=user, ver_mais_tarde=True)
#         .select_related("filme")
#     )

#     filmes = [
#         serialize_movie(a.filme, a)
#         for a in atividades
#     ]

#     return Response({"watch_later": filmes})

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def add_review(request, tmdb_id):
#     user= request.user
#     review_text= request.data.get("review")

#     if review_text is None or review_text.strip() == "":
#         return Response({"error":"review não pode ser vazia"},status=400)
    
#     filme,_= Filme.objects.get_or_create(id=tmdb_id)

#     atividade, created= AtividadeUsuario.objects.update_or_create(
#         usuario=user,
#         filme=filme,
#         defaults={"review":review_text}
#     )

#     return Response({
#         "message":"Review adicionada" if created else "Review atualizada",
#         "filme":filme.nome,
#         "review":review_text
#     })

# @api_view(["GET"])
# def list_reviews(request, tmdb_id):
#     atividades = (
#         AtividadeUsuario.objects
#         .filter(filme_id=tmdb_id)
#         .select_related("usuario")
#     )

#     reviews = [
#         {
#             "user_id": a.usuario.id,
#             "user_nome": a.usuario.nome,
#             "comentario": a.review
#         }
#         for a in atividades
#     ]

#     return Response({
#         "tmdb_id": tmdb_id,
#         "total_reviews": len(reviews),
#         "reviews": reviews
#     })


# @api_view(["DELETE"])
# @permission_classes([IsAuthenticated])
# def delete_review(request, tmdb_id):
#     user= request.user

#     try:
#         atividade= AtividadeUsuario.objects.get(
#             usuario=user,
#             filme__id=tmdb_id,
#         )
#     except AtividadeUsuario.DoesNotExist:
#         return Response({"error":"Review não encontrada"},status=404)
    
#     atividade.review= None
#     atividade.save()

#     return Response({"message":"Review removida com sucesso"})


# ########################################### AI

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_movie_recommendations(request):
#     """
#     Endpoint de recomendações personalizadas para utilizador autenticado.
    
#     RF-10 (Motor de Recomendação): Recomendações baseadas em avaliações > 7.5
#     RF-11 (Tendências/Populares): Fallback para filmes populares se < 3 avaliações
    
#     Casos de teste:
#     - >= 3 avaliações positivas: recomendações por género
#     - < 3 avaliações positivas: filmes populares como fallback
#     - Sem filmes recomendáveis: lista vazia
#     - Não autenticado: HTTP 401 Unauthorized
    
#     Performance: tempo resposta ≤ 800ms
#     """
#     user = request.user
    
#     # Buscar avaliações positivas do utilizador (rating > 7.5)
#     high_ratings = AtividadeUsuario.objects.filter(
#         usuario=user,
#         rating__gt=7.5
#     ).select_related('filme').prefetch_related('filme__generos')
    
#     num_high_ratings = high_ratings.count()
    
#     # Obter IDs de filmes que o utilizador já avaliou (para exclusão)
#     filmes_avaliados_ids = AtividadeUsuario.objects.filter(
#         usuario=user,
#         rating__isnull=False
#     ).values_list('filme_id', flat=True)
    
#     # Caso 1: Utilizador tem >= 3 avaliações positivas
#     if num_high_ratings >= 3:
#         # Extrair géneros dos filmes bem avaliados usando tuple (hashable)
#         generos_ids = tuple()
        
#         for atividade in high_ratings:
#             filme = atividade.filme
#             for genero in filme.generos.all():
#                 if genero.nome not in generos_ids:
#                     generos_ids = generos_ids + (genero.nome,)
        
#         if generos_ids:
#             # Filmes com géneros similares, excluindo os já avaliados
#             filmes_recomendados = (
#                 Filme.objects
#                 .filter(generos__nome__in=generos_ids)
#                 .exclude(id__in=filmes_avaliados_ids)
#                 .prefetch_related('generos')
#                 .distinct()
#                 .order_by('-rating')[:20]
#             )
#         else:
#             filmes_recomendados = Filme.objects.none()
    
#     # Caso 2: Utilizador tem < 3 avaliações positivas (fallback para populares)
#     else:
#         # Filmes populares (maior rating do TMDB), excluindo os já avaliados
#         filmes_recomendados = (
#             Filme.objects
#             .exclude(id__in=filmes_avaliados_ids)
#             .prefetch_related('generos')
#             .order_by('-rating')[:20]
#         )
    
#     # Serializar filmes recomendados
#     resultado = []
#     for filme in filmes_recomendados:
#         filme_dict = {
#             "tmdb_id": filme.id,
#             "titulo": filme.nome,
#             "descricao": filme.descricao,
#             "poster_url": tmdb_image_url(filme.poster_path),
#             "rating_tmdb": filme.rating,
#             "generos": [g.nome for g in filme.generos.all()],
#         }
#         resultado.append(filme_dict)
    
#     return Response({
#         "num_user_ratings": num_high_ratings,
#         "recommendation_type": "personalized" if num_high_ratings >= 3 else "popular",
#         "total": len(resultado),
#         "recommendations": resultado
#     })


# def recommendations_view(request):
#     """Alias para compatibilidade com urls.py"""
#     return get_movie_recommendations(request)




# class RatingFilterPagination(PageNumberPagination):
#     page_size = 10
#     page_query_param = "page"
#     page_size_query_param = "page_size"
#     max_page_size = 100


# @api_view(["GET"])
# def filter_by_rating(request):
#     """
#     GET /api/movies/filter_by_rating/?min_rating=<float>&max_rating=<float>&page=<int>&page_size=<int>

#     Filters films by the average user rating (average of AtividadeUsuario.rating).
#     - min_rating and max_rating are optional (defaults: 0 and 10).
#     - Values must be numeric and in [0, 10].
#     - Returns paginated JSON response with film info and avg_user_rating.
#     - Validation errors return HTTP 400 with a clear message.
#     """
#     # Parse query parameters with sensible defaults
#     min_raw = request.GET.get("min_rating", "")
#     max_raw = request.GET.get("max_rating", "")

#     # Default values
#     if min_raw == "":
#         min_rating = 0.0
#     else:
#         try:
#             min_rating = float(min_raw)
#         except (TypeError, ValueError):
#             return Response(
#                 {"error": "min_rating must be a number between 0 and 10."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#     if max_raw == "":
#         max_rating = 10.0
#     else:
#         try:
#             max_rating = float(max_raw)
#         except (TypeError, ValueError):
#             return Response(
#                 {"error": "max_rating must be a number between 0 and 10."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#     # Validate ranges
#     if not (0.0 <= min_rating <= 10.0):
#         return Response(
#             {"error": "min_rating must be between 0 and 10."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )
#     if not (0.0 <= max_rating <= 10.0):
#         return Response(
#             {"error": "max_rating must be between 0 and 10."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )
#     if min_rating > max_rating:
#         return Response(
#             {"error": "min_rating cannot be greater than max_rating."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     # Build queryset: annotate with avg user rating and filter by it.
#     # Exclude films without user ratings (avg_user_rating is NULL).
#     films_qs = (
#         Filme.objects
#         .annotate(avg_user_rating=Avg("atividadeusuario__rating"))
#         .filter(
#             avg_user_rating__isnull=False,
#             avg_user_rating__gte=min_rating,
#             avg_user_rating__lte=max_rating,
#         )
#         .prefetch_related("generos")
#         .order_by("-avg_user_rating", "-rating", "id")
#     )

#     # Pagination
#     paginator = RatingFilterPagination()
#     page = paginator.paginate_queryset(films_qs, request)

#     # Serialization helper
#     def _serialize(film):
#         return {
#             "tmdb_id": film.id,
#             "titulo": film.nome,
#             "descricao": film.descricao,
#             "poster_url": tmdb_image_url(film.poster_path),
#             "rating_tmdb": film.rating,
#             "avg_user_rating": round(getattr(film, "avg_user_rating", 0.0), 2),
#             "generos": [g.nome for g in film.generos.all()],
#         }

#     results = [_serialize(f) for f in page] if page is not None else []

#     # Total matching results for client-side pagination
#     total_matching = films_qs.count()

#     response_payload = {
#         "min_rating": min_rating,
#         "max_rating": max_rating,
#         "total_results": total_matching,
#         "page": int(request.GET.get("page", 1)),
#         "page_size": paginator.get_page_size(request) or paginator.page_size,
#         "results": results,
#     }

#     return Response(response_payload, status=status.HTTP_200_OK)

# @api_view(["GET"])
# def get_genres(request):
#     """
#     GET /api/movies/genres/

#     Devolve a lista completa de géneros existentes na base de dados local,
#     associados a filmes reais. Ordenados alfabeticamente, sem duplicações.

#     RF-02 (Gestão de Catálogo): Fornece catálogo de géneros disponíveis.
#     RF-05 (Pesquisa e Filtro): Suporta filtros dinâmicos por género.
#     US03 & US05: Permite ao frontend carregar géneros para seleção.

#     Retorna:
#         {
#             "total": <int>,
#             "genres": [
#                 {"nome": "Ação", "descricao": "..."},
#                 {"nome": "Comédia", "descricao": "..."},
#                 ...
#             ]
#         }
#     """
#     try:
#         # Buscar apenas géneros associados a filmes existentes
#         genres = (
#             Genero.objects
#             .filter(filmes__isnull=False)  # Apenas com filmes associados
#             .distinct()  # Sem duplicações
#             .order_by("nome")  # Ordenado alfabeticamente
#         )

#         # Serializar com nome e descrição
#         genre_list = [
#             {
#                 "nome": g.nome,
#                 "descricao": g.descricao,
#             }
#             for g in genres
#         ]

#         return Response(
#             {
#                 "total": len(genre_list),
#                 "genres": genre_list,
#             },
#             status=status.HTTP_200_OK,
#         )

#     except Exception as e:
#         return Response(
#             {"error": "Erro ao obter géneros.", "detail": str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )
    




# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def watched_movies(request):
#     """
#     Endpoint para obter a lista de filmes que o utilizador autenticado já visualizou.
    
#     Requisitos cumpridos:
#     - RF-09: Histórico de Interação
#     - RF-02: Autenticação (apenas utilizadores autenticados)
#     - RF-04: Explorar Catálogo
    
#     GET /api/movies/watched/
    
#     Autenticação: Obrigatória (Bearer Token JWT)
    
#     Response (HTTP 200 - Com histórico):
#     {
#         "total": 5,
#         "results": [
#             {
#                 "tmdb_id": 550,
#                 "titulo": "Fight Club",
#                 "descricao": "An insomniac office worker...",
#                 "poster_url": "https://image.tmdb.org/t/p/w500/...",
#                 "generos": ["Drama", "Thriller"],
#                 "tmdb_rating": 8.8,
#                 "user_rating": 9,
#                 "review": "Filme excelente!",
#                 "visto": true
#             },
#             ...
#         ]
#     }
    
#     Response (HTTP 200 - Sem histórico):
#     {
#         "total": 0,
#         "results": []
#     }
    
#     Response (HTTP 401):
#     {"detail": "As credenciais de autenticação não foram fornecidas."}
    
#     Comportamento:
#     - Filtra apenas filmes com visto=True do utilizador autenticado
#     - Ordenação decrescente por ID (mais recente primeiro)
#     - Ignora itens inválidos, continua processamento
#     - Valida relação utilizador-filme
#     - Queries otimizadas (select_related, prefetch_related)
#     - Sem falhas por dados inválidos
#     """
    
#     user = request.user
    
#     try:
#         # Buscar todas as atividades do utilizador com filmes marcados como visto
#         # select_related otimiza a relação com Filme (join)
#         # prefetch_related otimiza a relação ManyToMany com Generos
#         atividades = (
#             AtividadeUsuario.objects
#             .filter(usuario=user, visto=True)
#             .select_related('filme')
#             .prefetch_related('filme__generos')
#             .order_by('-id')  # Ordenação decrescente por ID (mais recente primeiro)
#         )
        
#         # Construir lista de resposta com tratamento robusto de erros
#         watched_list = []
        
#         for atividade in atividades:
#             try:
#                 # Validar existência do filme (relação integridade)
#                 if not atividade.filme:
#                     continue  # Ignorar se filme não existe
                
#                 filme = atividade.filme
                
#                 # Construir objeto de resposta com dados essenciais
#                 watched_item = {
#                     "tmdb_id": filme.id,
#                     "titulo": filme.nome if filme.nome else "Sem título",
#                     "descricao": filme.descricao if filme.descricao else "",
#                     "poster_url": tmdb_image_url(filme.poster_path),
#                     "generos": [g.nome for g in filme.generos.all()],
#                     "tmdb_rating": filme.rating if filme.rating is not None else None,
#                     "user_rating": atividade.rating if atividade.rating is not None else None,
#                     "review": atividade.review if atividade.review else None,
#                     "visto": atividade.visto,
#                 }
                
#                 watched_list.append(watched_item)
                
#             except Exception as e:
#                 # Ignorar itens inválidos e continuar processamento
#                 # Evita falhas por dados corrompidos ou faltantes
#                 continue
        
#         # Retornar resposta estruturada
#         return Response({
#             "total": len(watched_list),
#             "results": watched_list
#         }, status=status.HTTP_200_OK)
    
#     except Exception as e:
#         # Erro crítico no processamento (raro com try/except interno)
#         return Response(
#             {"error": "Erro ao obter histórico de visualizações", "detail": str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
    


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_favorite(request):
#     """
#     Endpoint para adicionar um filme à lista de favoritos do utilizador autenticado.
    
#     Requisitos cumpridos:
#     - RF-08: Favoritos / Watchlist
#     - RF-02: Autenticação (apenas utilizadores autenticados)
#     - RF-06: Detalhe de Item
    
#     POST /api/movies/favorites/add/
    
#     Autenticação: Obrigatória (Bearer Token JWT)
    
#     Request Body:
#     {
#         "movie_id": 550
#     }
    
#     Response (HTTP 201 - Sucesso):
#     {
#         "message": "Filme adicionado aos favoritos com sucesso",
#         "favorite": {
#             "tmdb_id": 550,
#             "titulo": "Fight Club",
#             "descricao": "An insomniac office worker...",
#             "poster_url": "https://image.tmdb.org/t/p/w500/...",
#             "generos": ["Drama", "Thriller"],
#             "tmdb_rating": 8.8,
#             "user_rating": null,
#             "favorito": true,
#             "visto": false,
#             "ver_mais_tarde": false
#         }
#     }
    
#     Response (HTTP 400 - Filme já nos favoritos):
#     {
#         "error": "Este filme já está na sua lista de favoritos"
#     }
    
#     Response (HTTP 404 - Filme não existe):
#     {
#         "error": "Filme não encontrado na base de dados"
#     }
    
#     Response (HTTP 400 - Input inválido):
#     {
#         "error": "movie_id é obrigatório"
#     }
    
#     Response (HTTP 401 - Não autenticado):
#     {"detail": "As credenciais de autenticação não foram fornecidas."}
    
#     Comportamento:
#     - Valida presença e tipo do movie_id
#     - Verifica existência do filme na BD
#     - Previne duplicados (filme já favorito)
#     - Cria registo AtividadeUsuario com favorito=True
#     - Retorna dados completos do filme em caso de sucesso
#     - Queries otimizadas (select_related, prefetch_related)
#     - Mensagens de erro claras e específicas
#     - Conformidade com código existente
#     """
    
#     user = request.user
#     data = request.data
    
#     # Validar presença do movie_id
#     if "movie_id" not in data:
#         return Response(
#             {"error": "movie_id é obrigatório"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     # Validar tipo e extrair movie_id
#     try:
#         movie_id = int(data["movie_id"])
#         if movie_id <= 0:
#             raise ValueError("movie_id deve ser positivo")
#     except (ValueError, TypeError):
#         return Response(
#             {"error": "movie_id deve ser um inteiro válido e positivo"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     # Verificar existência do filme na base de dados
#     try:
#         filme = Filme.objects.select_related().prefetch_related('generos').get(id=movie_id)
#     except Filme.DoesNotExist:
#         return Response(
#             {"error": "Filme não encontrado na base de dados"},
#             status=status.HTTP_404_NOT_FOUND
#         )
    
#     # Verificar se o filme já está nos favoritos do utilizador
#     atividade_existente = AtividadeUsuario.objects.filter(
#         usuario=user,
#         filme=filme,
#         favorito=True
#     ).first()
    
#     if atividade_existente:
#         return Response(
#             {"error": "Este filme já está na sua lista de favoritos"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     # Criar ou atualizar registo de atividade
#     atividade, created = AtividadeUsuario.objects.update_or_create(
#         usuario=user,
#         filme=filme,
#         defaults={"favorito": True}
#     )
    
#     # Serializar resposta com dados completos do filme
#     filme_data = serialize_movie(filme, atividade)
    
#     return Response({
#         "message": "Filme adicionado aos favoritos com sucesso",
#         "favorite": filme_data
#     }, status=status.HTTP_201_CREATED)



# @api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
# def remove_favorite(request):
#     """
#     Endpoint para remover um filme da lista de favoritos do utilizador autenticado.
    
#     Requisitos cumpridos:
#     - RF-08: Favoritos / Watchlist
#     - RF-02: Autenticação (apenas utilizadores autenticados)
#     - RF-06: Detalhe de Item
    
#     DELETE /api/movies/favorites/remove/
    
#     Autenticação: Obrigatória (Bearer Token JWT)
    
#     Request Body ou Query Parameter:
#     {
#         "movie_id": 550
#     }
#     OU
#     ?movie_id=550
    
#     Response (HTTP 200 - Sucesso):
#     {
#         "message": "Filme removido dos favoritos com sucesso",
#         "movie_id": 550,
#         "titulo": "Fight Club"
#     }
    
#     Response (HTTP 400 - Filme não está nos favoritos):
#     {
#         "error": "Este filme não está na sua lista de favoritos"
#     }
    
#     Response (HTTP 404 - Filme não existe):
#     {
#         "error": "Filme não encontrado na base de dados"
#     }
    
#     Response (HTTP 400 - Input inválido):
#     {
#         "error": "movie_id é obrigatório"
#     }
    
#     Response (HTTP 401 - Não autenticado):
#     {"detail": "As credenciais de autenticação não foram fornecidas."}
    
#     Comportamento:
#     - Aceita movie_id no corpo (JSON) ou em parâmetro query
#     - Valida presença e tipo do movie_id
#     - Verifica existência do filme na BD
#     - Verifica se o filme está efetivamente na lista de favoritos
#     - Remove apenas o flag favorito, mantendo o registo de atividade
#     - Operação idempotente: removição repetida sempre segura
#     - Queries otimizadas (select_related, prefetch_related)
#     - Mensagens de erro claras e específicas
#     - Conformidade com código existente
#     """
    
#     user = request.user
    
#     # Obter movie_id do corpo do pedido ou de query parameter
#     movie_id = None
    
#     if request.method == 'DELETE':
#         # Tentar obter do corpo do pedido (JSON)
#         if request.data:
#             movie_id = request.data.get("movie_id")
        
#         # Se não encontrou no corpo, tentar query parameter
#         if movie_id is None:
#             movie_id = request.GET.get("movie_id")
    
#     # Validar presença do movie_id
#     if movie_id is None:
#         return Response(
#             {"error": "movie_id é obrigatório"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     # Validar tipo e extrair movie_id
#     try:
#         movie_id = int(movie_id)
#         if movie_id <= 0:
#             raise ValueError("movie_id deve ser positivo")
#     except (ValueError, TypeError):
#         return Response(
#             {"error": "movie_id deve ser um inteiro válido e positivo"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     # Verificar existência do filme na base de dados
#     try:
#         filme = Filme.objects.get(id=movie_id)
#     except Filme.DoesNotExist:
#         return Response(
#             {"error": "Filme não encontrado na base de dados"},
#             status=status.HTTP_404_NOT_FOUND
#         )
    
#     # Verificar se o filme está realmente na lista de favoritos do utilizador
#     try:
#         atividade = AtividadeUsuario.objects.get(
#             usuario=user,
#             filme=filme,
#             favorito=True
#         )
#     except AtividadeUsuario.DoesNotExist:
#         return Response(
#             {"error": "Este filme não está na sua lista de favoritos"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     # Remover o filme dos favoritos (apenas atualizar flag, manter histórico)
#     atividade.favorito = False
#     atividade.save()
    
#     return Response({
#         "message": "Filme removido dos favoritos com sucesso",
#         "movie_id": filme.id,
#         "titulo": filme.nome
#     }, status=status.HTTP_200_OK)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def list_favorites(request):
#     """
#     Endpoint para obter a lista completa de filmes favoritos (watchlist) do utilizador autenticado.
    
#     Requisitos cumpridos:
#     - RF-08: Favoritos / Watchlist
#     - RF-02: Autenticação (apenas utilizadores autenticados)
    
#     GET /api/movies/favorites/
    
#     Autenticação: Obrigatória (Bearer Token JWT)
    
#     Query Parameters (Opcionais):
#     - page: Número da página (padrão: 1)
#     - page_size: Itens por página (padrão: 50, máximo: 100)
    
#     Response (HTTP 200 - Com favoritos):
#     {
#         "total": 5,
#         "page": 1,
#         "page_size": 50,
#         "results": [
#             {
#                 "tmdb_id": 550,
#                 "titulo": "Fight Club",
#                 "descricao": "An insomniac office worker...",
#                 "poster_url": "https://image.tmdb.org/t/p/w500/...",
#                 "generos": ["Drama", "Thriller"],
#                 "tmdb_rating": 8.8,
#                 "user_rating": 9,
#                 "favorito": true,
#                 "visto": false,
#                 "ver_mais_tarde": false
#             },
#             ...
#         ]
#     }
    
#     Response (HTTP 200 - Sem favoritos):
#     {
#         "total": 0,
#         "page": 1,
#         "page_size": 50,
#         "results": []
#     }
    
#     Response (HTTP 401 - Não autenticado):
#     {"detail": "As credenciais de autenticação não foram fornecidas."}
    
#     Comportamento:
#     - Filtra apenas filmes com favorito=True do utilizador autenticado
#     - Ordenação decrescente por ID (mais recente primeiro)
#     - Ignora itens com filmes inexistentes (integridade)
#     - Paginação suportada (opcional)
#     - Queries otimizadas (select_related, prefetch_related)
#     - Segurança: Apenas acesso ao próprio histórico de favoritos
#     - Sem falhas por dados inconsistentes
#     """
    
#     user = request.user
    
#     try:
#         # Buscar todas as atividades do utilizador com filmes marcados como favorito
#         # select_related otimiza a relação com Filme (join)
#         # prefetch_related otimiza a relação ManyToMany com Generos
#         atividades_query = (
#             AtividadeUsuario.objects
#             .filter(usuario=user, favorito=True)
#             .select_related('filme')
#             .prefetch_related('filme__generos')
#             .order_by('-id')  # Ordenação decrescente por ID (mais recente primeiro)
#         )
        
#         # Suporte a paginação manual
#         page = int(request.GET.get('page', 1))
#         page_size = int(request.GET.get('page_size', 50))
        
#         # Validar parâmetros de paginação
#         if page < 1:
#             page = 1
#         if page_size < 1:
#             page_size = 50
#         if page_size > 100:
#             page_size = 100
        
#         # Calcular offsets
#         start = (page - 1) * page_size
#         end = start + page_size
        
#         # Contar total antes da paginação
#         total_count = atividades_query.count()
        
#         # Aplicar paginação
#         atividades_paginadas = atividades_query[start:end]
        
#         # Construir lista de resposta com tratamento robusto de erros
#         favorites_list = []
        
#         for atividade in atividades_paginadas:
#             try:
#                 # Validar existência do filme (relação integridade)
#                 if not atividade.filme:
#                     continue  # Ignorar se filme não existe
                
#                 # Serializar com função existente do projeto
#                 filme_data = serialize_movie(atividade.filme, atividade)
                
#                 favorites_list.append(filme_data)
                
#             except Exception as e:
#                 # Ignorar itens inválidos e continuar processamento
#                 # Evita falhas por dados corrompidos ou faltantes
#                 continue
        
#         # Retornar resposta estruturada com suporte a paginação
#         return Response({
#             "total": total_count,
#             "page": page,
#             "page_size": page_size,
#             "results": favorites_list
#         }, status=status.HTTP_200_OK)
    
#     except ValueError:
#         # Erro na conversão de parâmetros de paginação
#         return Response(
#             {"error": "Parâmetros de paginação inválidos. page e page_size devem ser inteiros."},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     except Exception as e:
#         # Erro crítico no processamento
#         return Response(
#             {"error": "Erro ao obter lista de favoritos", "detail": str(e)},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# ################ AI
