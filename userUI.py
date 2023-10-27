import random, pygame, sys, socket, asyncio, json
from pygame.locals import *
pygame.init()

white = (255, 255, 255)
yellow = (255, 255, 102)
grey = (211, 211, 211)
black = (0, 0, 0)
green = (0, 255, 0)
lightGreen = (153, 255, 204)

font = pygame.font.SysFont("Helvetica neue", 40)
bigFont = pygame.font.SysFont("Helvetica neue", 80)

youWin = bigFont.render("You Win!", True, lightGreen)
youLose = bigFont.render("You Lose!", True, lightGreen)
playAgain = bigFont.render("Play Again?", True, lightGreen)

class Message:

    def __init__(self):
        self.json_size = None
        self.header = None
        self.content_size = None
        self.content = None
        self.encoded_content = None
        self.type = None

    async def read(self, client, loop):
        self.json_size = int.from_bytes(await loop.sock_recv(client, 2), "big")
        self.header = json.loads((await loop.sock_recv(client, self.json_size)).decode("utf-8"))
        self.content_size = self.header['content_size']
        self.type = self.header['response_type']
        if self.content_size != 0:
            self.encoded_content = await loop.sock_recv(client, self.content_size)
            self.content = self.encoded_content.decode("utf-8")
        else:
            self.content = ""
            self.encoded_content = self.content.encode("utf-8")

    def write(self, type, content):
        self.type = type
        self.content = content
        self.encoded_content = self.content.encode("utf-8")
        self.content_size = len(self.encoded_content)
        self.header = json.dumps({'content_size': self.content_size, 'response_type': type}, ensure_ascii=False).encode("utf-8")
        self.json_size = len(self.header)

    async def send(self, client, loop):
        await loop.sock_sendall(client, self.json_size.to_bytes(2, "big"))
        await loop.sock_sendall(client, self.header)
        await loop.sock_sendall(client, self.content)

def draw(mask, guess, turns, window):
    renderList = ["", "", "", "", ""]
    spacing = 0
    guessColorCode = [grey, grey, grey, grey, grey]
    for x in range(0, 5):
        if mask[x] == '1':
            guessColorCode[x] = green
        if mask[x] == '2':
            guessColorCode[x] = yellow
    
    for x in range(0, 5):
        renderList[x] = font.render(guess[x], True, black)
        pygame.draw.rect(window, guessColorCode[x], pygame.Rect(60 +spacing, 50+ (turns * 80), 50, 50))
        window.blit(renderList[x], (70 * spacing, 50 + (turns * 80)))
        spacing += 80
    
    if guessColorCode == [green, green, green, green, green]:
        return True
    else:
        return False

def main():
    height = 600
    width = 500
    FPS = 60
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((width, height))
    window.fill(black)
    for x in range(0,5):
        for y in range(0,5):
            pygame.draw.rect(window, grey, pygame.Rect(60 + (x * 80), 50 + (y * 80), 50, 50), 2)
    pygame.display.set_caption("Wordle - Redes")
    turns = 0
    win = False
    guess = ""
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.exit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                guess += event.unicode.upper()
                if event.key == K_RETURN and win == True:
                    main()
                if event.key == K_RETURN and turns == 6:
                    main()
                if event.key == pygame.K_BACKSPACE or len(guess) > 5:
                    guess = guess[:-1]
                if event.key == K_RETURN and len(guess) > 4:
                    msg = check(turns, guess)
                    win = draw(msg.content, guess, turns, window)
                    turns += 1
                    guess = ""
                    window.fill(black, (0, 500, 500, 200))
        window.fill(black, (0, 500, 500, 200))
        renderGuess = font.render(guess, True, grey)
        window.blit(renderGuess, (180, 530))

        if win == True:
            window.blit(youWin, (90, 200))
            window.blit(playAgain, (60, 300))

        if turns == 6 and win != True:
            window.blit(youLose, (90, 200))
            window.blit(playAgain, (60, 300))
        pygame.display.update()
        clock.tick(FPS)



if __name__ == "__main__":
    main()
