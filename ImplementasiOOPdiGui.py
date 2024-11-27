import tkinter as tk
import random

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [random.choice([-2, -1, 1, 2]), -3]  # Randomized start with sharper vertical motion
        self.speed = 3
        item = canvas.create_oval(
            x - self.radius, y - self.radius,
            x + self.radius, y + self.radius,
            fill=random.choice(['white', '#FF69B4', '#87CEFA', '#98FB98']))
        super().__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)
        self.speed += 0.005  # Gradual increase in speed

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 100
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill='#FFA500')
        super().__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super().move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

    def shrink(self):
        if self.width > 40:
            self.width -= 10
        coords = self.get_position()
        self.canvas.coords(self.item,
                           coords[0], coords[1],
                           coords[0] + self.width, coords[3])


class Brick(GameObject):
    COLORS = ['#E74C3C', '#9B59B6', '#1ABC9C', '#F1C40F', '#3498DB']

    def __init__(self, canvas, x, y, hits):
        self.width = 70
        self.height = 20
        self.hits = hits
        color = random.choice(Brick.COLORS)
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill=color, tags='brick')
        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
        else:
            new_color = random.choice(Brick.COLORS)
            self.canvas.itemconfig(self.item, fill=new_color)


class Game(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#101820',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 350)
        self.items[self.paddle.item] = self.paddle

        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 2)
            self.add_brick(x + 37.5, 100, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(15))

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, 'Press Space to Start', 20)
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 340)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size=40, color='#FFFFFF'):
        font = ('Helvetica', size)
        return self.canvas.create_text(x, y, text=text, font=font, fill=color)

    def update_lives_text(self):
        text = f'Lives: {self.lives}'
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15, '#FFFFFF')
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.update_background()
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.draw_text(300, 200, 'YOU WIN!', 30, '#00FF00')
        elif self.ball.get_position()[3] >= self.height:
            self.lives -= 1
            self.paddle.shrink()
            if self.lives <= 0:
                self.draw_text(300, 200, 'GAME OVER!', 30, '#FF0000')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

    def update_background(self):
        colors = ['#101820', '#0F2235', '#1A2749']
        new_color = random.choice(colors)
        self.canvas.config(bg=new_color)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Brick Breaker Reloaded')
    game = Game(root)
    game.mainloop()
