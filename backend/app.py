"""
Aplicação Flask - Trabalho 02 Redes
Backend HTTP com sessão centralizada em PostgreSQL
"""

from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime, timedelta
import socket
import os

# Configurar caminho do frontend (funciona tanto local quanto Docker)
# No Docker, o frontend é montado como volume em /app/frontend
FRONTEND_PATH = '/app/frontend'
if not os.path.exists(FRONTEND_PATH):
    # Se não encontrar no Docker, tenta caminho relativo (desenvolvimento local)
    FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')

# Configurar CORS para permitir requisições de diferentes origens
# Necessário para detecção de falha funcionar entre diferentes portas
# Lista completa de origens possíveis (localhost e meutrabalho.com.br em todas as portas)
allowed_origins = []
for port in ['5000', '5001', '5002']:
    allowed_origins.extend([
        f'http://localhost:{port}',
        f'http://127.0.0.1:{port}',
        f'http://www.meutrabalho.com.br:{port}',
        f'http://meutrabalho.com.br:{port}'
    ])

CORS(app, 
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'Cookie'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Content-Type'])

# Permitir servir arquivos JavaScript
@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve arquivos JavaScript"""
    return send_from_directory(os.path.join(FRONTEND_PATH, 'js'), filename)

app.secret_key = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')

# Configuração do banco de dados PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '172.20.0.20'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'meutrabalho'),
    'user': os.getenv('DB_USER', 'trabalho'),
    'password': os.getenv('DB_PASSWORD', 'trabalho123')
}

def get_db():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Erro ao conectar ao banco de dados:")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Port: {DB_CONFIG['port']}")
        print(f"   Database: {DB_CONFIG['database']}")
        print(f"   User: {DB_CONFIG['user']}")
        print(f"   Erro: {e}")
        raise
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco: {e}")
        raise

def criar_sessao(usuario_id):
    """Cria uma nova sessão no banco de dados"""
    session_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=1)
    
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO sessoes (session_id, usuario_id, expires_at) VALUES (%s, %s, %s)',
                (session_id, usuario_id, expires_at)
            )
        conn.commit()
        return session_id
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Erro ao criar sessão: {e}")
        raise
    finally:
        conn.close()

def validar_sessao(session_id):
    """Valida se a sessão existe e não expirou"""
    if not session_id:
        return None
    
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT * FROM sessoes WHERE session_id = %s AND expires_at > %s',
                (session_id, datetime.now())
            )
            sessao = cur.fetchone()
            return sessao
    except psycopg2.Error as e:
        print(f"Erro ao validar sessão: {e}")
        return None
    finally:
        conn.close()

def get_hostname():
    """Retorna o hostname do servidor"""
    # Tenta usar variável de ambiente primeiro, depois hostname do sistema
    return os.getenv('SERVER_NAME', socket.gethostname())

# ============================================
# ROTAS DO FRONTEND
# ============================================

@app.route('/')
def index():
    """Página de login"""
    try:
        return send_from_directory(FRONTEND_PATH, 'index.html')
    except Exception as e:
        # Se não conseguir carregar, retornar fallback que tenta outros servidores
        try:
            return send_from_directory(FRONTEND_PATH, 'fallback.html')
        except:
            return f"Erro ao carregar página. Caminho: {FRONTEND_PATH}", 500

@app.route('/perfil.html')
def perfil():
    """Página de perfil"""
    try:
        return send_from_directory(FRONTEND_PATH, 'perfil.html')
    except Exception as e:
        return f"Erro ao carregar perfil.html: {e}. Caminho: {FRONTEND_PATH}", 500

@app.route('/fallback.html')
def fallback():
    """Página de fallback para redirecionamento automático"""
    try:
        return send_from_directory(FRONTEND_PATH, 'fallback.html')
    except Exception as e:
        return f"Erro ao carregar fallback.html: {e}. Caminho: {FRONTEND_PATH}", 500

# ============================================
# ROTAS DA API
# ============================================

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint de login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'erro': 'Dados inválidos'}), 400
        
        login = data.get('login')
        senha = data.get('senha')
        
        if not login or not senha:
            return jsonify({'erro': 'Login e senha são obrigatórios'}), 400
        
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT * FROM usuarios WHERE login = %s',
                    (login,)
                )
                usuario = cur.fetchone()
        finally:
            conn.close()
        
        if not usuario:
            return jsonify({'erro': 'Credenciais inválidas'}), 401
        
        # Verificar senha
        if not check_password_hash(usuario['senha_hash'], senha):
            return jsonify({'erro': 'Credenciais inválidas'}), 401
        
        # Criar sessão
        session_id = criar_sessao(usuario['id'])
        
        response = make_response(jsonify({
            'sucesso': True,
            'session_id': session_id
        }))
        
        # Definir cookie
        response.set_cookie(
            'session_id',
            session_id,
            httponly=True,
            max_age=3600,  # 1 hora
            samesite='Lax',
            path='/'
        )
        
        return response
    
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/api/meu-perfil', methods=['GET'])
def meu_perfil():
    """Endpoint protegido - retorna dados do perfil"""
    try:
        session_id = request.cookies.get('session_id')
        
        sessao = validar_sessao(session_id)
        if not sessao:
            return jsonify({'erro': 'Não autenticado'}), 401
        
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    'SELECT * FROM usuarios WHERE id = %s',
                    (sessao['usuario_id'],)
                )
                usuario = cur.fetchone()
        finally:
            conn.close()
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'nome': usuario['nome'],
            'hostname': get_hostname(),
            'data_login': sessao['created_at'].isoformat(),
            'codigo_sessao': sessao['session_id']
        })
    
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Endpoint de logout"""
    try:
        session_id = request.cookies.get('session_id')
        
        if session_id:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        'DELETE FROM sessoes WHERE session_id = %s',
                        (session_id,)
                    )
                conn.commit()
            finally:
                conn.close()
        
        response = make_response(jsonify({'sucesso': True}))
        response.set_cookie('session_id', '', expires=0, path='/')
        return response
    
    except Exception as e:
        print(f"Erro no logout: {e}")
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check para detecção de falha (ponto extra)"""
    try:
        # Verificar conexão com banco
        conn = get_db()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'hostname': get_hostname(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'hostname': get_hostname(),
            'erro': str(e)
        }), 503

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == '__main__':
    # Verificar conexão com banco na inicialização
    try:
        conn = get_db()
        conn.close()
        print(f"✅ Conectado ao banco de dados: {DB_CONFIG['host']}")
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível conectar ao banco: {e}")
        print("   A aplicação tentará conectar novamente nas requisições.")
    
    print(f"🚀 Iniciando servidor HTTP: {get_hostname()}")
    print(f"📡 Escutando em 0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

