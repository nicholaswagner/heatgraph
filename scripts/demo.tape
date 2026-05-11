Output images/game-of-life-example.gif
Set FontFamily "Dank Mono"
Set FontSize 13
Set Width 640
Set Height 480
Set WindowBar Colorful
Set BorderRadius 10
Set Framerate 15

Require uv

Sleep 1s
Escape
Type "~uv run heatgraph-helpers game-of-life --seed 42 | heatgraph --glyphs terminal --follow"
Sleep 500ms
Enter
Sleep 5s
Screenshot ./images/game-of-life.png
Sleep 25s
Ctrl+C

