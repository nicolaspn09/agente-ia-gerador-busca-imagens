import asyncio
import json
import os
import requests
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# --- CONFIGURAÇÃO ---
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ajuste conforme o site que você vai mapear hoje
SITE_ALVO = "https://placeholder.lett.com.br/#/catalog"
TERMO_BUSCA = "7509546695631" 
PASTA_DOWNLOAD = r"C:\Users\Nícolas Nasário\Downloads\Teste Imagens"

# Credenciais para testar o código gerado depois
CREDENCIAIS_TESTE = {
    "usuario": "leandro_silva@colpal.com",
    "senha":   "Qq457979@"
}

logs_rede = []
urls_imagens_vistas = [] # Nova lista para ajudar a descobrir a Base URL

async def interceptar_trafego():
    print(f"\n🕵️ --- MODO ESPIÃO: {SITE_ALVO} ---")
    print("1. O navegador abrirá.")
    print("2. FAÇA O LOGIN.")
    print(f"3. FAÇA A BUSCA POR: {TERMO_BUSCA}")
    print("4. Quando a imagem do produto aparecer, FECHE O NAVEGADOR.")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Captura APIs (JSON)
        page.on("request", lambda request: capturar_api(request))
        # Captura Imagens (para descobrir a URL completa)
        page.on("request", lambda request: capturar_imagem(request))
        
        try:
            await page.goto(SITE_ALVO)
            await page.wait_for_event("close", timeout=0) 
        except:
            print("Navegador fechado. Processando...")

    return logs_rede, urls_imagens_vistas

def capturar_api(request):
    if request.resource_type in ["fetch", "xhr"]:
        try:
            # Tenta pegar o post data, limitando tamanho
            post_data = request.post_data[:1000] if request.post_data else None
        except:
            post_data = None
            
        logs_rede.append({
            "url": request.url,
            "method": request.method,
            "headers": request.headers,
            "post_data": post_data,
            "tipo": "API"
        })

def capturar_imagem(request):
    # Só nos interessa imagens que pareçam de produto (jpg, png, webp)
    if request.resource_type == "image":
        urls_imagens_vistas.append(request.url)

def gerar_driver_robusto(logs, imagens_vistas):
    print(f"📊 Analisando {len(logs)} requisições API e {len(imagens_vistas)} imagens...")
    
    # Filtra logs relevantes (auth ou o termo de busca)
    logs_uteis = [
        l for l in logs 
        if "login" in l['url'].lower() 
        or "auth" in l['url'].lower() 
        or "token" in l['url'].lower()
        or TERMO_BUSCA in str(l).replace("'", "") # Busca o termo no URL ou no Body
    ]
    
    # Encontra a imagem que corresponde ao produto (heurística simples)
    exemplo_imagem = imagens_vistas[0] if imagens_vistas else "Nenhuma imagem capturada"

    prompt_system = """
    Você é um Engenheiro Sênior de RPA Python.
    Sua tarefa é criar uma CLASSE `ConectorSite` para acessar uma API não documentada.

    ANÁLISE PROFUNDA NECESSÁRIA:
    1. Analise os logs de LOGIN. O token NÃO é sempre 'token'. Pode ser 'id', 'access_token', 'jwt', ou estar dentro de 'data'. 
       -> Crie um método `_extrair_token(self, response_json)` que tenta todas essas chaves com segurança.
    
    2. Analise os logs de BUSCA. Onde está a imagem?
       -> O JSON pode retornar um caminho parcial (ex: '/pic/123.jpg').
       -> Compare isso com a 'URL REAL DA IMAGEM' fornecida abaixo.
       -> Se forem diferentes, deduza a BASE_URL e faça a concatenação no código.
       -> O JSON de resposta é aninhado. Use `.get('data', {}).get('products', [])` ou similar. Não assuma raiz plana.

    3. ESTRUTURA DO CÓDIGO:
       - Use `requests`.
       - Método `login(self)`.
       - Método `buscar_imagem(self, token, ean)`.
       - Método `baixar_imagem(self, url, nome)`.
       - Inclua tratamento de erro `try/except`.
       - Se o login falhar, printe o JSON de resposta para debug.
    
    SAÍDA: Apenas o código Python. Sem markdown.
    """

    prompt_user = f"""
    LOGS DE REDE (APIS):
    {json.dumps(logs_uteis, indent=2)}

    URL REAL DA IMAGEM VISTA NO NAVEGADOR (Use para deduzir a Base URL):
    {exemplo_imagem}

    PASTA DE DOWNLOAD DESEJADA:
    r"{PASTA_DOWNLOAD}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ],
            temperature=0
        )
        return response.choices[0].message.content.replace("```python", "").replace("```", "")
    except Exception as e:
        print(f"Erro GPT: {e}")
        return ""

def testar_driver(codigo, credenciais, ean):
    print("\n🧪 --- TESTANDO DRIVER GERADO ---")
    try:
        # Executa o código gerado em um contexto local
        namespace = {}
        exec(codigo, globals(), namespace)
        
        ConectorSite = namespace.get('ConectorSite')
        if not ConectorSite:
            print("❌ Erro: Classe ConectorSite não encontrada no código gerado.")
            return

        print(f"🔑 Logando como {credenciais['usuario']}...")
        bot = ConectorSite(credenciais['usuario'], credenciais['senha'])
        token = bot.login()
        
        if token:
            print(f"✅ Token obtido: {str(token)[:15]}...")
            print(f"🔎 Buscando EAN {ean}...")
            url_img = bot.buscar_imagem(token, ean)
            
            if url_img:
                print(f"📸 URL Imagem: {url_img}")
                print("⬇️ Tentando baixar...")
                # Tenta chamar baixar_imagem se ela existir na classe ou como função solta
                if hasattr(bot, 'baixar_imagem'):
                    bot.baixar_imagem(url_img, f"{ean}.jpg")
                else:
                    print("⚠️ Função baixar_imagem não encontrada na classe.")
            else:
                print("❌ Imagem não encontrada na busca.")
        else:
            print("❌ Falha ao obter token.")

    except Exception as e:
        print(f"❌ Erro fatal ao rodar driver: {e}")
        # print(codigo) # Descomente se quiser ver onde quebrou

if __name__ == "__main__":
    logs, imagens = asyncio.run(interceptar_trafego())
    
    if logs:
        codigo_final = gerar_driver_robusto(logs, imagens)
        
        arquivo_saida = os.path.join(script_dir, r"C:\Users\Nícolas Nasário\Downloads\Teste Imagens\driver_gerado_robusto.py")
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write(codigo_final)
            
        print(f"\n📄 Código salvo em: {arquivo_saida}")
        print("-" * 40)
        print(codigo_final)
        print("-" * 40)
        
        resp = input("Quer testar agora? (s/n): ")
        if resp.lower() == 's':
            testar_driver(codigo_final, CREDENCIAIS_TESTE, TERMO_BUSCA)
    else:
        print("Sem dados capturados.")