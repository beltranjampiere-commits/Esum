import os
import json
import gspread
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
# ¡OJO! Aquí debes poner el ID de la hoja donde quieres que se escriban los datos (Tu "Consolidado")
ID_HOJA_MAESTRA = "18FdW9ywr3A1F6l6Br4zVisHqoBkYMBcbuNVfmwUkydU" 

# Los IDs de tus bases de datos (Copiados de tu código)
IDS = {
    "REPORTE": "15nEl-SJ1K6WqgPZikTLwQVaahTTEErZw_V13aLtBB9E",
    "GLP": "18suk74673GWKKl_B3c32npwuMrbTuCRZ32kp333Mh9I",
    "REPROGRAMADOS": "1VtqpcLb0zv1n2nNI6uvFRjIhW3IClxn5ObMA8c4q2BI",
    "DESPACHOS": "15nEl-SJ1K6WqgPZikTLwQVaahTTEErZw_V13aLtBB9E"
}

def main():
    # 1. Autenticación
    json_credenciales = os.environ.get('GOOGLE_CREDENTIALS')
    if not json_credenciales:
        print("Error: No se encontraron las credenciales.")
        return

    credenciales_dict = json.loads(json_credenciales)
    gc = gspread.service_account_from_dict(credenciales_dict)

    print("🤖 Iniciando actualización masiva...")

    # 2. Conectar a la Hoja Maestra y leer VINs
    try:
        sh_maestra = gc.open_by_key(ID_HOJA_MAESTRA)
        # Asumimos que es la primera hoja o busca por nombre si prefieres
        ws_maestra = sh_maestra.get_worksheet(0) 
        
        # Leemos toda la columna A (VINs) desde la fila 2
        col_vins = ws_maestra.col_values(1)[1:] # [1:] salta el encabezado
        if not col_vins:
            print("No hay VINs para procesar.")
            return
            
        print(f"📥 Procesando {len(col_vins)} VINs...")

    except Exception as e:
        print(f"Error accediendo a la hoja maestra: {e}")
        return

    # 3. Descarga Masiva de Datos (Equivalente a tu traerDatosAPI)
    # Usamos diccionarios para búsqueda rápida (Hash Maps)
    
    # --- A. REPORTE UBICACION (B:L) ---
    map_ubicacion = {}
    try:
        sh_rep = gc.open_by_key(IDS["REPORTE"])
        # Traemos datos como lista de listas. value_render_option='FORMATTED_VALUE' trae el texto como se ve en Excel
        raw_ub = sh_rep.worksheet("REPORTE_UBICACION_AUTO").get("B:L", value_render_option='FORMATTED_VALUE')
        for row in raw_ub:
            if row: # Si la fila no está vacía
                vin = str(row[0]).strip() # Col B es indice 0
                if vin: map_ubicacion[vin] = row
    except Exception as e:
        print(f"⚠️ Error leyendo Reporte Ubicación: {e}")

    # --- B. PLANIFICADOS (A:I) ---
    map_planificados = {}
    try:
        # Reusamos sh_rep porque es el mismo archivo
        raw_plan = sh_rep.worksheet("PLANIFICADOS").get("A:I", value_render_option='FORMATTED_VALUE')
        for row in raw_plan:
            if row:
                vin = str(row[0]).strip() # Col A es indice 0
                if vin: map_planificados[vin] = row
    except Exception as e:
        print(f"⚠️ Error leyendo Planificados: {e}")

    # --- C. REPROGRAMADOS (Hoja 1!D:K) ---
    map_reprog = {}
    try:
        sh_reprog = gc.open_by_key(IDS["REPROGRAMADOS"])
        raw_rep = sh_reprog.worksheet("Hoja 1").get("D:K", value_render_option='FORMATTED_VALUE')
        for row in raw_rep:
            if row:
                vin = str(row[0]).strip() # Col D es indice 0 relativo al rango
                if vin: map_reprog[vin] = row
    except Exception as e:
        print(f"⚠️ Error leyendo Reprogramados: {e}")

    # --- D. DESPACHOS (A:H) ---
    map_despachos = {}
    try:
        sh_desp = gc.open_by_key(IDS["DESPACHOS"])
        raw_desp = sh_desp.worksheet("DESPACHOS").get("A:H", value_render_option='FORMATTED_VALUE')
        for row in raw_desp:
            if row:
                vin = str(row[0]).strip()
                if vin: map_despachos[vin] = row
    except Exception as e:
        print(f"⚠️ Error leyendo Despachos: {e}")

    # --- E. GLP (Múltiples hojas) ---
    map_glp = {}
    hojas_glp = ["octubre 2025", "NOVIEMBRE 2025", "DICIEMBRE 2025"]
    try:
        sh_glp = gc.open_by_key(IDS["GLP"])
        for nombre_hoja in hojas_glp:
            try:
                raw_glp = sh_glp.worksheet(nombre_hoja).get_all_values()
                for row in raw_glp:
                    if len(row) > 5: # Asegurar que existe columna F
                        vin = str(row[0]).strip()
                        fecha = str(row[5]).strip() # Col F es indice 5
                        if vin and fecha:
                            map_glp[vin] = fecha
            except:
                continue # Si una hoja no existe, seguimos
    except Exception as e:
        print(f"⚠️ Error leyendo GLP: {e}")

    # 4. Procesamiento en Memoria (Cruzar datos)
    out_BCD = []
    out_HI = []
    out_OPQ = []
    out_T = []

    for vin in col_vins:
        vin = str(vin).strip()
        
        # --- Lógica B, C, D (Modelo, Ubicación, Concesionario) ---
        ub = map_ubicacion.get(vin)
        plan = map_planificados.get(vin)
        
        # Indices seguros (usamos len para no fallar si falta una celda)
        modelo = "- - -"
        ubicacion = "-"
        if ub:
            p1 = ub[6] if len(ub) > 6 else "" # H
            p2 = ub[5] if len(ub) > 5 else "" # G
            p3 = ub[1] if len(ub) > 1 else "" # C
            modelo = f"{p1} {p2} {p3}".strip()
            ubicacion = ub[7] if len(ub) > 7 else "-" # I
        
        concesionario = plan[3] if (plan and len(plan) > 3) else "" # D
        out_BCD.append([modelo, ubicacion, concesionario])

        # --- Lógica H, I (GLP) ---
        glp_fecha = map_glp.get(vin, "")
        h_val, i_val = "-", ""
        
        if glp_fecha:
            # Validación simple de fecha (contiene / o -)
            if "/" in glp_fecha or "-" in glp_fecha:
                h_val = f"FUE CONVERTIDO A GLP - {glp_fecha}"
                if "2025" in glp_fecha:
                    i_val = glp_fecha
            else:
                h_val = glp_fecha
        
        out_HI.append([h_val, i_val])

        # --- Lógica O, P, Q (Reprogramados) ---
        rep = map_reprog.get(vin)
        if rep:
            obs = rep[3] if len(rep) > 3 else "" # G -> index 3 en D:K
            new_date = rep[7] if len(rep) > 7 else "" # K -> index 7 en D:K
            out_OPQ.append(["SÍ", obs, new_date])
        else:
            out_OPQ.append(["NO", "", ""])

        # --- Lógica T (Despachos) ---
        desp = map_despachos.get(vin)
        fecha_desp = desp[7] if (desp and len(desp) > 7) else "" # H -> index 7
        out_T.append([fecha_desp])

    # 5. Escritura Masiva (Batch Update)
    print("💾 Guardando cambios...")
    
    # Calculamos el rango exacto basado en la cantidad de VINs
    num_rows = len(col_vins)
    rango_fin = num_rows + 1 # +1 porque empezamos en fila 2
    
    # Actualizamos por bloques (Es mucho más rápido que celda por celda)
    ws_maestra.update(range_name=f"B2:D{rango_fin}", values=out_BCD)
    ws_maestra.update(range_name=f"H2:I{rango_fin}", values=out_HI)
    ws_maestra.update(range_name=f"O2:Q{rango_fin}", values=out_OPQ)
    ws_maestra.update(range_name=f"T2:T{rango_fin}", values=out_T)

    print("✅ ¡Actualización completada con éxito!")

if __name__ == "__main__":
    main()
