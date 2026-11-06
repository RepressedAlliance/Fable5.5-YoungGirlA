# Fable5.5-YoungGirlA

镜音铃《少女A》的同人视频工程。构思、分镜、代码、3D 场景和合成由 Claude Code 完成，人物图由 Codex 依据一张人设图生成。

**关于模型：** 项目名是作者定的。这次制作的运行记录显示，所用模型为 Claude Opus 5.5。

方案名叫《谁是少女A》：所有人都在谈论代号“少女A”，没有人关心她本人。她自己擦掉眼睛上的黑条，颜色从眼睛亮开，最后划掉“少女A”，写下自己的名字。

## 怎么做的

| 部分 | 做法 | 代码 |
|---|---|---|
| 2D 段落 | Skia 合成，Codex 图片连续换张形成动态 | `src/clips/`、`src/engine.py` |
| 3D 场景 | Blender Cycles 只输出数据通道 | `src/three/` |
| 上色 | 平涂、硬边阴影、世界坐标墨线，可在显卡上运行 | `src/npr/` |
| 日文排版 | 量好再放，支持竖排和禁则 | `src/typo/` |
| 人物图 | Codex 带人设图生成，提示词见 `work/gen/prompts.py` | `src/tools/codex_gen.py`、`src/art/` |
| 全片合成 | 按帧表渲染各段并拼接 | `src/make_full.py`、`src/assemble_full.py` |

设计过程在 `docs/`：需求是 `需求_完整版.md`，方案是 `新方案_谁是少女A.md`，分镜是 `全片分镜.md`。`问题根因清单.md` 记录了制作中每个问题的成因和全片排查项。

## 复现

仓库不含歌曲、歌词数据、字体和成片，需要自备：

- `input/song.mp4`：歌曲音频，请自行合法取得。
- `work/analysis/lyrics_timed.json`：带时间的歌词，由 `src/analysis/lyric_timing.py` 生成。
- `assets/fonts/ttf/`：代码引用的 Google Fonts 字体，如 BIZ UDPMincho、Shippori Mincho、Klee One。
- Blender 5.2；Python 依赖按报错安装，显卡上色另需带 CUDA 的 PyTorch。

```bash
python src/make_full.py
```

结果在 `out/少女A_full.mp4`。部分路径是按作者的 Windows 环境写的，例如 `src/three/pipeline.py` 里的 Blender 路径，使用前要改。这是一个作品的工程记录，不是通用工具，也不保证开箱即用。

## 权利

- **代码：** MIT，见 `LICENSE`。
- **本仓库的图片和文档：** CC BY-NC 4.0。
- **镜音铃：** 角色权利属于 Crypton Future Media, INC.，本作依 [Piapro Character License](https://piapro.net/intl/license.html) 以非商业同人形式制作。
- **《少女A》：** 作词作曲 椎名もた，本仓库不包含这首歌的音频，代码和文档中只有为对应画面引用的少量歌词片段。

这是非官方同人作品，与上述权利方无关。
