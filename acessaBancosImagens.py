import os
import sys
import psycopg2
from psycopg2 import Error
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv

sys.path.append(r"C:\rpa\Python")

from Classes.Oracle.Oracle.ConectaOracle import ConectaOracle
from Classes.Postgres.Postgres.ConectaPG import ConectaPG


script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))


class AcessaBancosImagens:
    def __init__(self):
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT")
        self.pg_database = os.getenv("PG_DATABASE")
        self.pg_user = os.getenv("PG_USER")
        self.pg_password = os.getenv("PG_PASSWORD")
        self.connection = None
        self.cursor = None

    
    def conectar(self):
        try:
            self.connection = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password
            )
            self.cursor = self.connection.cursor()
            return True
        except Error as e:
            print(f"Erro ao conectar ao PostgreSQL: {e}")
            return False

    
    def desconectar(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    
    def atualiza_banco_pg(self, codigo_mercadoria):
        try:
            sql = f"""
            UPDATE prddm.dc_mercadoria
            SET id_imagem = 'true'
            WHERE cd_mercadoria IN ({codigo_mercadoria})
            """

            self.cursor.execute(sql)
            self.connection.commit()
        
        except Exception as e:
            print(e)            
            self.connection.rollback()

    
    def busca_produtos_novos(self):
        # Calcular ontem e hoje
        hoje = datetime.now()
        ontem = hoje - timedelta(days=3)

        # Formatar no padrão DD/MM/YYYY
        data_ontem = ontem.strftime('%d/%m/%Y')
        data_hoje = hoje.strftime('%d/%m/%Y')

        sql = f"""
        SELECT AUD.NR_MERCADORIA||MERC.NR_DV_MERCADORIA, CD_EAN_VENDA, DECODE(DS_NIVEL_ECNM, 1, 'MEDICAMENTO', 2, 'NÃO MEDICAMENTO'), DS_MERCADORIA
        FROM PRDDM.DC_AUDITORIA_PRODUTO AUD, PRDDM.DC_MERCADORIA MERC
        WHERE AUD.NR_MERCADORIA = MERC.CD_MERCADORIA
        AND AUD.DT_ATUALIZACAO BETWEEN '{data_ontem}' AND '{data_hoje}'
        AND AUD.ID_POSICAO_CADASTRO = 'C'
        AND (
            (DS_NIVEL_ECNM = 1 AND DS_NIVEL_ERGM = 37)
            OR 
            DS_NIVEL_ECNM = 2
        )
        GROUP BY AUD.NR_MERCADORIA||MERC.NR_DV_MERCADORIA, CD_EAN_VENDA, DS_NIVEL_ECNM, DS_MERCADORIA
        """

        tabela = ConectaOracle(sql=sql).conecta_oracle()

        return tabela
    

    def inserir_novos_produtos(self, cd_mercadoria, ean, tipo_mercadoria, descricao_mercadoria, status):
        sql = f"""
        INSERT INTO MARKETING.IMAGENS_MERCADORIAS (CD_MERCADORIA, EAN, TIPO_MERCADORIA, DESCRICAO_MERCADORIA, DT_INICIO_PESQUISA, DT_ATUALIZACAO, STATUS ) VALUES ({cd_mercadoria}, {ean}, '{tipo_mercadoria}', '{descricao_mercadoria}', '{datetime.now()}', '{datetime.now()}', '{status}')
        """

        ConectaPG(sql=sql).conecta_pg_insert()

    
    def buscar_mercadorias_sem_imagem(self):
        # Calcular ontem e hoje
        hoje = datetime.now()
        data_antiga = hoje - timedelta(days=9)
        ontem = hoje - timedelta(days=10)

        # Formatar no padrão DD/MM/YYYY
        data_ontem = data_antiga.strftime('%d/%m/%Y')
        data_hoje = ontem.strftime('%d/%m/%Y')

        sql = f"""
        SELECT CD_MERCADORIA, EAN, TIPO_MERCADORIA, DESCRICAO_MERCADORIA FROM MARKETING.IMAGENS_MERCADORIAS
        WHERE DT_INICIO_PESQUISA::DATE BETWEEN '{data_hoje}' AND '{data_ontem}'
        AND STATUS IN ('Não Encontrado', 'Pendente')
        """

        tabela = ConectaPG(sql=sql).conecta_pg()

        return tabela
    

    def atualizar_status_mercadoria(self, cd_mercadoria, status):
        sql = f"""
        UPDATE MARKETING.IMAGENS_MERCADORIAS
        SET STATUS = '{status}', DT_ATUALIZACAO = '{datetime.now()}'
        WHERE CD_MERCADORIA = {cd_mercadoria}
        """

        ConectaPG(sql=sql).conecta_pg_insert()