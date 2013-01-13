# -*- coding: utf-8 -*-
# 
# touch-editor is based on wx.stc.StyledTextCtrl
# author : juntao.qiu@gmail.com
# date   : 2012/02/11
#

class CommonHelper(object):
    # function declareation map
    fdmap = {}
    # user-define keywords
    udkeys = []
    #pre-defined keywords
    keywords = []

    def __init__(self, ext):
        self.ext = ext
        self.loadKeywords()
        self.loadTips()

    def loadFileToList(self, file, list):
        f = open(file, "rb")
        if not f:
            return
        line = f.readline()
        while line:
            list.append(line.strip())
            line = f.readline()

        f.close()

    def loadKeywords(self):
        self.loadFileToList("extra\c.kw", self.keywords)
        self.loadFileToList("extra\oracle.kw", self.keywords)
        self.keywords.sort()

    def loadTips(self):
        f = open("extra\idp.api", "rb")
        if not f:
            return

        line = f.readline()
        while line:
            pos = line.find('(')
            
            if pos == -1:
                self.udkeys.append(line)
                line = f.readline()
                continue
            else:
                key = line[:pos]
                value = line
                self.fdmap[key] = line
                self.udkeys.append(key)
            line = f.readline()

        f.close()
        return

    def GetKeywords(self):
        return self.keywords

    def GetFunctionMap(self):
        return self.fdmap

    def GetUserKeywords(self):
        return self.udkeys

class SnippetHelper(object):
    defaultSnippets = {
        "inc"    : "#include \"${1:idp_api.h}\"${0:}", 
        "Inc"    : "#include <${1:stdio.h}>${0:}", 
        "td"     : "typedef ${1:int} ${2:my_int};${0:}", 
        "def"    : "#ifndef ${1:MACRO}\n#define ${1:MACRO} ${2:MACRO}\n#endif${0:}\n",
        "struct" : "struct ${1:name}{\n\t${0:/*data*/}\n};\n", 

        "if"     : "if(${1:cond}){\n\t${0:/*code*/}\n}\n", 
        "ifel"   : "if(${1:cond}){\n\t${2:/*code*/}\n}else{\n\t${3:/*code*/}\n}${0:}", 
        "while"  : "while(${1:cond}){\n\t${0:/*code*/}\n}\n", 
        "for"    : "for(int ${1:i} = ${2:0}; ${1:} < ${3:count}; ${1:} += ${4:1}){\n\t${0:/*code*/}\n}\n", 
        "dow"    : "do{\n\t${0:/*code*/}\n}while(${1:cond});\n", 
     
        "main"   : "int main(int argc, char *argv[]){\n\t${0:/*code*/}\n\treturn 0;\n}\n",
    }

    def GetDefaultSnippets(self):
        return self.defaultSnippets

if __name__ == "__main__":
    helper = CommonHelper([])
    print helper.GetKeywords()
    print helper.GetFunctionMap()
    print helper.GetUserKeywords()

    snippetHelper = SnippetHelper()
    print snippetHelper.GetDefaultSnippets()
