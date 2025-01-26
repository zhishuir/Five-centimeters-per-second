import pygame
import cv2
import sys
import os

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Game:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        pygame.mixer.init()

        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("秒速五厘米")

        # 加载字体
        font_path = resource_path("simhei.ttf")
        if not os.path.isfile(font_path):
            print(f"字体文件 {font_path} 不存在，请确保字体文件在项目目录中。")
            pygame.quit()
            sys.exit()

        self.font_large = pygame.font.Font(font_path, 48)
        self.font_small = pygame.font.Font(font_path, 24)

        # 定义颜色
        self.bg_color = (0, 0, 0)  # 背景颜色
        self.text_color = (255, 255, 255)  # 普通文字颜色（白色）
        self.prompt_text_color = (255, 0, 0)  # 滑动提示文字颜色（红色）
        self.choice_text_color = (255, 0, 0)  # 选择按钮文字颜色（红色）
        self.clock = pygame.time.Clock()
        self.fps = 30

        # 滑动相关变量
        self.swipe_start_pos = None
        self.swipe_end_pos = None
        self.swipe_threshold = 100  # 最小滑动距离
        self.swipe_allowed_time = 1000  # 最大滑动时间（毫秒）
        self.swipe_start_time = None
        self.swipe_trail = []  # 存储滑动轨迹

        self.last_frame_surface = None
        self.x_offset = 0  # 初始化偏移量
        self.y_offset = 0  # 初始化偏移量

    def detect_swipe(self, event, direction):
        """检测滑动事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.swipe_start_pos = event.pos
            self.swipe_start_time = pygame.time.get_ticks()
            self.swipe_trail = [self.swipe_start_pos]
        elif event.type == pygame.MOUSEMOTION and self.swipe_start_pos:
            self.swipe_trail.append(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and self.swipe_start_pos:
            end_pos = event.pos
            time_elapsed = pygame.time.get_ticks() - self.swipe_start_time
            dx = end_pos[0] - self.swipe_start_pos[0]
            dy = end_pos[1] - self.swipe_start_pos[1]
            if direction == "left" and dx < -self.swipe_threshold and abs(
                    dy) < 50 and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            elif direction == "left_hand" and dx < -self.swipe_threshold and abs(
                    dy) < 50 and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            elif direction == "left_hug" and dx < -self.swipe_threshold and abs(
                    dy) < 50 and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            elif direction == "right" and dx > self.swipe_threshold and abs(dy) < 50 and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            elif direction == "down" and dy > self.swipe_threshold and abs(dx) < 50 and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            elif direction == "up" and dy < -self.swipe_threshold and abs(dx) < 50 and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            elif direction == "left_down" and dx < -self.swipe_threshold and dy > self.swipe_threshold and time_elapsed < self.swipe_allowed_time:
                self.swipe_start_pos = None
                self.swipe_end_pos = None
                self.swipe_trail = []
                return True
            # 重置滑动位置和轨迹
            self.swipe_start_pos = None
            self.swipe_end_pos = None
            self.swipe_trail = []
        return False

    def draw_swipe_trail(self):
        """绘制滑动轨迹"""
        if len(self.swipe_trail) > 1:
            pygame.draw.lines(self.screen, (255, 0, 0), False, self.swipe_trail, 3)

    def play_video_and_audio(self, video_path, audio_path=None, swipe_scenes=None, pause_scenes=None):
        """播放视频和音频"""
        cap = cv2.VideoCapture(resource_path(video_path))
        if not cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return

        try:
            if audio_path:
                pygame.mixer.music.load(resource_path(audio_path))
                pygame.mixer.music.play()
        except pygame.error as e:
            print(f"无法播放音频文件: {e}")
            cap.release()
            return

        # 获取视频帧率
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps == 0:
            video_fps = 30  # 默认帧率
        frame_delay = 1 / video_fps

        # 计算需要暂停等待点击的帧数
        pause_frame_numbers = []
        if pause_scenes:
            for scene in pause_scenes:
                frame_num = int(scene['time'] * video_fps)
                pause_frame_numbers.append({'frame': frame_num, 'message': scene['message']})

        # 计算需要滑动的帧数
        swipe_frame_numbers = []
        if swipe_scenes:
            for scene in swipe_scenes:
                frame_num = int(scene['time'] * video_fps)
                swipe_frame_numbers.append({'frame': frame_num, 'direction': scene['direction']})

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 转换视频帧格式
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

            # 显示帧
            self.last_frame_surface = frame_surface.copy()
            self.screen.fill(self.bg_color)
            self.screen.blit(frame_surface, (self.x_offset, self.y_offset))

            for swipe_scene in swipe_frame_numbers:
                if frame_count == swipe_scene['frame']:
                    pygame.mixer.music.pause()
                    direction = swipe_scene['direction']
                    if direction == "left":
                        swipe_message = "请向左滑动"
                    elif direction == "left_hand":
                        swipe_message = "请向左滑动牵起手"
                    elif direction == "left_hug":
                        swipe_message = "请向左滑动拥抱"
                    elif direction == "right":
                        swipe_message = "请向右滑动"
                    elif direction == "down":
                        swipe_message = "请向下滑动"
                    elif direction == "up":
                        swipe_message = "请向上滑动"
                    elif direction == "left_down":
                        swipe_message = "请向左下滑动"
                    else:
                        swipe_message = "请滑动"

                    print(f"触发滑动场景: {swipe_message} at frame {frame_count}")  # Debug statement
                    self.wait_for_swipe(direction, swipe_message)
                    pygame.mixer.music.unpause()

            # 检查是否需要触发暂停
            for pause_scene in pause_frame_numbers:
                if frame_count == pause_scene['frame']:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                    pause_message = pause_scene['message']
                    print(f"触发暂停场景: {pause_message} at frame {frame_count}")  # Debug statement
                    self.wait_for_click(pause_message)
                    pygame.mixer.music.unpause()

            pygame.display.update()
            self.clock.tick(video_fps)
            frame_count += 1

            # 检测退出事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.quit()
                    sys.exit()

        cap.release()
        pygame.mixer.music.stop()

    def wait_for_swipe(self, direction, message):
        """等待滑动操作"""
        waiting = True
        self.swipe_trail = []  # 开始等待时重置滑动轨迹
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif self.detect_swipe(event, direction):
                    print(f"检测到滑动方向: {direction}")  # Debug statement
                    waiting = False

            if self.last_frame_surface:
                # 使用存储的偏移量绘制视频帧
                self.screen.blit(self.last_frame_surface, (self.x_offset, self.y_offset))
            self.draw_swipe_trail()  # 绘制滑动轨迹
            prompt_text = self.font_small.render(message, True, self.prompt_text_color)
            prompt_rect = prompt_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(prompt_text, prompt_rect)
            pygame.display.flip()
            self.clock.tick(60)  # 在等待时以合理的帧率运行

    def wait_for_click(self, message):
        """等待鼠标点击操作"""
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False

            if self.last_frame_surface:
                # 使用存储的偏移量绘制视频帧
                self.screen.blit(self.last_frame_surface, (self.x_offset, self.y_offset))

            # 渲染暂停消息
            prompt_text = self.font_small.render(message, True, self.prompt_text_color)
            prompt_rect = prompt_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(prompt_text, prompt_rect)

            pygame.display.flip()
            self.clock.tick(60)  # 保持合理的帧率

    def display_choices(self, choices):
        """显示选择界面，背景为暂停的视频帧"""
        rendered_choices = [self.font_large.render(choice, True, self.choice_text_color) for choice in choices]
        # 增大按钮之间的垂直间距，例如150像素
        choice_rects = [text.get_rect(center=(self.screen_width // 2, 200 + i * 150)) for i, text in
                        enumerate(rendered_choices)]

        # 清空事件队列，确保没有残留事件
        pygame.event.clear()

        while True:
            if self.last_frame_surface:
                # 使用存储的偏移量绘制视频帧
                self.screen.blit(self.last_frame_surface, (self.x_offset, self.y_offset))
            for text, rect in zip(rendered_choices, choice_rects):
                self.screen.blit(text, rect)
            pygame.display.flip()

            # 等待新的事件
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, rect in enumerate(choice_rects):
                    if rect.collidepoint(mouse_pos):
                        print(f"选择了: {choices[i]}")  # Debug statement
                        return choices[i]

    def show_text_screen(self, title, subtitle):
        """显示黑屏文本"""
        self.screen.fill(self.bg_color)
        title_text = self.font_large.render(title, True, self.text_color)
        subtitle_text = self.font_small.render(subtitle, True, self.text_color)
        self.screen.blit(title_text, ((self.screen_width - title_text.get_width()) // 2, self.screen_height // 3))
        self.screen.blit(subtitle_text, ((self.screen_width - subtitle_text.get_width()) // 2, self.screen_height // 2))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            self.clock.tick(60)
    def chapter_two(self):
        """第二章逻辑"""
        self.play_video_and_audio(
            "res/小时候结识.mp4",
            "res/小时候结识.mp3",
            swipe_scenes=[
                {'time':16, 'direction':'right'},
                {'time':22, 'direction':'down'},
                {'time':77, 'direction':'left_hand'},
                {'time':80, 'direction':'up'}
            ]
        )
        self.play_video_and_audio("res/给明里写信.mp4", "res/给明里写信.mp3")
        # 显示选择界面，用户进行选择
        choice = self.display_choices(["不再联系", "表达转学", "隐瞒转学"])
        # 根据用户选择进行不同的分支
        if choice == "不再联系":
            self.play_video_and_audio("res/好久没联系了.mp4", "res/好久没联系了.mp3")
            self.show_text_screen("成就达成", "花开花落终有时，相逢相聚本无意")
        elif choice == "表达转学":
            self.play_video_and_audio("res/突然转学.mp4", "res/突然转学.mp3")
            choice2 = self.display_choices(["写信沟通", "另做打算"])
            if choice2 == "写信沟通":
                self.play_video_and_audio("res/再次写给明里.mp4", "res/再次写给明里.mp3")
                self.play_video_and_audio("res/天冷最近还好吗.mp4", "res/天冷最近还好吗.mp3")
                self.play_video_and_audio(
                    "res/让你来我这边车站.mp4",
                    "res/让你来我这边车站.mp3",
                    swipe_scenes=[
                        {'time': 6, 'direction': 'left_down'}
                    ]
                )
                self.play_video_and_audio(
                    "res/晚点.mp4",
                    "res/晚点.mp3",
                    pause_scenes=[
                        {'time': 124, 'message': "点击屏幕关闭车门"}
                    ]
                )
                self.play_video_and_audio("res/下车要见明里了.mp4", "res/下车要见明里了.mp3",swipe_scenes=[
                        {'time': 4, 'direction': 'up'}
                    ])
                self.play_video_and_audio("res/再次晚点.mp4", "res/再次晚点.mp3",
                swipe_scenes=[
                    {'time': 36, 'direction': 'down'}
                ])
                self.play_video_and_audio("res/火车终于等到明里.mp4", "res/火车终于等到明里.mp3",
                                          swipe_scenes=[
                                              {'time': 78, 'direction': 'left'},
                                              {'time': 93, 'direction': 'right'},
                                              {'time': 214, 'direction': 'up'},
                                              {'time': 338, 'direction': 'left_hug'}
                                          ], pause_scenes=[
                        {'time': 99, 'message': "点击叫明里名字"}
                    ])
                self.show_text_screen("成就达成", "樱花的秒速是每秒五厘米，那么两颗心要多久才能相遇...未完待续")
            elif choice2 == "另做打算":
                self.play_video_and_audio("res/一年没见.mp4", "res/一年没见.mp3")
                self.show_text_screen("成就达成", "渐行渐远渐无书，水阔鱼沉何处问")
        elif choice == "隐瞒转学":
            self.play_video_and_audio("res/谢谢你的回信.mp4", "res/谢谢你的回信.mp3")
            self.play_video_and_audio(
                "res/让你来我这边车站.mp4",
                "res/让你来我这边车站.mp3",
                swipe_scenes=[
                    {'time': 6, 'direction': 'left_down'}
                ]
            )
            self.play_video_and_audio("res/晚点.mp4","res/晚点.mp3",
                pause_scenes=[
                    {'time': 124, 'message': "点击关上车门"}
                ]
            )
            self.play_video_and_audio("res/下车要见明里了.mp4", "res/下车要见明里了.mp3",swipe_scenes=[
                        {'time': 4, 'direction': 'up'}
                    ])
            self.play_video_and_audio("res/再次晚点.mp4", "res/再次晚点.mp3",
                swipe_scenes=[
                    {'time': 36, 'direction': 'down'}
                ])
            self.play_video_and_audio("res/火车终于等到明里.mp4", "res/火车终于等到明里.mp3",
                swipe_scenes=[
                    {'time': 78, 'direction': 'left'},
                    {'time': 93, 'direction': 'right'},
                    {'time': 214, 'direction': 'up'},
                    {'time': 338, 'direction': 'left_hug'}
                ],pause_scenes=[
        {'time': 99, 'message': "点击叫明里名字"}
    ])
            self.show_text_screen("成就达成", "樱花下落的秒速是秒速五厘米，那么两颗心要多久才能相遇...未完待续")

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    pygame.init()
    infoObject = pygame.display.Info()
    screen_width = int(infoObject.current_w)
    screen_height = int(infoObject.current_h)
    game = Game(screen_width, screen_height)
    game.chapter_two()
