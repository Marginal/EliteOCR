# -*- coding: utf-8 -*-
from PyQt4.QtGui import QApplication, QDialog, QTableWidgetItem
from editorUI import Ui_Editor
import os
from os.path import join
import json
import codecs

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class EditorDialog(QDialog, Ui_Editor):
    def __init__(self, settings):
        QDialog.__init__(self)
        self.setupUi(self)
        self.settings = settings
        self.save.clicked.connect(self.saveCommodities)
        self.add_button.clicked.connect(self.addCommodity)
        self.delete_button.clicked.connect(self.deleteCommodity)

        try:
            with codecs.open(join(self.settings.storage_path, "commodities.json"), 'r', "utf-8") as h:
                commdict = json.loads(h.read())
        except:
            with codecs.open(join(self.settings.app_path, "commodities.json"), 'r', "utf-8") as h:
                commdict = json.loads(h.read())
        # WTF? Clean it!
        titles = []
        for k, v in commdict.iteritems():
            titles = commdict[k].keys()
            break
        if "rare" in titles:
            titles.remove("rare")
        if unicode(self.settings["ocr_language"]) in titles:
            titles.remove(unicode(self.settings["ocr_language"]))
            titles.insert(0,unicode(self.settings["ocr_language"]))
        
        self.table.setColumnCount(len(titles)+2)
        self.table.setHorizontalHeaderLabels(["rare", "eng"]+titles)
        totable = []
        for k, v in commdict.iteritems():
            rest = [commdict[k][i] for i in titles]
            totable.append([_translate("EliteOCR", commdict[k].get("rare", False) and "Yes" or "No", None), k] + rest)
            
        #print totable
        totable.sort(key=lambda x: x[1])
        
        self.table.setRowCount(len(totable))
        for i in xrange(len(totable)):
            for j in xrange(len(totable[i])):
                newitem = QTableWidgetItem(unicode(totable[i][j]))
                #print totable[i][j]
                self.table.setItem(i, j, newitem)
        
    def addCommodity(self):
        self.table.setRowCount(self.table.rowCount()+1)
        self.table.selectRow(self.table.rowCount()-1)

    def deleteCommodity(self):
        self.table.removeRow(self.table.currentRow())
    
    def saveCommodities(self):
        save_dict = {}
        all_rows = self.table.rowCount()
        all_cols = self.table.columnCount()
        
        for row in xrange(all_rows):
            if (not self.table.item(row,0) is None) and (not self.table.item(row,1) is None):
                save_dict[unicode(self.table.item(row,1).text())] = {}
                if self.table.item(row,0).text().toLower() == _translate("EliteOCR", "Yes", None).toLower():
                    save_dict[unicode(self.table.item(row,1).text())][unicode(self.table.horizontalHeaderItem(0).text())] = True
                for col in xrange(2,all_cols):
                    if not self.table.item(row,col) is None:
                        save_dict[unicode(self.table.item(row,1).text())][unicode(self.table.horizontalHeaderItem(col).text())] = unicode(self.table.item(row,col).text())
                    else:
                        save_dict[unicode(self.table.item(row,1).text())][unicode(self.table.horizontalHeaderItem(col).text())] = u""

        with open(join(self.settings.storage_path, "commodities.json"), 'wt') as h:
            h.write(json.dumps(save_dict, indent=2, sort_keys=True, separators=(',', ': '), ensure_ascii=False).encode('utf-8'))

        self.close()
