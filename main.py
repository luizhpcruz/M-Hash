from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware  # <--- O SEGREDO ESTÁ AQUI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
import hashlib
from typing import Optional

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS ---
class Conta(SQLModel, table=True):
    api_key: str = Field(primary_key=True)
    nome: str
    saldo_restante: int = 1000

class RegistroAudit(SQLModel, table=True):
    hash_sha256: str = Field(primary_key=True)
    nome_arquivo: str
    data_registro: datetime
    quem_registrou: str

engine = create_engine("sqlite:///banco_mhash.db")

def criar_tabelas():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# --- 2. O APLICATIVO ---
app = FastAPI()

# --- CONFIGURAÇÃO DO CORS (LIBERA O LOVABLE) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Libera acesso para todos (incluindo o Lovable)
    allow_credentials=True,
    allow_methods=["*"],  # Libera todos os métodos (GET, POST, OPTIONS)
    allow_headers=["*"],  # Libera todos os cabeçalhos
)

@app.on_event("startup")
def on_startup():
    criar_tabelas()
    with Session(engine) as session:
        admin = session.get(Conta, "mhash_admin_key")
        if not admin:
            session.add(Conta(api_key="mhash_admin_key", nome="Admin Master", saldo_restante=9999))
            session.commit()

# --- 3. FUNÇÕES AUXILIARES ---
def calcular_hash(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()

# --- 4. AS ROTAS ---
@app.post("/api/v1/auditar")
async def auditar_arquivo(
    arquivo: UploadFile = File(...),
    x_api_key: str = Header(...),
    session: Session = Depends(get_session)
):
    cliente = session.get(Conta, x_api_key)
    if not cliente:
        raise HTTPException(status_code=401, detail="API Key inválida")
    
    if cliente.saldo_restante <= 0:
        raise HTTPException(status_code=402, detail="Saldo insuficiente.")

    conteudo = await arquivo.read()
    hash_gerado = calcular_hash(conteudo)
    
    registro_existente = session.get(RegistroAudit, hash_gerado)
    if registro_existente:
        return {
            "status": "JÁ REGISTRADO",
            "mensagem": "Este arquivo já consta no livro oficial.",
            "certificado_mhash": {
                "hash_sha256": registro_existente.hash_sha256,
                "data_registro": registro_existente.data_registro,
                "registrado_por": registro_existente.quem_registrou
            },
            "conta": {
                "cliente": cliente.nome,
                "saldo_restante": cliente.saldo_restante
            }
        }

    cliente.saldo_restante -= 1
    session.add(cliente)
    
    novo_registro = RegistroAudit(
        hash_sha256=hash_gerado,
        nome_arquivo=arquivo.filename,
        data_registro=datetime.now(),
        quem_registrou=cliente.api_key
    )
    session.add(novo_registro)
    session.commit()
    session.refresh(novo_registro)

    return {
        "status": "SUCESSO",
        "mensagem": "Arquivo auditado e registrado.",
        "certificado_mhash": {
            "hash_sha256": novo_registro.hash_sha256,
            "data_registro": novo_registro.data_registro,
            "arquivo_original": novo_registro.nome_arquivo
        },
        "conta": {
            "cliente": cliente.nome,
            "saldo_restante": cliente.saldo_restante
        }
    }

@app.post("/api/v1/verificar")
async def verificar_arquivo(
    arquivo: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    conteudo = await arquivo.read()
    hash_consulta = calcular_hash(conteudo)
    
    registro = session.get(RegistroAudit, hash_consulta)
    
    if registro:
        return {
            "status": "AUTÊNTICO",
            "resultado": "✅ Arquivo Original Encontrado!",
            "dados": {
                "hash": registro.hash_sha256,
                "data_original": registro.data_registro,
                "nome_original": registro.nome_arquivo,
                "registrado_por_api": registro.quem_registrou
            }
        }
    else:
        return {
            "status": "DESCONHECIDO",
            "resultado": "❌ Arquivo não encontrado ou modificado.",
            "dados": {
                "hash_calculado": hash_consulta
            }
        }
