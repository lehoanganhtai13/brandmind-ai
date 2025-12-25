# Dockerfile for milvus-backup
# Downloads pre-built binary instead of building from source
# Uses envsubst to substitute environment variables in config at runtime

FROM alpine:3.19

# Install runtime dependencies (gettext for envsubst)
RUN apk add --no-cache ca-certificates curl gettext

# Create app directory
WORKDIR /app

# Download pre-built milvus-backup binary from GitHub releases
# Using latest stable release
ARG MILVUS_BACKUP_VERSION=0.5.9
RUN curl -L -o milvus-backup.tar.gz \
    "https://github.com/zilliztech/milvus-backup/releases/download/v${MILVUS_BACKUP_VERSION}/milvus-backup_${MILVUS_BACKUP_VERSION}_Linux_x86_64.tar.gz" && \
    tar -xzf milvus-backup.tar.gz && \
    rm milvus-backup.tar.gz && \
    chmod +x milvus-backup

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create config and backup directories
RUN mkdir -p /app/configs /app/logs /backup

# Expose API port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8090/api/v1/list || exit 1

# Use entrypoint script to generate config then run server
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["server", "-p", "8090"]
