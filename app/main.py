import streamlit as st
import pandas as pd
import re
import io
from auth import check_password, hash_password
from database import init_db, get_connection, import_matrix_data

# 1. Configuração Base
st.set_page_config(page_title="FortiGate Matrix", page_icon="⚡", layout="wide")

# --- FUNÇÕES AUXILIARES DE INTELIGÊNCIA ---

def parse_throughput(valor):
    """Converte '5 Gbps' ou '800 Mbps' em um float para comparação numérica."""
    if not valor or valor in ["-", "—", "unknown"]: return 0.0
    valor = str(valor).lower().replace(',', '.')
    match = re.search(r"(\d+\.?\d*)", valor)
    if not match: return 0.0
    num = float(match.group(1))
    if "gbps" in valor: return num * 1000
    return num

def extrair_total_portas(texto_interfaces):
    if not texto_interfaces or texto_interfaces == "-": return 0
    numeros = re.findall(r'(\d+)\s*[xX]', str(texto_interfaces))
    return sum(int(n) for n in numeros)

def main():
    try:
        init_db()
    except Exception as e:
        st.error(f"Erro crítico: {e}")
        st.stop()

    if not check_password():
        st.stop()

    user_role = st.session_state.get("user_role", "user")
    is_admin = (user_role == "admin")

    st.sidebar.title("MENU")
    menu = st.sidebar.radio(
        "Selecione uma opção:",
        ["Dashboard", "De/Para", "Comparador", "Matriz", "Forms", "Usuários"]
    )
    
    if st.sidebar.button("Sair"):
        st.session_state["authenticated"] = False
        st.rerun()

    # --- MÓDULO: DE/PARA (COM HARDWARE COMPLETO) ---
    if menu == "De/Para":
        st.title("🔄 Inteligência De/Para - Upgrade Linha G")
        
        try:
            conn = get_connection()
            df_all = pd.read_sql("SELECT * FROM matrix WHERE status = 'ativo'", conn)
            conn.close()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Equipamento Atual (Cliente)")
                modelo_atual_nome = st.selectbox("Selecione o modelo atual:", [""] + list(df_all['model'].unique()))
                
                if modelo_atual_nome:
                    atual = df_all[df_all['model'] == modelo_atual_nome].iloc[0]
                    portas_atuais = extrair_total_portas(atual['interfaces'])
                    
                    st.info(f"**Hardware Atual:** {atual['asic_version']} | {atual['ram_mb']} MB RAM")
                    st.write(f"**Portas Totais:** {portas_atuais}")

                    # Valores de referência para o filtro
                    fw_ref = parse_throughput(atual['firewall_throughput'])
                    tp_ref = parse_throughput(atual['threat_protection'])
                    ram_ref = parse_throughput(atual['ram_mb'])

            with col2:
                st.subheader("Sugestões Técnicas Selecionadas")
                if modelo_atual_nome:
                    portas_em_uso = st.number_input("Quantas portas estão em uso hoje?", min_value=0, value=portas_atuais)
                    
                    # Filtro: Linha G + Performance Superior ou Igual
                    df_g = df_all[df_all['model'].str.contains('G', case=False)]
                    sugestoes = []
                    
                    for _, sug in df_g.iterrows():
                        # Critério: FW e TP Throughput devem ser >= ao atual
                        if (parse_throughput(sug['firewall_throughput']) >= fw_ref and 
                            parse_throughput(sug['threat_protection']) >= tp_ref):
                            sugestoes.append(sug)

                    if sugestoes:
                        for sugerido in sugestoes:
                            with st.expander(f"⭐ Sugestão: {sugerido['model']}", expanded=True):
                                # Comparativo de Performance
                                st.write(f"**Throughput FW:** {sugerido['firewall_throughput']} (Atual: {atual['firewall_throughput']})")
                                st.write(f"**Threat Protection:** {sugerido['threat_protection']} (Atual: {atual['threat_protection']})")
                                
                                # Comparativo de Hardware (Nova Solicitação)
                                st.markdown("---")
                                st.write(f"**Processador:** {sugerido['asic_version']} (Atual: {atual['asic_version']})")
                                st.write(f"**Memória RAM:** {sugerido['ram_mb']} MB (Atual: {atual['ram_mb']} MB)")
                                
                                # Verificação de Portas
                                p_sug = extrair_total_portas(sugerido['interfaces'])
                                if p_sug < portas_em_uso:
                                    st.error(f"⚠️ **Alerta de Portas:** Possui {p_sug}, cliente usa {portas_em_uso}.")
                                else:
                                    st.success(f"✅ **Conectividade OK:** {p_sug} portas disponíveis.")
                    else:
                        st.warning("Nenhum modelo da Linha G atende aos requisitos mínimos de performance deste cenário.")

        except Exception as e: st.error(f"Erro no De/Para: {e}")

    # --- MÓDULO: MATRIZ (EDIÇÃO VERTICAL PERSISTENTE) ---
    elif menu == "Matriz":
        st.title("📊 Gestão da Matriz")
        try:
            conn = get_connection()
            df_all = pd.read_sql("SELECT * FROM matrix", conn)
            conn.close()

            modelo_edit = st.selectbox("Pesquise o modelo para editar:", [""] + list(df_all['model'].unique()))
            
            if modelo_edit:
                dados = df_all[df_all['model'] == modelo_edit].iloc[0]
                
                # Gerencia estado para não perder edição ao trocar de aba
                if f"edit_{modelo_edit}" not in st.session_state:
                    st.session_state[f"edit_{modelo_edit}"] = {c: str(dados[c]) for c in df_all.columns if c not in ['id', 'status']}
                    st.session_state[f"status_{modelo_edit}"] = dados['status']

                with st.form("form_edicao_vertical"):
                    st.markdown(f"### Detalhes Técnicos: {modelo_edit}")
                    c1, c2, c3 = st.columns(3)
                    campos = [c for c in df_all.columns if c not in ['id', 'status']]
                    novos_inputs = {}

                    for i, campo in enumerate(campos):
                        t_col = c1 if i % 3 == 0 else (c2 if i % 3 == 1 else c3)
                        novos_inputs[campo] = t_col.text_input(
                            campo.replace('_',' ').title(), 
                            value=st.session_state[f"edit_{modelo_edit}"][campo]
                        )
                    
                    status_op = st.selectbox("Status no Sistema", ["ativo", "inativo"], 
                                           index=0 if st.session_state[f"status_{modelo_edit}"] == "ativo" else 1)

                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        if is_admin:
                            conn = get_connection(); cursor = conn.cursor()
                            sets = ", ".join([f"{c} = %s" for c in novos_inputs.keys()])
                            cursor.execute(f"UPDATE matrix SET {sets}, status=%s WHERE model=%s", 
                                         list(novos_inputs.values()) + [status_op, modelo_edit])
                            conn.commit(); conn.close()
                            
                            # Atualiza estado e feedback
                            st.session_state[f"edit_{modelo_edit}"] = novos_inputs
                            st.session_state[f"status_{modelo_edit}"] = status_op
                            st.success(f"✅ Dados do {modelo_edit} salvos com sucesso!")
                            st.toast("Banco de dados atualizado!", icon='✅')
                        else:
                            st.error("Apenas administradores podem editar.")

            st.markdown("---")
            st.dataframe(df_all, use_container_width=True, hide_index=True)
        except Exception as e: st.error(e)

    # --- MÓDULO: COMPARADOR (ESTILO TUDOCELULAR) ---
    elif menu == "Comparador":
        st.title("⚖️ Comparador Lado a Lado")
        try:
            conn = get_connection()
            df_c = pd.read_sql("SELECT * FROM matrix WHERE status = 'ativo'", conn)
            conn.close()
            sel = st.multiselect("Selecione até 4 modelos:", df_c['model'].unique(), max_selections=4)
            if sel:
                # Transpõe para visualização vertical de campos
                comp_view = df_c[df_c['model'].isin(sel)].set_index('model').drop(columns=['id','status']).T
                st.table(comp_view)
        except Exception as e: st.error(e)

    # --- MÓDULOS DASHBOARD, FORMS E USUÁRIOS (PRESERVADOS) ---
    elif menu == "Dashboard":
        st.title("🚀 Dashboard")
        st.metric("Perfil", user_role.upper())

    elif menu == "Usuários":
        st.title("👥 Gestão de Usuários")
        
        if not is_admin:
            st.warning("⚠️ Somente administradores podem gerenciar usuários.")
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT username, role, status FROM usuarios")
                users = cursor.fetchall()
                for u in users:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{u['username']}**")
                    col2.write(f"Perfil: {u['role']}")
                    col3.write(f"Status: {u['status']}")
                cursor.close()
                conn.close()
            except:
                st.info("Nenhum usuário cadastrado.")
        else:
            t_lista, t_novo = st.tabs(["Listar Usuários", "Cadastrar Novo"])
            with t_lista:
                try:
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT id, username, role, status FROM usuarios")
                    users = cursor.fetchall()
                    for u in users:
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        col1.write(f"**{u['username']}**")
                        col2.write(f"Perfil: {u['role']}")
                        col3.write(f"Status: {u['status']}")
                        if col4.button("Inverter Status", key=f"status_{u['id']}"):
                            novo = 'inativo' if u['status'] == 'ativo' else 'ativo'
                            cursor.execute("UPDATE usuarios SET status = %s WHERE id = %s", (novo, u['id']))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    cursor.close()
                    conn.close()
                except:
                    st.info("Nenhum usuário no banco.")

            with t_novo:
                with st.form("novo_user_form", clear_on_submit=True):
                    st.subheader("Cadastrar Novo Usuário")
                    novo_u = st.text_input("Login")
                    novo_p = st.text_input("Senha", type="password")
                    novo_r = st.selectbox("Perfil", ["user", "admin"])
                    
                    if st.form_submit_button("Salvar"):
                        if novo_u and novo_p:
                            h = hash_password(novo_p)
                            try:
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute(
                                    "INSERT INTO usuarios (username, password, role) VALUES (%s, %s, %s)",
                                    (novo_u, h, novo_r)
                                )
                                conn.commit()
                                cursor.close()
                                conn.close()
                                st.success(f"Usuário {novo_u} ({novo_r}) criado!")
                            except:
                                st.error("Erro: Usuário já existe ou erro de DB.")
                        else:
                            st.warning("Preencha todos os campos.")

    elif menu == "Forms":
        st.title("📝 Formulário de Dimensionamento V3")
        st.info("Próximo passo: Integração com o banco de dimensionamentos.")

if __name__ == "__main__":
    main()