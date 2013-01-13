# -*- coding: utf-8 -*-
# 
# touch-editor is based on wx.stc.StyledTextCtrl
# author : juntao.qiu@gmail.com
# date   : 2012/02/11
#
import wx
import wx.stc as stc

from wx.lib.pubsub import Publisher

import re
import sys, os

reload(sys)
sys.setdefaultencoding('utf-8')

import HelperUtil
import TouchSnippet

wildcard =  "C source file (*.c)|*.c|"\
            "All files (*.*)|*.*"

class TouchEditorBase(stc.StyledTextCtrl):
    # Margins
    MARK_MARGIN = 0
    NUM_MARGIN  = 1
    FOLD_MARGIN = 2

    faces = {
        'times': 'Courier New',
        'mono' : 'Courier New',
        'helv' : 'Courier New',
        'other': 'Courier New',
        'size' : 11,
        'linesize': 10,
    }

    def getBMarkerNumber(self):
        return self.BMarkerNumber

    def InitSnippets(self):
        snippetHelper = HelperUtil.SnippetHelper()
        snippets = snippetHelper.GetDefaultSnippets()
        for item in snippets:
            self.snippets[item] = snippets[item]

    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        self.helper = HelperUtil.CommonHelper([])
        self.snippets = {}
        self.InitSnippets()

        self.isBundleMode = False
        self.currentSnippet = None
        self.hasOutdentWord = re.compile(r"\b(?:break|continue|return)\b")
        self.lineEnding = '\n'
        self.BMarkerNumber = 10

        self.macro = []

        # ctrl-+(in), ctrl--(out)
        self.CmdKeyAssign(ord('+'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('-'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        self.Bind(stc.EVT_STC_MACRORECORD, self.OnRecordMacro)
        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(stc.EVT_STC_CHARADDED, self.OnCharAdded)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        self.Bind(stc.EVT_STC_MODIFIED, self.OnModified)
        self.StyleClearAll()  # Reset all to be like the default
        self.InitUI()

    def OnRecordMacro(self, event):#{{{
        if self.recording:
            msg = event.GetMessage()
            if msg == 2170:
                pos = self.GetCurrentPos()
                lparam = self.GetTextRange(pos-1, pos)
            else:
                lparam = event.GetLParam()
            macro = (msg, event.GetWParam(), lparam)
            print macro
            self.macro.append(macro)
        else:
            event.Skip()

    def StartRecordMacro(self):
        self.recording = True
        self.StartRecord()

    def StopRecordMacro(self):
        self.recording = False
        self.StopRecord()#}}}

    def GetEOLChar(self):
        #m = self.GetEOLMode():
        return u'\r\n'

    def PlayRecordMacro(self):
        self.BeginUndoAction()

        for message in self.macro:
            if message[0] == 2170:
                self.AddText(message[2])
            elif message[0] == 2001:
                self.AddText(self.GetEOLChar() + u' '*(message[1] - 1))
            else:
                self.SendMsg(message[0], message[1], message[2])

        self.EndUndoAction()
        

    def OnModified(self, event):
        pass

    def InitMargin(self):#{{{
        #hide left & right 1px margin
        self.SetMargins(0, 0)
        #using margin 0 to be book-marker
        self.SetMarginWidth(self.MARK_MARGIN, 16)
        self.SetMarginType(self.MARK_MARGIN, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(self.MARK_MARGIN, ~wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(self.MARK_MARGIN, True)
        
        #using margin 1 to be line-number
        self.SetMarginWidth(self.NUM_MARGIN, 32)
        self.SetMarginType(self.NUM_MARGIN, wx.stc.STC_MARGIN_NUMBER)
        #clear number-panel's mask
        self.SetMarginMask(self.NUM_MARGIN, 0)
        
        #using margin 2 to be folding
        self.SetMarginWidth(self.FOLD_MARGIN, 16)
        self.SetMarginType(self.FOLD_MARGIN, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(self.FOLD_MARGIN, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(self.FOLD_MARGIN, True)#mouse sensitive

        #define folding marker
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,             "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,           "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,           "white", "#808080")

        # Vim-visual-marker : #3A5FCD, Google Search button : #3D83F0
        self.MarkerDefine(self.BMarkerNumber, stc.STC_MARK_ARROW, "#3A5FCD", "#3A5FCD")#}}}

    def InitStyle(self):#{{{
        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % self.faces)
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(helv)s,size:%(linesize)d" % self.faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % self.faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")
        self.StyleClearAll()  # Reset all to be like the default

        # Default 
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%(helv)s,size:%(size)d" % self.faces)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(other)s,size:%(size)d" % self.faces)
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % self.faces)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%(helv)s,size:%(size)d" % self.faces)
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#7F007F,face:%(helv)s,size:%(size)d" % self.faces)
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % self.faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % self.faces)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % self.faces)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % self.faces)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % self.faces)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % self.faces)
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,face:%(helv)s,size:%(size)d" % self.faces)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%(size)d" % self.faces)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#000000,face:%(mono)s,back:#E0C0E0,eol,size:%(size)d" % self.faces)#}}}

    def InitUI(self):#{{{
        keywords = self.helper.GetKeywords()
        self.SetLexer(stc.STC_LEX_CPP)
        #self.SetKeyWords(0, " ".join(ckeys)+" ".join(plkeys))
        self.SetKeyWords(0, " ".join(keywords))
        #self.SetKeyWords(1, " ".join(plkeys))
        self.SetProperty("fold", "1")
        #keywords and other words has same size
        self.SetProperty("tab.timmy.whinge.level", "1")

        self.SetIndent(4)
        self.SetTabIndents(True)
        self.SetTabWidth(4)
        self.SetUseTabs(False)
        self.SetIndentationGuides(True)
        self.SetViewWhiteSpace(False)
        
        self.SetEdgeMode(stc.STC_EDGE_LINE)
        self.SetEdgeColumn(80)
        self.SetScrollWidth(100)

        self.InitMargin()
        self.InitStyle()

        self.SetSelBackground(True, "#316AC5")
        self.SetSelForeground(True, wx.WHITE)
        self.SetCaretForeground("BLUE")
        
        #highlight the current line
        self.SetCaretLineVisible(True)
        #wxPythonInAction : #FFFFCC, UE: #C4E8FD
        self.SetCaretLineBackground("#C4E8FD")

        #self.SetWrapStartIndent(1)
        # register some images for use in the AutoComplete box.
        self.RegisterImage(1, wx.Image("extra/icons/method.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.RegisterImage(2, wx.Image("extra/icons/keyword.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.RegisterImage(3, wx.Image("extra/icons/function.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())

        self.InitAutoComp()#}}}

    def InitAutoComp(self):
        self.AutoCompSetIgnoreCase(True)
        self.AutoCompSetAutoHide(False)
        self.AutoCompSetChooseSingle(False)
        self.AutoCompSetDropRestOfWord(False)
        self.AutoCompStops("([{,")

    def SetTitle(self, title):
        self.title = title

    def GetTitle(self):
        return self.title

    def TryShowCallTip(self, currentPos, word):
        #print word, fdmap[word]
        fdmap = self.helper.GetFunctionMap()
        if word in fdmap.keys():
            self.CallTipShow(currentPos, fdmap[word])
        else:
            return

    def OnCharAdded(self, event):#{{{
        if self.CallTipActive():
            self.CallTipCancel()

        charc = event.GetKey()

        if self.isBundleMode:
            snippet = self.currentSnippet
            snippet.Update(charc)

        if self.AutoCompActive():
            return
        # check if current style is a string or a comment
        currentPos = self.GetCurrentPos()
        try:
            entire_text = self.GetTextRange( self.PositionFromLine( self.GetCurrentLine() ), currentPos - 1 ) # wx2.5.2.9
            entire_text_all = self.GetTextRange( self.PositionFromLine( self.GetCurrentLine() ), currentPos)
        except:
            evt.Skip()
            return
  
        word = entire_text.strip().split('.')[-1:][0].split(' ')[-1:][0].strip()
        #print word

        #code calltips
        if chr(charc) == "(" and self.CallTipActive() == 0:
            if self.BraceMatch(currentPos-1) == -1:
                if self.GetCharAt(currentPos) != 40:
                    self.AddText(')')
                    self.SetSelection(currentPos, currentPos)
                self.TryShowCallTip(currentPos, word)
            return False

        # Auto END string
        elif chr(charc) == '"' and \
                         self.GetLineEndPosition(self.LineFromPosition(currentPos)) == currentPos:
            self.AddText('"')
            self.SetSelection(currentPos, currentPos)
            return False
        elif chr(charc) == '\'' and \
                         self.GetLineEndPosition(self.LineFromPosition(currentPos)) == currentPos:
            self.AddText('\'')
            self.SetSelection(currentPos, currentPos)
            return False
        elif chr(charc) == '[' and \
                         self.GetLineEndPosition(self.LineFromPosition(currentPos)) == currentPos:
            self.AddText(']')
            self.SetSelection(currentPos, currentPos)
            return False
        elif chr(charc) == '{' and \
                         self.GetLineEndPosition(self.LineFromPosition(currentPos)) == currentPos:
            self.AddText('}')
            self.SetSelection(currentPos, currentPos)
            return False#}}}

    def DupCurrentLine(self):
        lno = self.GetCurrentLine()
        if len(self.GetLine(lno)) == 0:
            pass
        self.LineDuplicate()
        self.GotoLine(lno+1)
        self.LineEnd()

    def DelCurrentLine(self):
        lno = self.GetCurrentLine()
        self.LineDelete()
        self.GotoLine(lno-1)
        self.LineEnd()

    def AutoIndent(self):#{{{
        lno = self.GetCurrentLine()
        pos = self.GetCurrentPos()
        col = self.GetColumn(pos)

        lstart = self.PositionFromLine(lno)
        line = self.GetLine(lno)[:pos-lstart]
        index = self.GetLineIndentation(lno)
        n = 0
        if col <= index:
            n = col
        elif pos:
            n = index

        if len(line) == 0:
            pass
        elif line[-1:] == "\\":
            if lno > 1:
                prl = self.GetLine(lno-1)
                if prl[-2:] == "\\\n":
                    n -= self.GetIndent()
            n += self.GetIndent()
        elif line[-1:] in "([":
            n += self.GetIndent()
        elif n >= self.GetIndent():
            if self.hasOutdentWord.search(line, index) is not None:
                n -= self.GetIndent()
            elif lno > 1:
                prl = self.GetLine(lno-1)
                #print prl
                if prl[-2:] == "\\\n" and n >= self.GetIndent():
                    n -= self.GetIndent()
        text = n*' '
        if self.GetUseTabs():
            text = text.replace(self.GetTabWidth()*' ', '\t')

        self.ReplaceSelection(self.lineEnding + text)#}}}

    def GetWordAtPos(self, pos):
        word = ''
        x = pos
        while x != wx.stc.STC_INVALID_POSITION:
            ch = self.GetCharAt(x)
            if ch <= 32 or ch > 128:
                if x != pos:
                    break
            word = chr(ch) + word
            x = x - 1
        return word.strip()

    def OnKeyPressed(self, event):#{{{
        if self.CallTipActive():
            self.CallTipCancel()

        key = event.GetKeyCode()

        #duplicate a line and move next end
        if key == ord('D') and event.ControlDown():
            self.DupCurrentLine()
        #delete a line and move privous start
        elif key == ord('U') and event.ControlDown():
            self.DelCurrentLine()
        #move cursor down
        elif key == ord('N') and event.ControlDown():
            self.GotoLine(self.GetCurrentLine()+1)
        #move cursor up
        elif key == ord('P') and event.ControlDown():
            self.GotoLine(self.GetCurrentLine()-1)
        #handle bundles here
        elif key == wx.WXK_TAB: 
            #print self.isBundleMode
            pos = self.GetCurrentPos()
            word = self.GetWordAtPos(pos)
            line = self.GetCurrentLine()

            #The very first time of BundleMode, init the snippetPos, gotoline, etc
            if word in self.snippets.keys() and not self.isBundleMode:
                self.isBundleMode = True
                instance = TouchSnippet.TouchSnippet(self.snippets[word])
                instance.Build()
                snippet = instance.Arrange()
                self.currentSnippet = instance
                self.DelWordLeft()
                self.AddText(snippet)
                self.GotoLine(line)
                self.snippetLine = line
                self.snippetPos = pos - len(word)

            #move to next position
            if self.isBundleMode:
                if event.ShiftDown():
                    start, end = self.currentSnippet.PrevPos()
                else:
                    start, end = self.currentSnippet.NextPos()

                if (start, end) == (-1, -1):
                    self.isBundleMode = False
                    self.snippetPos = -1
                    self.currentSnippet = None
                    return 

                self.SetSelection(self.snippetPos+start, self.snippetPos+end)
            else:
                event.Skip()
            
            keywords = self.helper.GetKeywords()
            udkeys = self.helper.GetUserKeywords()

            #auto-complete
            if event.ControlDown():
                conds = []
                for i in range(len(keywords)):
                    if keywords[i].startswith(word.lower()):
                        conds.append(keywords[i] + '?2')
                for i in range(len(udkeys)):
                    if udkeys[i].startswith(word.lower()):
                        conds.append(udkeys[i] + '?3')
                if len(conds) > 0:
                    conds.sort()
                    end = self.GetCurrentPos()
                    start = end - len(word)
                    self.AutoCompShow(len(word), " ".join(conds))

        elif key == 13 or key == 14:
            if self.AutoCompActive():
                return self.AutoCompComplete()
            self.AutoIndent()
        elif key == ord('T') and event.ControlDown():
            pos = self.GetCurrentPos()
        else:
            event.Skip()#}}}


    def OnUpdateUI(self, event):#{{{
        if self.AutoCompActive() or self.CallTipActive():
            return
        #update the status bar
        row = self.GetCurrentLine()
        pos = self.GetCurrentPos()
        col = self.GetColumn(pos)
        msg = {}
        msg['type'] = "pos"
        msg['row'] = row+1
        msg['col'] = col
        Publisher().sendMessage(('change_status'), msg)

        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)#}}}


    def OnMarginClick(self, evt):#{{{
        # fold and unfold as needed
        #print evt.GetMargin(), self.MarkerGet(self.LineFromPosition(evt.GetPosition()))
        #print self.GetMarginMask(1)
        if evt.GetMargin() == 0:
            lineClicked = self.LineFromPosition(evt.GetPosition())
            mask = self.MarkerGet(lineClicked)
            if mask == 1024:
                self.MarkerDelete(lineClicked, self.BMarkerNumber)
            else:
                self.MarkerAdd(lineClicked, self.BMarkerNumber)
        elif evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)#}}}


    def FoldAll(self):#{{{
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1#}}}

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):#{{{
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line#}}}

    def OpenResource(self, path):
        raise NotImplementedError

    def SaveResource(self):
        raise NotImplementedError

    def SaveResourceAs(self, newpath):
        raise NotImplementedError

    def CompileResource(Self):
        raise NotImplementedError

class NormalEditor(TouchEditorBase):
    def __init__(self, parent, id, title):
        TouchEditorBase.__init__(self, parent, -1)
        self.title = title
        self.path = None

    def GetTitle(self):
        return self.title

    def OpenResource(self, path):
        if not path or len(path) == 0:
            return False

        self.path = path
        file = open(path, 'r')
        try:
            text = file.read()
        except:
            print "error while read path", path
            return False
        finally:
            file.close()

        self.SetText(unicode(text))
        self.EmptyUndoBuffer()
        self.Colourise(0, -1)

        return True

    def GetContentPath(self):
        return self.path

    def SaveResource(self):
        if self.GetModify():
            text  = self.GetText()
            file = open(self.path, "wb")
            try:
                file.write(text)
                file.close()
            except:
                print "error while write"
                return False
            finally:
                file.close()
            return True

        return False

    def SaveResourceAs(self, newpath):
        if self.path == newpath:
            return False
        text  = self.GetText()
        file = open(newpath, "wb")
        try:
            file.write(text)
            file.close()
        except:
            print "error while write as", newpath
            return False
        finally:
            file.close()

        return True

class EditorFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, title="edtior frame",
            pos=wx.DefaultPosition, size=wx.DefaultSize):
        wx.Frame.__init__(self, parent, id, title, pos, size)

        url = ""
        self.editor = NormalEditor(self, -1, "debug")
        self.editor.OpenResource(url)

        self.BMarkerNumber = 10
        mb = self.MakeMenuBar()
        self.SetMenuBar(mb)

        self.editor.EmptyUndoBuffer()
        self.editor.Colourise(0, -1)

    def ChangeStatusBar(self, msg):
        info = msg.data
        stype = info['type']
        #print info
        if stype == 'pos':
            pos = "Row : %d" % info['row'] + ", Col : %d" % info['col']
            self.statusbar.SetStatusText(pos, 2)
        elif stype == 'mod':
            mod = self.GetTitle()
            self.statusbar.SetStatusText(mod+'*', 1)

    def GetMenuModel(self):
        return (
            ("&File",
             ("&Open\tCtrl-O",       "Open file for edit", "extra/icons/folder.png", self.OnFileOpen),
             ("&Save File\tCtrl-S",  "Save buffer to file", "extra/icons/disk.png", self.OnFileSave),
             ("Save File &As\tF12",  "Save file as another", None, self.OnFileSaveAs),
             ("E&xit\tAlt-F4",       "Exit editor", "extra/icons/cross.png", self.OnFileExit)),
            ("&Edit",
             ("&Copy\tCtrl-C",       "Copy",  "extra/icons/page_copy.png", self.OnEditCopy),
             ("Cut\tCtrl-X",         "Cut",  "extra/icons/cut.png", self.OnEditCut),
             ("&Paste\tCtrl-V",      "Paste",  "extra/icons/page_paste.png", self.OnEditPaste),
             ("",                    "",  "", ""),
             ("&Find\tCtrl-F",       "Find",  "extra/icons/find.png", self.OnEditFind),
             ("Replace\tCtrl-H",     "Replace", "extra/icons/page_white_find.png", self.OnEditReplace),
             ("&Goto Line\tCtrl-G",  "Goto special line", "extra/icons/textfield.png", self.OnEditGotoLine),
             ("Goto Brace\tCtrl-B",  "Goto brace matched", "extra/icons/textfield.png", self.OnEditGotoBrace),
             ("Goto Marker\tF2",     "Goto next marker", "extra/icons/bookmark.png", self.OnEditNextMarker),
             ("Toggle marker\tCtrl-F2", "Toggle a marker",  None, self.OnEditToggleMarker)),
            ("P&rogramming",
             ("Toggle Comment\tF3",  "Toggle comment",  "extra/icons/comment.png", self.OnProgToggleComment),
             ("Start Record\tCtrl-M", "Start Record", None, self.OnProgStartRecord),
             ("Stop Record\tAlt-M", "Start Record", None, self.OnProgStopRecord),
             ("Play Record\tAlt-P", "Start Record", None, self.OnProgPlayRecord))
            )

    def OnProgStartRecord(self, event):
        self.editor.StartRecordMacro()

    def OnProgStopRecord(self, event):
        self.editor.StopRecordMacro()

    def OnProgPlayRecord(self, event):
        self.editor.PlayRecordMacro()

    def OnFileOpen(self, event):
        directory = os.getcwd()
        dlg = wx.FileDialog(self, message="Choose a file", 
                defaultDir=directory, defaultFile="",
                wildcard=wildcard, style=wx.OPEN|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            title = os.path.basename(path)
            self.editor.OpenResource(path)

        dlg.Destroy()

    def OnFileSave(self, event):
        self.editor.SaveResource()
    
    def OnFileSaveAs(self, event):
        dlg = wx.FileDialog(self, message="Save file as ...",
                defaultDir=os.getcwd(), defaultFile=dfile, wildcard=wildcard,
                style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.editor.SaveResourceAs(path)
        
        dlg.Destroy()
    
    def OnFileExit(self, event):
        self.Close()        

    def MakeMenuBar(self):
        mb = wx.MenuBar()
        for each in self.GetMenuModel():
            label = each[0]
            items = each[1:]
            mb.Append(self.CreateMenu(items), label)
        return mb
    
    def CreateMenu(self, model):
        menu = wx.Menu()
        for label, status, image, handler in model:
            #print "(%s, %s)" % (label, image)
            if not label:
                menu.AppendSeparator()
                continue
            item = menu.Append(-1, label, status)
            if image:
                item.SetBitmap(wx.Image(image, wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            self.Bind(wx.EVT_MENU, handler, item)
        return menu

    def OnEditCopy(self, event):
        self.editor.Copy()

    def OnEditCut(self, event):
        self.editor.Cut()

    def OnEditPaste(self, event):
        self.editor.Paste()

    def OnEditFind(self, event):
        pass

    def OnEditReplace(self, event):
        pass

    def OnEditGotoLine(self, event):
        pass

    def OnEditGotoBrace(self, event):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.editor.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.editor.GetCharAt(caretPos - 1)
            styleBefore = self.editor.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.editor.GetCharAt(caretPos)
            styleAfter = self.editor.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.editor.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.editor.BraceBadLight(braceAtCaret)
            pass
        else:
            self.editor.BraceHighlight(braceAtCaret, braceOpposite)
            self.editor.GotoPos(braceOpposite)


    def OnEditToggleMarker(self, event):
        line = self.editor.LineFromPosition(self.editor.GetCurrentPos())
        mask = self.editor.MarkerGet(line)
        if mask == 1024:
            self.editor.MarkerDelete(line, self.BMarkerNumber)
        else:
            self.editor.MarkerAdd(line, self.BMarkerNumber)

    def OnEditNextMarker(self, evt):
        current = self.editor.GetCurrentLine()
        #print current
        skipto = self.editor.MarkerNext(current, 1024)
        #print skipto
        if skipto == current:
            skipto = self.editor.MarkerNext(current+1, 1024)

        if skipto == -1:
            #pass
            self.editor.GotoLine(0)
            tryskip = self.editor.MarkerNext(0, 1024)
            if tryskip == -1:
                pass
            else:
                self.editor.GotoLine(tryskip)
                self.editor.SetFocus()
        else:
            self.editor.GotoLine(skipto)
            self.editor.SetFocus()

    def OnProgToggleComment(self, evt):
        acteditor = self.editor
        start, end = acteditor.GetSelection()
        bl = acteditor.LineFromPosition(start)
        el = acteditor.LineFromPosition(end)

        comment = "//"

        for i in range(bl, el+1):
            lineLen = len(acteditor.GetLine(i))
            pos = acteditor.PositionFromLine(i)

            if acteditor.GetTextRange(pos, pos+2) != comment:
                acteditor.InsertText(pos, comment)
            elif acteditor.GetTextRange(pos, pos+2) == comment:
                acteditor.GotoPos(pos+2)
                acteditor.DelWordLeft()

    def loadSegFile(self, url):
        text = "int main(int argc, char *argv[])\n{\n\treturn 0;\n}"
        return text


if __name__ == '__main__':
    app = wx.PySimpleApp(False)
    frame = EditorFrame(title="editor", size=(800, 600))
    frame.Show()
    app.MainLoop()

