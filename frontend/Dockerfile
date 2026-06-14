# Stage 1: Dependencies
FROM node:20-alpine AS deps
# Add libc6-compat for compatibility with native node packages
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package descriptors and install clean dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Accept build arguments and expose them as environment variables during build
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Disable telemetry during build to speed up compilation
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Configure non-root system user & group for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy public directory and static assets
COPY --from=builder /app/public ./public

# Setup directories with correct permissions for Next.js caching
RUN mkdir .next && chown nextjs:nodejs .next

# Leverage output traces to copy Next.js standalone server and static chunks
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to nextjs user
USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Execute Next.js standalone entrypoint
CMD ["node", "server.js"]
