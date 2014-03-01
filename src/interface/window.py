import site
site.addsitedir(r"R:\Pipe_Repo\Users\Qurban\utilities")
from uiContainer import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt

site.addsitedir(r"R:\Pipe_Repo\Users\Hussain\packages")
import qtify_maya_window as qtfy

import os.path as osp
import sys
import pymel.core as pc

rootPath = osp.dirname(osp.dirname(osp.dirname(__file__)))
uiPath = osp.join(rootPath, 'ui')

Form, Base = uic.loadUiType(osp.join(uiPath, 'window.ui'))

class Window(Form, Base):
    def __init__(self, parent = qtfy.getMayaWindow()):
        super(Window, self).__init__(parent)
        self.setupUi(self)
        
        self.files = []
        
        self.browseButton.clicked.connect(self.setFiles)
        self.closeButton.clicked.connect(self.close)
        self.createButton.clicked.connect(self.create)
        
        self.progressBar.hide()
        
        self.formats = "*.tiff *.tif *.png *.jpeg *jpg *.tga *.tx" 
        
    def create(self):
        self.progressBar.show()
        qApp.processEvents()
        placeNodes = []
        lt = pc.createNode('layeredTexture')
        gamma = self.addGammaButton.isChecked()
        print gamma
        num = len(self.files)
        self.progressBar.setMaximum(num)
        self.progressBar.setMinimum(0)
        if self.files:
            x = 0
            for f in self.files:
                f = str(f)
                fileName = osp.basename(f)
                data = fileName.split('.')
                
                if len(data) < 3 or len(data) > 3:
                    pc.warning('Texture file names do not match the required format'+
                               ' "file_name.<udim>.ext"')
                    pc.delete(lt)
                    self.progressBar.hide()
                    qApp.processEvents()
                    return
                
                fileNode, placeNode = self.createFileNode(data[0], data[1])
                
                placeNode.wrapU.set(0)
                placeNode.wrapV.set(0)
                
                fileNode.defaultColor.set(0.0, 0.0, 0.0)
                fileNode.fileTextureName.set(f)
                
                pc.connectAttr(fileNode.outColor, str(lt+'.inputs[%d].color'%x))
                pc.setAttr(lt+'.inputs[%d].blendMode'%x, 8)
                x += 1
                
                placeNodes.append(placeNode)
            
                if gamma:
                    pc.Mel.eval('vray addAttributesFromGroup %s vray_file_gamma 1;'%str(fileNode))
                
                self.progressBar.setValue(x)
                qApp.processEvents()
            
            placeNodes = sorted(placeNodes)
            y = 0
            while True:
                for i in range(10):
                    node = placeNodes.pop(0) 
                    node.translateFrameU.set(i)
                    node.translateFrameV.set(y)
                    if not placeNodes:
                        break
                if not placeNodes:
                    break
                y += 1
            
            pc.select(lt)
            pc.mel.hyperShadePanelGraphCommand("hyperShadePanel1",
                                               "showUpAndDownstream")
        self.progressBar.hide()
    
    def createFileNode(self, name, num):
        fileNode = pc.shadingNode('file', asTexture=True, name=name+"_"+num)
        place2dTextureNode = pc.shadingNode('place2dTexture', asUtility=True,
                                            name="UDIM_"+num)
        attrs = ['.coverage', '.translateFrame', '.rotateFrame', '.mirrorU',
                 '.mirrorV', '.stagger', '.wrapU', '.wrapV', '.repeatUV',
                 '.offset', '.rotateUV', '.noiseUV', '.vertexUvOne',
                 '.vertexUvTwo', '.vertexUvThree', '.vertexCameraOne']
        for attr in attrs:
            pc.connectAttr(place2dTextureNode+attr, fileNode+attr, force=True)
        pc.connectAttr(place2dTextureNode.outUV, fileNode.uv, force=True)
        pc.connectAttr(place2dTextureNode.outUvFilterSize, fileNode.uvFilterSize, force=True)
        return fileNode, place2dTextureNode
    
    def setFileNames(self):
        self.fileNameBox.clear()
        for f in self.files:
            self.fileNameBox.appendPlainText(osp.basename(str(f)))
        if self.files:
            self.pathBox.setText(osp.dirname(str(self.files[0])))
        
    def setFiles(self):
        fls = QFileDialog.getOpenFileNames(self,
                                             "Select Files", "", self.formats)
        if fls:
            self.files[:] = fls
            self.setFileNames()