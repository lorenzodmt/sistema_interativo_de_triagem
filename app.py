import pandas as pd
import numpy as np
import datetime
import time
# Configuração da Página
st.set_page_config(page_title="Triagem Inteligente (Manchester)", layout="wide")
st.title("�� Sistema Interativo de Triagem de Manchester")
st.markdown("Implementação baseada em Operações Matriciais e Filas de Prioridade
Dinâmica")
# --- 1. CONFIGURAÇÃO DO PROTOCOLO E MATRIZES ---
# Tabela Oficial de Tempos Máximos e Pesos
TEMPOS_MAXIMOS = {
'Emergência (Vermelho)': 0, # Imediato
'Muito Urgente (Laranja)': 10, # 10 minutos
'Urgente (Amarelo)': 60, # 60 minutos
'Pouco Urgente (Verde)': 120, # 120 minutos
'Não Urgente (Azul)': 240 # 240 minutos
}
# Nossa Matriz de Pesos Clínicos (T(x) = A * x)
PESOS_CLINICOS = np.array([
1.0, # Peso Idade
2.5, # Peso Desvio Temperatura
2.0, # Peso Desvio Freq. Cardíaca
5.0 # Peso Desvio Saturação O2
])
# --- 2. GERENCIAMENTO DE ESTADO (MEMÓRIA DO APP) ---
# Usamos st.session_state para guardar a lista de pacientes sem perder ao atualizar a
página
if 'fila_pacientes' not in st.session_state:
st.session_state.fila_pacientes = []
# --- 3. MOTOR ALGÉBRICO (A Lógica da Disciplina) ---
def calcular_score_fisiologico(idade, temp, fc, o2):
# Etapa 1: Transformação de Mudança de Base (Normalização dos desvios)
desvios = np.array([
idade / 100.0,
abs(temp - 36.5),
abs(fc - 80.0) / 10.0,
abs(o2 - 100.0)
])
# Etapa 2: Composição (Produto Matricial)
score_base = desvios @ PESOS_CLINICOS
return score_base
def classificar_cor(score_base):
if score_base >= 25: return 'Emergência (Vermelho)'
elif score_base >= 15: return 'Muito Urgente (Laranja)'
elif score_base >= 8: return 'Urgente (Amarelo)'
elif score_base >= 3: return 'Pouco Urgente (Verde)'
else: return 'Não Urgente (Azul)'
def atualizar_fila_dinamica():
# Se não há pacientes, não faz nada
if not st.session_state.fila_pacientes:
return pd.DataFrame()
agora = datetime.datetime.now()
dados_atualizados = []
for paciente in st.session_state.fila_pacientes:
# Calcula tempo de espera em minutos
tempo_espera = (agora - paciente['hora_chegada']).total_seconds() / 60
tempo_maximo = TEMPOS_MAXIMOS[paciente['cor']]
# Etapa 3 do Pipeline: Penalização Temporal (Aceleração do Score)
# Se o paciente é Vermelho, a prioridade já é infinita (tempo_maximo = 0)
if tempo_maximo == 0:
score_dinamico = float('inf')
else:
# Reta de prioridade: quanto mais o tempo de espera se aproxima do limite,
maior o score soma
fator_tempo = (tempo_espera / tempo_maximo) * 100
score_dinamico = paciente['score_base'] + fator_tempo
# Se estourou o tempo, a prioridade explode (Passa na frente por regra de
negócio)
if tempo_espera >= tempo_maximo:
score_dinamico += 1000
# Monta o dicionário atualizado
dados_atualizados.append({
'Nome': paciente['nome'],
'Classificação': paciente['cor'],
'Score Fisiológico': round(paciente['score_base'], 2),
'Tempo na Fila (min)': round(tempo_espera, 1),
'Tempo Alvo (min)': tempo_maximo,
'Score Dinâmico (Ordem)': score_dinamico
})
# Cria o DataFrame Pandas e ORDENA usando o Score Dinâmico
df_fila = pd.DataFrame(dados_atualizados)
# A mágica do ordenamento: Maior Score Dinâmico (risco + tempo) vai para o topo
(index 0)
df_fila = df_fila.sort_values(by='Score Dinâmico (Ordem)',
ascending=False).reset_index(drop=True)
return df_fila
# --- 4. INTERFACE GRÁFICA ---
col_form, col_fila = st.columns([1, 2])
with col_form:
st.subheader("�� Triagem (Admissão)")
with st.form("form_triagem"):
nome = st.text_input("Nome do Paciente")
idade = st.number_input("Idade", min_value=0, max_value=120, value=30)
st.markdown("Sinais Vitais:")
temp = st.number_input("Temperatura (°C)", value=36.5, step=0.1)
fc = st.number_input("Freq. Cardíaca (BPM)", value=80, step=1)
o2 = st.number_input("Saturação O2 (%)", min_value=0, max_value=100,
value=98)
btn_cadastrar = st.form_submit_button("Classificar e Inserir na Fila")
if btn_cadastrar and nome:
score_fisiologico = calcular_score_fisiologico(idade, temp, fc, o2)
cor = classificar_cor(score_fisiologico)
novo_paciente = {
'nome': nome,
'score_base': score_fisiologico,
'cor': cor,
'hora_chegada': datetime.datetime.now() # Registra o instante do clique
}
st.session_state.fila_pacientes.append(novo_paciente)
st.success(f"{nome} classificado como {cor}!")
with col_fila:
st.subheader("�� Fila de Atendimento Dinâmica (Ao Vivo)")
# Cria um botão para forçar a atualização manual do tempo e da fila
if st.button("�� Atualizar Tempos e Reordenar Fila"):
pass # Ao clicar, o Streamlit re-executa a tela inteira, chamando a função
atualizar_fila_dinamica()
df_exibicao = atualizar_fila_dinamica()
if not df_exibicao.empty:
# Destaca o próximo paciente
proximo = df_exibicao.iloc[0]
st.info(f"**Próximo Atendimento Chamado:** {proximo['Nome']}
({proximo['Classificação']}) - Tempo Espera: {proximo['Tempo na Fila (min)']} min")
# Exibe o DataFrame completo ordenado
st.dataframe(
df_exibicao[['Nome', 'Classificação', 'Tempo na Fila (min)', 'Tempo Alvo (min)',
'Score Fisiológico']],
use_container_width=True,
hide_index=True
)
else:
st.write("Fila vazia no momento.")
