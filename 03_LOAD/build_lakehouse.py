import duckdb
from pathlib import Path

# 1. Auto-descubrimiento Agnóstico al OS
directorio_actual = Path(__file__).resolve().parent
raiz_proyecto = directorio_actual.parent

print(f"[Sistema] Ruta raíz detectada: {raiz_proyecto}")

# 2. Construcción de Rutas
db_path = raiz_proyecto / 'DATA' / 'Consultation' / 'covid_lakehouse.duckdb'
fact_path = raiz_proyecto / 'DATA' / 'Gold' / 'COVID_FACT' / 'year=*' / 'month=*' / '*.parquet'

# Seguridad: Creación de directorios faltantes
db_path.parent.mkdir(parents=True, exist_ok=True)

# 3. Conversión Nativa POSIX (La clave multiplataforma)
# .as_posix() garantiza que la ruta devuelta use '/' siempre, 
# sin importar si Python se está ejecutando en Windows o Linux.
db_path_str = db_path.as_posix()
fact_path_str = fact_path.as_posix()

print("Iniciando conexión y reescritura del catálogo...")
con = duckdb.connect(db_path_str)

# 4. Inyección SQL
con.execute(f"""
CREATE OR REPLACE VIEW fact_covid AS
SELECT * FROM read_parquet('{fact_path_str}', hive_partitioning = true);
""")
print(" -> Vista 'fact_covid' vinculada (Formato POSIX).")

dimensiones = [
    'DIM_Geografico_residencia',
    'DIM_Descripcion_del_paciente',
    'DIM_Comorbilidades_Respiratorias'
]

for dim in dimensiones:
    # IMPORTANTE: Asegúrate de que las carpetas 'DIMENSIONES' y los nombres de archivo coincidan en mayúsculas/minúsculas
    dim_path = raiz_proyecto / 'DATA' / 'Gold' / 'DIMENSIONES' / f'{dim}.parquet'
    
    con.execute(f"CREATE OR REPLACE TABLE {dim} AS SELECT * FROM read_parquet('{dim_path.as_posix()}');")
    print(f" -> Tabla '{dim}' importada exitosamente.")

con.close()
print("\n[Éxito] Lakehouse generado. Compatible con Windows y Linux.")