import shutil
import sys
from pathlib import Path
from datetime import datetime

def mover_imagens_para_backup():
    """
    Move arquivos JPG do diretório de transferência para pasta de backup
    organizada por data no formato dd_MM_yyyy.
    """
    
    # Configurações de diretórios
    DIRETORIO_ORIGEM = r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\TransferirParaServidores"
    DIRETORIO_BACKUP_BASE = r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\Backup"
    
    # Obter data atual no formato dd_MM_yyyy
    data_atual = datetime.now().strftime("%d_%m_%Y")
    
    # Criar caminho completo do backup com a data
    diretorio_backup_completo = Path(DIRETORIO_BACKUP_BASE) / data_atual
    
    print("=" * 80)
    print("MOVENDO IMAGENS PARA BACKUP")
    print("=" * 80)
    print(f"\nOrigem: {DIRETORIO_ORIGEM}")
    print(f"Destino: {diretorio_backup_completo}")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\n" + "=" * 80 + "\n")
    
    # Validar diretório de origem
    caminho_origem = Path(DIRETORIO_ORIGEM)
    if not caminho_origem.exists():
        print(f"ERRO: Diretório de origem não encontrado: {DIRETORIO_ORIGEM}")
        return False
    
    # Buscar todos os arquivos JPG (case-insensitive)
    arquivos_jpg = list(caminho_origem.glob("*.jpg"))
    
    if not arquivos_jpg:
        print("AVISO: Nenhum arquivo .jpg encontrado no diretório de origem.")
        print("Nada para mover.")
        return True  # Não é erro, apenas não há arquivos
    
    print(f"Total de arquivos encontrados: {len(arquivos_jpg)}")
    print("-" * 80)
    
    # Criar diretório de backup se não existir
    try:
        diretorio_backup_completo.mkdir(parents=True, exist_ok=True)
        print(f"Diretório de backup criado/verificado: {diretorio_backup_completo}\n")
    except Exception as e:
        print(f"ERRO ao criar diretório de backup: {e}")
        return False
    
    # Mover arquivos
    arquivos_movidos = 0
    arquivos_com_erro = 0
    
    print("Movendo arquivos...")
    print("-" * 80)
    
    for arquivo in arquivos_jpg:
        nome_arquivo = arquivo.name
        destino = diretorio_backup_completo / nome_arquivo
        tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
        
        try:
            print(f"Movendo: {nome_arquivo} ({tamanho_mb:.2f} MB)... ", end="", flush=True)
            
            # Verificar se arquivo já existe no destino
            if destino.exists():
                print("JÁ EXISTE (pulando)")
                arquivos_com_erro += 1
                continue
            
            # Mover arquivo
            shutil.move(str(arquivo), str(destino))
            
            print("OK")
            arquivos_movidos += 1
            
        except PermissionError:
            print("ERRO DE PERMISSÃO")
            arquivos_com_erro += 1
            
        except Exception as e:
            print(f"ERRO: {type(e).__name__} - {e}")
            arquivos_com_erro += 1
    
    print("-" * 80)
    print(f"\nRESUMO DA OPERAÇÃO:")
    print(f"Arquivos movidos com sucesso: {arquivos_movidos}")
    print(f"Arquivos com erro/pulados: {arquivos_com_erro}")
    print(f"Total processado: {len(arquivos_jpg)}")
    print(f"Localização do backup: {diretorio_backup_completo}")
    
    print("\n" + "=" * 80)
    
    return arquivos_movidos > 0 or len(arquivos_jpg) == 0


def listar_arquivos_restantes():
    """
    Lista arquivos que ainda restam no diretório de origem após a movimentação.
    Útil para verificar se a operação foi completa.
    """
    caminho_origem = Path(r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\TransferirParaServidores")
    arquivos_restantes = list(caminho_origem.glob("*.jpg")) + list(caminho_origem.glob("*.JPG"))
    
    if arquivos_restantes:
        print("\nATENÇÃO: Ainda existem arquivos no diretório de origem:")
        print("-" * 80)
        for arquivo in arquivos_restantes:
            print(f"   📄 {arquivo.name}")
        print("-" * 80)
    else:
        print("\nDiretório de origem está vazio (todos os arquivos foram movidos).")


def main():
    print("SCRIPT DE BACKUP DE IMAGENS\n")
    
    # Executar movimentação
    sucesso = mover_imagens_para_backup()
    
    # Listar arquivos restantes
    listar_arquivos_restantes()
    
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