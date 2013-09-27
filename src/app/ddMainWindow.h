#ifndef __ddMainWindow_h
#define __ddMainWindow_h

#include <QMainWindow>

class ddViewManager;
class ddPropertiesPanel;
class ddPythonManager;
class QTreeWidget;
class QTextEdit;
class QDockWidget;

class ddMainWindow : public QMainWindow
{
    Q_OBJECT

public:

  ddMainWindow();
  virtual ~ddMainWindow();

  ddViewManager* viewManager() const;
  ddPropertiesPanel* propertiesPanel() const;
  QTreeWidget* objectTree() const;
  QToolBar* toolBar() const;
  QTextEdit* outputConsole() const;

  void addWidgetToViewMenu(QWidget* widget);

  void setPythonManager(ddPythonManager* pythonManager);

signals:

  void resetCamera();
  void toggleStereoRender();
  void toggleCameraTerrainMode();


protected slots:

  void startup();
  void toggleOutputConsoleVisibility();

protected:

  void handleCommandLineArgs();
  void setupPython();
  void setupViewMenu();

  class ddInternal;
  ddInternal* Internal;

  Q_DISABLE_COPY(ddMainWindow);
};

#endif