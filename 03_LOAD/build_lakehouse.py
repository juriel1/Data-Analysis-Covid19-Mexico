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
SELECT 
    *,
    TRY_CAST(FECHA_INGRESO AS DATE) AS FECHA_INGRESO_DATE,
    TRY_CAST(FECHA_SINTOMAS AS DATE) AS FECHA_SINTOMAS_DATE,
    TRY_CAST(FECHA_DEF AS DATE) AS FECHA_DEF_DATE
FROM read_parquet('{fact_path_str}', hive_partitioning = true, union_by_name = true);
""")
print(" -> Vista 'fact_covid' vinculada con tolerancia a Schema Drift.")

dimensiones = [
    'DIM_Antigeno',
    'DIM_Comorbilidades_de_presion',
    'DIM_Comorbilidades_Respiratorias',
    'DIM_Datos_de_laboratorio',
    'DIM_Descripcion_del_paciente',
    'DIM_Geografico_informacion_paciente',
    'DIM_Geografico_Nacionalidad',
    'DIM_Geografico_residencia',
    'DIM_Indigena',
    'DIM_Otras_caracteristicas_medicas',
    'DIM_Ubicacion_de_laboratorio'
]

for dim in dimensiones:
    dim_path = raiz_proyecto / 'DATA' / 'Gold' / 'DIMENSIONES' / f'{dim}.parquet'
    dim_path_str = dim_path.as_posix()
    
    info_columnas = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{dim_path_str}');").fetchall()
    
    columnas_limpias = [row[0] for row in info_columnas if not row[0].startswith('DESC_')]
    
    columnas_sql = ", ".join(columnas_limpias)
    
    con.execute(f"""
        CREATE OR REPLACE TABLE {dim} AS 
        SELECT {columnas_sql} 
        FROM read_parquet('{dim_path_str}');
    """)
    print(f" -> Tabla '{dim}' importada exitosamente (Columnas DESC_ purgadas).")

con.close()
print("\n[Éxito] Lakehouse generado. Compatible con Windows y Linux.")