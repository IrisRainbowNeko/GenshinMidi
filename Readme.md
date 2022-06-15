# 自动生成乐谱
首先使用 [MT3](https://github.com/magenta/mt3) 将mp3转换成Midi格式的音频 (可以使用colab在线运行，需要vpn)

运行 **midi_proc.py** 将midi转换成可以防止的脚步。

在 **管理员模式** 的命令行下， 运行 **plot_script.py** 摆放音符，节拍选择1/6。

如果转换的音乐和游戏内时间轴有偏差可以添加参数 --offset <tick> 修正时间轴，单位是做谱器的格子

# 自动演奏
在 **管理员模式** 的命令行下，运行以下代码，速度设置为1.25倍
```bash
# 默认分辨率为2k (2560x1440)
python auto_play.py --width <屏幕分辨率-宽> --height <屏幕分辨率-高>
```
按**t**开始，按**q**退出