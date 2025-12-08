from django.db import models

class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=512)
    password_hash = models.CharField(max_length=512)
    email = models.CharField(max_length=512, blank=True, null=True)
    
    @property
    def is_authenticated(self):
        return True
    
    def __str__(self):
        return self.nome


class Genero(models.Model):
    nome = models.CharField(max_length=512, primary_key=True)
    descricao = models.TextField()

    def __str__(self):
        return self.nome


class Filme(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=512)
    descricao = models.TextField()
    rating = models.FloatField(blank=True, null=True)
    generos = models.ManyToManyField(Genero, related_name='filmes')  
    capa = models.BinaryField()
    poster_path = models.CharField(max_length=512, blank=True, null=True)   

    
    def __str__(self):
        return self.nome


class AtividadeUsuario(models.Model):
    rating = models.SmallIntegerField(blank=True, null=True)
    visto = models.BooleanField(default=False)
    favorito = models.BooleanField(default=False)
    filme = models.ForeignKey(Filme, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    ver_mais_tarde = models.BooleanField(default=False)
    review=models.TextField(null=True)

    class Meta:
        unique_together = ('filme', 'usuario')

    def __str__(self):
        return f"{self.usuario.nome} - {self.filme.nome}"
