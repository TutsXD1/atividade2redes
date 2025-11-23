-- Inserir usuários de teste
-- Senhas: "senha1" e "senha2"
-- Hashes gerados com werkzeug (scrypt)

-- Usuário 1: login=usuario1, senha=senha1
INSERT INTO usuarios (login, senha_hash, nome) 
VALUES ('usuario1', 'scrypt:32768:8:1$fmxUSRHfCugd9daE$14386bc293986017e0e00c655765ede993dfbe4bb3c54bd9309a237ab7a12c7440f397619bfa2fc64d6eac6beee82c4715051fcee79e519ef9708b7b2e2dda48', 'João Silva')
ON CONFLICT (login) DO NOTHING;

-- Usuário 2: login=usuario2, senha=senha2
INSERT INTO usuarios (login, senha_hash, nome) 
VALUES ('usuario2', 'scrypt:32768:8:1$yj2dNpCnzfMXH5PM$4e59427b8a48f8b13b8f794e57471216345e88fe60f28156cdbf1d0816d0be244267b48375aada2920f0c8eb5b003019d27b4641078a61c36f4a6f05aef0c449', 'Maria Santos')
ON CONFLICT (login) DO NOTHING;

-- NOTA: Se precisar gerar novos hashes, execute:
-- python gerar_hash.py

