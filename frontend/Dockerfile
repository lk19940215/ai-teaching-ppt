FROM node:20-alpine AS base

# 安装 pnpm
RUN npm install -g pnpm

WORKDIR /app

# 复制依赖文件
COPY package.json pnpm-lock.yaml* ./

# 安装依赖
RUN pnpm install

# 复制源代码
COPY . .

# 构建应用
RUN pnpm build

# 生产阶段
FROM node:20-alpine AS production
WORKDIR /app

ENV NODE_ENV production

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖和构建产物
COPY --from=base /app/package.json /app/pnpm-lock.yaml ./
COPY --from=base /app/node_modules ./node_modules
COPY --from=base /app/.next ./.next
COPY --from=base /app/public ./public

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["pnpm", "start"]