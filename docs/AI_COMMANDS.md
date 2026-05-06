# AI Commands

AI Command Panel supports offline Mock parsing for common Chinese commands:

- `把所有图层导出 512x512`
- `把当前选中图层导出 256、512、1024 三套尺寸`
- `把人物、武器、背景分别导出`
- `提取左边的人物`
- `提取右边的道具`
- `把 logo 单独抠出来`
- `把文字区域识别出来`
- `给所有导出的图层加 32 像素透明边距`
- `把角色图层重命名为 player_character`
- `批量导出 128、256、512 三套图标`
- `只导出可见图层`
- `导出背景图`
- `清理图层边缘白边`
- `优化透明边缘，减少锯齿`
- `按 PSD 分层思路导出素材包`
- `把所有图层导出成 UE UMG 可以用的资源`

The output is an `ImageEditPlan`; execution is handled by `CommandExecutor`.

