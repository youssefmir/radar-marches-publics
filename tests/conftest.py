import pytest

from radar import config

requires_warehouse = pytest.mark.skipif(not config.WAREHOUSE.exists(), reason="entrepôt absent : lancez `make dbt`")
requires_avis = pytest.mark.skipif(
    not (config.INTERIM / "boamp_avis.parquet").exists(), reason="instantané BOAMP absent : lancez `make data`"
)
