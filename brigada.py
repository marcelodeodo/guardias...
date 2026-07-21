import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

excel_filename = "datos.xlsx"


@st.cache_data
def cargar_datos():
    if not os.path.exists(excel_filename):
        return None, "El archivo datos.xlsx no existe en la carpeta del proyecto."
    try:
        df = pd.read_excel(excel_filename, sheet_name='LISTADO PERSONAL 2024', header=None)
        personal = []
        for idx in range(6, len(df)):
            val_nombre = df.iloc[idx, 1]
            val_indicativo = df.iloc[idx, 2]

            if pd.notna(val_nombre):
                nombre = str(val_nombre).strip()
                if "." in nombre:
                    indicativo = str(val_indicativo).strip() if pd.notna(val_indicativo) else "S/D"

                    ind_upper = indicativo.upper()
                    if ind_upper.startswith("O"):
                        categoria = "Oficiales / Jefes"
                    elif ind_upper.startswith("BR") or ind_upper.startswith("B"):
                        categoria = "Brigadistas (Bravo)"
                    elif ind_upper.startswith("CH"):
                        categoria = "Choferes (Charlie)"
                    elif ind_upper.startswith("MK"):
                        categoria = "Mecánicos / Camioneros (MK)"
                    elif ind_upper.startswith("C"):
                        categoria = "Combatientes"
                    else:
                        categoria = "Otros / Sin Clasificar"

                    personal.append({
                        "Nombre": nombre,
                        "Indicativo": indicativo,
                        "Categoria": categoria
                    })
        return pd.DataFrame(personal), None
    except Exception as e:
        return None, str(e)


df_personal, error_detalle = cargar_datos()

if 'guardias_cargadas' not in st.session_state:
    st.session_state.guardias_cargadas = {
        "Mañana": [],
        "Tarde": [],
        "Noche": [],
        "Franco": []
    }

if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
    st.session_state.rol_actual = None

st.title("🔥 SPLIF El Bolsón - Control de Guardias")

if error_detalle:
    st.error(f"⚠️ Error al leer el Excel: {error_detalle}")

if not st.session_state.sesion_iniciada:
    st.markdown("### 🔐 Acceso al Sistema")
    tipo_ingreso = st.selectbox("Seleccioná el tipo de acceso:", ["Usuario (Visualización)", "Administrador (Gestión)"])
    pass_ingresada = st.text_input("Ingresá la contraseña:", type="password")

    if st.button("Ingresar", type="primary"):
        if tipo_ingreso == "Usuario (Visualización)":
            if pass_ingresada == "usuario2026":
                st.session_state.sesion_iniciada = True
                st.session_state.rol_actual = "Usuario"
                st.rerun()
            else:
                st.error("Contraseña incorrecta (Clave: usuario2026)")
        elif tipo_ingreso == "Administrador (Gestión)":
            if pass_ingresada == "splif2026":
                st.session_state.sesion_iniciada = True
                st.session_state.rol_actual = "Admin"
                st.rerun()
            else:
                st.error("Contraseña incorrecta (Clave: splif2026)")
else:
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.sesion_iniciada = False
        st.session_state.rol_actual = None
        st.rerun()

    orden_categorias = ["Oficiales / Jefes", "Choferes (Charlie)", "Mecánicos / Camioneros (MK)", "Combatientes",
                        "Brigadistas (Bravo)", "Otros / Sin Clasificar"]
    foto_provisoria = "https://cdn-icons-png.flaticon.com/512/149/149071.png"

    if st.session_state.rol_actual == "Usuario":
        st.subheader("📋 Estado Actual de Guardias por Rango y Turno")
        col1, col2, col3, col4 = st.columns(4)
        turnos_info = [("☀️ Mañana", "Mañana", col1), ("🌤️ Tarde", "Tarde", col2), ("🌙 Noche", "Noche", col3),
                       ("☕ Franco", "Franco", col4)]

        for titulo_turno, nombre_turno, columna in turnos_info:
            with columna:
                st.markdown(f"### {titulo_turno}")
                personal_turno = st.session_state.guardias_cargadas.get(nombre_turno, [])
                if not personal_turno:
                    st.info("Sin personal asignado.")
                else:
                    df_turno = pd.DataFrame(personal_turno)
                    for cat in orden_categorias:
                        subgrupo = df_turno[df_turno["Categoria"] == cat]
                        if not subgrupo.empty:
                            st.markdown(f"**📌 {cat}**")
                            for _, p in subgrupo.iterrows():
                                with st.container(border=True):
                                    st.image(foto_provisoria, width=40)
                                    st.markdown(f"**{p['Nombre']}**\n`{p['Indicativo']}`")

    elif st.session_state.rol_actual == "Admin":
        st.subheader("🔒 Panel de Administración Estilo Pizarrón")

        if df_personal is None or df_personal.empty:
            st.warning("⚠️ No se puede asignar personal porque el Excel no tiene datos válidos.")
        else:
            # Sección superior para agregar rápido
            with st.container(border=True):
                st.markdown("### ➕ Asignar Personal a Turno")
                col_sel1, col_sel2, col_sel3 = st.columns([2, 2, 1])

                with col_sel1:
                    personal_ya_asignado = [p["Nombre"] for t in ["Mañana", "Tarde", "Noche", "Franco"] for p in
                                            st.session_state.guardias_cargadas[t]]
                    df_disponibles = df_personal[~df_personal["Nombre"].isin(personal_ya_asignado)]

                    if df_disponibles.empty:
                        st.info("⚠️ Todo el personal fue asignado.")
                        opciones_personal = []
                    else:
                        opciones_personal = [f"{row['Nombre']} ({row['Indicativo']})" for _, row in
                                             df_disponibles.iterrows()]

                    miembro_seleccionado = st.selectbox("Personal disponible:",
                                                        opciones_personal if opciones_personal else ["Sin disponibles"])

                with col_sel2:
                    turno_elegido = st.selectbox("Turno de destino:", ["Mañana", "Tarde", "Noche", "Franco"])

                with col_sel3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if opciones_personal and st.button("Asignar", type="primary", use_container_width=True):
                        nombre_limpio = miembro_seleccionado.split(" (")[0]
                        indicativo_limpio = miembro_seleccionado.split(" (")[1].replace(")", "")
                        cat_miembro = df_personal[df_personal["Nombre"] == nombre_limpio]["Categoria"].values[0]

                        nuevo_elemento = {"Nombre": nombre_limpio, "Indicativo": indicativo_limpio,
                                          "Categoria": cat_miembro}
                        st.session_state.guardias_cargadas[turno_elegido].append(nuevo_elemento)
                        st.success(f"Asignado {nombre_limpio}")
                        st.rerun()

            st.markdown("---")
            st.markdown("### 📋 Pizarrón de Turnos Fijos (Hacé clic en 'Devolver' para sacarlos)")

            # Los 4 turnos fijos en columnas visuales
            col_m, col_t, col_n, col_f = st.columns(4)
            pizarron_info = [("☀️ Mañana", "Mañana", col_m), ("🌤️ Tarde", "Tarde", col_t), ("🌙 Noche", "Noche", col_n),
                             ("☕ Franco", "Franco", col_f)]

            for titulo_t, nombre_t, col_columna in pizarron_info:
                with col_columna:
                    with st.container(border=True):
                        st.markdown(f"#### {titulo_t}")
                        asignados_t = st.session_state.guardias_cargadas.get(nombre_t, [])

                        if not asignados_t:
                            st.info("Vacío")
                        else:
                            for idx_p, p in enumerate(asignados_t):
                                st.markdown(f"**{p['Nombre']}**\n`{p['Indicativo']}`")
                                # Botón individual para devolver al listado de disponibles
                                if st.button("↩️ Quitar", key=f"quitar_{nombre_t}_{idx_p}_{p['Nombre']}"):
                                    st.session_state.guardias_cargadas[nombre_t].pop(idx_p)
                                    st.rerun()
                                st.markdown("---")

            if st.button("🗑️ Reiniciar / Borrar Todas las Guardias"):
                st.session_state.guardias_cargadas = {"Mañana": [], "Tarde": [], "Noche": [], "Franco": []}
                st.rerun()
