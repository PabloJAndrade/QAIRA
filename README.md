# QAIRA
Quality Assurance Intelligent Report Assistant

Este projeto é um script Python que gera automaticamente casos de teste baseados em histórias de usuário do Jira utilizando IA (Gemini). Ideal para equipes de QA que desejam agilidade sem comprometer a qualidade.

⸻

✨ Funcionalidades
	•	🔍 Busca a descrição de tickets diretamente do Jira (usando API básica).
	•	🧠 Gera entre 3 e 5 casos de teste com IA (formato Given/When/Then + validações).
	•	💬 Permite inserir contexto adicional para melhorar a geração.
	•	📂 Salva os testes em .md localmente.
	•	🧱 (Opcional) Cria uma subtarefa no Jira com os testes em formato ADF.

⸻

⚙️ Configuração Rápida

🐍 Pré-requisitos
	•	Python 3.8+
	•	pip (gerenciador de pacotes)

1. Clone ou extraia o projeto

mkdir QAIRA && cd QAIRA
# Copie o script principal e o .env.example para cá

2. Crie e ative um ambiente virtual (opcional, mas recomendado)

python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows

3. Instale as dependências

pip install -r requirements.txt

4. Configure o .env

Crie um arquivo chamado .env na raiz e insira:

JIRA_EMAIL=seu.email@exemplo.com
JIRA_TOKEN=sua_chave_api_jira
JIRA_URL=https://seudominio.atlassian.net
GEMINI_API_KEY=sua_chave_api_google
JIRA_SUBTASK_ISSUE_TYPE_ID=10003  # opcional se não for criar subtarefas


⸻

🔑 Como obter suas chaves

📌 Chave da API do Jira
	1.	Acesse: https://id.atlassian.com/manage-profile/security/api-tokens
	2.	Clique em “Create API token”
	3.	Dê um nome e gere
	4.	Copie e cole no .env

📌 Chave da API do Google Gemini
	1.	Acesse: https://aistudio.google.com/app/apikey
	2.	Clique em “Criar chave de API”
	3.	Copie a chave gerada e cole no .env

⸻

🚀 Como usar

python gerar_teste.py

O script irá:
	1.	Pedir o ID da história do Jira (ex: TICKET-1234)
	2.	Buscar a descrição
	3.	Gerar os casos de teste
	4.	Perguntar se deseja adicionar mais contexto
	5.	Perguntar se quer criar subtarefa com os testes no Jira
	6.	Salvar um arquivo .md com os testes localmente

⸻

🛠️ Problemas comuns
	•	Erro 401/403 Jira: verifique token e permissões
	•	Erro 404 Jira: verifique se o ticket existe e se o seu usuário tem acesso
	•	API Gemini falha: confira sua chave e os limites de uso

⸻

📄 Licença

Distribuído sob a licença MIT.

⸻

Desenvolvido por Pablo Andrade ✨
