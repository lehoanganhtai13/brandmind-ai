#!/usr/bin/env python3
"""
Integration tests for Crawl4AI SDK client with Docker service.
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared', 'src'))

from shared.agent_tools.crawler.crawl4ai_client import create_crawl4ai_client, Crawl4AIPresets

def test_crawl4ai_client():
    """Test all modes of the Crawl4AI SDK client."""

    client = create_crawl4ai_client()
    print("✅ SDK Client created successfully")

    # Test URLs
    test_urls = [
        {
            "name": "github_claude_code",
            "url": "https://github.com/anthropics/claude-code",
            "query": "What is Claude Code and its main features?"
        },
        {
            "name": "thinkwithgoogle_trends",
            "url": "https://www.thinkwithgoogle.com/intl/en-emea/consumer-insights/consumer-trends/digital-marketing-trends-2025/",
            "query": "What are the AI agents marketing automation trends for 2025?"
        }
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/crawl4ai_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    all_results = {}

    for url_info in test_urls:
        print(f"\n{'='*60}")
        print(f"TESTING: {url_info['name'].upper()}")
        print(f"URL: {url_info['url']}")
        print('='*60)

        url_results = {}

        # 1. Test clean content extraction
        print(f"\n🔄 Testing clean content extraction...")
        try:
            result = client.fetch_clean_content(url_info["url"], Crawl4AIPresets.balanced())
            content_length = len(result.content)
            print(f"   ✅ {content_length:,} characters")

            # Save to file
            filename = f"{url_info['name']}_clean_content_{timestamp}.txt"
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"METHOD: clean_content\n")
                f.write(f"URL: {url_info['url']}\n")
                f.write(f"CONFIG: balanced preset\n")
                f.write(f"CONTENT LENGTH: {content_length} characters\n")
                f.write("=" * 80 + "\n")
                f.write(result.content)

            url_results["clean_content"] = {
                "length": content_length,
                "status": "SUCCESS",
                "filename": filename
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            url_results["clean_content"] = {"status": "ERROR", "error": str(e)}

        # 2. Test content summary
        print(f"\n🔄 Testing content summary...")
        try:
            result = client.fetch_content_summary(url_info["url"])
            content_length = len(result.content)
            print(f"   ✅ {content_length:,} characters")

            # Save to file
            filename = f"{url_info['name']}_content_summary_{timestamp}.txt"
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"METHOD: content_summary\n")
                f.write(f"URL: {url_info['url']}\n")
                f.write(f"PROVIDER: gemini/gemini-2.5-flash\n")
                f.write(f"CONTENT LENGTH: {content_length} characters\n")
                f.write("=" * 80 + "\n")
                f.write(result.content)

            url_results["content_summary"] = {
                "length": content_length,
                "status": "SUCCESS",
                "filename": filename
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            url_results["content_summary"] = {"status": "ERROR", "error": str(e)}

        # 3. Test relevant content filtering
        print(f"\n🔄 Testing relevant content filtering...")
        try:
            result = client.fetch_relevant_content(url_info["url"], url_info["query"])
            content_length = len(result.content)
            print(f"   ✅ {content_length:,} characters")

            # Save to file
            filename = f"{url_info['name']}_relevant_content_{timestamp}.txt"
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"METHOD: relevant_content\n")
                f.write(f"URL: {url_info['url']}\n")
                f.write(f"QUERY: {url_info['query']}\n")
                f.write(f"PROVIDER: gemini/gemini-2.5-flash\n")
                f.write(f"CONTENT LENGTH: {content_length} characters\n")
                f.write("=" * 80 + "\n")
                f.write(result.content)

            url_results["relevant_content"] = {
                "length": content_length,
                "status": "SUCCESS",
                "filename": filename
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            url_results["relevant_content"] = {"status": "ERROR", "error": str(e)}

        all_results[url_info['name']] = url_results

    # Create comprehensive summary
    summary_file = os.path.join(results_dir, f"crawl4ai_test_summary_{timestamp}.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("CRAWL4AI SDK CLIENT TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Methods Tested: 3 (clean_content, content_summary, relevant_content)\n")
        f.write(f"URLs Tested: {len(test_urls)}\n\n")

        # Results by URL
        for url_name, url_results in all_results.items():
            f.write(f"URL: {url_name.upper()}\n")
            f.write("-" * 30 + "\n")

            for method_name, method_data in url_results.items():
                f.write(f"{method_name}: ")
                if method_data["status"] == "SUCCESS":
                    f.write(f"{method_data['length']:,} chars - {method_data['filename']}\n")
                else:
                    f.write(f"ERROR - {method_data.get('error', 'Unknown error')}\n")
            f.write("\n")

        # Success summary
        total_tests = sum(len(url_results) for url_results in all_results.values())
        successful_tests = sum(
            sum(1 for method_data in url_results.values() if method_data["status"] == "SUCCESS")
            for url_results in all_results.values()
        )

        f.write(f"SUMMARY:\n")
        f.write(f"Total Tests: {total_tests}\n")
        f.write(f"Successful: {successful_tests}\n")
        f.write(f"Success Rate: {successful_tests/total_tests*100:.1f}%\n")

    print(f"\n🎉 Testing completed!")
    print(f"📁 Results saved to: {results_dir}")
    print(f"📊 Summary file: {summary_file}")
    print(f"✅ Total files created: {len(os.listdir(results_dir))}")

    return results_dir, all_results

if __name__ == "__main__":
    print("🚀 TESTING CRAWL4AI SDK CLIENT")
    print("=" * 50)
    print("Testing 3 core methods: clean_content, content_summary, relevant_content...")
    print("This may take several minutes...\n")

    try:
        results_dir, results = test_crawl4ai_client()

        # Quick stats
        total_methods = sum(len(url_data) for url_data in results.values())
        successful_methods = sum(
            sum(1 for method_data in url_data.values() if method_data["status"] == "SUCCESS")
            for url_data in results.values()
        )

        print(f"\n📈 Final Stats:")
        print(f"   Methods tested: {total_methods}")
        print(f"   Successful: {successful_methods}")
        print(f"   Success rate: {successful_methods/total_methods*100:.1f}%")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()