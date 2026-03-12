# 实现计划：新建utils目录和工具函数

## Context

用户需要在项目根目录创建utils目录，并实现5个TypeScript工具函数（sum, sub, mul, div, sqrt）。根据约束，每个实现步骤只能完成一个工具函数。

## 目标

- 在项目根目录创建 `utils/` 目录
- 使用TypeScript实现5个数学工具函数
- 确保代码质量和类型安全

## 实现步骤

### 步骤1：创建utils目录和sum函数
- 创建 `utils/` 目录
- 创建 `utils/index.ts` 文件（导出入口）
- 创建 `utils/sum.ts` 文件，实现加法函数
- 函数签名：`function sum(a: number, b: number): number`

### 步骤2：实现sub函数
- 创建 `utils/sub.ts` 文件
- 实现减法函数
- 函数签名：`function sub(a: number, b: number): number`

### 步骤3：实现mul函数
- 创建 `utils/mul.ts` 文件
- 实现乘法函数
- 函数签名：`function mul(a: number, b: number): number`

### 步骤4：实现div函数
- 创建 `utils/div.ts` 文件
- 实现除法函数，需要处理除数为0的情况
- 函数签名：`function div(a: number, b: number): number`
- 错误处理：当除数为0时抛出错误或返回特定值

### 步骤5：实现sqrt函数
- 创建 `utils/sqrt.ts` 文件
- 实现平方根函数，需要处理负数情况
- 函数签名：`function sqrt(n: number): number`
- 错误处理：当输入为负数时抛出错误或返回NaN

### 步骤6：更新导出入口
- 在 `utils/index.ts` 中导出所有函数

## 关键文件

| 文件路径 | 说明 |
|---------|------|
| `utils/index.ts` | 统一导出入口 |
| `utils/sum.ts` | 加法函数 |
| `utils/sub.ts` | 减法函数 |
| `utils/mul.ts` | 乘法函数 |
| `utils/div.ts` | 除法函数 |
| `utils/sqrt.ts` | 平方根函数 |

## 验证方式

1. 检查每个文件是否正确创建
2. 使用TypeScript编译器检查类型是否正确：`tsc utils/*.ts --noEmit`
3. 可选：编写简单的测试用例验证函数功能

## 使用示例

```typescript
import { sum, sub, mul, div, sqrt } from './utils';

console.log(sum(1, 2));    // 3
console.log(sub(5, 3));    // 2
console.log(mul(4, 3));    // 12
console.log(div(10, 2));   // 5
console.log(sqrt(16));     // 4
```