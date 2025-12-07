import cv2
import numpy as np
import os

# 1. 读取截图
if not os.path.exists("screen.png"):
    print("❌ 找不到 screen.png，请先运行 game_bot.py 截一张图！")
    exit()

img = cv2.imread("screen.png")

# 为了防止 1920 高度的图片超出你的电脑屏幕，我们缩小一半来显示
# (放心，计算时会自动乘回去，保证精度)
scale_factor = 0.5 
display_img = cv2.resize(img, (0, 0), fx=scale_factor, fy=scale_factor)

print("\n" + "="*50)
print("【校准模式】")
print("请在弹出的图片窗口中，依次点击以下两个点：")
print("👉 1. 左上角第一个格子(0,0) 的【正中心】")
print("👉 2. 右下角最后一个格子(6,6) 的【正中心】")
print("="*50 + "\n")

points = []

def get_pos(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # 把缩小的坐标还原回 1080p
        real_x = int(x / scale_factor)
        real_y = int(y / scale_factor)
        points.append((real_x, real_y))
        
        print(f"✅ 捕获点 {len(points)}: ({real_x}, {real_y})")
        
        # 在图上画个圈标记一下
        cv2.circle(display_img, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow("CALIBRATION", display_img)

        # 两个点都点完后，自动计算
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            
            # 计算逻辑：两个中心点之间隔了6个格子
            grid_w = (x2 - x1) // 6
            grid_h = (y2 - y1) // 6
            
            # 推算边缘：中心点减去半个格子的宽度
            left_start = x1 - (grid_w // 2)
            top_start  = y1 - (grid_h // 2)
            
            print("\n" + "👇👇👇 成功！请直接复制下面的代码覆盖 game_bot.py 的配置区域 👇👇👇")
            print("-" * 40)
            print(f"# === 自动校准生成的配置 ===")
            print(f"GRID_WIDTH  = {grid_w}")
            print(f"GRID_HEIGHT = {grid_h}")
            print(f"GRID_LEFT_X = {left_start}")
            print(f"GRID_TOP_Y  = {top_start}")
            print("-" * 40)
            print("\n按任意键退出...")

cv2.namedWindow("CALIBRATION")
cv2.setMouseCallback("CALIBRATION", get_pos)
cv2.imshow("CALIBRATION", display_img)
cv2.waitKey(0)
cv2.destroyAllWindows()