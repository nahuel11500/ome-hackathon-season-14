"""
Process all training data through the API pipeline and export results to CSV
"""

import sys
from pathlib import Path
import pandas as pd
import requests
import time
from tqdm import tqdm
import psycopg2

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
API_URL = "http://localhost:8000"
TRAIN_DATA_PATH = Path(__file__).parent / "data" / "train_cached.parquet"
OUTPUT_CSV_PATH = Path(__file__).parent / "data" / "processed_results.csv"

# Database configuration
DB_CONFIG = {
    "user": "user",
    "password": "ilovedataforgood",
    "host": "localhost",
    "port": 5432,
    "database": "ome_hackathon",
}


def load_training_data():
    """Load the cached training data"""
    print(f"Loading training data from {TRAIN_DATA_PATH}...")
    if not TRAIN_DATA_PATH.exists():
        print(f"❌ Error: {TRAIN_DATA_PATH} not found!")
        sys.exit(1)

    df = pd.read_parquet(TRAIN_DATA_PATH)
    print(f"✅ Loaded {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    return df


def prepare_batch_data(df, batch_size=50):
    """Prepare data in batches for API submission"""

    batches = []
    total_rows = len(df)

    for i in range(0, total_rows, batch_size):
        batch_df = df.iloc[i : i + batch_size]
        segments = []

        for idx, row in batch_df.iterrows():
            # Map category -> llm_category
            category = row.get("category", row.get("llm_category", "other"))

            # Parse and format dates properly
            try:
                start_dt = pd.to_datetime(
                    row.get("segment_start", "2024-01-01T00:00:00")
                )
                segment_start = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                segment_start = "2024-01-01T00:00:00"

            try:
                end_dt = pd.to_datetime(row.get("segment_end", "2024-01-01T00:05:00"))
                segment_end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                segment_end = "2024-01-01T00:05:00"

            segment = {
                "segment_id": str(row.get("segment_id", f"train_{idx}")),
                "channel_title": str(row.get("channel_title", "Unknown")),
                "channel_name": str(row.get("channel_name", "unknown")),
                "segment_start": segment_start,
                "segment_end": segment_end,
                "duration_seconds": str(row.get("duration_seconds", "300")),
                "report_text": str(row.get("report_text", "")),
                "llm_category": str(category),
            }
            segments.append(segment)

        batches.append(segments)

    return batches


def process_batches(batches):
    """Send all batches to the API for processing"""
    print(f"\n📤 Processing {len(batches)} batches through API pipeline...")

    successful = 0
    failed = 0

    for i, batch in enumerate(tqdm(batches, desc="Processing batches")):
        try:
            response = requests.post(
                f"{API_URL}/analyze/batch", json={"segments": batch}, timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                successful += result.get("successful", 0)
                failed += result.get("failed", 0)
            else:
                print(f"\n❌ Batch {i + 1} failed with status {response.status_code}")
                failed += len(batch)

            # Small delay to avoid overwhelming the services
            time.sleep(0.5)

        except Exception as e:
            print(f"\n❌ Error processing batch {i + 1}: {e}")
            failed += len(batch)

    print("\n✅ Processing complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")

    return successful, failed


def export_results_to_csv():
    """Export all results from PostgreSQL to CSV"""
    print("\n💾 Exporting results from database to CSV...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)

        # Query all data from category_classification table
        query = """
            SELECT 
                id,
                segment_id,
                channel_title,
                channel_name,
                segment_start,
                segment_end,
                duration_seconds,
                report_text,
                llm_category,
                predicted_category,
                sentiment,
                sentiment_confidence,
                actor_persons,
                actor_organizations,
                actor_locations,
                actor_misc,
                keywords,
                keywords_nouns
            FROM category_classification
            ORDER BY segment_start
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        # Save to CSV
        df.to_csv(OUTPUT_CSV_PATH, index=False)
        print(f"✅ Exported {len(df)} records to {OUTPUT_CSV_PATH}")

        # Display summary statistics
        print("\n📊 Summary Statistics:")
        print(f"   Total records: {len(df)}")
        print(
            f"   Date range: {df['segment_start'].min()} to {df['segment_start'].max()}"
        )

        if "sentiment" in df.columns:
            sentiment_counts = df["sentiment"].value_counts()
            print("\n   Sentiment distribution:")
            for sentiment, count in sentiment_counts.items():
                print(f"      {sentiment}: {count} ({count / len(df) * 100:.1f}%)")

        if "llm_category" in df.columns:
            print("\n   Top 5 categories:")
            category_counts = df["llm_category"].value_counts().head()
            for category, count in category_counts.items():
                print(f"      {category}: {count}")

        # Count total entities extracted
        total_persons = (
            df["actor_persons"]
            .apply(lambda x: len(x) if isinstance(x, list) else 0)
            .sum()
        )
        total_orgs = (
            df["actor_organizations"]
            .apply(lambda x: len(x) if isinstance(x, list) else 0)
            .sum()
        )
        total_locations = (
            df["actor_locations"]
            .apply(lambda x: len(x) if isinstance(x, list) else 0)
            .sum()
        )
        total_keywords = (
            df["keywords"].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
        )

        print("\n   Total entities extracted:")
        print(f"      Persons: {total_persons}")
        print(f"      Organizations: {total_orgs}")
        print(f"      Locations: {total_locations}")
        print(f"      Keywords: {total_keywords}")

        return df

    except Exception as e:
        print(f"❌ Error exporting results: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Main execution function"""
    print("=" * 80)
    print("PROCESSING TRAINING DATA THROUGH PIPELINE")
    print("=" * 80)

    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API Gateway is {health['status']}")
            print(f"   Database: {health['database']}")
            for service in health["services"]:
                print(f"   {service['name']}: {service['status']}")
        else:
            print(f"❌ API Gateway returned status {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API Gateway: {e}")
        print("Make sure services are running with: docker compose up")
        sys.exit(1)

    # Load training data
    df_train = load_training_data()

    # Ask user how many records to process
    print(f"\n⚠️  Dataset contains {len(df_train)} records.")
    print("   Processing all records may take 2-3 hours.")
    print("\n   Options:")
    print(f"   1. Process ALL {len(df_train)} records")
    print("   2. Process first 100 records (test run)")
    print("   3. Process first 500 records")
    print("   4. Process first 1000 records")
    print("   5. Custom number")

    choice = input("\n   Choose option (1-5): ").strip()

    if choice == "1":
        df_to_process = df_train
    elif choice == "2":
        df_to_process = df_train.head(100)
    elif choice == "3":
        df_to_process = df_train.head(500)
    elif choice == "4":
        df_to_process = df_train.head(1000)
    elif choice == "5":
        try:
            n = int(input("   Enter number of records: ").strip())
            df_to_process = df_train.head(n)
        except (ValueError, TypeError):
            print("Invalid input. Using first 100 records.")
            df_to_process = df_train.head(100)
    else:
        print("Invalid choice. Exiting.")
        sys.exit(0)

    print(f"\n📝 Will process {len(df_to_process)} records")

    # Prepare batches
    batch_size = 50  # Process 50 records at a time
    batches = prepare_batch_data(df_to_process, batch_size=batch_size)
    print(f"📦 Prepared {len(batches)} batches (batch size: {batch_size})")

    # Process through API
    print(f"\n⏱️  Estimated time: {len(df_to_process) * 2 / 60:.1f} minutes")
    input("\nPress Enter to start processing...")

    start_time = time.time()
    successful, failed = process_batches(batches)
    elapsed_time = time.time() - start_time

    print(
        f"\n⏱️  Processing took {elapsed_time:.1f} seconds ({elapsed_time / 60:.1f} minutes)"
    )
    print(f"   Average: {elapsed_time / len(df_to_process):.2f} seconds per record")

    # Export results
    df_results = export_results_to_csv()

    if df_results is not None:
        print(f"\n🎉 Complete! Results saved to: {OUTPUT_CSV_PATH}")
    else:
        print("\n⚠️  Processing completed but export failed.")


if __name__ == "__main__":
    main()
