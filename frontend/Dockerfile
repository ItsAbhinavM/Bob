# Multi-stage build for lightweight frontend image
# Stage 1: Builder
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install && \
    npm cache clean --force

# Copy source code
COPY . .

# Build Next.js app
RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Copy package files from builder
COPY --from=builder /app/package.json /app/package-lock.json* ./

# Copy node_modules from builder (only production deps)
COPY --from=builder /app/node_modules ./node_modules

# Copy built app from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Set environment variables
ENV NODE_ENV=production \
    NEXT_PUBLIC_API_URL=http://localhost:8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3001 || exit 1

# Expose port
EXPOSE 3001

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Run Next.js app
CMD ["npm", "start", "--", "-p", "3001"]
