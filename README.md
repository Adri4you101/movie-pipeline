# Movie Score Data Pipeline

Pipeline ETL en Python puro que combina datos de películas de tres proveedores en un dataset unificado.

## Ejecución

```bash
python main.py
```

## Tests

```bash
python -m unittest discover tests/ -v
```

## Proveedores

| Proveedor | Fichero(s) | Datos |
|-----------|-----------|-------|
| CriticAgg | `data/provider1.csv` | Puntuaciones de críticos |
| AudiencePulse | `data/provider2.json` | Ratings de audiencia |
| BoxOfficeMetrics | `data/provider3_domestic.csv`, `data/provider3_international.csv`, `data/provider3_financials.csv` | Taquilla y presupuesto |

## Añadir un Provider nuevo

1. Crear `src/providers/mi_provider.py` heredando de `Provider`
2. Implementar `parse() -> list[MovieRecord]`
3. Añadir campos nuevos a `MovieRecord` si es necesario (todos opcionales, `None` por defecto)
4. Registrar en `main.py`
