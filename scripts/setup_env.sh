#!/bin/bash
# Interactive environment setup script for BrandMind AI
# Creates environments/.env with user input or defaults from template

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$PROJECT_ROOT/environments/.template.env"
OUTPUT_FILE="$PROJECT_ROOT/environments/.env"
EXPORT_FILE="$PROJECT_ROOT/environments/.env.export"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║           BrandMind AI - Environment Setup                 ║${NC}"
echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if template exists
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo -e "${RED}Error: Template file not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

# Check if .env already exists
if [[ -f "$OUTPUT_FILE" ]]; then
    echo -e "${YELLOW}Warning: $OUTPUT_FILE already exists.${NC}"
    read -p "Do you want to overwrite it? [y/N]: " -r REPLY </dev/tty
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Aborted. Existing .env file preserved.${NC}"
        exit 0
    fi
    echo ""
fi

echo -e "${BOLD}Press Enter to use default values shown in [brackets].${NC}"
echo -e "${BOLD}Required fields are marked with ${RED}*${NC}${BOLD}.${NC}"
echo ""

# Helper function to get description for a variable
get_description() {
    case "$1" in
        GEMINI_API_KEY) echo "Google Gemini API key for LLM (get from https://aistudio.google.com)" ;;
        LLAMA_PARSE_API_KEY) echo "LlamaParse API key for PDF parsing (optional, get from https://cloud.llamaindex.ai)" ;;
        EMBEDDING_DIM) echo "Embedding dimension" ;;
        MINIO_ACCESS_KEY_ID) echo "MinIO access key" ;;
        MINIO_SECRET_ACCESS_KEY) echo "MinIO secret key" ;;
        MINIO_PORT) echo "MinIO API port" ;;
        MINIO_CONSOLE_PORT) echo "MinIO console port" ;;
        MILVUS_HOST) echo "Milvus host" ;;
        MILVUS_PORT) echo "Milvus port" ;;
        MILVUS_ROOT_PASSWORD) echo "Milvus root password" ;;
        FALKORDB_HOST) echo "FalkorDB host" ;;
        FALKORDB_PORT) echo "FalkorDB port" ;;
        FALKORDB_USERNAME) echo "FalkorDB username" ;;
        FALKORDB_PASSWORD) echo "FalkorDB password" ;;
        FALKORDB_GRAPH_NAME) echo "FalkorDB graph name" ;;
        COLLECTION_DOCUMENT_CHUNKS) echo "Milvus collection for document chunks" ;;
        COLLECTION_ENTITY_DESCRIPTIONS) echo "Milvus collection for entity descriptions" ;;
        COLLECTION_RELATION_DESCRIPTIONS) echo "Milvus collection for relation descriptions" ;;
        *) echo "$1" ;;
    esac
}

# Check if variable is required
is_required() {
    case "$1" in
        GEMINI_API_KEY) return 0 ;;
        *) return 1 ;;
    esac
}

# Check if variable is optional (can be empty)
is_optional() {
    case "$1" in
        LLAMA_PARSE_API_KEY) return 0 ;;
        *) return 1 ;;
    esac
}

# Print section header
print_section() {
    local section="$1"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  $section${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
}

# First pass: collect all variables from template
declare -a VAR_NAMES
declare -a VAR_DEFAULTS

while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    
    # Parse VAR=value
    if [[ "$line" =~ ^([A-Z_]+)=(.*)$ ]]; then
        VAR_NAMES+=("${BASH_REMATCH[1]}")
        VAR_DEFAULTS+=("${BASH_REMATCH[2]}")
    fi
done < "$TEMPLATE_FILE"

# Temporary file to store results
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Second pass: prompt for each variable
last_section=""
for i in "${!VAR_NAMES[@]}"; do
    var_name="${VAR_NAMES[$i]}"
    default_value="${VAR_DEFAULTS[$i]}"
    description=$(get_description "$var_name")
    
    # Determine section based on variable name
    case "$var_name" in
        GEMINI_API_KEY|LLAMA_PARSE_API_KEY)
            section="🔑 API Keys"
            ;;
        EMBEDDING_DIM)
            section="📊 Embedding Configuration"
            ;;
        MINIO_*)
            section="📦 MinIO (Object Storage)"
            ;;
        MILVUS_*)
            section="🔍 Milvus (Vector Database)"
            ;;
        FALKORDB_*)
            section="🕸️ FalkorDB (Graph Database)"
            ;;
        COLLECTION_*)
            section="📚 Vector Database Collections"
            ;;
        *)
            section=""
            ;;
    esac
    
    # Print section header if changed
    if [[ "$section" != "$last_section" ]] && [[ -n "$section" ]]; then
        print_section "$section"
        last_section="$section"
    fi
    
    # Display prompt
    if is_required "$var_name"; then
        echo -e "\n${BOLD}$var_name${NC} ${RED}*${NC}"
    else
        echo -e "\n${BOLD}$var_name${NC}"
    fi
    echo -e "${CYAN}$description${NC}"
    
    # Handle display of default value
    display_default="$default_value"
    if [[ "$var_name" == *"PASSWORD"* ]] || [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"API_KEY"* ]]; then
        if [[ "$default_value" != "your-"* ]] && [[ -n "$default_value" ]]; then
            display_default="********"
        fi
    fi
    
    # Prompt user - read from /dev/tty to avoid stdin conflicts
    if [[ "$default_value" == "your-"* ]] || [[ -z "$default_value" ]]; then
        read -p "Enter value: " user_input </dev/tty
    else
        read -p "Enter value [$display_default]: " user_input </dev/tty
    fi
    
    # Determine final value
    if [[ -z "$user_input" ]]; then
        if is_required "$var_name" && ([[ "$default_value" == "your-"* ]] || [[ -z "$default_value" ]]); then
            echo -e "${RED}Error: $var_name is required and cannot be empty.${NC}"
            echo ""
            echo -e "${RED}Setup aborted. No .env file was created.${NC}"
            exit 1
        fi
        if is_optional "$var_name" && ([[ "$default_value" == "your-"* ]] || [[ -z "$default_value" ]]); then
            final_value=""
        else
            final_value="$default_value"
        fi
    else
        final_value="$user_input"
    fi
    
    # Store in temp file
    echo "${var_name}=${final_value}" >> "$TEMP_FILE"
done

# Write .env file
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Creating .env file...${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

{
    echo "# BrandMind AI Environment Configuration"
    echo "# Generated by: make setup-env"
    echo "# Generated at: $(date)"
    echo ""
    
    prev_section=""
    while IFS='=' read -r var_name value; do
        # Add section comments
        case "$var_name" in
            GEMINI_API_KEY)
                echo "# API Keys"
                ;;
            EMBEDDING_DIM)
                echo ""
                echo "# Embedding Configuration"
                ;;
            MINIO_ACCESS_KEY_ID)
                echo ""
                echo "# MinIO (Object Storage)"
                ;;
            MILVUS_HOST)
                echo ""
                echo "# Milvus (Vector Database)"
                ;;
            FALKORDB_HOST)
                echo ""
                echo "# FalkorDB (Graph Database)"
                ;;
            COLLECTION_DOCUMENT_CHUNKS)
                echo ""
                echo "# Vector Database Collections"
                ;;
        esac
        
        echo "${var_name}=${value}"
    done < "$TEMP_FILE"
} > "$OUTPUT_FILE"

echo -e "${GREEN}✅ Created: $OUTPUT_FILE${NC}"

# Create export file
{
    echo "# Source this file to export env vars: source environments/.env.export"
    while IFS='=' read -r var_name value; do
        # Escape special characters for shell
        escaped_value="${value//\\/\\\\}"
        escaped_value="${escaped_value//\"/\\\"}"
        echo "export ${var_name}=\"${escaped_value}\""
    done < "$TEMP_FILE"
} > "$EXPORT_FILE"

echo -e "${GREEN}✅ Created: $EXPORT_FILE${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ✨ Setup Complete!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "To load environment variables in your current shell:"
echo -e "  ${YELLOW}source environments/.env.export${NC}"
echo ""
echo -e "Next steps:"
echo -e "  ${GREEN}1.${NC} source environments/.env.export"
echo -e "  ${GREEN}2.${NC} make services-up"
echo -e "  ${GREEN}3.${NC} make restore-package"
echo -e "  ${GREEN}4.${NC} brandmind"
echo ""
