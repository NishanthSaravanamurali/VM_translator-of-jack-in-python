from tkinter import *
import tkinter.messagebox as messagebox
from tkinter import filedialog
import sys
import os
import re

memseg={"local":"LCL","argument":"ARG","this":"THIS","that":"THAT"}
mempoint={"0":"THIS","1":"THAT"}
aritop=["add","sub","neg","not","and","or","eq","gt","lt"]

fnsfiles=[]
callfns=[]
SP=256
z=[]
callcount=0
func=""

def C_ARITHMETIC(x,i):
    global z
    arithmetic={"add":["@SP","AM=M-1","D=M","A=A-1","M=D+M"],
                "sub":["@SP","AM=M-1","D=M","A=A-1","M=M-D"],
                "neg":["@SP","A=M-1","M=M-1","M=!M"],
                "not":["@SP","A=M-1","M=!M"],
                "and":["@SP","AM=M-1","D=M","A=A-1","M=D&M"],
                "or":["@SP","AM=M-1","D=M","A=A-1","M=D|M"],
                "eq":["@SP","M=M-1","A=M","D=M","A=A-1","D=M-D","@YES"+str(i),"D;JEQ","@SP","A=M-1","M=0","@END"+str(i),"0;JMP","(YES"+str(i)+")","@SP","A=M-1","M=-1","(END"+str(i)+")"],
                "gt":["@SP","M=M-1","A=M","D=M","A=A-1","D=M-D","@YES"+str(i),"D;JGT","@SP","A=M-1","M=0","@END"+str(i),"0;JMP","(YES"+str(i)+")","@SP","A=M-1","M=-1","(END"+str(i)+")"],
                "lt":["@SP","M=M-1","A=M","D=M","A=A-1","D=M-D","@YES"+str(i),"D;JLT","@SP","A=M-1","M=0","@END"+str(i),"0;JMP","(YES"+str(i)+")","@SP","A=M-1","M=-1","(END"+str(i)+")"]}
    z.extend(arithmetic[x])

def push_memseg(x,i):
    global SP
    global memseg
    global z
    inst=["@"+memseg[x],"D=M","@"+str(i),"D=D+A","@13","AM=D","D=M","@SP","A=M","M=D","@SP","M=M+1"]
    z.extend(inst)

def pop_memseg(x,i):
    global SP
    global memseg
    global z
    inst=["@"+memseg[x],"D=M","@"+str(i),"D=D+A","@13","M=D","@SP","M=M-1","A=M","D=M","@13","A=M","M=D"]
    z.extend(inst)

def push_constant(i):
    global SP
    global z
    inst=["@"+str(i),"D=A","@SP","M=M+1","A=M-1","M=D"]
    z.extend(inst)

def push_temp(i):
    global SP
    global z
    inst=["@"+str(i),"D=A","@5","D=D+A","@13","AM=D","D=M","@SP","A=M","M=D","@SP","M=M+1"]
    z.extend(inst)

def pop_temp(i):
    global SP
    global z
    inst=["@"+str(i),"D=A","@5","D=D+A","@13","M=D","@SP","M=M-1","A=M","D=M","@13","A=M","M=D"]
    z.extend(inst)

def push_pointer(i):
    global SP
    global mempoint
    global z
    inst=["@"+mempoint[i],"D=M","@SP","A=M","M=D","@SP","M=M+1"]
    z.extend(inst)

def pop_pointer(i):
    global SP
    global mempoint
    global z
    inst=["@SP","AM=M-1","D=M","@"+mempoint[i],"M=D"]
    z.extend(inst)

def push_static(i):
    global SP
    global z
    global func
    global dripathlist
    if func=="":
        func=dirpathlist[-1]
    else:
        func2=func.split(".")
        func=func2[0]
    inst=["@"+func+"."+str(i),"D=M","@SP","A=M","M=D","@SP","M=M+1"]
    z.extend(inst)
    
def pop_static(i):
    global SP
    global z
    global func
    global dripathlist
    if func=="":
        func=dirpathlist[-1]
    else:
        func2=func.split(".")
        func=func2[0]
    inst=["@"+func+"."+str(i),"D=M","D=A","@13","M=D","@SP","AM=M-1","D=M","@13","A=M","M=D"]
    z.extend(inst)

def label(x):
    global z
    z.append("("+x+")")

def label_nocondition(x):
    global z
    z.extend(["@"+x,"0;JMP"])

def label_ifcondition(x):
    global z
    z.extend(["@SP","AM=M-1","D=M","@"+x,"D;JNE"])

def function(x,i):
    global z
    global func
    func=x
    inst=["("+x+")"]
    z.extend(inst)
    for j in range(int(i)):
        z.extend(["@SP", "A=M", "M=0", "@SP", "M=M+1"])

def functionreturn():
    global  z
    z.extend(["@LCL", "D=M", "@R13", "M=D","@5", "A=D-A", "D=M", "@R14", "M=D","@SP", "M=M-1", "A=M", "D=M", "@ARG", "A=M", "M=D","@ARG", "D=M", "@SP", "M=D+1","@R13", "AM=M-1", "D=M", "@THAT", "M=D","@R13", "AM=M-1", "D=M", "@THIS", "M=D","@R13", "AM=M-1", "D=M", "@ARG", "M=D","@R13", "AM=M-1", "D=M", "@LCL", "M=D","@R14", "A=M", "0;JMP"])

def call(x,i):
    global z
    global callcount
    z.extend(["@"+x+".return"+str(callcount), "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
    for pointer in ["@LCL", "@ARG", "@THIS", "@THAT"]:
        z.extend([pointer, "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
    z.extend(["@SP", "D=M", "@LCL", "M=D", "@5", "D=D-A", "@"+i, "D=D-A", "@ARG", "M=D", "@"+x,"0;JMP","("+x+".return"+str(callcount)+")"])
    callcount=callcount+1


def seperator(code):
    global aritop
    a=0
    for i in code:
        if len(i)==3:
            if  i[0]=='push':
                if i[1] in memseg.keys():
                    push_memseg(i[1],i[2])
                elif i[1]=="constant":
                    push_constant(i[2])
                elif i[1]=="temp":
                    push_temp(i[2])
                elif i[1]=="static":
                    push_static(i[2])
                elif i[2] in mempoint.keys():
                    push_pointer(i[2])
                else:
                    pass
            elif i[0]=="pop":
                if i[1] in memseg.keys():
                    pop_memseg(i[1],i[2])
                elif i[1]=="temp":
                    pop_temp(i[2])
                elif i[1]=="static":
                    pop_static(i[2])
                elif i[2] in mempoint.keys():
                    pop_pointer(i[2])
                else:
                    pass
            elif i[0]=="function":
                function(i[1],i[2])
            elif i[0]=="call":
                call(i[1],i[2])
        elif len(i)==2:
            if i[0]=="label":
                label(i[1])
            elif i[0]=="if-goto":
                label_ifcondition(i[1])
            elif i[0]=="goto":
                label_nocondition(i[1])
        elif len(i)==1:
            if i[0] in aritop:
                C_ARITHMETIC(i[0],a)
                a=a+1;
            elif i[0]=="return":
                functionreturn()
            else:
                pass
        else :
            pass
    
def writefile():
    global z
    global dir_path
    global dirpathlist
    filename2=""
    filename2=dir_path+"\\"+dirpathlist[-1]+".asm"
    file2=open(filename2,"w")
    for j in z:
        file2.writelines((j)+"\n")
    messagebox.showinfo("Information", "result file is stored in:"+filename2)
    file2.close()

def setvaluecheck():
    global z
    global filename
    global dir_path
    global dirpathlist
    global code
    global dir_list
    global fnsfiles
    global callfns
    filename4=""
    filename4=filename4+dir_path+"\\"+dirpathlist[-1]+".TST"
    setlst={}
    flg=0
    try:
        file4=open(filename4,"r")
        code2=(file4.readlines())
        code2=[s.replace('\n','') for s in code2]
        code2=[s.replace('\t','') for s in code2]
        code2=[s.split("\\")[0] for s in code2]
        code2=[s.split("//")[0] for s in code2]
        code2= [x for x in code2 if x != '']
        code2=[s.strip() for s in code2]
        code2=[s.split(" ") for s in code2]
        
        for i in code2:
            if len(i)==3:
                if i[0]=="set":
                    setlst[re.findall(r'\d+', i[1])[0]]=re.findall(r'\d+', i[2])[0]
                flg=1
    
    except FileNotFoundError:
            messagebox.showwarning("warning", filename4+"is not present in directory")

    q=filename.split("/")
    dir_list.remove(q[-1])
    dir_list=[s.split(".") for s in dir_list]
    for j in dir_list:
        if len(j)==2:
            if j[1]=="vm":
                flg=0
    c=0
    for k in code:
        if k[0]=="function":
            c=c+1;
        elif k[0]=="call":
            c=c+1
            fnsfiles.append(k[1].split(".")[0])
            callfns.append(k[1].split(".")[1])
    if c>2:
        flg=0
    
    if flg==0:
        z.extend(["@256", "D=A", "@SP", "M=D"])
        call("Sys.init", str(0))
        z[-3]="@Main.main"
        z.extend(["@Sys.init.return0","0;JMP"])
    elif flg==1:
        for j in setlst.keys():
            z.extend(["@"+str(setlst[j]),"D=A", "@"+str(j), "M=D"])

def codecheck(x):
    global filename
    global dir_path
    global dir_list
    global code
    global fnsfiles
    global callfns
    fnsfileslst=[]
    for i in fnsfiles:
        if i not in fnsfileslst:
            fnsfileslst.append(i)
    print(fnsfileslst)
    code2=[]
    for j in dir_list:
        if len(j)==2:
            if j[1]=="vm":
                if j[0] in fnsfileslst:
                    filename3=""
                    filename3=filename3+dir_path+"\\"+j[0]+".VM"
                    file3 = open(filename3, "r")
                    code1=(file3.readlines())
                    code1=[s.replace('\n','') for s in code1]
                    code1=[s.replace('\t','') for s in code1]
                    code1=[s.split("\\")[0] for s in code1]
                    code1=[s.split("//")[0] for s in code1]
                    code1=[s.strip() for s in code1]
                    code1= [x for x in code1 if x != '']
                    code1=[s.split(" ") for s in code1]
                    print(code1)
                    code2=code2+code1
    code2.extend(code)
    code=code2
    print(code)

def browseFiles():
    global filename
    global count
    global code
    global dir_path
    global dirpathlist
    global dir_list
    resetglobal()
    filename = filedialog.askopenfilename(initialdir = "/",title = "Select a File",filetypes = (("Text files","*.txt*"),("all files","*.*")))
    file1 = open(filename, "r")
    code=(file1.readlines())
    code=[s.replace('\n','') for s in code]
    code=[s.replace('\t','') for s in code]
    code=[s.split("\\")[0] for s in code]
    code=[s.split("//")[0] for s in code]
    code=[s.strip() for s in code]
    code = [x for x in code if x != '']
    code=[s.split(" ") for s in code]
    dir_path = os.path.dirname(os.path.realpath(filename))
    dir_list = os.listdir(dir_path)
    dirpathlist=dir_path.split("\\")
    setvaluecheck()
    codecheck(code)
    seperator(code)
    writefile()

def resetglobal():
    global z
    z=[]

root=Tk()
root.title("VM_Translator")
root.geometry("500x300")
root.configure(bg="#FFFFFF")
frame1 = Frame(root,background="#FFFFFF")
lbl1= Label(frame1, text = "VM_Translator", font=('Arial',25,'bold'),bg="#FFFFFF",fg='#000FFF')
lbl1.pack()
frame1.pack()
frame2=Frame(root,background="#FFFFFF")
btn1 = Button(frame2, text="open file",command=browseFiles,relief='flat',font=('Ariel',8,'bold'),width=7,height=1,bg="#000FFF",fg="#FFFFFF",activebackground="#FFFFFF",activeforeground="#000FFF")
btn1.grid(row=5,column=1,padx=28,sticky='w',columnspan=2,pady=20)
frame2.pack()
root.mainloop()
