import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re

st.set_page_config(page_title="Academia Arrayanes", layout="wide")

# --- LOGO ---
for nombre_logo in ["Logo.png.jpg", "logo.png", "Logo.png", "logo.jpg"]:
    if os.path.exists(nombre_logo):
        st.sidebar.image(nombre_logo, width=180)
        st.image(nombre_logo, width=110)
        break

st.title("Academia Arrayanes")

CSV_URL = "https://docs.google.com/spreadsheets/d/1iMkeOjucI-3-x70dgNP22OrH2hafSZj9i0eJbKFt7Kg/export?format=csv"
DIC_URL = "https://docs.google.com/spreadsheets/d/1iMkeOjucI-3-x70dgNP22OrH2hafSZj9i0eJbKFt7Kg/export?format=csv&gid=2071529339"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = [str(c).strip().upper() for c in df.columns]
    for col in df.columns:
        if col not in ['JUGADOR','NIVEL','PERIODO','FECHA','PROMEDIO','ORDEN']:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    tecnicas = [c for c in df.columns if c not in ['JUGADOR','FECHA','PERIODO','NIVEL','PROMEDIO','ORDEN']]
    tecnicas = [c for c in tecnicas if not df[c].isna().all()]
    df['PROMEDIO'] = df[tecnicas].mean(axis=1, skipna=True).round(2)
    if 'PERIODO' not in df.columns:
        df['PERIODO'] = "1er Semestre 2026"
    def get_orden(p):
        txt=str(p); m=re.search(r'(20\d\d)',txt)
        anio=int(m.group(1)) if m else 2026
        sem=1 if '1' in txt else 2
        return anio*10+sem
    df['ORDEN'] = df['PERIODO'].apply(get_orden)
    return df.sort_values('ORDEN'), tecnicas

@st.cache_data(ttl=60)
def load_diccionario():
    try:
        d = pd.read_csv(DIC_URL)
        d.columns = [str(c).strip().upper() for c in d.columns]
        return d
    except:
        return pd.DataFrame()

df, tecnicas = load_data()
dic_df = load_diccionario()

# --- SELECTORES ---
c_sel1, c_sel2 = st.columns(2)
with c_sel1:
    periodos = df.sort_values('ORDEN')['PERIODO'].dropna().unique().tolist()
    periodo_sel = st.selectbox("1. Selecciona Periodo:", periodos, index=len(periodos)-1)
with c_sel2:
    df_filtrado = df[df['PERIODO']==periodo_sel]
    jugador = st.selectbox("2. Selecciona Jugador:", sorted(df_filtrado['JUGADOR'].dropna().unique()))

df_jug_todos = df[df['JUGADOR']==jugador].sort_values('ORDEN')
df_jug_actual = df_filtrado[df_filtrado['JUGADOR']==jugador]
if len(df_jug_actual)==0:
    st.warning("Ese jugador no tiene datos"); st.stop()

ult = df_jug_actual.iloc[-1]
df_rank = df_filtrado.groupby('JUGADOR').last().reset_index().sort_values('PROMEDIO', ascending=False).reset_index(drop=True)
df_rank['PUESTO']=df_rank.index+1
puesto = int(df_rank[df_rank['JUGADOR']==jugador]['PUESTO'].values[0])

mejora_texto = ""; delta_prom = 0; ant = None
if len(df_jug_todos) >= 2:
    idx_actual = df_jug_todos[df_jug_todos['PERIODO']==periodo_sel].index
    if len(idx_actual)>0:
        pos = df_jug_todos.index.get_loc(idx_actual[0])
        if pos > 0:
            ant = df_jug_todos.iloc[pos-1]
            delta_prom = ult['PROMEDIO'] - ant['PROMEDIO']
            mejora_texto = f"vs {ant['PERIODO']}"

# --- METRICAS ---
c1,c2,c3,c4 = st.columns(4)
c1.metric("Periodo", periodo_sel)
c2.metric("Puesto", f"{puesto} de {len(df_rank)}")
c3.metric("Promedio", f"{ult['PROMEDIO']:.2f} / 5", delta=f"{delta_prom:+.2f} {mejora_texto}" if delta_prom!=0 else None)
c4.metric("Periodos jugados", len(df_jug_todos))

# --- NOTAS POR TECNICA ---
st.divider()
st.subheader("Notas por técnica")
cols_top = st.columns(len(tecnicas))
for i, tec in enumerate(tecnicas):
    nota = ult[tec]
    if ant is not None and pd.notna(ant[tec]) and pd.notna(nota):
        d = nota - ant[tec]
        cols_top[i].metric(tec, f"{nota:.1f}", delta=f"{d:+.1f}")
    else:
        cols_top[i].metric(tec, f"{nota:.1f}" if pd.notna(nota) else "-")

# --- GRAFICO EVOLUCION ---
st.divider()
st.subheader(f"Evolución de {jugador}")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_jug_todos['PERIODO'], y=df_jug_todos['PROMEDIO'], mode='lines+markers', name='PROMEDIO', line=dict(width=5, color='black'), marker=dict(size=12, symbol='star')))
for tec in tecnicas:
    fig.add_trace(go.Scatter(x=df_jug_todos['PERIODO'], y=df_jug_todos[tec], mode='lines+markers', name=tec))
fig.update_layout(yaxis=dict(range=[0,5.5], dtick=1), height=450, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- TELARAÑA ---
st.subheader(f"Telaraña - {jugador} - {periodo_sel}")
fig2 = go.Figure(go.Scatterpolar(r=ult[tecnicas].values, theta=tecnicas, fill='toself'))
fig2.update_layout(polar=dict(radialaxis=dict(range=[0,5], dtick=1)), height=500)
st.plotly_chart(fig2, use_container_width=True, key="telarana")

# --- DICCIONARIO FINAL ---
st.divider()
with st.expander("📊 Ver escala de progreso", expanded=False):
    if not dic_df.empty:
        st.dataframe(dic_df, use_container_width=True)
    else:
        st.warning("No se pudo cargar el diccionario. Verifique que la hoja gid=2071529339 esté publicada.")

if st.sidebar.button("Limpiar Cache"):
    st.cache_data.clear()