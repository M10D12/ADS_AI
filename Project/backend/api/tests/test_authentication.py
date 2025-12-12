from django.test import TestCase
from django.contrib.auth.hashers import make_password, check_password
from api.models import Usuario


class AuthenticationTest(TestCase):
    """Testes para autenticação de usuários"""
    
    def setUp(self):
        """Cria um usuário para testes de autenticação"""
        self.email = "teste@example.com"
        self.senha = "senha_segura_123"
        self.usuario = Usuario.objects.create(
            nome="Usuário Teste",
            email=self.email,
            password_hash=make_password(self.senha)
        )
    
    def test_password_hashing(self):
        """Testa que a senha é armazenada hasheada"""
        self.assertNotEqual(self.usuario.password_hash, self.senha)
    
    def test_password_verification(self):
        """Testa que a senha pode ser verificada"""
        senha_correta = check_password(self.senha, self.usuario.password_hash)
        self.assertTrue(senha_correta)
    
    def test_wrong_password_fails(self):
        """Testa que uma senha incorreta não verifica"""
        senha_errada = check_password("senha_errada", self.usuario.password_hash)
        self.assertFalse(senha_errada)
    
    def test_usuario_authentication_property(self):
        """Testa a propriedade is_authenticated"""
        self.assertTrue(self.usuario.is_authenticated)
    
    def test_email_retrieval_for_authentication(self):
        """Testa recuperação de usuário por email"""
        usuario_encontrado = Usuario.objects.get(email=self.email)
        self.assertEqual(usuario_encontrado.id, self.usuario.id)
        self.assertEqual(usuario_encontrado.nome, "Usuário Teste")
