
import wx

import matplotlib
# We want matplotlib to use a wxPython backend
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
# from PyQt5.QtWidgets import QWidget, QVBoxLayout
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

# from enthought.traits.api import Any, Instance
# from enthought.traits.ui.wx.editor import Editor
# from enthought.traits.ui.basic_editor_factory import BasicEditorFactory
from traits.api import Any, Instance
from traitsui.wx.editor import Editor
# from traitsui.api import Editor
from traitsui.basic_editor_factory import BasicEditorFactory

class _MPLFigureEditor(Editor):

    scrollable  = True

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.set_tooltip()
        
    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        """ Create the MPL canvas. """
        # The panel lets us add additional controls.
        panel = wx.Panel(parent, -1, style=wx.CLIP_CHILDREN)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        # matplotlib commands to create a canvas
        mpl_control = FigureCanvas(panel, -1, self.value)
        sizer.Add(mpl_control, 1, wx.LEFT | wx.TOP | wx.GROW)
        toolbar = NavigationToolbar2Wx(mpl_control)
        sizer.Add(toolbar, 0, wx.EXPAND)
        self.value.canvas.SetMinSize((10,10))
        return panel

        # Creating the panel as a QWidget
        # panel = QWidget(parent)
        # layout = QVBoxLayout(panel)  # Creating a QVBoxLayout for the panel

        # # Creating the matplotlib canvas
        # mpl_control = FigureCanvas(self.value)
        # layout.addWidget(mpl_control)  # Adding the canvas to the layout

        # # Creating the matplotlib toolbar
        # toolbar = NavigationToolbar(mpl_control, panel)
        # layout.addWidget(toolbar)  # Adding the toolbar to the layout

        # # Optionally, setting a minimum size for the canvas (if required)
        # self.value.canvas.setMinimumSize(10, 10)

        # # Setting the layout for the panel
        # panel.setLayout(layout)

        # return panel

class MPLFigureEditor(BasicEditorFactory):

    klass = _MPLFigureEditor


if __name__ == "__main__":
    # Create a window to demo the editor
    from traits.api import HasTraits
    from traitsui.api import View, Item
    from numpy import sin, cos, linspace, pi

    class Test(HasTraits):

        figure = Instance(Figure, ())

        view = View(Item('figure', editor=MPLFigureEditor(),
                                show_label=False),
                        width=400,
                        height=300,
                        resizable=True)

        def __init__(self):
            super(Test, self).__init__()
            axes = self.figure.add_subplot(111)
            t = linspace(0, 2*pi, 200)
            axes.plot(sin(t)*(1+0.5*cos(11*t)), cos(t)*(1+0.5*cos(11*t)))

    Test().configure_traits()

