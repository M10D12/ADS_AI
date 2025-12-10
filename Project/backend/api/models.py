from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Usuario(models.Model):
    """
    Modelo para representar um utilizador do sistema.
    
    Requisito R01: Gestão de Utilizadores
    - Suporta registo e autenticação
    - Email único para cada utilizador
    - Password armazenada com hash compatível com Django
    """
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(
        max_length=512,
        help_text="Nome completo do utilizador"
    )
    email = models.EmailField(
        max_length=512,
        unique=True,
        help_text="Email único para autenticação"
    )
    password_hash = models.CharField(
        max_length=512,
        help_text="Password hasheada com algoritmo do Django"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de criação da conta"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora da última atualização"
    )
    
    class Meta:
        verbose_name = "Utilizador"
        verbose_name_plural = "Utilizadores"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['-created_at']),
        ]
    
    @property
    def is_authenticated(self):
        """Compatibilidade com sistema de autenticação do Django."""
        return True
    
    def __str__(self):
        return f"{self.nome} ({self.email})"


class Genero(models.Model):
    """
    Modelo para representar um género de filme.
    
    Requisito R02: Gestão de Catálogo
    - Cada filme pode ter múltiplos géneros
    - Géneros reutilizáveis e padronizados
    """
    nome = models.CharField(
        max_length=512,
        primary_key=True,
        help_text="Nome do género (único)"
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição detalhada do género"
    )
    
    class Meta:
        verbose_name = "Género"
        verbose_name_plural = "Géneros"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
        ]
    
    def __str__(self):
        return self.nome


class Filme(models.Model):
    """
    Modelo para representar um filme no catálogo.
    
    Requisito R02: Gestão de Catálogo
    Requisito R03: Pesquisa
    Requisito R04: Avaliações (relação com AtividadeUsuario)
    Requisito R05: Sistema de Recomendações (rating TMDB e genres)
    
    - Título, sinopse, capa, ano, géneros
    - Rating médio calculado a partir das avaliações
    - Suporta pesquisa por título, sinopse e géneros
    """
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(
        max_length=512,
        help_text="Título do filme"
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        help_text="Sinopse ou descrição detalhada do filme"
    )
    ano_lancamento = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(2100),
        ],
        help_text="Ano de lançamento do filme"
    )
    generos = models.ManyToManyField(
        Genero,
        related_name='filmes',
        help_text="Géneros associados ao filme"
    )
    rating_tmdb = models.FloatField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(10.0),
        ],
        help_text="Rating do filme na TMDB (0-10)"
    )
    poster_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Caminho/URL do poster na TMDB"
    )
    capa = models.BinaryField(
        blank=True,
        null=True,
        help_text="Imagem da capa em formato binário"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de adição ao catálogo"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora da última atualização"
    )
    
    class Meta:
        verbose_name = "Filme"
        verbose_name_plural = "Filmes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['-rating_tmdb']),
            models.Index(fields=['-created_at']),
        ]
    
    def get_rating_medio_usuarios(self):
        """
        Calcula o rating médio do filme a partir das avaliações dos utilizadores.
        
        Requisito R04: Avaliações
        Requisito R05: Recomendações (filtra ratings > 7.5)
        
        Returns:
            float: Rating médio (0-10), ou None se sem avaliações
        """
        from django.db.models import Avg
        
        avg_rating = AtividadeUsuario.objects.filter(
            filme=self,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        
        return round(avg_rating, 2) if avg_rating is not None else None
    
    def get_numero_avaliacoes(self):
        """
        Retorna o número total de avaliações que o filme recebeu.
        
        Returns:
            int: Número de avaliações
        """
        return AtividadeUsuario.objects.filter(
            filme=self,
            rating__isnull=False
        ).count()
    
    def get_numero_visualizacoes(self):
        """
        Retorna o número total de utilizadores que marcaram como visto.
        
        Requisito R09: Histórico
        
        Returns:
            int: Número de visualizações
        """
        return AtividadeUsuario.objects.filter(
            filme=self,
            visto=True
        ).count()
    
    @property
    def rating(self):
        """
        Compatibilidade: retorna rating_tmdb se existir, senão tenta rating da BD.
        """
        try:
            # Tentar obter rating_tmdb (novo campo)
            if hasattr(self, '_rating_tmdb'):
                return self._rating_tmdb
            # Se não, retornar o campo original 'rating' da BD
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT rating FROM api_filme WHERE id = %s",
                    [self.id]
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except:
            return getattr(self, '_rating_tmdb', None)
    
    def __str__(self):
        return f"{self.nome} ({self.ano_lancamento or 'N/A'})"


class AtividadeUsuario(models.Model):
    """
    Modelo para registar todas as interações do utilizador com filmes.
    
    Requisito R04: Avaliações (0-10)
    Requisito R08: Favoritos / Watchlist
    Requisito R09: Histórico de Interação
    
    Consolida numa única tabela:
    - Avaliações (rating 0-10)
    - Favoritos (flag boolean)
    - Filmes vistos (flag boolean)
    - Ver mais tarde / Watchlist (flag boolean)
    - Reviews/Comentários de utilizadores
    - Timestamps para histórico
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='atividades',
        help_text="Utilizador que realizou a atividade"
    )
    filme = models.ForeignKey(
        Filme,
        on_delete=models.CASCADE,
        related_name='atividades_usuarios',
        help_text="Filme alvo da atividade"
    )
    rating = models.SmallIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
        help_text="Avaliação do utilizador (0-10)"
    )
    visto = models.BooleanField(
        default=False,
        help_text="Marcado como visto pelo utilizador"
    )
    favorito = models.BooleanField(
        default=False,
        help_text="Marcado como favorito"
    )
    ver_mais_tarde = models.BooleanField(
        default=False,
        help_text="Adicionado à lista 'Ver Mais Tarde' (watchlist)"
    )
    review = models.TextField(
        blank=True,
        null=True,
        help_text="Comentário/review do utilizador sobre o filme"
    )
    data_visualizacao = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e hora em que o filme foi marcado como visto"
    )
    data_adicao_favoritos = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e hora em que foi adicionado aos favoritos"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de criação do registo de atividade"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora da última atualização"
    )
    
    class Meta:
        verbose_name = "Atividade de Utilizador"
        verbose_name_plural = "Atividades de Utilizadores"
        unique_together = ('usuario', 'filme')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['usuario', 'favorito']),
            models.Index(fields=['usuario', 'visto']),
            models.Index(fields=['usuario', 'rating']),
            models.Index(fields=['usuario', 'ver_mais_tarde']),
            models.Index(fields=['filme', 'rating']),
            models.Index(fields=['-updated_at']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Override do save para atualizar timestamps automáticos.
        """
        if self.visto and not self.data_visualizacao:
            self.data_visualizacao = timezone.now()
        
        if self.favorito and not self.data_adicao_favoritos:
            self.data_adicao_favoritos = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.usuario.nome} → {self.filme.nome}"


class Favorito(models.Model):
    """
    Modelo alternativo explícito para Favoritos/Watchlist.
    
    Requisito R08: Favoritos / Watchlist
    
    Nota: Este modelo é opcional. O projeto atual usa AtividadeUsuario.favorito
    para gerir favoritos. Este modelo pode ser usado como alternativa se necessário
    separação explícita, ou para histórico auditável de favoritos.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='favoritos',
        help_text="Utilizador que marcou como favorito"
    )
    filme = models.ForeignKey(
        Filme,
        on_delete=models.CASCADE,
        related_name='favoritado_por',
        help_text="Filme marcado como favorito"
    )
    data_adicao = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de adição aos favoritos"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de apresentação na lista (0 = recente primeiro)"
    )
    
    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"
        unique_together = ('usuario', 'filme')
        ordering = ['-data_adicao']
        indexes = [
            models.Index(fields=['usuario', '-data_adicao']),
            models.Index(fields=['filme']),
        ]
    
    def __str__(self):
        return f"{self.usuario.nome} → ❤️ {self.filme.nome}"


class HistoricoVisualizacao(models.Model):
    """
    Modelo para registar o histórico detalhado de visualizações.
    
    Requisito R09: Histórico de Interação
    
    Nota: Este modelo é opcional. O projeto atual usa AtividadeUsuario.visto
    e data_visualizacao. Este modelo pode ser usado para auditoria detalhada
    ou para rastrear múltiplas visualizações do mesmo filme.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='historico_visualizacoes',
        help_text="Utilizador que visualizou"
    )
    filme = models.ForeignKey(
        Filme,
        on_delete=models.CASCADE,
        related_name='visualizacoes',
        help_text="Filme visualizado"
    )
    data_visualizacao = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora da visualização"
    )
    minuto_parado = models.IntegerField(
        blank=True,
        null=True,
        help_text="Minuto em que o utilizador parou (para funcionalidades futuras)"
    )
    completo = models.BooleanField(
        default=True,
        help_text="Se o filme foi visualizado completamente"
    )
    
    class Meta:
        verbose_name = "Histórico de Visualização"
        verbose_name_plural = "Históricos de Visualização"
        ordering = ['-data_visualizacao']
        indexes = [
            models.Index(fields=['usuario', '-data_visualizacao']),
            models.Index(fields=['filme', '-data_visualizacao']),
        ]
    
    def __str__(self):
        return f"{self.usuario.nome} viu {self.filme.nome} em {self.data_visualizacao.strftime('%d/%m/%Y %H:%M')}"


class Avaliacao(models.Model):
    """
    Modelo explícito para Avaliações (alternativa a usar AtividadeUsuario.rating).
    
    Requisito R04: Avaliações
    Requisito R05: Recomendações (filtra ratings > 7.5)
    
    Nota: O projeto atual consolida avaliações em AtividadeUsuario.rating.
    Este modelo pode ser usado se necessária separação explícita ou auditoria.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        help_text="Utilizador que avaliou"
    )
    filme = models.ForeignKey(
        Filme,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        help_text="Filme avaliado"
    )
    rating = models.SmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
        help_text="Classificação do filme (0-10)"
    )
    comentario = models.TextField(
        blank=True,
        null=True,
        help_text="Comentário/review detalhado"
    )
    data_avaliacao = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora da avaliação"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora da última atualização"
    )
    
    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        unique_together = ('usuario', 'filme')
        ordering = ['-data_avaliacao']
        indexes = [
            models.Index(fields=['usuario', 'rating']),
            models.Index(fields=['filme', 'rating']),
            models.Index(fields=['-data_avaliacao']),
        ]
    
    def __str__(self):
        return f"{self.usuario.nome} deu {self.rating}/10 a {self.filme.nome}"