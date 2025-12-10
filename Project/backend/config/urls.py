"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import routers
from api.views import *
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

# Router para ViewSets
router = routers.DefaultRouter()
router.register(r'favorites', FavoriteViewSet, basename='favorite')

@api_view(['GET'])
def api_status(request):
    return Response({'status': 'Django + React conectados com sucesso!'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/status/', api_status, name='api-status'),
    
    # ViewSets (Router)
    path('api/', include(router.urls)),

    # API endpoints
    
    # Catálogo (RF-04, RF-05)
    path('api/movies/catalogue/', MovieCatalogueView.as_view(), name='movie_catalogue'),
    
    path('api/movies/search/', search_movies, name='search_movies'),
    path('api/movies/search/tmdb/', search_movies_tmdb, name='search_movies_tmdb'),
    path('api/movies/<int:movie_id>/', movie_details),
    path("api/movies/trending/", trending_movies, name="trending_movies"),
    path("api/movies/rate/", rate_movie, name="rate_movie"),
    # path("api/movies/rate_tmdb/", rate_tmdb_movie),
    # path("api/movies/my-rated/", my_rated_movies, name="my_rated_movies"),
    # path("api/movies/rate/<int:tmdb_id>/", update_rating, name="update_rating"),
    # path("api/movies/rate/<int:tmdb_id>/delete/", delete_rating, name="delete_rating"),

    # path("api/movies/genres/", get_genres),
    # path("api/movies/by_genres/", get_genres),

    # path("api/movies/filter_by_rating/", filter_by_rating),

    # path("api/movies/watched/", watched_movies),
    path("api/movies/mark_watched/", MarkWatchedView.as_view(), name="mark_watched"),
    # path("api/movies/unmark_watched/", unmark_watched),

    # path("api/movies/favorites/", list_favorites),
    # path("api/movies/add_favorite/", add_favorite),
    # path("api/movies/remove_favorite/", remove_favorite),
    # path("api/movies/catalog/",movies_catalog),
    # path("api/movies/history/",history),
    # path("api/movies/<int:tmdb_id>/review/", add_review),
    # path("api/movies/<int:tmdb_id>/review/delete/", delete_review),
    # path("api/movies/<int:tmdb_id>/reviews/", list_reviews),
    # path('api/movies/recommendations/', recommendations_view, name='movie-recommendations'),


    # path("api/movies/watch_later/add/", add_watch_later),
    # path("api/movies/watch_later/remove/", remove_watch_later),
    # path("api/movies/watch_later/", list_watch_later),
    path("api/movies/details/<int:movie_id>/", movie_details, name="movie_details"),



    # Authentication endpoints
    path('api/auth/register/', register, name='register'),
    path('api/auth/login/', login, name='login'),
    path('api/auth/logout/', logout, name='logout'),
    path('api/auth/me/', user_me, name='user_me'),
    path('api/auth/me/update/', user_me_update, name='user_me_update'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Legacy routes for backwards compatibility
    path('api/user/info/', UserInfo, name='user_info'),
    path('api/user/update/', UpdateProfile, name='update_profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
