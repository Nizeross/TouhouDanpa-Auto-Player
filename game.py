import cv2
import numpy as np
import subprocess
import time
import random
import os

# ==========================================
# 【=== 1. 核心配置区域 (已根据截图修正) ===】
# ==========================================

ADB_PATH = r"C:\Program Files\Netease\MuMu\nx_main\adb.exe"  # 确保 adb.exe 在同目录下，或者填完整路径

# --- A. 网格位置 (基于 720x1280 分辨率估算) ---
GRID_WIDTH  = 112
GRID_HEIGHT = 112
GRID_LEFT_X = 146
GRID_TOP_Y  = 568

# --- B. 按钮位置 (修正) ---
# 假设分辨率宽 720，高 1280
# 底部按钮的 Y 坐标大概在 1050 左右
BTN_Y_ROW = 1468 

BTN_SKILL_1 = (200, BTN_Y_ROW) # 技能1 (竖线)
BTN_SKILL_2 = (305, BTN_Y_ROW) # 技能2 (三点)
BTN_SKILL_3 = (400, BTN_Y_ROW) # 技能3 (阴阳玉)
BTN_MOVE    = (500, BTN_Y_ROW) # 移动 (十字箭头)
BTN_NEXT    = (700, BTN_Y_ROW) # 下一回合 (快进)

# 🟢 关键修改：绿色对勾按钮的坐标
# 它在最右侧，和其他按钮同一行
BTN_CONFIRM = (800, 1476) # ✅ 修正为截图右下角位置

# ==========================================
# 【=== 2. 工具函数 ===】
# ==========================================

def run_adb(cmd):
    full_cmd = f'"{ADB_PATH}" {cmd}'
    subprocess.run(full_cmd, shell=True)

def get_screenshot():
    run_adb("shell screencap -p /sdcard/screen.png")
    run_adb("pull /sdcard/screen.png .")
    if not os.path.exists("screen.png"):
        return None
    return cv2.imread("screen.png")

def tap(x, y):
    run_adb(f"shell input tap {x} {y}")
    print(f"👉 点击: ({x}, {y})")

def get_grid_center(row, col):
    """根据行列计算屏幕坐标"""
    cx = GRID_LEFT_X + (col * GRID_WIDTH) + (GRID_WIDTH // 2)
    cy = GRID_TOP_Y + (row * GRID_HEIGHT) + (GRID_HEIGHT // 2)
    return cx, cy

def scan_grid(image):
    """
    视觉识别系统
    0: 未知/敌人
    1: 空地
    3: 玩家
    """
    board = np.zeros((7, 7), dtype=int)
    player_pos = None

    for r in range(7):
        for c in range(7):
            cx, cy = get_grid_center(r, c)
            
            # 越界保护
            if cy >= image.shape[0] or cx >= image.shape[1]:
                continue

            # 获取颜色 (BGR格式)
            b, g, red_val = image[cy, cx]
            
            # === 颜色判断逻辑 (根据你的描述微调) ===
            
            # 1. 判断空地 (薄荷绿: R207 G245 B232 -> BGR: 232, 245, 207)
            # 我们设置一个宽松的范围
            if b > 200 and g > 200 and red_val > 180:
                board[r][c] = 1 # 空地
                
            # 2. 判断玩家 (红色系)
            # 玩家是红衣服，R 值通常很高，且明显高于 B 和 G
            elif red_val > 150 and red_val > b + 20: 
                board[r][c] = 3 # 玩家
                player_pos = (r, c)
                
            # 3. 其他都当做敌人 (白色幽灵/弹幕)
            else:
                board[r][c] = 2 # 敌人
                
    return board, player_pos

def execute_turn(action_type, target_r, target_c):
    """
    执行：点按钮 -> 点格子 -> 点对勾
    """
    print(f"执行动作: {action_type} -> 目标 ({target_r}, {target_c})")
    
    # 1. 点击功能按钮
    if action_type == "move":
        tap(*BTN_MOVE)
    elif action_type == "skill1":
        tap(*BTN_SKILL_1)
    
    time.sleep(0.5) # 等待 UI 弹出绿色对勾
    
    # 2. 点击网格目标
    tx, ty = get_grid_center(target_r, target_c)
    tap(tx, ty)
    
    time.sleep(0.3)
    
    # 3. 🟢 关键一步：点击确认 (绿色对勾)
    tap(*BTN_CONFIRM)
    
    print("⏳ 回合结算中...")
    time.sleep(1.5) 

# ==========================================
# 【=== 3. 主程序逻辑 ===】
# ==========================================

def play_game():
    print("🤖 游戏助手启动...")
    run_adb("devices")
    
    while True:
        print("\n--- 📸 正在截图 ---")
        img = get_screenshot()
        if img is None: 
            print("❌ 截图失败")
            break
        
        # 1. 识别
        board, player_pos = scan_grid(img)
        print(f"地图状态:\n{board}")
        
        if player_pos is None:
            print("❌ 没找到玩家，可能是死了或者被遮挡，等待5秒...")
            time.sleep(5)
            continue
            
        pr, pc = player_pos
        print(f"📍 玩家位置: {player_pos}")
        
        # 2. 决策 (优先找周围的安全格子)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)] # 上下左右
        safe_moves = []
        
        for dr, dc in moves:
            nr, nc = pr + dr, pc + dc
            # 检查越界
            if 0 <= nr < 7 and 0 <= nc < 7:
                # 检查是不是空地 (1)
                if board[nr][nc] == 1: 
                    safe_moves.append((nr, nc))
        
        if safe_moves:
            # 随机选一个安全的走
            target = random.choice(safe_moves)
            print(f"💡 策略: 移动到安全格子 {target}")
            execute_turn("move", target[0], target[1])
        else:
            print("😱 周围全是怪！尝试原地不动 (跳过回合)...")
            tap(*BTN_NEXT)
            time.sleep(2)

if __name__ == "__main__":
    play_game()