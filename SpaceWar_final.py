import pygame
from pygame.locals import *
from time import sleep, time
import random
import mediapipe as mp
import cv2
from screeninfo import get_monitors
from pynput.mouse import Button, Controller
import numpy as np

BLACK=(0,0,0)
WHITE=(255,255,255)
YELLOW=(250,250,50)
RED=(250,50,50)
Window_Width = 480
Window_Height = 640

FPS = 30



class Fighter(pygame.sprite.Sprite):
    def __init__(self):
        super(Fighter,self).__init__()
        self.image = pygame.image.load('fighter.png')
        self.rect = self.image.get_rect()
        self.rect.x = int(Window_Width/2)
        self.rect.y = Window_Height-self.rect.height
        self.dx = 0
        self.dy = 0

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

        if self.rect.x <0 or self.rect.x+self.rect.width > Window_Width:
            self.rect.x -= self.dx

        if self.rect.y <0 or self.rect.y+self.rect.width > Window_Height:
            self.rect.y -= self.dy

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def collide(self, sprites):
        for sprite in sprites:
            if pygame.sprite.collide_rect(self, sprite):
                return sprite
            
class Missile(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, speed):
        super(Missile,self).__init__()
        self.image = pygame.image.load('missile.png')
        self.rect=self.image.get_rect()
        self.rect.x = xpos
        self.rect.y = ypos
        self.speed = speed
        

    

    def update(self):
        self.rect.y-= self.speed
        if self.rect.y + self.rect.height <0:
            self.kill()

    def collide(self, sprites):
        for sprite in sprites:
            if pygame.sprite.collide_rect(self,sprite):
                return sprite
            

class Rock(pygame.sprite.Sprite):
    def __init__ (self,xpos,ypos,speed):
        super(Rock, self).__init__()
        rock_images = ('ship01.png', 'ship02.png', 'ship03.png', 'ship04.png', 'ship05.png')
        self.image = pygame.image.load(random.choice(rock_images))
        self.rect = self.image.get_rect()
        self.rect.x = xpos-45
        self.rect.y = ypos
        self.speed=speed

    def update(self):
        self.rect.y += self.speed

    def out_of_screen(self):
        if self.rect.y > Window_Height:
            return True
        

class Item(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, speed):
        super(Item, self).__init__()
        self.image = pygame.image.load('rock16.png')  # 아이템 이미지 파일 로드
        self.rect = self.image.get_rect()
        self.rect.x = xpos-45
        self.rect.y = ypos
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > Window_Height:
            self.kill()


def draw_text(text, font, surface, x,y,main_color):
    text_obj = font.render(text, True, main_color)
    text_rect = text_obj.get_rect()
    text_rect.centerx = x
    text_rect.centery = y
    surface.blit(text_obj, text_rect)

def occur_explosion(surface, x,y):
    explosion_image = pygame.image.load('explosion.png')
    explosion_rect = explosion_image.get_rect()
    explosion_rect.x = x
    explosion_rect.y = y
    surface.blit(explosion_image, explosion_rect)

def get_states(positions):
    """Return the state of the index, middle, and thumb fingers (up or down)."""
    states = [False] * 3
    # 검지, 중지, 엄지 손가락의 랜드마크 좌표 인덱스를 설정합니다.
    index_finger_indices = [8, 7, 6]  # 검지 손가락의 첫 번째, 두 번째, 세 번째 관절 인덱스
    middle_finger_indices = [12, 11, 10]  # 중지 손가락의 첫 번째, 두 번째, 세 번째 관절 인덱스
    thumb_finger_indices = [4, 3, 2]  # 엄지 손가락의 첫 번째, 두 번째, 세 번째 관절 인덱스

    # 검지 손가락의 첫 번째와 두 번째 관절 간의 Y 좌표 차이를 계산합니다.
    index_y_diff = positions[index_finger_indices[0]].y - positions[index_finger_indices[1]].y
    # 중지 손가락의 첫 번째와 두 번째 관절 간의 Y 좌표 차이를 계산합니다.
    middle_y_diff = positions[middle_finger_indices[0]].y - positions[middle_finger_indices[1]].y
    # 엄지 손가락의 첫 번째와 두 번째 관절 간의 Y 좌표 차이를 계산합니다.
    thumb_y_diff = positions[thumb_finger_indices[0]].y - positions[thumb_finger_indices[1]].y

    # Y 좌표 차이가 어느 정도 이상이면 손가락을 펴고 있다고 판단합니다.
    if index_y_diff > 0.02:  # 검지 손가락 펴짐 여부 판단을 위한 임계값
        states[0] = True  # 검지 손가락 펴짐 상태 설정
    if middle_y_diff > 0.02:  # 중지 손가락 펴짐 여부 판단을 위한 임계값
        states[1] = True  # 중지 손가락 펴짐 상태 설정
    if thumb_y_diff > 0.02:  # 엄지 손가락 펴짐 여부 판단을 위한 임계값
        states[2] = True  # 엄지 손가락 펴짐 상태 설정

    return states


def game_loop():
    global high_score
    cap = cv2.VideoCapture(cv2.CAP_DSHOW+0)
    cap.set(3, 640)  # 가로 해상도 설정
    cap.set(4, 480)
    default_font = pygame.font.Font('NanumGothic.ttf', 28)
    background_image = pygame.image.load('background2.png')

    fps_clock = pygame.time.Clock()

    fighter = Fighter()
    missiles = pygame.sprite.Group()
    rocks = pygame.sprite.Group()

    occur_prob = 40
    shot_count = 0
    count_missed = 0
    last_shot_time = 0  # 마지막 총알 발사 시간 추가

    done = False

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1)
    items = pygame.sprite.Group()
    last_item_time = 0  # 마지막 아이템 생성 시간 추가
    item_count = 0  # 아이템 수 초기화
    item_effect_duration = 10.0  # 아이템 효과 지속 시간 (초)
    item_effect_end_time = 0.0  # 아이템 효과 종료 시간 초기화
    
    
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pass  # 스페이스 바 관련 코드 삭제

        screen.blit(background_image, background_image.get_rect())

        _, frame = cap.read()
        frame = cv2.flip(frame, 1)

        frame.flags.writeable = False
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        frame.flags.writeable = True
        current_time = time()  # 현재 시간 기록

    # 마지막 아이템 생성 시간에서 1초 이상 지났을 때만 추가 아이템 생성 허용
        if current_time - last_item_time >= 1:
            
            if random.randint(1, 1000) == 1:
                item = Item(random.randint(0, Window_Width - 5), 0, 5)  # 속도를 5로 설정
                items.add(item)
                last_item_time = current_time

        # 아이템 효과가 종료되었을 때 아이템 효과를 해제
        

        # 아이템과 충돌 검사
        for item in items:
            if pygame.sprite.collide_rect(fighter, item):
                item.kill()  # 아이템 효과 지속 시간 설정
                item_count+=1
                # 아이템 효과를 적용하는 코드 추가

        items.update()
        items.draw(screen)
        if results.multi_hand_landmarks:
            # Get the position of the index finger
            landmarks = results.multi_hand_landmarks[0].landmark
            index_finger = landmarks[8]
            middle_finger = landmarks[12]
            thumb_finger = landmarks[4]
            finger_x = int(index_finger.x * Window_Width)
            finger_y = int(index_finger.y * Window_Height)

            # Move the fighter plane based on finger position
            fighter.rect.x = finger_x - fighter.rect.width // 2
            fighter.rect.y = finger_y - fighter.rect.height // 2

            # 중지 손가락이 펴져 있을 때 자동으로 총알 발사
            finger_states = get_states(landmarks)
            
            current_time = time()  # 현재 시간 기록
            # 마지막 총알 발사 시간에서 1초 이상 지났을 때만 추가 발사 허용
            if current_time> item_effect_end_time:
                item_effect_end_time = 0
                missile_speed=10
                time_between = 0.3
                if finger_states[2]:  # 엄지 손가락 펴짐 여부 판단을 위한 인덱스 (2: 엄지 손가락)
                    if item_count > 0:
                        item_count -= 1
                        missile_speed = 20
                        time_between = 0.15

                        item_effect_duration = 10.0
                        item_effect_end_time = current_time + item_effect_duration
                    else:
                        pass
            else:
                missile_speed = 20
                time_between = 0.15

            
            if finger_states[1] and current_time - last_shot_time >= time_between:
                missile = Missile(fighter.rect.centerx, fighter.rect.y, missile_speed)
                missiles.add(missile)
                last_shot_time = current_time 
            

        

        occur_of_rocks = 2 + int(shot_count / 150)
        min_rock_speed = 1 + int(shot_count / 100)
        max_rock_speed = 1 + int(shot_count / 50)

        if random.randint(1, occur_prob) == 1:
            for i in range(occur_of_rocks):
                speed = random.randint(min_rock_speed, max_rock_speed)
                rock = Rock(random.randint(0, Window_Width - 5), 0, speed)
                rocks.add(rock)

        draw_text('파괴한 비행선: {}'.format(shot_count), default_font, screen, 130, 20, YELLOW)
        draw_text('놓친 비행선: {}'.format(count_missed), default_font, screen, 360, 20, RED)
        draw_text('아이템 개수: {}'.format(item_count), default_font, screen, 360, 80, WHITE)
        for missile in missiles:
            rock = missile.collide(rocks)
            if rock:
                missile.kill()
                rock.kill()
                occur_explosion(screen, rock.rect.x, rock.rect.y)
                shot_count += 1

        for rock in rocks:
            if rock.out_of_screen():
                rock.kill()
                count_missed += 1

        rocks.update()
        rocks.draw(screen)
        missiles.update()
        missiles.draw(screen)
        fighter.update()
        fighter.draw(screen)
        pygame.display.flip()

        if fighter.collide(rocks) or count_missed >= 3:
            if shot_count > high_score:
                high_score = shot_count
                with open('highscore.txt', 'w') as file:
                    file.write(str(high_score))
            occur_explosion(screen, fighter.rect.x, fighter.rect.y)
            pygame.display.update()

            sleep(1)
            done = True

        fps_clock.tick(FPS)

    return 'game_menu'

# 나머지 코드는 그대로 유지됩니다.

high_score = 0

try:
    with open('highscore.txt', 'r') as file:
        high_score = int(file.read())
except FileNotFoundError:
    pass

def game_menu():
    start_image = pygame.image.load('background2.png')
    screen.blit(start_image,[0,0])
    draw_x = int(Window_Width/2)
    draw_y = int(Window_Height/2)
    font_70 = pygame.font.Font('NanumGothic.ttf',70)
    font_40 = pygame.font.Font('NanumGothic.ttf',40)

    draw_text('우주 전쟁!', font_70, screen, draw_x, draw_y, YELLOW)
    draw_text('엔터 키를 누르면', font_40, screen, draw_x, draw_y+200, WHITE)
    draw_text('게임이 시작됩니다.', font_40, screen, draw_x, draw_y+250, WHITE)


    draw_text('최고 기록: {}'.format(high_score), font_40, screen, draw_x, draw_y + 300, WHITE)
    
    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return 'play'
        if event.type == QUIT:  # 종료 이벤트 처리
            return 'quit'

    return 'game_menu'


def main():
    global screen

    pygame.init()
    
    screen = pygame.display.set_mode((Window_Width, Window_Height))
    pygame.display.set_caption('PyShooting')

    action = 'game_menu'
    while action != 'quit':
        if action =='game_menu':
            action = game_menu()
        elif action == 'play':
            action = game_loop()
    
    pygame.quit()

if __name__ == "__main__":
    main()