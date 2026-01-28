import hashlib
from datetime import datetime

import numpy as np
import pandas as pd
from api.database.database_connection import connect_to_db
from api.database.logs import get_logger
from sqlalchemy import (
    Column,
    DateTime,
    Double,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, insert as pg_insert
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta

logger = get_logger()

Base = declarative_base()


class CategoryClassifications(Base):
    __tablename__ = "category_classification"

    id = Column(Text, primary_key=True)
    segment_id = Column(Text)
    channel_title = Column(String, nullable=False)
    channel_name = Column(Text, nullable=False)
    segment_start = Column(DateTime(), default=datetime.now)
    segment_end = Column(DateTime(), default=datetime.now)
    duration_seconds = Column(Text)
    report_text = Column(Text)
    llm_category = Column(Text)
    predicted_category = Column(Text)
    agricultural_category = Column(
        Text
    )  # Agricultural discourse classification (productiviste/alternatif/neutre/autre)
    sentiment = Column(Text)  # New: sentiment label (positive/negative/neutral)
    sentiment_confidence = Column(Double)  # New: confidence score for sentiment
    # NER fields
    actor_persons = Column(ARRAY(Text))  # List of persons extracted by NER
    actor_organizations = Column(ARRAY(Text))  # List of organizations extracted by NER
    actor_locations = Column(ARRAY(Text))  # List of locations extracted by NER
    actor_misc = Column(ARRAY(Text))  # List of misc entities extracted by NER
    # Keywords fields
    keywords_filtered = Column(
        ARRAY(Text)
    )  # List of filtered keywords extracted from text
    keywords_nouns = Column(ARRAY(Text))  # List of nouns found in keywords


class ClassificationMetrics(Base):
    __tablename__ = "classification_metrics"

    run_id = Column(Text, primary_key=True)
    model_name = Column(String, nullable=False)
    mobility_transport_precision = Column(Double, nullable=True)
    agriculture_alimentation_precision = Column(Text, nullable=True)
    energy_precision = Column(Double, nullable=True)
    other_precision = Column(Double, nullable=True)
    macro_precision = Column(Double, nullable=True)
    weighted_precision = Column(Double, nullable=True)

    mobility_transport_recall = Column(Double, nullable=True)
    agriculture_alimentation_recall = Column(Text, nullable=True)
    energy_recall = Column(Double, nullable=True)
    other_recall = Column(Double, nullable=True)
    macro_recall = Column(Double, nullable=True)
    weighted_recall = Column(Double, nullable=True)

    mobility_transport_f1 = Column(Double, nullable=True)
    agriculture_alimentation_f1 = Column(Text, nullable=True)
    energy_f1 = Column(Double, nullable=True)
    other_f1 = Column(Double, nullable=True)
    macro_f1 = Column(Double, nullable=True)
    weighted_f1 = Column(Double, nullable=True)


def create_tables(conn=None):
    """Create tables in the PostgreSQL database"""
    logger.info("Create tables")
    try:
        if conn is None:
            engine = connect_to_db()
        else:
            engine = conn

        Base.metadata.create_all(engine, checkfirst=True)

    except Exception as error:
        logger.error(error)
    finally:
        if engine is not None:
            engine.dispose()


def upsert_data_optimized(
    session: Session, df: pd.DataFrame, table_class: DeclarativeMeta, primary_key: str
):
    """
    Optimized upsert for large DataFrames using pandas and SQLAlchemy.

    Args:
        session: SQLAlchemy session
        df (pd.DataFrame): DataFrame containing data to upsert
        table_class: SQLAlchemy table class

    Returns:
        int: Number of records processed
    """
    try:
        # convert nan to None
        # Convert to dict and remove SQLAlchemy internal attributes if present
        data_list = df.replace({np.nan: None}).to_dict("records")
        for record in data_list:
            record.pop("_sa_instance_state", None)
            record.pop("_sa_registry", None)

        # Use PostgreSQL ON CONFLICT
        stmt = pg_insert(table_class)
        stmt = stmt.values(data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=[primary_key], set_=dict(stmt.excluded)
        )
        session.execute(stmt)
        session.commit()
        return len(data_list)

    except Exception as e:
        session.rollback()
        with open("errors.log", "w") as f:
            f.write(f"Error during upsert: {e}")
        raise


def get_consistent_hash(seed_string):
    obj_str = str(seed_string)
    sha256 = hashlib.sha256()
    sha256.update(obj_str.encode("utf-8"))
    hash_value = sha256.hexdigest()
    return hash_value


def create_hash_id(
    df: pd.DataFrame, column_name: str, id_column: str = "id", position: int = 0
):
    """
    Create a hash ID column by combining specified columns and applying a consistent hash function.

    This function generates a new hash column by concatenating the values of the specified
    ID column and channel_name column, then applying a consistent hash
    function to the concatenated string.

    Args:
        df (pd.DataFrame): Input DataFrame containing the data to process
        column_name (str): Name of the new hash column to be created
        id_column (str, optional): Name of the ID column to include in hash calculation.
            Defaults to "id".
        position (int, optional): The position of the new column in the dataframe.

    Returns:
        pd.DataFrame: DataFrame with the new hash column inserted at the beginning (index 0)

    Example:
        >>> df = pd.DataFrame({
        ...     'id': [1, 2, 3],
        ...     'channel_name': ["m6", "france3idf", "france2"],
        ... })
        >>> result_df = create_hash_id(df, 'hash_id')
        >>> print(result_df)
           hash_id      id  channel_name
        0  hash_value1   1          m6
        1  hash_value2   2  france3idf
        2  hash_value3   3     france2

    Note:
        - The function modifies the DataFrame in-place by inserting the new column at index 0
        - The hash is generated by concatenating id_columna and channel_name
        - Assumes 'channel_name' column exists in the DataFrame
    """
    df.insert(
        position,
        column_name,
        (df[id_column].astype(str) + df.channel_name.astype(str)).apply(
            get_consistent_hash
        ),
    )
    return df
