import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Academia Golf - Progreso", page_icon="⛳", layout="wide")

# --- TU SHEET VIVO ---
SHEET_ID = "1iMkeOjucI-3-x70dgNP22OrH2hafSZj9i0eJbKFt7Kg"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip().upper() for c in df.columns]
    # Normaliza nombres
    tecnicas = ['GRIP','POSTURA','ALINEACIÓN Y DIRECCIÓN','BACK SWING','CHIP','PUTT','DESEMPEÑO EN EL CAMPO','REGLAS DE ETIQUETA','ESTRATEGIA DE JUEGO']
    # Asegura que existan
    tecnicas = [t for t in tecnicas if t in df.columns]
    return df, tecnicas

df, tecnicas = load_data()

# --- REGLA DE ORO: ULTIMO PERIODO ---
# Detecta cual es el ultimo periodo (ej: 1er SEMESTRE DE 2026)
ultimo_periodo = df['PERIODO'].dropna().astype(str).unique()
ultimo_periodo = sorted(ultimo_periodo)[-1]
df_ultimo = df[df['PERIODO'] == ultimo_periodo].copy()
df_ultimo['PROMEDIO'] = pd.to_numeric(df_ultimo['PROMEDIO'], errors='coerce')

st.title(f"⛳ Dashboard Academia - {ultimo_periodo}")
st.caption("Datos en vivo desde tu Google Sheets. Se actualiza solo al editar.")

jugador = st.selectbox("🔍 Busca al jugador", sorted(df['JUGADOR'].dropna().unique()))

data_hist = df[df['JUGADOR'] == jugador].sort_values('PERIODO')

if not df_ultimo[df_ultimo['JUGADOR']==jugador].empty:
    data_actual = df_ultimo[df_ultimo['JUGADOR']==jugador].iloc[0]
else:
    data_actual = data_hist.iloc[-1]
    st.warning(f"{jugador} no tiene datos en {ultimo_periodo}, mostrando {data_actual['PERIODO']}")

m1,m2,m3 = st.columns(3)
m1.metric("Promedio", f"{float(data_actual['PROMEDIO']):.2f} / 5.0")
m2.metric("Nivel", data_actual['NIVEL'])
m3.metric("Evaluaciones", len(data_hist))

# Radar vs Academia
fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=[float(data_actual[t]) for t in tecnicas], theta=tecnicas, fill='toself', name=jugador))
prom_acad = [df_ultimo[t].astype(float).mean() for t in tecnicas]
fig.add_trace(go.Scatterpolar(r=prom_acad, theta=tecnicas, fill='toself', name=f'Promedio Academia', line_dash='dot'))
fig.update_layout(polar=dict(radialaxis=dict(range=[0,5])), showlegend=True, height=500)
st.plotly_chart(fig, use_container_width=True)

# Evolución
if len(data_hist) > 1:
    st.subheader(f"📈 Evolución de {jugador}")
    fig2 = px.line(data_hist, x='PERIODO', y='PROMEDIO', markers=True)
    fig2.update_yaxes(range=[0,5])
    st.plotly_chart(fig2, use_container_width=True)

# Semaforo
st.subheader("Detalle por técnica")
def color_val(v):
    try:
        v=float(v)
        if v>=4: return 'background-color: #C6EFCE; color: #006100'
        if v>=3: return 'background-color: #FFEB9C; color: #9C6500'
        return 'background-color: #FFC7CE; color: #9C0006'
    except: return ''

st.dataframe(df_ultimo[df_ultimo['JUGADOR']==jugador][['JUGADOR']+tecnicas+['PROMEDIO']].style.applymap(color_val, subset=tecnicas), use_container_width=True)

st.divider()
st.subheader(f"🏆 Ranking Academia - {ultimo_periodo}")
st.dataframe(df_ultimo[['JUGADOR','NIVEL','PROMEDIO']].sort_values('PROMEDIO', ascending=False).reset_index(drop=True), use_container_width=True)