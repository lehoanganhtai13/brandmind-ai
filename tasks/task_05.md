# Task 05: Refactor `core` with Optional Dependencies

## 📌 Metadata

- **Epic**: Core Architecture & Tooling
- **Priority**: High
- **Estimated Effort**: 1-2 days
- **Team**: Backend/Full-stack
- **Related Tasks**: Task 04: Refactor Project into a Standard Installable Package

### ✅ Progress Checklist

- [ ] 🎯 [Context & Goals](#🎯-context--goals) - Problem definition and success metrics
- [ ] 🛠 [Solution Design](#🛠-solution-design) - Architecture and technical approach
- [ ] 🔄 [Implementation Plan](#🔄-implementation-plan) - Detailed execution phases
- [ ] 📋 [Implementation Detail](#📋-implementation-detail) - Component requirements
    - [x] ✅ [Component 1](#component-1) - `Makefile` Enhancement
    - [x] ✅ [Component 2](#component-2) - Dependency Refactoring via `make`
    - [x] ✅ [Component 3](#component-3) - Final Configuration & Verification- [ ] 🧪 [Test Cases](#🧪-test-cases) - Manual test cases and validation
- [ ] 📝 [Task Summary](#📝-task-summary) - Final implementation summary

## 🔗 Reference Documentation

- **uv `add` command**: [uv Docs](https://docs.astral.sh/uv/commands/uv-add/)
- **uv `remove` command**: [uv Docs](https://docs.astral.sh/uv/commands/uv-remove/)
- **PEP 621 - Optional Dependencies**: [PEP 621](https://peps.python.org/pep-0621/#optional-dependencies)

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- The `core` package contains multiple components, but not all services that use `core` need the dependencies for every single component.
- Currently, dependencies for `core`'s components (like `llama-cloud-services`) are declared in the top-level service groups (e.g., `indexer`), which violates the principle of encapsulation and makes dependency management brittle.
- This approach can lead to dependency bloat for services that only need a subset of `core`'s functionality.

### Mục tiêu

Refactor the `core` package to use **Optional Dependencies**. This will allow services to install `core` along with only the specific extra dependencies required for the features they use, making the dependency graph cleaner, more modular, and easier to maintain.

### Success Metrics / Acceptance Criteria

- **Modular Dependencies**: The `core` package defines its own optional dependencies (e.g., for `document_processing`).
- **Clean Service Definitions**: The `indexer` service group in the root `pyproject.toml` depends on `core[document_processing]` instead of declaring `llama-cloud-services` directly.
- **Automated Management**: New `Makefile` targets (`add-core-optional`, `remove-indexer`) allow for easy management of these dependencies.
- **Successful Installation**: `make install-all` runs successfully after the refactoring, correctly installing all required base and optional dependencies.
- **No Regressions**: All application functionality (CLI, tests) works as expected after the changes.

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**Automated Refactoring via `uv` and `Makefile`**: Instead of manually editing `pyproject.toml` files, we will leverage `uv`'s capabilities through new `Makefile` targets to perform the dependency migration.

1.  **Enhance `Makefile`**: Add new targets (`add-core-optional`, `remove-indexer`) to programmatically add/remove dependencies from specific packages and groups.
2.  **Execute Migration**: Use the new `make` targets to remove `llama-cloud-services` from the `indexer` group and add it, along with `beautifulsoup4`, to a new `document_processing` optional dependency group within the `core` package. `uv` will handle version resolution and `pyproject.toml` modification.
3.  **Finalize Configuration**: Manually update the `indexer` group to depend on `core[document_processing]`.

### Stack công nghệ

- **`uv` CLI**: For its powerful dependency management features, including adding/removing packages from specific groups and workspaces.
- **`Makefile`**: To create a simple, repeatable, and high-level interface for complex `uv` commands.
- **`pyproject.toml` (Optional Dependencies)**: To declare the modular dependency groups within the `core` package.

### Issues & Solutions

1. **Challenge**: How to add a dependency to a new, non-existent optional group in a sub-package?
   → **Solution**: `uv add --package core --optional <group_name> <pkg_name>` automatically creates the `[project.optional-dependencies]` table and the specified group if they do not exist.
2. **Challenge**: How to ensure correct and compatible versions for new packages?
   → **Solution**: By using `uv add`, we delegate version resolution to `uv`, which finds the latest compatible version based on the existing dependency tree, avoiding manual version selection.

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Enhance `Makefile`**
1. **Add `add-core-optional` target**: This target will take `GROUP` and `PKG` as arguments to add a package to an optional dependency group in the `core` package.
2. **Add `remove-indexer` target**: This target will take `PKG` as an argument to remove a package from the `indexer` dependency group in the root `pyproject.toml`.

### **Phase 2: Execute Dependency Migration via `make`**
1. **Run `make remove-indexer`**: Execute `make remove-indexer PKG=llama-cloud-services` to remove the dependency from the top-level service group.
2. **Run `make add-core-optional` for `llama-cloud-services`**: Execute `make add-core-optional GROUP=document_processing PKG=llama-cloud-services` to add it to `core`'s optional dependencies.
3. **Run `make add-core-optional` for `beautifulsoup4`**: Execute `make add-core-optional GROUP=document_processing PKG=beautifulsoup4` to add the second dependency to the same group.

### **Phase 3: Finalize Configuration and Verify**
1. **Manually Edit Root `pyproject.toml`**: Change the `indexer` group to depend on `core[document_processing]`.
2. **Run `make install-all`**: To apply all changes and synchronize the virtual environment.
3. **Run Verification Tests**: Execute `make test` and `make parse-docs` to ensure no regressions were introduced.

------------------------------------------------------------------------

## 📋 Implementation Detail

### Component 1

#### Requirement 1 - `Makefile` Enhancement
- **Requirement**: Add `add-core-optional` and `remove-indexer` targets to the `Makefile`.
- **Implementation**:
  - `Makefile`
  ```makefile
  # Add to "Package Management" section
  add-core-optional: ## Add optional dependency to core. Usage: make add-core-optional GROUP=group_name PKG=package_name
	@if [ -z "$(PKG)" ] || [ -z "$(GROUP)" ]; then echo "Error: PKG and GROUP are required."; exit 1; fi
	uv add --package core --optional $(GROUP) $(PKG)

  remove-indexer: ## Remove package from indexer group. Usage: make remove-indexer PKG=package_name
	@if [ -z "$(PKG)" ]; then echo "Error: PKG is required."; exit 1; fi
	uv remove --group indexer $(PKG)
  ```
- **Acceptance Criteria**:
  - [ ] `Makefile` contains the new `add-core-optional` target.
  - [ ] `Makefile` contains the new `remove-indexer` target.

### Component 2

#### Requirement 1 - Dependency Refactoring via `make`
- **Requirement**: Use the new Makefile targets to migrate dependencies.
- **Execution Steps**:
  1. `make remove-indexer PKG=llama-cloud-services`
  2. `make add-core-optional GROUP=document_processing PKG=llama-cloud-services`
  3. `make add-core-optional GROUP=document_processing PKG=beautifulsoup4`
- **Acceptance Criteria**:
  - [ ] `llama-cloud-services` is removed from the `[dependency-groups.indexer]` table in the root `pyproject.toml`.
  - [ ] `src/core/pyproject.toml` now contains a `[project.optional-dependencies.document_processing]` table.
  - [ ] This new table contains `llama-cloud-services` and `beautifulsoup4` with `uv`-resolved versions.

### Component 3

#### Requirement 1 - Final Configuration & Verification
- **Requirement**: Update the `indexer` dependency group and verify the entire setup.
- **Implementation**:
  - Manually edit `pyproject.toml` (root):
    ```toml
    [dependency-groups]
    indexer = [
        "shared",
        "core[document_processing]",
    ]
    ```
  - Run `make install-all` to apply changes.
- **Acceptance Criteria**:
  - [ ] `dependency-groups.indexer` is correctly updated.
  - [ ] `make install-all` completes successfully.

------------------------------------------------------------------------

## 🧪 Test Cases

### Test Case 1: `Makefile` and Dependency Migration
- **Purpose**: Verify that the `make` commands correctly modify the `pyproject.toml` files.
- **Steps**:
  1. Run `make remove-indexer PKG=llama-cloud-services`.
  2. Check that `llama-cloud-services` is gone from `[dependency-groups.indexer]` in the root `pyproject.toml`.
  3. Run `make add-core-optional GROUP=document_processing PKG=llama-cloud-services`.
  4. Run `make add-core-optional GROUP=document_processing PKG=beautifulsoup4`.
  5. Check that `src/core/pyproject.toml` has the new `[project.optional-dependencies.document_processing]` group with both packages.
- **Expected Result**: All `pyproject.toml` files are modified as expected by the `uv` commands.
- **Status**: ✅ Passed

### Test Case 2: Final Installation
- **Purpose**: Verify that the new dependency structure with optional dependencies can be installed correctly.
- **Steps**:
  1. Manually update `dependency-groups.indexer` to use `core[document_processing]`.
  2. Run `make install-all`.
- **Expected Result**: The command completes successfully, installing `core`, `shared`, and the optional dependencies (`llama-cloud-services`, `beautifulsoup4`).
- **Status**: ✅ Passed

### Test Case 3: Regression Testing
- **Purpose**: Verify that the application still functions correctly after the dependency refactoring.
- **Steps**:
  1. Run `make parse-docs`.
  2. Run `make test`.
- **Expected Result**: Both the CLI and all automated tests pass without errors.
- **Status**: ✅ Passed

------------------------------------------------------------------------

## 📝 Task Summary

### What Was Implemented

- [x] ✅ **Component 1**: `Makefile` Enhancement
- [x] ✅ **Component 2**: Dependency Refactoring via `make`
- [x] ✅ **Component 3**: Final Configuration & Verification

### Files Created/Modified**:
```
Makefile              # Added add-core-optional, remove-indexer targets
pyproject.toml        # Updated [dependency-groups.indexer] to use core[document_processing]
src/core/pyproject.toml # Added [project.optional-dependencies] with document_processing group
```

### Technical Highlights

**Architecture Decisions**:
- **Adopted Optional Dependencies**: Refactored the `core` package to use optional dependency groups (`core[document_processing]`), allowing consumer services to install only the features they need. This improves modularity and reduces dependency bloat.
- **Automated Dependency Management**: Leveraged `uv` through new `Makefile` targets (`add-core-optional`, `remove-indexer`) to programmatically manage dependencies, ensuring consistency and reliable version resolution. This avoids manual editing of `pyproject.toml` files for adding/removing packages.

**Result**: The project's dependency architecture is now significantly more robust, modular, and maintainable, adhering to modern Python packaging best practices. ✅