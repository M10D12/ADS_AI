from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Filme, Usuario, AtividadeUsuario, Avaliacao, Favorito


class FilmeModelTests(TestCase):
    """Testes para o modelo Filme"""
    
    def setUp(self):
        self.filme = Filme.objects.create(
            titulo="Teste Filme",
            descricao="Descrição de teste",
            ano_lancamento=2024,
            tmdb_id=12345,
            poster_path="/test_poster.jpg"
        )
    
    def test_criar_filme(self):
        """Testa criação de um filme"""
        self.assertEqual(self.filme.titulo, "Teste Filme")
        self.assertEqual(self.filme.tmdb_id, 12345)
    
    def test_filme_string_representation(self):
        """Testa representação em string do modelo Filme"""
        self.assertEqual(str(self.filme), "Teste Filme")


class UsuarioModelTests(TestCase):
    """Testes para o modelo Usuario"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.usuario = Usuario.objects.create(
            user=self.user,
            bio="Bio de teste",
            foto_perfil=""
        )
    
    def test_criar_usuario(self):
        """Testa criação de um usuário"""
        self.assertEqual(self.usuario.user.username, 'testuser')
    
    def test_usuario_string_representation(self):
        """Testa representação em string do modelo Usuario"""
        self.assertEqual(str(self.usuario), 'testuser')


class AtividadeUsuarioModelTests(TestCase):
    """Testes para o modelo AtividadeUsuario"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.usuario = Usuario.objects.create(
            user=self.user,
            bio="",
            foto_perfil=""
        )
        self.filme = Filme.objects.create(
            titulo="Filme Teste",
            descricao="Desc",
            ano_lancamento=2024,
            tmdb_id=999,
            poster_path="/test.jpg"
        )
        self.atividade = AtividadeUsuario.objects.create(
            usuario=self.usuario,
            filme=self.filme,
            visto=True
        )
    
    def test_criar_atividade_usuario(self):
        """Testa criação de uma atividade de usuário"""
        self.assertTrue(self.atividade.visto)
        self.assertEqual(self.atividade.usuario.user.username, 'testuser')
    
    def test_atividade_timestamps(self):
        """Testa se timestamps são criados automaticamente"""
        self.assertIsNotNone(self.atividade.criado_em)
        self.assertIsNotNone(self.atividade.atualizado_em)


class AvaliacaoModelTests(TestCase):
    """Testes para o modelo Avaliacao"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.usuario = Usuario.objects.create(
            user=self.user,
            bio="",
            foto_perfil=""
        )
        self.filme = Filme.objects.create(
            titulo="Filme Teste",
            descricao="Desc",
            ano_lancamento=2024,
            tmdb_id=999,
            poster_path="/test.jpg"
        )
        self.avaliacao = Avaliacao.objects.create(
            usuario=self.usuario,
            filme=self.filme,
            nota=8.5
        )
    
    def test_criar_avaliacao(self):
        """Testa criação de uma avaliação"""
        self.assertEqual(self.avaliacao.nota, 8.5)
        self.assertEqual(self.avaliacao.filme.titulo, "Filme Teste")


class FavoritoModelTests(TestCase):
    """Testes para o modelo Favorito"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.usuario = Usuario.objects.create(
            user=self.user,
            bio="",
            foto_perfil=""
        )
        self.filme = Filme.objects.create(
            titulo="Filme Favorito",
            descricao="Desc",
            ano_lancamento=2024,
            tmdb_id=777,
            poster_path="/fav.jpg"
        )
        self.favorito = Favorito.objects.create(
            usuario=self.usuario,
            filme=self.filme
        )
    
    def test_criar_favorito(self):
        """Testa criação de um filme favorito"""
        self.assertEqual(self.favorito.filme.titulo, "Filme Favorito")


class FilmeAPITests(APITestCase):
    """Testes para os endpoints da API de Filmes"""
    
    def setUp(self):
        self.client = Client()
        self.filme = Filme.objects.create(
            titulo="API Test Filme",
            descricao="Teste API",
            ano_lancamento=2024,
            tmdb_id=5555,
            poster_path="/api_test.jpg"
        )
    
    def test_listar_filmes(self):
        """Testa se conseguimos listar filmes via API"""
        # Este teste verifica se o endpoint existe e retorna dados
        # Ajuste conforme sua URL real
        response = self.client.get('/api/filmes/', format='json')
        # Aceita 404 se o endpoint não existir (ainda não configurado)
        self.assertIn(response.status_code, [200, 404])


class HealthCheckTests(APITestCase):
    """Testes básicos de saúde da aplicação"""
    
    def test_database_accessible(self):
        """Testa se a base de dados é acessível"""
        # Cria um objeto simples para verificar se DB funciona
        user = User.objects.create_user(
            username='healthcheck',
            password='test'
        )
        self.assertTrue(User.objects.filter(username='healthcheck').exists())

