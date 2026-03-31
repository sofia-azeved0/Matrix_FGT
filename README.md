# ⚡ FortiGate Matrix

O **FortiGate Matrix** é uma ferramenta de apoio técnico para pré-vendas e engenharia de redes, focada no dimensionamento e comparação de ativos Fortinet. O sistema permite analisar a performance de modelos legados e sugerir upgrades precisos para a nova **Linha G**, levando em conta throughput, hardware e conectividade física.

---

## 🚀 Funcionalidades Principais

* **Inteligência De/Para:** Analisa o modelo atual do cliente e sugere substitutos na Linha G que possuam performance (FW, TP, IPS, RAM) igual ou superior.
* **Validação de Portas:** Verifica se o novo modelo atende à quantidade de portas físicas em uso no cenário atual.
* **Comparador Técnico:** Visualização lado a lado (estilo "TudoCelular") de até 4 modelos simultâneos.
* **Gestão de Matriz:** Edição vertical simplificada de 31 colunas de especificações técnicas.
* **Controle de Acesso:** Sistema de autenticação com perfis de `Admin` (edição total) e `User` (apenas consulta).

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11+
* **Interface:** [Streamlit](https://streamlit.io/)
* **Banco de Dados:** MySQL 8.0
* **Containerização:** Docker & Docker Compose
* **Processamento de Dados:** Pandas & SQLAlchemy

---

## 📦 Como Instalar e Rodar

1.  **Clonar o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/fortigate-matrix.git](https://github.com/seu-usuario/fortigate-matrix.git)
    cd fortigate-matrix
    ```

2.  **Configurar o ambiente:**
    Certifique-se de que o arquivo `matriz_completo.csv` está na pasta `app/data/`.

3.  **Subir os Containers:**
    ```bash
    docker compose up -d --build
    ```

4.  **Acessar o sistema:**
    Abra o navegador em `http://localhost:8081`.

---

## 👥 Colaboradores

Este projeto foi desenvolvido com foco em automação técnica e eficiência em pré-vendas por:

* **André Luiz Leitão de Azevedo** | [LinkedIn](https://www.linkedin.com/in/andreazevedo1980/)
* **Sofia Leitão de Azevedo** | [LinkedIn](https://www.linkedin.com/in/sofialeitaodeazevedo/)

---

## 📄 Licença

Este projeto é de uso técnico e consultivo. Verifique as permissões de uso de dados da Fortinet antes de distribuições comerciais.
