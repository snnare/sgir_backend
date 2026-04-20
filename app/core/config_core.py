from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str = "sgir"
    POSTGRES_PASSWORD: str = "sgir"
    POSTGRES_DB: str = "sgir_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def POSTGRES_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MySQL 5.x
    MYSQL5_USER: str = "sgir"
    MYSQL5_PASSWORD: str = "sgir"
    MYSQL5_DB: str = "sgir_db_5"
    MYSQL5_HOST: str = "localhost"
    MYSQL5_PORT: int = 3305

    @property
    def MYSQL5_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL5_USER}:{self.MYSQL5_PASSWORD}@{self.MYSQL5_HOST}:{self.MYSQL5_PORT}/{self.MYSQL5_DB}"

    # MySQL 8.x
    MYSQL8_USER: str = "sgir"
    MYSQL8_PASSWORD: str = "sgir"
    MYSQL8_DB: str = "sgir_db_8"
    MYSQL8_HOST: str = "localhost"
    MYSQL8_PORT: int = 3308

    @property
    def MYSQL8_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL8_USER}:{self.MYSQL8_PASSWORD}@{self.MYSQL8_HOST}:{self.MYSQL8_PORT}/{self.MYSQL8_DB}"

    # Oracle 10g
    ORACLE10_USER: str = "sgir"
    ORACLE10_PASSWORD: str = "sgir"
    ORACLE10_DSN: str = "localhost:1521/ORCL10"

    @property
    def ORACLE10_DATABASE_URL(self) -> str:
        return f"oracle+oracledb://{self.ORACLE10_USER}:{self.ORACLE10_PASSWORD}@{self.ORACLE10_DSN}"

    # Oracle 11g
    ORACLE11_USER: str = "sgir"
    ORACLE11_PASSWORD: str = "sgir"
    ORACLE11_DSN: str = "localhost:1522/ORCL11"

    @property
    def ORACLE11_DATABASE_URL(self) -> str:
        return f"oracle+oracledb://{self.ORACLE11_USER}:{self.ORACLE11_PASSWORD}@{self.ORACLE11_DSN}"

    # Oracle 19c
    ORACLE19_USER: str = "monitor_user"
    ORACLE19_PASSWORD: str = "monitor_pass"
    ORACLE19_DSN: str = "localhost:1521/ORCLCDB"

    @property
    def ORACLE19_DATABASE_URL(self) -> str:
        return f"oracle+oracledb://{self.ORACLE19_USER}:{self.ORACLE19_PASSWORD}@{self.ORACLE19_DSN}"

    # MongoDB
    MONGODB_USER: str = "monitor_user"
    MONGODB_PASSWORD: str = "monitor_pass"
    MONGODB_AUTH_DB: str = "admin"
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017

    @property
    def MONGODB_URL(self) -> str:
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/?authSource={self.MONGODB_AUTH_DB}"

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # CHANGE THIS IN PRODUCTION
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_DAYS_REMEMBER: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        secrets_dir="/run/secrets",
        extra="ignore"
    )


settings = Settings()
