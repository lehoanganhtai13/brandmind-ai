# BrandMind AI - Deployment Architecture Analysis Report

> **Purpose**: Phân tích chi tiết kiến trúc deployment cho 3 mode (TUI, Web Local, Web Cloud), đề xuất hướng tối ưu dựa trên research các hệ thống thực tế.
>
> **Date**: 2026-02-13
> **Status**: Proposal for Discussion

---

## 1. Bối Cảnh & Vấn Đề

### 1.1 Plan Ban Đầu (3 mode riêng lẻ)

```
Mode 1: TUI (Local)
├── BrandMind agent embedded trực tiếp trong CLI process
├── Chạy: `brandmind` (Textual TUI)
└── ✅ Đã có base hoạt động

Mode 2: Web Local
├── ❌ Plan: Embed web UI vào CLI ("brandmind-ui" kiểu Google ADK)
├── Backend + Frontend cùng 1 process
└── Phức tạp: phải bundle web vào Python package

Mode 3: Web Cloud (Multi-tenant)
├── ❌ Plan: Full microservice trong Docker
├── BrandMind service riêng + Web UI service riêng
└── Khác biệt hoàn toàn về kiến trúc so với Mode 2
```

### 1.2 Vấn Đề Với Plan Cũ

| Vấn đề | Chi tiết |
|--------|----------|
| **3 integration patterns khác nhau** | TUI: embedded, Web local: monolith, Web cloud: microservice |
| **Code duplication** | Agent logic phải adapt cho 3 cách gọi khác nhau |
| **Testing complexity** | Phải test 3 deployment topology riêng biệt |
| **Maintenance burden** | Mỗi lần thay đổi agent API phải update 3 nơi |

---

## 2. Research: Các Hệ Thống Tham Khảo

### 2.1 Google ADK (Agent Development Kit)

**Kiến trúc**: Backend (FastAPI) tách biệt hoàn toàn với Frontend (Angular SPA).

```
┌─────────────────────────────┐     ┌───────────────────────────────┐
│  adk-web (Angular SPA)      │     │  adk-python (FastAPI)         │
│  github.com/google/adk-web  │────▶│  github.com/google/adk-python │
│  Port 4200                  │REST │  Port 8000                    │
│                             │SSE  │                               │
│                             │WS   │  /run_sse, /run_live          │
└─────────────────────────────┘     └───────────────────────────────┘
```

**Key takeaways**:
- `adk web` CLI command = spin up FastAPI backend + serve pre-built static frontend (convenience wrapper)
- `adk api_server` = headless API only (cho production / custom frontend)
- Frontend là SPA riêng, communicate qua REST + SSE + WebSocket
- **Không có auth** — dev-only tool, không dùng cho production
- API pattern: `/apps/{app}/users/{user_id}/sessions/{session_id}`

**Relevance cho BrandMind**: ADK giải quyết đúng vấn đề "CLI dev convenience" nhưng **không** giải quyết local-vs-cloud deployment. ADK Web là dev-only, không production-grade.

### 2.2 Dify (Production AI Platform)

**Kiến trúc**: Service-oriented, **same codebase** cho self-hosted & cloud.

```
┌──────────────────────────────────────────────────────┐
│                    nginx (reverse proxy)             │
│  /api → api:5001  |  / → web:3000                    │
└──────┬─────────────────────────┬─────────────────────┘
       │                         │
┌──────▼──────────┐    ┌─────────▼─────────┐
│  api (Flask)    │    │  web (Next.js)    │
│  EDITION=       │    │  Static frontend  │
│  SELF_HOSTED    │    │                   │
│  or CLOUD       │    │                   │
└──────┬──────────┘    └───────────────────┘
       │
┌──────▼──────────┐  ┌───────────┐  ┌──────────┐
│  worker (Celery)│  │  Redis    │  │  Postgres│
│  Background jobs│  │  Queue    │  │  Database│
└─────────────────┘  └───────────┘  └──────────┘
```

**Key takeaways**:
- **`EDITION` env var** gates behavior: `SELF_HOSTED` vs `CLOUD`
- Decorators `@only_edition_self_hosted` / `@only_edition_cloud` cho endpoint access
- Cùng Docker Compose cho local, cùng codebase cho cloud (khác ở infra layer)
- Auth: **luôn bật**, ngay cả self-hosted cũng phải setup admin đầu tiên
- `tenant_id` pervasive trong toàn bộ codebase từ đầu

**Relevance cho BrandMind**: **Mô hình phù hợp nhất**. Same codebase, config-driven mode switching, tenant_id built-in từ đầu.

### 2.3 Open WebUI

**Kiến trúc**: Pure monolith, single Docker image.

```
┌────────────────────────────────────────┐
│  Single Docker Container               │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ SvelteKit    │  │ FastAPI        │  │
│  │ (pre-built)  │  │ Backend        │  │
│  │ Static files │  │ /api/v1/*      │  │
│  └──────────────┘  └────────────────┘  │
│           Same Python process          │
└────────────────────────────────────────┘
```

**Key takeaways**:
- `WEBUI_AUTH=False` disables auth entirely (single-user)
- `WEBUI_AUTH=True` enables full JWT + OAuth (multi-user)
- Không có multi-tenant concept, chỉ multi-user trên cùng instance
- **Đơn giản nhất** nhưng không scale cho multi-tenant

**Relevance cho BrandMind**: Quá đơn giản cho mục tiêu cloud multi-tenant, nhưng `WEBUI_AUTH` toggle pattern hay.

### 2.4 Supabase

**Kiến trúc**: True microservices, **cùng stack** cho local CLI & cloud.

```
┌───────────────────────────────────────────────────┐
│                  Kong (API Gateway)               │
│  /auth/* → GoTrue  |  /rest/* → PostgREST         │
│  /realtime/* → Realtime  |  /storage/* → Storage  │
└──────┬──────────┬──────────┬──────────┬───────────┘
       │          │          │          │
┌──────▼───┐ ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐
│ GoTrue   │ │PostgRES │ │Realtime│ │ Storage │
│ (Auth)   │ │ T       │ │(Elixir)│ │ API     │
└──────────┘ └─────────┘ └────────┘ └─────────┘
                    │
              ┌─────▼──────┐
              │ PostgreSQL │
              │ + RLS      │
              └────────────┘
```

**Key takeaways**:
- `supabase start` chạy **đúng** cùng microservice stack locally
- Cloud = managed version of same services (ECS, RDS, etc.)
- **Kong API Gateway** = centralized policy enforcement
- **Row Level Security (RLS)** = zero-trust at database level
- Mỗi service verify JWT independently

**Relevance cho BrandMind**: Zero-trust pattern (Kong + RLS) rất tốt cho cloud, nhưng overhead quá lớn cho MVP.

### 2.5 Langflow

**Kiến trúc**: Monolith, `AUTO_LOGIN` flag.

**Key takeaways**:
- `AUTO_LOGIN=True` → auto-create default user, bypass auth
- `AUTO_LOGIN=False` → full JWT auth
- Có package nhẹ `lfx` với no-op AuthService cho embedded use
- Không multi-tenant

---

## 3. So Sánh Tổng Hợp

| Tiêu chí | Dify | Supabase | Open WebUI | Langflow | ADK |
|----------|------|----------|------------|----------|-----|
| Same codebase local/cloud | ✅ EDITION flag | ✅ Same stack | ✅ (no cloud) | ✅ AUTO_LOGIN | ❌ Dev only |
| Multi-tenant | ✅ tenant_id | ✅ RLS | ❌ | ❌ | ❌ |
| Auth bypass (local) | ❌ Always on | ❌ Always on | ✅ WEBUI_AUTH | ✅ AUTO_LOGIN | N/A |
| Zero-trust inter-service | Partial (API keys) | ✅ Kong + RLS | N/A (monolith) | N/A | N/A |
| Startup complexity (local) | ~10 containers | ~10 containers | 1 container | 1 container | 1 process |
| Production-grade | ✅ | ✅ | Partial | Partial | ❌ |

---

## 4. Đề Xuất Kiến Trúc: "Unified Service, Config-Driven Mode"

### 4.1 Triết Lý Cốt Lõi

Lấy cảm hứng chính từ **Dify** (same codebase, config-driven) + **Supabase** (zero-trust for cloud):

> **"Một codebase, hai deployment mode, config quyết định behavior"**

```
┌────────────────────────────────────────────────────────┐
│                   BrandMind Codebase                   │
│                                                        │
│   ┌──────────┐   ┌──────────────┐   ┌───────────────┐  │
│   │ TUI      │   │ API Server   │   │ Web UI (SPA)  │  │
│   │ (Textual)│   │ (FastAPI)    │   │ (React/Svelte)│  │
│   │          │   │              │   │               │  │
│   │ embedded │   │ standalone   │   │ standalone    │  │
│   │ agent    │   │ service      │   │ static app    │  │
│   └──────────┘   └──────┬───────┘   └───────┬───────┘  │
│                         │                   │          │
│                         └────────┬──────────┘          │
│                                  │                     │
│                    ┌─────────────▼──────────────┐      │
│                    │   Core Agent Engine        │      │
│                    │   (shared business logic)  │      │
│                    └────────────────────────────┘      │
└────────────────────────────────────────────────────────┘
```

### 4.2 Ba Mode Chạy

```
Mode 1: TUI (không thay đổi)
─────────────────────────────
$ brandmind
→ Textual TUI, agent embedded in-process
→ Không cần API server, không cần web
→ Single-user, no auth

Mode 2: Web Local (docker compose up)
──────────────────────────────────────
$ docker compose -f docker-compose.yml up
→ BrandMind API Server (FastAPI) — container
→ Web UI (static SPA) — container (nginx hoặc Node)
→ Infra services (FalkorDB, Milvus, Valkey) — containers
→ DEPLOY_MODE=local
→ Auth: bypass (auto-create single user, no login screen)
→ VFS: local disk mount

Mode 3: Web Cloud (docker compose -f docker-compose.cloud.yml up)
─────────────────────────────────────────────────────────────────
→ Cùng BrandMind API Server image
→ Cùng Web UI image
→ DEPLOY_MODE=cloud
→ Auth: JWT + API key enforcement
→ VFS: S3 backend
→ Zero-trust: API Gateway (Traefik/Kong) giữa frontend ↔ backend
→ tenant_id isolation in graph DB
```

### 4.3 Architecture Chi Tiết

#### 4.3.1 Tổng Quan Component

```
                    ┌─────────────────────────────────────┐
                    │          CLIENT LAYER               │
                    │                                     │
                    │  ┌─────────┐     ┌───────────────┐  │
                    │  │  TUI    │     │  Web SPA      │  │
                    │  │(Textual)│     │(React/Svelte) │  │
                    │  └────┬────┘     └───────┬───────┘  │
                    │       │                  │          │
                    └───────┼──────────────────┼──────────┘
                            │                  │
                   In-process call        REST + SSE
                            │                  │
                    ┌───────┼──────────────────┼──────────┐
                    │       │    SERVICE LAYER │          │
                    │       │                  │          │
                    │  ┌────▼──────────────────▼───────┐  │
                    │  │     BrandMind API Server      │  │
                    │  │         (FastAPI)             │  │
                    │  │                               │  │
                    │  │  ┌──────────┐ ┌─────────────┐ │  │
                    │  │  │ Auth     │ │ Agent       │ │  │
                    │  │  │ Layer    │ │ Engine      │ │  │
                    │  │  │(mode-    │ │(core logic) │ │  │
                    │  │  │ aware)   │ │             │ │  │
                    │  │  └──────────┘ └─────────────┘ │  │
                    │  │                               │  │
                    │  │  ┌──────────┐ ┌────────────┐  │  │
                    │  │  │ Memory   │ │ VFS        │  │  │
                    │  │  │ Service  │ │ (backend-  │  │  │
                    │  │  │(Graphiti)│ │ abstracted)│  │  │
                    │  │  └──────────┘ └────────────┘  │  │
                    │  └───────────────────────────────┘  │
                    │                                     │
                    └─────────────────────────────────────┘
                                      │
                    ┌─────────────────┼───────────────────┐
                    │    INFRASTRUCTURE LAYER             │
                    │                                     │
                    │  ┌────────┐ ┌────────┐ ┌──────────┐ │
                    │  │FalkorDB│ │Milvus  │ │Valkey    │ │
                    │  │(Graph) │ │(Vector)│ │(Cache/Q) │ │
                    │  └────────┘ └────────┘ └──────────┘ │
                    │                                     │
                    └─────────────────────────────────────┘
```

#### 4.3.2 Auth Layer Design (Config-Driven)

```python
# Pseudocode - Auth Strategy Pattern

class AuthConfig:
    """Auth configuration driven by DEPLOY_MODE."""
    
    @staticmethod
    def from_env() -> "AuthStrategy":
        mode = os.getenv("DEPLOY_MODE", "local")
        if mode == "local":
            return LocalAuthStrategy()
        elif mode == "cloud":
            return CloudAuthStrategy()

class LocalAuthStrategy:
    """Local mode: minimal auth, single implicit user."""
    
    def __init__(self):
        self.auto_user_id = "local_user"  # Fixed user ID
        self.require_login = False
    
    async def authenticate(self, request) -> User:
        # Always return the local user, no token needed
        return User(id=self.auto_user_id, tenant_id="local")
    
    async def get_tenant_id(self, request) -> str:
        return "local"  # Fixed tenant

class CloudAuthStrategy:
    """Cloud mode: JWT-based auth, multi-tenant isolation."""
    
    def __init__(self):
        self.require_login = True
        self.jwt_secret = os.getenv("JWT_SECRET")
    
    async def authenticate(self, request) -> User:
        token = extract_bearer_token(request)
        payload = verify_jwt(token, self.jwt_secret)
        return User(id=payload["sub"], tenant_id=payload["tenant_id"])
    
    async def get_tenant_id(self, request) -> str:
        user = await self.authenticate(request)
        return user.tenant_id
```

**Key design decisions:**

1. **`tenant_id` built-in từ đầu** — Local mode vẫn có `tenant_id="local"`, nên DB schema/queries luôn filter theo tenant. Khi chuyển cloud, chỉ thay giá trị, không thay logic.

2. **Auth middleware configurable** — FastAPI dependency injection:
```python
# In API routes
@router.post("/chat")
async def chat(
    message: ChatMessage,
    user: User = Depends(get_current_user),  # Auto-resolved by mode
):
    # user.tenant_id is always available
    ...
```

3. **Frontend không cần biết mode** — Local: API trả user info ngay (no login screen). Cloud: redirect to login page. Frontend chỉ check `GET /auth/me` — nếu 200 thì đã auth, nếu 401 thì show login.

#### 4.3.3 VFS Backend Abstraction (Đã có trong Memory Architecture)

```python
# Đã plan trong BRANDMIND_MEMORY_ARCHITECTURE.md
class FilesystemBackend(Protocol):
    async def read(self, path: str) -> bytes: ...
    async def write(self, path: str, data: bytes): ...
    async def list(self, path: str) -> list[str]: ...

class LocalFilesystemBackend:
    """DEPLOY_MODE=local → ~/.brandmind/workspace/{tenant_id}/"""
    base_path = Path.home() / ".brandmind" / "workspace"

class S3FilesystemBackend:
    """DEPLOY_MODE=cloud → s3://brandmind-users/{tenant_id}/"""
    bucket = "brandmind-users"
```

#### 4.3.4 Graph DB Tenant Isolation

```
Approach: Tenant-Prefixed Graph Names

Local:   knowledge_graph (shared KG) + local_memory (user graph)
Cloud:   knowledge_graph (shared KG) + {tenant_id}_memory (per-tenant)

Shared KG: Read-only marketing knowledge (Kotler, Keller, etc.)
           → Same for all tenants (no duplication)
           
Per-tenant Memory Graph: Episodic + Semantic memory
           → Isolated by tenant_id prefix
           → Graphiti engine scoped to tenant's subgraph
```

#### 4.3.5 API Contract (Unified)

```yaml
# API endpoints - same for local & cloud
# Difference: auth enforcement

# === CORE (Web UI uses these) ===
POST   /api/v1/chat                    # Send message, get SSE stream (thinking + answer)
GET    /api/v1/chat/sessions           # List user's sessions
GET    /api/v1/chat/sessions/{id}      # Get session details + history
DELETE /api/v1/chat/sessions/{id}      # Delete session
GET    /api/v1/auth/me                 # Get current user info
POST   /api/v1/auth/login              # Login (cloud only, 404 on local)
POST   /api/v1/auth/register           # Register (cloud only, 404 on local)
GET    /api/v1/health                  # Health check

# === ADVANCED (Exist but not exposed in Web UI - for CLI/dev/future) ===
GET    /api/v1/search/kg               # Knowledge Graph search (dev tool)
GET    /api/v1/search/docs             # Document Library search (dev tool)
GET    /api/v1/workspace/files         # VFS file listing (future: file upload)
PUT    /api/v1/workspace/files/{path}  # VFS file write (future: file upload)
GET    /api/v1/workspace/profile       # User profile/preferences (future)
PUT    /api/v1/workspace/profile       # Update profile (future)
```

**Note**: Web UI chỉ dùng CORE endpoints. Agent tự động gọi search_kg/search_docs internally khi cần (không qua API).

#### 4.3.6 Zero-Trust for Cloud

```
LOCAL MODE:
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Web SPA  │────▶│ BrandMind API│────▶│ Infra (DBs)  │
│ :3000    │     │ :8000        │     │              │
└──────────┘     └──────────────┘     └──────────────┘
    Direct connection, same Docker network, no TLS needed

CLOUD MODE:
┌──────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────┐
│ Web SPA  │────▶│ API Gateway   │────▶│ BrandMind API│────▶│ Infra    │
│ (CDN)    │HTTPS│ (Traefik/Kong)│mTLS │ (internal)   │     │ (DBs)    │
└──────────┘     └───────────────┘     └──────────────┘     └──────────┘
                       │
                 ┌─────▼──────┐
                 │ Auth rules │
                 │ Rate limit │
                 │ CORS       │
                 │ JWT verify │
                 └────────────┘

Zero-trust measures (cloud only):
1. API Gateway validates JWT on every request
2. mTLS between gateway ↔ backend services
3. Internal services NOT exposed to internet
4. tenant_id from JWT, never from client input
5. Rate limiting per tenant
6. CORS restricted to known frontend domain
```

### 4.4 Docker Compose Configurations

#### 4.4.1 Local Mode

```yaml
# docker-compose.yml (local, extends existing infra)
services:
  # === NEW: BrandMind API Server ===
  brandmind-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: brandmind-api
    environment:
      - DEPLOY_MODE=local
      - FALKORDB_HOST=falkordb
      - MILVUS_HOST=milvus
      - VALKEY_HOST=valkey
    ports:
      - "8000:8000"
    volumes:
      - brandmind-workspace:/data/workspace  # Local VFS
    depends_on:
      - falkordb
      - milvus
    networks:
      - brandmind-network

  # === NEW: Web UI ===
  brandmind-web:
    build:
      context: ./web
      dockerfile: Dockerfile
    container_name: brandmind-web
    environment:
      - API_URL=http://brandmind-api:8000
    ports:
      - "3000:3000"
    depends_on:
      - brandmind-api
    networks:
      - brandmind-network

  # === EXISTING: Infra services (from current docker-compose.yml) ===
  falkordb:
    # ... (existing config)
  milvus:
    # ... (existing config)
  # etc.
```

#### 4.4.2 Cloud Mode

```yaml
# docker-compose.cloud.yml (extends docker-compose.yml)
services:
  # API Gateway
  traefik:
    image: traefik:v3
    ports:
      - "443:443"
    volumes:
      - ./infra/traefik:/etc/traefik
    networks:
      - brandmind-network

  brandmind-api:
    environment:
      - DEPLOY_MODE=cloud
      - JWT_SECRET=${JWT_SECRET}
      - S3_BUCKET=${S3_BUCKET}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=PathPrefix(`/api`)"
      - "traefik.http.routers.api.tls=true"
    # NO ports exposed — only through Traefik

  brandmind-web:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=PathPrefix(`/`)"
      - "traefik.http.routers.web.tls=true"
    # NO ports exposed — only through Traefik
```

### 4.5 Frontend Strategy

#### Option A: Embedded SPA served by FastAPI (như Open WebUI / Langflow)

```
FastAPI serves:
  /api/*        → API routes
  /*            → Static SPA files (pre-built React/Svelte)
```

**Pros**: Single container, simple deployment, ít config
**Cons**: Coupling frontend build với backend, khó scale frontend independently

#### Option B: Separate SPA container (như Dify / ADK) ⬅️ **RECOMMENDED**

```
brandmind-web (nginx):
  /*            → Static SPA files
  /api/*        → reverse proxy to brandmind-api:8000

brandmind-api (FastAPI):
  /api/*        → API routes only
```

**Pros**: Independent scaling, CDN-friendly, clear separation
**Cons**: Thêm 1 container

#### Decision: **Option B** (Separate containers) ✅ CONFIRMED

Lý do:
1. **Consistent với microservice philosophy** đã plan trong Memory Architecture
2. **CDN-ready** — Cloud mode có thể serve SPA từ CDN, chỉ API traffic đến server
3. **Independent development** — Frontend dev không cần rebuild Python
4. **Enterprise-friendly** — "Enterprise muốn xài thì họ có thể tự build frontend" (như bạn nói) → API-first design tự nhiên support điều này
5. **Local vẫn đơn giản** — 2 containers nhỏ, docker compose up là xong
6. **Dễ quản lý và scale** — Frontend có thể deploy riêng, scale horizontally độc lập

---

## 4.6 Scope Clarification: TUI/CLI vs Web UI

### TUI Mode (hiện tại - `brandmind`)

```
Features:
├── Chat (ask mode)              ✅ Main feature
├── KG search (search-kg)         ✅ Dev/test tool
├── Doc search (search-docs)      ✅ Dev/test tool
└── Embedded agent in-process
```

### CLI Mode (command-line - `brandmind ask/search-*`)

```
Features:
├── brandmind ask -q "..."       ✅ One-shot Q&A
├── brandmind search-kg          ✅ Dev/test tool
├── brandmind search-docs        ✅ Dev/test tool
└── Same agent as TUI, headless
```

### Web UI Mode (NEW - docker compose)

```
Features:
├── Chat interface                ✅ ONLY feature exposed
│   ├── Real-time streaming
│   ├── Thinking blocks
│   ├── Tool calls display
│   └── Chat history
│
├── KG search                     ❌ NOT exposed in UI
├── Doc search                    ❌ NOT exposed in UI
└── API endpoints exist but not in frontend

Rationale:
- search-kg/docs là dev tools, không phù hợp end-user UX
- Web UI focus vào conversational experience
- Agent tự động dùng KG/Doc tools internally khi cần
- Giữ UI đơn giản, không overwhelm user
```

**Key insight**: Web UI là **chat-first**, không phải "expose all CLI features". Agent đủ thông minh để search KG/docs tự động.

---

## 5. Tại Sao Approach Này Tốt Hơn Plan Cũ

### 5.1 So Sánh Trực Tiếp

| Tiêu chí | Plan Cũ (3 mode riêng lẻ) | Plan Mới (Unified) |
|----------|--------------------------|---------------------|
| Integration patterns | 3 khác nhau | 2 (TUI embedded + Web microservice) |
| Agent logic duplication | Phải adapt 3 nơi | 1 core engine, 2 entry points |
| Web UI codebase | Phải maintain 2 (local + cloud) | 1 SPA, mode-agnostic |
| Docker Compose files | 2 bộ khác nhau | 1 base + 1 override cho cloud |
| Auth implementation | 2 implementations khác nhau | 1 strategy pattern, config-driven |
| Testing | Test 3 topologies | Test 2 (TUI + API server) |
| Time to MVP web | Phải build "brandmind-ui" CLI wrapper | Chỉ cần FastAPI endpoints + SPA |

### 5.2 Simplification Map

```
TRƯỚC (Plan Cũ):
─────────────────
TUI ──── embedded agent ──── direct DB calls
Web Local ── embedded web+agent in CLI ── bundled everything
Web Cloud ── separate services ── different architecture

SAU (Plan Mới):
────────────────
TUI ──── embedded agent ──── direct DB calls (không đổi)
Web * ── API Server + SPA ── same architecture, DEPLOY_MODE config
```

### 5.3 Migration Path

```
Phase 0 (Current): TUI works ✅
     │
Phase 1: Build FastAPI API Server
     │   - Extract agent logic thành service layer
     │   - Expose REST + SSE endpoints
     │   - DEPLOY_MODE=local (no auth)
     │   - Test with curl/Postman
     │
Phase 2: Build minimal Web SPA
     │   - Chat interface
     │   - Connect to API Server
     │   - docker compose up → cả 2 chạy
     │
Phase 3: Add cloud support
     │   - DEPLOY_MODE=cloud
     │   - JWT auth
     │   - S3 VFS backend
     │   - API Gateway (Traefik)
     │   - tenant_id isolation
     │
Phase 4: Memory Service integration
         - Redis Streams event publishing
         - Memory Worker container
         - Graphiti per-tenant graphs
```

---

## 6. Chi Tiết Kỹ Thuật Quan Trọng

### 6.1 Agent Engine Extraction

Hiện tại `create_qa_agent()` trong [src/cli/inference.py](../../../src/cli/inference.py) tạo agent trực tiếp. Agent đã có **streaming support** đầy đủ (thinking + answer tokens via `StreamingThinkingEvent` + `StreamingTokenEvent`). Cần extract thành service layer reusable cho cả TUI và API Server:

```python
# src/core/agent_service.py (proposed)
class AgentService:
    """Stateless agent service, reusable by TUI and API."""
    
    def __init__(self, tenant_id: str, user_id: str):
        self.tenant_id = tenant_id
        self.user_id = user_id
    
    async def chat_stream(
        self, 
        message: str,
        session_id: str,
    ) -> AsyncIterator[AgentEvent]:
        """
        Stream agent response as events (SSE-compatible).
        
        Events include:
        - StreamingThinkingEvent (thinking tokens)
        - ToolCallEvent (when agent uses search_kg/search_docs internally)
        - ToolResultEvent (tool results)
        - StreamingTokenEvent (answer tokens)
        - TodoUpdateEvent (todo list updates)
        """
        agent = self._create_agent()  # Already has KG/doc tools attached
        async for event in agent.astream(message):
            yield event
```

```python
# src/cli/inference.py (TUI, minimal changes)
from core.agent_service import AgentService

async def run_ask_mode(question: str):
    service = AgentService(tenant_id="local", user_id="local_user")
    async for event in service.chat_stream(question, session_id="tui"):
        renderer.handle_event(event)
```

```python
# src/api/routes/chat.py (new, for web mode)
from core.agent_service import AgentService
from sse_starlette.sse import EventSourceResponse

@router.post("/api/v1/chat")
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
):
    service = AgentService(
        tenant_id=user.tenant_id,
        user_id=user.id,
    )
    
    async def event_generator():
        """Convert agent events to SSE format."""
        async for event in service.chat_stream(body.message, body.session_id):
            # SSE format: data: {json}\n\n
            yield {
                "event": event.type,  # thinking, tool_call, tool_result, token, todo
                "data": event.model_dump_json(),
            }
    
    return EventSourceResponse(event_generator())
```

### 6.2 Frontend Auth Flow

```
LOCAL MODE:
┌─────────┐     GET /api/v1/auth/me       ┌────────────┐
│ Web SPA │ ─────────────────────────────▶│ API Server │
│         │     200 { user: local_user }  │ DEPLOY_MODE│
│         │ ◀─────────────────────────────│ =local     │
│ → Show  │     (no login needed)         └────────────┘
│   chat  │
└─────────┘

CLOUD MODE:
┌─────────┐     GET /api/v1/auth/me       ┌────────────┐
│ Web SPA │ ─────────────────────────────▶│ API Server │
│         │     401 Unauthorized          │ DEPLOY_MODE│
│         │ ◀─────────────────────────────│ =cloud     │
│ → Show  │                               └────────────┘
│   login │     POST /api/v1/auth/login
│   page  │ ─────────────────────────────▶
│         │     200 { token: "jwt..." }
│         │ ◀─────────────────────────────
│ → Store │
│   token │
│ → Show  │
│   chat  │
└─────────┘
```

Frontend chỉ cần 1 logic:
```typescript
// On app init
const me = await fetch('/api/v1/auth/me');
if (me.ok) {
  // Authenticated (local or cloud with valid token)
  showChat();
} else {
  // Need login (cloud mode)
  showLogin();
}
```

### 6.3 Enterprise Extension Point

Vì API Server là headless service, enterprise users có thể:

```
Option 1: Dùng built-in Web UI (SPA container)
    → Đủ cho hầu hết use cases

Option 2: Build custom frontend
    → Chỉ cần gọi REST + SSE endpoints
    → Auth via JWT token
    → API docs tại /docs (Swagger)
    
Option 3: Integrate vào existing platform
    → Embed BrandMind API như microservice
    → Gọi qua internal network
    → Custom auth layer phía trước
```

---

## 7. Rủi Ro & Mitigation

| Rủi ro | Impact | Mitigation |
|--------|--------|------------|
| FastAPI API server thêm complexity | Medium | Giữ thin layer, delegate logic cho AgentService |
| SSE streaming qua reverse proxy | Low | Traefik/nginx hỗ trợ tốt SSE, cần config `proxy_buffering off` |
| tenant_id leak cross-tenant | High | **Luôn** extract tenant_id từ JWT (cloud), không tin client input |
| Local mode không test được auth | Medium | CI pipeline chạy test suite cho cả 2 mode |
| Web SPA framework choice | Low | Bất kỳ SPA framework nào cũng được, API-first design |

---

## 8. Kết Luận & Recommendation

### Recommendation: **Đồng ý với hướng của bạn, với refinements**

Ý tưởng ban đầu của bạn đã đúng hướng:
> *"Web local và web cloud đều host microservice lên luôn với 2 service BrandMind và Web UI, chỉ khác ở cách BrandMind work filesystem backend"*

Tôi refine thêm:

1. **Dùng `DEPLOY_MODE` env var** (inspired by Dify's `EDITION`) thay vì 2 Docker Compose file hoàn toàn khác nhau. Base compose + cloud override.

2. **Auth strategy pattern** thay vì if-else rải rác — 1 dependency injection point, LocalAuth vs CloudAuth.

3. **`tenant_id` pervasive từ đầu** — ngay cả local mode cũng dùng `tenant_id="local"`. Không bao giờ phải refactor schema sau này.

4. **Separate SPA container** (không embed vào FastAPI) — clean separation, CDN-ready, enterprise-friendly.

5. **Zero-trust chỉ bật cho cloud** — Local không cần API gateway, cloud thêm Traefik. Pragmatic, không over-engineer.

6. **TUI không thay đổi** — vẫn embedded agent, vẫn `brandmind` command. Chỉ thêm entry point mới cho API server.

### Next Steps ✅ CONFIRMED

1. ✅ **Thiết kế API contract** — Chat-focused endpoints, SSE streaming
2. **Extract `AgentService`** từ `inference.py` — Keep streaming logic, remove CLI-specific code
3. **Build FastAPI API server** (Phase 1):
   - `/api/v1/chat` (SSE streaming với thinking + answer)
   - `/api/v1/auth/me` (local bypass, cloud JWT)
   - Health check, CORS, rate limiting
4. **Chọn frontend framework**:
   - React + Vite (hoặc Next.js nếu cần SSR)
   - TypeScript cho type safety
   - TailwindCSS + shadcn/ui cho components
5. **Build minimal chat SPA**:
   - Chat input + message history
   - SSE event handling (thinking blocks, tool calls, streaming answer)
   - Session management
   - Responsive design (mobile-first)

---

*Document này cần được review và approve trước khi bắt đầu implementation.*
