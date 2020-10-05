from functools import partial as N
from operator import *
from math import sin,cos
#
import BeebCfg
#
def _u(x):
  if x < 0: return (0x10000 + x) & 0xffff
  else: return x & 0xffff
def _s(x):
  if x > 0x7fff: return x - 0x10000
  else: return x
def _n(x):
  if x > 0x10000: return x - 0x10000
  else: return x
# ==========================================================    
# cintcode functions
# ==========================================================

# Direct load
def Ln(n,s):  s.B = s.A; s.A = n; s.PC += 1  #
def LM1(s):   s.B = s.A; s.A = -1; s.PC += 1 #  
def Lb(s):     s.B = s.A; s.A = s.b; s.PC += 2 #
def LM(s):    s.B = s.A; s.A = -s.b; s.PC += 2 # !!! supposed definition  
def LH(s):    s.B = s.A; s.A = s.h; s.PC += 3 #
def LMH(s):   s.B = s.A; s.A = -s.h; s.PC += 3 #  
def LW(s):    s[s.b1].Var = s.A; s.PC += 2  # s.B = s.A; s.A = s.w; s.PC += 5 # !!!
def MW(s):    s.MW = s.w; s.PC += 5 #
def LPn(n,s): s.B = s.A; s.A = s[s.P, n].M; s.PC += 1 #
def LP(s):    s.B = s.A; s.A = s[s.P,s.b].M; s.PC += 2 #
def LPH(s):   s.B = s.A; s.A = s[s.P,s.h].M; s.PC += 3 #
def LPW(s):   s.B = s.A; s.A = s[s.P,s.w].M; s.PC += 5 #
def LG(s):    s.B = s.A; s.A = s[s.G,s.b].M; s.PC += 2 #
def LG1(s):   s.B = s.A; s.A = s[s.G,s.b1].M; s.PC += 2 #
def LGH(s):   s.B = s.A; s.A = s[s.G,s.b2].M; s.PC += 2 #s.B = s.A; s.A = s[s.G,s.h].M; s.PC += 3 #
def LL(s):    s.B = s.A; s.A = s[s.b].Rel; s.PC += 2 #
def LL_(s):   s.B = s.A; s.A = s[s.b].RelInd; s.PC += 2 #
def LF(s):    Kn(12,s) #                                s.B = s.A; s.A = s[s.b].Rel; s.PC += 2 #
def LF_(s):   s.processLF() # s.B = s.A; s.A = s[s.b].RelInd; s.PC += 2 #
def LLP(s):   s.B = s.A; s.A = s[s.P,s.b].at; s.PC += 2 #q
def LLPH(s):  s.B = s.A; s.A = s[s.P,s.b2].at; s.PC += 2 #s.A = s[s.P,s.h].at; s.PC += 3 # !!!
def LLPW(s):  s[s.b].Var = s.A; s.PC += 2 #  s.A = s[s.P,s.w].at; s.PC += 5 # !!!
def LLG(s):   s.B = s.A; s.A = s[s.G,s.b].at; s.PC += 2 #
def LLG1(s):  s.B = s.A; s.A = s[s.G,s.b1].at; s.PC += 2 #
def LLGH(s):  s.B = s.A; s.A = s[s.G,s.b2].at; s.PC += 2 #s.B = s.A; s.A = s[s.G,s.h].at; s.PC += 3 #
def LLL(s):   s.B = s.A; s.A = s[s.b].atR>>1; s.PC += 2  #
def LLL_(s):  s.B = s.A; s.A = s[s.b].atRI>>1; s.PC += 2 # !!!

# Indirect load
def GBYT(s):      s.A = s[s.B, s.A].asByte; s.PC += 1 #
def RVn(n,s):     s.A = s[s.A, n].M; s.PC += 1 #
def RVPn(n,s):    s.A = s[s.P,n,s.A].M; s.PC += 1 #
def LiPn(i, n,s): s.B = s.A; s.A = s[s.P, n,i].M; s.PC += 1 #
def LnG(n,s):     s.B = s.A; s.A = s[s.G,s.b, n].M; s.PC += 2 #
def LnG1(n,s):    s.B = s.A; s.A = s[s.G,s.b1,n].M; s.PC += 2 #
def LnGH(n,s):    s.B = s.A; s.A = s[s.G,s.b2, n].M; s.PC += 2 # !!!

# Expresssions
def X1(op,s):  s.A = op(s.A); s.PC += 1 #  
def NEG(s):    s.A = -_s(s.A) ; s.PC += 1 #
def INV(s):    s.A = _u(s.A) ^ 0xffff; s.PC += 1 # python invert affects sign bit ??
def X2(op,s):  s.A = op( s.B,s.A) & 0xffff; s.PC += 1 #  
def LSH(s):    s.A = (s.B << s.A) & 0xffff; s.PC += 1
def RSH(s):    s.A = s.B >> s.A; s.PC += 1
def An(n,s):   s.A += n; s.PC += 1 #  
def Sn(n,s):   s.A -= n; s.PC += 1 #  
def Ab(s):      s.A += s.b; s.PC += 2 #  
def AH(s):     s.A = _s(s.A + s.h); s.PC += 3 #  
def AW(s):     s.A += s.w; s.PC += 5 #  
def Sb(s):      s.A -= s.b; s.PC += 2 #  
def SH(s):     s.A -= s.h; s.PC += 3 #  
def APn(n,s):  s.A = _s(s.A + s[s.P,n].M); s.PC += 1 #  
def AP(s):     s.A = (s.A + s[s.P,s.b].M) & 0xffff; s.PC += 2 #  
def APH(s):    s.A += s[s.P,s.h].M; s.PC += 3 #  
def APW(s):    s.A += s[s.P,s.w].M; s.PC += 5 #  
def AG(s):     s.A += s[s.G,s.b].M; s.PC += 2 #  
def AG1(s):    s.A += s[s.G,s.b1].M; s.PC += 2 #  
def AGH(s):    s.A += s[s.G,s.b2].M; s.PC += 2 #    s.A += s[s.G,s.h].M; s.PC += 3 #

# Simple assignment
def SPn(n,s):  s[s.P, n].M = s.A; s.PC += 1 #
def SP(s):     s[s.P,s.b].M = s.A; s.PC += 2 #
def SPH(s):    s[s.P,s.h].M = s.A; s.PC += 3 #
def SPW(s):    s[s.P,s.w].M = s.A; s.PC += 5 #
def SG(s):     s[s.G,s.b].M = s.A; s.PC += 2 #
def SG1(s):    s[s.G,s.b1].M = s.A; s.PC += 2 #
def SGH(s):    s[s.G,s.b2].M = s.A; s.PC += 2 # s[s.G,s.h].M = s.A; s.PC += 3 #
def SL(s):     s[s.b].Rel = s.A; s.PC += 2 #
def SL_(s):    s[s.b].RelInd = s.A; s.PC += 2 #

# Indirect assignment
def PBYT(s):     s[s.B, s.A].asByte = s.C; s.PC += 1 # 
def XPBYT(s):    s[s.A, s.B].asByte = s.C; s.PC += 1 # 
def STn(n,s):    s[s.A, n].M = s.B; s.PC += 1 #
def STiPn(i,n,s):  s[s.P, n,i].M = s.A; s.PC += 1 #
def STPn(n,s):   s[s.P,n,s.A].M = s.B; s.PC += 1 #
def S0G(s):      KnG(12,s)  # s[s.G,s.b,0].M = s.A; s.PC += 2 # !!!
def S0G1(s):     KnG1(12,s) # s[s.G,s.b1,0].M = s.A; s.PC += 2 # !!!
def S0GH(s):     KnGH(12,s) # s[s.G,s.h,0].M = s.A; s.PC += 3 # !!!

# Calls
def _k0(k,s):
  if s.callTrace: 
    s.callDepth += 1
    spacer = s.callDepth*'+'
    BeebCfg.traceFile.write('%s| hw 0x%04x\n' % (spacer,s.A))
  s.m[s.P + k].H = s.P; s.P += k 
  s.m[s.P + 1].H = s.PC; s.PC = s.A << 1
  s.m[s.P + 2].H = s.PC >> 1; s.A = s.B 
  s.m[s.P + 3].H = _u(s.A) 
def Kn(n,s):  s.PC += 1; _k0(n,s)   #
def Kb(s):     k = s.b; s.PC += 2; _k0(k,s) #
def KH(s):    k = s.h; s.PC += 3; _k0(k,s) #
def KW(s):    k = s.w; s.PC += 5; _k0(k,s) #
def _k1(gn, k,s):
  if s.callTrace:
    s.callDepth += 1
    spacer = s.callDepth*'+'
    g = s.globalname.get(gn,'gn 0x%04x' % gn)
    BeebCfg.traceFile.write('%s| %s\n' % (spacer,g))
  s.m[s.P + k].H = s.P; s.P += k 
  s.m[s.P + 1].H = s.PC; s.PC = s[s.G, gn].M<<1  
  s.m[s.P + 2].H = s.PC >> 1 
  s.m[s.P + 3].H = _u(s.A)
def KnG(n,s):  gn = s.b;  s.PC += 2; _k1(gn,n,s)  #
def KnG1(n,s): gn = s.b1; s.PC += 2; _k1(gn,n,s) #
def KnGH(n,s): gn = s.b2;  s.PC += 2; _k1(gn,n,s) # gn = s.h;  s.PC += 3; _k1(gn,n,s) # !!!
def RTN(s):
  if s.callTrace:
    s.callDepth -= 1
  s.PC = s.m[s.P + 1].H; s.P = s.m[s.P].H 

#  Control Flow -   tests
def J(s):  s.PC = s[s.b].atR  #
def J_(s): s.PC = s[s.b].atRI #
def Jrel(op,s):
  #print('Jrel %i %i %i' % ( s.B, s.A, op( s.B,s.A)))
  if op( _s(s.B), _s(s.A)): s.PC = s[s.b].atR
  else:  s.PC += 2 #
def Jrel_(op,s):  
  #print('Jrel_ %i %i %i' % ( s.B, s.A, op( s.B,s.A)))
  if op( _s(s.B),_s(s.A)): s.PC = s[s.b].atRI
  else:   s.PC += 2 #
def Jrel0(op,s):
  #print('Jrel0  %i %i' % ( s.A, op( _s(s.A),0)))
  if op(_s(s.A), 0): s.PC = s[s.b].atR
  else: s.PC += 2 #
def Jrel0_(op,s):
  if op(_s(s.A), 0): s.PC = s[s.b].atRI
  else:  s.PC += 2 #
def GOTO(s):      s.PC = s.A<<1 #
def FHOP(s):      s.A = 0; s.PC += 2 #

# Switch c
def SWL(s):
  x = s.PC >> 1
  n = s.m[x+1].h; default = s.m[x+2].h; offset = s.m[x+3].h
  index = s.A - offset
  #print('SWL: n = 0x%04x PC = 0x%04x A = 0x%04x' % (n,s.PC,s.A))
  #for i in range(0,n+4):
  #  print('L%02i = 0x%04x new PC = 0x%04x' %  (i, s.m[x+1+i].h, ((x+1+i)<<1) + s.m[x+1+i].h )   )
  if (index < 0) or (index >= n): s.PC = ((x+2)<<1) + default
  else: s.PC = ((x+4+index)<<1) + s.m[x+4+index].h

def SWB(s): # Linear version
  if (s.PC & 0x1) == 0x0: s.PC += 1  # skip filler byte
  x = (s.PC+1) >> 1
  n = s.m[x].h
  pc = s.PC + 3
  s.PC = pc + s.m[x+1].h # default value
  i = 1
  #print('SWB: n = 0x%04x default = 0x%04x A = 0x%04x' % (n,s.PC,s.A))
  while i <= n:
    Ki = s.m[x+2*i].h
    Ln = s.m[x+2*i + 1].h
    #print('Ki=0x%04x Ln = 0x%04x pc=0x%04x' % (Ki,Ln,pc+4*i+Ln))
    if _s(s.A) == Ki:
      s.PC = pc + 4*i + Ln 
      break
    i += 1
  pass
    
# Miscellaneous
def XCH(s):  s.A, s.B = s.B, s.A; s.PC += 1 #
def ATB(s):  s.B = s.A; s.PC += 1 #
def ATC(s):  s.C = s.A; s.PC += 1 #
def BTC(s):  s.C = s.B; s.PC += 1 #
def NOP(s):  s.PC += 1 #
def SYS(s):  print('### Undefined  - SYS ###'); s.PC += 1
def MDIV(s):  print('### Undefined - MDIV ###'); s.PC += 1
def CHGCO(s):  print('### Undefined - CHGCO ###'); s.PC += 1
def BRK(s):  print('### Undefined - BRK ###'); s.PC += 1
def UDn(n,s):  print('### Undefined 0x%02x ###' % n); s.PC += 1

# ==========================================================

class cintState:
  def __init__(self,PC=0x3f38,P=0x021d,A=0,B=0x4d02,C=0xffff,G=0x400,memory=None,os=None):
    self.m = memory
    self.P = P; self.PC = PC; self.G = G
    self.A = A; self.B = B; self.C = C
    self.instr = ''; self.error = False
    self.callDepth = 0
    #
    self.os = os
    #
    self.f = [
      N(UDn,0), N(UDn,1), N(BRK), N(Kn,3), N(Kn,4), N(Kn,5), N(Kn,6), N(Kn,7),
      N(Kn,8), N(Kn,9), N(Kn,10), N(Kn,11), N(LF), N(LF_), N(LM), N(LM1),
      N(Ln,0), N(Ln,1), N(Ln,2), N(Ln,3), N(Ln,4), N(Ln,5), N(Ln,6), N(Ln,7),
      N(Ln,8), N(Ln,9), N(Ln,10), N(FHOP), N(Jrel,eq), N(Jrel_,eq), N(Jrel0,eq), N(Jrel0_,eq),
      # 32
      N(Kb), N(KH), N(KW), N(KnG,3), N(KnG,4), N(KnG,5), N(KnG,6), N(KnG,7),
      N(KnG,8), N(KnG,9), N(KnG,10), N(KnG,11), N(S0G), N(LnG,0), N(LnG,1), N(LnG,2),
      N(LG), N(SG), N(LLG), N(AG), N(X2,mul), N(X2,floordiv), N(X2,mod), N(X2,xor),
      N(SL), N(SL_), N(LL), N(LL_), N(Jrel, ne), N(Jrel_, ne), N(Jrel0, ne), N(Jrel0_, ne),
      # 64
      N(LLP), N(LLPH), N(LLPW), N(KnG1,3), N(KnG1,4), N(KnG1,5), N(KnG1,6), N(KnG1,7),
      N(KnG1,8), N(KnG1,9), N(KnG1,10), N(KnG1,11), N(S0G1), N(LnG1,0), N(LnG1,1), N(LnG1,2),
      N(LG1), N(SG1), N(LLG1), N(AG1), N(X2,add), N(X2,sub), N(LSH), N(RSH),
      N(X2,and_), N(X2,or_), N(LLL), N(LLL_), N(Jrel,lt), N(Jrel_,lt), N(Jrel0,lt), N(Jrel0_,lt),
      # 96
      N(Lb), N(LH), N(LW), N(KnGH,3), N(KnGH,4), N(KnGH,5), N(KnGH,6), N(KnGH,7),
      N(KnGH,8), N(KnGH,9), N(KnGH,10), N(KnGH,11), N(S0GH), N(LnGH,0), N(LnGH,1), N(LnGH,2),
      N(LGH), N(SGH), N(LLGH), N(AGH), N(RVn,0), N(RVn,1), N(RVn,2), N(RVn,3),
      N(RVn,4), N(RVn,5), N(RVn,6), N(RTN), N(Jrel,gt), N(Jrel_,gt), N(Jrel0,gt), N(Jrel0_,gt),
      # 128
      N(LP), N(LPH), N(LPW), N(LPn,3), N(LPn,4), N(LPn,5), N(LPn,6), N(LPn,7),
      N(LPn,8), N(LPn,9), N(LPn,10), N(LPn,11), N(LPn,12), N(LPn,13), N(LPn,14), N(LPn,15),
      N(LPn,16), N(SYS), N(SWB), N(SWL), N(STn,0), N(STn,1), N(STn,2), N(STn,3),
      N(STPn,3), N(STPn,4), N(STPn,5), N(GOTO), N(Jrel,le), N(Jrel_,le), N(Jrel0,le), N(Jrel0_,le),
      # 160
      N(SP), N(SPH), N(SPW), N(SPn,3), N(SPn,4), N(SPn,5), N(SPn,6), N(SPn,7),
      N(SPn,8), N(SPn,9), N(SPn,10), N(SPn,11), N(SPn,12), N(SPn,13), N(SPn,14), N(SPn,15),
      N(SPn,16), N(Sn,1), N(Sn,2), N(Sn,3), N(Sn,4), N(XCH), N(GBYT), N(PBYT),
      N(ATC), N(ATB), N(J), N(J_), N(Jrel,ge), N(Jrel_,ge), N(Jrel0,ge), N(Jrel0_,ge),
      # 192
      N(AP), N(APH), N(APW), N(APn,3), N(APn,4), N(APn,5), N(APn,6), N(APn,7),
      N(APn,8), N(APn,9), N(APn,10), N(APn,11), N(APn,12), N(XPBYT), N(LMH), N(BTC),
      N(NOP), N(An,1), N(An,2), N(An,3), N(An,4), N(An,5), N(RVPn,3), N(RVPn,4),
      N(RVPn,5), N(RVPn,6), N(RVPn,7), N(STiPn,0,3), N(STiPn,0,4), N(STiPn,1,3), N(STiPn,1,4), N(MW),
      # 224
      N(Ab), N(AH), N(AW), N(LiPn,0,3), N(LiPn,0,4), N(LiPn,0,5), N(LiPn,0,6), N(LiPn,0,7),
      N(LiPn,0,8), N(LiPn,0,9), N(LiPn,0,10), N(LiPn,0,11), N(LiPn,0,12), N(Sb), N(SH), N(MDIV),
      N(CHGCO), N(NEG), N(INV), N(LiPn,1,3), N(LiPn,1,4), N(LiPn,1,5), N(LiPn,1,6), N(LiPn,2,3),
      N(LiPn,2,4), N(LiPn,2,5), N(LiPn,3,3), N(LiPn,3,4), N(LiPn,4,3), N(LiPn,4,4), N(UDn,254), N(UDn,255),
      ]
    #
    self.globalname = {}
    with open('./gv.txt','r') as f:
      for line in f:
        parts = line.split()
        self.globalname[ int(parts[0][:-1]) ] = parts[1]
      
  def step(self):
    self.handled = True
    self.callTrace = BeebCfg.callTracing
    self.ir = self.m[self.PC].B 
    self.instr = self.f[self.ir].func.__name__
    if BeebCfg.cintTracing: 
      spacer = self.callDepth*'+'
      BeebCfg.traceFile.write('%s %8s 0x%04x 0x%04x 0x%04x 0x%04x\n' %\
                                (spacer,self.instr,self.PC,self.A, self.B, self.C))
    self.f[self.ir](self)
    return self.handled
  
  def __getitem__(self, n): #
    self.idx = n
    #print('set idx ',self.idx)
    return self
    
  def getRegs(self):
    return [0,0,self.P,self.PC,_u(self.A),_u(self.B),_u(self.C),self.G]
  
  def putRegs(self,l):
    self.G = l[7]; self.P = l[2]; self.PC = l[3]  
    self.A = l[4]; self.B = l[5]; self.C = l[6]
    
  def setRW(self,rw):
    self.m.rw = rw
          
  @property
  def b(self): x = self.PC + 1; return self.m[x].B
    
  @property
  def b1(self): x = self.PC + 1; return self.m[x].B + 256 

  @property
  def b2(self): x = self.PC + 1; return self.m[x].B + 512 # !!!

  @property
  def h(self): x = self.PC + 1; return self.m[x].B+256*self.m[x+1].B # note: not aligned!!
  
  @property
  def w(self): x = self.PC + 1; return self.m[x].W 

  @property
  def M(self): return self.m[self.at].H
    
  @M.setter
  def M(self,data): 
    self.m[self.at].H = _u(data)
    
  @property
  def asByte(self): x = (self.atByte) & 0xffff; return self.m[x].B
    
  @asByte.setter
  def asByte(self,data):
    self.m[self.atByte].B = data & 0xff

  @property
  def Rel(self):
    x = self.atR
    return self.m[x>>1].H # ?? h or H
  
  @Rel.setter
  def Rel(self,data):
    #data = _u(data)
    self.m[self.atR>>1].H = _u(data)
    
  @property
  def RelInd(self): return self.m[self.atRI>>1].H # ?? h or H 
   
  @RelInd.setter
  def RelInd(self,data):
    self.m[self.atRI>>1].H = _u(data)
    
  @property
  def Var(self):
    return self.m[self.atVar].h
    
  @Var.setter
  def Var(self,data):
    self.m[self.atVar].h = data
    
  @property
  def at(self):
    x = self.idx
    #print(x)
    if type(x) == int: return x
    else:
      y = (x[0]+x[1]) #& 0xffff
      if len(x) == 2: return y #x[0] + x[1]
      else: 
        z = self.m[y].H + x[2]
        return z #& 0x7fff
  
  @property
  def atByte(self): x = self.idx[0]<<1; y =self.idx[1]; return x+y #
  
  @property
  def atR(self):  #
    x = self.PC + 1
    y = self.idx - 128
    #print('jmp %04x %04x' % (x,y))
    return (x + 1 + y)
  
  @property
  def atRI(self): # 
    b = self.idx
    q = (self.PC + 3 + 2*b) & 0xfffe # !!!
    #hh = self.m[q].B + 256*self.m[q+1].B
    hh = self.m[q>>1].H # ??h or H
    #print('b = 0x%02x q = %04x hh %04x' % (b,q,hh))
    return (q + hh) & 0xffff

  @property
  def atVar(self): # 
    b = self.idx
    q = (self.G + 0x100 + b)# !!!
    hh = self.m[q].h
    #print('b = 0x%02x q = %04x hh %x' % (b,q,hh))
    return hh #& 0x7fff

  #=====================================================================================================
  def processLF(self):
    pc = self.PC 
    self.handled = False  # default
    if pc ==   0x1786: self.opsys()
    elif pc == 0x17a0: self.callbyte()
    elif pc == 0x19e2: self.vdu()
    elif pc == 0x17bc: self.writeS()
    elif pc == 0x1752: self.move()
    elif pc == 0x167c: self.muldiv()
    elif pc == 0x1798: self.call()
    elif pc == 0x17b8: self.wrchr()
    elif pc == 0x0e0a: self.add32()
    elif pc == 0x0e38: self.sub32()
    elif pc == 0x0e5c: self.mul32()
    elif pc == 0x0e98: self.div32()
    elif pc == 0x0f4e: self.cmp32()
    elif pc == 0x5bb8: self.sine()
    elif pc == 0x5b96: self.cosine()
    elif pc == 0xb5aa: self.sqCol()
    else:
      outstr = '-- at 0x%04x' % pc 
      print('%s ' % outstr )
    # ... and return
    if self.handled:
      self.PC = 0x1563

  
  def opsys(self):
    pNew = self.P
    p0,p1,p2,p3 = self.m[(pNew+3)<<1].B,self.m[(pNew+4)<<1].B,self.m[(pNew+5)<<1].B,self.m[((pNew+5)<<1)+1].B
    addr,cpua,cpux,cpuy = 0xfff4,p0,p1,p2
    #print('opsys    0x%04x 0x%02x 0x%02x 0x%02x' % (addr, cpua, cpux, cpuy)  , end=' ')
    cpua, cpux, cpuy = self.m.osCall(addr, cpua, cpux, cpuy)
    #print('return 0x%02x 0x%02x 0x%02x' % (cpua,cpux,cpuy))
    self.A = cpux + 256*cpuy
    self.handled = True

  def callbyte(self):
    pNew = self.P
    p0,p1,p2,p3 = self.m[(pNew+3)].H,self.m[(pNew+4)<<1].B,self.m[(pNew+5)<<1].B,self.m[((pNew+5)<<1)+1].B
    addr,cpua,cpux,cpuy = p0,p1,p2,p3
    #print('callbyte 0x%04x 0x%02x 0x%02x 0x%02x' % (addr, cpua, cpux, cpuy)  , end=' ')
    cpua, cpux, cpuy = self.m.osCall(addr, cpua, cpux, cpuy)
    #print('return 0x%02x 0x%02x 0x%02x' % (cpua,cpux,cpuy))
    self.A = cpux + 256*cpuy
    self.m[0x40b].H = cpua # result in global MCRESULT
    self.handled = True

  def vdu(self):
    pNew = self.P
    pOld = self.m[pNew].H
    k = pNew - pOld
    pc,a= self.PC, self.A
    if a < 0: a += 0x10000
    a = a << 1
    pNew = pNew  + 4
    # merge parameters into format string
    count = self.m[a].B
    out1 = ''
    j = 0
    for i in range(count): 
      c = chr(self.m[a+1+i].B)
      if c == '%': 
        out1 += '%i' % self.m[pNew+j].H
        j += 1
      else: out1 += chr(self.m[a+1+i].B)
    # convert format string to bytes ready for vdu call
    out2 = []
    j = ''
    for c in out1:
      if c ==',':
        out2.append(int(j) & 0xff)
        j = ''
      elif c==';':
        if j == '#XFFFF': j = -1
        out2.append(int(j) & 0xff)
        out2.append(int(j)>>8)
        j = ''
      else: j += c
    if j != '': out2.append(int(j) % 0xff)
    #print('vdu ' , out2 )
    #
    for t in out2: self.A = t & 0x00ff; self.wrchr()  # make this more efficient idc
    self.handled = True
    
  def writeS(self):
    pc,a = self.PC, self.A
    if a < 0: a += 0x10000
    a = a << 1
    count = self.m[a].B
    outstr = ''
    for i in range(count):
      t = self.m[a+1+i].B
      self.A = t; self.wrchr()  # make this more efficient idc
      outstr += chr(t)
    s = 'writeS  '+4*'0x%02x ' % (self.m[a].B,self.m[a+1].B,self.m[a+2].B,self.m[a+3].B)
    #print(outstr)
    self.handled = True
    
  def move(self):  # src halfword, dest halfword, length
    pNew = self.P
    p0,p1,p2 = self.m[pNew+3].H, self.m[pNew+4].H,self.m[pNew+5].H
    #print('move from:0x%04x to:0x%04x length:0x%04x' % (p0,p1,p2))
    for i in range(p2):
      self.m[p1+i].H = self.m[p0+i].H
    self.A = (self.A & 0xff) + 0x200*(p2 & 0x7f)
    self.handled = True
    
  def muldiv(self): # signed !
    pNew = self.P
    p0,p1,p2 = self.m[pNew+3].h,self.m[pNew+4].h,self.m[pNew+5].h
    p3,p4 = divmod((p0 * p1),p2)
    r2 = self.m[0x40f].h
    if p3 < 0: p3 += 1; p4 -= p2 # fix up to agree with bcpl library routine
    #print('\nmuldiv (%i * %i)/%i = %i rem %i pre-r2 %i' % (p0,p1,p2,p3,p4,r2))
    self.A = p3
    self.m[0x40f].h = p4 # gn_result2
    self.handled = True

  def add32(self):
    pNew = self.P
    p0,p1 = self.m[pNew+3].H<<1,self.m[pNew+4].H<<1 
    # 4 byte words are not aligned
    y0 = self.m[p0].B+(self.m[p0+1].B<<8)+(self.m[p0+2].B<<16)+(self.m[p0+3].B<<24)
    y1 = self.m[p1].B+(self.m[p1+1].B<<8)+(self.m[p1+2].B<<16)+(self.m[p1+3].B<<24)
    y2 = y1 + y0
    if (y2 & 0x100000000) == 0: carry = 0x0000
    else: carry = 0xffff
    result = y2 & 0xffffffff
    #print('add32 0x%08x + 0x%08x = 0x%08x at 0x%04x, 0x%04x' % (y0,y1,y2,p0,p1))
    self.m[p1].B = y2 & 0xff; self.m[p1+1].B = (y2>>8) & 0xff
    self.m[p1+2].B = (y2>>16) & 0xff; self.m[p1+3].B = (y2>>24) & 0xff
    self.A = carry
    self.handled = True
    
  def sub32(self):
    pNew = self.P
    p0,p1 = self.m[pNew+3].H<<1,self.m[pNew+4].H<<1
    #
    y0 = self.m[p0].B+(self.m[p0+1].B<<8)+(self.m[p0+2].B<<16)+(self.m[p0+3].B<<24)
    y1 = self.m[p1].B+(self.m[p1+1].B<<8)+(self.m[p1+2].B<<16)+(self.m[p1+3].B<<24)
    y2 = y1 - y0
    #print('sub32 0x%08x - 0x%08x = 0x%08x at 0x%04x, 0x%04x' % (y0,y1,y2,p0,p1))
    self.m[p1].B = y2 & 0xff; self.m[p1+1].B = (y2>>8) & 0xff
    self.m[p1+2].B = (y2>>16) & 0xff; self.m[p1+3].B = (y2>>24) & 0xff
    self.A = 0x0400 # residual values of cpu.x and cpu.y after 6502 sub32 routine
    self.handled = True

  def mul32(self):
    pNew = self.P
    p0,p1 = self.m[pNew+3].H<<1,self.m[pNew+4].H<<1
    #
    y0 = self.m[p0].B+(self.m[p0+1].B<<8)+(self.m[p0+2].B<<16)+(self.m[p0+3].B<<24)
    y1 = self.m[p1].B+(self.m[p1+1].B<<8)+(self.m[p1+2].B<<16)+(self.m[p1+3].B<<24)
    y2 = y1 * y0
    #print('mul32 0x%08x * 0x%08x = 0x%08x at 0x%04x, 0x%04x' % (y0,y1,y2,p0,p1))
    self.m[p1].B = y2 & 0xff; self.m[p1+1].B = (y2>>8) & 0xff
    self.m[p1+2].B = (y2>>16) & 0xff; self.m[p1+3].B = (y2>>24) & 0xff
    self.A = 0xffff
    self.handled = True

  def div32(self): 
    pNew = self.P
    p0,p1,p2 = self.m[pNew+3].H<<1,self.m[pNew+4].H<<1,self.m[pNew+5].H<<1
    #
    y0 = self.m[p0].B+(self.m[p0+1].B<<8)+(self.m[p0+2].B<<16)+(self.m[p0+3].B<<24)
    y1 = self.m[p1].B+(self.m[p1+1].B<<8)+(self.m[p1+2].B<<16)+(self.m[p1+3].B<<24)
    if y0 == 0: self.A = 0
    else:
      self.A = 0xffff
      y2,y3 = divmod(y1,y0)
      #print('div32 0x%08x / 0x%08x = 0x%08x rem 0x%08x at 0x%04x, 0x%04x, 0x%04x' % (y1,y0,y2,y3,p0,p1,p2))
      self.m[p1].B = y2 & 0xff; self.m[p1+1].B = (y2>>8) & 0xff
      self.m[p1+2].B = (y2>>16) & 0xff; self.m[p1+3].B = (y2>>24) & 0xff
      self.m[p2].B = y3 & 0xff; self.m[p2+1].B = (y3>>8) & 0xff
      self.m[p2+2].B = (y3>>16) & 0xff; self.m[p2+3].B = (y3>>24) & 0xff
    self.handled = True

  def cmp32(self): # compare SIGNED 32 bit numbers
    pNew = self.P
    p0,p1 = self.m[pNew+3].H<<1,self.m[pNew+4].H<<1
    y0 = self.m[p0].B+(self.m[p0+1].B<<8)+(self.m[p0+2].B<<16)+(self.m[p0+3].B<<24)
    y1 = self.m[p1].B+(self.m[p1+1].B<<8)+(self.m[p1+2].B<<16)+(self.m[p1+3].B<<24)
    if y0 > 0x80000000: y0 -= 0x100000000
    if y1 > 0x80000000: y1 -= 0x100000000
    if y1 < y0: y2 = 1
    elif y1 == y0: y2 = 0
    else: y2 = 0xffff
    #print('cmp32 0x%08x to 0x%08x = 0x%08x at 0x%04x, 0x%04x' % (y1,y0,y2,p0,p1))
    self.A = y2
    self.handled = True

  
  def call(self):  print('Call')
  
  def wrchr(self):  
    #print('Writechr chr=%s' % chr(self.A & 0x00ff))
    addr,cpua,cpux,cpuy = 0xffee,self.A & 0x00ff, 0x00, 0x00
    cpua, cpux, cpuy = self.m.osCall(addr, cpua, cpux, cpuy)
    self.A = cpux + 256*cpuy
    self.handled = True
    
  def sine(self): 
    x = self.A
    if x > 0x7fff: x = (x-0x10000)*0.0001
    else: x = x*0.0001
    y = sin(x)
    self.A = int(y*10000)
    if self.A < 0: self.A += 0x10000
    #print('sine(%f) =  %f returning 0x%04x' % (x,y,self.A))
    self.handled = True

  def cosine(self): 
    x = self.A
    if x > 0x7fff: x = (x-0x10000)*0.0001
    else: x = x*0.0001
    y = cos(x)
    self.A = int(y*10000)
    if self.A < 0: self.A += 0x10000
    #print('cosine(%f) =  %f returning 0x%04x' % (x,y,self.A))
    self.handled = True
    
  def sqCol(self):
    # Called from g.nm.plot.fine, within nested loops.
    # Choosing colour value g.nm.square.colour
    # 
    pNew = self.P
    p0 = self.m[pNew+3].H
    value = self.m[p0].H
    class_col = self.m[self.G+360].H
    class_upb = self.m[self.G+361].H
    self.handled = True
    cl = 0
    #for i in range(10): print(self.m[class_upb+i].h)
    while cl < 5: # max class size m.nm.max.num.of.class.intervals
      upb = self.m[class_upb+cl].h
      if value <= upb: break
      else: cl += 1
    self.A = self.m[class_col+cl].H
    #print('sqCol value=%i, upb=%i, class %i colour %i' % (value, upb,cl,self.A))
  


    

