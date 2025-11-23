FROM ubuntu:22.04

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar BIND9
RUN apt-get update && apt-get install -y \
    bind9 \
    bind9utils \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios necessários
RUN mkdir -p /var/cache/bind /var/log/named

# Configurar permissões
RUN chown -R bind:bind /var/cache/bind /var/log/named && \
    chmod 755 /var/log/named

# Expor portas DNS
EXPOSE 53/udp 53/tcp 953/tcp

# Comando padrão
CMD ["named", "-g", "-c", "/etc/bind/named.conf", "-u", "bind"]

