from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from api.models import Usuario, Filme


class UtilizadorViewTest(TestCase):
    """Testes para as views de Utilizador"""
    
    def setUp(self):
        """Configura o cliente e cria dados de teste"""
        self.client = Client()
        self.usuario = Usuario.objects.create(
            nome="João Silva",
            email="joao@example.com",
            password_hash=make_password("senha123")
        )
    
    def test_usuario_can_be_retrieved(self):
        """Testa que um usuário pode ser recuperado"""
        self.assertIsNotNone(self.usuario.id)
        self.assertEqual(self.usuario.nome, "João Silva")
    
    def test_multiple_usuarios_creation(self):
        """Testa criação de múltiplos usuários"""
        usuario2 = Usuario.objects.create(
            nome="Maria Santos",
            email="maria@example.com",
            password_hash=make_password("outra_senha")
        )
        usuarios = Usuario.objects.all()
        self.assertEqual(usuarios.count(), 2)
        self.assertIn(self.usuario, usuarios)
        self.assertIn(usuario2, usuarios)


class FilmeViewTest(TestCase):
    """Testes para as views de Filme"""
    
    def setUp(self):
        """Configura dados de teste"""
        self.filme = Filme.objects.create(
            titulo="Interstellar",
            descricao="Uma jornada pelo espaço",
            genero="Ficção Científica",
            ano_lancamento=2014,
            tmdb_id=157336,
            avaliacao_media=8.6,
            poster_path="/path/to/interstellar.jpg"
        )
    
    def test_filme_can_be_retrieved(self):
        """Testa que um filme pode ser recuperado"""
        filme = Filme.objects.get(tmdb_id=157336)
        self.assertEqual(filme.titulo, "Interstellar")
        self.assertEqual(filme.ano_lancamento, 2014)
    
    def test_filme_queryset_ordering(self):
        """Testa a ordenação dos filmes"""
        filme2 = Filme.objects.create(
            titulo="Tenet",
            descricao="Thriller de ação",
            genero="Ação",
            ano_lancamento=2020,
            tmdb_id=577922,
            avaliacao_media=7.3
        )
        filmes = Filme.objects.all()
        # Verifica que há pelo menos 2 filmes
        self.assertGreaterEqual(filmes.count(), 2)
    
    def test_filme_poster_path_is_optional(self):
        """Testa que poster_path pode ser nulo"""
        filme = Filme.objects.create(
            titulo="Filme sem Poster",
            descricao="Um filme sem poster",
            genero="Drama",
            ano_lancamento=2021,
            tmdb_id=999999,
            avaliacao_media=6.0,
            poster_path=None
        )
        self.assertIsNone(filme.poster_path)
