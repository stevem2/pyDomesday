import BeebCfg

# =====================================================================

class py65Mem:
  def __init__(self,m):
    self.m = m
    self.mv = memoryview(m.mv1)
    
  def __getitem__(self,addr):
    if (addr < 0xff00): return self.mv[addr]
    else:
      self.m.os(self.m.cpu, self.m, addr)
      return 0x60 # 6502 RTS instr

  def __setitem__(self,addr,data):
    self.mv[addr] = data

# =====================================================================

class cintMem:
  def __init__(self,m,rw=True):
    self.m = m
    self.mv = memoryview(m.mv2)
    self.mb = memoryview(m.mv2).cast('b')
    self.mH = memoryview(m.mv2).cast('H')
    self.mh = memoryview(m.mv2).cast('h')
    self.mW = memoryview(m.mv2).cast('L')
    self.rw = rw
    
  def __getitem__(self,x):
    self.idx = x
    return self
    
  def osCall(self,addr,a,x,y):
    if self.rw:
      self.m.cpu.a, self.m.cpu.x, self.m.cpu.y = a, x, y
      self.m.os(self.m.cpu, self.m, addr)
    return self.m.cpu.a, self.m.cpu.x, self.m.cpu.y
    
  @property
  def B(self):  return self.mv[self.idx]
  @B.setter
  def B(self,data): 
    if self.rw: self.mv[self.idx] = data

  @property
  def b(self):  return self.mb[self.idx]
  @b.setter
  def b(self,data):
    if self.rw: self.mb[self.idx] = data

  @property
  def H(self):
    if (self.idx > 0x7fff): self.idx = self.idx & 0x7fff   # !!!
    return self.mH[self.idx]
  @H.setter
  def H(self,data):
    if self.rw:  self.mH[self.idx] = data

  @property
  def h(self):  return self.mh[self.idx]
  @h.setter
  def h(self,data): 
    if self.rw:  self.mh[self.idx] = data

  @property
  def W(self):  return self.mW[self.idx]
  @W.setter
  def W(self,data): 
    if self.rw:  self.mW[self.idx] = data

# =====================================================================

class TubeMem:
  def __init__(self):
    #
    self.main = bytearray(0x10000)
    self.side = bytearray(0x10000)
    #
    self.mv = memoryview(self.main)
    self.mv1 = memoryview(self.main)
    self.mv2 = memoryview(self.main)
    self.sv = memoryview(self.side)
    #
    self.cregs =  self.mv[0x00:0x100].cast('H')
    self.cstack = self.mv[0x430:0x800].cast('H')
    self.cglob = self.mv[0x800:0xe00].cast('H')
    #
    self.bank = 0x00
    #
    self.cliDispatch = {
      '*SRWRITE':self.srWrite,'*SRREAD':self.srRead, \
      '*SRROM':self.noopCLI,'*INSERT':self.noopCLI,'*SRDATA':self.noopCLI
      }

  def cli(self,l):
    self.dispatched = True   # May be set to false by fcode
    if l[0] in self.cliDispatch:
      self.cliDispatch[ l[0] ](l)
      #print('Mem dispatched %s' % l[0])
      return self.dispatched
    else: return False
    
  def noopCLI(self,l): pass

  def initialize(self):
    e = BeebCfg.adlDirectory.files['!BOOT']
    load_addr = e.l_addr
    BeebCfg.adlFile.seek(e.ssec*256)
    s = BeebCfg.adlFile.read(e.length)
    l = len(s)
    self.main[load_addr:load_addr+l] = s
    #'''
    # set up global vector
    for i in range(0x300): self.cglob[i] = 0xfc88
    jmp_addr = self.mv[0x0e05] + 0x100*self.mv[0x0e06]
    start_addr = self.mv[jmp_addr - 8] + 0x100*self.mv[jmp_addr - 7]
    end_addr = jmp_addr - 14 
    for i in range(start_addr+2, end_addr, 4):
      addr = self.mv[i] + 0x100*self.mv[i+1]
      value = self.mv[i+2] + 0x100*self.mv[i+3]
      self.mv[addr], self.mv[addr+1] = value & 0xff, (value &0xff00)>>8
    # set up various other values
    for i,j in enumerate([0x02,0x4d,0xfe,0x77]): self.mv[0x0a+i] = j
    for i,j in enumerate([0x84,0x0f,0xfc,0xef,0xff,0xff]): self.mv[0x54+i] = j
    for i,j in enumerate([0x0b,0x4e,0,0,0x96,0x0f]): self.mv[0x1fe+i] = j
    for i,j in enumerate([0x96,0x0f]): self.mv[0x40e+i] = j
    for i,j in enumerate([0x54,0x15,0x00,0x00,0x00,0x00,0xa0,0x00]): self.mv[0x410+i] = j
    for i,j in enumerate([0xb1,0x06,0xa8,0xe6,0x06,0xf0,0x0d,0xbe]): self.mv[0x418+i] = j
    for i,j in enumerate([0xe2,0x17,0x86,0x52,0xbe,0xe2,0x18,0x86]): self.mv[0x420+i] = j
    for i,j in enumerate([0x53,0x6c,0x52,0x00,0xe6,0x07,0xd0,0xef]): self.mv[0x428+i] = j
    for i,j in enumerate([0xfe,0x77]): self.mv[0x86c+i] = j
    for i,j in enumerate([0xfe,0x77,0,0]): self.mv[0x4a5c+i] = j
    for i,j in enumerate([0xff,0xff]): self.mv[0xeffe+i] = j
    #'''
    
  def setos(self,os,cpu):
    self.os = os
    self.cpu = cpu

  def __getitem__(self,addr):
    if (addr < 0xff00): return self.mv[addr]
    else:
      self.os(self.cpu, self, addr)
      return 0x60 # 6502 RTS instr

  def __setitem__(self,addr,data):
    self.mv[addr] = data

  def get(self,start,length):
    return self.mv[start:start+length]

  def getString(self,addr):
    i = addr
    s = ''
    while self.mv[i] != 0x0d:
      s += chr(self.mv[i])
      i +=1
    return s

  def load(self,block,start,end):
    xfer = len(block)
    self.mv[start:start+xfer] = block[0:xfer]

  def xferToSide(self,bank,main_addr,side_addr,length):
    self.sv[side_addr:side_addr+length] = self.mv[main_addr:main_addr+length]

  def xferFromSide(self,bank,main_addr,side_addr,length):
    self.mv[main_addr:main_addr+length] = self.sv[side_addr:side_addr+length]

  def srWrite(self,l):
    main_addr = int(l[1],16) & 0x0000ffff
    length = int(l[2][1:],16)
    side_addr = int(l[3],16)
    if len(l) == 5:  sa = (int(l[4])-4)*0x4000 + (side_addr & 0x7fff)
    else:  sa = side_addr
    self.xferToSide(0,main_addr,sa,length)

  def srRead(self,l):
    main_addr = int(l[1],16) & 0x0000ffff
    length = int(l[2][1:],16)
    side_addr = int(l[3],16)
    if len(l) == 5:  sa = (int(l[4])-4)*0x4000 + (side_addr & 0x7fff)
    else:  sa = side_addr
    self.xferFromSide(0,main_addr,sa,length)



