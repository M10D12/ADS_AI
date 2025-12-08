from rest_framework import serializers
from .models import Usuario, Filme, Genero, AtividadeUsuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class FilmeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filme
        fields = '__all__'

class GeneroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genero
        fields = '__all__'

class AtividadeUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AtividadeUsuario
        fields = '__all__'
