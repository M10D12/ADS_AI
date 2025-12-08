from django.core.management.base import BaseCommand
from api.models import Filme, Genero
from django.conf import settings
import requests
import time


def tmdb_request(endpoint, params=None):
    """Faz pedido à API da TMDB com a API key."""
    base_url = "https://api.themoviedb.org/3"
    params = params or {}
    params["api_key"] = settings.TMDB_API_KEY
    response = requests.get(f"{base_url}/{endpoint}", params=params)
    return response.json()


class Command(BaseCommand):
    help = "Popula a base de dados com filmes recentes da TMDB (apenas rating > 0 e com poster)."

    def handle(self, *args, **kwargs):
        self.stdout.write("➡ A obter filmes mais recentes...")

        filmes_guardados = 0
        page = 1

        # 🔥 Buscar géneros uma vez (muito mais rápido)
        generos_tmdb = tmdb_request("genre/movie/list").get("genres", [])
        generos_map = {g["id"]: g["name"] for g in generos_tmdb}

        while filmes_guardados < 100:
            data = tmdb_request("discover/movie", {
                "sort_by": "release_date.desc",
                "page": page
            })

            results = data.get("results", [])
            if not results:
                break

            for movie in results:
                tmdb_id = movie["id"]
                rating_tmdb = movie.get("vote_average", 0)
                poster_path = movie.get("poster_path")

                # 🛑 Ignorar filmes sem rating ou sem poster
                if rating_tmdb == 0 or not poster_path:
                    continue

                # 📥 Tentar descarregar a capa
                capa_bin = b""
                img_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

                try:
                    img_resp = requests.get(img_url, timeout=5)
                    if img_resp.status_code == 200:
                        capa_bin = img_resp.content
                    else:
                        continue
                except:
                    continue  # poster inválido ou timeout

                # Criar filme
                filme, created = Filme.objects.get_or_create(
                    id=tmdb_id,
                    defaults={
                        "nome": movie.get("title"),
                        "descricao": movie.get("overview", "") or "",
                        "poster_path": poster_path,
                        "rating": rating_tmdb,
                        "capa": capa_bin,
                    }
                )

                # Associar géneros reais
                for gid in movie.get("genre_ids", []):
                    nome_genero = generos_map.get(gid, f"Genero {gid}")
                    genero, _ = Genero.objects.get_or_create(
                        nome=nome_genero,
                        defaults={"descricao": ""}
                    )
                    filme.generos.add(genero)

                if created:
                    filmes_guardados += 1
                    

                if filmes_guardados >= 500:
                    break

            page += 1
            time.sleep(0.2)  # evitar rate limit

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Foram guardados {filmes_guardados} filmes (rating > 0 e com poster)."
            )
        )
