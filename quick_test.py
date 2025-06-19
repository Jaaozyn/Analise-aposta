#!/usr/bin/env python3
"""Teste rápido do FastAPI"""

import sys
print('🐍 Python version:', sys.version)

try:
    import fastapi
    print('✅ FastAPI version:', fastapi.__version__)
except ImportError as e:
    print('❌ FastAPI não encontrado:', e)
    sys.exit(1)

try:
    import uvicorn
    print('✅ Uvicorn disponível')
except ImportError as e:
    print('❌ Uvicorn não encontrado:', e)
    sys.exit(1)

try:
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get('/')
    def read_root():
        return {
            'message': '🚀 QuantumBet v2.0 - Teste básico funcionando!', 
            'status': 'ok',
            'melhorias': [
                'Rate Limiting',
                'Smart Cache', 
                'WebSocket Real-time',
                'Dynamic Pricing',
                'Ensemble Models',
                'Audit Trail'
            ]
        }
    
    print('✅ App FastAPI criado com sucesso')
    
    # Iniciar servidor
    print('🚀 Iniciando servidor na porta 8000...')
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
except Exception as e:
    print('❌ Erro ao criar app:', str(e))
    import traceback
    traceback.print_exc() 