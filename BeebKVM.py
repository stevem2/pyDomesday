import BeebCfg
import pygame
import pygame.freetype
from math import sqrt,atan2
if BeebCfg.useCV2:
  try:
    import cv2
    BeebCfg.useCV2 = True
    print('Using OpenCV and mp4 files')
  except:
    BeebCfg.cv2 = False
    print('OpenCV not available.')


class Beebkvm:
  def __init__(self):
    self.dispX = BeebCfg.DispX
    self.dispY = BeebCfg.DispY
    self.imgX = self.dispX 
    self.imgY = self.dispY 
    self.iOffX = 0 
    self.iOffY = 0 
    self.scrX = int(0.75*self.dispX) 
    self.scrY = int(0.875* self.dispY)
    self.offX = int(0.125*self.dispX)
    self.offY = int(0.06*self.dispY)
    #
    self.cliDispatch = {
      'FCODE':self.fcode,'*POINTER':self.setMouseVisibility,'*TSET':self.setMousePosn
      }
  # ------------------------------------------------------------------------------  

  def cli(self,l):
    self.dispatched = True   # May be set to false by fcode
    if l[0] in self.cliDispatch:
      self.cliDispatch[ l[0] ](l)
      #print('kvm dispatched %s' % l[0])
      return self.dispatched
    else: return False
    
  def fcode(self,l):
    if l[1] == 'VPX': self.queryVP()
    elif l[1] in ('VP1','VP2','VP3','VP4','VP5','VP6'): self.setMixMode( int(l[1][-1:]) )
    else: self.dispatched = False
    
  def disk(self,name):
    if BeebCfg.useCV2:
      self.FOffset = BeebCfg.Disks[name]['mp4Offset']
      self.mp4 = cv2.VideoCapture(BeebCfg.Disks[name]['mp4File'])
    else:
      self.FOffset = BeebCfg.Disks[name]['Offset']
      self.frameForm = BeebCfg.Disks[name]['frameForm']
    self.frame = 0
  
  # --------------------------------------------------------------------------------
  def initialize(self):
    pygame.init()
    self.screen = pygame.display.set_mode((self.dispX,self.dispY))
    self.clock = pygame.time.Clock()
    self.FPS = 25
    self.font = pygame.freetype.Font('./font2.bdf')
    self.Main = pygame.Surface((1280+1,1024))
    self.Shadow = pygame.Surface((1280+1,1024))
    self.s = self.Main
    self.changed = True
    #
    self.defaultKey = (0,0,0)
    self.highlightKey = (0,0,255)
    self.s.set_colorkey(self.defaultKey)
    #
    self.sound = pygame.mixer.Sound('./beep.wav')
    #
    self.MixMode = 3
    self.oldMixMode = 3
    #
    self.mouseX, self.mouseY = 0,0
    self.mouseVisible = False
    yellow = (255,255,0)
    red = (255,0,0)
    green = (0,255,0)
    self.pointer = [pygame.Surface((16,16)),pygame.Surface((16,16)),\
                    pygame.Surface((16,16)),pygame.Surface((16,16))]
    pygame.draw.polygon(self.pointer[0],yellow,\
      [(6,0),(6,6),(0,6),(0,8),(6,8),(6,15),(8,15),(8,8),(15,8),(15,6),(8,6),(8,0)])
    pygame.draw.polygon(self.pointer[2],yellow,\
      [(4,16),(0,0),(16,4),(8,8),(4,16)])
    pygame.draw.rect(self.pointer[1],red,(1,1,14,14))
    pygame.draw.rect(self.pointer[3],green,(1,1,14,14))
    for i in range(4): self.pointer[i].set_colorkey(self.defaultKey)
    self.currentPointer = self.pointer[0]
    pygame.mouse.set_visible(False)
    #  
    self.keyPressed = False
    self.BeebKey = 0x00
    self.pykeys = {
    	pygame.K_F1:0x8c,pygame.K_F2:0x8d,pygame.K_F3:0x8e,pygame.K_F4:0x8f,
    	pygame.K_F5:0x90,pygame.K_F6:0x91,pygame.K_F7:0x92,pygame.K_F8:0x93,
    	pygame.K_F9:0x94,pygame.K_F10:0x95,
    	pygame.K_INSERT:0x97,pygame.K_LEFT:0x98,pygame.K_RIGHT:0x99,
    	pygame.K_DOWN:0x9a,pygame.K_UP:0x9b,pygame.K_BACKSPACE:0x7f
    	}
    #
  
  def setMixMode(self,i):
    self.changed = True
    if i == 6: self.MixMode = self.oldMixMode
    else:
      self.oldMixMode = self.MixMode
      self.MixMode = i
  
  def queryVP(self):
    BeebCfg.FCresponse = b'VP%1i\r' % self.MixMode 
        
  def display(self, n):
    if n == 0: self.s = self.Main
    else: self.s = self.Shadow

  def setPointer(self, n):
    self.currentPointer = self.pointer[n]
    
  def pygame2beeb(self,x,y): 
    x, y = (x-self.offX)*1280.0/self.scrX, 1024-(y-self.offY)*1024.0/self.scrY
    x, y = max(x,0), max(y,0) 
    x, y = min(x, 1280), min(y,1024)
    return int(x),int(y)
    
  def beeb2pygame(self,x,y): return int(x*self.dispX/1280.0), self.dispY-int(y*self.dispY/1024.0)

# -------------------------------------------------------------------------
  def drawChr(self,c, point, colour):
    #self.s.blit(self.font.render(c,True,colour),(point[0],1014-point[1]))
    self.font.render_to(self.s,(point[0],1024-point[1]),c,fgcolor=colour)
    self.changed = True
    
  def drawLine(self, fromPt, toPt, colour, fill=None):
    pygame.draw.line(self.s, colour, (fromPt[0]-1, 1024-fromPt[1]), (toPt[0]-1, 1024-toPt[1]),2)
    self.changed = True

  def drawRect(self, fromPt, toPt, colour, fill=None):
    left, top = min(fromPt[0],toPt[0]), min(1024-fromPt[1], 1024-toPt[1])
    width, height = abs(fromPt[0]-toPt[0])+1, abs(fromPt[1]-toPt[1])+1
    pygame.draw.rect(self.s,colour,(left, top, width, height))
    self.changed = True

  def drawPoly(self, points, colour, fill=None):
    pts = []
    for p in points: pts.append( (p[0],1024-p[1]) )
    pygame.draw.polygon(self.s, colour, pts)
    self.changed = True
    
  def drawSector(self,xc,yc,x1,y1,x2,y2,colour, fill=None):
    deg = 180.0/3.142
    radius = sqrt((x1-xc)*(x1-xc)+(y1-yc)*(y1-yc))
    rect = [xc-radius,1024-yc-radius,2*radius,2*radius]
    start = atan2(y1-yc,x1-xc)
    end = atan2(y2-yc,x2-xc)
    if colour == (0,0,0): colour = (128,128,128)
    pygame.draw.arc(self.s, colour, rect, start,end,int(radius))
    self.changed = True
# -------------------------------------------------------------------------

  def setMouseVisibility(self,l):
    if l[1] == '1': self.mouseVisible = True
    elif l[1] == '2': self.mouseVisible = False
    else: self.mouseVisible = False

  def mousePosn(self): return self.pygame2beeb(self.mouseX, self.mouseY)
    
  def mouseButton(self):
    y = 0
    if self.button == 1: y = y & 0x02
    if self.button == 3: y = y & 0x01
    self.button = 0
    return y

  def setMousePosn(self, l):
    #print('set mouse %s %s' % (l[1],l[2]))
    self.changed = True
    x, y = int(l[1][:-1]), int(l[2])
    x, y = self.beeb2pygame(x,y)
    self.mouseX = x
    self.mouseY = y
    pygame.mouse.set_pos([x,y])

# ----------------------------------------------------------------

  def inkey(self):
    if self.keyPressed:
      self.keyPresed = False
      b = self.BeebKey
      self.BeebKey = 0
    else: b = 0
    return b
    
# ---------------------------------------------------------------
  def beep(self,i):
    self.sound.play(maxtime=500*(i+1))

# ---------------------------------------------------------------
  def showPointer(self):
    if self.mouseVisible: self.screen.blit(self.currentPointer, (self.mouseX, self.mouseY))
       
  def update(self, lvrom):
    #self.clock.tick(self.FPS)
    #
    if self.changed: self.s1 = pygame.transform.scale(self.s,(self.scrX,self.scrY))
    #
    frame = lvrom.update()
    if self.frame != frame:
      self.changed = True
      if BeebCfg.useCV2:
        if (frame-self.frame) != 1: self.mp4.set(cv2.CAP_PROP_POS_FRAMES,max(frame+self.FOffset,0))
        result, jpgFrame = self.mp4.read()
        cv2.imwrite('/dev/shm/f.jpg',jpgFrame)
        self.s0 = pygame.transform.scale(pygame.image.load('/dev/shm/f.jpg'),(self.imgX,self.imgY))
      else:
        backdrop = self.frameForm % max(frame+self.FOffset,1)
        self.s0 = pygame.transform.scale(pygame.image.load(backdrop),(self.imgX,self.imgY))
      self.frame = frame
    #
    m = self.MixMode
    if self.changed:
      if m in (1,3,4,5): self.screen.blit(self.s0,(self.iOffX,self.iOffY))
      else: self.screen.fill((0,0,0))
      if m in (2,3,4): self.s.set_colorkey(self.defaultKey)
      if m == 5:      
        self.s1.set_colorkey(self.highlightKey)
        self.s1.set_alpha(128)
      if m in(2,3,4,5):
        self.screen.blit(self.s1,(self.offX,self.offY))
        self .showPointer()
    self.changed = False
    #
    pygame.display.flip()
    #
    for event in pygame.event.get():
      if event.type == pygame.MOUSEMOTION:
        self.mouseX, self.mouseY = event.pos[0],event.pos[1]
        self.changed = True
      elif event.type ==   pygame.MOUSEBUTTONDOWN:
        self.button = event.button
        if self.button == 1:
          self.keyPressed = True
          self.BeebKey = 0x0d
        elif self.button == 3:
          self.keyPressed = True
          self.BeebKey = 0x09
        else: pass
        #print('button %i' % self.button)
      elif event.type == pygame.KEYDOWN:
        self.keyPressed = True
        key, mod, uni = event.key, event.mod, event.unicode
        if key == pygame.K_PAUSE: return True
        elif uni == '': self.BeebKey = self.pykeys.get(key,0)
        elif key == pygame.K_BACKSPACE: self.BeebKey = 0x7f
        else: self.BeebKey = bytes(uni.encode('utf-8'))[0]
      elif event.type == pygame.QUIT: return True
      else:
        pass
    return False

  def quit(self):
    pygame.quit()

