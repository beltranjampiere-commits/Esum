import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def sincronizar_todo():
    print("--- Iniciando Sincronización Maestra ---")

    # 1. AUTENTICACIÓN
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
    except Exception as e:
        print("Error de credenciales:", e)
        return

    # 2. CONFIGURACIÓN DE TAREAS
    # Aquí definimos qué archivo va a dónde.
    # El destino parece ser el mismo para todas (1_KCf...), así que lo optimizamos.
    ID_DESTINO_GLOBAL = "1_KCf41GMXjKlVV9cjZVhy_MATxVy0qO68E6aMlC5TX4"

    tareas = [
        {
            "nombre": "Seguimiento Retrasos",
            "id_origen": "18FdW9ywr3A1F6l6Br4zVisHqoBkYMBcbuNVfmwUkydU",
            "hoja_origen": "SEGUIMIENTO_RETRASOS",
            "hoja_destino": "BD_IMPORTADA",
            "solo_columnas_ak": False # Copiar todo
        },
        {
            "nombre": "Reprogramaciones",
            "id_origen": "1sxgbTWYkmowdFqWZphPS6TN3hjXJcsJtyBEtyluMFco",
            "hoja_origen": "REPROGRAMACIONES",
            "hoja_destino": "REPROGRAMACIONES_IMPORTADO",
            "solo_columnas_ak": True # Solo copiar A hasta K
        },
        {
            "nombre": "Reprocesos AppSheet",
            "id_origen": "1Gc68Jsqag-wK6xaV_KB98Ax5rHo5c2nLuzCmDsZRsIc",
            "hoja_origen": "REPROCESO",
            "hoja_destino": "BD_REPROPROCESOS",
            "solo_columnas_ak": False
        },
        {
            "nombre": "Ubicaciones",
            "id_origen": "15nEl-SJ1K6WqgPZikTLwQVaahTTEErZw_V13aLtBB9E",
            "hoja_origen": "REPORTE_UBICACION_AUTO",
            "hoja_destino": "UBICACION_ESUM_BD",
            "solo_columnas_ak": False
        }
    ]

    # Abrimos el archivo destino UNA sola vez para ahorrar tiempo
    try:
        ss_destino = client.open_by_key(ID_DESTINO_GLOBAL)
    except Exception as e:
        print(f"Error crítico al abrir destino global: {e}")
        return

    # 3. EJECUTAR BUCLE DE COPIA
    for tarea in tareas:
        print(f"\nProcesando: {tarea['nombre']}...")
        try:
            # A. Leer Origen (Usando Pandas es más rápido para leer todo)
            # Construimos la URL de descarga csv para velocidad
            url = f"https://docs.google.com/spreadsheets/d/{tarea['id_origen']}/gviz/tq?tqx=out:csv&sheet={tarea['hoja_origen']}"
            df = pd.read_csv(url)

            # B. Filtros Especiales
            if tarea['solo_columnas_ak']:
                # Seleccionar solo primeras 11 columnas (A-K)
                df = df.iloc[:, :11]

            # Limpieza básica (vacíos)
            df = df.fillna('')
            
            # C. Escribir en Destino
            try:
                worksheet = ss_destino.worksheet(tarea['hoja_destino'])
            except:
                print(f"  - La hoja {tarea['hoja_destino']} no existe, creándola...")
                worksheet = ss_destino.add_worksheet(title=tarea['hoja_destino'], rows=1000, cols=20)

            # Limpiar contenido anterior
            worksheet.clear()
            
            # Subir datos nuevos (incluyendo encabezados)
            datos_a_subir = [df.columns.values.tolist()] + df.values.tolist()
            
            if datos_a_subir:
                worksheet.update(range_name='A1', values=datos_a_subir)
                print(f"  ✅ {len(df)} filas copiadas exitosamente.")
            else:
                print("  ⚠️ No se encontraron datos para copiar.")

        except Exception as e:
            print(f"  ❌ Error en {tarea['nombre']}: {e}")

if __name__ == "__main__":
    sincronizar_todo()
