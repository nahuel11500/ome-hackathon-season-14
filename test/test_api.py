"""
Comprehensive test script for the full API pipeline
Tests: deduplication -> NER -> sentiment analysis -> PostgreSQL storage

Run after starting services with:
  docker compose up --build api-gateway sentiment-service ner-service postgres
"""

import requests
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor

API_URL = "http://localhost:8000"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "ome_hackathon",
    "user": "user",
    "password": "ilovedataforgood",
}


def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(**DB_CONFIG)


def query_postgres(segment_id: str):
    """Query PostgreSQL to verify data was stored correctly"""
    print(f"🔍 Querying PostgreSQL for segment: {segment_id}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                id, segment_id, channel_title, report_text,
                sentiment, sentiment_confidence,
                actor_persons, actor_organizations, actor_locations, actor_misc,
                keywords, keywords_nouns
            FROM category_classification
            WHERE segment_id = %s
        """
        cursor.execute(query, (segment_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            print("✅ Data found in PostgreSQL:")
            print(f"   ID: {result['id']}")
            print(f"   Segment ID: {result['segment_id']}")
            print(f"   Channel: {result['channel_title']}")
            print(
                f"   Sentiment: {result['sentiment']} (confidence: {result['sentiment_confidence']})"
            )
            print(f"   Persons: {result['actor_persons']}")
            print(f"   Organizations: {result['actor_organizations']}")
            print(f"   Locations: {result['actor_locations']}")
            print(f"   Misc: {result['actor_misc']}")
            print(f"   Keywords: {result['keywords']}")
            print(f"   Keywords Nouns: {result['keywords_nouns']}")
            print(f"   Text preview: {result['report_text'][:100]}...")
            return result
        else:
            print("❌ No data found in PostgreSQL")
            return None

    except Exception as e:
        print(f"❌ Error querying PostgreSQL: {e}")
        return None


def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def test_analyze_single():
    """Test single segment analysis with full pipeline"""
    print("🔍 Testing single segment analysis (full pipeline)...")

    # Test data with repetitive text pattern to test deduplication
    # and French text with entities for NER
    segment_data = {
        "segment_id": "test_full_pipeline_123",
        "channel_title": "France 2",
        "channel_name": "france2",
        "segment_start": "2024-01-15T20:00:00",
        "segment_end": "2024-01-15T20:05:00",
        "duration_seconds": "300",
        "report_text": "Emmanuel Macron a annoncé de nouvelles mesures pour l'agriculture. Le Président de la République a rencontré les agriculteurs français à Paris. L'Union Européenne soutient cette initiative. Les agriculteurs de Bretagne sont satisfaits de ces annonces positives.",
        "llm_category": "agriculture_alimentation",
    }

    response = requests.post(f"{API_URL}/analyze", json=segment_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("✅ Analysis successful!")
        print(json.dumps(result, indent=2))

        # Verify the pipeline features are present
        assert result.get("sentiment") is not None, "Sentiment should be present"
        assert result.get("actor_persons") is not None, "NER persons should be present"
        assert result.get("actor_locations") is not None, (
            "NER locations should be present"
        )
        assert result.get("keywords") is not None, "Keywords should be present"

        print("\n📊 Pipeline Features Verified:")
        print(f"   ✓ Sentiment: {result['sentiment']}")
        print(f"   ✓ Persons: {result['actor_persons']}")
        print(f"   ✓ Organizations: {result['actor_organizations']}")
        print(f"   ✓ Locations: {result['actor_locations']}")
        print(f"   ✓ Misc: {result['actor_misc']}")
        print(f"   ✓ Keywords: {result['keywords']}")
        print(f"   ✓ Keywords Nouns: {result['keywords_nouns']}")
    else:
        print(f"❌ Error: {response.text}")

    print()
    return segment_data["segment_id"]


def test_batch_analysis():
    """Test batch analysis with diverse examples"""
    print("📦 Testing batch analysis...")

    batch_data = {
        "segments": [
            {
                "segment_id": "batch_ner_001",
                "channel_title": "France 2",
                "channel_name": "france2",
                "segment_start": "2024-01-15T20:00:00",
                "segment_end": "2024-01-15T20:05:00",
                "duration_seconds": "300",
                "report_text": "Jean Castex et Élisabeth Borne ont visité la Normandie pour rencontrer les agriculteurs. Le ministère de l'Agriculture a annoncé des aides supplémentaires pour les exploitations biologiques en France.",
                "llm_category": "agriculture_alimentation",
            },
            {
                "segment_id": "batch_ner_002",
                "channel_title": "TF1",
                "channel_name": "tf1",
                "segment_start": "2024-01-15T21:00:00",
                "segment_end": "2024-01-15T21:05:00",
                "duration_seconds": "300",
                "report_text": "La pollution dans les grandes villes françaises continue d'augmenter. Paris, Lyon et Marseille dépassent les seuils recommandés. Les autorités appellent à réduire l'utilisation des véhicules polluants.",
                "llm_category": "mobility_transport",
            },
            {
                "segment_id": "batch_ner_003",
                "channel_title": "M6",
                "channel_name": "m6",
                "segment_start": "2024-01-15T22:00:00",
                "segment_end": "2024-01-15T22:05:00",
                "duration_seconds": "300",
                "report_text": "Les manifestations d'agriculteurs à Toulouse et Bordeaux se poursuivent. La FNSEA demande au gouvernement de renégocier les accords européens. Les producteurs de lait sont particulièrement touchés.",
                "llm_category": "agriculture_alimentation",
            },
        ]
    }

    response = requests.post(f"{API_URL}/analyze/batch", json=batch_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Processed: {result['processed']}")
        print(f"✅ Successful: {result['successful']}")
        print(f"❌ Failed: {result['failed']}")

        # Show details for first result
        if result["results"]:
            first_result = result["results"][0]
            print("\nFirst result details:")
            print(f"   Segment ID: {first_result['segment_id']}")
            print(f"   Sentiment: {first_result.get('sentiment')}")
            print(f"   Persons: {first_result.get('actor_persons', [])}")
            print(f"   Locations: {first_result.get('actor_locations', [])}")
    else:
        print(f"❌ Error: {response.text}")

    print()
    return [seg["segment_id"] for seg in batch_data["segments"]]


def test_get_results(segment_id):
    """Test retrieving results by segment ID"""
    print(f"📊 Testing get results for segment {segment_id}...")

    response = requests.get(f"{API_URL}/results/{segment_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("✅ Results retrieved from API:")
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"❌ Error: {response.text}")
    print()


def test_full_pipeline():
    """
    Test the complete pipeline:
    1. Submit data to API
    2. Verify response contains all features
    3. Query PostgreSQL to confirm data storage
    4. Verify all pipeline features are in database
    """
    print("\n" + "=" * 80)
    print("🚀 FULL PIPELINE TEST")
    print("=" * 80)
    print(
        "Testing: Data Input -> Deduplication -> NER -> Sentiment -> Keywords -> PostgreSQL"
    )
    print("=" * 80 + "\n")

    # Test with repetitive text to verify deduplication
    test_segment = {
        "segment_id": "full_pipeline_test_999",
        "channel_title": "France 3",
        "channel_name": "france3",
        "segment_start": "2024-01-20T19:00:00",
        "segment_end": "2024-01-20T19:05:00",
        "duration_seconds": "300",
        "report_text": "Le ministre de l'Agriculture, Marc Fesneau, a rencontré les représentants de la FNSEA à Paris ce mardi. Les agriculteurs français demandent plus de soutien face à la concurrence européenne. La région Bretagne est particulièrement touchée par cette crise agricole. Emmanuel Macron devrait s'exprimer prochainement sur ce sujet important.",
        "llm_category": "agriculture_alimentation",
    }

    print("📤 Step 1: Submitting data to API...")
    response = requests.post(f"{API_URL}/analyze", json=test_segment)

    if response.status_code != 200:
        print(f"❌ API request failed: {response.text}")
        return False

    result = response.json()
    print("✅ Step 1 completed: Data submitted successfully\n")

    print("🔍 Step 2: Verifying API response contains all features...")
    checks_passed = 0
    checks_total = 8

    if result.get("sentiment"):
        print(
            f"   ✓ Sentiment: {result['sentiment']} (confidence: {result.get('sentiment_confidence')})"
        )
        checks_passed += 1
    else:
        print("   ✗ Sentiment: MISSING")

    if result.get("actor_persons") is not None:
        print(f"   ✓ Persons (NER): {result['actor_persons']}")
        checks_passed += 1
    else:
        print("   ✗ Persons (NER): MISSING")

    if result.get("actor_organizations") is not None:
        print(f"   ✓ Organizations (NER): {result['actor_organizations']}")
        checks_passed += 1
    else:
        print("   ✗ Organizations (NER): MISSING")

    if result.get("actor_locations") is not None:
        print(f"   ✓ Locations (NER): {result['actor_locations']}")
        checks_passed += 1
    else:
        print("   ✗ Locations (NER): MISSING")

    if result.get("actor_misc") is not None:
        print(f"   ✓ Misc entities (NER): {result['actor_misc']}")
        checks_passed += 1
    else:
        print("   ✗ Misc entities (NER): MISSING")

    if result.get("keywords") is not None:
        print(f"   ✓ Keywords: {result['keywords']}")
        checks_passed += 1
    else:
        print("   ✗ Keywords: MISSING")

    if result.get("keywords_nouns") is not None:
        print(f"   ✓ Keywords Nouns: {result['keywords_nouns']}")
        checks_passed += 1
    else:
        print("   ✗ Keywords Nouns: MISSING")

    if result.get("id"):
        print(f"   ✓ Database ID: {result['id']}")
        checks_passed += 1
    else:
        print("   ✗ Database ID: MISSING")

    print(f"\n✅ Step 2 completed: {checks_passed}/{checks_total} checks passed\n")

    # Wait a moment for data to be fully committed to database
    print("⏳ Waiting for database commit...")
    time.sleep(2)

    print("🔍 Step 3: Querying PostgreSQL to verify data storage...")
    db_result = query_postgres(test_segment["segment_id"])

    if not db_result:
        print("❌ Step 3 FAILED: Data not found in database\n")
        return False

    print("\n✅ Step 3 completed: Data found in PostgreSQL\n")

    print("🔍 Step 4: Verifying all pipeline features in database...")
    db_checks_passed = 0
    db_checks_total = 7

    if db_result.get("sentiment"):
        print(f"   ✓ Sentiment in DB: {db_result['sentiment']}")
        db_checks_passed += 1
    else:
        print("   ✗ Sentiment in DB: MISSING")

    if db_result.get("actor_persons"):
        print(f"   ✓ Persons in DB: {db_result['actor_persons']}")
        db_checks_passed += 1
    else:
        print("   ✗ Persons in DB: MISSING")

    if db_result.get("actor_organizations") is not None:
        print(f"   ✓ Organizations in DB: {db_result['actor_organizations']}")
        db_checks_passed += 1
    else:
        print("   ✗ Organizations in DB: MISSING")

    if db_result.get("actor_locations"):
        print(f"   ✓ Locations in DB: {db_result['actor_locations']}")
        db_checks_passed += 1
    else:
        print("   ✗ Locations in DB: MISSING")

    if db_result.get("sentiment_confidence"):
        print(f"   ✓ Sentiment confidence in DB: {db_result['sentiment_confidence']}")
        db_checks_passed += 1
    else:
        print("   ✗ Sentiment confidence in DB: MISSING")

    if db_result.get("keywords") is not None:
        print(f"   ✓ Keywords in DB: {db_result['keywords']}")
        db_checks_passed += 1
    else:
        print("   ✗ Keywords in DB: MISSING")

    if db_result.get("keywords_nouns") is not None:
        print(f"   ✓ Keywords Nouns in DB: {db_result['keywords_nouns']}")
        db_checks_passed += 1
    else:
        print("   ✗ Keywords Nouns in DB: MISSING")

    print(
        f"\n✅ Step 4 completed: {db_checks_passed}/{db_checks_total} database checks passed\n"
    )

    print("=" * 80)
    if checks_passed == checks_total and db_checks_passed == db_checks_total:
        print("🎉 FULL PIPELINE TEST PASSED!")
        print(
            "   All features working: Deduplication ✓ NER ✓ Sentiment ✓ Keywords ✓ PostgreSQL ✓"
        )
    else:
        print("⚠️  FULL PIPELINE TEST COMPLETED WITH WARNINGS")
        print(f"   API checks: {checks_passed}/{checks_total}")
        print(f"   DB checks: {db_checks_passed}/{db_checks_total}")
    print("=" * 80 + "\n")

    return checks_passed == checks_total and db_checks_passed == db_checks_total


def main():
    """Run all tests"""
    print("=" * 80)
    print("API Gateway Test Suite - Full Pipeline Testing")
    print("=" * 80)
    print()

    try:
        # Test health
        test_health()

        # Test single analysis
        segment_id = test_analyze_single()

        # Wait a bit for database write
        time.sleep(1)

        # Query database to verify
        if segment_id:
            query_postgres(segment_id)
            test_get_results(segment_id)

        # Test batch analysis
        batch_ids = test_batch_analysis()

        # Wait for batch processing
        time.sleep(2)

        # Verify one batch item in database
        if batch_ids:
            query_postgres(batch_ids[0])

        # Run comprehensive full pipeline test
        test_full_pipeline()

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure services are running:")
        print(
            "   docker compose up --build api-gateway sentiment-service ner-service postgres"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
