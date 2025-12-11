# Frontend - Sistema de Registo e Login

## Descrição

Implementação completa do frontend para o sistema de autenticação da plataforma de filmes, incluindo formulários de **Registo (Register)** e **Login** com integração total com o backend Django REST Framework.

## Funcionalidades Implementadas

### ✅ Componente Register (`/register`)
- **Formulário de Registo** com campos:
  - Nome Completo (validação: 2-512 caracteres)
  - Email (validação de formato)
  - Password (validação: mínimo 6 caracteres)
  - Confirmação de Password (match validation)
  
- **Validações Frontend**:
  - Validação de campos obrigatórios
  - Validação de comprimento de strings
  - Validação de formato de email
  - Validação de correspondência de passwords
  - Erros em tempo real enquanto o utilizador digita

- **Recursos de UX**:
  - Botão de mostrar/ocultar password
  - Mensagens de erro específicas por campo
  - Spinner de carregamento durante envio
  - Mensagens de sucesso e erro globais
  - Desabilitar formulário durante processamento
  - Redirecionamento automático para login após sucesso

### ✅ Componente Login (`/login`)
- **Formulário de Login** com campos:
  - Email
  - Password
  - Checkbox "Lembrar email" (persistência em localStorage)
  - Link para "Esqueceu a password?" (placeholder para futura implementação)

- **Validações Frontend**:
  - Validação de campos obrigatórios
  - Validação de formato de email
  - Erros em tempo real

- **Recursos de UX**:
  - Botão de mostrar/ocultar password
  - Opção de "Lembrar email" com persistência
  - Spinner de carregamento
  - Proteção: redireciona para home se já autenticado
  - Suporte a pré-preenchimento de email via state da navegação
  - Redirecionamento automático para home após sucesso

### ✅ Contexto de Autenticação (`AuthContext`)
- **Gerenciamento de Estado Global**:
  - `user` - Dados do utilizador autenticado
  - `token` - Token JWT armazenado
  - `isAuthenticated` - Flag de autenticação
  - `isLoading` - Flag de carregamento inicial

- **Métodos**:
  - `login(userData, token, refreshToken)` - Fazer login
  - `logout()` - Fazer logout
  - `updateUser(userData)` - Atualizar dados do utilizador
  - `fetchUserData(token)` - Buscar dados do utilizador da API

- **Persistência**:
  - Tokens guardados em localStorage
  - Verificação automática de autenticação no carregamento da app
  - Limpeza de dados em caso de token inválido

### ✅ Serviço de Autenticação (`authService`)
Centraliza todas as chamadas à API com métodos:
- `register(userData)` - Registar novo utilizador
- `login(credentials)` - Fazer login
- `logout()` - Fazer logout
- `getCurrentUser()` - Obter dados do utilizador atual
- `updateProfile(updateData)` - Atualizar perfil

## Estrutura de Diretórios

```
frontend/
├── src/
│   ├── components/
│   │   ├── Register/
│   │   │   ├── Register.jsx       # Componente de registo
│   │   │   └── Register.css       # Estilos do registo
│   │   └── Login/
│   │       ├── Login.jsx          # Componente de login
│   │       └── Login.css          # Estilos do login
│   ├── context/
│   │   └── AuthContext.jsx        # Contexto de autenticação
│   ├── services/
│   │   └── authService.js         # Serviço de API
│   ├── App.jsx                    # Componente principal
│   ├── App.css                    # Estilos globais da app
│   ├── index.jsx                  # Entry point
│   └── index.css                  # Estilos globais
├── public/
│   └── index.html                 # HTML template
├── package.json                   # Dependências
├── vite.config.js                 # Configuração Vite
└── README.md                      # Este arquivo
```

## Instalação

### 1. Instalar Dependências
```bash
cd frontend
npm install
```

### 2. Configurar Variáveis de Ambiente
Criar arquivo `.env` (opcional, se necessário):
```
VITE_API_URL=http://localhost:8000
```

### 3. Iniciar Servidor de Desenvolvimento
```bash
npm run dev
```

O servidor estará disponível em `http://localhost:3000` (ou a próxima porta disponível se 3000 estiver em uso).

## Endpoints da API Utilizados

### Autenticação
- **POST** `/api/auth/register/` - Registar novo utilizador
- **POST** `/api/auth/login/` - Fazer login
- **POST** `/api/auth/logout/` - Fazer logout
- **GET** `/api/auth/me/` - Obter dados do utilizador autenticado
- **PUT** `/api/auth/me/update/` - Atualizar perfil do utilizador

## Fluxo de Autenticação

### Fluxo de Registo
1. Utilizador acede a `/register`
2. Preenche o formulário (nome, email, password, confirmação)
3. Frontend valida os dados
4. Envia POST para `/api/auth/register/`
5. Backend valida e cria novo utilizador
6. Se sucesso: mensagem de sucesso + redirecionamento para `/login`
7. Se erro: exibir mensagem de erro (email já existe, etc)

### Fluxo de Login
1. Utilizador acede a `/login`
2. Se já autenticado: redireciona para `/`
3. Preenche email e password
4. Frontend valida os dados
5. Envia POST para `/api/auth/login/`
6. Backend valida credenciais e retorna tokens JWT
7. Se sucesso:
   - Guardar tokens em localStorage
   - Atualizar estado de autenticação
   - Redirecionamento para `/`
8. Se erro: exibir mensagem (email/password inválidos)

### Fluxo de Logout
1. Utilizador clica em botão Logout
2. Frontend envia POST para `/api/auth/logout/`
3. Limpar tokens de localStorage
4. Atualizar estado de autenticação
5. Redirecionar para `/login`

## Segurança

### Práticas Implementadas
- **Token Storage**: JWT guardado em localStorage (pode ser melhorado com HttpOnly cookies)
- **CORS**: Proxy configurado no Vite para chamadas à API
- **Validação**: Validação dupla (frontend + backend)
- **Password**: Campo de password com visualização segura
- **Session**: Verificação automática de autenticação ao carregar
- **Token Expiration**: Tratamento de tokens expirados (futura implementação de refresh)

### Melhorias Futuras
- Utilizar HttpOnly Cookies em vez de localStorage
- Implementar auto-refresh de tokens
- CSRF protection
- Rate limiting no frontend
- Logout em caso de inatividade

## Estilos

### Design System
- **Paleta de Cores**:
  - Primária: `#667eea` (Roxo)
  - Secundária: `#764ba2` (Roxo escuro)
  - Sucesso: `#155724` (Verde escuro)
  - Erro: `#721c24` (Vermelho escuro)
  - Fundo: `#f5f5f5` (Cinzento claro)

- **Tipografia**:
  - Font: System fonts (SF Pro Display, Segoe UI, etc)
  - Tamanhos: 12px a 28px

- **Componentes**:
  - Inputs com border focus dinâmica
  - Buttons com hover e active states
  - Alertas animadas
  - Spinners de carregamento
  - Links com underline ao hover

### Responsivo
- Desktop: Layout completo (420px width)
- Tablet: Ajustamentos de padding
- Mobile: Stack vertical, font reduzida, full width

## Testes de Integração com Backend

### Teste de Registo
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@example.com",
    "password": "senha123",
    "password_confirm": "senha123"
  }'
```

### Teste de Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@example.com",
    "password": "senha123"
  }'
```

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VITE_API_URL` | `http://localhost:8000` | URL base da API |

## Scripts Disponíveis

```bash
npm run dev      # Iniciar servidor de desenvolvimento
npm run build    # Build para produção
npm run preview  # Preview do build de produção
```

## Dependências

- **react** (^18.2.0) - Framework UI
- **react-dom** (^18.2.0) - React DOM binding
- **react-router-dom** (^7.10.1) - Roteamento

## DevDependencies

- **vite** (^5.0.0) - Build tool
- **@vitejs/plugin-react** (^4.2.0) - Plugin Vite para React

## Navegação

- `/` - Home (redirecionada de login se não autenticado)
- `/register` - Página de registo
- `/login` - Página de login

## Melhorias Futuras

1. **Funcionalidades**
   - Recuperação de password
   - Two-factor authentication (2FA)
   - OAuth integrations (Google, GitHub)
   - Email verification

2. **Técnicas**
   - HttpOnly Cookies para tokens
   - Refresh token rotation
   - Token encryption
   - Session persistence

3. **UI/UX**
   - Loading skeletons
   - Toast notifications
   - Form auto-save
   - Dark mode

4. **Segurança**
   - CSRF tokens
   - Rate limiting
   - Input sanitization
   - Helmet headers

## Suporte

Para questões ou bugs, abra uma issue no repositório.

---

**Último Atualizado**: 11 de Dezembro de 2025
**Versão**: 1.0.0
