# FilesystemBackend Virtual Path Resolution Analysis

## Summary
Analysis of all FilesystemMiddleware tools to identify which ones properly handle virtual path resolution in `virtual_mode=True`.

## Tools Analysis

### ✅ **Working Tools** (Path properly resolved)

#### 1. `ls` (List Files)
- **Middleware**: Calls `_validate_path(path)` before passing to backend
- **Backend**: `ls_info(path)` calls `self._resolve_path(path)` ✅
- **Status**: **WORKS CORRECTLY**

#### 2. `read_file` (Read File)
- **Middleware**: Calls `_validate_path(file_path)` before passing to backend
- **Backend**: `read(file_path)` calls `self._resolve_path(file_path)` ✅
- **Status**: **WORKS CORRECTLY**

#### 3. `write_file` (Write File)
- **Middleware**: Calls `_validate_path(file_path)` before passing to backend
- **Backend**: `write(file_path)` calls `self._resolve_path(file_path)` ✅
- **Status**: **WORKS CORRECTLY**

#### 4. `edit_file` (Edit File)
- **Middleware**: Calls `_validate_path(file_path)` before passing to backend
- **Backend**: `edit(file_path)` calls `self._resolve_path(file_path)` ✅
- **Status**: **WORKS CORRECTLY**

#### 5. `glob` (Find Files by Pattern)
- **Middleware**: Does NOT validate pattern, but validates `path` parameter
- **Backend**: `glob_info(pattern, path)` 
  - Calls `self._resolve_path(path)` for search base ✅
  - Pattern is used directly with `rglob(pattern)` - but this is OK because:
    - Pattern is stripped of leading `/` if present
    - Used as relative pattern within resolved base path
- **Status**: **WORKS CORRECTLY** (pattern is relative, not a path)

---

### ❌ **BROKEN Tool** (Path NOT properly resolved)

#### 6. `grep` (Search File Contents)
- **Middleware**: Does NOT validate `glob` parameter (only validates `path` if provided)
- **Backend**: `grep_raw(pattern, path, glob)`
  - Calls `self._resolve_path(path or ".")` for base path ✅
  - **BUG**: `glob` parameter is passed directly to ripgrep WITHOUT resolution ❌
  
**Problem Code** (`_ripgrep_search` method):
```python
cmd = ["rg", "--json"]
if include_glob:
    cmd.extend(["--glob", include_glob])  # ❌ include_glob is virtual path!
cmd.extend(["--", pattern, str(base_full)])
```

**Example Failure**:
```python
# Agent calls:
grep(pattern="Part 1", glob="/page_*.md")

# What happens:
# 1. path=None → base_full = /real/path/to/document/folder ✅
# 2. glob="/page_*.md" → passed to ripgrep as-is ❌
# 3. ripgrep searches with --glob "/page_*.md" 
#    but this is a VIRTUAL path, not matching real filesystem!
# 4. Result: "No matches found" even though files exist
```

**Expected Behavior**:
```python
# glob should be resolved:
# Virtual: "/page_*.md"
# Real: "page_*.md" (relative to base_full)
```

---

## Root Cause

The `grep` tool's `glob` parameter needs the same treatment as other path parameters:
1. Strip leading `/` from virtual glob pattern
2. Use as relative pattern within resolved base path

**Fix Location**: `deepagents/backends/filesystem.py` in `_ripgrep_search()` method

**Suggested Fix**:
```python
def _ripgrep_search(self, pattern: str, base_full: Path, include_glob: str | None):
    cmd = ["rg", "--json"]
    if include_glob:
        # Strip leading / from virtual glob pattern
        if include_glob.startswith("/"):
            include_glob = include_glob.lstrip("/")
        cmd.extend(["--glob", include_glob])
    cmd.extend(["--", pattern, str(base_full)])
    # ... rest of implementation
```

---

## Impact

**Affected**: Document Cartographer agent
- Agent cannot use `grep` tool to search across multiple files with glob patterns
- Forces agent to use less efficient `line_search` on individual files
- Causes "No matches found" errors in logs (messages 40-43 in cartographer logs)

**Workaround**: Create `grep_wrapper` in `agent_config.py` similar to `line_search_wrapper` to resolve glob patterns before calling grep.

---

## Recommendation

1. **Short-term**: Implement `grep_wrapper` in our codebase
2. **Long-term**: Report bug to deepagents maintainers
3. **Testing**: Add test case for `grep` with virtual glob patterns
