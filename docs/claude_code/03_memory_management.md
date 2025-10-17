# Memory Management & Context Handling

## Overview
Claude Code quản lý 200K token context window để duy trì session state, file contents, và conversation history xuyên suốt project work.

## Context Architecture

### 1. Context Window Structure
```
Total: 200,000 tokens
├── System Instructions (5K tokens)
├── Tool Definitions (10K tokens)
├── Conversation History (80K tokens)
├── File Contents Cache (90K tokens)
├── Active TodoWrite State (5K tokens)
├── Environment Context (5K tokens)
└── Reserved Buffer (5K tokens)
```

### 2. Memory Layers

#### Layer 1: Persistent Session Memory
```javascript
const sessionMemory = {
  projectContext: {
    workingDirectory: '/path/to/project',
    gitStatus: 'current branch info',
    projectType: 'detected framework',
    dependencies: 'package.json analysis'
  },
  userPreferences: {
    codingStyle: 'inferred patterns',
    frameworks: 'preferred technologies',
    conventions: 'coding standards'
  }
}
```

#### Layer 2: File Content Cache
```javascript
const fileCache = {
  recentlyRead: new Map([
    ['src/main.js', { content: '...', timestamp: Date.now() }],
    ['package.json', { content: '...', timestamp: Date.now() }]
  ]),
  frequentlyAccessed: new Set(['config/app.js', 'src/utils.js']),
  modificationHistory: new Map([
    ['src/main.js', [{ timestamp: Date.now(), changes: '...' }]]
  ])
}
```

#### Layer 3: Task Context Memory
```javascript
const taskMemory = {
  currentTodoList: [...],
  taskHistory: [...],
  contextualInfo: {
    originalRequest: 'user\'s initial request',
    discoveredRequirements: [...],
    implementationDecisions: [...]
  }
}
```

## Memory Management Strategies

### 1. Intelligent Context Pruning

#### LRU (Least Recently Used) for File Contents
```python
class FileContentCache:
    def __init__(self, max_size_tokens=90000):
        self.cache = OrderedDict()
        self.max_size = max_size_tokens
        self.current_size = 0

    def get(self, file_path):
        if file_path in self.cache:
            # Move to end (most recently used)
            content = self.cache.pop(file_path)
            self.cache[file_path] = content
            return content
        return None

    def put(self, file_path, content):
        token_count = estimate_tokens(content)

        # Remove old entries if needed
        while (self.current_size + token_count > self.max_size and
               len(self.cache) > 0):
            oldest_file, oldest_content = self.cache.popitem(last=False)
            self.current_size -= estimate_tokens(oldest_content)

        self.cache[file_path] = content
        self.current_size += token_count
```

#### Conversation History Compression
```python
def compress_conversation_history(history, target_tokens=80000):
    # Keep recent messages intact
    recent_threshold = 20  # last 20 messages
    recent_messages = history[-recent_threshold:]

    # Summarize older messages by task completion
    older_messages = history[:-recent_threshold]
    compressed_older = summarize_by_task_completion(older_messages)

    return compressed_older + recent_messages
```

### 2. Context Switching Optimization

#### Project Context Loading
```javascript
function loadProjectContext(workingDirectory) {
  const context = {
    // Essential project info
    packageManager: detectPackageManager(),
    framework: detectFramework(),
    buildTools: detectBuildTools(),
    testFramework: detectTestFramework(),

    // Project structure
    keyDirectories: identifyKeyDirectories(),
    entryPoints: findEntryPoints(),
    configFiles: findConfigFiles(),

    // Git context
    currentBranch: getCurrentBranch(),
    recentCommits: getRecentCommits(5),
    modifiedFiles: getModifiedFiles()
  }

  return context;
}
```

#### Lazy Loading Strategy
```javascript
const contextLoader = {
  // Load immediately
  immediate: ['project structure', 'git status', 'package.json'],

  // Load on demand
  onDemand: {
    'dependency analysis': () => analyzeDependencies(),
    'test configuration': () => loadTestConfig(),
    'build configuration': () => loadBuildConfig()
  },

  // Cache for session
  cached: new Map()
}
```

### 3. Memory-Aware Tool Usage

#### Batch Operations
```javascript
// Instead of multiple Read calls
const files = await Promise.all([
  readFile('src/component1.js'),
  readFile('src/component2.js'),
  readFile('src/component3.js')
]);

// Process all together to optimize context usage
analyzeComponents(files);
```

#### Context-Preserving Searches
```javascript
function smartSearch(query, options = {}) {
  // Use Grep instead of reading entire files
  const matches = grep(query, options);

  // Only read full files for top matches
  const relevantFiles = matches.slice(0, 5);
  const fullContents = relevantFiles.map(file =>
    readFile(file.path)
  );

  return { matches, fullContents };
}
```

## Context Preservation Techniques

### 1. State Serialization
```javascript
function serializeSessionState() {
  return {
    todoList: getCurrentTodoList(),
    fileCache: serializeFileCache(),
    projectContext: getProjectContext(),
    userPreferences: getUserPreferences(),
    taskHistory: getTaskHistory(),
    timestamp: Date.now()
  }
}

function deserializeSessionState(serializedState) {
  restoreTodoList(serializedState.todoList);
  restoreFileCache(serializedState.fileCache);
  restoreProjectContext(serializedState.projectContext);
  // ...
}
```

### 2. Contextual Anchoring
```javascript
// Maintain references to important context
const contextAnchors = {
  originalRequest: 'user initial request',
  keyDecisions: [
    'chose React over Vue for components',
    'decided to use TypeScript',
    'selected Jest for testing'
  ],
  progressMarkers: [
    'completed authentication system',
    'finished API integration',
    'deployed to staging'
  ]
}
```

### 3. Progressive Context Building
```javascript
function buildProgressiveContext(userRequest) {
  let context = {
    immediate: parseUserRequest(userRequest),
    project: null,
    dependencies: null,
    codebase: null
  };

  // Build context progressively as needed
  if (requiresProjectAnalysis(userRequest)) {
    context.project = analyzeProjectStructure();
  }

  if (requiresDependencyCheck(userRequest)) {
    context.dependencies = analyzeDependencies();
  }

  if (requiresCodebaseUnderstanding(userRequest)) {
    context.codebase = buildCodebaseMap();
  }

  return context;
}
```

## Performance Optimization

### 1. Token Estimation
```python
def estimate_tokens(text):
    # Approximation: 1 token ≈ 4 characters for English
    # Vietnamese có thể khác nhau
    return len(text) // 3.5  # Conservative estimate

def shouldCacheFile(file_path, content):
    token_count = estimate_tokens(content)
    file_importance = calculateFileImportance(file_path)

    # Cache if important or small enough
    return (file_importance > 0.8 or token_count < 1000)
```

### 2. Selective Context Loading
```javascript
const contextLoadingStrategy = {
  // Always load
  essential: [
    'current working directory',
    'git status',
    'active todo list'
  ],

  // Load based on request type
  conditional: {
    'coding tasks': ['project structure', 'dependencies'],
    'debugging tasks': ['error logs', 'test results'],
    'research tasks': ['documentation', 'code patterns']
  },

  // Load only when explicitly needed
  expensive: [
    'full codebase analysis',
    'dependency graph',
    'test coverage report'
  ]
}
```

### 3. Memory Monitoring
```javascript
class MemoryMonitor {
  constructor() {
    this.tokenUsage = {
      system: 0,
      conversation: 0,
      fileCache: 0,
      todoState: 0
    };
  }

  trackTokenUsage(category, tokens) {
    this.tokenUsage[category] += tokens;

    if (this.getTotalUsage() > 180000) { // 90% of limit
      this.triggerContextPruning();
    }
  }

  getTotalUsage() {
    return Object.values(this.tokenUsage).reduce((a, b) => a + b, 0);
  }

  triggerContextPruning() {
    // Remove least important cached content
    this.pruneFileCache();
    this.compressConversationHistory();
    this.summarizeCompletedTasks();
  }
}
```

## Cross-Session Memory

### 1. Project Memory Persistence
```javascript
// Stored in project-specific memory (not implemented in current system)
const projectMemory = {
  conventions: {
    codingStyle: 'detected patterns',
    namingConventions: 'learned preferences',
    architecturalPatterns: 'identified patterns'
  },

  frequentTasks: [
    'npm run test',
    'npm run build',
    'git commit patterns'
  ],

  problemPatterns: [
    'common errors encountered',
    'successful solution patterns'
  ]
}
```

### 2. Learning from Interactions
```javascript
function learnFromSession(sessionData) {
  const insights = {
    userPreferences: extractUserPreferences(sessionData),
    effectivePatterns: identifySuccessfulPatterns(sessionData),
    commonPitfalls: identifyCommonErrors(sessionData),
    optimizationOpportunities: findOptimizations(sessionData)
  };

  // Store for future sessions (conceptual)
  updateUserProfile(insights);
}
```

## Best Practices

### 1. Memory-Efficient Coding
- Use Grep thay vì Read cho searches
- Batch tool calls để giảm context switching
- Cache frequently accessed files
- Remove obsolete cached content

### 2. Context Preservation
- Maintain reference to original user intent
- Preserve key implementation decisions
- Keep track of progress milestones
- Document important discoveries

### 3. Proactive Memory Management
- Monitor context usage continuously
- Prune unnecessary content proactively
- Compress old conversation history
- Prioritize high-value information

## Error Recovery

### Memory Overflow Scenarios
```javascript
function handleMemoryOverflow() {
  const recovery = {
    immediate: [
      'Clear oldest file cache entries',
      'Compress conversation history',
      'Summarize completed tasks'
    ],

    graceful: [
      'Ask user for priority guidance',
      'Suggest breaking down large tasks',
      'Recommend session restart if needed'
    ]
  };

  executeRecoveryStrategy(recovery);
}
```