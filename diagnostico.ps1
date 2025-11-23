# Script de Diagnóstico - Trabalho 02 Redes
# Execute este script para verificar o status do projeto

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DIAGNÓSTICO DO PROJETO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Docker
Write-Host "1. Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "   ✅ Docker instalado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker não encontrado!" -ForegroundColor Red
    exit 1
}

# 2. Verificar containers
Write-Host ""
Write-Host "2. Verificando containers..." -ForegroundColor Yellow
$containers = docker-compose ps
if ($containers -match "Up") {
    Write-Host "   ✅ Containers estão rodando" -ForegroundColor Green
    docker-compose ps
} else {
    Write-Host "   ⚠️  Containers não estão rodando" -ForegroundColor Yellow
    Write-Host "   Execute: docker-compose up -d" -ForegroundColor Cyan
}

# 3. Verificar banco de dados
Write-Host ""
Write-Host "3. Verificando banco de dados..." -ForegroundColor Yellow
try {
    $dbCheck = docker-compose exec -T database psql -U trabalho -d meutrabalho -c "\dt" 2>&1
    if ($dbCheck -match "usuarios") {
        Write-Host "   ✅ Tabelas criadas corretamente" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Tabelas não encontradas" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erro ao conectar ao banco" -ForegroundColor Red
}

# 4. Verificar usuários
Write-Host ""
Write-Host "4. Verificando usuários..." -ForegroundColor Yellow
try {
    $users = docker-compose exec -T database psql -U trabalho -d meutrabalho -c "SELECT login, nome FROM usuarios;" 2>&1
    if ($users -match "usuario1") {
        Write-Host "   ✅ Usuários cadastrados" -ForegroundColor Green
        Write-Host $users
    } else {
        Write-Host "   ⚠️  Usuários não encontrados" -ForegroundColor Yellow
        Write-Host "   Execute o seed.sql manualmente" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ Erro ao verificar usuários" -ForegroundColor Red
}

# 5. Verificar logs do http1
Write-Host ""
Write-Host "5. Últimas linhas do log do http1..." -ForegroundColor Yellow
docker-compose logs --tail=10 http1

# 6. Testar conexão HTTP
Write-Host ""
Write-Host "6. Testando conexão HTTP..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ Servidor HTTP respondendo" -ForegroundColor Green
    Write-Host "   Resposta: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Servidor HTTP não está respondendo" -ForegroundColor Red
    Write-Host "   Erro: $_" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FIM DO DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

