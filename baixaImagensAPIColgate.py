import os
import requests
from dotenv import load_dotenv, find_dotenv


# --- CONFIGURAÇÕES ---
DIR_TEMP = r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\Download Agente"

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))
USUARIO = os.getenv("LETT_USER")
SENHA = os.getenv("LETT_PASS")


def fazer_login():
    """Realiza login e retorna o TOKEN de autorização."""
    print("🔑 Tentando fazer login...")
    
    url = 'https://api-placeholder.lett.com.br/api/Operator/login'
    
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://placeholder.lett.com.br',
        'referer': 'https://placeholder.lett.com.br/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    }
    
    params = {'include': 'user'}
    data = {'username': USUARIO, 'password': SENHA}

    try:
        # Usa data= para x-www-form-urlencoded
        response = requests.post(url, params=params, headers=headers, data=data)
        
        if response.status_code == 200:
            dados = response.json()
            # Tenta pegar o token (Ajuste a chave 'id' se o JSON de resposta for diferente)
            # Geralmente é 'id', 'token' ou 'access_token'
            token = dados.get('id') or dados.get('token') or dados.get('access_token')
            
            if token:
                print(f"✅ Login com sucesso! Token: {token[:10]}...")
                return token
            else:
                print("❌ Login funcionou, mas não achei o campo do token no JSON.")
                print("JSON recebido:", dados)
        else:
            print(f"❌ Erro no login: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Erro de conexão no login: {e}")
    
    return None

def baixar_imagem(url, nome_arquivo):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            caminho_completo = os.path.join(DIR_TEMP, nome_arquivo)
            with open(caminho_completo, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"💾 Imagem salva em: {caminho_completo}")
            return True, os.path.join(DIR_TEMP, nome_arquivo)
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")
    return False, ""

def buscar_produto(token, ean):
    print(f"🔎 Buscando produto {ean}...")
    
    url = 'https://api-placeholder.lett.com.br/api/Lett/getProductsWithStatistics'
    
    headers = {
        'accept': '*/*',
        'authorization': token, # Token dinâmico aqui
        'content-type': 'application/json',
        'origin': 'https://placeholder.lett.com.br',
        'referer': 'https://placeholder.lett.com.br/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    }
    
    json_data = {
        'query': str(ean),
        'supplierIds': [], 'countryId': [], 'brandIds': [], 'brickIds': [], 'offset': 0
    }

    download = False
    local_download = ""

    try:
        response = requests.post(url, headers=headers, json=json_data)
        
        if response.status_code == 200:
            dados = response.json()
            produtos = dados.get('data', {}).get('products', [])
            
            if produtos:
                prod = produtos[0]
                imagens = prod.get('picPrimary', [])
                
                if imagens:
                    caminho_parcial = imagens[0].get('processed_url')
                    # Base URL fixa que descobrimos
                    base_url = "https://image-server-media.lett.com.br/image-handler-view/fit-in/1000x1000/filters:quality(80)/"
                    url_final = base_url + caminho_parcial
                    
                    print(f"📸 Imagem encontrada: {url_final}")
                    download, local_download = baixar_imagem(url_final, f"{ean}.jpg")
                else:
                    print("⚠️ Produto encontrado, mas sem imagem.")
            else:
                print("❌ Produto não encontrado na busca.")
        else:
            print(f"Erro na busca: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Erro crítico na busca: {e}")

    finally:
        return download, local_download

def main(ean):
    download = False
    local_download = ""
    token_sessao = fazer_login()
    
    if token_sessao:
        download, local_download = buscar_produto(token_sessao, ean)
    
    return download, local_download