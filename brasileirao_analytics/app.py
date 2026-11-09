import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.database import carregar_partidas, atualizar_placar_manual, limpar_partidas
from src.collector import sincronizar_fbref, gerar_dados_exemplo, MAPA_CLUBES
from src.engine import TabelaBrasileirao

st.set_page_config(page_title="Brasileirão Analytics", layout="wide", page_icon="⚽")

st.title("⚽ Brasileirão Série A — Painel Analítico, Modelagem & Simulação")

# --- BARRA LATERAL: FONTE DE DADOS E FILTROS ---
with st.sidebar:
    st.header("🔄 Fonte de Dados")
    substituir_tudo = st.checkbox(
        "Limpar base antes de sincronizar",
        value=True,
        help="Evita misturar dados simulados com jogos reais. Desmarque apenas se quiser preservar jogos editados manualmente."
    )
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Sincronizar Real", use_container_width=True):
            with st.spinner("Sincronizando partidas, scouts e calendário..."):
                ok, msg = sincronizar_fbref(limpar_antes=substituir_tudo)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    with col_btn2:
        if st.button("Dados Simulados", use_container_width=True):
            ok, msg = gerar_dados_exemplo()
            st.info(msg)
            st.rerun()

    if st.button("🗑️ Zerar Banco de Dados", use_container_width=True):
        limpar_partidas()
        st.warning("Banco de dados esvaziado!")
        st.rerun()

    st.divider()
    st.header("🎛️ Filtros de Recorte")
    filtro_condicao = st.selectbox("Mando de Campo", ["Geral", "Casa", "Fora"])
    filtro_turno = st.radio("Turno", ["Todos", "1º Turno", "2º Turno"], horizontal=True)
    filtro_faixa = st.selectbox(
        "Faixa do Adversário Enfrentado",
        ["Todos", "G-6", "Meio", "Z-4"],
        help="Filtra apenas partidas contra clubes que estão atualmente no G-6 (1º-6º), Meio (7º-16º) ou Z-4 (17º-20º)."
    )
    filtro_recorte = st.selectbox("Recorte Recente", ["Todos os jogos", "Últimos 5 jogos", "Últimos 10 jogos"])
    
    df_partidas = carregar_partidas()
    df_realizadas = df_partidas.dropna(subset=['gols_mandante', 'gols_visitante']) if not df_partidas.empty else pd.DataFrame()

    if not df_realizadas.empty:
        r_min_db = int(df_realizadas['rodada'].min())
        r_max_db = int(df_realizadas['rodada'].max())
        if r_min_db < r_max_db:
            intervalo_rodadas = st.slider(
                "Intervalo de Rodadas Concluídas",
                min_value=r_min_db,
                max_value=r_max_db,
                value=(r_min_db, r_max_db)
            )
        else:
            st.caption(f"Apenas a rodada {r_min_db} concluída no banco.")
            intervalo_rodadas = (r_min_db, r_max_db)
    else:
        intervalo_rodadas = (1, 38)

    # --- INSERÇÃO OU EDIÇÃO MANUAL DE PARTIDAS ---
    st.divider()
    with st.expander("✏️ Inserir / Editar Jogo Individual"):
        clubes_existentes = sorted(
            list(set(df_partidas['mandante'].unique()).union(set(df_partidas['visitante'].unique())))
        ) if not df_partidas.empty else []

        m_rodada = st.number_input("Rodada", min_value=1, max_value=38, value=1)
        
        if len(clubes_existentes) >= 2:
            m_mandante = st.selectbox("Clube Mandante", clubes_existentes, index=0)
            m_visitante = st.selectbox("Clube Visitante", clubes_existentes, index=1)
        else:
            m_mandante = st.text_input("Clube Mandante", placeholder="Ex: Cruzeiro")
            m_visitante = st.text_input("Clube Visitante", placeholder="Ex: Atlético-MG")
            
        c1, c2 = st.columns(2)
        m_gm = c1.number_input("Gols Casa", min_value=0, value=0)
        m_gv = c2.number_input("Gols Fora", min_value=0, value=0)
        m_xgm = c1.number_input("xG Casa", min_value=0.0, step=0.1, value=0.0)
        m_xgv = c2.number_input("xG Fora", min_value=0.0, step=0.1, value=0.0)
        m_cam = c1.number_input("CA Casa", min_value=0, value=0)
        m_cav = c2.number_input("CA Fora", min_value=0, value=0)
        m_cvm = c1.number_input("CV Casa", min_value=0, value=0)
        m_cvv = c2.number_input("CV Fora", min_value=0, value=0)
        
        if st.button("Salvar Resultado", use_container_width=True):
            if m_mandante and m_visitante and m_mandante != m_visitante:
                nome_casa = MAPA_CLUBES.get(m_mandante.strip(), m_mandante.strip())
                nome_fora = MAPA_CLUBES.get(m_visitante.strip(), m_visitante.strip())
                atualizar_placar_manual(
                    m_rodada, nome_casa, nome_fora,
                    m_gm, m_gv, m_xgm, m_xgv, m_cam, m_cav, m_cvm, m_cvv
                )
                st.success("Jogo salvo! Atualizando painel...")
                st.rerun()
            else:
                st.error("Escolha dois clubes válidos e diferentes.")

# --- VERIFICAÇÃO INICIAL ---
if df_realizadas.empty:
    st.warning(
        "Nenhuma partida finalizada encontrada no banco local. Clique em **'Sincronizar Real'** "
        "ou **'Dados Simulados'** na barra lateral para começar."
    )
    st.stop()

motor = TabelaBrasileirao(df_partidas)
ultimos_n = 5 if filtro_recorte == "Últimos 5 jogos" else (10 if filtro_recorte == "Últimos 10 jogos" else None)

df_tabela = motor.gerar_tabela(
    condicao=filtro_condicao,
    turno=filtro_turno,
    ultimos_n=ultimos_n,
    intervalo_rodadas=intervalo_rodadas,
    faixa_adversario=filtro_faixa
)

if df_tabela.empty:
    st.info("Nenhuma partida encontrada para a combinação de filtros selecionada.")
    st.stop()

# --- CARDS DE DESTAQUE ESTATÍSTICO DO RECORTE ---
c1, c2, c3, c4, c5 = st.columns(5)
lider = df_tabela.iloc[0]
maior_elo = df_tabela.sort_values(by=['Elo', 'P'], ascending=False).iloc[0]
mais_eficiente = df_tabela.sort_values(by=['Dif_xPts'], ascending=False).iloc[0]
mais_desperdica = df_tabela.sort_values(by=['Dif_xPts'], ascending=True).iloc[0]
mais_regular = df_tabela.sort_values(by=['DP_Pts', 'P'], ascending=[True, False]).iloc[0]

c1.metric("🏆 Líder no Recorte", f"{lider['Clube']}", f"{lider['P']} pts ({lider['Ap(%)']}%)")
c2.metric("⚡ Maior Rating Elo", f"{maior_elo['Clube']}", f"{maior_elo['Elo']} pts Elo")
c3.metric("🎯 Mais Letal (P > xPts)", f"{mais_eficiente['Clube']}", f"{mais_eficiente['Dif_xPts']:+.1f} pts vs esp.")
c4.metric("📉 Mais Desperdiça (P < xPts)", f"{mais_desperdica['Clube']}", f"{mais_desperdica['Dif_xPts']:+.1f} pts vs esp.")
c5.metric("📏 Mais Regular (Menor σ)", f"{mais_regular['Clube']}", f"DP: {mais_regular['DP_Pts']} pts/J")

# --- NAVEGAÇÃO POR ABAS (7 ABAS COMPLETAS) ---
aba_tabela, aba_montecarlo, aba_simulador, aba_matematica, aba_quadrantes, aba_evolucao, aba_matriz = st.tabs([
    "📊 Classificação Geral",
    "🎲 Projeções (Monte Carlo)",
    "🕹️ Simulador de Rodadas",
    "🧠 Eficiência (xPts), Elo & SoS",
    "🎯 Quadrantes (Ataque vs. Defesa)",
    "📈 Evolução por Rodada",
    "⚔️ Matriz 20x20"
])

# =====================================================================
# ABA 1: TABELA DE CLASSIFICAÇÃO COM ESCUDOS, xPts, ELO E SoS
# =====================================================================
with aba_tabela:
    st.subheader(
        f"Classificação — {filtro_condicao} | {filtro_turno} | Adv: {filtro_faixa} | {filtro_recorte} "
        f"(Rodadas {intervalo_rodadas[0]} a {intervalo_rodadas[1]})"
    )

    def colorir_zonas(row):
        pos = row.name
        cor = ''
        if filtro_condicao == 'Geral' and filtro_faixa == 'Todos' and ultimos_n is None and len(df_tabela) == 20:
            if pos <= 4:
                cor = 'background-color: rgba(30, 136, 229, 0.18)'
            elif pos <= 6:
                cor = 'background-color: rgba(0, 172, 193, 0.18)'
            elif pos <= 12:
                cor = 'background-color: rgba(67, 160, 71, 0.18)'
            elif pos >= 17:
                cor = 'background-color: rgba(229, 57, 53, 0.22)'
        return [cor] * len(row)

    tabela_estilizada = (
        df_tabela.style
        .apply(colorir_zonas, axis=1)
        .background_gradient(subset=['Ap(%)', 'Elo'], cmap='Greens')
        .background_gradient(subset=['Dif_xPts'], cmap='RdYlGn')
        .background_gradient(subset=['DP_Pts', 'SoS_Enf'], cmap='YlOrRd')
        .format({
            'Ap(%)': '{:.1f}%',
            'PPG': '{:.2f}',
            'xPts': '{:.1f}',
            'Dif_xPts': '{:+.1f}',
            'SoS_Enf': '{:.1f}%',
            'SoS_Prox': lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
            'DP_Pts': '{:.2f}',
            'DP_SG': '{:.2f}',
            'xGP': '{:.1f}',
            'xGC': '{:.1f}'
        })
    )

    st.dataframe(
        tabela_estilizada,
        column_config={
            "Escudo": st.column_config.ImageColumn("", width="small"),
            "Clube": st.column_config.TextColumn("Clube", width="medium"),
            "xPts": st.column_config.NumberColumn("xPts", help="Pontos Esperados via Distribuição de Poisson"),
            "Dif_xPts": st.column_config.NumberColumn("P - xPts", help="Saldo de Eficiência (Pontos Reais menos Pontos Esperados)"),
            "Elo": st.column_config.NumberColumn("Elo", help="Rating Elo Dinâmico (Base 1500)"),
            "SoS_Enf": st.column_config.NumberColumn("SoS Enf.", help="Aproveitamento médio dos adversários enfrentados"),
            "SoS_Prox": st.column_config.NumberColumn("SoS Próx. 5", help="Aproveitamento médio dos próximos 5 adversários"),
        },
        use_container_width=True,
        height=740
    )

    st.caption(
        "🟦 **1º–4º:** Libertadores | 🟦 **5º–6º:** Pré-Libertadores | 🟩 **7º–12º:** Sul-Americana | 🟥 **17º–20º:** Z-4"
    )

# =====================================================================
# ABA 2: SIMULAÇÃO DE MONTE CARLO (PROBABILIDADES DE TÍTULO, VAGAS E Z-4)
# =====================================================================
with aba_montecarlo:
    col_mc1, col_mc2 = st.columns([3, 1])
    with col_mc1:
        st.subheader(f"🎲 Projeção de Monte Carlo (Baseada até a Rodada {intervalo_rodadas[1]})")
        st.caption(
            "Simula milhares de vezes todas as partidas restantes combinando Força de Ataque ($\alpha_i$), "
            "Defesa ($\beta_i$), Gols Esperados ($xG$), Rating Elo e vantagem de mando de campo."
        )
    with col_mc2:
        qtd_sim = st.select_slider(
            "Número de Simulações do Campeonato:",
            options=[1000, 2500, 5000, 10000],
            value=5000
        )

    with st.spinner(f"Simulando o restante da Série A {qtd_sim:,} vezes..."):
        df_proj, df_corte_z4 = motor.executar_monte_carlo(
            n_simulacoes=qtd_sim,
            r_max_ref=intervalo_rodadas[1]
        )

    if not df_proj.empty:
        # Cards com os favoritos apontados pela simulação
        fav_titulo = df_proj.sort_values('Título (%)', ascending=False).iloc[0]
        maior_risco_z4 = df_proj.sort_values('Z-4 Risco (%)', ascending=False).iloc[0]
        corte_45 = df_corte_z4[df_corte_z4['Pontos_Num'] == 45]['Risco de Queda (%)'].values[0] if not df_corte_z4.empty else 0.0

        k1, k2, k3 = st.columns(3)
        k1.metric("👑 Maior Favorito ao Título", f"{fav_titulo['Clube']}", f"{fav_titulo['Título (%)']:.1f}% de chance (Proj: {fav_titulo['Pts_Proj']} pts)")
        k2.metric("🚨 Maior Alerta de Z-4", f"{maior_risco_z4['Clube']}", f"{maior_risco_z4['Z-4 Risco (%)']:.1f}% de risco (Proj: {maior_risco_z4['Pts_Proj']} pts)")
        k3.metric("🛡️ Risco de Queda com 45 Pontos", f"{corte_45:.1f}% de risco", f"{100.0 - corte_45:.1f}% de chance de permanência")

        est_proj = (
            df_proj.style
            .background_gradient(subset=['Pts_Proj', 'Título (%)', 'G-4 (%)', 'G-6 (%)'], cmap='Greens')
            .background_gradient(subset=['Sul-Americana (%)'], cmap='Blues')
            .background_gradient(subset=['Z-4 Risco (%)'], cmap='Reds')
            .format({
                'Pts_Proj': '{:.1f}',
                'Título (%)': '{:.1f}%',
                'G-4 (%)': '{:.1f}%',
                'G-6 (%)': '{:.1f}%',
                'Sul-Americana (%)': '{:.1f}%',
                'Z-4 Risco (%)': '{:.1f}%'
            })
        )

        st.dataframe(
            est_proj,
            column_config={
                "Escudo": st.column_config.ImageColumn("", width="small"),
                "P_Atual": st.column_config.NumberColumn("Pts Atuais"),
                "Pts_Proj": st.column_config.NumberColumn("Pts Projetados", help="Média de pontos ao fim da 38ª rodada"),
                "IC_90%": st.column_config.TextColumn("Faixa Provável (90%)", help="Intervalo entre os percentis 5% (pessimista) e 95% (otimista)"),
            },
            use_container_width=True,
            height=730
        )

        if not df_corte_z4.empty:
            st.divider()
            st.markdown("#### 🛡️ Curva da 'Pontuação Mágica' contra o Rebaixamento (39 a 48 pontos)")
            fig_z4 = px.bar(
                df_corte_z4,
                x='Pontuação Final',
                y=['Chance de Permanência (%)', 'Risco de Queda (%)'],
                barmode='group',
                text_auto='.1f',
                color_discrete_map={
                    'Chance de Permanência (%)': '#43A047',
                    'Risco de Queda (%)': '#E53935'
                },
                height=380
            )
            fig_z4.update_layout(yaxis_title="Probabilidade (%)", legend_title_text="Cenário")
            st.plotly_chart(fig_z4, use_container_width=True)

# =====================================================================
# ABA 3: SIMULADOR INTERATIVO DE RODADAS (PALPITES EM TEMPO REAL)
# =====================================================================
with aba_simulador:
    st.subheader("🕹️ Simulador Interativo de Rodadas")
    st.caption(
        "Escolha uma rodada abaixo, digite os placares na tabela da esquerda e veja **em tempo real** na direita "
        "como ficaria a classificação e quantas posições cada clube subiria (`🔼`) ou cairia (`🔽`)."
    )

    proxima_rodada_sugerida = min(38, int(df_realizadas['rodada'].max()) + 1)
    rodada_sim = st.number_input(
        "Selecione a Rodada para Simular:",
        min_value=1, max_value=38, value=proxima_rodada_sugerida
    )

    df_jogos_sim = motor.obter_partidas_para_simulador(rodada_sim)

    if not df_jogos_sim.empty:
        col_ed, col_res = st.columns([1.05, 1.45])

        with col_ed:
            st.markdown(f"#### ⚽ Palpites da {rodada_sim}ª Rodada")
            df_editado = st.data_editor(
                df_jogos_sim,
                column_config={
                    "Rodada": None,
                    "Escudo_Casa": st.column_config.ImageColumn("", width="small"),
                    "Mandante": st.column_config.TextColumn("Mandante", disabled=True),
                    "Gols_Casa": st.column_config.NumberColumn("Gols Casa", min_value=0, max_value=15, step=1),
                    "Gols_Fora": st.column_config.NumberColumn("Gols Fora", min_value=0, max_value=15, step=1),
                    "Visitante": st.column_config.TextColumn("Visitante", disabled=True),
                    "Escudo_Fora": st.column_config.ImageColumn("", width="small"),
                    "Simular_Jogo": st.column_config.CheckboxColumn("Aplicar?", default=True)
                },
                hide_index=True,
                use_container_width=True,
                key=f"editor_rodada_{rodada_sim}"
            )

            if st.button("💾 Gravar estes Placares Oficialmente no Banco", use_container_width=True):
                ativos = df_editado[df_editado['Simular_Jogo'] == True]
                for _, r_row in ativos.iterrows():
                    gm, gv = int(r_row['Gols_Casa']), int(r_row['Gols_Fora'])
                    atualizar_placar_manual(
                        int(r_row['Rodada']),
                        str(r_row['Mandante']),
                        str(r_row['Visitante']),
                        gm, gv,
                        round(gm * 0.75 + 0.40, 2),
                        round(gv * 0.75 + 0.30, 2)
                    )
                st.success(f"Placares da {rodada_sim}ª rodada gravados no banco SQLite!")
                st.rerun()

        with col_res:
            st.markdown("#### 📊 Classificação Simulada com os Palpites")
            df_tab_simulada = motor.simular_tabela_com_palpites(df_editado)
            cols_vis_sim = ['Escudo', 'Clube', ' Δ Pos', 'P', ' Δ Pts', 'J', 'V', 'E', 'D', 'SG', 'GP', 'Ap(%)']

            st.dataframe(
                df_tab_simulada[cols_vis_sim],
                column_config={
                    "Escudo": st.column_config.ImageColumn("", width="small"),
                    " Δ Pos": st.column_config.TextColumn("Var. Pos", help="Posições ganhas ou perdidas após os palpites"),
                    " Δ Pts": st.column_config.TextColumn("+Pts"),
                },
                use_container_width=True,
                height=720
            )
    else:
        st.info("Não há confrontos listados para esta rodada.")

# =====================================================================
# ABA 4: MODELAGEM MATEMÁTICA (xPts, FAIXAS DE ADVERSÁRIO E SoS)
# =====================================================================
with aba_matematica:
    st.subheader("🧠 Painel de Eficiência (Poisson xPts), Força de Calendário (SoS) e Desempenho por Faixa")
    
    df_resumo = motor.gerar_resumo_faixas_e_calendario(intervalo_rodadas=intervalo_rodadas)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("#### 🎯 Sobredesempenho vs. Subdesempenho ($P - xPts$)")
        df_xpts_ord = df_resumo.sort_values('Dif_xPts', ascending=True)
        fig_xpts = px.bar(
            df_xpts_ord,
            x='Dif_xPts',
            y='Clube',
            orientation='h',
            text='Dif_xPts',
            color='Dif_xPts',
            color_continuous_scale='RdYlGn',
            hover_data={'P': True, 'xPts': True, 'Elo': True},
            labels={'Dif_xPts': 'Diferença (Pontos Reais - xPts)', 'Clube': ''},
            height=540
        )
        fig_xpts.update_traces(texttemplate='%{text:+.1f}', textposition='outside')
        fig_xpts.add_vline(x=0, line_width=2, line_color="white")
        st.plotly_chart(fig_xpts, use_container_width=True)

    with col_g2:
        st.markdown("#### ⚔️ Aproveitamento por Faixa de Adversário (vs. G-6, Meio e Z-4)")
        df_melted = df_resumo.melt(
            id_vars=['Clube'],
            value_vars=['Ap_vs_G6(%)', 'Ap_vs_Meio(%)', 'Ap_vs_Z4(%)'],
            var_name='Faixa',
            value_name='Aproveitamento (%)'
        )
        df_melted['Faixa'] = df_melted['Faixa'].replace({
            'Ap_vs_G6(%)': 'Contra G-6 (1º-6º)',
            'Ap_vs_Meio(%)': 'Contra Meio (7º-16º)',
            'Ap_vs_Z4(%)': 'Contra Z-4 (17º-20º)'
        })
        fig_faixas = px.bar(
            df_melted,
            x='Clube',
            y='Aproveitamento (%)',
            color='Faixa',
            barmode='group',
            color_discrete_map={
                'Contra G-6 (1º-6º)': '#1E88E5',
                'Contra Meio (7º-16º)': '#43A047',
                'Contra Z-4 (17º-20º)': '#E53935'
            },
            height=540
        )
        fig_faixas.update_layout(xaxis_tickangle=-45, legend_title_text="Adversário")
        st.plotly_chart(fig_faixas, use_container_width=True)

    st.divider()
    st.markdown("#### 📅 Tabela Consolidada: Rating Elo, Desempenho por Bloco e Dificuldade dos Próximos 5 Jogos")

    est_resumo = (
        df_resumo.style
        .background_gradient(subset=['Elo', 'Ap_vs_G6(%)', 'Ap_vs_Meio(%)', 'Ap_vs_Z4(%)'], cmap='Greens')
        .background_gradient(subset=['Dif_xPts'], cmap='RdYlGn')
        .background_gradient(subset=['SoS_Enf', 'SoS_Prox'], cmap='YlOrRd')
        .format({
            'xPts': '{:.1f}',
            'Dif_xPts': '{:+.1f}',
            'Ap(%)': '{:.1f}%',
            'SoS_Enf': '{:.1f}%',
            'SoS_Prox': lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
            'Ap_vs_G6(%)': '{:.1f}%',
            'Ap_vs_Meio(%)': '{:.1f}%',
            'Ap_vs_Z4(%)': '{:.1f}%'
        })
    )

    st.dataframe(
        est_resumo,
        column_config={
            "Escudo": st.column_config.ImageColumn("", width="small"),
            "SoS_Enf": st.column_config.NumberColumn("SoS Passado", help="Dificuldade média dos adversários já enfrentados"),
            "SoS_Prox": st.column_config.NumberColumn("SoS Futuro (5J)", help="Dificuldade média dos próximos 5 adversários"),
        },
        use_container_width=True,
        height=680
    )

# =====================================================================
# ABA 5: GRÁFICO DE QUADRANTES (ATAQUE VS DEFESA)
# =====================================================================
with aba_quadrantes:
    st.subheader("🎯 Eficiência Ofensiva vs. Solidez Defensiva")
    
    tipo_metrica = st.radio(
        "Selecione a base dos quadrantes:",
        ["Gols Esperados por Jogo (xGP/J vs. xGC/J)", "Gols Reais por Jogo (GP/J vs. GC/J)"],
        horizontal=True
    )

    df_quad = df_tabela.copy()
    if "Esperados" in tipo_metrica:
        df_quad['Eixo_X'] = (df_quad['xGP'] / df_quad['J']).round(2)
        df_quad['Eixo_Y'] = (df_quad['xGC'] / df_quad['J']).round(2)
        label_x = "xG Pró por Jogo (Criação Ofensiva → Maior é melhor)"
        label_y = "xG Contra por Jogo (Exposição Defensiva → Topo/Menor é melhor)"
    else:
        df_quad['Eixo_X'] = (df_quad['GP'] / df_quad['J']).round(2)
        df_quad['Eixo_Y'] = (df_quad['GC'] / df_quad['J']).round(2)
        label_x = "Gols Pró por Jogo (Ataque → Maior é melhor)"
        label_y = "Gols Sofridos por Jogo (Defesa → Topo/Menor é melhor)"

    media_x = df_quad['Eixo_X'].mean()
    media_y = df_quad['Eixo_Y'].mean()

    fig_quad = px.scatter(
        df_quad,
        x='Eixo_X',
        y='Eixo_Y',
        text='Clube',
        size='Elo',
        color='Ap(%)',
        color_continuous_scale='RdYlGn',
        hover_data={'Clube': True, 'P': True, 'xPts': True, 'Elo': True, 'Eixo_X': True, 'Eixo_Y': True},
        labels={'Eixo_X': label_x, 'Eixo_Y': label_y, 'Ap(%)': 'Aprov. (%)'},
        height=640
    )

    fig_quad.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_quad.update_yaxes(autorange="reversed")

    fig_quad.add_vline(x=media_x, line_dash="dash", line_color="gray", annotation_text=f"Média Ataque ({media_x:.2f})")
    fig_quad.add_hline(y=media_y, line_dash="dash", line_color="gray", annotation_text=f"Média Defesa ({media_y:.2f})")

    x_max, x_min = df_quad['Eixo_X'].max(), df_quad['Eixo_X'].min()
    y_max, y_min = df_quad['Eixo_Y'].max(), df_quad['Eixo_Y'].min()

    fig_quad.add_annotation(x=x_max, y=y_min, text="🟢 DOMINANTES (Ataque Forte + Defesa Sólida)", showarrow=False, font=dict(color="green", size=12))
    fig_quad.add_annotation(x=x_min, y=y_min, text="🛡️ RETRANCA EFICIENTE (Defesa Sólida + Pouco Ataque)", showarrow=False, font=dict(color="teal", size=12))
    fig_quad.add_annotation(x=x_max, y=y_max, text="⚡ JOGOS ABERTOS (Ataque Forte + Defesa Vazada)", showarrow=False, font=dict(color="orange", size=12))
    fig_quad.add_annotation(x=x_min, y=y_max, text="🔴 ALERTA DE CRISE (Baixa Criação + Defesa Exposta)", showarrow=False, font=dict(color="red", size=12))

    st.plotly_chart(fig_quad, use_container_width=True)

# =====================================================================
# ABA 6: EVOLUÇÃO POSICIONAL OU ELO RODADA A RODADA
# =====================================================================
with aba_evolucao:
    st.subheader("📈 Trajetória Rodada a Rodada")
    
    df_evolucao = motor.gerar_evolucao_posicoes(
        condicao=filtro_condicao,
        intervalo_rodadas=intervalo_rodadas
    )

    if not df_evolucao.empty:
        col_ev1, col_ev2 = st.columns([1, 2])
        with col_ev1:
            metrica_ev = st.radio("Métrica do Eixo Vertical:", ["Posição na Tabela (1º ao 20º)", "Evolução do Rating Elo"], horizontal=False)
        with col_ev2:
            todos_clubes_ordem = df_tabela['Clube'].tolist()
            selecao_padrao = todos_clubes_ordem[:4] + todos_clubes_ordem[-2:] if len(todos_clubes_ordem) >= 6 else todos_clubes_ordem
            clubes_selecionados = st.multiselect(
                "Selecione os clubes para comparar:",
                options=todos_clubes_ordem,
                default=selecao_padrao
            )

        df_ev_filtrado = df_evolucao[df_evolucao['Clube'].isin(clubes_selecionados)]

        if "Posição" in metrica_ev:
            fig_bump = px.line(
                df_ev_filtrado,
                x='Rodada',
                y='Posição',
                color='Clube',
                markers=True,
                hover_data={'Posição': True, 'Pontos': True, 'Elo': True},
                height=600
            )
            fig_bump.update_yaxes(autorange="reversed", dtick=1, range=[20.5, 0.5], title="Posição na Tabela")
            fig_bump.add_hrect(y0=0.5, y1=4.5, fillcolor="royalblue", opacity=0.08, line_width=0, annotation_text="G-4")
            fig_bump.add_hrect(y0=16.5, y1=20.5, fillcolor="crimson", opacity=0.08, line_width=0, annotation_text="Z-4")
        else:
            fig_bump = px.line(
                df_ev_filtrado,
                x='Rodada',
                y='Elo',
                color='Clube',
                markers=True,
                hover_data={'Elo': True, 'Posição': True, 'Pontos': True},
                height=600
            )
            fig_bump.add_hline(y=1500, line_dash="dash", line_color="gray", annotation_text="Média Base (1500)")

        fig_bump.update_xaxes(dtick=1, title="Rodada do Campeonato")
        fig_bump.update_traces(line=dict(width=3), marker=dict(size=8))
        st.plotly_chart(fig_bump, use_container_width=True)
    else:
        st.info("Dados insuficientes para gerar a evolução de rodadas.")

# =====================================================================
# ABA 7: MATRIZ DE CONFRONTOS DIRETOS (GRID 20x20)
# =====================================================================
with aba_matriz:
    st.subheader("⚔️ Matriz de Confrontos Diretos (Mandante nas Linhas × Visitante nas Colunas)")
    st.caption("🟩 **Verde:** Vitória do Mandante | 🟨 **Amarelo:** Empate | 🟥 **Vermelho:** Vitória do Visitante")

    df_matriz = motor.gerar_matriz_confrontos(intervalo_rodadas=intervalo_rodadas)

    def estilizar_celula_confronto(val):
        if not isinstance(val, str) or "–" not in val:
            return 'color: #888888;'
        try:
            gm, gv = map(int, val.split("–"))
            if gm > gv:
                return 'background-color: rgba(67, 160, 71, 0.30); font-weight: bold;'
            elif gm < gv:
                return 'background-color: rgba(229, 57, 53, 0.30); font-weight: bold;'
            else:
                return 'background-color: rgba(251, 192, 45, 0.25); font-weight: bold;'
        except Exception:
            return ''

    st.dataframe(
        df_matriz.style.map(estilizar_celula_confronto),
        use_container_width=True,
        height=740
    )

# =====================================================================
# RODAPÉ: CONFERÊNCIA DO BANCO E GLOSSÁRIO COMPLETO EM TÓPICOS
# =====================================================================
st.divider()
with st.expander(f"📋 Conferir Partidas Registradas no Banco ({len(df_realizadas)} realizadas / {len(df_partidas)} totais no calendário)"):
    st.dataframe(df_partidas, use_container_width=True, height=300)

with st.expander("📖 Glossário Completo de Siglas, Métricas e Critérios Regulamentares", expanded=False):
    col_gl1, col_gl2 = st.columns(2)

    with col_gl1:
        st.markdown("""
        ### 1. Indicadores Tradicionais de Classificação
        * **`Pos` (Posição):** Colocação atual do clube na tabela de classificação conforme os critérios da CBF.
        * **`P` (Pontos Ganhos):** Total de pontos somados pelo clube ($3$ por vitória, $1$ por empate e $0$ por derrota).
        * **`J` (Jogos):** Quantidade total de partidas disputadas pelo clube dentro do recorte selecionado.
        * **`V` (Vitórias):** Total de partidas vencidas pelo clube.
        * **`E` (Empates):** Total de partidas terminadas com placar igualado.
        * **`D` (Derrotas):** Total de partidas perdidas pelo clube.
        * **`GP` (Gols Pró / Gols Feitos):** Total de gols marcados pela equipe.
        * **`GC` (Gols Contra / Gols Sofridos):** Total de gols sofridos pela defesa da equipe.
        * **`SG` (Saldo de Gols):** Diferença aritmética entre os gols marcados e os gols sofridos ($\text{SG} = \text{GP} - \text{GC}$).
        * **`Ap(%)` (Aproveitamento Percentual):** Porcentagem de pontos conquistados em relação ao total de pontos disputados ($\frac{\text{P}}{\text{J} \times 3} \times 100$).
        * **`PPG` (*Points Per Game* / Pontos por Jogo):** Média simples de pontos conquistados a cada partida ($\frac{\text{P}}{\text{J}}$).
        * **`Forma` (Sequência Recente):** Histórico visual dos últimos 5 jogos disputados no recorte (🟢 = Vitória, ⚪ = Empate, 🔴 = Derrota).

        ---

        ### 2. Métricas de Gols Esperados e Eficiência Tática
        * **`xG` (*Expected Goals* / Gols Esperados):** Métrica que avalia a probabilidade de uma finalização resultar em gol (de $0.00$ a $1.00$) com base no perigo real da chance criada.
        * **`xGP` (*Expected Goals For* / Gols Esperados Pró):** Soma do volume ofensivo de $xG$ criado pelo clube a seu favor.
        * **`xGC` (*Expected Goals Against* / Gols Esperados Contra):** Soma do volume de $xG$ cedido pela defesa do clube aos adversários.
        * **`xPts` (*Expected Points* / Pontos Esperados via Poisson):** Pontuação justa estimada para o clube aplicando a Distribuição de Poisson sobre o `xGP` e `xGC` de cada partida ($\text{xPts} = 3 \cdot P_v + 1 \cdot P_e$).
        * **`P - xPts` ou `Dif_xPts` (Saldo de Eficiência):** Diferença entre os pontos reais na tabela e os pontos esperados:
          * **Valor Positivo ($> 0$):** Clube pontua acima do esperado (alta letalidade nas finalizações ou grande desempenho do goleiro).
          * **Valor Negativo ($< 0$):** Clube cria volume suficiente para vencer, mas desperdiça pontos nas duas áreas.
        * **`CS` (*Clean Sheets* / Jogos sem Sofrer Gols):** Quantidade de partidas em que o clube terminou com a defesa intacta ($\text{GC} = 0$).
        * **`SM` (Jogos Sem Marcar):** Quantidade de partidas em que o ataque do clube passou em branco ($\text{GP} = 0$).
        """)

    with col_gl2:
        st.markdown("""
        ### 3. Oscilação, Rating de Força e Calendário
        * **`DP_Pts` ($\sigma_{\text{pts}}$ — Desvio Padrão de Pontos):** Mede a dispersão dos resultados jogo a jogo ($0$, $1$ ou $3$ pts). Valores próximos de `0.00` indicam estabilidade; valores próximos de `1.50` indicam comportamento "8 ou 80" (alternância constante entre vitórias e derrotas).
        * **`DP_SG` ($\sigma_{\text{sg}}$ — Desvio Padrão do Saldo de Gols):** Mede a elasticidade dos placares. Valor baixo indica jogos decididos por margem mínima (1 gol); valor alto indica equipe envolvida frequentemente em goleadas.
        * **`Elo` (Rating Elo Dinâmico):** Índice contínuo de força (iniciado em `1500` pontos) que aumenta ou diminui a cada rodada ponderando o nível do adversário, a vantagem do mando de campo ($+65$ pts) e a margem de gols da partida.
        * **`SoS Enf.` (*Strength of Schedule* Enfrentado):** Média do aproveitamento geral de todos os adversários que o clube **já enfrentou** até o momento.
        * **`SoS Próx. 5` (*Strength of Schedule* Futuro):** Média do aproveitamento atual dos **próximos 5 adversários** no calendário (quanto maior a porcentagem, mais difícil é a sequência futura).
        * **`Ap_vs_G6(%)`, `Ap_vs_Meio(%)` e `Ap_vs_Z4(%)`:** Taxa de aproveitamento do clube recortada exclusivamente contra equipes do topo (1º–6º), bloco intermediário (7º–16º) e zona de rebaixamento (17º–20º).

        ---

        ### 4. Disciplina, Regulamento (CBF) e Simulação
        * **`CV` (Cartões Vermelhos):** Total de expulsões sofridas pela equipe (6º critério de desempate da CBF).
        * **`CA` (Cartões Amarelos):** Total de advertências recebidas pela equipe (7º critério de desempate da CBF).
        * **`H2H` (*Head-to-Head* / Confronto Direto):** 5º critério oficial de desempate da CBF, acionado automaticamente pelo motor quando **exatamente 2 clubes** empatam em `P`, `V`, `SG` e `GP`.
        * **`G-4` e `G-6` (Zona da Libertadores):** Grupos de clubes classificados diretamente à Fase de Grupos da Copa Libertadores (1º ao 4º) e à Pré-Libertadores (5º e 6º).
        * **`Sula` (Zona da Sul-Americana):** Faixa de classificação para a Copa Sul-Americana (7º ao 12º colocado).
        * **`Z-4` (Zona de Rebaixamento):** Os 4 últimos colocados (17º ao 20º) que são rebaixados à Série B.
        * **`Pts_Proj` (Pontos Projetados — Monte Carlo):** Média de pontos com que o clube termina a 38ª rodada após milhares de simulações matemáticas do campeonato.
        * **`IC 90%` (Intervalo de Confiança de 90%):** Faixa de pontuação final entre o cenário pessimista (percentil 5%) e o cenário otimista (percentil 95%) nas simulações.
        * **`Δ Pos` e `Δ Pts` (Variação no Simulador):** Quantidade de posições e pontos ganhos (`🔼`) ou perdidos (`🔽`) na tabela após aplicar os palpites no Simulador de Rodadas.
        """)