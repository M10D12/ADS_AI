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

def tmdb_image_url(path):
    if path:
        return f"https://image.tmdb.org/t/p/w500{path}"
    return None

def serialize_movie(filme, atividade=None):
    tmdb_rating = filme.rating if filme.rating is not None else None
    user_rating = atividade.rating if atividade else None

    return {
        "tmdb_id": filme.id,
        "titulo": filme.nome,
        "descricao": filme.descricao,
        "poster_url": tmdb_image_url(filme.poster_path),
        "generos": [g.nome for g in filme.generos.all()],

        "tmdb_rating": tmdb_rating,
        "user_rating": user_rating,

        "favorito": atividade.favorito if atividade else False,
        "visto": atividade.visto if atividade else False,
        "ver_mais_tarde": atividade.ver_mais_tarde if atividade else False,
    }



@api_view(["POST"])
def CreateAccount(request):
    data = request.data
    
    if "email" not in data or "nome" not in data:
        return Response({"message": "Email e Nome são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)

    
    if "password" in data:
        data["password_hash"] = make_password(data.pop("password"))
    else:
        return Response({"message": "Password obrigatória"}, status=status.HTTP_400_BAD_REQUEST)


    if Usuario.objects.filter(email=data["email"]).exists():
        return Response({"message": "Email já registado"}, status=status.HTTP_400_BAD_REQUEST)

    user = UsuarioSerializer(data=data)
    
    if user.is_valid():
        saved_user = user.save()
        return Response({
            "id": saved_user.id,
            "nome": saved_user.nome,
            "email": saved_user.email
        }, status=status.HTTP_201_CREATED)
        
    return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def Login(request):
    data = request.data
    
    if "email" not in data or "password" not in data:
        return Response({"message": "Credenciais Incompletas"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = Usuario.objects.get(email=data["email"])
    except Usuario.DoesNotExist:
        return Response({"message":"Credenciais Inválidas"},status=status.HTTP_401_UNAUTHORIZED)
    
    if check_password(data["password"],user.password_hash):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return Response({
            "Acess_token":str(access),
            "Refresh_token":str(refresh),
        },status=status.HTTP_200_OK) 
        
    else:
        return Response({"message":"Credenciais Inválidas"},status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def UserInfo(request):
    user = request.user
    return Response({
        "user_id":user.id,
        "nome":user.nome,
        "email":user.email
    })

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def UpdateProfile(request):
    user = request.user
    data = request.data
    try:
        if "nome" in data:
            user.nome = data["nome"]

        if "email" in data:
            if Usuario.objects.exclude(id=user.id).filter(email=data["email"]).exists():
                return Response(
                    {"error": "Email já está em uso"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = data["email"]

        if "password" in data:
            user.password_hash = make_password(data["password"])

        user.save()
        return Response({
            "message": "Perfil atualizado",
            "user": {
                "id": user.id,
                "nome": user.nome,
                "email": user.email
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "Erro ao atualizar perfil", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



def tmdb_request(endpoint, params=None):
    base_url = "https://api.themoviedb.org/3"
    if params is None:
        params = {}
    params['api_key'] = settings.TMDB_API_KEY
    response = requests.get(f"{base_url}/{endpoint}", params=params)
    return response.json()  


@api_view(['GET'])
def search_movies(request):
    query = request.GET.get('q', '')
    if not query:
        return Response({"error": "Query parameter is required."}, status=400)
    
    data = tmdb_request("search/movie", params={"query": query})
    return Response(data)


@api_view(['GET'])
def movie_details(request, movie_id):
    """
    Devolve detalhes do filme, preferindo a BD local.
    Se não existir na BD:
        - Vai buscar a TMDB
        - Guarda automaticamente o filme na BD (cache)
    Inclui estado do utilizador:
        - rating_user
        - favorito
        - visto
        - ver_mais_tarde
    """

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
            "tmdb_rating": filme.rating,
            "poster_url": tmdb_image_url(filme.poster_path),

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
        rating=tmdb_rating,
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
        "tmdb_rating": filme.rating,
        "poster_url": tmdb_image_url(filme.poster_path),
        "rating_user": rating_user,
        "favorito": favorito,
        "visto": visto,
        "ver_mais_tarde": ver_mais_tarde,

        "source": "tmdb_cached"
    })










#Trending Movies
#ENDPOINT PARA TESTE http://127.0.0.1:8000/api/movies/trending/?period=Z     Z=  day  ou week

@api_view(['GET'])
def trending_movies(request):
    period = request.GET.get('period', 'day')

    if period not in ['day', 'week']:
        return Response(
            {"error": "Period must be 'day' or 'week'."},
            status=400
        )

    # trending bruto (sem info completa)
    raw = tmdb_request(f"trending/movie/{period}").get("results", [])

    detailed_movies = []

    # buscar detalhes completos do TMDB
    for m in raw[:20]:  # limitar para performance
        movie_id = m.get("id")
        if not movie_id:
            continue

        details = tmdb_request(f"movie/{movie_id}")

        # ignorar filmes sem título → não existem na TMDB
        if not details.get("title"):
            continue

        detailed_movies.append({
            "id": details["id"],
            "title": details["title"],
            "overview": details.get("overview"),
            "poster_url": tmdb_image_url(details.get("poster_path")),
            "rating": details.get("vote_average"),
            "genres": [g["name"] for g in details.get("genres", [])]
        })

    return Response({
        "total": len(detailed_movies),
        "results": detailed_movies
    })




#Rate Movie
#ADD RATING A UM FILME DA TMDB E GUARDA NA BD 
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_tmdb_movie(request):
    user = request.user
    data = request.data

    if "tmdb_id" not in data or "rating" not in data:
        return Response({"error": "tmdb_id e rating são obrigatórios"}, status=400)

    tmdb_id = data["tmdb_id"]
    rating = int(data["rating"])

    if not (1 <= rating <= 10):
        return Response({"error": "Rating deve estar entre 1 e 10"}, status=400)

    # procura filme na TMDB
    tmdb_data = tmdb_request(f"movie/{tmdb_id}")
    if "id" not in tmdb_data:
        return Response({"error": "Filme não encontrado na TMDB"}, status=404)

    titulo = tmdb_data.get("title", "Sem título")
    descricao = tmdb_data.get("overview", "")
    generos_tmdb = tmdb_data.get("genres", [])
    poster_path = tmdb_data.get("poster_path")

    
    capa_bin = b""
    if poster_path:
        img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        img_resp = requests.get(img_url)
        if img_resp.status_code == 200:
            capa_bin = img_resp.content

    # Criar filme na BD
    filme, created = Filme.objects.get_or_create(
        id=tmdb_id,
        defaults={
            "nome": titulo,
            "descricao": descricao,
            "rating": None,
            "capa": capa_bin,
            "poster_path": poster_path,
        }
    )

    # Guardar géneros
    for g in generos_tmdb:
        genre, _ = Genero.objects.get_or_create(
            nome=g["name"],
            defaults={"descricao": ""}
        )
        filme.generos.add(genre)

    # Atualizar rating do user
    atividade, created_act = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={"rating": rating}
    )

    return Response({
        "message": "Rating registado" if created_act else "Rating atualizado",
        "filme": filme.nome,
        "rating": rating
    })

#My Rated Movies
#ENDPOINT PARA OBTER A LISTA DE FILMES AVALIADOS PELO USER
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_rated_movies(request):
    user = request.user

    atividades = (
        AtividadeUsuario.objects
        .filter(usuario=user, rating__isnull=False)
        .select_related("filme")
        .prefetch_related("filme__generos")
    )

    resultado = [
        serialize_movie(atividade.filme, atividade)
        for atividade in atividades
    ]

    return Response({"filmes": resultado})



#Editar o rating
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_rating(request, tmdb_id):
    user = request.user
    data = request.data

    if "rating" not in data:
        return Response({"error": "rating é obrigatório"}, status=400)

    rating = int(data["rating"])

    if not (1 <= rating <= 10):
        return Response({"error": "Rating deve estar entre 1 e 10"}, status=400)

    try:
        filme = Filme.objects.get(id=tmdb_id)
    except Filme.DoesNotExist:
        return Response({"error": "Filme não encontrado"}, status=404)

    atividade, _ = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={"rating": rating}
    )

    return Response({
        "message": "Rating atualizado",
        "filme": filme.nome,
        "rating": rating
    })


#Delete Rating
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_rating(request, tmdb_id):
    user = request.user

    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme__id=tmdb_id)
    except AtividadeUsuario.DoesNotExist:
        return Response({"error": "Este filme não tem rating registado pelo user"}, status=404)

    atividade.rating = None
    atividade.save()

    return Response({"message": "Rating removido com sucesso"})




#Filtragem de movies por género 

#Disponibiliza todos os generos que estão no TMDB
@api_view(["GET"])
def get_genres(request):
    """
    Devolve todos os géneros disponíveis na TMDB para que o frontend
    possa criar filtros por género.
    """
    try:
        response = tmdb_request("genre/movie/list")
        genres = response.get("genres", [])

        # Apenas devolvemos id + nome, limpo
        return Response({
            "total": len(genres),
            "genres": genres
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)




#marcar e desmarcar filmes vistos

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_watched(request):
    user = request.user
    tmdb_id = request.data.get("tmdb_id")

    if not tmdb_id:
        return Response({"error": "tmdb_id é obrigatório"}, status=400)

    filme, _ = Filme.objects.get_or_create(id=tmdb_id)

    atividade, _ = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={"visto": True}
    )

    return Response({"message": "Filme marcado como visto"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unmark_watched(request):
    user = request.user
    tmdb_id = request.data.get("tmdb_id")

    if not tmdb_id:
        return Response({"error": "tmdb_id é obrigatório"}, status=400)

    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme_id=tmdb_id)
        atividade.visto = False
        atividade.save()
    except AtividadeUsuario.DoesNotExist:
        return Response({"error": "Filme não estava marcado como visto"}, status=404)

    return Response({"message": "Filme removido dos vistos"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_watched(request):
    user = request.user

    atividades = (
        AtividadeUsuario.objects
        .filter(usuario=user, visto=True)
        .select_related("filme")
    )

    filmes = [
        serialize_movie(a.filme, a)
        for a in atividades
    ]

    return Response({"watched": filmes})



#marcar e desmarcar filmes favoritos

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_favorite(request):
    user = request.user
    tmdb_id = request.data.get("tmdb_id")

    if not tmdb_id:
        return Response({"error": "tmdb_id é obrigatório"}, status=400)

    filme, _ = Filme.objects.get_or_create(id=tmdb_id)

    atividade, _ = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={"favorito": True}
    )

    return Response({"message": "Adicionado aos favoritos"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_favorite(request):
    user = request.user
    tmdb_id = request.data.get("tmdb_id")

    if not tmdb_id:
        return Response({"error": "tmdb_id é obrigatório"}, status=400)

    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme_id=tmdb_id)
        atividade.favorito = False
        atividade.save()
    except AtividadeUsuario.DoesNotExist:
        return Response({"error": "Filme não estava nos favoritos"}, status=404)

    return Response({"message": "Removido dos favoritos"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_favorites(request):
    user = request.user

    atividades = (
        AtividadeUsuario.objects
        .filter(usuario=user, favorito=True)
        .select_related("filme")
    )

    filmes = [
        serialize_movie(a.filme, a)
        for a in atividades
    ]

    return Response({"favorites": filmes})



@api_view(["GET"])
def movies_catalog(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    # Calcular offsets
    start = (page - 1) * page_size
    end = start + page_size

    # Buscar total
    total_filmes = Filme.objects.count()

    # Buscar filmes paginados
    filmes = Filme.objects.all().order_by("id")[start:end]

    filmes_formatados = [
        {
            "tmdb_id": f.id,
            "titulo": f.nome,
            "descricao": f.descricao,
            "poster_url": tmdb_image_url(f.poster_path),
            "rating_tmdb": f.rating,   # rating guardado do TMDB
            "generos": [g.nome for g in f.generos.all()],
        }
        for f in filmes
    ]

    return Response({
        "page": page,
        "page_size": page_size,
        "total_results": total_filmes,
        "filmes": filmes_formatados
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history(request):
    user = request.user

    atividades = (
        AtividadeUsuario.objects
        .filter(usuario=user)
        .select_related("filme")
    )

    resultado = []

    for a in atividades:
        filme_data = serialize_movie(a.filme, a)

        filme_data["tipo"] = (
            "rating" if a.rating is not None else
            "visto" if a.visto else
            "favorito" if a.favorito else
            "ver_mais_tarde" if a.ver_mais_tarde else
            "atividade"
        )

        resultado.append(filme_data)

    return Response({
        "total": len(resultado),
        "history": resultado
    })




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_watch_later(request):
    user = request.user
    tmdb_id = request.data.get("tmdb_id")

    if not tmdb_id:
        return Response({"error": "tmdb_id é obrigatório"}, status=400)

    filme, _ = Filme.objects.get_or_create(id=tmdb_id)

    atividade, _ = AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={"ver_mais_tarde": True}
    )

    return Response({"message": "Adicionado à lista Ver Mais Tarde"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_watch_later(request):
    user = request.user
    tmdb_id = request.data.get("tmdb_id")

    if not tmdb_id:
        return Response({"error": "tmdb_id é obrigatório"}, status=400)

    try:
        atividade = AtividadeUsuario.objects.get(usuario=user, filme_id=tmdb_id)
        atividade.ver_mais_tarde = False
        atividade.save()
    except AtividadeUsuario.DoesNotExist:
        return Response({"error": "Filme não estava na lista Ver Mais Tarde"}, status=404)

    return Response({"message": "Removido da lista Ver Mais Tarde"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_watch_later(request):
    user = request.user

    atividades = (
        AtividadeUsuario.objects
        .filter(usuario=user, ver_mais_tarde=True)
        .select_related("filme")
    )

    filmes = [
        serialize_movie(a.filme, a)
        for a in atividades
    ]

    return Response({"watch_later": filmes})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_review(request, tmdb_id):
    user= request.user
    review_text= request.data.get("review")

    if review_text is None or review_text.strip() == "":
        return Response({"error":"review não pode ser vazia"},status=400)
    
    filme,_= Filme.objects.get_or_create(id=tmdb_id)

    atividade, created= AtividadeUsuario.objects.update_or_create(
        usuario=user,
        filme=filme,
        defaults={"review":review_text}
    )

    return Response({
        "message":"Review adicionada" if created else "Review atualizada",
        "filme":filme.nome,
        "review":review_text
    })

@api_view(["GET"])
def list_reviews(request, tmdb_id):
    atividades = (
        AtividadeUsuario.objects
        .filter(filme_id=tmdb_id)
        .select_related("usuario")
    )

    reviews = [
        {
            "user_id": a.usuario.id,
            "user_nome": a.usuario.nome,
            "comentario": a.review
        }
        for a in atividades
    ]

    return Response({
        "tmdb_id": tmdb_id,
        "total_reviews": len(reviews),
        "reviews": reviews
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_review(request, tmdb_id):
    user= request.user

    try:
        atividade= AtividadeUsuario.objects.get(
            usuario=user,
            filme__id=tmdb_id,
        )
    except AtividadeUsuario.DoesNotExist:
        return Response({"error":"Review não encontrada"},status=404)
    
    atividade.review= None
    atividade.save()

    return Response({"message":"Review removida com sucesso"})


########################################### AI

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_movie_recommendations(request):
    """
    Endpoint de recomendações personalizadas para utilizador autenticado.
    
    RF-10 (Motor de Recomendação): Recomendações baseadas em avaliações > 7.5
    RF-11 (Tendências/Populares): Fallback para filmes populares se < 3 avaliações
    
    Casos de teste:
    - >= 3 avaliações positivas: recomendações por género
    - < 3 avaliações positivas: filmes populares como fallback
    - Sem filmes recomendáveis: lista vazia
    - Não autenticado: HTTP 401 Unauthorized
    
    Performance: tempo resposta ≤ 800ms
    """
    user = request.user
    
    # Buscar avaliações positivas do utilizador (rating > 7.5)
    high_ratings = AtividadeUsuario.objects.filter(
        usuario=user,
        rating__gt=7.5
    ).select_related('filme').prefetch_related('filme__generos')
    
    num_high_ratings = high_ratings.count()
    
    # Obter IDs de filmes que o utilizador já avaliou (para exclusão)
    filmes_avaliados_ids = AtividadeUsuario.objects.filter(
        usuario=user,
        rating__isnull=False
    ).values_list('filme_id', flat=True)
    
    # Caso 1: Utilizador tem >= 3 avaliações positivas
    if num_high_ratings >= 3:
        # Extrair géneros dos filmes bem avaliados usando tuple (hashable)
        generos_ids = tuple()
        
        for atividade in high_ratings:
            filme = atividade.filme
            for genero in filme.generos.all():
                if genero.nome not in generos_ids:
                    generos_ids = generos_ids + (genero.nome,)
        
        if generos_ids:
            # Filmes com géneros similares, excluindo os já avaliados
            filmes_recomendados = (
                Filme.objects
                .filter(generos__nome__in=generos_ids)
                .exclude(id__in=filmes_avaliados_ids)
                .prefetch_related('generos')
                .distinct()
                .order_by('-rating')[:20]
            )
        else:
            filmes_recomendados = Filme.objects.none()
    
    # Caso 2: Utilizador tem < 3 avaliações positivas (fallback para populares)
    else:
        # Filmes populares (maior rating do TMDB), excluindo os já avaliados
        filmes_recomendados = (
            Filme.objects
            .exclude(id__in=filmes_avaliados_ids)
            .prefetch_related('generos')
            .order_by('-rating')[:20]
        )
    
    # Serializar filmes recomendados
    resultado = []
    for filme in filmes_recomendados:
        filme_dict = {
            "tmdb_id": filme.id,
            "titulo": filme.nome,
            "descricao": filme.descricao,
            "poster_url": tmdb_image_url(filme.poster_path),
            "rating_tmdb": filme.rating,
            "generos": [g.nome for g in filme.generos.all()],
        }
        resultado.append(filme_dict)
    
    return Response({
        "num_user_ratings": num_high_ratings,
        "recommendation_type": "personalized" if num_high_ratings >= 3 else "popular",
        "total": len(resultado),
        "recommendations": resultado
    })


def recommendations_view(request):
    """Alias para compatibilidade com urls.py"""
    return get_movie_recommendations(request)




class RatingFilterPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100


@api_view(["GET"])
def filter_by_rating(request):
    """
    GET /api/movies/filter_by_rating/?min_rating=<float>&max_rating=<float>&page=<int>&page_size=<int>

    Filters films by the average user rating (average of AtividadeUsuario.rating).
    - min_rating and max_rating are optional (defaults: 0 and 10).
    - Values must be numeric and in [0, 10].
    - Returns paginated JSON response with film info and avg_user_rating.
    - Validation errors return HTTP 400 with a clear message.
    """
    # Parse query parameters with sensible defaults
    min_raw = request.GET.get("min_rating", "")
    max_raw = request.GET.get("max_rating", "")

    # Default values
    if min_raw == "":
        min_rating = 0.0
    else:
        try:
            min_rating = float(min_raw)
        except (TypeError, ValueError):
            return Response(
                {"error": "min_rating must be a number between 0 and 10."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if max_raw == "":
        max_rating = 10.0
    else:
        try:
            max_rating = float(max_raw)
        except (TypeError, ValueError):
            return Response(
                {"error": "max_rating must be a number between 0 and 10."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Validate ranges
    if not (0.0 <= min_rating <= 10.0):
        return Response(
            {"error": "min_rating must be between 0 and 10."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not (0.0 <= max_rating <= 10.0):
        return Response(
            {"error": "max_rating must be between 0 and 10."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if min_rating > max_rating:
        return Response(
            {"error": "min_rating cannot be greater than max_rating."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Build queryset: annotate with avg user rating and filter by it.
    # Exclude films without user ratings (avg_user_rating is NULL).
    films_qs = (
        Filme.objects
        .annotate(avg_user_rating=Avg("atividadeusuario__rating"))
        .filter(
            avg_user_rating__isnull=False,
            avg_user_rating__gte=min_rating,
            avg_user_rating__lte=max_rating,
        )
        .prefetch_related("generos")
        .order_by("-avg_user_rating", "-rating", "id")
    )

    # Pagination
    paginator = RatingFilterPagination()
    page = paginator.paginate_queryset(films_qs, request)

    # Serialization helper
    def _serialize(film):
        return {
            "tmdb_id": film.id,
            "titulo": film.nome,
            "descricao": film.descricao,
            "poster_url": tmdb_image_url(film.poster_path),
            "rating_tmdb": film.rating,
            "avg_user_rating": round(getattr(film, "avg_user_rating", 0.0), 2),
            "generos": [g.nome for g in film.generos.all()],
        }

    results = [_serialize(f) for f in page] if page is not None else []

    # Total matching results for client-side pagination
    total_matching = films_qs.count()

    response_payload = {
        "min_rating": min_rating,
        "max_rating": max_rating,
        "total_results": total_matching,
        "page": int(request.GET.get("page", 1)),
        "page_size": paginator.get_page_size(request) or paginator.page_size,
        "results": results,
    }

    return Response(response_payload, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_genres(request):
    """
    GET /api/movies/genres/

    Devolve a lista completa de géneros existentes na base de dados local,
    associados a filmes reais. Ordenados alfabeticamente, sem duplicações.

    RF-02 (Gestão de Catálogo): Fornece catálogo de géneros disponíveis.
    RF-05 (Pesquisa e Filtro): Suporta filtros dinâmicos por género.
    US03 & US05: Permite ao frontend carregar géneros para seleção.

    Retorna:
        {
            "total": <int>,
            "genres": [
                {"nome": "Ação", "descricao": "..."},
                {"nome": "Comédia", "descricao": "..."},
                ...
            ]
        }
    """
    try:
        # Buscar apenas géneros associados a filmes existentes
        genres = (
            Genero.objects
            .filter(filmes__isnull=False)  # Apenas com filmes associados
            .distinct()  # Sem duplicações
            .order_by("nome")  # Ordenado alfabeticamente
        )

        # Serializar com nome e descrição
        genre_list = [
            {
                "nome": g.nome,
                "descricao": g.descricao,
            }
            for g in genres
        ]

        return Response(
            {
                "total": len(genre_list),
                "genres": genre_list,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": "Erro ao obter géneros.", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


################ AI