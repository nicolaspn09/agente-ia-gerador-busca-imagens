import subprocess
import sys
from pathlib import Path

def executar_espelhamento_minio():
    """
    Executa o espelhamento de diretório usando MinIO Client (mc.exe)
    com configuração prévia de codificação UTF-8.
    """
    
    # Definir os comandos que serão executados
    comando_chcp = "chcp 65001"
    comando_minio = r'C:\mc\mc.exe mirror --overwrite "C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\TransferirParaServidores" eCOMPANY_NAME/produtos'
    
    # Combinar comandos usando && para executar na mesma sessão
    # O && garante que o segundo comando só executa se o primeiro for bem-sucedido
    comando_completo = f'{comando_chcp} && {comando_minio}'
    
    print("=" * 80)
    print("INICIANDO PROCESSO DE ESPELHAMENTO MINIO")
    print("=" * 80)
    print(f"\nComandos a serem executados:")
    print(f"1. {comando_chcp}")
    print(f"2. {comando_minio}")
    print("\n" + "=" * 80 + "\n")
    
    try:
        # Executar os comandos combinados no CMD
        # shell=True: necessário para executar comandos internos do CMD como 'chcp'
        # text=True: retorna strings em vez de bytes
        # capture_output=True: captura stdout e stderr
        # encoding='utf-8': define a codificação para leitura da saída
        processo = subprocess.run(
            comando_completo,
            shell=True,
            text=True,
            capture_output=True,
            encoding='utf-8',
            errors='replace'  # Substitui caracteres inválidos em vez de falhar
        )
        
        # Exibir saída padrão (stdout)
        if processo.stdout:
            print("SAÍDA DO PROCESSO:")
            print("-" * 80)
            print(processo.stdout)
            print("-" * 80)
        
        # Exibir erros (stderr) se houver
        if processo.stderr:
            print("\nMENSAGENS DE ERRO/AVISO:")
            print("-" * 80)
            print(processo.stderr)
            print("-" * 80)
        
        # Verificar código de retorno
        if processo.returncode == 0:
            print("\nPROCESSO CONCLUÍDO COM SUCESSO!")
            print(f"Código de retorno: {processo.returncode}")
            return True
        else:
            print(f"\nPROCESSO FALHOU!")
            print(f"Código de retorno: {processo.returncode}")
            return False
            
    except FileNotFoundError:
        print("ERRO: mc.exe não foi encontrado no caminho especificado.")
        print("Verifique se o arquivo existe em: C:\\mc\\mc.exe")
        return False
        
    except subprocess.SubprocessError as e:
        print(f"ERRO ao executar subprocess: {e}")
        return False
        
    except Exception as e:
        print(f"ERRO inesperado: {type(e).__name__} - {e}")
        return False


def validar_prerequisitos():
    """
    Valida se os arquivos e diretórios necessários existem antes da execução.
    """
    mc_path = Path(r"C:\mc\mc.exe")
    origem_path = Path(r"C:\rpa\Marketing\ImagensMercadorias\ImagensParaUpload\TransferirParaServidores")
    
    problemas = []
    
    if not mc_path.exists():
        problemas.append(f"mc.exe não encontrado em: {mc_path}")
    
    if not origem_path.exists():
        problemas.append(f"Diretório de origem não encontrado: {origem_path}")
    elif not origem_path.is_dir():
        problemas.append(f"O caminho de origem não é um diretório: {origem_path}")
    
    if problemas:
        print("\nPROBLEMAS DETECTADOS:\n")
        for problema in problemas:
            print(problema)
        print("\nCorreja os problemas antes de continuar.\n")
        return False
    
    print("Todos os pré-requisitos validados com sucesso!\n")
    return True


# Execução principal
def main():
    print("\nSCRIPT DE ESPELHAMENTO MINIO\n")
    
    # Validar pré-requisitos antes de executar
    if validar_prerequisitos():
        sucesso = executar_espelhamento_minio()
        
        return sucesso
    else:
        return False


if __name__ == "__main__":
    main()