import os
import requests

DIR_DOWNLOAD = r"C:\Users\Nícolas Nasário\Downloads\Teste Imagens"


class ConectorSite:
    def __init__(self, usuario, senha):
        self.usuario = usuario
        self.senha = senha
        self.base_url = "https://api-placeholder.lett.com.br/api"

    def login(self) -> str:
        url = f"{self.base_url}/Operator/login?include=user"
        headers = {
            "sec-ch-ua-platform": "\"Windows\"",
            "referer": "https://placeholder.lett.com.br/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "accept": "*/*",
            "sec-ch-ua": "\"Not:A-Brand\";v=\"24\", \"Chromium\";v=\"134\"",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "sec-ch-ua-mobile": "?0"
        }
        data = {
            "username": self.usuario,
            "password": self.senha
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        dados = response.json()
        token = dados.get('id') or dados.get('token') or dados.get('access_token')

        return token

    def buscar_imagem(self, token, ean) -> str:
        url = f"{self.base_url}/Lett/getProductsWithStatistics"
        headers = {
            "sec-ch-ua-platform": "\"Windows\"",
            "authorization": token,
            "referer": "https://placeholder.lett.com.br/",
            "sec-ch-ua": "\"Not:A-Brand\";v=\"24\", \"Chromium\";v=\"134\"",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "accept": "*/*",
            "content-type": "application/json"
        }
        data = {
            "query": ean,
            "supplierIds": [],
            "countryId": [],
            "brandIds": [],
            "brickIds": [],
            "offset": 0
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
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
                baixar_imagem(url_final, f"{ean}.jpg")
            else:
                print("⚠️ Produto encontrado, mas sem imagem.")
        else:
            print("❌ Produto não encontrado na busca.")

def baixar_imagem(url, nome_arquivo):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            caminho_completo = os.path.join(DIR_DOWNLOAD, nome_arquivo)
            with open(caminho_completo, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"💾 Imagem salva em: {caminho_completo}")
            return True
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")
    return False
    

conector = ConectorSite(usuario="leandro_silva@colpal.com", senha = 'REMOVED_FOR_GITHUB')
token = conector.login()
imagem = conector.buscar_imagem(token=token, ean="7509546695631")