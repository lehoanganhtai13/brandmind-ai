#!/usr/bin/env python3
"""
Integration tests for SearXNG web search with rate limiting and deduplication.
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared', 'src'))

from shared.agent_tools.search_web import search_web

def test_searxng_vietnamese_queries():
    """Test SearXNG with Vietnamese food-related queries."""

    vietnamese_queries = [
        "cách làm phở bò",
        "vị của lạp xưởng tươi là gì",
        "gia vị trong phở",
        "món ăn từ thịt bò",
        "cách chế biến bún bò huế",
        "nguyên liệu làm bánh mì",
        "công dụng của rau muống",
        "giá trị dinh dưỡng của cà rốt",
        "các loại hải sản phổ biến",
    ]

    print("=" * 100)
    print("Testing SearXNG Web Search - VIETNAMESE QUERIES")
    print("=" * 100)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/searxng_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    vietnamese_success = 0
    vietnamese_start = time.time()

    result = search_web(vietnamese_queries, top_k=3)

    vietnamese_time = time.time() - vietnamese_start

    # Save detailed results
    detailed_results = []

    for query, data in result["queries"].items():
        print("\n" + "=" * 100)
        print(f"[SEARXNG TEST] Query: {query}")
        print(f"Engine: {data['engine_used']} | Results: {data['result_count']} | Time: {data['response_time']:.2f}s")
        print("=" * 100)

        query_result = {
            "query": query,
            "engine": data['engine_used'],
            "result_count": data['result_count'],
            "response_time": data['response_time'],
            "results": []
        }

        if data['result_count'] > 0:
            print(f"✓ Found {data['result_count']} results")

            # Simple relevance check - if title or snippet contains keywords from query
            is_relevant = any(
                any(word.lower() in (result.title + result.snippet).lower()
                    for word in query.replace("?", "").split()[:3])
                for result in data["results"][:2]
            )

            if is_relevant:
                vietnamese_success += 1
                print(f"✓ Results appear RELEVANT")
                query_result["relevance"] = "RELEVANT"
            else:
                print(f"⚠ Results appear LESS RELEVANT (might be valid edge case)")
                query_result["relevance"] = "LESS_RELEVANT"

            for i, search_result in enumerate(data["results"][:3], 1):
                print(f"\n  [{i}] {search_result.title}")
                print(f"      URL: {search_result.url}")
                print(f"      Snippet: {search_result.snippet[:100]}...")

                query_result["results"].append({
                    "title": search_result.title,
                    "url": search_result.url,
                    "snippet": search_result.snippet[:200]
                })
        else:
            print(f"✗ No results found")
            query_result["relevance"] = "NO_RESULTS"

        detailed_results.append(query_result)

    # Save results to file
    results_file = os.path.join(results_dir, f"vietnamese_queries_{timestamp}.txt")
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("SEARXNG VIETNAMESE QUERIES TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Queries: {len(vietnamese_queries)}\n")
        f.write(f"Relevant Results: {vietnamese_success}/{len(vietnamese_queries)} ({100*vietnamese_success/len(vietnamese_queries):.0f}%)\n")
        f.write(f"Total Time: {vietnamese_time:.2f}s\n")
        f.write(f"Average Time/Query: {vietnamese_time/len(vietnamese_queries):.2f}s\n\n")

        for query_result in detailed_results:
            f.write(f"QUERY: {query_result['query']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Engine: {query_result['engine']}\n")
            f.write(f"Results: {query_result['result_count']}\n")
            f.write(f"Response Time: {query_result['response_time']:.2f}s\n")
            f.write(f"Relevance: {query_result['relevance']}\n\n")

            for i, result in enumerate(query_result["results"], 1):
                f.write(f"  [{i}] {result['title']}\n")
                f.write(f"      URL: {result['url']}\n")
                f.write(f"      Snippet: {result['snippet']}\n\n")
            f.write("\n")

    print("\n" + "=" * 100)
    print(f"VIETNAMESE RESULTS:")
    print(f"  Relevant: {vietnamese_success}/{len(vietnamese_queries)} ({100*vietnamese_success/len(vietnamese_queries):.0f}%)")
    print(f"  Total time: {vietnamese_time:.2f}s")
    print(f"  Avg/query: {vietnamese_time/len(vietnamese_queries):.2f}s")
    print(f"  Results saved: {results_file}")
    print("=" * 100)

    return {
        "success_count": vietnamese_success,
        "total_queries": len(vietnamese_queries),
        "total_time": vietnamese_time,
        "results_file": results_file
    }

def test_searxng_english_queries():
    """Test SearXNG with English food-related queries."""

    english_queries = [
        "how to make Vietnamese pho",
        "what does fresh Chinese sausage taste like",
        "spices in pho",
        "beef dishes recipes",
        "how to cook bun bo hue",
        "bread making ingredients",
        "benefits of water spinach",
        "nutritional value of carrots",
        "common types of seafood",
    ]

    print("\n\n" + "=" * 100)
    print("Testing SearXNG Web Search - ENGLISH QUERIES")
    print("=" * 100)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/searxng_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    english_success = 0
    english_start = time.time()

    result = search_web(english_queries, top_k=3)

    english_time = time.time() - english_start

    # Save detailed results
    detailed_results = []

    for query, data in result["queries"].items():
        print("\n" + "=" * 100)
        print(f"[SEARXNG TEST] Query: {query}")
        print(f"Engine: {data['engine_used']} | Results: {data['result_count']} | Time: {data['response_time']:.2f}s")
        print("=" * 100)

        query_result = {
            "query": query,
            "engine": data['engine_used'],
            "result_count": data['result_count'],
            "response_time": data['response_time'],
            "results": []
        }

        if data['result_count'] > 0:
            print(f"✓ Found {data['result_count']} results")

            # Simple relevance check
            is_relevant = any(
                any(word.lower() in (result.title + result.snippet).lower()
                    for word in query.replace("?", "").split()[:3])
                for result in data["results"][:2]
            )

            if is_relevant:
                english_success += 1
                print(f"✓ Results appear RELEVANT")
                query_result["relevance"] = "RELEVANT"
            else:
                print(f"⚠ Results appear LESS RELEVANT (might be valid edge case)")
                query_result["relevance"] = "LESS_RELEVANT"

            for i, search_result in enumerate(data["results"][:3], 1):
                print(f"\n  [{i}] {search_result.title}")
                print(f"      URL: {search_result.url}")
                print(f"      Snippet: {search_result.snippet[:100]}...")

                query_result["results"].append({
                    "title": search_result.title,
                    "url": search_result.url,
                    "snippet": search_result.snippet[:200]
                })
        else:
            print(f"✗ No results found")
            query_result["relevance"] = "NO_RESULTS"

        detailed_results.append(query_result)

    # Save results to file
    results_file = os.path.join(results_dir, f"english_queries_{timestamp}.txt")
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("SEARXNG ENGLISH QUERIES TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Queries: {len(english_queries)}\n")
        f.write(f"Relevant Results: {english_success}/{len(english_queries)} ({100*english_success/len(english_queries):.0f}%)\n")
        f.write(f"Total Time: {english_time:.2f}s\n")
        f.write(f"Average Time/Query: {english_time/len(english_queries):.2f}s\n\n")

        for query_result in detailed_results:
            f.write(f"QUERY: {query_result['query']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Engine: {query_result['engine']}\n")
            f.write(f"Results: {query_result['result_count']}\n")
            f.write(f"Response Time: {query_result['response_time']:.2f}s\n")
            f.write(f"Relevance: {query_result['relevance']}\n\n")

            for i, result in enumerate(query_result["results"], 1):
                f.write(f"  [{i}] {result['title']}\n")
                f.write(f"      URL: {result['url']}\n")
                f.write(f"      Snippet: {result['snippet']}\n\n")
            f.write("\n")

    print("\n" + "=" * 100)
    print(f"ENGLISH RESULTS:")
    print(f"  Relevant: {english_success}/{len(english_queries)} ({100*english_success/len(english_queries):.0f}%)")
    print(f"  Total time: {english_time:.2f}s")
    print(f"  Avg/query: {english_time/len(english_queries):.2f}s")
    print(f"  Results saved: {results_file}")
    print("=" * 100)

    return {
        "success_count": english_success,
        "total_queries": len(english_queries),
        "total_time": english_time,
        "results_file": results_file
    }

def test_query_deduplication():
    """Test query deduplication functionality."""

    print("\n\n" + "=" * 100)
    print("Testing Query Deduplication")
    print("=" * 100)

    duplicate_queries = [
        "cách làm phở bò",
        "bánh mì Việt Nam",
        "cách làm phở bò",  # Duplicate
        "cách chế biến bún bò huế",
        "bánh mì Việt Nam",  # Duplicate
    ]

    print(f"\nInput: {len(duplicate_queries)} queries (with duplicates)")
    print(f"Queries: {duplicate_queries}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/searxng_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    dedup_start = time.time()
    result = search_web(duplicate_queries, top_k=2)
    dedup_time = time.time() - dedup_start

    unique_count = len(result["queries"])
    print(f"\n✓ After deduplication: {unique_count} unique queries executed")
    print(f"  Time saved: ~{(len(duplicate_queries) - unique_count) * 2:.1f}s (approx 2s per duplicate)")
    print(f"  Actual time: {dedup_time:.2f}s")

    # Save deduplication results
    dedup_file = os.path.join(results_dir, f"deduplication_test_{timestamp}.txt")
    with open(dedup_file, 'w', encoding='utf-8') as f:
        f.write("SEARXNG QUERY DEDUPLICATION TEST\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input Queries: {len(duplicate_queries)}\n")
        f.write(f"Unique Queries Executed: {unique_count}\n")
        f.write(f"Duplicates Removed: {len(duplicate_queries) - unique_count}\n")
        f.write(f"Execution Time: {dedup_time:.2f}s\n\n")

        f.write("INPUT QUERIES:\n")
        for i, query in enumerate(duplicate_queries, 1):
            f.write(f"  {i}. {query}\n")

        f.write("\nUNIQUE QUERIES EXECUTED:\n")
        for i, (query, data) in enumerate(result["queries"].items(), 1):
            f.write(f"  {i}. {query}: {data['result_count']} results via {data['engine_used']}\n")

    for query, data in result["queries"].items():
        print(f"\n  {query}: {data['result_count']} results via {data['engine_used']}")

    print(f"\n✓ Deduplication test results saved: {dedup_file}")

    return {
        "input_count": len(duplicate_queries),
        "unique_count": unique_count,
        "time_taken": dedup_time,
        "results_file": dedup_file
    }

def test_rate_limiting():
    """Test rate limiting behavior."""

    print("\n\n" + "=" * 100)
    print("Testing Rate Limiting (2s delay per engine)")
    print("=" * 100)

    # Multiple queries that will hit the same engines
    test_queries = [
        "Python programming",
        "JavaScript frameworks",
        "Docker containers",
    ]

    print(f"\nExecuting {len(test_queries)} sequential queries...")
    print("Expected: 2s delay between requests to same engine")
    print("(Actual time may be lower due to parallel workers)")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/searxng_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    start = time.time()
    result = search_web(test_queries, top_k=2)
    elapsed = time.time() - start

    print(f"\n✓ Completed in {elapsed:.2f}s")
    print(f"  Total queries: {result['total_queries']}")
    print(f"  Total time: {result['total_execution_time']:.2f}s")
    print(f"  Avg/query: {result['average_time_per_query']:.2f}s")

    # Save rate limiting results
    rate_limit_file = os.path.join(results_dir, f"rate_limiting_test_{timestamp}.txt")
    with open(rate_limit_file, 'w', encoding='utf-8') as f:
        f.write("SEARXNG RATE LIMITING TEST\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Queries: {result['total_queries']}\n")
        f.write(f"Total Execution Time: {result['total_execution_time']:.2f}s\n")
        f.write(f"Average Time per Query: {result['average_time_per_query']:.2f}s\n")
        f.write(f"Wall Clock Time: {elapsed:.2f}s\n\n")

        f.write("PER-QUERY BREAKDOWN:\n")
        for query, data in result["queries"].items():
            f.write(f"  {query}: {data['response_time']:.2f}s via {data['engine_used']}\n")

    # Show per-engine breakdown
    for query, data in result["queries"].items():
        print(f"  {query}: {data['response_time']:.2f}s via {data['engine_used']}")

    print(f"\n✓ Rate limiting test results saved: {rate_limit_file}")

    return {
        "total_queries": result['total_queries'],
        "execution_time": result['total_execution_time'],
        "wall_clock_time": elapsed,
        "results_file": rate_limit_file
    }

def run_comprehensive_test():
    """Run all SearXNG tests and create summary report."""

    print("🚀 COMPREHENSIVE SEARXNG WEB SEARCH TEST")
    print("=" * 60)
    print("Running all test categories...")
    print("This may take several minutes...\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/searxng_comprehensive_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    # Run all tests
    vietnamese_results = test_searxng_vietnamese_queries()
    english_results = test_searxng_english_queries()
    dedup_results = test_query_deduplication()
    rate_limit_results = test_rate_limiting()

    # Create comprehensive summary
    summary_file = os.path.join(results_dir, f"comprehensive_summary_{timestamp}.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("SEARXNG COMPREHENSIVE TEST SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Categories: 4 (Vietnamese, English, Deduplication, Rate Limiting)\n\n")

        f.write("RESULTS OVERVIEW:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Vietnamese Queries: {vietnamese_results['success_count']}/{vietnamese_results['total_queries']} relevant ({100*vietnamese_results['success_count']/vietnamese_results['total_queries']:.0f}%)\n")
        f.write(f"English Queries: {english_results['success_count']}/{english_results['total_queries']} relevant ({100*english_results['success_count']/english_results['total_queries']:.0f}%)\n")
        f.write(f"Deduplication: {dedup_results['input_count']} → {dedup_results['unique_count']} queries\n")
        f.write(f"Rate Limiting: {rate_limit_results['total_queries']} queries in {rate_limit_results['execution_time']:.2f}s\n\n")

        f.write("PERFORMANCE METRICS:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Vietnamese avg time/query: {vietnamese_results['total_time']/vietnamese_results['total_queries']:.2f}s\n")
        f.write(f"English avg time/query: {english_results['total_time']/english_results['total_queries']:.2f}s\n")
        f.write(f"Rate limiting avg time/query: {rate_limit_results['execution_time']/rate_limit_results['total_queries']:.2f}s\n")
        f.write(f"Deduplication time saved: ~{(dedup_results['input_count'] - dedup_results['unique_count']) * 2:.1f}s\n\n")

        f.write("DETAILED RESULT FILES:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Vietnamese: {vietnamese_results['results_file']}\n")
        f.write(f"English: {english_results['results_file']}\n")
        f.write(f"Deduplication: {dedup_results['results_file']}\n")
        f.write(f"Rate Limiting: {rate_limit_results['results_file']}\n")

    print("\n\n" + "=" * 100)
    print("COMPREHENSIVE TEST COMPLETED")
    print("=" * 100)
    print(f"📊 Summary report: {summary_file}")
    print(f"📁 All results in: {results_dir}")
    print("=" * 100)

    return summary_file

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test SearXNG web search functionality")
    parser.add_argument(
        "--test",
        choices=["all", "vietnamese", "english", "dedup", "ratelimit", "comprehensive"],
        default="comprehensive",
        help="Test category to run"
    )

    args = parser.parse_args()

    if args.test == "vietnamese":
        test_searxng_vietnamese_queries()
    elif args.test == "english":
        test_searxng_english_queries()
    elif args.test == "dedup":
        test_query_deduplication()
    elif args.test == "ratelimit":
        test_rate_limiting()
    elif args.test == "comprehensive":
        run_comprehensive_test()
    elif args.test == "all":
        # Run individual tests without comprehensive summary
        test_searxng_vietnamese_queries()
        test_searxng_english_queries()
        test_query_deduplication()
        test_rate_limiting()