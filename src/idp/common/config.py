"""Centralized configuration management using pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinIOConfig(BaseSettings):
    """MinIO (Bronze Layer) configuration."""

    endpoint: str = Field(default="localhost:9000")
    access_key: str = Field(default="minioadmin")
    secret_key: str = Field(default="minioadmin")
    secure: bool = Field(default=False)
    bucket_bronze: str = Field(default="bronze")

    model_config = SettingsConfigDict(env_prefix="MINIO_")


class PostgresConfig(BaseSettings):
    """PostgreSQL (Gold Layer) configuration."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    db: str = Field(default="idp")
    user: str = Field(default="idp_user")
    password: str = Field(default="changeme")

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class DuckDBConfig(BaseSettings):
    """DuckDB (Transformation Layer) configuration."""

    path: str = Field(default="data/gold.duckdb")

    model_config = SettingsConfigDict(env_prefix="DUCKDB_")


class GeminiConfig(BaseSettings):
    """Gemini API configuration."""

    api_key: str | None = Field(default=None)
    embedding_model: str = Field(default="text-embedding-004")
    chat_model: str = Field(default="gemini-2.0-flash")

    model_config = SettingsConfigDict(env_prefix="GEMINI_")


class APIConfig(BaseSettings):
    """FastAPI server configuration."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(env_prefix="API_")


class ProxyConfig(BaseSettings):
    """Proxy configuration for external requests."""

    http_proxy: str | None = Field(default=None)
    https_proxy: str | None = Field(default=None)
    no_proxy: str = Field(default="localhost,127.0.0.1")

    model_config = SettingsConfigDict(env_prefix="")

    def get_proxies(self) -> dict[str, str] | None:
        """Get proxy dict for httpx/requests."""
        if self.http_proxy or self.https_proxy:
            return {
                "http://": self.http_proxy or "",
                "https://": self.https_proxy or "",
            }
        return None


class WorldBankConfig(BaseSettings):
    """World Bank API configuration."""

    api_url: str = Field(default="https://api.worldbank.org/v2")
    wds_url: str = Field(default="https://search.worldbank.org/api/v3/wds")
    per_page: int = Field(default=1000)
    batch_size: int = Field(default=10)
    default_start_year: int = Field(default=2010)

    model_config = SettingsConfigDict(env_prefix="WB_")


class Settings(BaseSettings):
    """Application-wide settings."""

    minio: MinIOConfig = Field(default_factory=MinIOConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    duckdb: DuckDBConfig = Field(default_factory=DuckDBConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    world_bank: WorldBankConfig = Field(default_factory=WorldBankConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Default indicator list for World Bank ingestion
INDICATORS: list[dict[str, str]] = [
    {"code": "NY.GDP.MKTP.CD", "name": "GDP (current US$)", "source": "WDI"},
    {"code": "NY.GDP.PCAP.CD", "name": "GDP per capita (current US$)", "source": "WDI"},
    {"code": "NY.GDP.MKTP.KD.ZG", "name": "GDP growth (annual %)", "source": "WDI"},
    {"code": "SP.POP.TOTL", "name": "Population, total", "source": "WDI"},
    {"code": "SP.POP.GROW", "name": "Population growth (annual %)", "source": "WDI"},
    {"code": "NE.EXP.GNFS.ZS", "name": "Exports of goods and services (% of GDP)", "source": "WDI"},
    {"code": "NE.IMP.GNFS.ZS", "name": "Imports of goods and services (% of GDP)", "source": "WDI"},
    {"code": "BN.CAB.XOKA.GD.ZS", "name": "Current account balance (% of GDP)", "source": "WDI"},
    {"code": "FP.CPI.TOTL.ZG", "name": "Inflation, consumer prices (annual %)", "source": "WDI"},
    {"code": "SL.UEM.TOTL.ZS", "name": "Unemployment, total (% of total labor force)", "source": "WDI"},
    {"code": "BX.KLT.DINV.WD.GD.ZS", "name": "Foreign direct investment, net inflows (% of GDP)", "source": "WDI"},
    {"code": "GC.DOD.TOTL.GD.ZS", "name": "Central government debt, total (% of GDP)", "source": "WDI"},
    {"code": "IT.NET.USER.ZS", "name": "Individuals using the Internet (% of population)", "source": "WDI"},
    {"code": "SE.ADT.LITR.ZS", "name": "Literacy rate, adult total (% of people ages 15 and above)", "source": "WDI"},
    {"code": "SH.XPD.CHEX.GD.ZS", "name": "Current health expenditure (% of GDP)", "source": "WDI"},
    {"code": "SP.DYN.LE00.IN", "name": "Life expectancy at birth, total (years)", "source": "WDI"},
    {"code": "EN.ATM.CO2E.KT", "name": "CO2 emissions (kt)", "source": "WDI"},
    {"code": "EG.USE.ELEC.KH.PC", "name": "Electric power consumption (kWh per capita)", "source": "WDI"},
    {"code": "ER.H2O.FWTL.ZS", "name": "Annual freshwater withdrawals, total (% of internal resources)", "source": "WDI"},
    {"code": "AG.LND.FRST.ZS", "name": "Forest area (% of land area)", "source": "WDI"},
    {"code": "DT.ODA.ODAT.GN.ZS", "name": "Net ODA received (% of GNI)", "source": "WDI"},
    {"code": "FM.LBL.BMNY.GD.ZS", "name": "Broad money (% of GDP)", "source": "WDI"},
    {"code": "FR.INR.RINR", "name": "Real interest rate (%)", "source": "WDI"},
    {"code": "PA.NUS.FCRF", "name": "Official exchange rate (LCU per US$, period average)", "source": "WDI"},
    {"code": "ST.INT.ARVL", "name": "International tourism, number of arrivals", "source": "WDI"},
    {"code": "TG.VAL.TOTL.GD.ZS", "name": "Merchandise trade (% of GDP)", "source": "WDI"},
    {"code": "TX.VAL.TECH.MF.ZS", "name": "High-technology exports (% of manufactured exports)", "source": "WDI"},
    {"code": "VC.IHR.PSRC.P5", "name": "Intentional homicides (per 100,000 people)", "source": "WDI"},
    {"code": "SI.POV.GINI", "name": "Gini index", "source": "WDI"},
    {"code": "SL.TLF.TOTL.IN", "name": "Labor force, total", "source": "WDI"},
    {"code": "NV.AGR.TOTL.ZS", "name": "Agriculture, forestry, and fishing, value added (% of GDP)", "source": "WDI"},
    {"code": "NV.IND.TOTL.ZS", "name": "Industry (including construction), value added (% of GDP)", "source": "WDI"},
    {"code": "NV.SRV.TOTL.ZS", "name": "Services, value added (% of GDP)", "source": "WDI"},
]

# Default country list for World Bank ingestion
COUNTRIES: list[dict[str, str]] = [
    {"code": "VN", "name": "Vietnam"},
    {"code": "CN", "name": "China"},
    {"code": "JP", "name": "Japan"},
    {"code": "KR", "name": "South Korea"},
    {"code": "SG", "name": "Singapore"},
    {"code": "IN", "name": "India"},
    {"code": "ID", "name": "Indonesia"},
    {"code": "TH", "name": "Thailand"},
    {"code": "US", "name": "United States"},
    {"code": "DE", "name": "Germany"},
    {"code": "FR", "name": "France"},
    {"code": "GB", "name": "United Kingdom"},
    {"code": "RU", "name": "Russia"},
    {"code": "BR", "name": "Brazil"},
    {"code": "ZA", "name": "South Africa"},
    {"code": "NG", "name": "Nigeria"},
    {"code": "AU", "name": "Australia"},
    {"code": "AE", "name": "United Arab Emirates"},
    {"code": "MX", "name": "Mexico"},
    {"code": "CA", "name": "Canada"},
]


def get_wb_indicators(codes: list[str] | None = None) -> list[dict[str, str]]:
    """Get World Bank indicator definitions.

    Args:
        codes: Optional list of indicator codes to filter by.

    Returns:
        List of indicator dicts with 'code', 'name', 'source' keys.
    """
    if codes is None:
        return list(INDICATORS)
    return [i for i in INDICATORS if i["code"] in codes]


def get_wb_countries(codes: list[str] | None = None) -> list[dict[str, str]]:
    """Get World Bank country definitions.

    Args:
        codes: Optional list of country codes to filter by.

    Returns:
        List of country dicts with 'code', 'name' keys.
    """
    if codes is None:
        return list(COUNTRIES)
    return [c for c in COUNTRIES if c["code"] in codes]
