# 创建utils工具函数实现计划

## Context
用户需要在项目中新建utils目录，并创建5个基础数学工具函数。每个函数独立实现，便于管理和测试。

## 实现计划

### 步骤1：创建utils目录和sum函数
- 创建 `utils/` 目录
- 创建 `utils/sum.js` 文件
- 实现 `sum(a, b)` 函数：返回两个数的和

### 步骤2：实现sub函数
- 创建 `utils/sub.js` 文件
- 实现 `sub(a, b)` 函数：返回 a - b

### 步骤3：实现mul函数
- 创建 `utils/mul.js` 文件
- 实现 `mul(a, b)` 函数：返回 a * b

### 步骤4：实现div函数
- 创建 `utils/div.js` 文件
- 实现 `div(a, b)` 函数：返回 a / b（需处理除零情况）

### 步骤5：实现sqrt函数
- 创建 `utils/sqrt.js` 文件
- 实现 `sqrt(n)` 函数：返回平方根（需处理负数情况）

## 文件结构
```
utils/
├── sum.js
├── sub.js
├── mul.js
├── div.js
└── sqrt.js
```

## 验证方式
- 每个函数创建后，使用 node 命令测试功能是否正常