# Request Analysis & Task Breakdown Process

## Quy trình phân tích yêu cầu

### Phase 1: Input Parsing
```
User Input → Language Detection → Intent Classification → Scope Identification
```

#### 1.1 Language Detection
- Tiếng Việt: Sử dụng natural language processing
- English: Technical commands và descriptions
- Code: Syntax highlighting và language detection

#### 1.2 Intent Classification
```javascript
const intentTypes = {
  CODING: ["implement", "create", "build", "develop"],
  DEBUGGING: ["fix", "debug", "solve", "error"],
  RESEARCH: ["find", "search", "analyze", "understand"],
  REFACTOR: ["refactor", "optimize", "improve", "clean"],
  DOCUMENTATION: ["document", "explain", "comment"],
  TESTING: ["test", "verify", "validate"],
  DEPLOYMENT: ["deploy", "build", "release"]
}
```

#### 1.3 Scope Identification
- **Single File**: Chỉ 1 file cần modification
- **Multi File**: Nhiều files liên quan
- **Project Wide**: Toàn bộ project structure
- **Research Only**: Không cần code changes

### Phase 2: Complexity Assessment

#### 2.1 Complexity Matrix
```
Simple (1-2 steps):
- Single function edit
- Variable rename
- Simple bug fix

Medium (3-5 steps):
- Feature implementation
- Multi-file changes
- API integration

Complex (6+ steps):
- Architecture changes
- Full feature development
- System integration
```

#### 2.2 Dependency Analysis
```python
def analyze_dependencies(request):
    dependencies = {
        'files': identify_affected_files(request),
        'libraries': check_required_libraries(request),
        'external_apis': scan_for_api_calls(request),
        'database': check_db_operations(request),
        'environment': assess_env_requirements(request)
    }
    return dependencies
```

### Phase 3: Task Breakdown Strategy

#### 3.1 Decomposition Rules
1. **Atomic Tasks**: Mỗi task chỉ làm 1 việc cụ thể
2. **Sequential Logic**: Tasks có thể depend on nhau
3. **Parallel Opportunities**: Identify tasks có thể chạy song song
4. **Verification Points**: Mỗi major task cần verification step

#### 3.2 TodoWrite Decision Tree
```
Request Received
    ├── Is it complex? (3+ steps)
    │   ├── Yes → Use TodoWrite
    │   └── No → Direct execution
    ├── Multiple files involved?
    │   ├── Yes → Use TodoWrite
    │   └── No → Consider direct
    ├── User provided list?
    │   ├── Yes → Always use TodoWrite
    │   └── No → Assess complexity
    └── Research required?
        ├── Extensive → Use TodoWrite
        └── Minimal → Direct execution
```

### Phase 4: Task Prioritization

#### 4.1 Priority Matrix
```
Priority 1 (Critical Path):
- Core functionality implementation
- Blocking dependencies
- Critical bug fixes

Priority 2 (Enhancement):
- Performance optimizations
- Code quality improvements
- Documentation updates

Priority 3 (Nice to Have):
- Additional features
- Cosmetic improvements
- Extra validations
```

#### 4.2 Execution Order Strategy
1. **Research First**: Understand codebase trước khi modify
2. **Dependencies**: Implement dependencies trước dependents
3. **Core Logic**: Main functionality trước edge cases
4. **Testing**: Verification sau mỗi major component
5. **Integration**: Connect components cuối cùng

## Examples

### Example 1: Simple Request
```
User: "Fix typo in function name"
Analysis:
- Intent: DEBUGGING
- Scope: Single File
- Complexity: Simple (1 step)
- Decision: Direct execution, no TodoWrite
```

### Example 2: Complex Request
```
User: "Add authentication system with JWT, OAuth, and role-based permissions"
Analysis:
- Intent: CODING
- Scope: Project Wide
- Complexity: Complex (10+ steps)
- Decision: TodoWrite with detailed breakdown

TodoWrite Tasks:
1. Research existing auth patterns
2. Design authentication architecture
3. Implement JWT token handling
4. Create OAuth integration
5. Build role-based permission system
6. Add middleware for route protection
7. Create user management endpoints
8. Implement session management
9. Add authentication UI components
10. Write comprehensive tests
11. Update documentation
```

### Example 3: Research Request
```
User: "Tìm hiểu cách implement caching trong project này"
Analysis:
- Intent: RESEARCH
- Scope: Project Wide
- Complexity: Medium (research extensive)
- Decision: TodoWrite for systematic research

TodoWrite Tasks:
1. Search for existing caching implementation
2. Analyze current data flow patterns
3. Identify caching opportunities
4. Research suitable caching libraries
5. Document findings and recommendations
```

## Advanced Patterns

### Pattern Matching
```javascript
const patterns = {
  CRUD_OPERATIONS: /create|read|update|delete|CRUD/i,
  API_DEVELOPMENT: /api|endpoint|route|server/i,
  UI_COMPONENTS: /component|react|vue|angular|ui/i,
  DATABASE_WORK: /database|db|sql|query|migration/i,
  TESTING: /test|spec|jest|cypress|unit|integration/i
}
```

### Context Preservation
- Maintain request context throughout execution
- Reference original request khi clarification needed
- Preserve user intent qua multiple tool calls

### Error Recovery
- Detect khi task breakdown không accurate
- Adjust plan based on discovered information
- Communicate changes back to user