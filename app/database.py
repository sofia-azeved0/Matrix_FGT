import mysql.connector
import pandas as pd
import os
import io

# Configurações - Senha: DCLvovMnTzrpXAM7XxKM
DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('DB_NAME', 'fortigate_matrix')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'DCLvovMnTzrpXAM7XxKM')

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tabela de Usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(255),
        role VARCHAR(20) DEFAULT 'admin',
        status ENUM('ativo', 'inativo') DEFAULT 'ativo'
    )
    """)

    # 2. Tabela Matrix (Garantindo as 31 colunas)
    # Se a tabela já existir sem a coluna 'cpus_threads', o comando abaixo NÃO a adiciona.
    # Por isso, adicionei comandos ALTER TABLE logo abaixo para garantir a compatibilidade.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matrix (
        id INT AUTO_INCREMENT PRIMARY KEY,
        model VARCHAR(100) UNIQUE,
        asic_version VARCHAR(100),
        cpu_model VARCHAR(255),
        cpus_threads VARCHAR(50),
        ram_mb VARCHAR(50),
        flash_mb VARCHAR(50),
        disk_mb VARCHAR(50),
        firewall_throughput VARCHAR(100),
        ipsec_throughput VARCHAR(100),
        ips_throughput VARCHAR(100),
        ngfw_throughput VARCHAR(100),
        threat_protection VARCHAR(100),
        firewall_latency VARCHAR(50),
        concurrent_sessions VARCHAR(100),
        new_sessions_sec VARCHAR(100),
        firewall_policies VARCHAR(100),
        max_gw_to_gw_tunnels VARCHAR(100),
        max_client_to_gw_tunnels VARCHAR(100),
        ssl_vpn_throughput VARCHAR(100),
        concurrent_ssl_users VARCHAR(100),
        ssl_inspection VARCHAR(100),
        app_control VARCHAR(100),
        max_fortiaps VARCHAR(100),
        max_fortiswitches VARCHAR(100),
        max_fortitokens VARCHAR(100),
        vdoms VARCHAR(50),
        interfaces TEXT,
        local_storage VARCHAR(255),
        power_supplies VARCHAR(255),
        form_factor VARCHAR(100),
        variants TEXT,
        status ENUM('ativo', 'inativo') DEFAULT 'ativo'
    )""")

    # TENTATIVA DE ADICIONAR COLUNAS FALTANTES (Caso a tabela já exista)
    try:
        cursor.execute("ALTER TABLE matrix ADD COLUMN cpus_threads VARCHAR(50) AFTER cpu_model")
    except: pass # Se a coluna já existir, ele apenas ignora
    
    try:
        cursor.execute("ALTER TABLE matrix ADD COLUMN flash_mb VARCHAR(50) AFTER ram_mb")
        cursor.execute("ALTER TABLE matrix ADD COLUMN disk_mb VARCHAR(50) AFTER flash_mb")
    except: pass

    # 3. Tabela de Dimensionamentos (Forms)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dimensionamentos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        zoho_number VARCHAR(50),
        cliente_nome VARCHAR(255),
        modelo_atual VARCHAR(100),
        usuarios_total INT,
        link_internet VARCHAR(100),
        throughput_requerido VARCHAR(100),
        observacoes TEXT,
        modelo_sugerido VARCHAR(100),
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('ativo', 'desativado') DEFAULT 'ativo'
    )""")
    
    conn.commit()
    cursor.close()
    conn.close()

def import_matrix_data():
    csv_path = '/app/data/matriz_completo.csv'
    if not os.path.exists(csv_path):
        return False, f"Arquivo não encontrado: {csv_path}"

    try:
        with open(csv_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read().strip()
        
        # Identifica separador e lê
        sep = ';' if ';' in content.split('\n')[0] else ','
        df = pd.read_csv(io.StringIO(content), sep=sep, engine='python').fillna("-")
        
        conn = get_connection()
        cursor = conn.cursor()

        for _, row in df.iterrows():
            vals = [str(v).strip() for v in row.values]
            if len(vals) < 5: continue
            while len(vals) < 31: vals.append("-")

            sql = """
            INSERT INTO matrix (
                model, asic_version, cpu_model, cpus_threads, ram_mb, flash_mb, disk_mb,
                firewall_throughput, ipsec_throughput, ips_throughput, ngfw_throughput, 
                threat_protection, firewall_latency, concurrent_sessions, new_sessions_sec, 
                firewall_policies, max_gw_to_gw_tunnels, max_client_to_gw_tunnels, 
                ssl_vpn_throughput, concurrent_ssl_users, ssl_inspection, app_control, 
                max_fortiaps, max_fortiswitches, max_fortitokens, vdoms, interfaces, 
                local_storage, power_supplies, form_factor, variants
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                firewall_throughput=VALUES(firewall_throughput),
                ips_throughput=VALUES(ips_throughput),
                concurrent_sessions=VALUES(concurrent_sessions)
            """
            cursor.execute(sql, tuple(vals[:31]))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, f"Sucesso! {len(df)} modelos importados."
    except Exception as e:
        return False, f"Erro na importação: {str(e)}"