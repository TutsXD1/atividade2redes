/**
 * Cliente API com detecção de falha e retry automático
 * Ponto Extra: Detecta servidor inativo e tenta próximo servidor
 */

class APIClient {
    constructor() {
        // Detectar origem atual (hostname e protocolo)
        const currentOrigin = window.location.origin;
        const currentHost = window.location.hostname;
        const currentPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
        
        // Lista de servidores conhecidos
        // Com Round Robin DNS real, todos os servidores usam a mesma porta (5000)
        // mas em IPs diferentes (172.20.0.10, 172.20.0.11, 172.20.0.12)
        // O DNS alterna entre os IPs, então usamos o hostname resolvido pelo DNS
        const baseUrl = `${window.location.protocol}//${currentHost}`;
        
        // Configurar servidores baseado na estratégia de portas
        // Cada servidor HTTP está mapeado para uma porta diferente no host
        // SEMPRE usar portas diferentes, independente do hostname
        const host = (currentHost === 'localhost' || currentHost === '127.0.0.1' || 
                     currentHost === 'www.meutrabalho.com.br' || currentHost === 'meutrabalho.com.br')
                     ? currentHost : currentHost;
        
        this.servers = [
            { url: `http://${host}:5000`, name: 'http1' },
            { url: `http://${host}:5001`, name: 'http2' },
            { url: `http://${host}:5002`, name: 'http3' }
        ];
        
        console.log('🌐 Servidores configurados:', this.servers.map(s => s.url));
        
        // Servidor atual sendo usado
        this.currentServerIndex = 0;
        this.baseUrl = null;
        
        // Cache de servidores ativos (para evitar testar todos sempre)
        this.activeServers = [];
    }

    /**
     * Cria um timeout para fetch
     */
    createTimeout(ms) {
        return new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Timeout')), ms);
        });
    }

    /**
     * Encontra um servidor ativo testando cada um
     */
    async findActiveServer() {
        // Limpar cache de servidores ativos se estiver vazio ou se todos falharam
        // Testar todos os servidores em ordem (ignorar cache para garantir que testamos todos)
        console.log('🔍 Procurando servidor ativo...');
        
        for (let i = 0; i < this.servers.length; i++) {
            try {
                console.log(`   Testando ${this.servers[i].name} (${this.servers[i].url})...`);
                const response = await Promise.race([
                    fetch(`${this.servers[i].url}/api/health`, {
                        method: 'GET',
                        credentials: 'include',
                        mode: 'cors'
                    }),
                    this.createTimeout(3000)  // Timeout maior para dar mais tempo
                ]);
                
                if (response && response.ok) {
                    this.currentServerIndex = i;
                    this.baseUrl = this.servers[i].url;
                    this.activeServers = [i]; // Atualizar lista de ativos
                    console.log(`✅ Servidor ativo encontrado: ${this.servers[i].name} (${this.servers[i].url})`);
                    return this.servers[i].url;
                } else {
                    console.log(`❌ Servidor ${this.servers[i].name} retornou status ${response?.status}`);
                }
            } catch (e) {
                const errorMsg = e.message || 'Erro desconhecido';
                console.log(`❌ Servidor ${this.servers[i].name} inativo (${errorMsg}), tentando próximo...`);
            }
        }

        // Nenhum servidor ativo encontrado
        console.error('❌ Nenhum servidor HTTP está disponível');
        throw new Error('Nenhum servidor HTTP está disponível');
    }

    /**
     * Faz uma requisição com retry automático
     */
    async request(endpoint, options = {}) {
        const maxRetries = this.servers.length;
        let lastError = null;

        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                // Sempre encontrar servidor ativo antes de fazer requisição
                // Isso garante que se um servidor caiu, vamos tentar outro
                const baseUrl = await this.findActiveServer();
                this.baseUrl = baseUrl;

                const url = `${baseUrl}${endpoint}`;
                
                console.log(`🔄 Tentando requisição para: ${url}`);
                
                const response = await Promise.race([
                    fetch(url, {
                        ...options,
                        credentials: 'include',
                        mode: 'cors'
                    }),
                    this.createTimeout(5000)
                ]);

                // Se sucesso, retornar resposta
                if (response.ok || response.status === 401) {
                    console.log(`✅ Requisição bem-sucedida para: ${url}`);
                    return response;
                }

                // Se erro 5xx ou 0 (network error), tentar próximo servidor
                if (response.status >= 500 || response.status === 0) {
                    console.log(`⚠️ Erro ${response.status} do servidor, tentando próximo...`);
                    // Marcar servidor atual como inativo
                    this.activeServers = this.activeServers.filter(i => i !== this.currentServerIndex);
                    this.currentServerIndex = null;
                    this.baseUrl = null;
                    continue;
                }

                // Outros erros (4xx), retornar normalmente
                return response;

            } catch (error) {
                lastError = error;
                const errorMsg = error.message || 'Erro desconhecido';
                console.log(`❌ Erro na requisição (tentativa ${attempt + 1}/${maxRetries}):`, errorMsg);
                
                // Se não foi timeout/network error, não tentar novamente
                if (errorMsg !== 'Timeout' && !errorMsg.includes('Failed to fetch') && !errorMsg.includes('NetworkError') && !errorMsg.includes('Nenhum servidor') && !errorMsg.includes('fetch')) {
                    throw error;
                }

                // Limpar cache de servidor atual (marcar como inativo)
                if (this.currentServerIndex !== null) {
                    this.activeServers = this.activeServers.filter(i => i !== this.currentServerIndex);
                    console.log(`🗑️ Removendo servidor ${this.servers[this.currentServerIndex].name} da lista de ativos`);
                }
                this.currentServerIndex = null;
                this.baseUrl = null;

                // Aguardar um pouco antes de tentar novamente
                if (attempt < maxRetries - 1) {
                    console.log(`⏳ Aguardando 500ms antes de tentar próximo servidor...`);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }
        }

        // Se chegou aqui, nenhum servidor está disponível
        // Redirecionar para fallback se estivermos em uma página que precisa de servidor
        if (window.location.pathname !== '/fallback.html' && window.location.pathname !== '/') {
            console.error('❌ Nenhum servidor disponível, redirecionando para fallback...');
            window.location.href = '/fallback.html';
        }
        
        throw lastError || new Error('Falha ao conectar com os servidores');
    }

    /**
     * Métodos auxiliares para requisições comuns
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
}

// Criar instância global
const apiClient = new APIClient();

