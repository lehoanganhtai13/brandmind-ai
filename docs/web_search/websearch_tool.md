# WebSearch Tool Documentation

## Overview
The WebSearch tool allows Claude Code to search the web and use results to inform responses. It provides up-to-date information for current events and recent data beyond Claude's knowledge cutoff.

## Functionality
- Performs web searches automatically within a single API call
- Returns search result information formatted as search result blocks
- Provides access to current information and recent data
- Only available in the US region

## Parameters

### Required
- `query` (string): The search query to use (minimum 2 characters)

### Optional
- `allowed_domains` (array): Only include search results from these domains
- `blocked_domains` (array): Never include search results from these domains

## Return Format
The tool returns structured search results containing:
- Website titles and URLs
- Content snippets from each result
- Ranked results based on relevance
- Metadata about the search

## Usage Examples

### Basic Search
```
WebSearch:
query: "React hooks useState 2024"
```

### Domain-Filtered Search
```
WebSearch:
query: "machine learning tutorials"
allowed_domains: ["github.com", "stackoverflow.com"]
```

### Blocked Domain Search
```
WebSearch:
query: "Python best practices"
blocked_domains: ["spam-site.com", "low-quality.net"]
```

## Sample Output Structure
```
Search Results:
1. [React Documentation] useState Hook - Complete Guide
   https://react.dev/reference/react/useState
   useState is a React Hook that lets you add state variables to function components...

2. [Medium] React useState Best Practices 2024
   https://medium.com/react-development/useState-patterns
   Learn the latest useState patterns and anti-patterns in React 18...

3. [Stack Overflow] useState not updating immediately
   https://stackoverflow.com/questions/useState-async-updates
   Common issue with useState updates being asynchronous and batched...
```

## Best Practices
- Use specific, targeted queries for better results
- Include current year in queries when seeking recent information
- Use domain filtering to focus on authoritative sources
- Keep queries concise but descriptive

## Limitations
- Only available in the United States
- Results depend on web search engine availability
- Cannot access content behind paywalls or login walls
- Rate limits may apply based on usage