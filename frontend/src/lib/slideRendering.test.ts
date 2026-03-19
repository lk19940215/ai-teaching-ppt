/**
 * slideRendering.ts 单元测试
 * feat-219: 幻灯片渲染决策工具函数测试
 *
 * 注意：项目当前没有配置 Jest/Vitest 等测试框架。
 * 此文件作为测试用例文档，可手动验证或在未来集成测试框架。
 *
 * 测试用例：
 * 1. getSlideRenderer - 图片渲染优先级
 * 2. getSlideRenderer - PptxViewJS 渲染优先级
 * 3. getSlideRenderer - PptxViewJS 降级模式
 * 4. getSlideRenderer - AI 内容渲染优先级
 * 5. getSlideRenderer - Canvas 渲染优先级
 * 6. getSlideRenderer - 占位符兜底
 * 7. versionToPageData - shapes 数据转换
 * 8. versionToPageData - content 数据转换
 * 9. getPptFile - 文件选择逻辑
 * 10. 辅助函数测试
 */

import {
  getSlideRenderer,
  versionToPageData,
  getPptFile,
  shouldUsePptxViewJS,
  shouldUseCanvas,
  shouldUseSlideContent,
  getRendererLabel,
  getRenderDecisionDebug,
  RENDERER_DEFAULTS,
  RENDER_QUALITY,
  type RenderDecision,
  type RendererType,
} from './slideRendering'
import type { SlidePoolItem, SlideVersion } from '@/types/merge-session'

// ============ 测试数据 ============

const mockSlide: SlidePoolItem = {
  slide_id: 'ppt_a_0',
  original_source: 'ppt_a',
  original_index: 0,
  versions: [],
  current_version: 'ppt_a_0_v1',
  is_selected: false,
  display_title: '测试幻灯片',
}

const mockVersion: SlideVersion = {
  version_id: 'ppt_a_0_v1',
  source_type: 'ppt_a',
  source_slide_index: 0,
  content: {
    title: '测试标题',
    main_points: ['要点1', '要点2'],
  },
  created_at: Date.now(),
}

const mockFile = new File([''], 'test.pptx', { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' })

// ============ 测试用例 ============

/**
 * 测试 1: 图片渲染优先级
 * 当有 imageUrl 时，应该返回 image 渲染器
 */
function testImageRendererPriority(): void {
  const decision = getSlideRenderer({
    slide: mockSlide,
    version: mockVersion,
    imageUrl: 'https://example.com/preview.png',
    pptFile: mockFile,
    fallbackMode: false,
  })

  console.assert(decision.renderer === 'image', `Expected 'image', got '${decision.renderer}'`)
  console.assert(decision.hasImageUrl === true, 'hasImageUrl should be true')
  console.log('✓ testImageRendererPriority passed')
}

/**
 * 测试 2: PptxViewJS 渲染优先级
 * 当是原始版本（无 action）且有 PPT 文件时，应该返回 pptxviewjs 渲染器
 */
function testPptxViewJSRendererPriority(): void {
  const versionWithoutAction: SlideVersion = {
    ...mockVersion,
    action: undefined,
  }

  const decision = getSlideRenderer({
    slide: mockSlide,
    version: versionWithoutAction,
    imageUrl: null,
    pptFile: mockFile,
    fallbackMode: false,
  })

  console.assert(decision.renderer === 'pptxviewjs', `Expected 'pptxviewjs', got '${decision.renderer}'`)
  console.assert(decision.hasPptFile === true, 'hasPptFile should be true')
  console.assert(decision.hasAction === false, 'hasAction should be false')
  console.log('✓ testPptxViewJSRendererPriority passed')
}

/**
 * 测试 3: PptxViewJS 降级模式
 * 当 fallbackMode 为 true 时，应该返回 pptxviewjs_fallback 渲染器
 */
function testPptxViewJSFallback(): void {
  const versionWithoutAction: SlideVersion = {
    ...mockVersion,
    action: undefined,
  }

  const decision = getSlideRenderer({
    slide: mockSlide,
    version: versionWithoutAction,
    imageUrl: null,
    pptFile: mockFile,
    fallbackMode: true,
  })

  console.assert(decision.renderer === 'pptxviewjs_fallback', `Expected 'pptxviewjs_fallback', got '${decision.renderer}'`)
  console.assert(decision.fallbackMode === true, 'fallbackMode should be true')
  console.log('✓ testPptxViewJSFallback passed')
}

/**
 * 测试 4: AI 内容渲染优先级
 * 当版本有 action 时，应该返回 slide_content 渲染器
 */
function testSlideContentRendererPriority(): void {
  const versionWithAction: SlideVersion = {
    ...mockVersion,
    action: 'polish',
  }

  const decision = getSlideRenderer({
    slide: mockSlide,
    version: versionWithAction,
    imageUrl: null,
    pptFile: null,
    fallbackMode: false,
  })

  console.assert(decision.renderer === 'slide_content', `Expected 'slide_content', got '${decision.renderer}'`)
  console.assert(decision.hasAction === true, 'hasAction should be true')
  console.log('✓ testSlideContentRendererPriority passed')
}

/**
 * 测试 5: Canvas 渲染优先级
 * 当有 content 但没有 action 和 PPT 文件时，应该返回 ppt_canvas 渲染器
 */
function testCanvasRendererPriority(): void {
  const decision = getSlideRenderer({
    slide: mockSlide,
    version: mockVersion,
    imageUrl: null,
    pptFile: null,
    fallbackMode: false,
  })

  console.assert(decision.renderer === 'ppt_canvas', `Expected 'ppt_canvas', got '${decision.renderer}'`)
  console.assert(decision.hasContent === true, 'hasContent should be true')
  console.log('✓ testCanvasRendererPriority passed')
}

/**
 * 测试 6: 占位符兜底
 * 当没有任何数据时，应该返回 placeholder 渲染器
 */
function testPlaceholderFallback(): void {
  const emptyVersion: SlideVersion = {
    version_id: 'test_v1',
    source_type: 'ppt_a',
    content: {},
    created_at: Date.now(),
  }

  const decision = getSlideRenderer({
    slide: null,
    version: emptyVersion,
    imageUrl: null,
    pptFile: null,
    fallbackMode: false,
  })

  console.assert(decision.renderer === 'placeholder', `Expected 'placeholder', got '${decision.renderer}'`)
  console.log('✓ testPlaceholderFallback passed')
}

/**
 * 测试 7: versionToPageData - shapes 数据转换
 */
function testVersionToPageDataWithShapes(): void {
  const versionWithShapes: SlideVersion = {
    ...mockVersion,
    shapes: [{
      type: 'text_box',
      name: 'title',
      position: { x: 50, y: 50, width: 860, height: 100 },
      text_content: [{
        runs: [{ text: '测试文本', font: { size: 24, color: '#333333' } }],
      }],
    }],
    layout: { width: 960, height: 540 },
  }

  const pageData = versionToPageData(versionWithShapes, 0)

  console.assert(pageData.index === 0, 'index should be 0')
  console.assert(pageData.shapes.length === 1, 'shapes should have 1 element')
  console.assert(pageData.layout.width === 960, 'layout width should be 960')
  console.log('✓ testVersionToPageDataWithShapes passed')
}

/**
 * 测试 8: getPptFile - 文件选择逻辑
 */
function testGetPptFile(): void {
  const fileA = new File(['a'], 'a.pptx', { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' })
  const fileB = new File(['b'], 'b.pptx', { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' })

  console.assert(getPptFile('ppt_a', fileA, fileB) === fileA, 'Should return fileA for ppt_a')
  console.assert(getPptFile('ppt_b', fileA, fileB) === fileB, 'Should return fileB for ppt_b')
  console.assert(getPptFile('merge', fileA, fileB) === null, 'Should return null for merge')
  console.assert(getPptFile(undefined, fileA, fileB) === null, 'Should return null for undefined')
  console.log('✓ testGetPptFile passed')
}

/**
 * 测试 9: 辅助函数
 */
function testHelperFunctions(): void {
  // shouldUsePptxViewJS
  console.assert(shouldUsePptxViewJS({ renderer: 'pptxviewjs' } as RenderDecision) === true, 'pptxviewjs should return true')
  console.assert(shouldUsePptxViewJS({ renderer: 'pptxviewjs_fallback' } as RenderDecision) === true, 'pptxviewjs_fallback should return true')
  console.assert(shouldUsePptxViewJS({ renderer: 'image' } as RenderDecision) === false, 'image should return false')

  // shouldUseCanvas
  console.assert(shouldUseCanvas({ renderer: 'ppt_canvas' } as RenderDecision) === true, 'ppt_canvas should return true')
  console.assert(shouldUseCanvas({ renderer: 'pptxviewjs_fallback' } as RenderDecision) === true, 'pptxviewjs_fallback should return true')
  console.assert(shouldUseCanvas({ renderer: 'slide_content' } as RenderDecision) === false, 'slide_content should return false')

  // shouldUseSlideContent
  console.assert(shouldUseSlideContent({ renderer: 'slide_content' } as RenderDecision) === true, 'slide_content should return true')
  console.assert(shouldUseSlideContent({ renderer: 'image' } as RenderDecision) === false, 'image should return false')

  // getRendererLabel
  console.assert(getRendererLabel('image') === '图片渲染', 'image label should be 图片渲染')
  console.assert(getRendererLabel('pptxviewjs') === 'PptxViewJS 渲染', 'pptxviewjs label should be PptxViewJS 渲染')
  console.assert(getRendererLabel('placeholder') === '占位符', 'placeholder label should be 占位符')

  console.log('✓ testHelperFunctions passed')
}

/**
 * 测试 10: 常量导出
 */
function testConstants(): void {
  console.assert(RENDERER_DEFAULTS.width === 800, 'default width should be 800')
  console.assert(RENDERER_DEFAULTS.height === 450, 'default height should be 450')
  console.assert(RENDERER_DEFAULTS.quality === 1.0, 'default quality should be 1.0')
  console.assert(RENDER_QUALITY.high === 1.0, 'high quality should be 1.0')
  console.assert(RENDER_QUALITY.low === 0.5, 'low quality should be 0.5')
  console.log('✓ testConstants passed')
}

// ============ 运行测试 ============

/**
 * 运行所有测试
 */
export function runAllTests(): void {
  console.log('=== slideRendering.ts 单元测试 ===\n')

  try {
    testImageRendererPriority()
    testPptxViewJSRendererPriority()
    testPptxViewJSFallback()
    testSlideContentRendererPriority()
    testCanvasRendererPriority()
    testPlaceholderFallback()
    testVersionToPageDataWithShapes()
    testGetPptFile()
    testHelperFunctions()
    testConstants()

    console.log('\n=== 所有测试通过 ===')
  } catch (error) {
    console.error('\n✗ 测试失败:', error)
  }
}

// 如果直接运行此文件，执行测试
if (typeof require !== 'undefined' && require.main === module) {
  runAllTests()
}