# M-Hash

**M-Hash** é uma API de auditoria digital de alta performance. O sistema garante a integridade de documentos (PDFs, Imagens, Logs) criando impressões digitais criptográficas imutáveis (SHA-256).

## Funcionalidades

- **Hash SHA-256:** Padrão de segurança militar/bancária.
- **Controle de Acesso:** Sistema de API Keys com gestão de créditos.
- **Alta Performance:** Backend em FastAPI (Python).

## Instalação Local

1. Clone o repositório.
2. Instale as dependências:
   `pip install -r requirements.txt`
3. Execute o servidor:
   `uvicorn main:app --reload`

## Como Usar

### Autenticação
Use o header `x-api-key`.
Chave de Admin para Teste: `mhash_admin_key`

### Endpoint Principal
`POST /api/v1/auditar`
Envie o arquivo via form-data.

---
Copyright © 2026 M-Hash
