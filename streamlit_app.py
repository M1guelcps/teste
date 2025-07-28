import streamlit as st
import datetime
import pandas as pd
import requests
import yfinance as yf
import streamlit.components.v1 as components

# Título do app
st.title("Recomendador de Carteira de Investimentos")

# Check subscription
st.sidebar.title("Conta")
subscription = st.sidebar.selectbox("Selecione seu plano:", ["Gratuito", "Premium"])

if subscription == "Gratuito":
    st.sidebar.info("Você está no plano Gratuito com anúncios.")
else:
    st.sidebar.success("Você está no plano Premium sem anúncios e pode baixar relatórios.")

# Seção 1: Coleta de dados do usuário
st.header("1. Dados do Usuário")
with st.form(key='user_input_form'):
    objetivo = st.text_input("Objetivo financeiro (ex: comprar casa, aposentadoria):")
    perfil = st.selectbox(
        "Perfil de investidor:", ["Conservador", "Equilibrado", "Agressivo"]
    )
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data inicial:", value=datetime.date.today())
    with col2:
        data_final = st.date_input("Data final:", value=datetime.date.today() + datetime.timedelta(days=365))
    valor_inicial = st.number_input("Valor inicial (R$):", min_value=0.0, format="%.2f")
    aporte_mensal = st.number_input("Aporte mensal (R$):", min_value=0.0, format="%.2f")
    valor_objetivo = st.number_input("Valor objetivo (R$):", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Calcular Projeção")

# Função de projeção

def simular_projecao(valor_inicial, aporte_mensal, meses, taxa_mensal):
    saldo = valor_inicial
    historico = []
    for mes in range(1, meses + 1):
        saldo += aporte_mensal
        rendimento = saldo * taxa_mensal
        saldo += rendimento
        historico.append({
            "Mês": mes,
            "Saldo": saldo,
            "Total Investido": valor_inicial + aporte_mensal * mes,
            "Rendimento Acumulado": saldo - (valor_inicial + aporte_mensal * mes)
        })
    return pd.DataFrame(historico)

# Função de recomendação via API dinâmica

def obter_recomendacoes(perfil):
    carteiras = {
        "Conservador": ["IMAB11.SA", "TESOURO SELIC"],
        "Equilibrado": ["BOVA11.SA", "IMAB11.SA", "CDB"],
        "Agressivo": ["IVVB11.SA", "BOVA11.SA", "BDR"]
    }
    tickers = carteiras.get(perfil, [])
    recomendacoes = []
    for ativo in tickers:
        if ativo.endswith('.SA'):
            info = yf.Ticker(ativo)
            hist = info.history(period='1y')
            if not hist.empty:
                start = hist['Close'][0]
                end = hist['Close'][-1]
                retorno = (end - start) / start
                recomendacoes.append({
                    "Ativo": ativo,
                    "Retorno 1 ano": f"{retorno*100:.2f}%",
                    "Preço Atual": f"R$ {end:.2f}"
                })
        else:
            recomendacoes.append({"Ativo": ativo, "Retorno 1 ano": "N/A", "Preço Atual": "N/A"})
    return pd.DataFrame(recomendacoes)

# Execução após submissão

if submitted:
    # Preparar projeção
    meses = (data_final.year - data_inicial.year) * 12 + (data_final.month - data_inicial.month)
    taxas_anuais = {"Conservador": 0.05, "Equilibrado": 0.08, "Agressivo": 0.12}
    taxa_anual = taxas_anuais.get(perfil, 0.05)
    taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    df_proj = simular_projecao(valor_inicial, aporte_mensal, meses, taxa_mensal)

    # Seção 2: Projeção
    st.header("2. Projeção de Investimentos")
    st.write(f"Período: {meses} meses | Taxa anual: {taxa_anual*100:.2f}%")
    st.subheader("Comparativo Mensal")
    st.line_chart(df_proj.set_index("Mês")["Saldo"], use_container_width=True)
    st.line_chart(df_proj.set_index("Mês")["Total Investido"], use_container_width=True)
    st.area_chart(df_proj.set_index("Mês")["Rendimento Acumulado"], use_container_width=True)
    st.table(df_proj)

    # Meta de objetivo
    if valor_objetivo > 0:
        atingido = df_proj[df_proj['Saldo'] >= valor_objetivo]
        if not atingido.empty:
            mes_atingido = int(atingido.iloc[0]['Mês'])
            st.success(f"Você alcançará R$ {valor_objetivo:,.2f} em {mes_atingido} meses.")
        else:
            st.warning("Não será possível atingir o objetivo no período definido.")

    # Seção 3: Recomendações dinâmicas
    st.header("3. Recomendações de Ativos")
    df_rec = obter_recomendacoes(perfil)
    st.write(f"Perfil: {perfil}")
    st.table(df_rec)

    # Seção 4: Anúncios ou exportação
    st.header("4. Relatórios e Monetização")
    if subscription == "Gratuito":
        # Exibir placeholder de anúncio
        st.markdown("---")
        components.html("<div style='border:1px solid #ddd; padding:10px; text-align:center;'>ANÚNCIO DO ADSENSE AQUI</div>", height=200)
        st.info("Faça upgrade para o plano Premium para remover anúncios e baixar relatórios.")
    else:
        # Exportar relatórios
        csv = df_proj.to_csv(index=False).encode('utf-8')
        st.download_button(label="Baixar Projeção CSV", data=csv, file_name='projecao.csv', mime='text/csv')
        # Gerar Excel
        with pd.ExcelWriter('projecao.xlsx', engine='xlsxwriter') as writer:
            df_proj.to_excel(writer, index=False, sheet_name='Projecao')
            # ... poder adicionar recomendações num outro sheet
        excel_data = open('projecao.xlsx', 'rb').read()
        st.download_button(label="Baixar Projeção Excel", data=excel_data, file_name='projecao.xlsx', mime='application/vnd.ms-excel')
