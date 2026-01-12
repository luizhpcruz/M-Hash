import sqlite3
import secrets
import hashlib
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# --- CONFIGURAÇÃO DA API ---
app = FastAPI(
    title="M-Hash API",
    description="Sistema de Auditoria Digital e Imutabilidade via SHA-256.",
    version="1.0.0"
)

# Configuração de CORS (Essencial para conectar com sites externos/Lovable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BANCO DE DADOS ---
def conectar_bd():
    # O banco agora se chama 'mhash.db'
    return sqlite3.connect("mhash.db")

def inicializar_banco():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            api_key TEXT PRIMARY KEY,
            nome_empresa TEXT,
            creditos INTEGER,
            status TEXT DEFAULT 'ATIVO'
        )
    ''')
    
    # Cria usuário ADMIN padrão para testes imediatos
    # Use a chave 'mhash_admin_key' para testar agora
    cursor.execute("""
        INSERT OR IGNORE INTO clientes (api_key, nome_empresa, creditos) 
        VALUES ('mhash_admin_key', 'Admin M-Hash', 9999)
    """)
    
    conn.commit()
    conn.close()

# Inicia o banco ao ligar o servidor
inicializar_banco()

# --- SEGURANÇA E COBRANÇA ---
def verificar_acesso(x_api_key: str = Header(...)):
    """
    O Porteiro: Verifica se a chave existe e desconta o crédito.
    """
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("SELECT creditos, status FROM clientes WHERE api_key = ?", (x_api_key,))
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        raise HTTPException(status_code=401, detail="M-Hash: Chave de acesso inválida.")
    
    creditos, status = resultado
    
    if status != 'ATIVO':
        conn.close()
        raise HTTPException(status_code=403, detail="M-Hash: Conta suspensa.")

    if creditos <= 0:
        conn.close()
        raise HTTPException(status_code=402, detail="M-Hash: Saldo insuficiente.")
    
    # Debita o crédito
    novo_saldo = creditos - 1
    cursor.execute("UPDATE clientes SET creditos = ? WHERE api_key = ?", (novo_saldo, x_api_key))
    conn.commit()
    conn.close()
    
    return novo_saldo

# --- ROTAS DA API ---

@app.get("/")
def status_sistema():
    return {
        "sistema": "M-Hash",
        "status": "ONLINE",
        "mensagem": "Auditoria Digital Operacional"
    }

@app.post("/admin/gerar-chave")
def criar_cliente(nome_empresa: str, pacote_creditos: int):
    """
    Gera uma nova chave para você vender pro cliente.
    """
    nova_key = "live_" + secrets.token_hex(8)
    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (api_key, nome_empresa, creditos) VALUES (?, ?, ?)", 
                       (nova_key, nome_empresa, pacote_creditos))
        conn.commit()
    except:
        conn.close()
        return {"erro": "Falha ao criar cliente"}
        
    conn.close()
    return {"mensagem": "Cliente M-Hash criado", "api_key": nova_key, "creditos": pacote_creditos}

@app.post("/api/v1/auditar")
async def processar_hash(
    arquivo: UploadFile = File(...), 
    saldo: int = Depends(verificar_acesso)
):
    """
    Recebe arquivo -> Gera Hash -> Retorna Certificado.
    """
    conteudo = await arquivo.read()
    
    # O MOTOR (SHA-256)
    hash_digital = hashlib.sha256(conteudo).hexdigest()
    
    return {
        "certificado_mhash": {
            "arquivo": arquivo.filename,
            "hash_sha256": hash_digital,
            "autenticidade": "GARANTIDA",
            "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        },
        "conta": {
            "saldo_restante": saldo
        }
    }