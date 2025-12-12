# GitHub Actions Workflows

Este projeto utiliza GitHub Actions para Continuous Integration (CI) e Continuous Deployment (CD).

## 📋 Workflows Disponíveis

### 1. **CI - Continuous Integration** (`ci.yml`)
Executado em **push** e **pull requests** nas branches `main` e `develop`.

**Tarefas:**
- ✅ Testes do Backend (Django)
- ✅ Build do Frontend (React/Vite)
- ✅ Verificações de qualidade de código (Flake8, Pylint)
- ✅ Testes de segurança (Bandit)
- ✅ Build Docker (sem push)

**Triggers:**
```yaml
- Push para main ou develop
- Pull requests para main ou develop
```

### 2. **CD - Continuous Deployment** (`cd.yml`)
Executado automaticamente **após sucesso do CI** na branch `main`.

**Tarefas:**
- 🐳 Build e Push de imagens Docker
- 📚 Deploy de documentação
- 🔔 Notificações de status

**Triggers:**
```yaml
- Push para main
- Sucesso do workflow CI
```

### 3. **Code Analysis** (`code-analysis.yml`)
Análise contínua de qualidade e segurança de código.

**Tarefas:**
- 🔍 SonarQube Code Quality
- 📦 Dependency Check (Python + Node.js)
- 🔐 OWASP Dependency Check

**Triggers:**
```yaml
- Push para main ou develop
- Pull requests para main ou develop
```

### 4. **Release and Deploy** (`release.yml`)
Para releases oficiais e deploys em produção.

**Tarefas:**
- 📦 Criação de Release
- 🐳 Build de imagens com versionamento
- ✅ Health checks
- 🔔 Notificações de deployment

**Triggers:**
```yaml
- GitHub Release publicada
- Dispatch manual (workflow_dispatch)
```

## 🔧 Configuração

### Secrets Necessários (GitHub Settings > Secrets and variables > Actions)

```
DOCKER_USERNAME      # Username do Docker Hub
DOCKER_PASSWORD      # Token/Password do Docker Hub
GITHUB_TOKEN         # Automático (fornecido pelo GitHub)
```

### Variáveis de Ambiente

```
DATABASE_URL         # PostgreSQL connection string
DEBUG                # Django debug mode
SECRET_KEY           # Django secret key
```

## 📊 Status dos Workflows

Você pode verificar o status dos workflows em:
- **GitHub**: Actions tab do repositório
- **Badge de Status**: Adicione ao README:

```markdown
![CI](https://github.com/M10D12/ADS_AI/workflows/CI%20-%20Continuous%20Integration/badge.svg)
![CD](https://github.com/M10D12/ADS_AI/workflows/CD%20-%20Continuous%20Deployment/badge.svg)
```

## 🚀 Fluxo de Desenvolvimento

```
Developer commit code
         ↓
Push para branch (main/develop)
         ↓
GitHub Actions CI inicia automaticamente
         ↓
✅ CI Sucesso → CD inicia automaticamente
         ↓
🐳 Docker images criadas
         ↓
📚 Documentação deploy
         ↓
✅ Deployment completo
```

## 📝 Exemplo: Como Fazer Release

```bash
# 1. Criar tag local
git tag -a v1.0.0 -m "Release v1.0.0"

# 2. Push tag para remote
git push origin v1.0.0

# 3. GitHub Actions:
#    - Detecta nova release
#    - Executa workflow 'Release and Deploy'
#    - Cria imagens Docker com tag v1.0.0
#    - Deploy automático
```

## 🔐 Segurança

Os workflows incluem:
- ✅ Bandit (verificação de vulnerabilidades Python)
- ✅ pip-audit (auditoria de dependências Python)
- ✅ npm audit (auditoria de dependências Node.js)
- ✅ OWASP Dependency Check

## 📈 Métricas e Relatórios

Todos os workflows geram relatórios:
- **Coverage**: Cobertura de testes
- **Code Quality**: Métricas de qualidade
- **Security**: Relatórios de segurança

## ⚙️ Manutenção

Para editar workflows:
1. Modifique arquivos em `.github/workflows/`
2. Commit e push
3. GitHub Actions valida a sintaxe automaticamente

## 🆘 Troubleshooting

**Workflow falha no build Docker?**
```bash
# Testar build localmente
docker build -f backend/Dockerfile .
docker build -f frontend/Dockerfile .
```

**Testes falhando?**
```bash
# Rodar testes localmente
cd backend && python manage.py test api
cd frontend && npm test
```

**Secrets não configurados?**
```
Settings → Secrets and variables → Actions
Adicione os secrets necessários
```

## 📚 Referências

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Checkout Action](https://github.com/actions/checkout)

---

**Última atualização:** 12 de Dezembro de 2025
