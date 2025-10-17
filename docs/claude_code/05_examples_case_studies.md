# Examples & Case Studies

## Case Study 1: Complex Feature Implementation

### Scenario: "Implement Real-time Chat System"

#### Initial Request Analysis
```
User: "Tôi muốn thêm chat realtime vào app React này. Cần có typing indicators, message history, và room management."

Analysis Result:
- Intent: CODING (complex feature)
- Scope: Project Wide
- Complexity: High (8+ steps)
- Technologies: React, WebSockets, Backend integration
- Decision: Use TodoWrite
```

#### TodoWrite Planning
```json
{
  "todos": [
    {"content": "Research existing WebSocket libraries and chat patterns", "status": "pending", "activeForm": "Researching existing WebSocket libraries and chat patterns"},
    {"content": "Design chat data schema and message structure", "status": "pending", "activeForm": "Designing chat data schema and message structure"},
    {"content": "Set up WebSocket server infrastructure", "status": "pending", "activeForm": "Setting up WebSocket server infrastructure"},
    {"content": "Implement message sending and receiving", "status": "pending", "activeForm": "Implementing message sending and receiving"},
    {"content": "Create typing indicator functionality", "status": "pending", "activeForm": "Creating typing indicator functionality"},
    {"content": "Build chat room management system", "status": "pending", "activeForm": "Building chat room management system"},
    {"content": "Design and implement chat UI components", "status": "pending", "activeForm": "Designing and implementing chat UI components"},
    {"content": "Add message history and persistence", "status": "pending", "activeForm": "Adding message history and persistence"},
    {"content": "Implement user authentication for chat", "status": "pending", "activeForm": "Implementing user authentication for chat"},
    {"content": "Write comprehensive tests for chat functionality", "status": "pending", "activeForm": "Writing comprehensive tests for chat functionality"},
    {"content": "Optimize performance and handle edge cases", "status": "pending", "activeForm": "Optimizing performance and handling edge cases"}
  ]
}
```

#### Execution Workflow

**Phase 1: Research & Discovery**
```javascript
// Tools used: Grep, Read, WebSearch
const discoveryActions = [
  grep('socket', { glob: '**/*.{js,jsx,ts,tsx}' }),
  read('package.json'),
  read('src/App.js'),
  webSearch('react websocket best practices 2024')
];

// Discoveries:
// - Project uses React 18 with hooks
// - No existing WebSocket implementation
// - Socket.io recommended for reliability
// - Need to consider authentication integration
```

**Phase 2: Architecture Design**
```javascript
// Dynamic task addition based on discoveries
const newTasks = [
  "Install and configure Socket.io client and server",
  "Create authentication middleware for WebSocket connections",
  "Design message encryption for security"
];

// Update TodoWrite with new discoveries
updateTodoList(existingTasks.concat(newTasks));
```

**Phase 3: Implementation**
```javascript
// Parallel execution where possible
const parallelImplementation = [
  // Backend work
  write('server/socket-handlers.js', socketHandlerCode),
  write('server/chat-middleware.js', authMiddlewareCode),

  // Frontend work
  write('src/hooks/useSocket.js', socketHookCode),
  write('src/components/ChatWindow.jsx', chatComponentCode),

  // Configuration
  edit('package.json', addSocketDependencies)
];

// Sequential execution for dependent tasks
const sequentialWork = [
  implementMessageSchema(),
  buildChatRoomLogic(),
  integrateWithAuth(),
  addTypingIndicators(),
  implementPersistence()
];
```

**Phase 4: Testing & Verification**
```javascript
const testingPhase = [
  write('src/tests/chat.test.js', chatTestSuite),
  write('server/tests/socket.test.js', socketTestSuite),
  bash('npm test -- --coverage'),
  bash('npm run build'),
  bash('npm run lint')
];

// Error handling during testing
if (testsFailed) {
  addTodoTask("Fix failing chat tests");
  analyzeTestFailures();
  implementFixes();
  rerunTests();
}
```

### Results & Lessons Learned
- **Time**: 2 hours of implementation
- **Files Modified**: 12 files
- **Tests Added**: 25 test cases
- **Key Insight**: Early architecture decisions prevented major refactoring later

---

## Case Study 2: Debugging Complex Issue

### Scenario: "App crashes on production but works locally"

#### Problem Analysis Workflow
```javascript
// Initial investigation (parallel)
const investigation = [
  bash('git log --oneline -10'),  // Recent changes
  bash('git diff main..HEAD'),    // Current differences
  grep('error|Error|ERROR', { glob: '**/*.{js,log}' }),
  read('.env.example'),
  read('package.json')
];

// Findings:
// - Recent deployment 2 days ago
// - Environment variables different in prod
// - No error logging in production
```

#### TodoWrite for Systematic Debugging
```json
{
  "todos": [
    {"content": "Analyze production error logs and crash reports", "status": "in_progress", "activeForm": "Analyzing production error logs and crash reports"},
    {"content": "Compare environment configurations between local and prod", "status": "pending", "activeForm": "Comparing environment configurations"},
    {"content": "Reproduce issue in local environment", "status": "pending", "activeForm": "Reproducing issue in local environment"},
    {"content": "Add comprehensive error logging", "status": "pending", "activeForm": "Adding comprehensive error logging"},
    {"content": "Implement error boundary components", "status": "pending", "activeForm": "Implementing error boundary components"},
    {"content": "Test fix in staging environment", "status": "pending", "activeForm": "Testing fix in staging environment"},
    {"content": "Deploy hotfix to production", "status": "pending", "activeForm": "Deploying hotfix to production"}
  ]
}
```

#### Root Cause Discovery
```javascript
// Found through systematic investigation
const rootCause = {
  issue: "Environment variable REACT_APP_API_URL missing in production",
  symptoms: [
    "API calls failing silently",
    "Undefined URL causing fetch errors",
    "App crash due to unhandled promise rejection"
  ],
  fix: "Add proper environment variable validation and fallbacks"
};
```

#### Implementation of Fix
```javascript
// Added environment validation
const envValidation = `
// src/utils/envValidation.js
export function validateEnv() {
  const required = ['REACT_APP_API_URL', 'REACT_APP_ENV'];
  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(\`Missing environment variables: \${missing.join(', ')}\`);
  }
}
`;

// Added error boundary
const errorBoundary = `
// src/components/ErrorBoundary.jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
`;
```

### Resolution & Prevention
- **Root Cause**: Missing environment variable validation
- **Fix Time**: 45 minutes from identification to deployment
- **Prevention**: Added CI/CD environment validation step

---

## Case Study 3: Performance Optimization

### Scenario: "React app is slow, especially on mobile"

#### Performance Investigation Strategy
```javascript
// Multi-pronged analysis approach
const performanceAnalysis = [
  // Bundle analysis
  bash('npm run build -- --analyze'),

  // Code analysis
  grep('useEffect\\(\\(\\)', { glob: 'src/**/*.{js,jsx}' }),
  grep('useState\\(.*\\[.*\\]\\)', { glob: 'src/**/*.jsx' }),

  // Dependency analysis
  bash('npm ls --depth=0'),
  read('package.json'),

  // Find large files
  bash('find src -name "*.js" -o -name "*.jsx" | xargs wc -l | sort -rn | head -10')
];
```

#### TodoWrite for Optimization Plan
```json
{
  "todos": [
    {"content": "Analyze bundle size and identify heavy dependencies", "status": "completed", "activeForm": "Analyzing bundle size"},
    {"content": "Profile React component re-renders", "status": "completed", "activeForm": "Profiling React component re-renders"},
    {"content": "Implement code splitting for large components", "status": "in_progress", "activeForm": "Implementing code splitting"},
    {"content": "Add React.memo for expensive components", "status": "pending", "activeForm": "Adding React.memo for expensive components"},
    {"content": "Optimize images and assets", "status": "pending", "activeForm": "Optimizing images and assets"},
    {"content": "Implement virtualization for large lists", "status": "pending", "activeForm": "Implementing virtualization for large lists"},
    {"content": "Add performance monitoring", "status": "pending", "activeForm": "Adding performance monitoring"},
    {"content": "Test performance improvements on mobile", "status": "pending", "activeForm": "Testing performance improvements on mobile"}
  ]
}
```

#### Discovery & Implementation
```javascript
// Major findings
const performanceIssues = {
  bundleSize: "3.2MB uncompressed, 850KB gzipped",
  heavyDependencies: ["moment.js (200KB)", "lodash (70KB)", "chart.js (180KB)"],
  componentIssues: [
    "ProductList re-rendering on every state change",
    "No memoization in expensive calculations",
    "Large image files not optimized"
  ]
};

// Implementation strategy
const optimizations = [
  // Bundle optimization
  edit('src/utils/dateUtils.js', replaceMomentWithDateFns),
  edit('src/utils/arrayUtils.js', replaceWithNativeMethods),

  // Component optimization
  edit('src/components/ProductList.jsx', addReactMemo),
  edit('src/components/ProductCard.jsx', optimizeRendering),

  // Asset optimization
  bash('npm install --save-dev imagemin-webpack-plugin'),
  edit('webpack.config.js', addImageOptimization)
];
```

#### Results Achieved
```javascript
const performanceResults = {
  bundleSize: {
    before: "850KB gzipped",
    after: "420KB gzipped",
    improvement: "50% reduction"
  },
  loadTime: {
    before: "4.2s on 3G",
    after: "1.8s on 3G",
    improvement: "57% faster"
  },
  renderPerformance: {
    before: "16-24ms per render",
    after: "4-8ms per render",
    improvement: "70% faster"
  }
};
```

---

## Case Study 4: API Integration

### Scenario: "Integrate with Stripe payment system"

#### Research-First Approach
```javascript
// Understanding requirements
const researchPhase = [
  webSearch('stripe react integration best practices 2024'),
  webSearch('stripe webhook security nodejs'),
  grep('payment|stripe', { glob: '**/*.{js,jsx}' }),
  read('src/services/api.js'),
  read('.env.example')
];
```

#### TodoWrite Planning
```json
{
  "todos": [
    {"content": "Research Stripe React integration patterns", "status": "completed", "activeForm": "Researching Stripe React integration patterns"},
    {"content": "Set up Stripe account and get API keys", "status": "completed", "activeForm": "Setting up Stripe account and API keys"},
    {"content": "Install and configure Stripe dependencies", "status": "in_progress", "activeForm": "Installing and configuring Stripe dependencies"},
    {"content": "Create payment intent endpoint on backend", "status": "pending", "activeForm": "Creating payment intent endpoint on backend"},
    {"content": "Implement checkout form component", "status": "pending", "activeForm": "Implementing checkout form component"},
    {"content": "Add payment confirmation flow", "status": "pending", "activeForm": "Adding payment confirmation flow"},
    {"content": "Implement webhook handling for payment events", "status": "pending", "activeForm": "Implementing webhook handling for payment events"},
    {"content": "Add error handling and retry logic", "status": "pending", "activeForm": "Adding error handling and retry logic"},
    {"content": "Test payment flow in sandbox environment", "status": "pending", "activeForm": "Testing payment flow in sandbox environment"},
    {"content": "Add payment history and receipts", "status": "pending", "activeForm": "Adding payment history and receipts"}
  ]
}
```

#### Security-First Implementation
```javascript
// Backend security measures
const securityMeasures = {
  webhookValidation: `
    const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

    const validateWebhook = (req, res, next) => {
      const sig = req.headers['stripe-signature'];
      const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

      try {
        const event = stripe.webhooks.constructEvent(req.body, sig, endpointSecret);
        req.stripeEvent = event;
        next();
      } catch (err) {
        console.log('Webhook signature verification failed.', err.message);
        return res.status(400).send(\`Webhook Error: \${err.message}\`);
      }
    };
  `,

  environmentValidation: `
    const requiredEnvVars = [
      'STRIPE_PUBLISHABLE_KEY',
      'STRIPE_SECRET_KEY',
      'STRIPE_WEBHOOK_SECRET'
    ];

    requiredEnvVars.forEach(envVar => {
      if (!process.env[envVar]) {
        throw new Error(\`Missing required environment variable: \${envVar}\`);
      }
    });
  `
};
```

#### Frontend Implementation
```javascript
// Stripe Elements integration
const stripeIntegration = `
// src/components/CheckoutForm.jsx
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const CheckoutForm = ({ amount, onSuccess, onError }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    if (!stripe || !elements) {
      return;
    }

    // Create payment intent
    const { client_secret } = await createPaymentIntent(amount);

    // Confirm payment
    const result = await stripe.confirmCardPayment(client_secret, {
      payment_method: {
        card: elements.getElement(CardElement),
      }
    });

    if (result.error) {
      onError(result.error);
    } else {
      onSuccess(result.paymentIntent);
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement />
      <button disabled={!stripe || loading}>
        {loading ? 'Processing...' : 'Pay Now'}
      </button>
    </form>
  );
};
`;
```

#### Testing Strategy
```javascript
const testingApproach = [
  // Unit tests
  write('src/tests/CheckoutForm.test.jsx', checkoutFormTests),
  write('server/tests/payment.test.js', paymentEndpointTests),

  // Integration tests
  write('tests/payment-flow.test.js', endToEndPaymentTests),

  // Manual testing checklist
  write('docs/payment-testing-checklist.md', testingChecklist)
];
```

### Key Learnings
- **Security**: Webhook validation critical for production
- **Testing**: Stripe test cards essential for development
- **Error Handling**: Payment errors need user-friendly messages
- **Compliance**: PCI compliance considerations for card data

---

## Common Patterns & Anti-Patterns

### ✅ Successful Patterns

#### 1. Research-First Approach
```javascript
// Always start with understanding
const successfulWorkflow = [
  'Analyze existing codebase',
  'Research best practices',
  'Plan implementation',
  'Execute with verification',
  'Test thoroughly'
];
```

#### 2. Incremental Implementation
```javascript
// Build in small, testable chunks
const incrementalSteps = [
  'Implement core functionality',
  'Add basic tests',
  'Verify functionality',
  'Add edge cases',
  'Enhance with advanced features'
];
```

#### 3. Parallel Task Execution
```javascript
// Maximize efficiency with batching
const parallelExecution = [
  Promise.all([
    bash('git status'),
    bash('npm test'),
    read('package.json')
  ]),

  // Process results together
  analyzeResults(results)
];
```

### ❌ Anti-Patterns to Avoid

#### 1. Implementation Without Research
```javascript
// ❌ Bad: Jump straight to coding
user: "Add authentication"
assistant: write('auth.js', basicAuthCode);

// ✅ Good: Research existing patterns first
user: "Add authentication"
assistant: grep('auth', project) → analyze patterns → plan approach → implement
```

#### 2. Ignoring Error States
```javascript
// ❌ Bad: Happy path only
const implementation = `
function fetchUser(id) {
  return fetch(\`/api/users/\${id}\`).then(res => res.json());
}
`;

// ✅ Good: Comprehensive error handling
const robustImplementation = `
async function fetchUser(id) {
  try {
    const response = await fetch(\`/api/users/\${id}\`);

    if (!response.ok) {
      throw new Error(\`HTTP \${response.status}: \${response.statusText}\`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}
`;
```

#### 3. Monolithic Task Breakdown
```javascript
// ❌ Bad: Too broad
{
  content: "Build entire user management system",
  status: "pending"
}

// ✅ Good: Specific, actionable tasks
[
  { content: "Create User model with validation", status: "pending" },
  { content: "Implement user registration endpoint", status: "pending" },
  { content: "Add email verification flow", status: "pending" },
  { content: "Build user profile management", status: "pending" }
]
```

## Summary of Best Practices

### 1. Planning Phase
- Always analyze before implementing
- Use TodoWrite for complex tasks
- Research existing patterns
- Plan for error scenarios

### 2. Execution Phase
- Batch independent operations
- Implement incrementally
- Test continuously
- Handle errors gracefully

### 3. Verification Phase
- Run comprehensive tests
- Check linting and type checking
- Verify in multiple environments
- Document implementation decisions

### 4. Communication
- Update progress in real-time
- Explain complex decisions
- Provide context for changes
- Highlight potential issues early