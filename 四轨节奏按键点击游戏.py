import gc; gc.collect()
import framebuf
from machine import SPI, Pin
import st7789
import utime
import urandom as random


spi = SPI(0, baudrate=40000000, polarity=1, phase=0, bits=8, endia=0, sck=Pin(6), mosi=Pin(8))
display = st7789.ST7789(spi, 240, 240, reset=Pin(11,func=Pin.GPIO, dir=Pin.OUT), dc=Pin(7,func=Pin.GPIO, dir=Pin.OUT))
display.init()
display.fill(0x0000)

BLACK=0x0000; WHITE=0xFFFF; BLUE=0x001F; GREEN=0x07E0
score_left=0; score_right=0
score_left=0; score_right=0
BTN_PINS=[2,1,0,14]                            
buttons=[Pin(p,func=Pin.GPIO,dir=Pin.IN,pull=Pin.PULL_DOWN) for p in BTN_PINS]     
prev_btn=[0,0,0,0]                    
JUDGE=230; LANE_W=60; NOTE_H=10; SPEED=100

ERASE_BUF=bytearray(60*10*2)
NOTE_BUF=bytearray(60*10*2)
fb_erase=framebuf.FrameBuffer(ERASE_BUF,60,10,framebuf.RGB565)
fb_note=framebuf.FrameBuffer(NOTE_BUF,60,10,framebuf.RGB565)
fb_erase.fill(BLACK); fb_note.fill(WHITE)

JUDGE_BUF=bytearray(240*10*2)
fb_judge=framebuf.FrameBuffer(JUDGE_BUF,240,10,framebuf.RGB565)
fb_judge.fill(GREEN)
display.blit_buffer(JUDGE_BUF,0,JUDGE,240,10)

SCORE_BUF=bytearray(240*20*2)
fb_score=framebuf.FrameBuffer(SCORE_BUF,240,20,framebuf.RGB565)
def draw_score():
    fb_score.fill(BLACK)
    t=str(score_left)+"-"+str(score_right)
    x=(240-len(t)*8)//2
    y=(20-8)//2
    fb_score.text(t,x,y,WHITE)
    display.blit_buffer(SCORE_BUF,0,0,240,20)
draw_score()

SCREENS = [
    (["Four-Lane Rhythm Game"], 0),
    (["Score format: Left - Right"], 0),
    (["Left: successful hits", "Right: total presses"], 0),
    (["Press correct key when", "note hits judgement line"], 0),
    (["Game over when", "misses exceed 30"], 1),
]
PROMPTS = ["Press any key to continue", "Press any key to start"]

LINE_BUF = bytearray(240 * 8 * 2)
fb_line = framebuf.FrameBuffer(LINE_BUF, 240, 8, framebuf.RGB565)

def wait_any_button():
    while True:
        for b in buttons:
            if b.value():
                utime.sleep_ms(250)
                return

for si in range(5):
    display.fill(BLACK)
    lines, pidx = SCREENS[si]
    prompt = PROMPTS[pidx]
    total_h = len(lines) * 8 + (len(lines) - 1) * 8
    start_y = 20 + (180 - total_h) // 2
    for line in lines:
        fb_line.fill(BLACK)
        x = (240 - len(line) * 8) // 2
        fb_line.text(line, x, 0, WHITE)
        display.blit_buffer(LINE_BUF, 0, start_y, 240, 8)
        start_y += 16
    fb_line.fill(BLACK)
    x = (240 - len(prompt) * 8) // 2
    fb_line.text(prompt, x, 0, WHITE)
    display.blit_buffer(LINE_BUF, 0, 216, 240, 8)
    wait_any_button()
    gc.collect()
gc.collect()

display.fill(BLACK)

class Note:
    def __init__(self,lane):
        self.lane=lane; self.x=lane*LANE_W; self.y=20; self.alive=True; self.old_y=None;self.hit=False
    def move(self,dt):
        if not self.alive: return
        self.y+=SPEED*dt
        if self.y-NOTE_H>=240: self.alive=False

notes=[]; last_spawn=0; last_tick=utime.ticks_ms()
start=utime.ticks_ms()                   
while True:
    now=utime.ticks_ms()
    dt=utime.ticks_diff(now,last_tick)/1000.0
    if dt>0.05: dt=0.05
    if score_right - score_left > 30: break 
    last_tick=now
    for lane in range(4):
        val=buttons[lane].value()
        if prev_btn[lane]==0 and val==1:
            score_right+=1
            for n in notes:
                if n.lane==lane and not n.hit and JUDGE-NOTE_H<int(n.y)<JUDGE:
                    display.blit_buffer(ERASE_BUF, n.x, int(n.y), 60, 10)
                    n.alive=False
                    n.hit=True
                    score_left+=1
                    break
        prev_btn[lane]=val
    if utime.ticks_diff(now,last_spawn)>500:
        lane=random.getrandbits(2)&3; notes.append(Note(lane))
        if random.getrandbits(1):
            l2=(lane+1+random.getrandbits(1))&3
            if l2!=lane: notes.append(Note(l2))
        last_spawn=now
    
    for n in notes[:]:
        n.old_y=int(n.y); n.move(dt)
        if not n.alive or int(n.y)>=JUDGE: notes.remove(n)
    
    for n in notes:
        if n.old_y is not None and n.old_y<JUDGE:
            display.blit_buffer(ERASE_BUF,n.x,n.old_y,60,10)
    for n in notes:
        iy=int(n.y)
        if iy<JUDGE:
            h=min(NOTE_H,JUDGE-iy)
            if h<NOTE_H:
                fb_note.fill(BLUE)
                fb_note.fill_rect(0,0,60,h,WHITE)
            else:
                fb_note.fill(WHITE)
            display.blit_buffer(NOTE_BUF,n.x,iy,60,10)
    display.blit_buffer(JUDGE_BUF,0,JUDGE,240,10)
    draw_score()
    gc.collect()

display.fill(BLACK)
line1 = "Successful hits: " + str(score_left)
line2 = "Total presses: " + str(score_right)
lines = [line1, line2]
total_h = len(lines) * 8 + (len(lines) - 1) * 8
start_y = 20 + (180 - total_h) // 2
for line in lines:
    fb_line.fill(BLACK)
    x = (240 - len(line) * 8) // 2
    fb_line.text(line, x, 0, WHITE)
    display.blit_buffer(LINE_BUF, 0, start_y, 240, 8)
    start_y += 16
prompt = "Press any key to exit"
fb_line.fill(BLACK)
x = (240 - len(prompt) * 8) // 2
fb_line.text(prompt, x, 0, WHITE)
display.blit_buffer(LINE_BUF, 0, 216, 240, 8)
wait_any_button()
raise SystemExit