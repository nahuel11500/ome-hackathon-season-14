# Sentiment Analysis Module

This module performs sentiment analysis on the agriculture/alimentation dataset.

## Usage

### Basic Usage

```python
# Run the sentiment analysis script
python sentiment/sentiment_analysis.py
```

### Using the Data Loader

```python
from main.main import get_agriculture_data

# Get agriculture data (automatically uses cache if available)
df = get_agriculture_data()

# Perform your own analysis
print(f"Total records: {len(df)}")
```

### Full Dataset Analysis

To run sentiment analysis on the full agriculture/alimentation dataset (2,565 records), edit `sentiment_analysis.py` and comment out or remove this line:

```python
df_filtered = df_filtered.head(10)  # Remove this line for full dataset
```

## How It Works

1. **Data Loading**: Uses the centralized `main.main` module to load data
2. **Caching**: Data is automatically cached in `data/train_cached.parquet` to avoid repeated downloads
3. **Filtering**: Filters for `agriculture_alimentation` category
4. **Sentiment Analysis**: Uses `pysentimiento` to analyze text sentiment
5. **Output**: Saves results to `dataset/train_agriculture_with_sentiment.parquet` and CSV

## Sentiment Labels

- `neu` - Neutral sentiment
- `pos` - Positive sentiment
- `neg` - Negative sentiment

## Output Files

- `dataset/train_agriculture_with_sentiment.parquet` - Parquet format (efficient)
- `dataset/train_agriculture_with_sentiment.csv` - CSV format (human-readable)

## Dependencies

- pandas
- pysentimiento
- transformers
- torch
