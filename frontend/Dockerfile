# Use ECR Public Gallery to avoid Docker Hub rate limits in CodeBuild
FROM public.ecr.aws/docker/library/node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
# Install dependencies for build (need dev dependencies for build)
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application with optimizations
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# OPTIMIZATION: Disable Next.js telemetry and analytics for faster startup
ENV DISABLE_OPENCOLLECTIVE=1

# Create nextjs user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy the built application and startup script
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --chown=nextjs:nodejs start.sh ./start.sh

# OPTIMIZATION: Pre-create cache directories to avoid runtime filesystem operations
RUN mkdir -p .next/cache && chown nextjs:nodejs .next/cache
RUN chmod +x start.sh

USER nextjs

EXPOSE 3000

# OPTIMIZATION: Use startup script for better logging
CMD ["./start.sh"]
