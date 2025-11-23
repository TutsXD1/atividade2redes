#!/usr/bin/env python3
"""
Script auxiliar para gerar hashes de senha
Use este script para gerar os hashes que serão inseridos no banco de dados
"""

from werkzeug.security import generate_password_hash

if __name__ == '__main__':
    print("=" * 60)
    print("Gerador de Hashes de Senha")
    print("=" * 60)
    print()
    
    senha1 = 'senha1'
    senha2 = 'senha2'
    
    hash1 = generate_password_hash(senha1)
    hash2 = generate_password_hash(senha2)
    
    print(f"Senha: {senha1}")
    print(f"Hash:  {hash1}")
    print()
    print(f"Senha: {senha2}")
    print(f"Hash:  {hash2}")
    print()
    print("=" * 60)
    print("Copie os hashes acima para o arquivo database/seed.sql")
    print("=" * 60)

