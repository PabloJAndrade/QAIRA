import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from base64 import b64encode
import sys
import datetime
import re # Importar módulo de expressões regulares

load_dotenv()

# --- Configurações das Variáveis de Ambiente ---
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_URL = os.getenv("JIRA_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JIRA_SUBTASK_ISSUE_TYPE_ID = os.getenv("JIRA_SUBTASK_ISSUE_TYPE_ID")

if not all([JIRA_EMAIL, JIRA_TOKEN, JIRA_URL, GEMINI_API_KEY, JIRA_SUBTASK_ISSUE_TYPE_ID]):
    print("❌ Erro: Algumas variáveis de ambiente essenciais (JIRA_EMAIL, JIRA_TOKEN, JIRA_URL, GEMINI_API_KEY, JIRA_SUBTASK_ISSUE_TYPE_ID) não foram carregadas.")
    print("Por favor, verifique seu arquivo .env e certifique-se de que JIRA_SUBTASK_ISSUE_TYPE_ID está configurado corretamente.")
    sys.exit(1)

# --- Configuração do Jira ---
auth_base64 = b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/json"
}

# --- Configuração do Gemini ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"❌ Erro ao configurar a API do Gemini: {e}")
    print("Por favor, verifique se sua GEMINI_API_KEY está correta e ativa.")
    sys.exit(1)

# --- Funções ---

def obter_id_historia():
    """Solicita ao usuário o ID do ticket Jira."""
    while True:
        issue_id = input("➡️ Digite o ID do ticket Jira (ex: TICKET-1234): ").strip().upper()
        if issue_id:
            return issue_id
        else:
            print("❌ O ID do ticket não pode ser vazio. Por favor, tente novamente.")

def buscar_descricao(issue_id):
    """Busca a descrição de um ticket Jira."""
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"
    print(f"🔍 Buscando descrição para o ticket: {issue_id}...")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        issue = response.json()

        descricao_rich = issue["fields"].get("description")
        if not descricao_rich:
            print("⚠️ Descrição não encontrada no ticket ou está vazia.")
            return "Descrição não fornecida."

        def extrair_texto_bloco(bloco):
            """Função auxiliar para extrair texto de blocos de conteúdo Jira rich text."""
            textos = []
            if "content" in bloco:
                for item in bloco["content"]:
                    if item["type"] == "text":
                        textos.append(item[
                            "text"])
                    elif "content" in item:
                        textos += extrair_texto_bloco(item)
            return textos

        texto_final = []
        for bloco in descricao_rich.get("content", []):
            texto_final += extrair_texto_bloco(bloco)

        if not texto_final:
            print("⚠️ A descrição existe, mas não foi possível extrair texto útil.")
            return "Descrição existe, mas não foi possível extrair conteúdo textual."

        return "\n".join(texto_final).strip()

    except requests.exceptions.RequestException as e:
        try:
            error_details = response.json()
            error_messages = error_details.get("errorMessages", [])
            errors = error_details.get("errors", {})
            full_error = ", ".join(error_messages) + " " + str(errors)
        except ValueError:
            full_error = str(e)
        raise Exception(f"❌ Erro ao conectar ao Jira para o ticket {issue_id}. Verifique a URL do Jira, sua conexão ou as credenciais: {full_error}")
    except ValueError as e:
        raise Exception(f"❌ Erro na resposta do Jira ou na extração da descrição: {e}")

def gerar_testes(descricao_completa):
    """
    Gera casos de teste detalhados usando a API do Gemini, seguindo o template GWT (Given-When-Then)
    e incluindo uma seção de validações.
    """
    print("🧠 Gerando casos de teste com a IA (isso pode levar alguns segundos)...")
    prompt = f"""
Você é um QA experiente e detalhista. Sua tarefa é analisar cuidadosamente a descrição de uma história de usuário
para identificar requisitos, condições e resultados esperados.
Com base nessa análise, gere um conjunto de casos de teste claros e abrangentes.
Foques em cobrir os principais cenários, incluindo casos de sucesso e de falha (se aplicável e inferível).

Gere entre 3 e 7 casos de teste.

Descrição da história (incluindo detalhes adicionais se fornecidos):
\"\"\"
{descricao_completa}
\"\"\"

Formato OBRIGATÓRIO para cada caso de teste:
CTXX - Validar [Ação/Funcionalidade]

**Dado que** [Pré-condição]

**Quando** [Evento]

**Então** [Resultado esperado]

📌 Validações:

✔ [Validação 1]

✔ [Validação 2]

✔ [Validação N...]

---

Exemplo de caso de teste (não inclua este exemplo na resposta final):
CT01 - Validar login com credenciais válidas

**Dado que** o usuário está na página de login e tem credenciais válidas (usuario@exemplo.com e senha123)

**Quando** o usuário insere as credenciais válidas e clica em "Entrar"

**Então** o sistema deve redirecionar o usuário para a página inicial logado

📌 Validações:

✔ O usuário é redirecionado para a URL da página inicial.

✔ O nome do usuário logado é exibido no cabeçalho.

✔ Não há mensagens de erro de login.
---
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response.text and response.text.strip():
            return response.text.strip()
        else:
            raise ValueError("A API do Gemini retornou uma resposta vazia ou ilegível.")
    except Exception as e:
        raise Exception(f"❌ Erro ao gerar casos de teste com o Gemini. Verifique sua GEMINI_API_KEY e os limites de uso: {e}")

def salvar_markdown(issue_id, conteudo):
    """Salva o conteúdo gerado em um arquivo Markdown."""
    filename = f"casos_de_teste_{issue_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Casos de Teste - {issue_id}\n\n")
            f.write(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write(conteudo)
        print(f"\n✅ Arquivo salvo localmente: {filename}")
    except IOError as e:
        print(f"❌ Erro ao salvar o arquivo '{filename}': {e}")

def markdown_para_adf(texto_markdown):
    """
    Converte uma string Markdown de múltiplos parágrafos e formatação básica
    em formato Atlassian Document Format (ADF), criando blocos ADF adequados.
    """
    content_blocks = []
    
    for linha in texto_markdown.splitlines():
        linha_strip = linha.strip()

        if re.match(r"CT\d{2} - ", linha_strip):
            content_blocks.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": linha_strip}]
            })
        elif linha_strip.startswith("**Dado que**") or \
             linha_strip.startswith("**Quando**") or \
             linha_strip.startswith("**Então**") or \
             linha_strip.startswith("📌 Validações:"):
            
            # Divide a linha em partes para aplicar negrito corretamente.
            parts = re.split(r'(\*\*.*?\*\*|\_.*?\_\`)', linha_strip)
            text_nodes = []
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    text_nodes.append({
                        "type": "text",
                        "text": part[2:-2], # Remove os **
                        "marks": [{"type": "strong"}]
                    })
                elif part:
                    text_nodes.append({
                        "type": "text",
                        "text": part
                    })
            if text_nodes:
                content_blocks.append({
                    "type": "paragraph",
                    "content": text_nodes
                })
        elif re.match(r"[\✔\•\*\-]\s", linha_strip):
            # Tenta converter marcadores de lista em itens de lista do ADF se a linha anterior for uma lista
            # ou se a linha atual for um item de lista.
            
            # Se a linha atual é um item de lista e o último bloco era uma lista, adiciona ao item da lista
            # Se não, cria um novo bulletList e um novo listItem
            
            final_text = linha.replace("✔ ", "• ")
            content_blocks.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": final_text}]
            })

        elif linha_strip == "---":
            content_blocks.append({"type": "rule"})

        elif linha_strip:
            content_blocks.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": linha_strip}]
            })
        else:
            content_blocks.append({"type": "paragraph", "content": []})

    return {
        "type": "doc",
        "version": 1,
        "content": content_blocks
    }

def criar_subtask_jira(issue_id_pai, casos_de_teste_markdown):
    """Cria uma sub-tarefa no Jira e popula sua descrição com os casos de teste."""
    print(f"📝 Tentando criar sub-tarefa '[QA] Casos de Testes' no ticket {issue_id_pai}...")

    description_adf = markdown_para_adf(casos_de_teste_markdown)
    
    project_key = issue_id_pai.split('-')[0]

    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "parent": {
                "key": issue_id_pai
            },
            "summary": "[QA] Casos de Testes",
            "issuetype": {
                "id": JIRA_SUBTASK_ISSUE_TYPE_ID
            },
            "description": description_adf
        }
    }

    url = f"{JIRA_URL}/rest/api/3/issue"
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        subtask_info = response.json()
        print(f"✅ Sub-tarefa '{subtask_info['key']}' criada com sucesso no Jira.")
        print(f"🔗 Link da Sub-tarefa: {JIRA_URL}/browse/{subtask_info['key']}")
        return subtask_info['key']
    except requests.exceptions.RequestException as e:
        try:
            error_details = response.json()
            error_messages = error_details.get("errorMessages", [])
            errors = error_details.get("errors", {})
            detailed_error = ", ".join(error_messages) + " " + str(errors)
        except ValueError:
            detailed_error = str(e)
        raise Exception(f"❌ Erro ao criar sub-tarefa no Jira. Detalhes: {detailed_error}. Verifique permissões ou configurações do Jira.")


def main():
    """Função principal para executar o fluxo do script."""
    print("🚀 Iniciando o gerador de casos de teste para Jira...")
    issue_id = obter_id_historia()
    try:
        # Tenta buscar a descrição do Jira
        descricao_jira = buscar_descricao(issue_id)
        
        # Inicia a descrição para a IA com a descrição do Jira
        descricao_para_ia = descricao_jira

        # --- Parte 1: Perguntar por descrição adicional se a do Jira for limitada/vazia ---
        if "Descrição não fornecida." in descricao_jira or "Descrição existe, mas não foi possível extrair conteúdo textual." in descricao_jira:
            print("\n⚠️ A descrição do ticket no Jira é limitada ou vazia.")
            resposta = input("Deseja fornecer uma descrição adicional para a IA analisar? (s/n): ").strip().lower()
            if resposta == 's':
                print("Por favor, digite a descrição adicional (pressione Enter duas vezes para finalizar):")
                linhas_adicionais = []
                while True:
                    linha = input()
                    if not linha:
                        break
                    linhas_adicionais.append(linha)
                descricao_adicional = "\n".join(linhas_adicionais).strip()
                if descricao_adicional:
                    descricao_para_ia = f"{descricao_jira}\n\n--- Descrição Adicional do Usuário ---\n{descricao_adicional}"
                    print("✅ Descrição adicional capturada para a IA.")
                else:
                    print("Nenhuma descrição adicional fornecida. A IA usará a descrição original do Jira.")
            else:
                print("Continuando com a descrição original do Jira (pode ser limitada).")
        
        # Gera os testes com base na descrição (original + adicional, se houver)
        testes_gerados_ia = gerar_testes(descricao_para_ia)
        
        salvar_markdown(issue_id, testes_gerados_ia) # Salva a primeira versão dos testes

        print("\n---")
        print("Casos de teste gerados pela IA:")
        print(testes_gerados_ia) # Exibe os testes iniciais no console para revisão
        print("---\n")

        # --- Nova Parte: Perguntar se o usuário quer adicionar mais contexto para REFINAR os testes ---
        resposta_refinar = input("Deseja adicionar mais alguma informação ou contexto para refinar os testes gerados? (s/n): ").strip().lower()
        if resposta_refinar == 's':
            print("Por favor, digite as informações adicionais para refinar os testes (pressione Enter duas vezes para finalizar):")
            refinamentos_linhas = []
            while True:
                linha = input()
                if not linha:
                    break
                refinamentos_linhas.append(linha)
            refinamentos_texto = "\n".join(refinamentos_linhas).strip()

            if refinamentos_texto:
                # Cria um novo prompt para a IA, incluindo os testes já gerados e o pedido de refinamento
                prompt_refinamento = f"""
Os seguintes casos de teste foram gerados para a história de usuário (cuja descrição original você já analisou):
\"\"\"
{testes_gerados_ia}
\"\"\"

Por favor, refine ou adicione a esses casos de teste as seguintes informações/contextos adicionais fornecidos pelo usuário:
\"\"\"
{refinamentos_texto}
\"\"\"

Mantenha o formato OBRIGATÓRIO (CTXX - Validar..., Dado que..., Quando..., Então..., Validações:...) e gere a versão final dos casos de teste.
"""
                print("🧠 Refinando casos de teste com base na sua entrada (isso pode levar alguns segundos)...")
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response_refinada = model.generate_content(prompt_refinamento)
                    if response_refinada.text and response_refinada.text.strip():
                        testes_finais = response_refinada.text.strip()
                        print("\n---")
                        print("Casos de teste REFINADOS:")
                        print(testes_finais)
                        print("---\n")
                    else:
                        print("⚠️ A IA não conseguiu refinar os testes. Usando a versão original.")
                        testes_finais = testes_gerados_ia
                except Exception as e:
                    print(f"❌ Erro ao refinar testes com o Gemini: {e}. Usando a versão original.")
                    testes_finais = testes_gerados_ia
            else:
                print("Nenhuma informação de refinamento fornecida. Usando a versão original dos testes.")
                testes_finais = testes_gerados_ia
        else:
            testes_finais = testes_gerados_ia # Usa os testes gerados originalmente se não houver refinamento

        # Salva a versão FINAL dos testes (sobreescrevendo a anterior se houver refinamento)
        salvar_markdown(issue_id, testes_finais)

        # --- Parte final: Perguntar se quer criar a subtarefa ---
        resposta_criar = input("Deseja criar a sub-tarefa no Jira com esses casos de teste? (s/n): ").strip().lower()
        if resposta_criar == 's':
            criar_subtask_jira(issue_id, testes_finais) # Passa os testes finais
        else:
            print("🚫 Sub-tarefa não criada no Jira. Os casos de teste foram salvos apenas localmente.")

    except Exception as e:
        print(f"🛑 Ocorreu um erro: {e}")
        print("Certifique-se de que o ID do ticket está correto, suas credenciais do Jira estão válidas e sua chave da API do Gemini está funcional.")

if __name__ == "__main__":
    main()