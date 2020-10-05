##########################################################################
#   pyDomesday emulates the 1986 BBC Domesday system.                    #
#   Copyright (C) 2020  Steve M.                                         #
#                                                                        # 
#   This program is free software: you can redistribute it and/or modify #
#   it under the terms of the GNU General Public License  version 3 as   #
#   published by the Free Software Foundation.                           # 
#                                                                        #
#   This program is distributed in the hope that it will be useful,      #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of       #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
#   GNU General Public License for more details.                         #
##########################################################################

import sys
import struct
import time
import datetime
#
import BeebCfg
#

registry = {}
oswrch = 0xffee; osasci = 0xffe3; oscli  = 0xfff7; osnewl = 0xffe7; osbyte = 0xfff4
osfile = 0xffdd; osfind = 0xffce; osword = 0xfff1; osgbpb = 0xffd1; osargs = 0xffda

# ====================================================================
class VFSDentry():
    def __init__(self,entry):
        f = struct.Struct('=10B 3I 4B')
        c0,c1,c2,c3,c4,c5,c6,c7,c8,c9, self.l_addr, self.x_addr, self.length, l3,l2,l1, self.seq = f.unpack(entry)
        s = chr(c0 & 0x7f) + chr(c1 & 0x7f) + chr(c2 & 0x7f) + chr(c3 & 0x7f) \
            + chr(c4) + chr(c5) + chr(c6) + chr(c7) + chr(c8) + chr(c9)
        self.name = s.rstrip(chr(0x00))
        self.ssec = ((l1*256)+l2)*256 + l3
        self.R =  (c0 & 0x80 == 0x80)
        self.W =  (c1 & 0x80 == 0x80)
        self.L =  (c2 & 0x80 == 0x80)
        self.D =  (c3 & 0x80 == 0x80)
        return None

class VFSDir():
    def __init__(self,start=0x200):
        sectorlen = 0x100
        f = struct.Struct('=x 10s 3B 33s B 4s x')
        BeebCfg.adlFile.seek(start,0)
        s = BeebCfg.adlFile.read(5*sectorlen)
        self.files = {}
        self.data = {}
        #now = time()
        for i in range(0,47):
           e = VFSDentry(s[5+i*26:5+(i+1)*26])
           if e.name != '':
             self.files[e.name] = e
        #print(self.files.keys())
        return None

# ====================================================================

def osFnc(vec, subfnc=None):
  def _osFnc(f):
    registry[(vec,subfnc)] = f
    return f
  return _osFnc

class MOS:
  def __init__(self,mem,lvrom,kvm):
    self.mem = mem
    self.lvrom = lvrom
    self.kvm = kvm
    #
    self.next_handle = 1
    self.files = {}
    self.fm1 = struct.Struct('< H L L L L')
    self.fm2 = struct.Struct('< B L H B H')
    self.fm3 = struct.Struct('< B L L L')
    #
    self.PrDriver = 1
    self.outputSelection = 0
    # Graphics positions
    self.oldx = 0; self.oldy = 0
    self.x = 0; self.y = 0
    self.newx = 0 ; self.newy = 0
    # Mouse positions
    self.pointerX = 128
    self.pointerY = 128
    self.pointerMaxX = 640 #1280
    self.pointerMaxY = 512 #1024
    # Colours
    self.PhysicalColours = [
      # black    red        green      yellow       blue       magenta       cyan        white
      (0,0,0), (255,0,0), (0,255,0), (255,255,0), (0,0,255), (255,0,255), (0,255,255), (255,255,255),
      (1,1,1), (254,0,0), (0,254,0), (254,254,0), (0,0,254), (254,0,254), (0,254,254), (254,254,254)]
    self.LogicalColours = []
    for i in [0,1,3,7,0,1,3,7,8,9,11,15,8,9,11,15]: self.LogicalColours.append(self.PhysicalColours[i])
    self.ECFColours = [(128,0,255),(0,255,128),(255,128,0),(200,100,50)]
    self.foreground = self.LogicalColours[1]
    self.background = self.LogicalColours[0]
    #
    self.cliDispatch = {
      'MOUSE':self.noopCLI,'FONT2':self.setfont2,'FCODE':self.fcode,'*TMAX':self.setMouseChange
      }
    #
    self.chrDispatch = {
     0:(self.u,1),1:(self.uu,2),2:(self.u,1),3:(self.u,1),4:(self.wtatt,1),5:(self.wtatg,1),6:(self.u,1),\
     7:(self.beep,1),8:(self.u,1),9:(self.u,1),10:(self.cursorNL,1),11:(self.u,1),\
     12:(self.clrtextarea,1),13:(self.cursorCR,1),14:(self.u,1),15:(self.u,1),\
     16:(self.u,1),17:(self.VDU17,2),18:(self.VDU18,3),19:(self.VDU19,6),\
     20:(self.u,1),21:(self.u,1),22:(self.VDU22,2),23:(self.VDU23,10),\
     24:(self.VDU24,9),25:(self.VDU25,6),26:(self.rstdefwins,1),27:(self.u,1),\
     28:(self.uu,5),29:(self.uu,5),30:(self.mvtxtcur,1),31:(self.VDU28,3),\
     127:(self.u,1)
      }
    #
    self.writeChr = self.writeChrFirst
    #
    self.font = {}
    for i in range(256): self.font[i] = bytearray('        '.encode('utf-8') )
    self.fontChange = False
    #

  def __call__(self,cpu,mem,addr):
    fnc = addr # mem.osCall
    if (fnc,None) in registry:
      #print('         0x%04x 0x%02x 0x%02x 0x%02x' % (fnc,cpu.a,cpu.x,cpu.y))
      registry[(fnc,None)](self,cpu,mem)
    elif (fnc,cpu.a) in registry :
      #print('         0x%04x 0x%02x 0x%02x 0x%02x' % (fnc,cpu.a,cpu.x,cpu.y))
      registry[(fnc,cpu.a)](self,cpu,mem)
    else:
      print('Unimplemented OS Call %04x: A = %02x X = %02x Y = %02x'% (fnc,cpu.a,cpu.x,cpu.y))

  def getParams(self,cpu,mem,length,fmx):
    start = cpu.y*0x100 + cpu.x
    block = mem.mv[start:start+length]
    return block, fmx.unpack(block)

  @osFnc(oswrch)
  def oswrch(self,cpu,mem):
    self.writeChr(cpu.a)

  @osFnc(osasci)
  def osasci(self,cpu,mem):
    self.oswrch(cpu,mem)

  @osFnc(osnewl)
  def osnewl(self,cpu,mem):
    cpu.a = 0x0d
    self.oswrch(cpu,mem)

  @osFnc(oscli)
  def oscli(self,cpu,mem):
    addr = cpu.y*0x100+cpu.x
    s = mem.getString(addr)
    l = s.upper().split()
    if len(l) > 0:
      for module in [self.lvrom,self.mem,self.kvm,self]: # put 'self' last to pick up unimplemented functions
        if module.cli(l): break
      else:
        self.unimplementedCLI(l)
    cpu.a = 0

  def cli(self,l):
    if l[0] in self.cliDispatch:
      self.cliDispatch[ l[0] ](l)
      return True
    else: return False
  # ===============  OSFIND ========================
  @osFnc(osfind,0x00)
  def osfind1(self, cpu, mem):
    if (cpu.y == 0x00): 
      self.next_handle = 1
      self.files = {}
    else: 
      if cpu.y in self.files: del self.files[cpu.y]

  @osFnc(osfind,0x40)
  def osfind2(self, cpu, mem):
    cpu.a = self.next_handle
    name = mem.getString(cpu.y*0x100+cpu.x)
    #print('Opening file ',name)
    self.files[self.next_handle] = BeebCfg.adlDirectory.files[name.upper()]
    self.next_handle += 1
    if self.next_handle > 0xff:
      print('Too many files opened...')
      sys.exit()

  @osFnc(osfind,0x80)
  def osfind4(self, cpu, mem): # ???
    cpu.a = self.next_handle
    name = mem.getString(cpu.y*0x100+cpu.x)
    print('Opening file %s for output' % name)
    self.files[self.next_handle] = open(name.upper(),'wb')
    self.next_handle += 1
    if self.next_handle > 0xff:
      print('Too many files opened...')
      sys.exit()

  @osFnc(osfind,0xc0)
  def osfind3(self, cpu, mem):
    cpu.a = self.next_handle
    name = mem.getString(cpu.y*0x100+cpu.x)
    #print('Opening file ',name)
    self.files[self.next_handle] = BeebCfg.adlDirectory.files[name.upper()]
    self.next_handle += 1
    if self.next_handle > 0xff:
      print('Too many files opened...')
      sys.exit()

  # ================  OSARGS ==========================
  @osFnc(osargs,0x00)
  def filingsystem(self,cpu, mem):
    if cpu.y == 0:
      #cpu.a = 0x08  # report ADFS filing system
      cpu.a = 0x0a  # report VFS filing system
    else:
      print('unimplemented OSARGS filing Y: %02x' % cpu.y)

  @osFnc(osargs,0x01)
  def seqptr(self,cpu, mem):
    print('unimplemented OSARGS seqptr Y: %02x' % cpu.y)

  @osFnc(osargs,0x02)
  def filelen(self,cpu, mem):
    f = self.files[cpu.y]
    size = f.length
    block = mem.mv[cpu.x:cpu.x+4]
    #print('length of %s is %x' % (f.name,size))
    struct.pack_into('< L',block,0,size)

  @osFnc(osargs,0xff)
  def flush(self,cpu, mem):
    print('unimplemented OSARGS-flush Y: %02x' % cpu.y)

  # ====================  OSBYTE ===========================
  @osFnc(osbyte,0x02)
  def selinput(self,cpu,mem):
    #print('select input 0x%02x' % cpu.x)
    cpu.x = 0x00

  @osFnc(osbyte,0x03)
  def seloutput(self,cpu,mem):
    old = self.outputSelection
    self.outputSelection = cpu.x
    #print('Select output 0x%02x' % cpu.x)
    cpu.x = old

  @osFnc(osbyte,0x04)
  def enableCursorEditing(self,cpu,mem):
    if cpu.x == 0: pass  #print('Enable cursor editing')
    elif cpu.x == 1: pass #print('Assign ASCII codes to soft keys')
    elif cpu.x == 2: pass #print('Assign Soft Key codes to soft keys')
    else: pass
    
  @osFnc(osbyte,0x05)
  def setPrDriver(self, cpu, mem):
    #print('Set print driver 0x%02x' % cpu.x)
    self.PrDriver = cpu.x

  @osFnc(osbyte,0x0b)
  def keybRptDly(self,cpu,mem):
    pass

  @osFnc(osbyte,0x15)
  def flushKeyb(self,cpu,mem):
    pass
    
  @osFnc(osbyte,0x19)
  def restoreFontDefns(self, cpu, mem): pass

  @osFnc(osbyte,0x44)
  def sideways(self,cpu,mem):
    cpu.x = 0x0f

  @osFnc(osbyte,0x6c)
  def pageMemory(self, cpu, mem):
    if cpu.x == 0:
      #print('Page Main memory into main map')
      self.displayed = 'Main'
      self.kvm.display(0)
    else: 
      #print('Page Shadow memory into main map')
      self.displayed = 'Shadow'
      self.kvm.display(1)

  @osFnc(osbyte,0x70)
  def selectShadowVDU(self,cpu,mem):
    cpu.x = 1
      
  @osFnc(osbyte,0x71)
  def selectShadowDisplay(self,cpu,mem):
    cpu.x = 1
      
  @osFnc(osbyte,0x72)
  def selectShadowWrite(self,cpu,mem):
    cpu.x = 1
      
  @osFnc(osbyte,0x7e)
  def escape(self,cpu,mem):
    sys.exit()

  @osFnc(osbyte,0x80)
  def mouse(self, cpu, mem):
    if cpu.x == 0x07:
      x,y = self.kvm.mousePosn()
      if x > self.pointerMaxX: n = 1
      else: n = 0
      if y > self.pointerMaxY: n += 2
      self.kvm.setPointer(n)
      #print('Mouse: x=%4d, y=%4d' % (x,y),end='\r')
      cpu.x = x & 0x00ff; cpu.y = (x & 0xff00) >> 8
    elif cpu.x == 0x08:
      x,y = self.kvm.mousePosn()
      if x > self.pointerMaxX: n = 1
      else: n = 0
      if y > self.pointerMaxY: n += 2
      self.kvm.setPointer(n)
      #print('Mouse: x=%4d, y=%4d' % (x,y),end='\r')
      cpu.x = y & 0x00ff; cpu.y = (y & 0xff00) >> 8
    elif cpu.x == 0x09:
      print('mouse button req')
      cpu.y = self.kvm.mouseButton()
    elif cpu.x == 0xfc: # bytes free in printer buffer
      cpu.x = 0xff
    else:
      print("Mouse fnc %02x" % cpu.x)
      cpu.x = 0   # change this in due course


  @osFnc(osbyte,0x81)
  def key(self, cpu, mem):
    key = self.kvm.inkey()
    if cpu.y == 0xff:
      #print('[scan for 0x%02x]' % cpu.x)
      if cpu.x == key: cpu.x = 0xff
      else: pass
    else:
      t = (cpu.y * 0x100 + cpu.x) / 100.0
      if t > 0: time.sleep(t)
      if key == 0x00:
        cpu.x = 0
        cpu.y = 0xff
        cpu.p = cpu.p | (cpu.CARRY) # set carry=1
      else:
        cpu.x = key
        cpu.p = cpu.p & (~cpu.CARRY) # set carry=0
  
  @osFnc(osbyte,0x82)
  def HOA(self,cpu,mem): # read High Order Address
    cpu.x,cpu.y = 0x00, 0x00  # zero for Tube
    
  @osFnc(osbyte,0x90)
  def setInterlace(self, cpu, mem):
    pass
    
  @osFnc(osbyte,0xa0)
  def vduvar(self,cpu,mem): # !!!
    var = cpu.x
    if var == 0x55: 
      cpu.x = 0
      cpu.y = 2 # ??
    else:
      print('Read VDU variable 0x%02x ' % (var,))
      pass

  @osFnc(osbyte,0xc8)
  def setBrkEsc(self, cpu, mem):
    cpu.x = 2

  @osFnc(osbyte,0xe1)
  def setSoftKey(self, cpu, mem):
    if cpu.y == 0:
      #print('Set SoftKey Values 0x%02x + code' % cpu.x)
      pass
          
  @osFnc(osbyte,0xe2)
  def setSoftKeyS(self, cpu, mem):
    if cpu.y == 0:
      #print('Set SoftKey+Shift Values 0x%02x + code' % cpu.x)
      pass
          
  @osFnc(osbyte,0xe3)
  def setSoftKeyC(self, cpu, mem):
    if cpu.y == 0:
      #print('Set SoftKey+Ctrl Values 0x%02x + code' % cpu.x)
      pass
          
  @osFnc(osbyte,0xe4)
  def setSoftKeySC(self, cpu, mem):
    if cpu.y == 0:
      #print('Set SoftKey+Shift+Ctrl Values 0x%02x + code' % cpu.x)
      pass
          
  @osFnc(osbyte,0xe5)
  def esckey(self,cpu,mem):
    cpu.x, cpu.y = 0x00, 0x00

  @osFnc(osbyte,0xf5)
  def getPrDriver(self,cpu,mem):
    #print('Get printer driver')
    cpu.x = self.PrDriver
  
  @osFnc(osbyte,0xfb)
  def MemoryDisplayed(self, cpu, mem):
    if self.displayed == 'Main': cpu.x = 1
    else: cpu.x = 2

  # =================  OSWORD ==============================
    
  @osFnc(osword,0x07)
  def GenerateSound(self,cpu,mem):
    self.kvm.beep(1)
    
  @osFnc(osword,0x09)
  def readPixelColour(self, cpu, mem):
    addr = cpu.y*0x100 + cpu.x
    x = mem[addr]+0x100*mem[addr+1]
    y = mem[addr+2]+0x100*mem[addr+3]
    print('request colour at (%i, %i)' % (x,y))
    mem[addr+4] = 3 # return what should be foreground??
    
  @osFnc(osword,0x0a)
  def readChDefn(self,cpu,mem):
    addr = cpu.y*0x100 + cpu.x
    c = mem[addr]
    for i in range(8): mem[addr+i+1] = self.font[c][i]

  @osFnc(osword,0x0b)
  def readPalette(self,cpu,mem):
    addr = cpu.y*0x100 + cpu.x
    lcol = mem[addr]
    pcol = self.LogicalColours[lcol]
    i = self.PhysicalColours.index(pcol)
    mem[addr+1] = i
      
  @osFnc(osword,0x0d)
  def cursorpos(self,cpu,mem):
    addr = cpu.y*0x100+cpu.x
    #oldx, oldy, newx,newy = self.kvm.getCoords()
    mem[addr  ] = self.oldx & 0xff; mem[addr+1] = self.oldx >> 8;
    mem[addr+2] = self.oldy & 0xff; mem[addr+3] = self.oldy >> 8;
    mem[addr+4] = self.x & 0xff; mem[addr+5] = self.x >> 8;
    mem[addr+6] = self.y & 0xff; mem[addr+7] = self.y >> 8;

  @osFnc(osword,0x42)
  def sideXfer(self,cpu,mem):
    block,(func,mem_addr,length,bank,side_addr) = self.getParams(cpu,mem,10,self.fm2)
    if func == 0x00:
      print('read abs side bank %02x mem %04x side %04x len %04x' % (bank,mem_addr,side_addr,length))
      pass
    elif func == 0x40:
      mem.xferFromSide(bank,mem_addr,side_addr,length)
    elif func == 0x80:
      print('write abs side bank %02x mem %04x side %04x len %04x' % (bank,mem_addr,side_addr,length))
    elif func == 0xc0:
      mem.xferToSide(bank,mem_addr,side_addr,length)
    else: print('Unknown sideways transfer')

  @osFnc(osword,0x62)
  def LVCmd(self, cpu, mem):
    addr = cpu.y*0x100 + cpu.x
    cntrlBlock = mem.get(addr,15)
    buf = cntrlBlock[1] + 0x100*cntrlBlock[2]
    cmdBlock = cntrlBlock[5:11]
    func = cmdBlock[0]
    discAddr = cmdBlock[1]*0x10000+cmdBlock[2]*0x100+cmdBlock[3]
    sectorCount = cmdBlock[4]
    length = 256*sectorCount
    if func == 0x08: # Read sectors
      BeebCfg.adlFile.seek(discAddr*256) 
      mem.load(BeebCfg.adlFile.read(length),buf,buf+length)
    elif func == 0xc8: # Read FC Result
      mem.load(BeebCfg.FCresponse,buf,buf+256)
    else: print('Unimplemented SCSI function!')
    

  # =====================  OSFILE ========================
  
  @osFnc(osfile,0x05)
  def rdfilecat(self,cpu,mem):
    block,(na,ld,ex,st,en) = self.getParams(cpu,mem,18,self.fm1)
    name = mem.getString(na)
    #print('Look-up file %s' % name)
    try:
      e = BeebCfg.adlDirectory.files[name.upper()]
      size, cpu.a = e.length, 1
    except:
      size, cpu.a = 0,0
    self.fm1.pack_into(block,0,na,0,0,size,0x00000009)
    
  @osFnc(osfile,0x06)
  def deleteFile(self,cpu,mem): # ???
    block,(na,ld,ex,st,en) = self.getParams(cpu,mem,18,self.fm1)
    name = mem.getString(na)
    print('deleteFile %s' % name)
    cpu.a = 0
    
  @osFnc(osfile,0xff)
  def loadfile(self,cpu,mem):
    block,(na,ld,ex,st,en) = self.getParams(cpu,mem,18,self.fm1)
    name = mem.getString(na)
    #print('Loading file %s' % name)
    e = BeebCfg.adlDirectory.files[name.upper()]
    BeebCfg.adlFile.seek(e.ssec*256)
    s = BeebCfg.adlFile.read(e.length)
    use_load = ex & 0xff
    if use_load == 0:
      if ld >= 0x10000:
        #print('skip loading file to I/O processor')
        cpu.a = 1
      else:
        load_address = ld
        #print('  load address = %08x ex %08x start %08x end %08x' % (ld, ex, st, en) )
        size = len(s)
        self.fm1.pack_into(block,0,na,0,0,size,0x00000009)
        mem.load(s,load_address,load_address+size)
        cpu.a = 1
    else:
      print('no load address')
      cpu.a = 0

  # =========================  OSGBPB ===========================
  
  @osFnc(osgbpb,0x01)
  def wrSeqNew(self,cpu,mem): # ???
    print('WriteSeqNew - write bytes to file')
    block,(fi, inbuf, length, posn) = self.getParams(cpu,mem,13,self.fm3)
    f = self.files[fi]
    f.write(mem.get(inbuf,length))
    cpu.p = cpu.p & (~cpu.CARRY)

  @osFnc(osgbpb,0x02)
  def wrSeq(self,cpu,mem): # ???
    print('WriteSeq - Append bytes to file')
    block,(fi, inbuf, length, posn) = self.getParams(cpu,mem,13,self.fm3)
    f = self.files[fi]
    f.write(mem.get(inbuf,length))
    cpu.p = cpu.p & (~cpu.CARRY)

  @osFnc(osgbpb,0x03)
  def rdSeqNew(self,cpu,mem):
    block,(fi, inbuf, length, posn) = self.getParams(cpu,mem,13,self.fm3)
    e = self.files[fi]
    BeebCfg.adlFile.seek(posn+e.ssec*256)
    s = BeebCfg.adlFile.read(length)
    if inbuf+length > 0xffff:
      print('File %s' % e.name)
      print('too long !!',inbuf,length)
    mem.load(s,inbuf,inbuf+length) #
    cpu.p = cpu.p & (~cpu.CARRY)

  @osFnc(osgbpb,0x04)
  def rdSeq(self, cpu, mem):
    block,(fi, inbuf, length, posn) = self.getParams(cpu,mem,13,self.fm3)
    e = self.files[fi]
    BeebCfg.adlFile.seek(posn+e.ssec*256)
    s = BeebCfg.adlFile.read(length)
    mem.load(s,inbuf,inbuf+length)
    cpu.p = cpu.p & (~cpu.CARRY)

  # ====================  HELPER METHODS ==========================
  def unimplementedCLI(self,l):
    print('Unimplemented CLI %s' % l[0])
    
  def noopCLI(self,l):
    pass
    
  def fcode(self,l):
    if False: pass
    else: 
      print('Uniplemented FCode %s' % l[1])
      return False
    return True
    
  def writeChrFirst(self, c):
    f,n = self.chrDispatch.get(c,(self.writeNormalChr,1))
    #print(f,n)
    if n == 1: f(c)
    else:
      self.pktLen = n-2
      self.ctlPkt = [c]
      self.writeChr = f

  def writeNormalChr(self, ccc):  # only called if c is a 'normal' chararcter
    c = chr(ccc)
    if (self.outputSelection & 0x2) == 0x00:
      self.kvm.drawChr(c, (self.x, self.y), self.foreground)
      if c in ('$','&','M','W','m','q','w','~'): self.x += 32
      elif c in (' ','"','[',']','f','t','{','}'): self.x += 24
      elif c in ("'",'(',')','i','j','l'): self.x += 20
      elif c in (',',':',';'): self.x += 16
      elif c in ('!','.','|'): self.x += 12
      else: self.x += 28
    if (self.outputSelection & 0x08) == 0x08: self.printToFile(c)
    
  def printToFile(self,c):
    if BeebCfg.printFile == None: 
      s = str(datetime.datetime.now())[:16]
      BeebCfg.printFile = open('./print-%s' % s,'w')
    BeebCfg.printFile.write(c)
      
  def u(self, c): print('VDU code <0x%02x>' % c)
   
  def wtatt(self,c): pass # write text at text cursor
  def wtatg(self,c): pass # write text at graphics cursor
  def mvtxtcur(self,c): pass # move text cursor to top of screen
    
  def beep(self,c): self.kvm.beep(0)

  def cursorNL(self,c): 
    if (self.outputSelection & 0x2) == 0x00: self.y = min(self.y-32,0)
    if (self.outputSelection & 0x08) == 0x08: self.printToFile('\n')
    
  def cursorCR(self,c): 
    if (self.outputSelection & 0x2) == 0x00: self.x = 0
    if (self.outputSelection & 0x08) == 0x08:self.printToFile('\r')
      
  def clrtextarea(self,c): pass
    
  def rstdefwins(self,c): pass
  
  def uu(self, c):
    self.ctlPkt.append(c)
    if self.pktLen > 0:
      self.pktLen -= 1; 
      self.writeChr = self.uu
    else:
      print('Unimplemented VDU code %s' % self.ctlPkt[0])
      print(self.ctlPkt)
      self.writeChr = self.writeChrFirst

  def VDU17(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0:
      self.pktLen -= 1
      self.writeChr = self.VDU17
    else:
      self.writeChr = self.writeChrFirst
      col = self.ctlPkt[1]
      #print('Set foreground/background colour to 0x%02x' % col)
      if (col < 0x80): self.foreground = self.LogicalColours[col]
      else: self.background = self.LogicalColours[col-128]

      
  def VDU18(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0:
      self.pktLen -= 1 
      self.writeChr = self.VDU18
    else:
      self.writeChr = self.writeChrFirst
      cmd, data  = self.ctlPkt[1], self.ctlPkt[2]
      op = cmd & 0x0f
      if cmd == 0:
        #print('Colour 0x%02x 0x%02x' % (cmd,data))
        if data < 128: self.foreground = self.LogicalColours[data]
        else:          self.background = self.LogicalColours[data-128]
      else:
        ecf = ((cmd & 0xf0) >> 4) -1
        if data < 128: self.foreground = self.ECFColours[ecf]
        else:          self.background = self.ECFColours[ecf]        
        #print('Extended colour fill', ecf)
   
  def VDU19(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0:
      self.pktLen -= 1
      self.writeChr = self.VDU19
    else:
      self.writeChr = self.writeChrFirst
      col1, col2 = self.ctlPkt[1], self.ctlPkt[2]
      #print('Define colours logical 0x%02x is physical 0x%02x' % (col1,col2))
      if (col1 < 16) and (col2<16): self.LogicalColours[col1] = self.PhysicalColours[col2]

  def VDU22(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0: 
      self.pktLen -= 1
      self.writeChr = self.VDU22
    else:
      self.writeChr = self.writeChrFirst
      self.LogicalColours = []
      for i in [0,1,3,7,0,1,3,7,0,1,3,7,0,1,3,7,]: self.LogicalColours.append(self.PhysicalColours[i])

  def VDU23(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0: 
      self.pktLen -= 1
      self.writeChr = self.VDU23
    else:
      #print('ctlPkt length = %i should be 2' % len(self.ctlPkt))
      #print(self.ctlPkt)
      c = self.ctlPkt[1]
      #print('VDU23 subcommand %i' % c)
      if (c >= 2) and (c <= 5):
        #print('ECF', self.ctlPkt)
        a = 1
        for n in self.ctlPkt: a = a*n
        r = a&0xff; g = (a & 0x3fc) >> 2; b = (a & 0xff0) >> 4
        self.ECFColours[c-2] = (r,g,b) # fudge patterns
      elif c >= 32:
        #print('Redefine character %i' % c)
        self.font[c] = self.ctlPkt[2:]
        self.fontChanged = True
      self.writeChr = self.writeChrFirst

  def VDU24(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0:
      self.pktLen -= 1
      self.writeChr = self.VDU24
    else:
      #print('ctlPkt length = %i should be 6' % len(self.ctlPkt))
      lx, rx = self.ctlPkt[1]+0x100*self.ctlPkt[2], self.ctlPkt[5]+0x100*self.ctlPkt[6]
      by, ty = self.ctlPkt[3]+0x100*self.ctlPkt[4], self.ctlPkt[7]+0x100*self.ctlPkt[8]
      #print('Set graphics area: lx=%i by=%i rx=%i ty=%i '% (lx,by,rx,ty))
      #self.plot(self.ctlPkt)
      self.writeChr = self.writeChrFirst

  def VDU25(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0:
      self.pktLen -= 1
      self.writeChr = self.VDU25
    else:
      self.writeChr = self.writeChrFirst
      #print('ctlPkt length = %i should be 6' % len(self.ctlPkt))
      #print(self.ctlPkt)
      self.plot(self.ctlPkt)
  # ---------------------------------------------------------------------------------------
  def plot(self,p):
    x, y =int.from_bytes(p[2:4],'little',signed=True), int.from_bytes(p[4:6],'little',signed=True)
    #
    if (p[1] & 0x04) == 0x00: self.newx = abs(self.x + x); self.newy = abs(self.y + y)
    else: self.newx = x; self.newy = y
    #
    if (p[1] & 0x03) == 0: colour = None
    elif (p[1] & 0x03) == 1:colour = self.foreground
    elif (p[1] & 0x03) == 2: colour = self.foreground # invert pixels
    else: colour = self.background
    # 
    cmd = (p[1] & 0xf8) >> 3
    if cmd == 0: 
      if colour == None: # move without drawing
        pass
      else:  # draw line
        self.kvm.drawLine((self.x, self.y), (self.newx, self.newy),colour)
    elif cmd == 3: 
      if colour == None: # move without drawing
        pass
      else:  # draw dotted line
        self.kvm.drawLine((self.x, self.y), (self.newx, self.newy),colour,fill='dotted')
    elif cmd == 10:  # draw triangle
      self.kvm.drawPoly([(self.oldx, self.oldy), (self.x, self.y), (self.newx, self.newy)],colour)
    elif cmd == 12: # draw rectangle
      self.kvm.drawRect((self.x,self.y),(self.newx,self.newy),colour)
    elif cmd == 14:  # draw parallelogram
      fourthx = self.newx + self.oldx - self.x
      fourthy = self.newy + self.oldy - self.y
      self.kvm.drawPoly([(self.oldx, self.oldy), (self.x, self.y),\
                                           (self.newx, self.newy),(fourthx, fourthy)],colour)
    elif cmd == 22:  # draw sector
      self.kvm.drawSector(self.oldx,self.oldy,self.x,self.y,self.newx,self.newy,colour)
    else:
      print('Plot<%i> x=%4d y=%4d' % (cmd*8,self.x,self.y))
    self.oldx, self.oldy = self.x, self.y
    self.x, self.y = self.newx, self.newy
# -------------------------------------------------------------------------
  def VDU28(self,c):
    self.ctlPkt.append(c)
    if self.pktLen > 0: 
      self.pktLen -= 1
      self.writeChr = self.VDU28
    else:
      self.writeChr = self.writeChrFirst
      #print('Set text area')

# --------------------------------------------------------------------------
  def setMouseChange(self, l):
    self.pointerMaxX = int(l[1][:-1])
    self.pointerMaxY = int(l[2])
    #print('PointerMax X %i Y %i' % (self.pointerMaxX,self.pointerMaxY))
      
  def setfont2(self,l):
    '''
    Currently does nothing.  FONT2 file is pre-created as a .BDF, and loaded by pygame.
    '''
    # read FONT2 file
    e = BeebCfg.adlDirectory.files['FONT2']
    BeebCfg.adlFile.seek(e.ssec*256)
    s = BeebCfg.adlFile.read(e.length)
    # for each char in it, reconstruct 8*8 bit pattern
    nchars = 0xe0
    first = 0x20
    offset = 0x44
    for i in range(nchars):
      ss = bytearray('        '.encode('utf-8') )
      for j in range(8):
        ss[j] = s[offset+j*nchars + i]
      self.font[first+i] = ss
    #print('FONT2 loaded!')
    self.fontChange = True
  
  

