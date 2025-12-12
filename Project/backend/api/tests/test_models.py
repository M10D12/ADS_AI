from django.test import TestCase
from django.contrib.auth.hashers import make_password
from api.models import Usuario, Filme, AtividadeUsuario


class UsuarioModelTest(TestCase):
    """Testes para o modelo Usuario"""
    
    def setUp(self):
        """Cria um usuário para testes"""
        self.usuario = Usuario.objects.create(
            nome="João Silva",
            email="joao@example.com",
            password_hash=make_password("senha123")
        )
    
    def test_usuario_creation(self):
        """Testa criação de um usuário"""
        self.assertEqual(self.usuario.nome, "João Silva")
        self.assertEqual(self.usuario.email, "joao@example.com")
        self.assertTrue(self.usuario.is_authenticated)
    
    def test_usuario_email_unique(self):
        """Testa que email é único"""
        with self.assertRaises(Exception):
            Usuario.objects.create(
                nome="Maria",
                email="joao@example.com",
                password_hash=make_password("outra_senha")
            )
    
    def test_usuario_timestamps(self):
        """Testa que timestamps são criados corretamente"""
        self.assertIsNotNone(self.usuario.created_at)
        self.assertIsNotNone(self.usuario.updated_at)
        self.assertEqual(self.usuario.created_at, self.usuario.updated_at)
    
    def test_usuario_str_representation(self):
        """Testa a representação em string do usuário"""
        self.assertEqual(str(self.usuario), self.usuario.nome)


class FilmeModelTest(TestCase):
    """Testes para o modelo Filme"""
    
    def setUp(self):
        """Cria um filme para testes"""
        self.filme = Filme.objects.create(
            nome="Inception",
            descricao="Um filme sobre sonhos dentro de sonhos",
            ano_lancamento=2010,
            rating_tmdb=8.8,
            poster_path="/path/to/poster.jpg"
        )
    
    def test_filme_creation(self):
        """Testa criação de um filme"""
        self.assertEqual(self.filme.nome, "Inception")
        self.assertEqual(self.filme.ano_lancamento, 2010)
        self.assertEqual(self.filme.rating_tmdb, 8.8)
    
    def test_filme_fields_are_optional(self):
        """Testa que campos opcionais podem ser nulos"""
        filme = Filme.objects.create(
            nome="Filme Mínimo",
            descricao=None,
            ano_lancamento=None,
            rating_tmdb=None,
            poster_path=None
        )
        self.assertIsNone(filme.descricao)
        self.assertIsNone(filme.ano_lancamento)
        self.assertIsNone(filme.rating_tmdb)
    
    def test_filme_avaliacao_range(self):
        """Testa que avaliação está no intervalo correto"""
        self.assertGreaterEqual(self.filme.avaliacao_media, 0)
        self.assertLessEqual(self.filme.avaliacao_media, 10)


class AtividadeUsuarioTest(TestCase):
    """Testes para o modelo AtividadeUsuario"""
    
    def setUp(self):
        """Cria dados necessários para testes"""
        self.usuario = Usuario.objects.create(
            nome="João Silva",
            email="joao@example.com",
            password_hash=make_password("senha123")
        )
        self.filme = Filme.objects.create(
            titulo="The Matrix",
            descricao="Um clássico de ficção científica",
            genero="Ficção Científica",
            ano_lancamento=1999,
            tmdb_id=603,
            avaliacao_media=8.7
        )
        self.atividade = AtividadeUsuario.objects.create(
            usuario=self.usuario,
            filme=self.filme,
            tipo_atividade="assistido"
        )
    
    def test_atividade_creation(self):
        """Testa criação de uma atividade"""
        self.assertEqual(self.atividade.usuario, self.usuario)
        self.assertEqual(self.atividade.filme, self.filme)
        self.assertEqual(self.atividade.tipo_atividade, "assistido")
    
    def test_atividade_timestamps(self):
        """Testa que timestamps são criados corretamente"""
        self.assertIsNotNone(self.atividade.data_atividade)
        self.assertIsNotNone(self.atividade.created_at)
