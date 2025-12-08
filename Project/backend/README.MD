# Como utilizar backend com o postgresql

## 1º Passo
Criar a BD no Postgresql.

## 2º Passo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'filmes',       
        'USER': 'postgres',     
        'PASSWORD': '123',   
        'HOST': 'localhost',       
        'PORT': '5432',         
    }
}
alterar isto para a vossa bd para testarem localmente depois as coisas do backend

## 3º Passo
python manage.py makemigrations
python manage.py migrate

## 4º Passo 
Ver se as tabelas foram criadas na BD do postgresql
Ignorem as tabelas auth_x  e django_x , são tabelas default do django para utilizarmos django admin e outras coisas.
Devem ter lá também api_x em que o x tem o nome dos models da api


## Criar Endpoits
Para criar os endpoints do backend, issues criados por mim recentemente, criamos nas views.