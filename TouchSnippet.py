# -*- coding: utf-8 -*-
# 
# touch-editor is based on wx.stc.StyledTextCtrl
# author : juntao.qiu@gmail.com
# date   : 2012/02/11
#

import re
import sys, os

#VAR_PATTERN = "\$\{[^\{\w\.\:]+\}"
VAR_PATTERN = "\$\{[^\}]+\}"

class TouchSnippet(object):
    def __init__(self, template):
        self.template = template
        self.stop = False
        self.prev = -1
        self.temp = ''

    def Build(self):
        #print self.template
        pattern = re.compile(VAR_PATTERN, re.IGNORECASE)
        it = pattern.finditer(self.template)
        
        self.it = []
        pos = 0
        for i in it:
            obj = {}
            group = i.group()
            inner = group[2:-1]
            index, default = inner.split(':')
            obj['span'] = i.span()
            obj['position'] = pos
            pos += 1
            obj['index'] = index
            obj['default'] = "" if len(default) == 0 else default
            obj['length']  = 0 if len(default) == 0 else len(default)
            self.it.append(obj)
        
        #sort list by position
        sorted(self.it, key=lambda item: item['position'])

        self.index = 0
        self.itlen = len(self.it)

    def NextPos(self):
        if self.stop:
            return (-1, -1)
        next = self.it[self.index]
        self.last = self.index
        self.index += 1
        if self.index == self.itlen:
            self.index = 0
        
        if next['index'] == "0":
            self.stop = True
        return next['span']

    def PrevPos(self):
        if self.stop:
            return (-1, -1)
        prev = self.it[self.index]
        self.last = self.index
        self.index -= 1
        if self.index < 0:
            self.index = self.itlen - 1

        #if jumped to the last tag, stop
        if prev['index'] == "0":
            self.stop = True
        return prev['span']

    def CurrentPos(self):
        return self.index

    def GetVarCount(self):
        return self.itlen

    def ReArrange(self):
        pass

    def Update(self, newchar):
        item = self.it[self.last]
        #print item, chr(newchar)
        print "self.index=%d, self.last=%d" % (self.last, self.prev)
        if self.last == self.prev:
            self.temp += chr(newchar)
        else:
            self.temp = ''
            self.temp = chr(newchar)
        self.prev = self.last

        offset = 0
        print "len(self.temp) = %d, item[length] = %d" % (len(self.temp), item['length'])
        offset = len(self.temp) - item['length']
        item['length'] = len(self.temp)
        print "len(self.temp) = %d, item[length] = %d" % (len(self.temp), item['length'])
        start, end = item['span']
        item['span'] = (start, start+len(self.temp))

        for i in range(self.last+1, self.itlen):
            s, e = self.it[i]['span']
            self.it[i]['span'] = (s+offset, e+offset)

        #print item
        #print self.temp, len(self.temp)

    def _GetDefault_(self, item):
        if len(item['default']) > 0:
            return item['default']
        else:
            #try to get the inherit value
            for o in self.it:
                if o['index'] == item['index'] and len(o['default']) > 0:
                    return o['default']
            return ""

    def Arrange(self):
        template = self.template
        pattern = re.compile(VAR_PATTERN, re.IGNORECASE)
        li = pattern.findall(template)

        if len(self.it) == 0:
            return self.template

        start, end = self.it[0]['span']
        offset = 0
        end = 0

        for i in range(len(self.it)):
            item = self.it[i]
            default = self._GetDefault_(item)
            s, e = item['span']
            start = s - offset
            end = start + len(default)
            self.it[i]['length'] = len(default)
            self.it[i]['span'] = (start, end)
            offset += len(li[i]) - len(default)
            template = template.replace(li[i], default)

        return template

    def Print(self):
        print self.Arrange()

defaultSnippets = {
    "inc_template" : "#include \"${1:idp_api.h}\"${0:}", 
    "Inc_template" : "#include <${1:stdio.h}>${0:}", 
    "td_template"  : "typedef ${1:int} ${2:my_int};", 
    "struct_template" : "struct ${1:name}{\n\t${0:/*data*/}\n};\n", 

    "if_template"  : "if(${1:cond}){\n\t${0:/*code*/}\n}\n", 
    "ifel_template" : "if(${1:cond}){\n\t${2:/*code*/}\n}else{\n\t${3:/*code*/}\n}\n", 
    "while_template" : "while(${1:cond}){\n\t${0:/*code*/}\n}\n", 
    "for_template" : "for(int ${1:i} = ${2:0}; ${1:} < ${3:count}; ${1:} += ${4:1}){\n\t${0:/*code*/}\n}\n", 
    "dowhile_template" : "do{\n\t${0:/*code*/}\n}while(${1:cond});\n", 
 
    "main_template" : "int main(int argc, char *argv[]){\n\t${0:/*code*/}\n\treturn 0;\n}\n",
    "static_tempalte" : "int i = 0;\n"
}

if __name__ == "__main__":
    #inc = TouchSnippet(inc_template)
    for key in defaultSnippets:
        """
        if not key == 'for_template':
            continue
        """
        snippet = TouchSnippet(defaultSnippets[key])
        snippet.Build()
        result = snippet.Arrange()
        print defaultSnippets[key], result
        for i in range(snippet.GetVarCount()):
            s, e = snippet.NextPos()
            print result[s:e]


