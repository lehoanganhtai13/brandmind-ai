# TodoWrite Tool & Task Management System

## Giới thiệu TodoWrite Tool

TodoWrite là core tool để quản lý task trong Claude Code system. Nó hoạt động như một dynamic project management system, giúp track progress và organize complex workflows.

## Architecture của TodoWrite

### Data Structure
```typescript
interface TodoItem {
  content: string;      // Imperative form: "Fix authentication bug"
  activeForm: string;   // Present continuous: "Fixing authentication bug"
  status: 'pending' | 'in_progress' | 'completed';
}

interface TodoList {
  todos: TodoItem[];
}
```

### State Machine
```
pending → in_progress → completed
   ↑           ↓
   └─── (can revert if needed)
```

## Usage Decision Matrix

### ALWAYS Use TodoWrite When:

#### 1. Multi-step Complex Tasks (3+ steps)
```
Example: "Implement user authentication"
Tasks:
- Research existing auth patterns
- Design JWT token system
- Create login/register endpoints
- Add middleware protection
- Build frontend components
- Write tests
```

#### 2. Multiple Files Involved
```
Example: "Add dark mode support"
Files affected:
- styles/theme.css
- components/ThemeToggle.jsx
- context/ThemeContext.js
- utils/themeUtils.js
```

#### 3. User Provides Lists
```
User: "I need these features: A, B, C and also fix bugs X, Y"
→ Always create TodoWrite cho từng item
```

#### 4. Research-Heavy Tasks
```
Example: "Optimize database performance"
Research needed:
- Analyze current query patterns
- Identify bottlenecks
- Research optimization techniques
- Implement solutions
- Measure improvements
```

### NEVER Use TodoWrite When:

#### 1. Single Simple Actions
```
❌ Bad: "Fix typo in variable name"
✅ Good: Direct edit
```

#### 2. Informational Requests
```
❌ Bad: "What does this function do?"
✅ Good: Direct code analysis
```

#### 3. Trivial Operations
```
❌ Bad: "Run npm install"
✅ Good: Direct bash execution
```

## Task Management Patterns

### 1. Task Creation Strategy

#### Atomic Task Principle
```javascript
// ❌ Too broad
{
  content: "Implement entire user system",
  activeForm: "Implementing entire user system"
}

// ✅ Atomic
{
  content: "Create User model with validation",
  activeForm: "Creating User model with validation"
}
```

#### Dependency Mapping
```javascript
const taskGraph = {
  "Create database schema": [],
  "Implement User model": ["Create database schema"],
  "Build auth endpoints": ["Implement User model"],
  "Add frontend forms": ["Build auth endpoints"],
  "Write integration tests": ["Add frontend forms"]
}
```

### 2. Status Management Rules

#### Critical Rules
1. **One Active Task**: Chỉ 1 task có status `in_progress` tại bất kì thời điểm nào
2. **Immediate Completion**: Mark `completed` ngay khi hoàn thành
3. **No Batching**: Không batch multiple completions
4. **Real-time Updates**: Update status trong mỗi tool call

#### Status Transition Logic
```python
def update_task_status(task_id, new_status):
    # Rule 1: Only one in_progress task
    if new_status == 'in_progress':
        set_all_other_tasks_to_pending()

    # Rule 2: Validate transition
    valid_transitions = {
        'pending': ['in_progress'],
        'in_progress': ['completed', 'pending'],  # can revert if needed
        'completed': []  # terminal state
    }

    current_status = get_task_status(task_id)
    if new_status not in valid_transitions[current_status]:
        raise InvalidTransitionError()

    # Rule 3: Update immediately
    tasks[task_id].status = new_status
    save_todo_list()
```

### 3. Task Breakdown Strategies

#### Top-Down Decomposition
```
"Build e-commerce site"
├── "Set up project structure"
├── "Implement product catalog"
│   ├── "Create Product model"
│   ├── "Build product API"
│   └── "Design product listing UI"
├── "Add shopping cart"
└── "Implement checkout flow"
```

#### Feature-Based Grouping
```javascript
const featureGroups = {
  authentication: [
    "Create user registration",
    "Implement login system",
    "Add password reset"
  ],
  productCatalog: [
    "Design product schema",
    "Build search functionality",
    "Add filtering options"
  ]
}
```

## Advanced TodoWrite Patterns

### 1. Dynamic Task Addition
```javascript
// Discovered during implementation
function addDiscoveredTask(newTask, afterTaskId) {
  const todoList = getCurrentTodoList();
  const insertIndex = findTaskIndex(afterTaskId) + 1;

  todoList.splice(insertIndex, 0, {
    content: newTask,
    activeForm: convertToActiveForm(newTask),
    status: 'pending'
  });

  updateTodoWrite(todoList);
}
```

### 2. Task Dependency Management
```javascript
// Wait for dependencies
function canStartTask(taskId) {
  const task = getTask(taskId);
  const dependencies = getTaskDependencies(taskId);

  return dependencies.every(depId =>
    getTask(depId).status === 'completed'
  );
}
```

### 3. Error Recovery Patterns
```javascript
// When task fails
function handleTaskFailure(taskId, error) {
  // Keep as in_progress, add recovery task
  const recoveryTask = {
    content: `Resolve ${error.type}: ${error.message}`,
    activeForm: `Resolving ${error.type}`,
    status: 'pending'
  };

  insertTaskAfter(taskId, recoveryTask);
}
```

## Real-time Examples

### Example 1: Complex Feature Implementation
```
User Request: "Add real-time chat to the app"

TodoWrite Creation:
1. "Research WebSocket libraries and patterns" (pending)
2. "Design chat data schema" (pending)
3. "Implement WebSocket server setup" (pending)
4. "Create chat room management" (pending)
5. "Build message sending/receiving" (pending)
6. "Add chat UI components" (pending)
7. "Implement typing indicators" (pending)
8. "Add message history storage" (pending)
9. "Write comprehensive tests" (pending)
10. "Deploy and test in staging" (pending)

Execution Flow:
Task 1: pending → in_progress → completed
Task 2: pending → in_progress → completed
... continue sequentially
```

### Example 2: Bug Fix with Investigation
```
User Request: "Fix the slow loading issue"

TodoWrite Creation:
1. "Investigate performance bottlenecks" (pending)
2. "Profile database queries" (pending)
3. "Analyze bundle size and loading" (pending)
4. "Identify root cause" (pending)
5. "Implement performance fixes" (pending)
6. "Measure performance improvements" (pending)
7. "Document optimization changes" (pending)

Dynamic Addition During Execution:
- Task discovered: "Add database indexing" (added after Task 4)
- Task discovered: "Implement lazy loading" (added after Task 5)
```

## Integration với Other Systems

### 1. Memory Management
```javascript
// TodoWrite state persists across tool calls
const todoContext = {
  currentSession: getCurrentTodoList(),
  completedTasks: getCompletedTasks(),
  blockedTasks: getBlockedTasks(),
  estimatedTimeRemaining: calculateTimeEstimate()
}
```

### 2. Error Reporting
```javascript
// Track task failure patterns
const taskMetrics = {
  successRate: calculateSuccessRate(),
  commonFailurePoints: identifyFailurePatterns(),
  averageTaskDuration: getAverageCompletionTime()
}
```

### 3. User Feedback Loop
```javascript
// Provide progress visibility
function generateProgressReport() {
  const total = todoList.length;
  const completed = todoList.filter(t => t.status === 'completed').length;
  const inProgress = todoList.filter(t => t.status === 'in_progress').length;

  return {
    progress: `${completed}/${total} completed`,
    currentTask: getCurrentTask()?.activeForm,
    estimatedRemaining: estimateRemainingTime()
  }
}
```

## Best Practices

### 1. Task Naming Convention
- **Content**: Imperative verb + specific object
  - ✅ "Implement JWT authentication middleware"
  - ❌ "Authentication stuff"
- **ActiveForm**: Present continuous của content
  - ✅ "Implementing JWT authentication middleware"

### 2. Granularity Guidelines
- 1 task = 1 logical unit of work
- Should complete trong 5-15 minutes
- Can be verified independently
- Has clear done criteria

### 3. Progress Communication
- Update TodoWrite after mỗi significant progress
- Provide context về current task
- Explain blockers or changes in approach

### 4. Quality Gates
```javascript
const qualityGates = {
  beforeCompletion: [
    'Code compiles successfully',
    'Tests pass',
    'No linting errors',
    'Meets acceptance criteria'
  ]
}
```