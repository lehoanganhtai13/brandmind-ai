# WebFetch Tool Documentation

## Overview
The WebFetch tool fetches content from specified URLs and processes it using an AI model. It converts HTML to markdown and analyzes the content based on provided prompts.

## Functionality
- Fetches content from any valid URL
- Converts HTML content to markdown format
- Processes content with AI model using custom prompts
- Returns AI-generated analysis or summary of the content
- Includes 15-minute self-cleaning cache for performance
- Automatically upgrades HTTP URLs to HTTPS

## Parameters

### Required
- `url` (string): The URL to fetch content from (must be valid URI format)
- `prompt` (string): The prompt to run on the fetched content

## Return Format
The tool returns the AI model's response about the content based on the provided prompt. The response format depends on the prompt but typically includes:
- Processed and analyzed content
- Summaries, extractions, or specific information requested
- Structured data based on prompt requirements

## Usage Examples

### Content Summary
```
WebFetch:
url: "https://react.dev/reference/react/useState"
prompt: "Summarize the useState syntax and basic usage"
```

### Specific Information Extraction
```
WebFetch:
url: "https://api-docs.example.com/authentication"
prompt: "Extract all available authentication methods and their required parameters"
```

### Code Example Extraction
```
WebFetch:
url: "https://github.com/example/repo/blob/main/README.md"
prompt: "Find and list all code examples with their explanations"
```

## Sample Output
```
useState is a React Hook with this syntax:

const [state, setState] = useState(initialValue)

Key points:
- Returns array with current state and setter function
- initialValue can be primitive value or function
- setState triggers component re-render
- Updates are asynchronous and batched in React 18
- Use functional updates for complex state logic

Example usage:
const [count, setCount] = useState(0)
setCount(count + 1) // or setCount(prev => prev + 1)
```

## Special Behaviors

### URL Redirects
When a URL redirects to a different host, the tool will:
1. Inform you of the redirect
2. Provide the redirect URL in a special format
3. Require a new WebFetch request with the redirect URL

### HTTP to HTTPS Upgrade
- HTTP URLs are automatically upgraded to HTTPS
- No manual conversion needed

### Content Processing
- HTML is converted to markdown for better readability
- Large content may be summarized if it exceeds processing limits
- Content is analyzed through a small, fast AI model

## Best Practices
- Write specific, clear prompts for better analysis
- Use descriptive prompts that specify the desired output format
- For large pages, focus prompts on specific sections or information
- Test prompts with similar content to refine results

## Limitations
- Read-only tool - cannot modify any files
- Results may be summarized for very large content
- Depends on website accessibility and structure
- Cannot access content requiring authentication
- May be blocked by websites with strict anti-bot measures
- Cache expires after 15 minutes

## Performance Features
- 15-minute cache reduces repeated fetches of same URL
- Automatic content optimization for AI processing
- Fast response times for cached content

## Security Considerations
- Only fetches from provided URLs (no URL generation)
- No credential or sensitive data exposure
- Safe for accessing public web content
- Cannot execute JavaScript or dynamic content