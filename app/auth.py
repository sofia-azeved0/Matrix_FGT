import streamlit as st
import bcrypt
from database import get_connection

def hash_password(password):
    """Gera hash seguro para novas senhas."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_hashes(password, hashed):
    """Compara senha digitada com o hash do banco."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def check_password():
    """Gerencia a tela de login e persistência da sessão."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("<h1 style='text-align: center; color: #00d4ff;'>FortiGate Matrix</h1>", unsafe_allow_html=True)
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                user_input = st.text_input("Usuário", key="login_user")
                pw_input = st.text_input("Senha", type="password", key="login_pw")
                
                if st.button("Entrar", use_container_width=True):
                    # 1. VERIFICAÇÃO HARDCODE (Prioridade para evitar erros de DB no admin)
                    if user_input == "admin" and pw_input == "DCLvovMnTzrpXAM7XxKM":
                        st.session_state["authenticated"] = True
                        st.session_state["user_role"] = "admin"
                        st.rerun()

                    # 2. VERIFICAÇÃO NO BANCO DE DADOS
                    try:
                        conn = get_connection()
                        cursor = conn.cursor(dictionary=True)
                        query = "SELECT password, role FROM usuarios WHERE username = %s AND status = 'ativo'"
                        cursor.execute(query, (user_input,))
                        result = cursor.fetchone()
                        cursor.close()
                        conn.close()

                        if result and check_hashes(pw_input, result['password']):
                            st.session_state["authenticated"] = True
                            st.session_state["user_role"] = result['role']
                            st.rerun()
                        else:
                            st.error("Usuário ou senha inválidos.")
                    except Exception as e:
                        # Se for erro de DB, avisa mas não trava o processamento se for nova tentativa
                        st.error("Erro ao consultar base de dados. Verifique a conexão do container.")
        return False
    return True