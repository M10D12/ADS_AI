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


#Pesquisa de filmes por um ou + género
@api_view(["GET"])
def movies_by_genres(request):
    user = request.user if request.user.is_authenticated else None

    genres_param = request.GET.get("genres")

    if not genres_param:
        return Response({"error": "É necessário fornecer ?genres=ID1,ID2"}, status=400)

    # Converter os IDs TMDB
    try:
        genre_ids = [int(g.strip()) for g in genres_param.split(",")]
    except:
        return Response({"error": "IDs de género inválidos"}, status=400)

    # Buscar tabela oficial TMDB para converter IDs → nomes
    tmdb_genres = tmdb_request("genre/movie/list").get("genres", [])
    tmdb_map = {g["id"]: g["name"] for g in tmdb_genres}

    # Converter ids TMDB → nomes reais usados na BD
    genre_names = [tmdb_map.get(gid) for gid in genre_ids if gid in tmdb_map]

    if not genre_names:
        return Response({"error": "Nenhum género encontrado para os IDs fornecidos"}, status=400)

    
    filmes_bd = (
        Filme.objects.filter(generos__nome__in=genre_names)
        .prefetch_related("generos")
        .distinct()
    )

    resultado = []
    ids_existentes = set()

    for filme in filmes_bd:
        atividade = None
        if user:
            atividade = AtividadeUsuario.objects.filter(usuario=user, filme=filme).first()

        filme_dict = serialize_movie(filme, atividade)
        filme_dict["source"] = "database"
        resultado.append(filme_dict)

        ids_existentes.add(filme.id)

    genre_string = ",".join(map(str, genre_ids))
    tmdb_data = tmdb_request(f"discover/movie", {"with_genres": genre_string})

    for movie in tmdb_data.get("results", []):
        tmdb_id = movie["id"]

        if tmdb_id in ids_existentes:
            continue

        filme, _ = Filme.objects.get_or_create(
            id=tmdb_id,
            defaults={
                "nome": movie.get("title"),
                "descricao": movie.get("overview", ""),
                "poster_path": movie.get("poster_path"),
                "rating": movie.get("vote_average"),
                "capa": b"",
            }
        )

        atividade = None
        if user:
            atividade = AtividadeUsuario.objects.filter(usuario=user, filme=filme).first()

        filme_dict = serialize_movie(filme, atividade)
        filme_dict["source"] = "tmdb"
        resultado.append(filme_dict)

        ids_existentes.add(tmdb_id)

    return Response({
        "genres_requested": genre_ids,
        "genre_names": genre_names,
        "total": len(resultado),
        "filmes": resultado
    })


@api_view(["GET"])
def filter_movies_by_rating(request):
    user = request.user if request.user.is_authenticated else None

    min_rating = float(request.GET.get("min", 0))
    max_rating = float(request.GET.get("max", 10))

    filmes_bd = (
        Filme.objects.filter(
            rating__gte=min_rating,
            rating__lte=max_rating
        )
        .prefetch_related("generos")
    )

    resultado = []
    ids_existentes = set()

    for filme in filmes_bd:
        atividade = None
        if user:
            atividade = AtividadeUsuario.objects.filter(
                usuario=user, filme=filme
            ).first()

        filme_dict = serialize_movie(filme, atividade)
        filme_dict["source"] = "database"
        resultado.append(filme_dict)

        ids_existentes.add(filme.id)

    MINIMO = 20  

    if len(resultado) < MINIMO:
        tmdb_data = tmdb_request("discover/movie", {
            "vote_average.gte": min_rating,
            "vote_average.lte": max_rating
        })

        for movie in tmdb_data.get("results", []):
            tmdb_id = movie["id"]

            if tmdb_id in ids_existentes:
                continue  # evitar duplicados

            filme, _ = Filme.objects.get_or_create(
                id=tmdb_id,
                defaults={
                    "nome": movie.get("title"),
                    "descricao": movie.get("overview", ""),
                    "poster_path": movie.get("poster_path"),
                    "rating": movie.get("vote_average"),
                    "capa": b"",
                }
            )

            atividade = None
            if user:
                atividade = AtividadeUsuario.objects.filter(
                    usuario=user, filme=filme
                ).first()

            filme_dict = serialize_movie(filme, atividade)
            filme_dict["source"] = "tmdb"  
            resultado.append(filme_dict)

            ids_existentes.add(tmdb_id)

            if len(resultado) >= MINIMO:
                break

   
    return Response({
        "min_rating": min_rating,
        "max_rating": max_rating,
        "total": len(resultado),
        "filmes": resultado
    })



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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendations(request):
    user = request.user

    interesses = set(
        AtividadeUsuario.objects
        .filter(usuario=user, rating__gte=6.5)
        .values_list("filme__generos__nome", flat=True)
    )


    if not interesses:
        return Response({
            "message": "Sem géneros de interesse identificados para recomendações"
        })

    genero_stats=(
        AtividadeUsuario.objects
        .filter(usuario=user, rating__gte=7.5)
        .values("filme__generos__nome")
        .annotate(
            count=Count("filme__generos__nome"),
            avg_rating=Avg("rating")
        )
    )

    genero_pesos = {}

    for g in genero_stats:
        nome = g["filme__generos__nome"]
        count = g["count"]
        avg_rating = g["avg_rating"]

        peso = log(1 + count) * avg_rating
        genero_pesos[nome] = peso

    candidatos = (
        Filme.objects
        .filter(generos__nome__in=interesses)
        .exclude(atividadeusuario__usuario=user)
        .prefetch_related("generos")
        .distinct()
    )[:50] 

    generos_por_filme = {
        filme.id: [g.nome for g in filme.generos.all()]
        for filme in candidatos
    }

    def peso_do_filme(filme):
        return sum(genero_pesos.get(g, 0) for g in generos_por_filme[filme.id])

    filmes_ordenados = sorted(candidatos, key=peso_do_filme, reverse=True)


    filmes_principais = filmes_ordenados[:24]

    trending = tmdb_request("trending/movie/week").get("results", [])
    tmdb_genres = tmdb_request("genre/movie/list").get("genres", [])
    genre_dict = {g["id"]: g["name"] for g in tmdb_genres}

    trending_filtro = []

    for movie in trending:

        tmdb_id = movie.get("id")
        if not tmdb_id:
            continue

        if AtividadeUsuario.objects.filter(usuario=user, filme__id=tmdb_id).exists():
            continue

        genre_ids = movie.get("genre_ids", [])
        movie_genre_names = {genre_dict.get(gid) for gid in genre_ids if gid in genre_dict}

        if not movie_genre_names.intersection(interesses):

            details = movie
            if not details or not details.get("title"):
                continue

            trending_filtro.append(details)

            if len(trending_filtro) >= 20:
                break

    dif = trending_filtro[:6]

    final = []
    i = 0
    d = 0

    while i < len(filmes_principais) or d < len(dif):

        if i < len(filmes_principais):
            final.append(filmes_principais[i])
            i += 1

        if i % 4 == 0 and d < len(dif): 
            final.append(dif[d])
            d += 1

    result = []

    for item in final:
        if isinstance(item, Filme):
            result.append({
                "id": item.id,
                "titulo": item.nome,
                "poster": tmdb_image_url(item.poster_path),
                "rating": item.rating,
                "source": "bd",
                "generos": [g.nome for g in item.generos.all()],
                "motivo": "Recomendado com base nos seus géneros mais avaliados."
            })
            continue

        if isinstance(item, dict):

            tmdb_id = item.get("id")
            if not tmdb_id:
                continue

            details = tmdb_request(f"movie/{tmdb_id}")
            if not details or not details.get("title"):
                continue

            generos = [g["name"] for g in details.get("genres", [])]

            result.append({
                "id": tmdb_id,
                "titulo": details.get("title"),
                "poster": tmdb_image_url(details.get("poster_path")),
                "rating": details.get("vote_average"),
                "source": "tmdb",
                "generos": generos,
                "motivo": "Trending global — adicionado para diversidade."
            })
            continue

    return Response({"total": len(result), "recomendacoes": result,"pesos": genero_pesos})
