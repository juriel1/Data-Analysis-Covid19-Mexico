import duckdb

db_path = '../DATA/Consultation/covid_lakehouse.duckdb'
con = duckdb.connect(db_path)

con.execute("""
CREATE OR REPLACE VIEW fact_covid AS
SELECT * FROM read_parquet('../DATA/Gold/COVID_FACT/year=*/month=*/*.parquet', hive_partitioning = true);
""")

dimensiones = [
    'DIM_Geografico_residencia',
    'DIM_Descripcion_del_paciente',
    'DIM_Comorbilidades_Respiratorias'
]

for dim in dimensiones:
    path = f"../DATA/Gold/DIMENSIONES/{dim}.parquet"
    con.execute(f"CREATE OR REPLACE TABLE {dim} AS SELECT * FROM read_parquet('{path}');")
    print(f"Dimensión {dim} integrada exitosamente.")

con.close()