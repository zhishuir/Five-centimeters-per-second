import pygame
import cv2
import sys
import os
import numpy as np
from main2 import Game as SecondChapter
import main2

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        infoObject = pygame.display.Info()
        self.screen_width = int(infoObject.current_w)
        self.screen_height = int(infoObject.current_h)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("秒速五厘米")

        # 加载字体
        font_filename = 'simhei.ttf'
        font_path = resource_path(font_filename)
        if not os.path.isfile(font_path):
            print(f"字体文件 {font_path} 不存在，请确保字体文件在项目目录中。")
            pygame.quit()
            sys.exit()
        self.font_large = pygame.font.Font(font_path, 48)
        self.font_small = pygame.font.Font(font_path, 24)

        self.bg_color = (0, 0, 0)
        self.prompt_text_color = (255, 0, 0)
        self.text_color = (255, 255, 255)

        self.state = "title"

        # 视频播放相关
        self.cap = None
        self.video_playing = False
        self.clock = pygame.time.Clock()
        self.fps = 30  # 默认帧率
        self.frame_delay = 1 / self.fps
        self.current_frame = 0  # 初始化 current_frame
        self.last_frame_surface = None  # 存储最后一帧

        # 音频相关
        self.audio_path = resource_path("res/chapter_one.mp3")  # 确保音频文件路径正确
        if not os.path.isfile(self.audio_path):
            print(f"音频文件 {self.audio_path} 不存在，请确保音频文件在项目目录中。")
            pygame.quit()
            sys.exit()
        self.audio_loaded = False

        # 交互相关
        self.pause_frame_number_1 = None
        self.pause_frame_number_2 = None
        self.interaction_done = False
        self.swipe_prompt_displayed = False

        # Swipe detection variables
        self.swipe_start_pos = None
        self.swipe_end_pos = None
        self.swipe_threshold = 100  # 最小滑动距离
        self.swipe_allowed_time = 1000  # 最大滑动时间（毫秒）
        self.swipe_start_time = None
        self.swipe_trail = []  # 存储滑动轨迹

        # 存储视频偏移量
        self.x_offset = 0
        self.y_offset = 0

    def draw_vertical_text(self, text, x, y, font):
        """垂直绘制文本"""
        for i, char in enumerate(text):
            rendered_char = font.render(char, True, self.text_color)
            self.screen.blit(rendered_char, (x, y + i * rendered_char.get_height()))

    def play_video_init(self, video_path):
        """初始化视频播放"""
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return False

        # 获取视频帧率和总帧数
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0:
            self.fps = 30  # 默认帧率
        self.frame_delay = 1 / self.fps
        self.video_playing = True
        self.current_frame = 0  # 重置帧计数器

        # 获取暂停帧点（假设需要在24秒和27秒暂停）
        self.pause_frame_number_1 = int(24 * self.fps)
        self.pause_frame_number_2 = int(27 * self.fps)

        return True

    def play_video_frame_func(self):
        """播放视频的单帧"""
        ret, frame = self.cap.read()
        if not ret:
            self.video_playing = False
            return False  # 视频播放结束

        self.current_frame += 1

        # 转换颜色从 BGR 到 RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 获取原始宽高比，保持视频比例
        original_height, original_width, _ = frame.shape
        aspect_ratio = original_width / original_height
        target_width = self.screen_width
        target_height = int(self.screen_width / aspect_ratio)

        if target_height > self.screen_height:
            target_height = self.screen_height
            target_width = int(self.screen_height * aspect_ratio)

        frame = cv2.resize(frame, (target_width, target_height))

        # 居中视频
        self.x_offset = (self.screen_width - target_width) // 2
        self.y_offset = (self.screen_height - target_height) // 2

        # 将帧转换为 Pygame 的 Surface
        frame_surface = pygame.surfarray.make_surface(frame)

        # 添加旋转和翻转以修正视频方向
        frame_surface = pygame.transform.rotate(frame_surface, -90)  # 旋转90度逆时针
        frame_surface = pygame.transform.flip(frame_surface, True, False)  # 水平翻转

        # 存储当前帧
        self.last_frame_surface = frame_surface.copy()

        self.screen.fill(self.bg_color)
        self.screen.blit(frame_surface, (self.x_offset, self.y_offset))
        pygame.display.update()
        return True

    def play_audio(self):
        """播放音频"""
        try:
            pygame.mixer.music.load(self.audio_path)
            pygame.mixer.music.play()
            self.audio_loaded = True
        except pygame.error as e:
            print(f"无法播放音频文件: {e}")
            self.audio_loaded = False

    def stop_audio(self):
        """停止音频播放"""
        pygame.mixer.music.stop()

    def detect_swipe(self, event, direction="right"):
        """检测鼠标滑动事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.swipe_start_pos = event.pos
            self.swipe_start_time = pygame.time.get_ticks()
            self.swipe_trail = [self.swipe_start_pos]  # 初始化滑动轨迹
        elif event.type == pygame.MOUSEMOTION and self.swipe_start_pos:
            self.swipe_trail.append(event.pos)  # 记录滑动轨迹
        elif event.type == pygame.MOUSEBUTTONUP and self.swipe_start_pos:
            self.swipe_end_pos = event.pos
            swipe_time = pygame.time.get_ticks() - self.swipe_start_time
            dx = self.swipe_end_pos[0] - self.swipe_start_pos[0]
            dy = self.swipe_end_pos[1] - self.swipe_start_pos[1]

            if direction == "right":
                result = dx > self.swipe_threshold and abs(dy) < self.swipe_threshold and swipe_time < self.swipe_allowed_time
            elif direction == "right_up":
                result = dx > self.swipe_threshold and dy < -self.swipe_threshold and swipe_time < self.swipe_allowed_time
            else:
                result = False

            self.swipe_start_pos = None
            self.swipe_end_pos = None
            return result
        return False

    def draw_swipe_trail(self):
        """绘制滑动轨迹"""
        if len(self.swipe_trail) > 1:
            pygame.draw.lines(self.screen, (255, 0, 0), False, self.swipe_trail, 3)

    def chapter_one_end(self):
        """第一章结束后的逻辑"""
        self.screen.fill(self.bg_color)
        end_text = self.font_large.render("第一章 樱花抄", True, self.text_color)
        self.screen.blit(end_text, ((self.screen_width - end_text.get_width()) // 2, self.screen_height // 3))
        japanese_text = self.font_small.render("第一章 桜花抄", True, self.text_color)
        self.screen.blit(japanese_text, ((self.screen_width - japanese_text.get_width()) // 2, self.screen_height // 2))
        click_text = self.font_small.render("故事发展会发生改变 请谨慎选择", True, self.text_color)
        self.screen.blit(click_text, ((self.screen_width - click_text.get_width()) // 2, self.screen_height - 50))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # 调用第二章逻辑
                    second_chapter = SecondChapter(self.screen_width, self.screen_height)
                    second_chapter.chapter_two()
                    waiting = False

    def run(self):
        running = True
        while running:
            if self.state != "playing_video":
                self.clock.tick(60)  # 控制主循环的最大帧率

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif self.state == "swipe_1" and self.detect_swipe(event, "right"):
                    pygame.mixer.music.unpause()
                    self.state = "playing_video"
                elif self.state == "swipe_2" and self.detect_swipe(event, "right_up"):
                    pygame.mixer.music.unpause()
                    self.state = "playing_video"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "title":
                        self.state = "chapter_one"
                    elif self.state == "chapter_one":
                        self.state = "chapter_one_video"

            # 根据当前状态执行相应的逻辑
            if self.state == "title":
                self.screen.fill(self.bg_color)
                self.draw_vertical_text("秒速五厘米", self.screen_width // 2 - 80, self.screen_height // 4, self.font_large)
                self.draw_vertical_text("秒速５センチメートル", self.screen_width // 2 + 50, self.screen_height // 4, self.font_large)
                click_text = self.font_small.render("点击屏幕继续", True, self.text_color)
                self.screen.blit(click_text, ((self.screen_width - click_text.get_width()) // 2, self.screen_height - 50))

            elif self.state == "chapter_one":
                self.screen.fill(self.bg_color)
                chapter_text = self.font_large.render("序章", True, self.text_color)
                self.screen.blit(chapter_text, ((self.screen_width - chapter_text.get_width()) // 2, self.screen_height // 2))
                click_text = self.font_small.render("点击继续", True, self.text_color)
                self.screen.blit(click_text, ((self.screen_width - click_text.get_width()) // 2, self.screen_height - 50))

            elif self.state == "chapter_one_video":
                # 初始化视频播放
                video_path = resource_path("res/chapter_one.mp4")
                if self.play_video_init(video_path):
                    # 播放音频
                    self.play_audio()
                    self.state = "playing_video"
                else:
                    running = False  # 无法播放视频，退出游戏

            elif self.state == "playing_video":
                self.clock.tick(self.fps)  # 控制视频播放的帧率
                frame_result = self.play_video_frame_func()
                if not frame_result:
                    self.state = "chapter_one_end"
                elif self.current_frame == self.pause_frame_number_1:
                    pygame.mixer.music.pause()
                    self.state = "swipe_1"
                elif self.current_frame == self.pause_frame_number_2:
                    pygame.mixer.music.pause()
                    self.state = "swipe_2"

            elif self.state == "swipe_1" or self.state == "swipe_2":
                if self.last_frame_surface:
                    # 使用存储的偏移量绘制视频帧
                    self.screen.blit(self.last_frame_surface, (self.x_offset, self.y_offset))
                self.draw_swipe_trail()  # 绘制滑动轨迹
                prompt_text = self.font_small.render(
                    "请向右滑动继续" if self.state == "swipe_1" else "请向右上滑动继续", True, self.prompt_text_color
                )
                prompt_rect = prompt_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(prompt_text, prompt_rect)

            elif self.state == "chapter_one_end":
                self.chapter_one_end()
                # 不再设置 running = False，这样主循环可以继续运行
                running = False  # 如果希望游戏在第二章结束后退出，可以保留此行

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
