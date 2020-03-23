'''
    author:mcwindy
    contact:QQ 645830306
'''

from math import cos, log, pi, sin, sqrt
from random import randint, random
from time import sleep, time

import pygame

USE_TIMER = False
FULL_SCREEN = True
ENTER_USER_NAME = True


class Obj():
    def __init__(self, _x, _y):
        self.x = _x
        self.y = _y

    def distance(self, obj_b):
        if type(obj_b) is tuple:
            return sqrt((self.x - obj_b[0]) ** 2 + (self.y - obj_b[1]) ** 2)
        else:
            return sqrt((self.x - obj_b.x) ** 2 + (self.y - obj_b.y) ** 2)

    def hit(self, obj_b, dis):
        return self.distance(obj_b) < dis

    def in_main_window(self):
        pos_x, pos_y = round(self.x), round(self.y)
        return main_window[0] < pos_x < main_window[0]+main_window[2] and main_window[1] < pos_y < main_window[1]+main_window[3]


class Player(Obj):
    point_list = [100, 250, 500, 800, 1100]

    def __init__(self, _move_speed):
        Obj.__init__(self, (main_window[0]*2+main_window[2])//2, round((main_window[1]*2+main_window[3])//1.5))
        self.name = 'default'
        self.score = 0
        self.hp = 0
        self.bomb = 0
        self.power = 10
        self.graze = 0
        self.point = 0
        self.move_speed = _move_speed
        self.tracking_bullet_fire_pos = 0
        self.tracking_bullet_frequency = 10
        self.last_tracking_bullet_frame = 0
        self.last_invincible_start_frame = 0
        self.is_invincible = False
        self.death_time = 0
        self.cheat = False

        self.img1 = pygame.image.load('pl.png').convert()
        self.img1.set_colorkey(blue)
        self.img2 = pygame.image.load('ball.png').convert()
        self.img2.set_colorkey(blue)

    def move(self, press):

        move_speed = self.move_speed
        if press[pygame.K_LSHIFT]:
            self.tracking_bullet_fire_pos = min(1, self.tracking_bullet_fire_pos+0.04)
            move_speed /= 2.5
        else:
            self.tracking_bullet_fire_pos = max(0, self.tracking_bullet_fire_pos-0.04)
        if sum([press[pygame.K_UP], press[pygame.K_DOWN], press[pygame.K_LEFT], press[pygame.K_RIGHT]]) == 2:
            self.x += (press[pygame.K_RIGHT] - press[pygame.K_LEFT]) * move_speed / 1.414
            self.y += (press[pygame.K_DOWN] - press[pygame.K_UP]) * move_speed / 1.414
        else:
            self.x += (press[pygame.K_RIGHT] - press[pygame.K_LEFT]) * move_speed
            self.y += (press[pygame.K_DOWN] - press[pygame.K_UP]) * move_speed

        # set limit on x and y
        self.x = min(max(main_window[0] + 21, round(self.x)), main_window[0] + main_window[2] - 21)
        self.y = min(max(main_window[1] + 15, round(self.y)), main_window[1] + main_window[3] - 10)

    def make_action(self, press):
        if press[pygame.K_x] and self.bomb > 0:
            self.use_bomb()

        if press[pygame.K_z]:
            self.score += difficulty[6]
            Bullet.player_bullets.append(self.shot1())
            Bullet.player_bullets.extend(self.shot2())

        # back door
        if press[pygame.K_v]:
            self.power += 20
            self.use_bomb()
            self.is_invincible = not self.is_invincible
            self.cheat = True

    def shot1(self):
        return Bullet(self.x, self.y-15, 0, -20, 1)

    def shot2(self):
        if current_frame - self.last_tracking_bullet_frame >= self.tracking_bullet_frequency:
            self.last_tracking_bullet_frame = current_frame
            dx = cos(0.8*self.tracking_bullet_fire_pos)*30
            dy = sin(0.8*self.tracking_bullet_fire_pos)*30
            if len(Monster.monsters) == 0:
                return Bullet(self.x - dx, self.y - dy, 0, -10, 2, -1), \
                    Bullet(self.x + dx, self.y - dy, 0, -10, 2, -1)
            else:
                min_dis = 100000
                min_dis_monster = 0
                for _monster in Monster.monsters:
                    if _monster.distance((self.x-dx, self.y-dy)) < min_dis:
                        min_dis_monster = _monster.id
                        min_dis = self.distance(_monster)
                        ddx = self.x - dx - _monster.x
                        ddy = self.y - dy - _monster.y
                vx = -ddx / sqrt(ddx ** 2 + ddy ** 2) * 10
                vy = -ddy / sqrt(ddx ** 2 + ddy ** 2) * 10

                left_bullet = Bullet(self.x - dx, self.y - dy, vx, vy, kind=2, tracking_target=min_dis_monster)

                min_dis = 100000
                min_dis_monster = 0
                for _monster in Monster.monsters:
                    if _monster.distance((self.x+dx, self.y-dy)) < min_dis:
                        min_dis_monster = _monster.id
                        min_dis = self.distance(_monster)
                        ddx = self.x + dx - _monster.x
                        ddy = self.y - dy - _monster.y
                vx = -ddx / sqrt(ddx ** 2 + ddy ** 2) * 10
                vy = -ddy / sqrt(ddx ** 2 + ddy ** 2) * 10

                right_bullet = Bullet(self.x + dx, self.y - dy, vx, vy, kind=2, tracking_target=min_dis_monster)

                return [left_bullet, right_bullet]

        else:
            return []

    def use_bomb(self):
        self.bomb -= 1
        self.is_invincible = True
        for _item in Item.items:
            self.hit_item(_item)
        Item.items = []
        for _monster in Monster.monsters:
            _monster.die()
        Monster.monsters = []
        Bullet.monster_bullets = []

    def check_graze(self):
        for _bullet in Bullet.monster_bullets:
            if self.hit(_bullet, 25):
                self.graze += 1
                self.score += 1000 * difficulty[6]

    def check_reach_top(self):
        if self.y < main_window[3] >> 2:
            for _item in Item.items:
                self.hit_item(_item)
            Item.items = []

    def check_hit_items(self):
        flag = False
        for _item in Item.items:
            if self.hit(_item, 50):
                flag = True
                self.hit_item(_item)
        if flag:
            tmp1 = []
            for _item in Item.items:
                if _item.exist:
                    tmp1.append(_item)
            Item.items = tmp1

    def hit_item(self, _item):
        _item.exist = False
        if _item.kind == 1:
            self.power += 1
        elif _item.kind == 2:
            self.score += 10000 * difficulty[6]
            self.point += 1
            if self.point in player.point_list:
                self.hp += 1
        elif _item.kind == 3:
            self.hp += 1
        elif _item.kind == 4:
            self.bomb += 1
        elif _item.kind == 5:
            self.power += 5

    def check_hit_bullet(self):
        for _bullet in Bullet.monster_bullets:
            if self.hit(_bullet, 9):
                return True
        for _monster in Monster.monsters:
            if self.hit(_monster, round(sqrt(_monster.hp)) + 14) and current_frame - _monster.generate_frame > 100:
                return True

    def check_invincible(self):
        if self.is_invincible:
            # invincible for 1.5s
            if current_frame-self.last_invincible_start_frame >= 120*1.5:
                self.is_invincible = False

    def die(self):
        global difficulty, main_loop_start_time, game_is_on
        self.hp -= 1
        self.bomb = 3
        self.x = (main_window[0]*2+main_window[2])//2
        self.y = round((main_window[1]*2+main_window[3])//1.5)
        self.power = max(self.power - 10, 10)
        self.last_invincible_start_frame = current_frame
        self.is_invincible = True
        self.death_time += 1
        Bullet.monster_bullets = []
        Bullet.player_bullets = []

        sleep(0.75)

        for i in range(4):
            Item.generate_item(randint(self.x-200, self.x+200), randint(-50, -10), 1)
        Item.generate_item(randint(self.x-200, self.x+200), randint(-50, -10), 5)

        if self.hp < 0:
            game_is_on = False
            end_game(2)
            if request_restart():
                reset_all()
                difficulty = Game.choose_difficulty_page(screen)
                main_loop_start_time = time()
            else:
                exit(0)

    def draw(self, screen):
        screen.blit(player.img1, (player.x-player.img1.get_width()//2, player.y-player.img1.get_height()//2))
        pygame.draw.circle(screen, (0, 255, 255), [player.x, player.y], 5)

        dx = cos(0.8*player.tracking_bullet_fire_pos)*30
        dy = sin(0.8*player.tracking_bullet_fire_pos)*30
        screen.blit(player.img2, (player.x-dx-player.img2.get_width()//2, player.y-dy-player.img2.get_height()//2))
        screen.blit(player.img2, (player.x+dx-player.img2.get_width()//2, player.y-dy-player.img2.get_height()//2))


class Monster(Obj):
    monster_count = 0
    monsters = []

    def __init__(self, _type, _hp, _x, _y, _speed, _bullet_speed, _shot_frequency, _score):
        Obj.__init__(self, _x, _y)

        def init_move_method():
            gather_point = ((main_window[0]*2+main_window[2])//2, 400)
            vx = gather_point[0]-self.x
            vy = gather_point[1]-self.y
            self.x_speed = vx/sqrt(vx**2+vy**2)*self.speed
            self.y_speed = vy/sqrt(vx**2+vy**2)*self.speed

        self.id = Monster.monster_count
        Monster.monster_count += 1
        self.type = _type
        self.hp = _hp
        self.speed = _speed
        self.x_speed = 0
        self.y_speed = 0
        self.bullet_speed = _bullet_speed
        self.shot_frequency = _shot_frequency
        self.color = (randint(140, 200), randint(140, 200), randint(140, 200))
        self.score = _score
        self.generate_frame = current_frame
        self.shot_times = 0
        init_move_method()

    @classmethod
    def generate_monster(cls, possibility, max_monster):
        if current_frame <= 120:
            return
        if random() < difficulty[3] and len(Monster.monsters) < max_monster:
            pos_x = randint(main_window[0]+20, main_window[0]+main_window[2]-20)
            pos_y = randint(60, 200)
            hp = 3 * round(0.1 * sqrt(current_frame)) + 1

            # _type, _hp, _x, _y, _speed, _bullet_speed, _shot_frequency,  _score
            if random() < 0.75:
                Monster.monsters.append(Monster(1, hp, pos_x, pos_y, difficulty[4], difficulty[5], 70, 10000))
            else:
                Monster.monsters.append(Monster(2, hp*2, pos_x, pos_y, difficulty[4], difficulty[5], 100, 25000))

    @classmethod
    def check_monster_die(cls):
        for _monster in cls.monsters:
            for player_bullet in Bullet.player_bullets:
                if player_bullet.exist:
                    if _monster.hp > 0 and _monster.hit(player_bullet, round(sqrt(_monster.hp)) + 17):
                        player_bullet.exist = False
                        if player_bullet.kind == 1:
                            _monster.hp -= player.power
                        else:
                            _monster.hp -= player.power//2

        for _monster in cls.monsters:
            if _monster.hp <= 0:
                _monster.die()
        Bullet.player_bullets = [_bullet for _bullet in Bullet.player_bullets if _bullet.exist]
        cls.monsters = [_monster for _monster in cls.monsters if _monster.hp > 0]

    @classmethod
    def move(cls):
        cls.monsters = [_monster for _monster in cls.monsters if _monster.monster_move().in_main_window()]

    @classmethod
    def draw(cls, screen):
        for _monster in cls.monsters:
            pygame.draw.circle(screen, _monster.color, [round(_monster.x), round(_monster.y)],
                               round(log(_monster.hp)) + 10)

    def shot(self, current_frame):
        if current_frame - self.generate_frame - player.death_time*0.75 > self.shot_frequency * self.shot_times:
            if len(Bullet.monster_bullets) < max_bullet:
                self.shot_times += 1
                if self.type == 1:
                    Bullet.monster_bullets.append(self.shot1())
                if self.type == 2:
                    Bullet.monster_bullets.extend(self.shot2(8))

    def monster_move(self):
        self.x += self.x_speed
        self.y += self.y_speed
        return self

    def shot1(self):
        dx = self.x - player.x
        dy = self.y - player.y
        vx = -dx / sqrt(dx * dx + dy * dy) * self.bullet_speed * difficulty[5]
        vy = -dy / sqrt(dx * dx + dy * dy) * self.bullet_speed * difficulty[5]
        return Bullet(self.x, self.y, vx, vy)

    def shot2(self, num_of_bullets):
        ret = []
        for i in range(num_of_bullets):
            vx = self.bullet_speed * sin(2 * pi / num_of_bullets * i + 1e-10)
            vy = self.bullet_speed * cos(2 * pi / num_of_bullets * i + 1e-10)
            ret.append(Bullet(self.x, self.y, vx, vy))
        return ret

    def die(self):
        player.score += self.score * difficulty[6]
        Item.generate_item(self.x, self.y)


class Bullet(Obj):
    player_bullets = []
    monster_bullets = []

    def __init__(self, _x, _y, _x_speed, _y_speed, kind=1, tracking_target=0):
        Obj.__init__(self, _x, _y)
        self.kind = kind
        self.x_speed = _x_speed
        self.y_speed = _y_speed
        self.tracking_target = tracking_target
        self.exist = True

    @classmethod
    def player_bullets_move(cls):
        tmp = []
        for _bullet in cls.player_bullets:
            if _bullet.kind == 1:
                _bullet.x += _bullet.x_speed
                _bullet.y += _bullet.y_speed
            elif _bullet.kind == 2:
                # TODO mininum rotate angle

                # //计算向小角度的方向转 (optional)
                # float f = fabs(targetAngle - m_vRotate.z);
                # if (f < D3DX_PI):
                #   if (targetAngle > m_vRotate.z)
                #       m_vRotate.z += mAngleSpeed*dt;
                #   else
                #       m_vRotate.z -= mAngleSpeed*dt;
                # else:
                #   if (targetAngle > m_vRotate.z)
                #       m_vRotate.z -= mAngleSpeed*dt;
                #   else
                #       m_vRotate.z += mAngleSpeed*dt;
                # 原文链接：https://blog.csdn.net/twicetwice/article/details/79765335

                if _bullet.tracking_target == -1:
                    _bullet.x += _bullet.x_speed
                    _bullet.y += _bullet.y_speed
                else:
                    # binary search is available
                    for _monster in Monster.monsters:
                        if _monster.id == _bullet.tracking_target:
                            dx = _bullet.x - _monster.x
                            dy = _bullet.y - _monster.y
                            vx = -dx / sqrt(dx ** 2 + dy ** 2) * 10
                            vy = -dy / sqrt(dx ** 2 + dy ** 2) * 10
                            _bullet.x_speed = vx
                            _bullet.y_speed = vy
                            _bullet.x += vx
                            _bullet.y += vy
                            break
                    else:
                        _bullet.x += _bullet.x_speed
                        _bullet.y += _bullet.y_speed

            if _bullet.in_main_window():
                tmp.append(_bullet)
        cls.player_bullets = tmp

    @classmethod
    def monster_bullets_move(cls):
        tmp = []
        for _bullet in cls.monster_bullets:
            if _bullet.kind == 1:
                _bullet.x += _bullet.x_speed
                _bullet.y += _bullet.y_speed
            if _bullet.in_main_window():
                tmp.append(_bullet)
        cls.monster_bullets = tmp

    @classmethod
    def draw(cls, screen, bullets, color):
        for _bullet in bullets:
            pos = [round(_bullet.x), round(_bullet.y)]
            if _bullet.kind == 1:
                pygame.draw.circle(screen, color, pos, 8)
            elif _bullet.kind == 2:
                pygame.draw.circle(screen, color, pos, 6)


class Item(Obj):
    items = []

    def __init__(self, _x, _y, _kind):
        Obj.__init__(self, _x, _y)
        self.kind = _kind
        self.x_speed = 0
        self.y_speed = -4
        self.generate_frame = current_frame
        self.exist = True

    @classmethod
    def generate_item(cls, pos_x, pos_y, kind=0):
        if kind == 0:
            tmp = random()
            if tmp < 0.4:
                cls.items.append(Item(pos_x, pos_y, 1))
            elif tmp < 0.8:
                cls.items.append(Item(pos_x, pos_y, 2))
            elif tmp < 0.802:
                cls.items.append(Item(pos_x, pos_y, 3))
            elif tmp < 0.81:
                cls.items.append(Item(pos_x, pos_y, 4))
            elif tmp < 0.83:
                cls.items.append(Item(pos_x, pos_y, 5))
        else:
            cls.items.append(Item(pos_x, pos_y, kind))

    @classmethod
    def move(cls):
        top = 0
        for _item in cls.items:
            _item.y_speed = min(2.7, _item.y_speed + (current_frame - _item.generate_frame - 3.5) // 25)
            _item.y += _item.y_speed
            if main_window[0] < _item.x < main_window[0]+main_window[2] and _item.y < main_window[1]+main_window[3]:
                cls.items[top] = _item
                top += 1
        cls.items = cls.items[0:top]

    @classmethod
    def draw(cls, screen):
        for _item in cls.items:
            pos_x, pos_y = round(_item.x), round(_item.y)
            if _item.kind == 1:  # rect
                pygame.draw.circle(screen, (0, 50, 100), [pos_x, pos_y], 8)
            elif _item.kind == 2:
                pygame.draw.circle(screen, (50, 150, 150), [pos_x, pos_y], 8)
            elif _item.kind == 3:
                pygame.draw.circle(screen, (150, 50, 150), [pos_x, pos_y], 8)
            elif _item.kind == 4:
                pygame.draw.circle(screen, (150, 100, 50), [pos_x, pos_y], 8)
            elif _item.kind == 5:
                pygame.draw.circle(screen, (0, 50, 100), [pos_x, pos_y], 12)


class File():
    use_file = True

    @classmethod
    def read(cls, file_name='high_score.dat'):
        score_list = []
        try:
            with open(file_name, 'r') as f:
                for line in f.readlines():
                    score_list.append(line.strip('[]\n').split(','))
        except FileNotFoundError:
            with open(file_name, 'w') as f:
                pass
        return score_list

    # @classmethod
    # def check_file():

    @classmethod
    def write(cls, score_list, file_name='high_score.dat'):
        score_list = [l[:-1] if l[-1] == -1 else l for l in score_list]
        score_list.append([player.name, difficulty[0], '0' * (9-len(str(player.score))) +
                           str(player.score), str(player.cheat), -1])
        score_list.sort(key=lambda x: int(x[2]), reverse=True)
        with open(file_name, 'w') as f:
            for i in range(min(len(score_list), 20)):
                # [player,difficulty,score,cheat],
                f.write('['+','.join(score_list[i][0:4])+']\n')
        return score_list


class Game():

    @classmethod
    def start_page(cls, screen):
        def repaint():
            screen.fill(white)
            pygame.draw.rect(screen, olive_green, [pos_x-main_window[2] // 2, 20, main_window[2], main_window[3]], 0)
            for i in range(4):
                text_surface = h2_font.render(text[i], True, white)
                screen.blit(text_surface, (pos_x - 50, 350 + 80 * i))
            pygame.display.update()

        key_dict = {pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_RETURN: False, pygame.K_ESCAPE: False}
        text = ['开始', '帮助', '选项', '退出']
        pos_x = window_size[0] // 2
        pos_y = 350

        repaint()
        while True:
            key_dict = {key: False for key in key_dict}
            key_dict = receive_keyboard(key_dict)
            if key_dict[pygame.K_RETURN]:  # enter
                if pos_y == 350:
                    break
                elif pos_y == 430:
                    cls.help_page(screen)
                    repaint()
                elif pos_y == 510:
                    cls.settings_page(screen)
                    repaint()
                elif pos_y == 590:
                    exit(0)
            elif key_dict[pygame.K_UP]:
                if pos_y != 350:
                    pos_y -= 80
            elif key_dict[pygame.K_DOWN]:
                if pos_y != 590:
                    pos_y += 80
            for i in range(350, 670, 80):
                if i == pos_y:
                    pygame.draw.polygon(screen, white, [(pos_x - 100, i + 10),
                                                        (pos_x - 100, i + 30), (pos_x - 90, i + 20)])
                else:
                    pygame.draw.polygon(screen, olive_green, [(pos_x - 100, i + 10),
                                                              (pos_x - 100, i + 30), (pos_x - 90, i + 20)])
            pygame.display.update([pos_x - 100, 360, 11, 300])
        screen.fill(white)
        pygame.display.update()

    @classmethod
    def help_page(cls, screen):
        text = [['按上下左右移动', '按Z射击', '按X使用炸弹', '按Shift慢速', '按ESC暂停', '按Q退出'], ['蓝色提高伤害', '青色增加分数', '紫色增加血量', '橙色增加炸弹']]

        screen.fill(white)
        pos_x = window_size[0] // 2
        pygame.draw.rect(screen, olive_green, [pos_x-main_window[2] // 2, 20, main_window[2], main_window[3]], 0)

        text_surface = h2_font.render('按键操作', True, green)
        screen.blit(text_surface, (pos_x - 200, 130))
        for i in range(6):
            text_surface = h3_font.render(text[0][i], True, white)
            screen.blit(text_surface, (pos_x - 200, 200 + 60 * i))

        text_surface = h2_font.render('道具效果', True, green)
        screen.blit(text_surface, (pos_x + 50, 130))
        for i in range(4):
            text_surface = h3_font.render(text[1][i], True, white)
            screen.blit(text_surface, (pos_x + 50, 200 + 60 * i))

        text_surface = h2_font.render('按ESC返回', True, grey)
        screen.blit(text_surface, (pos_x - 100, main_window[3]-100))

        pygame.display.update()

        key_dict = {pygame.K_RETURN: False, pygame.K_q: False, pygame.K_ESCAPE: False}
        while True:
            key_dict = receive_keyboard(key_dict)
            if key_dict[pygame.K_ESCAPE] or key_dict[pygame.K_RETURN]:
                break
            elif key_dict[pygame.K_q]:
                exit()

    @classmethod
    def settings_page(cls, screen):
        screen.fill(white)
        pos_x = window_size[0] // 2
        pygame.draw.rect(screen, olive_green, [pos_x-main_window[2] // 2, 20, main_window[2], main_window[3]], 0)

        text_surface = h1_font.render('选项', True, green)
        screen.blit(text_surface, (pos_x-50, 100))

        text_surface = h2_font.render('显示:', True, blue)
        screen.blit(text_surface, (pos_x-150, main_window[3]//2-100))
        text_surface = h2_font.render('全屏', True, blue)
        screen.blit(text_surface, (pos_x-50, main_window[3]//2-100))
        text_surface = h2_font.render('窗口', True, blue)
        screen.blit(text_surface, (pos_x+50, main_window[3]//2-100))

        text_surface = h1_font.render('施工中', True, red)
        screen.blit(text_surface, (pos_x - 100, main_window[3]-200))

        text_surface = h2_font.render('按ESC返回', True, grey)
        screen.blit(text_surface, (pos_x - 100, main_window[3]-100))

        pygame.display.update()

        key_dict = {pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_RETURN: False,
                    pygame.K_LEFT: False, pygame.K_RIGHT: False, pygame.K_ESCAPE: False}
        pos_x = 0
        pos_y = 300
        while True:
            key_dict = {key: False for key in key_dict}
            key_dict = receive_keyboard(key_dict)
            if key_dict[pygame.K_ESCAPE]:
                return
            elif key_dict[pygame.K_UP]:
                if pos_y > 300:
                    pos_y -= 100
            elif key_dict[pygame.K_DOWN]:
                if pos_y < 600:
                    pos_y -= 100
            # TODO
            elif key_dict[pygame.K_LEFT]:
                # if
                pass
            elif key_dict[pygame.K_RIGHT]:
                # if
                pass

    @classmethod
    def choose_difficulty_page(cls, screen):
        # difficulty : 等级, 玩家初始血量, 玩家初始B, 刷怪概率, 怪物移速, 怪物弹速, 分数加成(各物品掉落概率)
        difficulties = (
            ('简单', 4, 3, 0.015, 0.8, 1.5, 1,),
            ('中等', 3, 2, 0.025, 1.2, 2.0, 2,),
            ('困难', 2, 2, 0.04, 1.5, 2.5, 4,)
        )
        _difficulty = difficulties[0]
        key_dict = {pygame.K_1: False, pygame.K_2: False, pygame.K_3: False,
                    pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_RETURN: False, pygame.K_ESCAPE: False}

        screen.fill(white)
        pos_x = window_size[0] // 2
        # TODO pos_y use enum?
        pos_y = 350
        pygame.draw.rect(screen, olive_green, [pos_x-main_window[2] // 2, 20, main_window[2], main_window[3]], 0)
        text_surface = h1_font.render('选择难度', True, blue)
        screen.blit(text_surface, (pos_x-100, 100))
        for i in range(3):
            text_surface = h2_font.render(difficulties[i][0], True, white)
            screen.blit(text_surface, (pos_x - 50, 350 + 100 * i))
        pygame.display.update()

        while True:
            key_dict = {key: False for key in key_dict}
            key_dict = receive_keyboard(key_dict)
            if key_dict[pygame.K_1]:
                _difficulty = difficulties[0]
                break
            elif key_dict[pygame.K_2]:
                _difficulty = difficulties[1]
                break
            elif key_dict[pygame.K_3]:
                _difficulty = difficulties[2]
                break
            elif key_dict[pygame.K_RETURN]:
                _difficulty = difficulties[(pos_y - 350) // 100]
                break
            elif key_dict[pygame.K_UP]:
                if pos_y != 350:
                    pos_y -= 100
            elif key_dict[pygame.K_DOWN]:
                if pos_y != 350 + 200:
                    pos_y += 100
            for i in range(350, 350 + 300, 100):
                if i == pos_y:
                    pygame.draw.polygon(screen, white, [(pos_x - 100, i + 10),
                                                        (pos_x - 100, i + 30), (pos_x - 90, i + 20)])
                else:
                    pygame.draw.polygon(screen, olive_green, [(pos_x - 100, i + 10),
                                                              (pos_x - 100, i + 30), (pos_x - 90, i + 20)])
            pygame.display.update([pos_x - 100, 360, 11, 300])
        player.hp = _difficulty[1]
        player.bomb = _difficulty[2]
        screen.fill(white)
        pygame.display.update()
        return _difficulty

    @classmethod
    def enter_name_page(cls, screen):
        # back_image = pygame.image.load('logo2.jpg').convert()
        text = ''
        key_dict = {pygame.MOUSEBUTTONDOWN: False, 8: False, pygame.K_RETURN: False}
        for key in range(48, 128):
            key_dict[key] = False
        screen.fill(white)
        pos_x = window_size[0] // 2
        pos_y = window_size[1] // 2
        pygame.draw.rect(screen, olive_green, [pos_x-main_window[2] // 2, 20, main_window[2], main_window[3]], 0)

        message_box = [pos_x-150, pos_y-150, 300, 70]
        submit_button = [pos_x-150, pos_y+50, 300, 80]
        # screen.blit(back_image, (400, 100))
        # submit button
        screen.set_clip(submit_button)  # submit button's location
        screen.fill(grey)  # submit button's color
        screen.blit(h2_font.render('确认', True, white), (pos_x-30, pos_y+70))
        screen.set_clip(message_box)
        screen.fill(grey)
        screen.blit(h2_font.render('name:', True, white), (pos_x-120, pos_y-135))
        pygame.display.update()

        while True:
            key_dict = {key: False for key in key_dict}
            key_dict = receive_keyboard(key_dict)
            if key_dict[pygame.K_BACKSPACE] and len(text) > 0:
                text = text[:-1]
            elif key_dict[pygame.K_RETURN] and len(text) > 0:
                break
            # elif key_dict[pygame.MOUSEBUTTONDOWN] and len(text) > 0:
            #     x, y = pygame.mouse.get_pos()
            #     if submit_button[0] < x < submit_button[0]+submit_button[2]  \
            #             and submit_button[1] < y < submit_button[1]+submit_button[3]:
            #         break
            else:
                for key in range(48, 128):
                    if key_dict[key]and len(text) < 8:
                        text += chr(key)
            # message box
            screen.fill(grey)
            screen.blit(h2_font.render('name:', True, white), (pos_x-120, pos_y-135))
            screen.blit(h2_font.render(text, True, white), (pos_x-15, pos_y-135))
            pygame.display.update(message_box)
        screen.set_clip()

        player.name = text


def timer(conf):
    def metric(fn):
        def wrap(*args, **kw):
            if conf:
                time1 = time()
                result = fn(*args, **kw)
                time2 = time()
                print('%s executed in %s ms' % (fn.__name__, time2 - time1))
            else:
                result = fn(*args, **kw)
            return result
        return wrap
    return metric


def init_screen():
    global window_size, main_window

    # info_object = pygame.display.Info()
    # window_width = info_object.current_w
    # window_height = info_object.current_h
    # scaling_factor = [window_width / 1920, window_height / 1080]
    window_width = 1280
    window_height = 800
    window_size = [window_width, window_height]
    main_window_width = 660
    main_window_height = round(window_height - 40)
    main_window = [100, 20, main_window_width, main_window_height]
    # 左上(40, 20)　右上(700, 20) 左下(40, 780) 右下(700, 780)

    # ctypes.windll.user32.SetProcessDPIAware()
    # true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))

    # true_res
    if FULL_SCREEN:
        new_screen = pygame.display.set_mode(window_size, pygame.FULLSCREEN, 32)
    else:
        new_screen = pygame.display.set_mode(window_size, 0, 32)
    pygame.display.set_caption('Shot')
    return new_screen


def reset_all():
    global difficulty, player, press, current_frame, game_is_on

    try:
        tmp = player.name
        del player
        player = Player(4)
        player.name = tmp
    except NameError:
        player = Player(4)
    Monster.monsters = []
    Bullet.player_bullets = []
    Bullet.monster_bullets = []
    Item.items = []
    press = {
        pygame.K_UP: False, pygame.K_DOWN: False,
        pygame.K_LEFT: False, pygame.K_RIGHT: False,
        pygame.K_LSHIFT: False, pygame.K_z: False,
        pygame.K_x: False, pygame.K_v: False,
    }
    current_frame = 0
    game_is_on = True


def draw_info_column(screen):
    global high_score_list

    pos_x = main_window[0]+main_window[2]+100

    pygame.draw.rect(screen, white, [pos_x, 100, 300, 30], 0)
    if len(high_score_list) != 0 and int(high_score_list[0][2]) >= player.score:
        text_surface = h3_font.render('High score:'+high_score_list[0][2], True, blue)
    else:
        text_surface = h3_font.render('High score:'+'0' * (9-len(str(player.score))) + str(player.score), True, blue)
    screen.blit(text_surface, (pos_x, 100))

    pygame.draw.rect(screen, white, [pos_x, 150, 300, 30], 0)
    text_surface = h3_font.render('Score:     ' + '0' * (9-len(str(player.score))) + str(player.score), True, blue)
    screen.blit(text_surface, (pos_x, 150))

    pygame.draw.rect(screen, white, [pos_x, 230, 150, 30], 0)
    text_surface = h3_font.render('Player:' + str(player.hp), True, blue)
    screen.blit(text_surface, (pos_x, 230))

    pygame.draw.rect(screen, white, [pos_x, 270, 150, 30], 0)
    text_surface = h3_font.render('Spell:' + str(player.bomb), True, blue)
    screen.blit(text_surface, (pos_x, 270))

    pygame.draw.rect(screen, white, [pos_x, 350, 150, 30], 0)
    text_surface = h3_font.render('Power:' + str(player.power), True, blue)
    screen.blit(text_surface, (pos_x, 350))

    pygame.draw.rect(screen, white, [pos_x, 400, 150, 30], 0)
    text_surface = h3_font.render('Graze:' + str(player.graze), True, blue)
    screen.blit(text_surface, (pos_x, 400))

    _upper_point = 1100
    for _point in Player.point_list:
        if _point > player.point:
            _upper_point = _point
            break
    pygame.draw.rect(screen, white, [pos_x, 450, 200, 30], 0)
    text_surface = h3_font.render('Point:' + str(player.point) + '/' + str(_upper_point), True, blue)
    screen.blit(text_surface, (pos_x, 450))


def draw_fps(screen):
    fps = round(current_frame / (time() - main_loop_start_time - player.death_time*0.75), 1)
    text_surface = h3_font.render('FPS:' + str(fps), True, grey)
    screen.blit(text_surface, (main_window[0]+10, 30))


@timer(USE_TIMER)
def paint_all(screen):
    draw_info_column(screen)

    screen.set_clip(main_window)
    screen.fill(olive_green)

    draw_fps(screen)
    Item.draw(screen)
    Bullet.draw(screen, Bullet.player_bullets, (150, 150, 200))
    player.draw(screen)
    Bullet.draw(screen, Bullet.monster_bullets, white)
    Monster.draw(screen)

    screen.set_clip()
    pygame.display.update([main_window, [main_window[0]+main_window[2]+100, 100, 300, 400]])


def start_game():
    global main_loop_start_time, game_is_on, max_fps, press, current_frame

    main_loop_start_time = time()
    while game_is_on:
        if max_fps == 0 or (time() - main_loop_start_time - player.death_time*0.75) * max_fps > current_frame:
            current_frame += 1

            # to avoid use spells at a time
            press[pygame.K_x] = False
            press = receive_keyboard(press)
            player.move(press)
            player.make_action(press)

            Monster.generate_monster(difficulty[3], max_monster)
            for monster in Monster.monsters:
                monster.shot(current_frame)
            Monster.move()
            # print(Monster.monsters)
            Bullet.player_bullets_move()
            Bullet.monster_bullets_move()
            Item.move()
            Monster.check_monster_die()
            player.check_graze()
            player.check_reach_top()
            player.check_hit_items()
            player.check_invincible()
            if player.check_hit_bullet() and player.is_invincible == False:
                player.die()

            paint_all(screen)


def end_game(status):
    global screen, high_score_list

    screen.fill(white)
    # TODO put in enter_name_page
    text_surface = h1_font.render('Score:' + str(player.score), True, blue)
    screen.blit(text_surface, (window_size[0] // 2 - 100, 300))
    text_surface = h1_font.render('Time:' + str(round(time() - main_loop_start_time, 2)), True, blue)
    screen.blit(text_surface, (window_size[0] // 2 - 100, 400))
    pygame.display.update()
    sleep(2)

    if ENTER_USER_NAME:
        Game.enter_name_page(screen)

    if status == 1:
        pass
    elif status == 2:
        screen.fill(white)
        if File.use_file:
            high_score_list = File.write(high_score_list)
            show_high_score_page(screen, high_score_list)


def request_restart():
    key_dict = {pygame.K_RETURN: False, pygame.K_q: False, pygame.K_ESCAPE: False}
    while True:
        key_dict = receive_keyboard(key_dict)
        if key_dict[pygame.K_q]:
            return False
        elif key_dict[pygame.K_RETURN]:
            return True


def pause():
    global main_loop_start_time

    text_surface = h3_font.render('Paused', True, red)
    screen.blit(text_surface, (main_window[0]+main_window[2]-90, 30))
    pygame.display.update()

    pause_begin_time = time()

    # 过滤多余事件
    event = pygame.event.wait()
    key_dict = {pygame.K_RETURN: False, pygame.K_q: False, pygame.K_ESCAPE: False}
    while True:
        key_dict = receive_keyboard(key_dict)
        if key_dict[pygame.K_ESCAPE] or key_dict[pygame.K_RETURN]:
            break
        elif key_dict[pygame.K_q]:
            exit()

    pause_end_time = time()
    main_loop_start_time += pause_end_time-pause_begin_time

    pygame.draw.rect(screen, olive_green, [main_window[0]+main_window[2]-90, 30, 90, 50], 0)
    pygame.display.update()


def receive_keyboard(wait_for_dict={}):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key in wait_for_dict:
                wait_for_dict[event.key] = True
            elif event.key == pygame.K_q:
                exit()
            elif event.key == pygame.K_ESCAPE:
                pause()
        elif event.type == pygame.KEYUP:
            if event.key in wait_for_dict:
                wait_for_dict[event.key] = False
    return wait_for_dict


def show_high_score_page(screen, score_list):
    max_len = max(len(score[2]) for score in score_list)
    for j in range(5):
        screen.fill(white)
        pos_x = main_window[0] + main_window[2] + 100
        text_surface = h1_font.render('player', True, blue)
        screen.blit(text_surface, (window_size[0] // 2 - 200, 100))
        text_surface = h1_font.render('score', True, blue)
        screen.blit(text_surface, (window_size[0] // 2 + 100, 100))
        for i in range(min(len(score_list), 10)):
            if (j & 1 == 0) or score_list[i][-1] != -1:
                text_surface = h2_font.render(score_list[i][0], True, blue)
                screen.blit(text_surface, (window_size[0] // 2 - 200, 200 + i * 50))
                text_surface = h2_font.render(' '*(max_len-len(score_list[i][2]))+score_list[i][2], True, blue)
                screen.blit(text_surface, (window_size[0] // 2 + 80, 200 + i * 50))
        pygame.display.update()
        sleep(0.4)
    sleep(1)


# 11/33

# processing
# TODO class game (processing)
# TODO settings page (processing)
# TODO player and bomb use shape (processing)
# TODO (error) graze count by frame (processing)
# TODO change shape when moving right or left (processing)

# postponed
# TODO adapt resolution (postponed)
# TODO able to choose character (postponed)
# TODO generate monster and bullets according to custom setting config (postponed)

# optional
# TODO score//10 (optional)
# TODO overlapping of Monster.monsters (optional)
# TODO item_drop use py_game.draw.rect (optional)

# skipped
# TODO use blocks to accelerate the check of collision (skipped)
# TODO able to change size of Monster.monsters' bullets (skipped)

# done
# TODO pause (done)
# TODO help page (done)
# TODO difficulty (done)
# TODO restart game (done)
# TODO uniform font (done)
# TODO invincible time (done)
# TODO high score list (done)
# TODO (bug) pause time (done)
# TODO non-tracking bullets (done)
# TODO fullscreen or window (done)
# TODO enter high_score name (done)
# TODO info_column add things (done)
# TODO beautify the score page (done)
# TODO show paused on the screen (done)
# TODO restrict the length of name (done)
# TODO able to move Monster.monsters (done)
# TODO refactoring check_monster_die (done)


if __name__ == '__main__':
    if File.use_file:
        high_score_list = File.read()

    max_fps = 120
    max_bullet = 1000
    max_monster = 100
    black = (0, 0, 0)
    red = (200, 0, 0)
    green = (0, 200, 0)
    blue = (100, 100, 200)
    grey = (120, 120, 120)
    white = (230, 230, 230)
    olive_green = (50, 100, 100)

    pygame.init()
    screen = init_screen()
    h1_font = pygame.font.SysFont('SimHei', 45)
    h2_font = pygame.font.SysFont('SimHei', 35)
    h3_font = pygame.font.SysFont('SimHei', 25)

    reset_all()
    Game.start_page(screen)
    difficulty = Game.choose_difficulty_page(screen)
    start_game()
