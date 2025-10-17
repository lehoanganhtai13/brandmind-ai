# Workflow Execution Patterns

## Execution Architecture

### Tool Orchestration Engine
```
Request Analysis → Tool Selection → Parallel Execution → Result Integration → Next Steps
       ↓                 ↓                ↓                    ↓                 ↓
Context Building   Tool Ranking    Concurrent Calls      Response Merging   State Update
```

## Tool Ecosystem

### Available Tools (20+ tools)
```javascript
const toolCategories = {
  fileOperations: ['Read', 'Write', 'Edit', 'MultiEdit', 'Glob'],
  codeManagement: ['Grep', 'NotebookEdit'],
  projectManagement: ['Bash', 'TodoWrite'],
  research: ['WebSearch', 'WebFetch', 'Task'],
  systemControl: ['BashOutput', 'KillShell'],
  workflow: ['ExitPlanMode']
}
```

### Tool Selection Matrix
```python
def select_tools(user_request, context):
    intent = classify_intent(user_request)

    tool_mapping = {
        'SEARCH_CODE': ['Grep', 'Glob'],
        'READ_FILES': ['Read'],
        'MODIFY_CODE': ['Edit', 'MultiEdit'],
        'CREATE_FILES': ['Write'],
        'RUN_COMMANDS': ['Bash'],
        'RESEARCH': ['WebSearch', 'Task'],
        'COMPLEX_TASKS': ['Task', 'TodoWrite']
    }

    return tool_mapping.get(intent, ['Task'])  # default to Task agent
```

## Execution Patterns

### 1. Sequential Execution
```javascript
// For dependent operations
async function sequentialWorkflow(tasks) {
  let context = {};

  for (const task of tasks) {
    const result = await executeTask(task, context);
    context = mergeContext(context, result);

    // Update TodoWrite status
    await updateTaskStatus(task.id, 'completed');
  }

  return context;
}

// Example: Authentication Implementation
const authTasks = [
  { type: 'research', action: 'analyze existing auth patterns' },
  { type: 'design', action: 'create auth schema' },
  { type: 'implement', action: 'build JWT middleware' },
  { type: 'test', action: 'write auth tests' }
];
```

### 2. Parallel Execution
```javascript
// For independent operations
async function parallelWorkflow(tasks) {
  // Batch tool calls trong single message
  const promises = tasks.map(task => executeTask(task));
  const results = await Promise.all(promises);

  return mergeResults(results);
}

// Example: Multi-file Analysis
const analysisPromises = [
  bash('git status'),
  bash('git diff'),
  bash('git log --oneline -5'),
  grep('TODO', { glob: '**/*.js' }),
  read('package.json')
];
```

### 3. Conditional Execution
```javascript
function conditionalWorkflow(userRequest) {
  const analysis = analyzeRequest(userRequest);

  if (analysis.complexity === 'high') {
    return executeComplexWorkflow(analysis);
  } else if (analysis.requiresResearch) {
    return executeResearchWorkflow(analysis);
  } else {
    return executeSimpleWorkflow(analysis);
  }
}
```

## Workflow Strategies

### 1. Research-First Pattern
```
User Request: "How to implement caching in this project?"

Workflow:
1. Analyze project structure (Glob, Read)
2. Search for existing caching (Grep)
3. Research best practices (WebSearch, Task)
4. Document findings
5. Propose implementation plan
```

### 2. Implement-and-Verify Pattern
```
User Request: "Add user registration endpoint"

Workflow:
1. Research existing patterns (Grep, Read)
2. Implement endpoint (Edit/Write)
3. Add validation (Edit)
4. Write tests (Write)
5. Run tests (Bash)
6. Fix any issues (Edit)
7. Verify functionality (Bash)
```

### 3. Refactor-Safely Pattern
```
User Request: "Refactor authentication system"

Workflow:
1. Analyze current implementation (Read, Grep)
2. Write comprehensive tests (Write)
3. Run existing tests (Bash)
4. Create backup (git branch)
5. Refactor incrementally (Edit)
6. Test after each change (Bash)
7. Verify all functionality (Bash)
```

## Error Handling & Recovery

### 1. Error Detection Patterns
```javascript
const errorPatterns = {
  compilationErrors: /error|failed|syntax/i,
  testFailures: /failed|failing|error/i,
  lintingIssues: /warning|style|format/i,
  dependencyIssues: /not found|missing|unable to resolve/i
}

function detectErrors(commandOutput) {
  for (const [type, pattern] of Object.entries(errorPatterns)) {
    if (pattern.test(commandOutput)) {
      return { type, detected: true, output: commandOutput };
    }
  }
  return { detected: false };
}
```

### 2. Recovery Strategies
```javascript
const recoveryStrategies = {
  compilationErrors: [
    'analyze error message',
    'check syntax around error location',
    'fix syntax issues',
    'retry compilation'
  ],

  testFailures: [
    'identify failing tests',
    'analyze failure reasons',
    'fix code or update tests',
    'run tests again'
  ],

  dependencyIssues: [
    'check package.json',
    'run npm install',
    'verify dependencies',
    'update if needed'
  ]
}

async function executeRecovery(errorType, context) {
  const strategy = recoveryStrategies[errorType];

  for (const step of strategy) {
    await executeRecoveryStep(step, context);

    // Check if issue resolved
    if (await isIssueResolved(errorType, context)) {
      break;
    }
  }
}
```

### 3. Graceful Degradation
```javascript
function gracefulDegradation(operation, fallbacks) {
  try {
    return operation();
  } catch (error) {
    console.log(`Primary operation failed: ${error.message}`);

    for (const fallback of fallbacks) {
      try {
        return fallback();
      } catch (fallbackError) {
        console.log(`Fallback failed: ${fallbackError.message}`);
      }
    }

    throw new Error('All fallback strategies exhausted');
  }
}

// Example usage
const result = gracefulDegradation(
  () => readFile('config.json'),
  [
    () => readFile('config.default.json'),
    () => generateDefaultConfig(),
    () => ({ error: 'No config available' })
  ]
);
```

## Performance Optimization

### 1. Tool Call Batching
```javascript
// ❌ Inefficient: Multiple separate calls
await bash('git status');
await bash('git diff');
await bash('npm test');

// ✅ Efficient: Single message with multiple tool calls
const [gitStatus, gitDiff, testResult] = await Promise.all([
  bash('git status'),
  bash('git diff'),
  bash('npm test')
]);
```

### 2. Context Reuse
```javascript
class WorkflowContext {
  constructor() {
    this.fileCache = new Map();
    this.commandResults = new Map();
    this.projectInfo = null;
  }

  async getFile(path) {
    if (!this.fileCache.has(path)) {
      const content = await readFile(path);
      this.fileCache.set(path, content);
    }
    return this.fileCache.get(path);
  }

  async runCommand(command) {
    if (!this.commandResults.has(command)) {
      const result = await bash(command);
      this.commandResults.set(command, result);
    }
    return this.commandResults.get(command);
  }
}
```

### 3. Lazy Evaluation
```javascript
class LazyWorkflow {
  constructor(userRequest) {
    this.request = userRequest;
    this.analysis = null;
    this.projectContext = null;
  }

  async getAnalysis() {
    if (!this.analysis) {
      this.analysis = await analyzeRequest(this.request);
    }
    return this.analysis;
  }

  async getProjectContext() {
    if (!this.projectContext) {
      this.projectContext = await buildProjectContext();
    }
    return this.projectContext;
  }
}
```

## Advanced Patterns

### 1. Pipeline Processing
```javascript
class WorkflowPipeline {
  constructor() {
    this.stages = [];
  }

  addStage(name, processor) {
    this.stages.push({ name, processor });
    return this;
  }

  async execute(input) {
    let result = input;

    for (const stage of this.stages) {
      console.log(`Executing stage: ${stage.name}`);
      result = await stage.processor(result);

      // Update TodoWrite progress
      await updateTaskProgress(stage.name, 'completed');
    }

    return result;
  }
}

// Example usage
const implementationPipeline = new WorkflowPipeline()
  .addStage('analysis', analyzeRequirements)
  .addStage('design', createDesign)
  .addStage('implementation', implementFeature)
  .addStage('testing', runTests)
  .addStage('verification', verifyFeature);
```

### 2. State Machine Workflows
```javascript
class WorkflowStateMachine {
  constructor() {
    this.currentState = 'initial';
    this.states = {
      initial: { transitions: ['analyzing'] },
      analyzing: { transitions: ['planning', 'implementing'] },
      planning: { transitions: ['implementing'] },
      implementing: { transitions: ['testing', 'error'] },
      testing: { transitions: ['completed', 'implementing'] },
      error: { transitions: ['analyzing', 'implementing'] },
      completed: { transitions: [] }
    };
  }

  async transition(nextState, action) {
    const currentStateConfig = this.states[this.currentState];

    if (!currentStateConfig.transitions.includes(nextState)) {
      throw new Error(`Invalid transition: ${this.currentState} -> ${nextState}`);
    }

    await action();
    this.currentState = nextState;

    console.log(`Workflow transitioned to: ${nextState}`);
  }
}
```

### 3. Event-Driven Workflows
```javascript
class EventDrivenWorkflow {
  constructor() {
    this.eventHandlers = new Map();
    this.workflowState = {};
  }

  on(event, handler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event).push(handler);
  }

  async emit(event, data) {
    const handlers = this.eventHandlers.get(event) || [];

    for (const handler of handlers) {
      await handler(data, this.workflowState);
    }
  }
}

// Example usage
const workflow = new EventDrivenWorkflow();

workflow.on('file_modified', async (data, state) => {
  console.log(`File ${data.path} was modified`);
  await runLinting(data.path);
});

workflow.on('tests_failed', async (data, state) => {
  console.log('Tests failed, starting fix workflow');
  await debugTestFailures(data.failures);
});
```

## Quality Assurance Integration

### 1. Continuous Verification
```javascript
async function executeWithVerification(task) {
  const result = await executeTask(task);

  // Always verify after significant changes
  if (task.type === 'code_modification') {
    await runLinting();
    await runTypeChecking();
    await runTests();
  }

  return result;
}
```

### 2. Rollback Capability
```javascript
class RollbackCapableWorkflow {
  constructor() {
    this.checkpoints = [];
  }

  async createCheckpoint(description) {
    const checkpoint = {
      description,
      timestamp: Date.now(),
      gitHash: await getCurrentGitHash(),
      fileStates: await captureFileStates()
    };

    this.checkpoints.push(checkpoint);
  }

  async rollbackToCheckpoint(index) {
    const checkpoint = this.checkpoints[index];
    await restoreFileStates(checkpoint.fileStates);
    console.log(`Rolled back to: ${checkpoint.description}`);
  }
}
```

## Best Practices

### 1. Workflow Design
- Start with research and analysis
- Use parallel execution khi có thể
- Include verification steps
- Plan for error recovery
- Maintain clear state transitions

### 2. Tool Usage
- Batch independent operations
- Cache frequently accessed data
- Use appropriate tools cho từng task
- Monitor context usage
- Implement graceful degradation

### 3. Progress Tracking
- Update TodoWrite status realtime
- Provide meaningful progress indicators
- Log important decisions
- Document blockers and solutions
- Communicate changes to user

### 4. Error Handling
- Detect errors early
- Implement automatic recovery
- Provide clear error messages
- Maintain system stability
- Learn from failure patterns