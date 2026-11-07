# 数值数据与字体清单

- `audio.json`：原制作使用的节拍周期、相位、节拍／小节时间、响度曲线与分析结果；不含音频样本、歌词或账户信息。复制到 `work/analysis/audio.json` 可保留原片的歌曲时间基准。
- `fonts.json`：制作目录中 Google Fonts 字体的文件名和官方下载地址，由 `src/tools/fetch_fonts.py` 读取；字体本体不进入 Git。

逐字歌词数据仍在本地生成：自备 `input/lyrics.ass` 与 `work/analysis/lyrics_ja.txt`，运行 `src/analysis/lyric_timing.py`。详细输入约束见 [制作流程](../docs/制作流程.md#环境与输入)。
