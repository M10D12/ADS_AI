from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Usuario, Filme, Genero, AtividadeUsuario, Favorito


# ============================================================================
# SERIALIZERS DE GÉNERO
# ============================================================================

class GeneroSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Genero.
    
    Requisito R02: Gestão de Catálogo
    - Expõe nome e descrição do género
    - Utilisável como nested serializer em FilmeSerializer
    """
    class Meta:
        model = Genero
        fields = ['nome', 'descricao']
        read_only_fields = ['nome']


class GeneroSimplificadoSerializer(serializers.ModelSerializer):
    """
    Versão simplificada de GeneroSerializer para respostas compactas.
    """
    class Meta:
        model = Genero
        fields = ['nome']
        read_only_fields = ['nome']


# ============================================================================
# SERIALIZERS DE FILME
# ============================================================================

class FilmeSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Filme.
    
    Requisito R02: Gestão de Catálogo
    Requisito R03: Pesquisa
    Requisito R04: Avaliações (inclui métodos para calcular ratings)
    Requisito R05: Recomendações
    
    - Inclui aninhamento de géneros
    - Calcula rating médio a partir das avaliações
    - Conta número de avaliações e visualizações
    - Apropriado para responses complexas
    """
    generos = GeneroSimplificadoSerializer(many=True, read_only=True)
    rating_medio_usuarios = serializers.SerializerMethodField(
        read_only=True,
        help_text="Rating médio calculado a partir das avaliações dos utilizadores"
    )
    numero_avaliacoes = serializers.SerializerMethodField(
        read_only=True,
        help_text="Total de avaliações recebidas"
    )
    numero_visualizacoes = serializers.SerializerMethodField(
        read_only=True,
        help_text="Total de utilizadores que marcaram como visto"
    )
    
    class Meta:
        model = Filme
        fields = [
            'id',
            'nome',
            'descricao',
            'ano_lancamento',
            'generos',
            'rating_tmdb',
            'rating_medio_usuarios',
            'numero_avaliacoes',
            'numero_visualizacoes',
            'poster_path',
            'capa',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'capa',
            'created_at',
            'updated_at',
            'rating_medio_usuarios',
            'numero_avaliacoes',
            'numero_visualizacoes',
        ]
    
    def get_rating_medio_usuarios(self, obj):
        """Calcula rating médio do filme."""
        return obj.get_rating_medio_usuarios()
    
    def get_numero_avaliacoes(self, obj):
        """Retorna número de avaliações."""
        return obj.get_numero_avaliacoes()
    
    def get_numero_visualizacoes(self, obj):
        """Retorna número de visualizações."""
        return obj.get_numero_visualizacoes()


class FilmeResumidoSerializer(serializers.ModelSerializer):
    """
    Versão simplificada de FilmeSerializer para listas e responses compactas.
    
    Requisito R02: Gestão de Catálogo
    - Expõe apenas campos essenciais
    - Otimizado para performance em listas grandes
    """
    generos = GeneroSimplificadoSerializer(many=True, read_only=True)
    rating_medio_usuarios = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Filme
        fields = [
            'id',
            'nome',
            'descricao',
            'ano_lancamento',
            'generos',
            'rating_tmdb',
            'rating_medio_usuarios',
            'poster_path',
        ]
        read_only_fields = fields
    
    def get_rating_medio_usuarios(self, obj):
        """Calcula rating médio do filme."""
        return obj.get_rating_medio_usuarios()


# ============================================================================
# SERIALIZERS DE UTILIZADOR
# ============================================================================

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Usuario.
    
    Requisito R01: Gestão de Utilizadores
    - Expõe informações públicas do utilizador
    - Password é write-only para segurança
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Password (write-only)"
    )
    password_hash = serializers.CharField(read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'nome',
            'email',
            'password',
            'password_hash',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'password_hash',
            'created_at',
            'updated_at',
        ]
    
    def create(self, validated_data):
        """
        Cria um novo utilizador com password hasheada.
        """
        password = validated_data.pop('password', None)
        usuario = Usuario(**validated_data)
        
        if password:
            usuario.password_hash = make_password(password)
        
        usuario.save()
        return usuario
    
    def update(self, instance, validated_data):
        """
        Atualiza um utilizador, hasheando password se fornecida.
        """
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password_hash = make_password(password)
        
        instance.save()
        return instance


class UsuarioResumidoSerializer(serializers.ModelSerializer):
    """
    Versão simplificada de UsuarioSerializer.
    
    Útil para exibir informações de utilizador em nested serializers
    sem expor dados sensíveis.
    """
    class Meta:
        model = Usuario
        fields = [
            'id',
            'nome',
            'email',
            'created_at',
        ]
        read_only_fields = fields


class UsuarioCriacaoSerializer(serializers.ModelSerializer):
    """
    Serializer especializado para criação de novos utilizadores (registo).
    
    Requisito R01: Gestão de Utilizadores
    - Obriga password e email
    - Valida email único
    - Hasheada automaticamente
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        help_text="Password com mínimo 6 caracteres"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Confirmação da password"
    )
    
    class Meta:
        model = Usuario
        fields = [
            'nome',
            'email',
            'password',
            'password_confirm',
        ]
    
    def validate(self, data):
        """
        Valida que as passwords coincidirem.
        """
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError(
                {"password": "As passwords não coincidem."}
            )
        
        if len(data['password']) < 6:
            raise serializers.ValidationError(
                {"password": "A password deve ter pelo menos 6 caracteres."}
            )
        
        return data
    
    def validate_email(self, value):
        """
        Valida que o email é único.
        """
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Um utilizador com este email já existe."
            )
        return value
    
    def create(self, validated_data):
        """
        Cria um novo utilizador com password hasheada.
        """
        usuario = Usuario(
            nome=validated_data['nome'],
            email=validated_data['email'],
            password_hash=make_password(validated_data['password'])
        )
        usuario.save()
        return usuario


# ============================================================================
# SERIALIZERS DE ATIVIDADE DO UTILIZADOR
# ============================================================================

class AtividadeUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo AtividadeUsuario.
    
    Requisito R04: Avaliações
    Requisito R08: Favoritos / Watchlist
    Requisito R09: Histórico de Interação
    
    Consolida avaliações, favoritos, filmes vistos e watchlist.
    """
    usuario = UsuarioResumidoSerializer(read_only=True)
    filme = FilmeResumidoSerializer(read_only=True)
    
    class Meta:
        model = AtividadeUsuario
        fields = [
            'id',
            'usuario',
            'filme',
            'rating',
            'visto',
            'favorito',
            'ver_mais_tarde',
            'review',
            'data_visualizacao',
            'data_adicao_favoritos',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'usuario',
            'filme',
            'data_visualizacao',
            'data_adicao_favoritos',
            'created_at',
            'updated_at',
        ]
    
    def validate_rating(self, value):
        """
        Valida que o rating está entre 0 e 10.
        """
        if value is not None and not (0 <= value <= 10):
            raise serializers.ValidationError(
                "O rating deve estar entre 0 e 10."
            )
        return value


class AvaliacaoSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para avaliar um filme.
    
    Requisito R04: Avaliações
    - Valida rating entre 0 e 10
    - Garante unicidade por utilizador+filme
    """
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    filme_nome = serializers.CharField(source='filme.nome', read_only=True)
    
    class Meta:
        model = AtividadeUsuario
        fields = [
            'usuario_nome',
            'filme_nome',
            'rating',
            'review',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'usuario_nome',
            'filme_nome',
            'created_at',
            'updated_at',
        ]
    
    def validate_rating(self, value):
        """
        Valida rating entre 0 e 10.
        """
        if not (0 <= value <= 10):
            raise serializers.ValidationError(
                "O rating deve estar entre 0 e 10."
            )
        return value


# ============================================================================
# SERIALIZERS DE FAVORITOS
# ============================================================================

class FavoritoSerializer(serializers.ModelSerializer):
    """
    Serializer para favoritos.
    
    Requisito R08: Favoritos / Watchlist
    - Relaciona utilizador e filme
    - Inclui data de adição
    """
    usuario = UsuarioResumidoSerializer(read_only=True)
    filme = FilmeResumidoSerializer(read_only=True)
    
    class Meta:
        model = AtividadeUsuario
        fields = [
            'usuario',
            'filme',
            'favorito',
            'data_adicao_favoritos',
            'created_at',
        ]
        read_only_fields = [
            'usuario',
            'filme',
            'data_adicao_favoritos',
            'created_at',
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Favorito explícito.
    
    Requisito R08: Favoritos / Watchlist
    - Lista favoritos do utilizador
    - Inclui informações do filme e data de adição
    """
    filme = FilmeResumidoSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    added_at = serializers.DateTimeField(source='data_adicao', read_only=True)
    
    class Meta:
        model = Favorito
        fields = [
            'id',
            'movie_id',
            'filme',
            'added_at',
        ]
        read_only_fields = ['id', 'added_at', 'filme']
    
    def validate_movie_id(self, value):
        """
        Valida que o filme existe.
        """
        if not Filme.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Filme com este ID não foi encontrado."
            )
        return value


class AdicionarFavoritoSerializer(serializers.Serializer):
    """
    Serializer para endpoint de adição de favoritos.
    
    Requisito R08: Favoritos / Watchlist
    - Aceita movie_id
    - Valida existência do filme
    """
    movie_id = serializers.IntegerField(
        required=True,
        help_text="ID do filme a adicionar aos favoritos"
    )
    
    def validate_movie_id(self, value):
        """
        Valida que o filme existe.
        """
        if not Filme.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Filme com este ID não foi encontrado."
            )
        return value


# ============================================================================
# SERIALIZERS DE HISTÓRICO
# ============================================================================

class HistoricoVisualizacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o histórico de visualizações.
    
    Requisito R09: Histórico de Interação
    - Expõe filme e data de visualização
    """
    usuario = UsuarioResumidoSerializer(read_only=True)
    filme = FilmeResumidoSerializer(read_only=True)
    
    class Meta:
        model = AtividadeUsuario
        fields = [
            'usuario',
            'filme',
            'visto',
            'data_visualizacao',
            'created_at',
        ]
        read_only_fields = fields


class MarcarVistaSerializer(serializers.Serializer):
    """
    Serializer para endpoint de marcar filme como visto.
    
    Requisito R09: Histórico de Interação
    - Aceita movie_id
    - Valida existência do filme
    """
    movie_id = serializers.IntegerField(
        required=True,
        help_text="ID do filme a marcar como visto"
    )
    
    def validate_movie_id(self, value):
        """
        Valida que o filme existe.
        """
        if not Filme.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Filme com este ID não foi encontrado."
            )
        return value


# ============================================================================
# SERIALIZERS PARA RECOMENDAÇÕES
# ============================================================================

class RecomendacaoFilmeSerializer(serializers.Serializer):
    """
    Serializer simplificado para filmes em recomendações.
    
    Requisito R05: Sistema de Recomendações
    - Versão ultra-compacta para performance
    """
    tmdb_id = serializers.IntegerField(source='id')
    titulo = serializers.CharField(source='nome')
    descricao = serializers.CharField()
    poster_url = serializers.SerializerMethodField()
    rating_tmdb = serializers.FloatField()
    generos = serializers.SerializerMethodField()
    rating_medio_usuarios = serializers.SerializerMethodField()
    
    def get_poster_url(self, obj):
        """Formata URL do poster."""
        if obj.poster_path:
            return f"https://image.tmdb.org/t/p/w500{obj.poster_path}"
        return None
    
    def get_generos(self, obj):
        """Retorna lista de nomes de géneros."""
        return [g.nome for g in obj.generos.all()]
    
    def get_rating_medio_usuarios(self, obj):
        """Calcula rating médio."""
        return obj.get_rating_medio_usuarios()


# ============================================================================
# SERIALIZERS PARA AUTENTICAÇÃO / LOGIN
# ============================================================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de login.
    
    Requisito R01: Gestão de Utilizadores / Autenticação
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer para resposta de token de autenticação.
    
    Requisito R01: Gestão de Utilizadores / Autenticação
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    usuario = UsuarioResumidoSerializer()


# ============================================================================
# SERIALIZERS PARA WATCH LATER / VER MAIS TARDE
# ============================================================================

class VerMaisTardeSerializer(serializers.Serializer):
    """
    Serializer para endpoint de adicionar à lista 'Ver Mais Tarde'.
    
    Requisito R08: Favoritos / Watchlist
    - Aceita movie_id
    - Valida existência do filme
    """
    movie_id = serializers.IntegerField(
        required=True,
        help_text="ID do filme a adicionar à lista 'Ver Mais Tarde'"
    )
    
    def validate_movie_id(self, value):
        """
        Valida que o filme existe.
        """
        if not Filme.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Filme com este ID não foi encontrado."
            )
        return value


# ============================================================================
# SERIALIZERS DE BUSCA / FILTRO
# ============================================================================

class BuscaFilmeSerializer(serializers.Serializer):
    """
    Serializer para parametrização de buscas de filmes.
    
    Requisito R03: Pesquisa e Filtro
    """
    query = serializers.CharField(
        max_length=512,
        required=False,
        help_text="Termo de busca para título ou sinopse"
    )
    generos = serializers.CharField(
        max_length=512,
        required=False,
        help_text="Géneros para filtro (separados por vírgula)"
    )
    ano_minimo = serializers.IntegerField(
        required=False,
        help_text="Ano de lançamento mínimo"
    )
    ano_maximo = serializers.IntegerField(
        required=False,
        help_text="Ano de lançamento máximo"
    )
    rating_minimo = serializers.FloatField(
        required=False,
        help_text="Rating TMDB mínimo (0-10)"
    )
    ordenacao = serializers.ChoiceField(
        choices=['titulo', '-titulo', 'rating_tmdb', '-rating_tmdb', '-data_adicao'],
        required=False,
        default='-data_adicao',
        help_text="Campo e ordem de ordenação"
    )
    pagina = serializers.IntegerField(
        required=False,
        default=1,
        help_text="Número da página"
    )
    tamanho_pagina = serializers.IntegerField(
        required=False,
        default=20,
        help_text="Filmes por página"
    )