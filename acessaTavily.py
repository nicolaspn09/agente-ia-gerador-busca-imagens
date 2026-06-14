import os
import re
import sys
import requests
import base64
import sobeImagensMinio
import sobeImagensFTPTablet
import moverArquivosBackup
import baixaImagensAPIColgate
from acessaBancosImagens import AcessaBancosImagens
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tavily import TavilyClient
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from PIL import Image, ImageOps

sys.path.append(r"C:\rpa\Python")
from Classes.ZimbraMailer.ZimbraMailer.Zimbra import ZimbraMailer


script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))

# --- CONFIGURAÇÕES ---
# Defina suas chaves aqui ou nas variáveis de ambiente
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Diretórios
DIR_TEMP = r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\Download Agente"
DIR_FINAL = r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\TransferirParaServidores"

# Criar diretórios se não existirem
os.makedirs(DIR_TEMP, exist_ok=True)
os.makedirs(DIR_FINAL, exist_ok=True)

# Clientes
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)


def envia_email(produtos_validos, produtos_invalidos):
    destinatarios_email = []
    destinatarios_email.append("nicolas.nasario@COMPANY_NAME.com.br")
    destinatarios_email.append("mario.viana@COMPANY_NAME.com.br")
    destinatarios_email.append("lucas.remor@COMPANY_NAME.com.br")
    destinatarios_email.append("davi.lopes@COMPANY_NAME.com.br")
    destinatarios_email.append("israel.martins@COMPANY_NAME.com.br")

    assunto = "Agente - Upload Imagens Mercadorias"

    # Contadores
    total_validos = len(produtos_validos)
    total_invalidos = len(produtos_invalidos)
    total_geral = total_validos + total_invalidos

    # Tabela de produtos VÁLIDOS
    if produtos_validos:
        linhas_validos = ""
        for cod, ean, tipo, descricao in produtos_validos:
            linhas_validos += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{cod}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{ean}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{tipo}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{descricao}</td>
            </tr>
            """
        tabela_validos = f"""
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr style="background-color: #28a745; color: white;">
                    <th style="padding: 10px; border: 1px solid #ddd;">Código</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">EAN</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Tipo</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Descrição</th>
                </tr>
            </thead>
            <tbody>
                {linhas_validos}
            </tbody>
        </table>
        """
    else:
        tabela_validos = "<p style='color: #666; font-style: italic;'>Nenhuma imagem foi carregada nesta execução.</p>"

    # Tabela de produtos INVÁLIDOS
    if produtos_invalidos:
        linhas_invalidos = ""
        for cod, ean, tipo, descricao in produtos_invalidos:
            linhas_invalidos += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{cod}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{ean}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{tipo}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{descricao}</td>
            </tr>
            """
        tabela_invalidos = f"""
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr style="background-color: #dc3545; color: white;">
                    <th style="padding: 10px; border: 1px solid #ddd;">Código</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">EAN</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Tipo</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Descrição</th>
                </tr>
            </thead>
            <tbody>
                {linhas_invalidos}
            </tbody>
        </table>
        """
    else:
        tabela_invalidos = "<p style='color: #666; font-style: italic;'>Todas as imagens foram carregadas com sucesso!</p>"

    # Resumo com badges
    mensagem = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .resumo {{ 
                background-color: #f8f9fa; 
                padding: 15px; 
                border-radius: 5px; 
                margin-bottom: 20px;
                border-left: 4px solid #007bff;
            }}
            .badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                margin-right: 10px;
            }}
            .badge-success {{ background-color: #28a745; color: white; }}
            .badge-danger {{ background-color: #dc3545; color: white; }}
            .badge-info {{ background-color: #17a2b8; color: white; }}
        </style>
    </head>
    <body>
        <h2 style="color: #333;">🤖 Agente de Upload de Imagens - Relatório de Execução</h2>
        
        <div class="resumo">
            <h3 style="margin-top: 0;">📊 Resumo da Execução</h3>
            <p>
                <span class="badge badge-info">Total: {total_geral}</span>
                <span class="badge badge-success">Sucesso: {total_validos}</span>
                <span class="badge badge-danger">Falhas: {total_invalidos}</span>
            </p>
            <p style="margin-bottom: 0;">
                Taxa de sucesso: <strong>{(total_validos/total_geral*100) if total_geral > 0 else 0:.1f}%</strong>
            </p>
        </div>

        <h3 style="color: #28a745;">✅ Imagens Carregadas com Sucesso ({total_validos})</h3>
        {tabela_validos}

        <h3 style="color: #dc3545;">❌ Imagens Não Carregadas ({total_invalidos})</h3>
        {tabela_invalidos}

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        
        <p style="color: #666; font-size: 14px;">
            Atenciosamente,<br>
            <strong>Equipe de RPA COMPANY_NAME</strong><br>
            <em>Automação Inteligente</em>
        </p>
    </body>
    </html>
    """

    ZimbraMailer().envia_email(assunto_email=assunto, mensagem_email=mensagem, destinatarios_email=destinatarios_email)


def encode_image(image_path):
    """Converte a imagem para base64 para enviar ao GPT."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def validar_imagem_gpt4o(caminho_imagem, descricao_produto):
    """
    Agora passamos a descrição para o GPT ajudar a validar se a imagem condiz com o texto.
    """
    base64_image = encode_image(caminho_imagem)

    print("==================================================")
    print(f"Analisando imagem: {caminho_imagem}")

    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini", #gpt-4o-mini #gpt-4.1-nano
            messages=[
                {
                    "role": "system",
                    "content": "Você é um validador de imagens de produtos para e-commerce. Seu objetivo é ACEITAR imagens válidas de produtos e REJEITAR apenas conteúdo claramente inadequado."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            # "text": (
                            #     f"Produto alvo: '{descricao_produto}'\n\n"
                            #     "Analise a imagem. Responda 'SIM' APENAS se:\n"
                            #     "1. A imagem for CLARAMENTE a embalagem FRONTAL (ou semelhante) do produto.\n"
                            #     "2. A imagem parecer corresponder à descrição do produto (ex: marca, tipo).\n\n"
                            #     "Responda 'NAO' para:\n"
                            #     "- Logotipos, Banners, Tabelas Nutricionais.\n"
                            #     "- Imagens borradas, cortadas ou com má qualidade.\n"
                            #     "- Imagens genéricas que não sejam do produto.\n"
                            #     "- Presença de logos, nomes ou marcas de drogarias/farmácias (ex: Drogaria São Paulo, Pacheco, Droga Raia, Pague Menos, etc).\n"
                            #     "- Produtos de marcas completamente diferentes da descrição.\n"
                            #     "Responda apenas com 'SIM' ou 'NAO'."
                            # )
                            "text": (
                                f"Produto esperado: '{descricao_produto}'\n\n"
                                "Analise esta imagem e responda APENAS 'SIM' ou 'NAO'.\n\n"
                                
                                "Responda 'SIM' se a imagem mostrar:\n"
                                "• Embalagem de produto (caixa, frascoister, sachê, tubo, pote, etc.)\n"
                                "• Produto em ângulo frontal)\n"
                                "• Produto com componentes (ex: caixa + sachês, frasco + tampa)\n"
                                "• Múltiplas unidades do mesmo produto\n"
                                "• Produto em fundo branco, colorido ou em contexto de uso\n"
                                "• Imagem com qualidade razoável (não precisa ser perfeita)\n\n"
                                
                                "Responda 'NAO' APENAS para:\n"
                                "• Logos de FARMÁCIAS/DROGARIAS (Drogaria São Paulo, Pacheco, Raia, Pague Menos, Ultrafarma,il, etc.)\n"
                                "• APENAS logo da marca (sem embalagem do produto)\n"
                                "• APENAS tabela nutricional ou bula (sem mostrar o produto)\n"
                                "• Banner promocional genérico sem produto visível\n"
                                "• Imagem totalmente borrada ou corrompida\n"
                                "• Produto que indica 'imagem restritiva' ou 'venda sob prescrição médica'\n"
                                "• Produto COMPLETAMENTE diferente (ex: descrição diz 'shampoo' mas a imagem é um 'remédio')\n\n"
                                
                                "⚠️ IMPORTANTE:\n"
                                "• Se houver QUALQUER embalagem de produto visível, responda SIM\n"
                                "• Variações de cor, tamanho ou apresentação são ACEITÁVEIS\n"
                                "• Produtos similares da mesma marca são ACEITÁVEIS\n"
                                "• Em caso de dúvida, ACEITE a imagem (SIM)\n\n"
                                
                                "Responda APENAS: SIM ou NAO"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=10,
            temperature=0.0
        )
        resultado = response.choices[0].message.content.strip().upper()
        # print(f"Análise GPT: {resultado}") 
        return "SIM" in resultado

    except Exception as e:
        print(f"Erro na API da OpenAI: {e}")
        return False


def fetch_images_from_page(page_url):
    """Acessa a página e extrai URLs de imagens."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    image_urls = []

    # FILTRO 1: Blacklist de domínios/padrões problemáticos
    dominios_bloqueados = [
        'mercadolivre.com.br',  # Geral do ML tem muitas imagens
        'fileformat.app',        # Site de ferramentas
        'tray.com.br',           # Base de conhecimento
        'facebook.com',
        'instagram.com',
        'youtube.com',
        'google.com',
        'collinsdictionary.com',
        'spanishdict.com',
        'dictionary.reverso.net',
        'spanishdictionary.cc',
        'homelessnesslearninghub.ca',
        'alibaba.com',
        'qrscanner.net',
        'zhihu.com',
        'itributacao.com.br',
        'ecommercenapratica.com',
        'sebrae.com.br',
        'your-online.ru',
        'pt.product-search.net',
        'products.aspose.app',
        'en.wikipedia.org',
        'drugs.com',
        'clubic.com',
        'dropboxforum.com'
    ]
    
    if any(dominio in page_url.lower() for dominio in dominios_bloqueados):
        print(f"URL bloqueada (domínio na blacklist): {page_url}")
        return []

    try:
        print(f"Acessando página: {page_url}")
        response = requests.get(page_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Estratégia: pegar todas as imagens, mas filtrar ícones muito pequenos depois
        img_tags = soup.find_all("img")

        for img in img_tags:
            img_url = img.get("src") or img.get("data-src")
            
            if not img_url:
                continue
                
            # FILTRO 2: Padrões de URL indesejados
            padroes_bloqueados = [
                'logo', 'icon', 'banner', 'sprite', 'thumb', 
                'avatar', 'badge', 'social', 'footer', 'header',
                'loading', 'placeholder', 'pixel', 'tracking',
                'gif', '.svg'  # GIFs e SVGs geralmente são ícones
            ]
            
            if any(padrao in img_url.lower() for padrao in padroes_bloqueados):
                continue
            
            # FILTRO 3: Apenas extensões válidas
            if not any(ext in img_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue
                
            full_img_url = urljoin(page_url, img_url)
            image_urls.append(full_img_url)
            
            # FILTRO 4: Limitar quantidade de imagens por página
            if len(image_urls) >= 20:  # Máximo X imagens por página
                print(f"Limite de 20 imagens atingido para esta página")
                break

        print(f"{len(image_urls)} imagens encontradas após filtros")
        return list(dict.fromkeys(image_urls))  # Remove duplicatas

    except Exception as e:
        print(f"Erro ao ler página {page_url}: {e}")
        return []


def download_image(url, nome_arquivo):
    """Baixa a imagem para a pasta temporária."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Filtro básico de tamanho para evitar ícones minúsculos (menos de 5KB)
            if len(response.content) < 5000: 
                return None
                
            caminho_completo = os.path.join(DIR_TEMP, nome_arquivo)
            with open(caminho_completo, 'wb') as f:
                f.write(response.content)
            return caminho_completo
    except:
        pass
    return None


def processar_imagem_final(caminho_origem, ean):
    """
    Redimensiona para 314x312 mantendo proporção (com fundo branco),
    converte para JPG e salva na pasta final.
    """
    target_size = (314, 314)
    caminho_destino = os.path.join(DIR_FINAL, f"{ean}.jpg")

    try:
        print("Processando imagem (Resize 314x314 + Convert to JPG)...")
        with Image.open(caminho_origem) as img:
            # 1. Converter para RGB (necessário para salvar como JPG se vier PNG com transparência)
            img = img.convert('RGB')

            # 2. Redimensionar mantendo aspecto e preenchendo com branco (Pad fit)
            # Usa LANCZOS para melhor qualidade de resampling
            processed_img = ImageOps.pad(img, target_size, method=Image.Resampling.LANCZOS, color='white', centering=(0.5, 0.5))

            # 3. Salvar como JPG com boa qualidade
            processed_img.save(caminho_destino, 'JPEG', quality=95)
            
        print(f"Imagem final salva em: {caminho_destino}")
        return True
        
    except Exception as e:
        print(f"Erro ao processar imagem final com Pillow: {e}")
        return False
    

def limpar_descricao(descricao):
    """
    Remove termos técnicos comuns de ERP que sujam a busca.
    Ajuste conforme sua base de dados.
    """
    # Remove quantidades em caixa ex: CX/12, C/24, UN
    descricao = re.sub(r'\b(CX|CX\/|C\/)\d+\b', '', descricao, flags=re.IGNORECASE)
    descricao = re.sub(r'\b(UN|UND)\b', '', descricao, flags=re.IGNORECASE)
    # Remove caracteres especiais
    descricao = re.sub(r'[^\w\s]', '', descricao)
    return descricao.strip()


def processar_produto(ean, descricao_bruta):
    print(f"\nIniciando busca para EAN: {ean} - {descricao_bruta}")

    descricao_limpa = limpar_descricao(descricao_bruta)
    
    queries = [
        {"tipo": "EAN", "q": f"Produto EAN {ean}"},
        {"tipo": "DESC", "q": f"{descricao_limpa}"}
    ]
    
    produto_resolvido = False

    for tentativa in queries:
        if produto_resolvido: 
            break
        
        print(f"Tentativa via {tentativa['tipo']}: '{tentativa['q']}'")
        
        try:
            search_result = tavily_client.search(
                query=tentativa['q'], 
                search_depth="advanced", 
                include_images=False, 
                max_results=3
            )
            urls_paginas = [r['url'] for r in search_result.get('results', [])]

        except Exception as e:
            print(f"Erro no Tavily: {e}")
            continue

        if not urls_paginas:
            print(f"Sem URLs retornadas para {tentativa['tipo']}.")
            continue

        for url_pagina in urls_paginas:
            if produto_resolvido: 
                break
            
            # print(f"   --- URL: {url_pagina}") # Opcional: descomentar para debug
            imagens_candidatas = fetch_images_from_page(url_pagina)
            
            if not imagens_candidatas: 
                continue

            for i, url_img in enumerate(imagens_candidatas):
                extensao_match = os.path.splitext(url_img.split('?')[0])[1]
                extensao = extensao_match.replace('.', '') if extensao_match else "jpg"
                if len(extensao) > 4 or extensao == "": 
                    extensao = "jpg"
                
                nome_temp = f"temp_{ean}_{tentativa['tipo']}_{i}.{extensao}"
                caminho_temp = download_image(url_img, nome_temp)
                
                if caminho_temp:
                    eh_frente = validar_imagem_gpt4o(caminho_temp, descricao_bruta)
                    
                    if eh_frente:
                        sucesso = processar_imagem_final(caminho_temp, ean)
                        if sucesso:
                            produto_resolvido = True
                            os.remove(caminho_temp)
                            break
                        else:
                            os.remove(caminho_temp)
                    else:
                        os.remove(caminho_temp)
        
        if not produto_resolvido:
            print(f"Falha na estratégia {tentativa['tipo']}.")

    if not produto_resolvido:
        print(f"FRACASSO TOTAL: Não foi possível encontrar imagem para {ean}")

    # --- AQUI ESTAVA FALTANDO O RETORNO ---
    return produto_resolvido



def main():
    # Busca as mercadorias novas no banco de dados
    try:
        tabela_produtos = AcessaBancosImagens().busca_produtos_novos()
    except Exception as e:
        print(e)

        destinatarios_email = []
        destinatarios_email.append("nicolas.nasario@COMPANY_NAME.com.br")
        destinatarios_email.append("lucas.remor@COMPANY_NAME.com.br")
        destinatarios_email.append("davi.lopes@COMPANY_NAME.com.br")
        destinatarios_email.append("israel.martins@COMPANY_NAME.com.br")

        assunto = "Erro no RPA do Tavily - Imagens MKT"

        mensagem = f"""
        <strong>Olá!</strong><br><br>

        Há erro ao acessar o banco de dados para a busca de produtos!<br>
        Bloco: AcessaBancosImagens().busca_produtos_novos()

        Erro: {e}
        """

        ZimbraMailer().envia_email(assunto_email=assunto, mensagem_email=mensagem, destinatarios_email=destinatarios_email)

    produto_encontrado = False
    produtos_encontrados = []
    produtos_nao_encontrados = []

    for mercadoria, ean, tipo_produto, nome_mercadoria in tabela_produtos:
        download_api = False
        caminho_produto_api = ""

        download_api, caminho_produto_api = baixaImagensAPIColgate.main(ean=ean)

        if download_api:
            sucesso = processar_imagem_final(caminho_produto_api, ean)
            if sucesso:
                os.remove(caminho_produto_api)
                
                produtos_encontrados.append((mercadoria, ean, tipo_produto, nome_mercadoria))

                banco = AcessaBancosImagens()
                banco.conectar()
                banco.atualiza_banco_pg(mercadoria[:-1])
                banco.desconectar()

                AcessaBancosImagens().inserir_novos_produtos(cd_mercadoria=mercadoria, ean=ean, tipo_mercadoria=tipo_produto, descricao_mercadoria=nome_mercadoria, status="Encontrado")

            else:
                os.remove(caminho_produto_api)

        else:
            produto_encontrado = processar_produto(ean, nome_mercadoria)

            if produto_encontrado:
                produtos_encontrados.append((mercadoria, ean, tipo_produto, nome_mercadoria))

                banco = AcessaBancosImagens()
                banco.conectar()
                banco.atualiza_banco_pg(mercadoria[:-1])
                banco.desconectar()

                AcessaBancosImagens().inserir_novos_produtos(cd_mercadoria=mercadoria, ean=ean, tipo_mercadoria=tipo_produto, descricao_mercadoria=nome_mercadoria, status="Encontrado")

            else:
                produtos_nao_encontrados.append((mercadoria, ean, tipo_produto, nome_mercadoria))

                AcessaBancosImagens().inserir_novos_produtos(cd_mercadoria=mercadoria, ean=ean, tipo_mercadoria=tipo_produto, descricao_mercadoria=nome_mercadoria, status="Não Encontrado")

    # Pega as imagens que não foram encontradas em até 3 dias
    try:
        produtos_sem_imagem = AcessaBancosImagens().buscar_mercadorias_sem_imagem()
    except Exception as e:
        print(e)

        destinatarios_email = []
        destinatarios_email.append("nicolas.nasario@COMPANY_NAME.com.br")
        destinatarios_email.append("lucas.remor@COMPANY_NAME.com.br")
        destinatarios_email.append("davi.lopes@COMPANY_NAME.com.br")
        destinatarios_email.append("israel.martins@COMPANY_NAME.com.br")

        assunto = "Erro no RPA do Tavily - Imagens MKT"

        mensagem = f"""
        <strong>Olá!</strong><br><br>

        Há erro ao acessar o banco de dados para a busca de produtos!<br>
        Bloco: AcessaBancosImagens().busca_produtos_novos()

        Erro: {e}
        """

        ZimbraMailer().envia_email(assunto_email=assunto, mensagem_email=mensagem, destinatarios_email=destinatarios_email)

    produto_encontrado = False

    for mercadoria, ean, tipo_produto, nome_mercadoria in produtos_sem_imagem:
        download_api = False
        caminho_produto_api = ""

        download_api, caminho_produto_api = baixaImagensAPIColgate.main(ean=ean)

        if download_api:
            sucesso = processar_imagem_final(caminho_produto_api, ean)
            if sucesso:
                os.remove(caminho_produto_api)
                
                produtos_encontrados.append((mercadoria, ean, tipo_produto, nome_mercadoria))

                banco = AcessaBancosImagens()
                banco.conectar()
                banco.atualiza_banco_pg(mercadoria[:-1])
                banco.desconectar()

                AcessaBancosImagens().inserir_novos_produtos(cd_mercadoria=mercadoria, ean=ean, tipo_mercadoria=tipo_produto, descricao_mercadoria=nome_mercadoria, status="Encontrado")
                
            else:
                os.remove(caminho_produto_api)

        else:
            produto_encontrado = processar_produto(ean, nome_mercadoria)

            if produto_encontrado:
                produtos_encontrados.append((mercadoria, ean, tipo_produto, nome_mercadoria))

                banco = AcessaBancosImagens()
                banco.conectar()
                banco.atualiza_banco_pg(mercadoria[:-1])
                banco.desconectar()

                AcessaBancosImagens().atualizar_status_mercadoria(cd_mercadoria=int(mercadoria), status="Encontrado")

            else:
                produtos_nao_encontrados.append((int(mercadoria), int(ean), tipo_produto, nome_mercadoria))

                AcessaBancosImagens().atualizar_status_mercadoria(cd_mercadoria=int(mercadoria), status="Não Encontrado")

    try:
        # Carrega as imagens para o minio da COMPANY_NAME
        sobeImagensMinio.main()
    except Exception as e:
        print(e)

        destinatarios_email = []
        destinatarios_email.append("nicolas.nasario@COMPANY_NAME.com.br")
        destinatarios_email.append("lucas.remor@COMPANY_NAME.com.br")
        destinatarios_email.append("davi.lopes@COMPANY_NAME.com.br")
        destinatarios_email.append("israel.martins@COMPANY_NAME.com.br")

        assunto = "Erro no RPA do Tavily - Imagens MKT"

        mensagem = f"""
        <strong>Olá!</strong><br><br>

        Há erro para subir as imagens para o Minio!<br>
        Bloco: sobeImagensMinio.main()

        Erro: {e}
        """

        ZimbraMailer().envia_email(assunto_email=assunto, mensagem_email=mensagem, destinatarios_email=destinatarios_email)

    try:
        # Carrega as imagens para o FTP do tablet
        sobeImagensFTPTablet.main()
    except Exception as e:
        print(e)

        destinatarios_email = []
        destinatarios_email.append("nicolas.nasario@COMPANY_NAME.com.br")
        destinatarios_email.append("lucas.remor@COMPANY_NAME.com.br")
        destinatarios_email.append("davi.lopes@COMPANY_NAME.com.br")
        destinatarios_email.append("israel.martins@COMPANY_NAME.com.br")

        assunto = "Erro no RPA do Tavily - Imagens MKT"

        mensagem = f"""
        <strong>Olá!</strong><br><br>

        Há erro para subir as imagens para o FTP!<br>
        Bloco: sobeImagensFTPTablet.main()

        Erro: {e}
        """

        ZimbraMailer().envia_email(assunto_email=assunto, mensagem_email=mensagem, destinatarios_email=destinatarios_email)

    # Move as imagens para o backup
    moverArquivosBackup.main()

    # Dispara o e-mail com os produtos com imagens e sem imagens
    envia_email(produtos_validos=produtos_encontrados, produtos_invalidos=produtos_nao_encontrados)


# --- EXECUÇÃO --- #
if __name__ == "__main__":
    main()