/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
 * Container showing several tabs - all necessary for displaying forms for editing an object.
 */
qx.Class.define("gosa.ui.widgets.ObjectEdit", {

  extend: qx.ui.container.Composite,

  /**
   * @param templates {Array} List of hash maps in the shape {extension : <extension name>, template : <parsed template>}
   * filled with valid values
   */
  construct: function(templates) {
    this.base(arguments);
    qx.core.Assert.assertArray(templates);

    var base = templates[0].extension;
    this._templates = templates.sort(function(a, b) {
      if (a.extension === base) {
        return -1;
      } else if (b.extension === base) {
        return 1;
      } else {
        return a.extension.localeCompare(b.extension);
      }
    });

    this._contexts = [];
    this.__openDialogs = [];

    this.setLayout(new qx.ui.layout.VBox());
  },

  events : {

    /**
     * Fired when the widget/the window in which the window is gets closed.
     */
    "close" : "qx.event.type.Event",

    /**
     * Fired when the edited object gets closed by the backend due to an inactivity timeout
     */
    "timeoutClose": "qx.event.type.Event",

    /**
     * Fired when a context was added. Data is the context object (of type {@link gosa.engine.Context}).
     */
    "contextAdded": "qx.event.type.Data"
  },

  properties : {
    controller : {
      check : "gosa.data.controller.ObjectEdit",
      init : null,
      apply : "_applyController"
    }
  },

  members : {

    _templates : null,
    _tabView : null,
    _toolMenu : null,
    _buttonPane : null,
    _contexts : null,
    _okButton : null,
    _extendMenu : null,
    _retractMenu : null,
    _actionMenu : null,
    _extendButton : null,
    _retractButton : null,
    __openDialogs : null,
    __closingDialog : null,

    /**
     * Retrieve all contexts this widget is showing.
     *
     * @return {Array} A (maybe empty) array of {@link gosa.engine.Context} objects
     */
    getContexts : function() {
      return this._contexts;
    },

    /**
     * Removes and disposes a tab page from the tab view. It removes only the widget and nothing from the object.
     *
     * @param tabPage {qx.ui.tabview.Page}
     */
    removeTab : function(tabPage) {
      qx.core.Assert.assertNotUndefined(tabPage);
      qx.core.Assert.assertInstance(tabPage, qx.ui.tabview.Page);

      var context = this._contexts.find(function(context) {
        return context.getRootWidget() === tabPage;
      });

      this._tabView.remove(tabPage);
      tabPage.dispose();
      qx.lang.Array.remove(this._contexts, context);

      this._updateExtensionMenus();
    },

    addTab : function(templateObj) {
      var tabPage = new qx.ui.tabview.Page();
      tabPage.setAppearance("edit-tabview-page");
      tabPage.setLayout(new qx.ui.layout.Grow());

      // add a scroll container around the content
      var scroll = new qx.ui.container.Scroll();
      var desktopBounds = gosa.ui.controller.Objects.getInstance().getDesktop().getBounds();
      scroll.setMaxHeight(desktopBounds.height - 100);
      tabPage.add(scroll);
      var tabContent = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      scroll.add(tabContent);

      if (templateObj.extension !== this.getController().getBaseType()) {
        tabPage.setShowCloseButton(true);

        var closeButton = tabPage.getButton();
        closeButton.getChildControl("close-button").setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove extension")));
        closeButton.addListener("close", function() {
          this.getController().getExtensionController().removeExtension(templateObj.extension);
        }, this);
      }

      var context = new gosa.engine.Context(templateObj.template, tabContent, templateObj.extension, this.getController());
      this._contexts.push(context);
      tabPage.setUserData("context", context);
      this._tabView.add(tabPage);

      tabContent.bind("height", scroll, "height");

      // remove existing listeners on the tab page to prevent automatic closing
      var manager = qx.event.Registration.getManager(tabPage);
      manager.getListeners(tabPage, "close").forEach(function(l) {
        tabPage.removeListener("close", l.handler, l.context);
      });

      this._updateExtensionMenus();

      this.getController().addContext(context);
    },

    /**
     * Listener for when the object should get closed automatically (timeout pending).
     *
     * @param dn {String} dn of the object
     * @param minutes {Integer} Timeout until the object is automatically closed
     */
    onClosing : function(dn, minutes) {
      var closingDialog = this.__closingDialog = new gosa.ui.dialogs.ClosingObject(dn, minutes * 60);
      closingDialog.addListener("closeObject", function() {
        this.closeOpenDialogs();
        this.getController().closeObject();
        this._close();
      }, this);
      closingDialog.addListener("continue", this.getController().continueEditing, this.getController());
      closingDialog.open();
      this.addDialog(closingDialog);
    },

    closeCloseDialog : function() {
      if (this.__closingDialog) {
        this.__closingDialog.destroy();
        this.__closingDialog = null;
      }
    },

    /**
     * Closes the closing dialog if there is one.
     */
    closeOpenDialogs : function () {
      if (this.__openDialogs) {
        this.__openDialogs.forEach(function(dialog) {
          if (!dialog.isDisposed()) {
            dialog.close();
            if (!dialog.isDisposed()) {
              dialog.dispose();
            }
          }
        });
        this.__openDialogs = [];
      }
    },

    /**
     * Add an existing dialog object to have it automatically closed when the object is closed.
     */
    addDialog : function(dialog) {
      this.__openDialogs.push(dialog);
    },

    /**
     * Call when the object was closed due to inactivity.
     */
    onClosed : function() {
      this.closeOpenDialogs();
      new gosa.ui.dialogs.Info(this.tr("This object has been closed due to inactivity!")).open();
      this._getParentWindow().close();  // don't fire close event
      this.fireEvent("timeoutClose"); // fire special close event (needed to let the WindowController know whats going on)
      this.dispose();
    },

    _applyController : function(value, old) {
      if (old) {
        old.removeListener("changeModified", this._updateOkButtonEnabled, this);
        old.removeListener("changeValid", this._updateOkButtonEnabled, this);
        old.getExtensionFinder() && old.getExtensionFinder().removeListener("extensionsChanged", this._updateExtendMenu, this);
        old.dispose();
      }

      if (value) {
        value.addListener("changeModified", this._updateOkButtonEnabled, this);
        value.addListener("changeValid", this._updateOkButtonEnabled, this);
        value.getExtensionFinder().addListener("extensionsChanged", this._updateExtendMenu, this);
        this._initWidgets();
      }
    },

    _updateOkButtonEnabled : function(context) {
      var c = this.getController();
      if (context && context instanceof gosa.engine.Context) {
        this._okButton.setEnabled(c.isModified() && c.checkValidity(context));
      } else {
        this._okButton.setEnabled(c.isModified() && c.isValid());
      }
    },

    _initWidgets : function() {
      if (this._templates.length === 0) {
        this.add(new qx.ui.basic.Label(this.tr("There is currently no template defined for this kind of object. You have to add one in order to be able to create a new object")));
      } else {
        this._createTabView();
        this._templates.forEach(this.addTab, this);
        this._createToolmenu();
      }
      this._createButtons();
    },

    _createTabView : function() {
      this._tabView = new gosa.ui.tabview.TabView();
      this._tabView.getChildControl("bar").setScrollStep(150);
      this.add(this._tabView, {flex : 1});
    },

    _createToolmenu : function() {
      this._toolMenu = new qx.ui.menu.Menu();
      this._tabView.getChildControl("bar").setMenu(this._toolMenu);

      this._createActionButtons();
      this._createRetractMenu();
      this._createExtendMenu();
      this.__updateToolMenuButtonVisibility();
    },

    _createActionButtons : function() {
      var allActionEntries = {};
      var actionEntries, key;

      var command = new qx.ui.command.Command("Ctrl+M");

      // button creation
      var button = new qx.ui.menu.Button(this.tr('Move object...'), "@Ligature/move", command);
      button.setAppearance("icon-menu-button");

      // disable when modified
      this.getController().bind("modified", button, "enabled", {
        converter: function(value) {
          return !value;
        }
      });
      var actionController = new gosa.data.controller.Actions(this.getController().getObject(), this);

      // listener to open dialog
      button.addListener("execute", function() {
        var dialog = new gosa.ui.dialogs.actions.MoveObjectDialog(actionController);
        dialog.setAutoDispose(true);
        dialog.open();
      });

      allActionEntries["actionMoveObject"] = button;

      // collect action menu entries
      this._contexts.forEach(function(context) {
        actionEntries = context.getActions();
        for (var name in actionEntries) {
          if (actionEntries.hasOwnProperty(name)) {
            qx.core.Assert.assertFalse(allActionEntries.hasOwnProperty(name), "Duplicate action name: '" + name + "'");
            allActionEntries[name] = actionEntries[name];
          }
        }
      });

      // sort by name
      var sorted = [];
      for(key in allActionEntries) {
        sorted[sorted.length] = key;
      }
      sorted.sort();

      // create action menu
      var actionMenu = this._actionMenu = new qx.ui.menu.Menu();
      var actionButton = new qx.ui.menu.Button(this.tr("Action"), "@Ligature/magic", null, actionMenu);
      actionButton.setAppearance("icon-menu-button");
      this._toolMenu.add(actionButton);

      // add menu entries to widget
      sorted.forEach(function(key) {
        actionMenu.add(allActionEntries[key]);
      }, this);

      if (actionMenu.getChildren().length > 0) {
        actionButton.show();
      }
      else {
        actionButton.exclude();
      }
    },

    _createRetractMenu : function() {
      this._retractMenu = new qx.ui.menu.Menu();
      this._retractButton = new qx.ui.menu.Button(this.tr("Retract"), "@Ligature/minus", null, this._retractMenu);
      this._retractButton.setAppearance("icon-menu-button");
      this._toolMenu.add(this._retractButton);
      this._updateRetractMenu();
    },

    _createExtendMenu : function() {
      this._extendMenu = new qx.ui.menu.Menu();
      this._extendButton = new qx.ui.menu.Button(this.tr("Extend"), "@Ligature/plus", null, this._extendMenu);
      this._extendButton.setAppearance("icon-menu-button");
      this._toolMenu.add(this._extendButton);
      this._updateExtendMenu();
    },

    _updateExtensionMenus : function() {
      this._updateExtendMenu();
      this._updateRetractMenu();
    },

    _updateExtendMenu : function() {
      if (!this._extendMenu) {
        // might not be initialized yet
        return;
      }

      // cleanup menu
      var oldChildren = this._extendMenu.removeAll();
      oldChildren.forEach(function(child) {
        if (!child.isDisposed()) {
          child.dispose();
        }
      });

      // create new menu entries
      var extFinder = this.getController().getExtensionFinder();
      extFinder.getAddableExtensions().sort(this.__compareExtensionsByTranslatedName).forEach(function(ext) {

        var config = gosa.Cache.extensionConfig[ext];
        if (!config) {
          // don't show menus w/o configuration
          return;
        }

        // some buttons extensions don't have an icon
        var button;
        if (config.icon) {
          // button = new qx.ui.menu.Button(ext, gosa.Config.getImagePath(config.icon, 22));
          button = new qx.ui.menu.Button(config.title, config.icon);
          button.setAppearance("icon-menu-button");
        }
        else {
          button = new qx.ui.menu.Button(config.title);
        }

        this._extendMenu.add(button);

        button.addListener("execute", function() {
          this.getController().getExtensionController().addExtension(ext);
        }, this);

        this.__updateToolMenuButtonVisibility();
      }, this);

      // switch visibility
      if (this._extendMenu.getChildren().length > 0) {
        this._extendButton.show();
      }
      else {
        this._extendButton.exclude();
      }
    },

    _updateRetractMenu : function() {
      if (!this._retractMenu) {
        // might not be initialized yet
        return;
      }

      // cleanup menu
      var oldChildren = this._retractMenu.removeAll();
      oldChildren.forEach(function(child) {
        if (!child.isDisposed()) {
          child.dispose();
        }
      });

      // create new menu entries
      var actExts = this.getController().getActiveExtensions();
      var extFinder = this.getController().getExtensionFinder();

      // create button for each extension
      extFinder.getRetractableExtensions().sort(this.__compareExtensionsByTranslatedName).forEach(function(ext) {
        if (qx.lang.Array.contains(actExts, ext)) {
          var config = gosa.Cache.extensionConfig[ext];
          if (!config) {
            // don't show menus w/o configuration
            return;
          }

          // some buttons extensions don't have an icon
          var button;
          if (config.icon) {
            button = new qx.ui.menu.Button(config.title, config.icon);
            button.setAppearance("icon-menu-button");
          }
          else {
            button = new qx.ui.menu.Button(config.title);
          }

          this._retractMenu.add(button);

          button.addListener("execute", function() {
            this.getController().getExtensionController().removeExtension(ext);
          }, this);
        }

        this.__updateToolMenuButtonVisibility();
      }, this);

      // switch visibility
      if (this._retractMenu.getChildren().length > 0) {
        this._retractButton.show();
      }
      else {
        this._retractButton.exclude();
      }
    },

    __compareExtensionsByTranslatedName : function(extA, extB) {
      var configA = gosa.Cache.extensionConfig[extA];
      var configB = gosa.Cache.extensionConfig[extB];

      if (!configA || !configB) {
        return 0;
      }
      return configA.title < configB.title ? -1 : 1;
    },

    __updateToolMenuButtonVisibility : function() {
      if (!this._extendMenu || !this._retractMenu || !this._actionMenu) {
        return;
      }

      // show button only if any submenu has at least one entry
      if (this._retractMenu.getChildren().length
          || this._extendMenu.getChildren().length
          || this._actionMenu.getChildren().length) {
        this._tabView.getChildControl("bar").setMenu(this._toolMenu);
      }
      else {
        this._tabView.getChildControl("bar").resetMenu();
      }
    },

    _createButtons : function() {
      var paneLayout = new qx.ui.layout.HBox();
      paneLayout.set({
        spacing: 4,
        alignX : "right",
        alignY : "middle"
      });
      this._buttonPane = new qx.ui.container.Composite(paneLayout);
      this._buttonPane.setMarginTop(11);

      this.add(this._buttonPane);
      this._createOkButton();
      this._createCancelButton();
    },

    /**
     * Open a TabView page for the given context
     *
     * @param context {gosa.engine.Context}
     */
    openTab: function(context) {
      this._tabView.getSelectables(true).some(function(page) {
        if (page.getUserData("context") === context) {
          this._tabView.setSelection([page]);
          return true;
        }
      }, this);
    },

    /**
     * Closes the widget.
     */
    close : function() {
      this.closeOpenDialogs();
      this._getParentWindow().close();
      this.fireEvent("close");
    },

    _createOkButton : function() {
      var button = this._okButton = gosa.ui.base.Buttons.getOkButton();
      button.set({
        appearance : "button-primary",
        enabled : false,
        tabIndex : 30000
      });
      button.addState("default");
      this._buttonPane.add(button);

      button.addListener("execute", this._onOk, this);
    },

    _createCancelButton : function() {
      var button = gosa.ui.base.Buttons.getCancelButton();
      button.setTabIndex(30001);
      this._buttonPane.add(button);

      button.addListener("execute", this._onCancel, this);
    },

    /**
     * @return {qx.ui.window.Window | null}
     */
    _getParentWindow : function() {
      var parent = this;
      do {
        parent = parent.getLayoutParent();
        if (parent instanceof qx.ui.window.Window) {
          return parent;
        }
      } while (parent);
      return null;
    },

    _onOk : function() {
      this.getController().saveObject()
      .then(this._close, this)
      .catch(function(exc) {
        throw exc;
        // do nothing as the error has already been handled
      });
    },

    _onCancel : function() {
      if (this.getController() && this.getController().isModified()) {
        this._createConfirmDialog();
      }
      else {
        this.getController().closeObject();
        this._close();
      }
    },

    _close : function() {
      this.closeOpenDialogs();
      this._getParentWindow().close();
      this.fireEvent("close");
    },

    _createConfirmDialog : function() {
      var dialog = new gosa.ui.dialogs.Dialog(this.tr("Unsaved changes"));
      dialog.setAppearance("window-warning");
      dialog.setAutoDispose(true);
      dialog.addElement(new qx.ui.basic.Label(this.tr("There are unsaved changes. Are you sure to really abort?")));
      this.addDialog(dialog);

      var okButton = new qx.ui.form.Button(this.tr("Yes"), "@Ligature/trash");
      okButton.setAppearance("button-warning");
      okButton.addListener("execute", function() {
        dialog.close();
        if (this.getController()) {
          this.getController().closeObject();
        }
        this._close();
      }, this);
      dialog.addButton(okButton);

      var cancelButton = new qx.ui.form.Button(this.tr("No"), "@Ligature/undo");
      cancelButton.setAppearance("button-warning");
      cancelButton.addListener("execute", dialog.close, dialog);
      dialog.addButton(cancelButton);

      dialog.open();
    }
  },

  destruct : function() {
    this.resetController();
    this._templates = null;
    this.__openDialogs = null;
    qx.util.DisposeUtil.disposeArray("_contexts");
    this._disposeObjects(
      "_okButton",
      "_extendMenu",
      "_retractMenu",
      "_actionMenu",
      "_extendButton",
      "_retractButton",
      "_toolMenu",
      "_buttonPane",
      "_tabView",
      "__closingDialog"
    );
  }
});
