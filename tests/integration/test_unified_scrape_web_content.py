#!/usr/bin/env python3
"""
Test the unified scrape_web_content function with 3 modes across diverse URLs.
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared', 'src'))

from shared.agent_tools.crawler.crawl_web import scrape_web_content

def test_unified_scrape():
    """Test all 3 modes of the unified scrape_web_content function."""

    print("🚀 TESTING UNIFIED SCRAPE_WEB_CONTENT FUNCTION")
    print("=" * 60)
    print("Testing 3 modes: clean, summary, relevant")
    print("Testing across 5 diverse domains and content types...\n")

    # Diverse test URLs from different domains and content types
    test_urls = [
        {
            "name": "tech_news",
            "url": "https://techcrunch.com/2024/12/23/openai-chatgpt-search-vs-google/",
            "query": "How does ChatGPT search compare to Google search features?"
        },
        {
            "name": "documentation",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "query": "What are the basic Python data types and their usage?"
        },
        {
            "name": "ecommerce",
            "url": "https://www.amazon.com/dp/B08N5WRWNW",
            "query": "What are the key features and specifications of this product?"
        },
        {
            "name": "blog_post",
            "url": "https://openai.com/index/introducing-chatgpt-and-whisper-apis/",
            "query": "What are the pricing and capabilities of the new ChatGPT API?"
        },
        {
            "name": "news_article",
            "url": "https://www.bbc.com/news/technology-67755909",
            "query": "What are the main concerns about AI regulation and safety?"
        }
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/unified_scrape_test_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    all_results = {}

    for url_info in test_urls:
        print(f"\n{'='*60}")
        print(f"TESTING: {url_info['name'].upper()}")
        print(f"URL: {url_info['url']}")
        print('='*60)

        url_results = {}

        # Test Mode 1: Clean content extraction
        print(f"\n🔄 Testing CLEAN mode...")
        try:
            result = scrape_web_content(url_info["url"], mode="clean")
            content_length = len(result.content)
            print(f"   ✅ {content_length:,} characters")

            # Save to file
            filename = f"{url_info['name']}_clean_mode_{timestamp}.txt"
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"MODE: clean\n")
                f.write(f"URL: {url_info['url']}\n")
                f.write(f"DESCRIPTION: Clean content extraction with balanced filtering\n")
                f.write(f"CONTENT LENGTH: {content_length} characters\n")
                f.write("=" * 80 + "\n")
                f.write(result.content)

            url_results["clean"] = {
                "length": content_length,
                "status": "SUCCESS",
                "filename": filename
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            url_results["clean"] = {"status": "ERROR", "error": str(e)}

        # Test Mode 2: Summary extraction
        print(f"\n🔄 Testing SUMMARY mode...")
        try:
            result = scrape_web_content(url_info["url"], mode="summary")
            content_length = len(result.content)
            print(f"   ✅ {content_length:,} characters")

            # Save to file
            filename = f"{url_info['name']}_summary_mode_{timestamp}.txt"
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"MODE: summary\n")
                f.write(f"URL: {url_info['url']}\n")
                f.write(f"DESCRIPTION: LLM-generated structured summary\n")
                f.write(f"CONTENT LENGTH: {content_length} characters\n")
                f.write("=" * 80 + "\n")
                f.write(result.content)

            url_results["summary"] = {
                "length": content_length,
                "status": "SUCCESS",
                "filename": filename
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            url_results["summary"] = {"status": "ERROR", "error": str(e)}

        # Test Mode 3: Relevant content filtering
        print(f"\n🔄 Testing RELEVANT mode...")
        try:
            result = scrape_web_content(url_info["url"], mode="relevant", query=url_info["query"])
            content_length = len(result.content)
            print(f"   ✅ {content_length:,} characters")

            # Save to file
            filename = f"{url_info['name']}_relevant_mode_{timestamp}.txt"
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"MODE: relevant\n")
                f.write(f"URL: {url_info['url']}\n")
                f.write(f"QUERY: {url_info['query']}\n")
                f.write(f"DESCRIPTION: LLM-filtered content relevant to query\n")
                f.write(f"CONTENT LENGTH: {content_length} characters\n")
                f.write("=" * 80 + "\n")
                f.write(result.content)

            url_results["relevant"] = {
                "length": content_length,
                "status": "SUCCESS",
                "filename": filename
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            url_results["relevant"] = {"status": "ERROR", "error": str(e)}

        all_results[url_info['name']] = url_results

    # Create comprehensive summary
    summary_file = os.path.join(results_dir, f"unified_scrape_summary_{timestamp}.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("UNIFIED SCRAPE_WEB_CONTENT TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Modes Tested: 3 (clean, summary, relevant)\n")
        f.write(f"URLs Tested: {len(test_urls)}\n")
        f.write(f"Domains Covered: Tech News, Documentation, E-commerce, Blog, News\n\n")

        # Results by URL
        for url_name, url_results in all_results.items():
            f.write(f"URL: {url_name.upper()}\n")
            f.write("-" * 30 + "\n")

            for mode_name, mode_data in url_results.items():
                f.write(f"{mode_name}: ")
                if mode_data["status"] == "SUCCESS":
                    f.write(f"{mode_data['length']:,} chars - {mode_data['filename']}\n")
                else:
                    f.write(f"ERROR - {mode_data.get('error', 'Unknown error')}\n")
            f.write("\n")

        # Success summary
        total_tests = sum(len(url_results) for url_results in all_results.values())
        successful_tests = sum(
            sum(1 for mode_data in url_results.values() if mode_data["status"] == "SUCCESS")
            for url_results in all_results.values()
        )

        f.write(f"SUMMARY:\n")
        f.write(f"Total Tests: {total_tests}\n")
        f.write(f"Successful: {successful_tests}\n")
        f.write(f"Success Rate: {successful_tests/total_tests*100:.1f}%\n\n")

        # Mode comparison
        f.write("MODE ANALYSIS:\n")
        f.write("-" * 20 + "\n")

        mode_stats = {"clean": [], "summary": [], "relevant": []}
        for url_results in all_results.values():
            for mode, data in url_results.items():
                if data["status"] == "SUCCESS":
                    mode_stats[mode].append(data["length"])

        for mode, lengths in mode_stats.items():
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                f.write(f"{mode.upper()} mode: {len(lengths)}/{len(test_urls)} successful, avg {avg_length:.0f} chars\n")
            else:
                f.write(f"{mode.upper()} mode: 0/{len(test_urls)} successful\n")

    print(f"\n🎉 Testing completed!")
    print(f"📁 Results saved to: {results_dir}")
    print(f"📊 Summary file: {summary_file}")
    print(f"✅ Total files created: {len(os.listdir(results_dir))}")

    return results_dir, all_results

if __name__ == "__main__":
    try:
        results_dir, results = test_unified_scrape()

        # Quick stats
        total_modes = sum(len(url_data) for url_data in results.values())
        successful_modes = sum(
            sum(1 for mode_data in url_data.values() if mode_data["status"] == "SUCCESS")
            for url_data in results.values()
        )

        print(f"\n📈 Final Stats:")
        print(f"   Total mode tests: {total_modes}")
        print(f"   Successful: {successful_modes}")
        print(f"   Success rate: {successful_modes/total_modes*100:.1f}%")

        # Mode breakdown
        mode_counts = {"clean": 0, "summary": 0, "relevant": 0}
        for url_data in results.values():
            for mode, data in url_data.items():
                if data["status"] == "SUCCESS":
                    mode_counts[mode] += 1

        print(f"\n📊 Mode Success Breakdown:")
        for mode, count in mode_counts.items():
            print(f"   {mode.capitalize()}: {count}/5 URLs")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()