#!/usr/bin/env python3
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
import time
import struct
import cmd
#
import BeebCfg
import Cinterp
import BeebMem
import BeebKVM
import BeebMOS
#
if (BeebCfg.mode==3) and BeebCfg.modeLock:
  print('Not using py65')
else:
  try:
    from py65.devices.mpu65c02 import MPU
    from py65 import disassembler 
    print('Using py65.')
  except:
    print('Py65 unavailable.')
    BeebCfg.mode = 3
    BeebCfg.modeLock = True
#

# =====================================================================

class LVRom:
  def __init__(self):
    self.playing = False
    self.cliDispatch = {
      'AUDIO':self.noopCLI,'PLAY':self.play,\
      'SEARCH':self.search,'FRAME':self.search,'STILL':self.search,\
      'F':self.forward,'B':self.back,'BYE':self.bye,\
      'EJECT':self.eject,'RESET':self.reset,'MOUNT':self.mount,\
      'FCODE':self.fcode
      }

  def cli(self,l):
    self.dispatched = True   # May be set to false by fcode
    if l[0] in self.cliDispatch:
      self.cliDispatch[ l[0] ](l)
      #print('lvrom dispatched %s' % l[0])
      return self.dispatched
    else: return False
    
  def fcode(self,l):
    if l[1] == '?U': self.setUID()
    elif l[1] == 'X': self.stop()
    elif l[1] ==',1': self.loadDisc()
    elif l[1] in ('I0','I1','J0','J1','$0','E0','E1'): pass
    else: self.dispatched = False
    
  def noopCLI(self,l): pass
    
  def disk(self,name):
    self.UID = bytes(BeebCfg.Disks[name]['UID'],'utf-8')
    self.FNo = 1   
 
  def play(self,l):
    BeebCfg.FCresponse = b'S\r'
    self.FNo = int(l[1][:-1])
    self.StopFrame = int(l[2])
    self.playing = True

  def stop(self):
    self.playing = False
    BeebCfg.FCresponse = b'A2\r'
    
  def search(self,l):
    self.FNo = int(l[1])
    BeebCfg.FCresponse = b'A2\r'
    self.playing = False
    
  def eject(self,l):
    self.FNo = 1
    BeebCfg.FCresponse = b'O\r'
    #print('Eject')
    self.playing = False
    
  def loadDisc(self):  
    self.FNo = 1
    print('*** PAUSE and change disk ***')
    time.sleep(2)
    self.playing = False
    
  def forward(self,l):
    if len(l) < 2: self.FNo += 1
    else: self.FNo += int(l[1])
    BeebCfg.FCresponse = b'A2\r'
    self.playing = False

  def back(self,l):
    if len(l) < 2: self.FNo -= 1
    else: self.FNo -= int(l[1])
    BeebCfg.FCresponse = b'A2\r'
    self.playing = False

  def setUID(self):
    BeebCfg.FCresponse = self.UID
    
  def readMSN(self,addr):
    pass

  def readInfo(self,addr): pass
  
  def reset(self,l): pass #print('LV reset'); time.sleep(1)
  
  def mount(self,l): pass #print('LV mount'); time.sleep(1)
  
  def bye(self,l): pass

  def update(self):
    if self.playing: 
      if self.FNo >= self.StopFrame:
        self.playing = False
        BeebCfg.FCresponse = b'A2\r'
      else: self.FNo += 1
    return self.FNo

# ===================================================================
class FakeMPU():
  def __init__(self):
    self.pc, self.sp = 0,0
    self.a, self.x, self.y, self.p = 0,0,0,0
    self.CARRY,self.NEGATIVE,self.ZERO,self.OVERFLOW = 0,0,0,0

# ====================================================================
class BeebApp(cmd.Cmd):
  
  def preloop(self):
    print('Preparing Interpreter')
    self.initialized = False
    self.maxticks = BeebCfg.maxticks
    self.avTime = 0.0
    self.executionMode = BeebCfg.mode
    self.mem = BeebMem.TubeMem()
    self.cint = Cinterp.cintState(PC=0x3f38, G=0x0400,\
      memory=BeebMem.cintMem(self.mem))
    self.ld = LVRom()
    self.kvm = BeebKVM.Beebkvm()
    self.changeDisk(BeebCfg.defaultDisk)
    if (BeebCfg.mode == 3) and BeebCfg.modeLock:
      self.cpu = FakeMPU()
    else:
      self.cpu = MPU(BeebMem.py65Mem(self.mem), 0x0e00)
      self.cpu.pc = 0x0416; self.cpu.sp = 0x00ff
      self.cpu.a = 0x0f; self.cpu.x = 0xff; self.cpu.y = 0x00
      self.disassembler = disassembler.Disassembler(self.cpu)
    self.oldMode = BeebCfg.mode
    self.executionMode = BeebCfg.mode
    self.showStatus()
    
  def postloop(self):
    print('Bye!')
    if BeebCfg.printFile != None: BeebCfg.printFile.close()
    if BeebCfg.traceFile != None: BeebCfg.traceFile.close()
    if BeebCfg.adlFile   != None: BeebCfg.adlFile.close()
    
  def postcmd(self, stop, line):
    self.showStatus()
    return cmd.Cmd.postcmd(self, stop, line)
    
  def initialize(self):
    #self.ld.disk(self.disk)
    #self.kvm.disk(self.disk)
    self.kvm.initialize()
    self.os = BeebMOS.MOS(self.mem,self.ld,self.kvm)
    self.cint.os = self.os
    self.setExecutionMode(self.executionMode)
    self.mem.initialize()
    self.mem.setos(self.os,self.cpu)
    
  def setExecutionMode(self,mode):
    if   mode == 0:
      self.doSlice = self.xeqtMode0; self.cint.setRW(False)
      if (self.oldMode == 2) or (self.oldMode == 3):
        for i in range(8): self.mem.cregs[i] = self.cint.getRegs()[i]
    elif mode == 1:
      self.doSlice = self.xeqtMode1; self.cint.setRW(False)
      if (self.oldMode == 2) or (self.oldMode == 3):
        for i in range(8): self.mem.cregs[i] = self.cint.getRegs()[i]
    elif mode == 2:  
      self.doSlice = self.xeqtMode2; self.cint.setRW(True)
      if (self.oldMode == 0) or (self.oldMode == 1):
        self.cint.putRegs(self.mem.cregs[0:8])
    else: 
      self.doSlice = self.xeqtMode3; self.cint.setRW(True)
      if (self.oldMode == 0) or (self.oldMode == 1):
        self.cint.putRegs(self.mem.cregs[0:8])
    self.oldMode = mode
    
  def xeqtMode0(self,count): # 6502 emulation only
    while count > 0:
      count -= 1
      self.interp65()
      
  def xeqtMode1(self,count): # 6502 emulation with cintcode readonly comparison
    while count > 0:
      count -= 1
      temp = self.cint.getRegs() # snap regs before execution
      self.interp65()
      handled = self.cint.step()
      if not handled:
        self.cint.putRegs(self.mem.cregs[0:8])
        print('### %s' % self.cint.instr)
      self.compare(temp)  
      
  def xeqtMode2(self,count): # cintcode emulation with 6502 fallback for unhandled LF$ instructions
    while count > 0:
      count -= 1
      handled = self.cint.step()
      if not handled:
        for i in range(8): self.mem.cregs[i] = self.cint.getRegs()[i]
        self.interp65()
        self.cint.putRegs(self.mem.cregs[0:8])
        print('### %s A = 0x%04x' % (self.cint.instr,self.mem.cregs[4]))
        
  def xeqtMode3(self,count): # cintcode emulation only
    while count > 0:
      count -= 1
      handled = self.cint.step()
      if not handled: sys.exit(-1)

  def interp65(self):
    loop = True
    trace = BeebCfg.mpuTracing
    while loop:
      if trace:
        ict, dis_str = self.disassembler.instruction_at(self.cpu.pc)
        pc,a,x,y = self.cpu.pc,self.cpu.a, self.cpu.x, self.cpu.y
      #
      self.cpu = self.cpu.step()
      #
      if trace:
        BeebCfg.traceFile.write('0x%04x %12s 0x%02x->0x%02x 0x%02x->0x%02x 0x%02x->0x%02x\n' \
            % (pc,dis_str,a,self.cpu.a,x,self.cpu.x,y,self.cpu.y))
      #
      loop = (self.cpu.pc != 0x0416)
        
  def compare(self,temp):
    t2 = self.cint.getRegs()
    pc0, pc1, pc2 = temp[3], self.mem.cregs[3], t2[3]
    g0, g1, g2   = temp[7], self.mem.cregs[7],  t2[7]
    a0, a1, a2   = temp[4], self.mem.cregs[4],  t2[4]
    b0, b1, b2   = temp[5], self.mem.cregs[5],  t2[5]
    c0, c1, c2   = temp[6], self.mem.cregs[6],  t2[6]
    p0, p1, p2   = temp[2], self.mem.cregs[2],  t2[2]
    if (pc1!=pc2)or(g1!=g2)or(a1!=a2)or(b1!=b2)or(c1!=c2)or(p1!=p2):
      print('= pre  %04x   %04x   %04x   %04x   %04x   %04x ' % (pc0,p0,a0,b0,c0,g0))
      print('### PC=%04x P=%04x A=%04x B=%04x C=%04x G=%04x %-6s |' % (pc1,p1,a1,b1,c1,g1,self.cint.instr))
      print('= post %04x   %04x   %04x   %04x   %04x   %04x  0x%02x' % (pc2,p2,a2,b2,c2,g2, self.cint.ir))
      print()
      # and repair cintcode registers
      self.cint.putRegs([0,0,p1,pc1,a1,b1,c1,g1])
      BeebCfg.misMatch -= 1
      if BeebCfg.misMatch <= 0:
        print('Maximum mis-matches exceeded!')
        sys.exit()

  def showStatus(self):
    print('''
===============  BBC Domesday Emulator  ===============
|
|
|  Disk:             %s
|  Execution Mode:   %i
|  Call Tracing:     %s
|  Cintcode Tracing: %s
|  6502 Tracing:     %s
|  Av. Instrs:       %i kips
|
|
-------------------------------------------------------
|  Commnds: g - start/resume emulation; q - Quit; 
|           a, n, s - select National, Community North,
|                              or Community South disks
|           c - toggle call tracing
|           i - toggle cint tracing
|           6 - toggle 6502 tracing
|
|   ** Press 'PAUSE' during emulation to return here **
-------------------------------------------------------
    ''' % (self.disk,self.executionMode,BeebCfg.callTracing,BeebCfg.cintTracing,BeebCfg.mpuTracing,\
           self.avTime))
    

  def changeDisk(self,name):
    self.disk = name
    if BeebCfg.adlFile != None: BeebCfg.adlFile.close()
    if BeebCfg.mp4File != None: BeebCfg.mp4File.close()
    self.prompt = 'Disk: %s > ' % self.disk
    BeebCfg.adlFile = open(BeebCfg.Disks[self.disk]['adlFile'],'rb')
    if BeebCfg.useCV2: 
        BeebCfg.mp4File = open(BeebCfg.Disks[self.disk]['mp4File'],'rb')
    BeebCfg.adlDirectory = BeebMOS.VFSDir()
    self.ld.disk(self.disk)
    self.kvm.disk(self.disk)
    BeebCfg.FCresponse = b'S\r'
       
  def do_a(self, line):
    self.changeDisk('natA')
    
  def do_s(self, line):
    self.changeDisk('comS')

  def do_n(self, line): 
    self.changeDisk('comN')

  def do_c(self, line): 
    if BeebCfg.traceFile == None: BeebCfg.traceFile = open('trace.out','w')
    BeebCfg.callTracing = not BeebCfg.callTracing
      
  def do_i(self, line):
    if BeebCfg.traceFile == None: BeebCfg.traceFile = open('trace.out','w')
    BeebCfg.cintTracing = not BeebCfg.cintTracing
      
  def do_6(self, line):
    if BeebCfg.traceFile == None: BeebCfg.traceFile = open('trace.out','w')
    BeebCfg.mpuTracing = not BeebCfg.mpuTracing
      
  def do_mode(self, line):
    if BeebCfg.modeLock:
      print('Mode is locked!')
    else:
      self.executionMode = int(line)
      if self.initialized: self.setExecutionMode(self.executionMode)
  
  def do_g(self,line):
    done = False
    if self.initialized:
      print('Resuming interpreter')
    else:
      self.initialize()
      self.initialized = True
      print('Starting Interpreter')
    cycleCount = 0
    cycles = 100
    st = time.time()
    while not done:
      # run emulation steps
      #self.c.doSlice(cycles)
      self.doSlice(cycles)
      cycleCount += cycles
      # update display at 25 FPS
      et = time.time()
      if (et-st) > 0.04:
        self.avTime = cycleCount*0.025
        st = et
        cycleCount = 0
        done =  self.kvm.update(self.ld)
      if cycleCount > self.maxticks:
        time.sleep(0.04-et+st)
      
  def do_q(self,line): 
    if self.initialized: 
      self.kvm.quit()
    return True

        
# =====================================================================
#
#

if __name__ == "__main__":
  BeebApp().cmdloop()
  

