import os
import ftplib
import sys
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv, find_dotenv


def upload_imagens_ftp():
    """
    Realiza upload de arquivos JPG para servidor FTP do tablet.
    Substitui a sequência de comandos FTP do CMD de forma mais robusta.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))
    
    # Configurações do servidor FTP
    FTP_HOST = os.getenv("FTP_HOST")
    FTP_USER = os.getenv("FTP_USER")
    FTP_PASS = os.getenv("FTP_PASS")
    DIRETORIO_LOCAL = r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\TransferirParaServidores"
    
    print("=" * 80)
    print("INICIANDO UPLOAD FTP PARA SERVIDOR DO TABLET")
    print("=" * 80)
    print(f"\nServidor: {FTP_HOST}")
    print(f"Usuário: {FTP_USER}")
    print(f"Diretório local: {DIRETORIO_LOCAL}")
    print(f"Horário de início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\n" + "=" * 80 + "\n")
    
    # Validar se o diretório local existe
    caminho_local = Path(DIRETORIO_LOCAL)
    if not caminho_local.exists():
        print(f"ERRO: Diretório local não encontrado: {DIRETORIO_LOCAL}")
        return False
    
    # Buscar todos os arquivos JPG (case-insensitive)
    arquivos_jpg = list(caminho_local.glob("*.jpg")) + list(caminho_local.glob("*.JPG"))
    
    if not arquivos_jpg:
        print("AVISO: Nenhum arquivo .jpg encontrado no diretório.")
        print("Nada para enviar.")
        return True  # Não é erro, apenas não há arquivos
    
    print(f"Total de arquivos encontrados: {len(arquivos_jpg)}")
    print("-" * 80)
    
    ftp = None
    arquivos_enviados = 0
    arquivos_com_erro = 0
    
    try:
        # Conectar ao servidor FTP
        print("🔌 Conectando ao servidor FTP...")
        ftp = ftplib.FTP(timeout=30)  # Timeout de 30 segundos
        ftp.connect(FTP_HOST, 21)
        
        # Fazer login
        print("Realizando autenticação...")
        ftp.login(FTP_USER, FTP_PASS)
        
        # Exibir mensagem de boas-vindas do servidor
        print(f"Conectado com sucesso!")
        print(f"Mensagem do servidor: {ftp.getwelcome()}")
        print()
        
        # Configurar modo binário (importante para imagens)
        ftp.set_pasv(True)  # Modo passivo (melhor compatibilidade com firewalls)
        
        # Enviar cada arquivo JPG
        print("Iniciando upload dos arquivos...")
        print("-" * 80)
        
        for arquivo in arquivos_jpg:
            nome_arquivo = arquivo.name
            tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
            
            try:
                print(f"Enviando: {nome_arquivo} ({tamanho_mb:.2f} MB)... ", end="", flush=True)
                
                # Abrir arquivo em modo binário e enviar
                with open(arquivo, 'rb') as file:
                    # STOR = comando FTP para armazenar arquivo
                    ftp.storbinary(f'STOR {nome_arquivo}', file)
                
                print("OK")
                arquivos_enviados += 1
                
            except ftplib.error_perm as e:
                print(f"ERRO DE PERMISSÃO: {e}")
                arquivos_com_erro += 1
                
            except Exception as e:
                print(f"ERRO: {type(e).__name__} - {e}")
                arquivos_com_erro += 1
        
        print("-" * 80)
        print(f"\nRESUMO DO UPLOAD:")
        print(f"Arquivos enviados com sucesso: {arquivos_enviados}")
        print(f"Arquivos com erro: {arquivos_com_erro}")
        print(f"Total processado: {len(arquivos_jpg)}")
        
        # Considerar sucesso se pelo menos um arquivo foi enviado
        return arquivos_enviados > 0
        
    except ftplib.error_perm as e:
        print(f"\nERRO DE AUTENTICAÇÃO/PERMISSÃO: {e}")
        print("Verifique usuário e senha.")
        return False
        
    except ftplib.error_temp as e:
        print(f"\nERRO TEMPORÁRIO DO SERVIDOR: {e}")
        print("Tente novamente mais tarde.")
        return False
        
    except ConnectionRefusedError:
        print(f"\nERRO: Conexão recusada pelo servidor {FTP_HOST}")
        print("Verifique se o servidor FTP está ativo e acessível.")
        return False
        
    except TimeoutError:
        print(f"\nERRO: Timeout ao conectar com {FTP_HOST}")
        print("Verifique a conexão de rede.")
        return False
        
    except OSError as e:
        print(f"\nERRO DE REDE: {e}")
        print("Verifique a conectividade com o servidor.")
        return False
        
    except Exception as e:
        print(f"\nERRO INESPERADO: {type(e).__name__} - {e}")
        return False
        
    finally:
        # Sempre fechar a conexão FTP
        if ftp:
            try:
                print("\n🔌 Encerrando conexão FTP...")
                ftp.quit()
                print("Desconectado com sucesso!")
            except:
                # Se quit() falhar, forçar o fechamento
                try:
                    ftp.close()
                except:
                    pass
        
        print(f"\nHorário de término: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)


def validar_conectividade(host):
    """
    Testa conectividade básica com o servidor antes de tentar FTP.
    """
    print(f"Testando conectividade com {host}...")
    
    # Ping simples (funciona no Windows)
    response = os.system(f"ping -n 1 -w 1000 {host} > nul 2>&1")
    
    if response == 0:
        print(f"Servidor {host} está acessível na rede.\n")
        return True
    else:
        print(f"AVISO: Servidor {host} não responde ao ping.")
        print("Tentando conexão FTP mesmo assim...\n")
        return False


def main():
    print("\nSCRIPT DE UPLOAD FTP - SERVIDOR TABLET\n")
    
    # Testar conectividade (opcional, não bloqueia execução)
    validar_conectividade("10.1.1.69")
    
    # Executar upload
    sucesso = upload_imagens_ftp()
    
    # Definir código de saída
    if sucesso:
        print("\nPROCESSO FINALIZADO COM SUCESSO!")
        return True
    else:
        print("\nPROCESSO FINALIZADO COM ERROS!")
        return False

# Execução principal
if __name__ == "__main__":
    main()