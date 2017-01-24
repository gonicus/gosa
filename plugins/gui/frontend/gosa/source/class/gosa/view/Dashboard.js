/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Customizable Dashboard view
 * 
 */
qx.Class.define("gosa.view.Dashboard", {
  extend : qx.ui.tabview.Page,
  include: [gosa.upload.MDragUpload, gosa.ui.MEditableView],
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/dashboard");
    this._setLayout(new qx.ui.layout.VBox());
    this.__gridLayout = new qx.ui.layout.Grid(5, 5);
    this.__columns = 6;
    this.__rows = 12;
    this.__patchedThemes = {};

    this.addListener("appear", function() {
      if (!this.__drawn) {
        this.draw();
      }
    }, this);

    gosa.io.Sse.getInstance().addListener("pluginUpdate", this._onPluginUpdate, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-tabview-page-dashboard"
    },

    columns : {
      check: "Number",
      init: 2
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __gridLayout : null,
    __settings: null,
    __patchedThemes : null,
    __toolbarButtons: null,
    _createMenu : null,
    __draggedWidget: null,
    __dragPointerOffsetX: null,
    __dragPointerOffsetY: null,
    __draggedWidgetsLayoutProperties: null,
    __columns: null,
    __rows: null,

    // property apply
    _applyEditMode: function(value) {
      var grid = this.__gridLayout;
      var board = this.getChildControl("board");
      var row, column, widget, lr, lc;

      if (value) {
        this.getChildControl("empty-info").exclude();
        this.getChildControl("board").addListener("tap", this._onTap, this);
        this.getChildControl("board").getChildren().forEach(function(child) {
          if (child instanceof gosa.plugins.AbstractDashboardWidget) {
            child.addListener("tap", this._onTap, this);
          }
        }, this);

        var rowHeight = 60;
        // add dropboxes to empty cells + one additional row
        for (row=1, lr = this.__rows; row < lr; row++) {
          grid.setRowHeight(row, rowHeight);
          grid.setRowMinHeight(row, rowHeight);
          grid.setRowMaxHeight(row, rowHeight);
          for (column=0, lc = grid.getColumnCount(); column < lc; column++) {
            widget = grid.getCellWidget(row, column);
            if (widget instanceof qx.ui.core.Spacer) {
              widget.destroy();
              widget = null;
            }
            if (!widget) {
              board.add(new gosa.ui.core.GridCellDropbox(), {row: row, column: column});
            }
          }
        }
        qx.event.message.Bus.subscribe("gosa.dashboard.drop", this._onMove, this);
      } else {
        this.getChildControl("board").getChildren().forEach(function(child) {
          if (child instanceof gosa.plugins.AbstractDashboardWidget) {
            child.removeListener("tap", this._onTap, this);
          }
        }, this);
        this.getChildControl("board").removeListener("tap", this._onTap, this);

        // remove the grid dropboxes
        for (row=1, lr = this.__rows; row < lr; row++) {
          for (column=0, lc = grid.getColumnCount(); column < lc; column++) {
            widget = grid.getCellWidget(row, column);
            if (widget instanceof gosa.ui.core.GridCellDropbox) {
              widget.destroy();
            }
          }
        }
        qx.event.message.Bus.unsubscribe("gosa.dashboard.drop", this._onMove, this);
      }
    },

    _onMove: function(ev) {
      var data = ev.getData();
      var oldProps = qx.lang.Object.clone(data.widget.getLayoutProperties());
      var col, l, row, lr;

      // free space
      for (row=data.props.row, lr=row + oldProps.rowSpan||1; row < lr; row++) {
        for (col = data.props.column, l = col + oldProps.colSpan || 1; col < l; col++) {
          var old = this.__gridLayout.getCellWidget(row, col);
          if (old && old !== data.widget) {
            old.destroy();
          }
        }
      }

      if (data.widget === this.__draggedWidget) {
        this.__removeDraggedWidget();
      }

      data.widget.setLayoutProperties({row: data.props.row, column: data.props.column, colSpan: oldProps.colSpan, rowSpan: oldProps.rowSpan});

      // add placeholders on old widgets place
      var board = this.getChildControl("board");
      for (row=oldProps.row, lr=row + oldProps.rowSpan||1; row < lr; row++) {
        for (col = oldProps.column, l = oldProps.column + oldProps.colSpan || 1; col < l; col++) {
          var cur = this.__gridLayout.getCellWidget(row, col);
          if (!cur) {
            board.add(new gosa.ui.core.GridCellDropbox(), {
              row    : oldProps.row,
              column : col
            });
          }
        }
      }
      this.setModified(true);
    },

    _onTap: function(ev) {
      if (ev.getCurrentTarget() instanceof gosa.plugins.AbstractDashboardWidget) {
        this.setSelectedWidget(ev.getCurrentTarget());
        ev.stopPropagation();
      } else {
        this.setSelectedWidget(null);
      }
    },

    _applySelectedWidget: function(value) {
      if (value) {
        this.__toolbarButtons['delete'].setEnabled(true);
        this.__toolbarButtons['edit'].setEnabled(true);
      } else {
        this.__toolbarButtons['delete'].setEnabled(false);
        this.__toolbarButtons['edit'].setEnabled(false);
      }
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "upload-dropbox":
          control = new qx.ui.container.Composite(new qx.ui.layout.Atom().set({center: true}));
          var dropBox = new qx.ui.basic.Atom(this.tr("Drop file here to add it to the available widgets."), "@Ligature/upload/128");
          dropBox.set({
            allowGrowY: false
          });
          control.addListener("appear", function() {
            var element = control.getContentElement().getDomElement();
            element.ondrop = function(e) {
              gosa.util.DragDropHelper.getInstance().onHtml5Drop.call(gosa.util.DragDropHelper.getInstance(), e);
              this.setUploadMode(false);
              return false;
            }.bind(this);

            element.ondragover = function(ev) {
              ev.preventDefault();
            };
          }, this);
          control.add(dropBox);
          control.exclude();
          qx.core.Init.getApplication().getRoot().add(control, {edge: 0});
          break;

        case "board":
          control = new qx.ui.container.Composite(this.__gridLayout);
          this._addAt(control, 1, {flex: 1});
          break;

        case "empty-info":
          var label = new qx.ui.basic.Label(this.tr("The dashboard is empty. To add widgets please activate the edit mode by clicking the settings button in the upper right corner"));
          control = new qx.ui.container.Composite(new qx.ui.layout.Atom().set({center: true}));
          control.add(label);
          control.exclude();
          control.addListener("changeVisibility", function(ev) {
            if (ev.getData() === "visible") {
              this.getChildControl("board").exclude();
            } else {
              this.getChildControl("board").show();
            }
          }, this);
          this._addAt(control, 2, {flex: 1});
          break;

      }

      if (this._createMixinChildControlImpl && !control) {
        control = this._createMixinChildControlImpl(id);
      }

      return control || this.base(arguments, id);
    },

    /**
     * Add buttons to the toolbar for the editing mode
     * @param toolbar {qx.ui.container.Composite} the toolbar
     */
    __fillToolbar: function(toolbar) {
      this.__toolbarButtons = {};

      // widget creation menu
      var menu = this._createMenu = new qx.ui.menu.Menu();
      var uploadButton = new com.zenesis.qx.upload.UploadMenuButton(this.tr("Upload"), "@Ligature/upload");
      uploadButton.setAppearance("icon-menu-button");

      gosa.io.Rpc.getInstance().cA("registerUploadPath", "widget")
      .then(function(result) {
        var path = result[1];
        new gosa.util.UploadMgr(uploadButton, path);
      }, this);
      menu.add(uploadButton);
      menu.add(new qx.ui.menu.Separator());

      var registry = gosa.data.DashboardController.getWidgetRegistry();
      Object.getOwnPropertyNames(registry).forEach(function(name) {
        var entry = registry[name];
        var button = new qx.ui.menu.Button(entry.options.displayName, entry.options.icon);
        button.setAppearance("icon-menu-button");
        button.setUserData("widget", name);
        menu.add(button);
        button.addListener("execute", this._createWidget, this);
      }, this);

      // add the unloaded parts (loaded parts are already in the registry
      var parts = gosa.data.DashboardController.getPartRegistry();
      Object.getOwnPropertyNames(parts).forEach(function(name) {
        var displayName = parts[name];
        var button = new qx.ui.menu.Button(displayName);
        button.setUserData("part", name);
        menu.add(button);
        button.addListener("execute", function() {
          gosa.data.DashboardController.getInstance().loadFromPart(name).then(this._createWidget, this);
        }, this);
      }, this);

      // add the uploaded widgets which can be downloaded from the backend
      gosa.io.Rpc.getInstance().cA("getDashboardWidgets")
      .then(function(widgets) {
        widgets.forEach(function(widget) {
          if (!gosa.data.DashboardController.getWidgetRegistry()[widget.provides.namespace]) {
            var displayName = widget.info.name;
            var button = new qx.ui.menu.Button(displayName);
            button.setUserData("namespace", widget.provides.namespace);
            menu.add(button);
            button.addListener("execute", function() {
              gosa.data.DashboardController.getInstance().loadFromBackend(widget.provides.namespace).then(this._createWidget, this);
            }, this);
          }
        }, this);
      }, this);

      // add button
      var widget = new qx.ui.form.MenuButton(this.tr("Add"), "@Ligature/plus", menu);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("appear", this.__setUploadTarget, this);
      gosa.util.DragDropHelper.getInstance().addListener("loaded", this._onExternalLoad, this);
      toolbar.add(widget);
      this.__toolbarButtons["add"] = widget;

      // edit button
      widget = new qx.ui.form.Button(this.tr("Edit"), "@Ligature/gear");
      widget.setDroppable(true);
      widget.setEnabled(false);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("tap", function() {
        if (this.getSelectedWidget()) {
          // open edit dialog
          var dialog = new gosa.ui.dialogs.EditDashboardWidget(this.getSelectedWidget());
          dialog.addListenerOnce("modified", function() {
            this.setModified(true);
          }, this);
          dialog.open();
        }
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["edit"] = widget;

      // delete button
      widget = new qx.ui.form.Button(this.tr("Delete"), "@Ligature/trash");
      widget.setDroppable(true);
      widget.setEnabled(false);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("tap", function() {
        if (this.getSelectedWidget()) {
          this.__deleteWidget(this.getSelectedWidget());
        }
      }, this);
      widget.addListener("drop", function(ev) {
        this.__deleteWidget(ev.getRelatedTarget());
        this.__draggedWidget = null;
      }, this);
      widget.addListener("dragover", function(ev) {
        qx.bom.element.Animation.animate(ev.getTarget().getContentElement().getDomElement(), gosa.util.AnimationSpecs.HIGHLIGHT_DROP_TARGET);
      }, this);
      widget.addListener("dragleave", function(ev) {
        qx.bom.element.Animation.animate(ev.getTarget().getContentElement().getDomElement(), gosa.util.AnimationSpecs.UNHIGHLIGHT_DROP_TARGET);
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["delete"] = widget;


      // clear dashboard
      widget = new qx.ui.form.Button(this.tr("Clear"), "@Ligature/clear");
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        var changed = false;
        var rows = this.__gridLayout.getRowCount();
        var columns = this.__gridLayout.getColumnCount();
        for (var row=1; row < rows; row++) {
          for (var col=0; col < columns; col++) {
            var widget = this.__gridLayout.getCellWidget(row, col);
            if (widget && !(widget instanceof gosa.ui.core.GridCellDropbox)) {
              this.__deleteWidget(widget);
              changed = true;
            }
          }
        }
        this.setModified(changed);
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["clear"] = widget;

      // abort editing
      widget = new qx.ui.form.Button(this.tr("Abort"), "@Ligature/undo");
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        this.setEditMode(false);
        this.refresh();
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["cancel"] = widget;

      // finish editing
      widget = new qx.ui.form.Button(this.tr("Save"), "@Ligature/check");
      widget.setEnabled(this.isModified());
      this.addListener("changeModified", function(ev) {
        this.__toolbarButtons['save'].setEnabled(ev.getData() === true);
      }, this);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        this.setEditMode(false);
        this.save();
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["save"] = widget;
    },

    __setUploadTarget: function() {
      var highlightElement = null;
      var element = null;
      if (!(arguments[0] instanceof qx.event.type.Event)) {
        highlightElement = arguments[0].getContentElement().getDomElement();
        element = arguments[1].getTarget().getContentElement().getDomElement();
      } else {
        element = arguments[0].getTarget().getContentElement().getDomElement();
        highlightElement = element;
      }

      element.ondrop = function(e) {
        gosa.util.DragDropHelper.getInstance().onHtml5Drop.call(gosa.util.DragDropHelper.getInstance(), e);
        highlightElement.ondragexit();
        this.setUploadMode(false);
        return false;
      }.bind(this);

      element.ondragover = function(ev) {
        ev.preventDefault();
      };

      highlightElement.ondragexit = function() {
        qx.bom.element.Animation.animate(highlightElement, gosa.util.AnimationSpecs.UNHIGHLIGHT_DROP_TARGET);
        return false;
      };
      highlightElement.ondragenter = function() {
        qx.bom.element.Animation.animate(highlightElement, gosa.util.AnimationSpecs.HIGHLIGHT_DROP_TARGET);
        return false;
      };
    },

    __deleteWidget: function(widget) {
      var layoutProps = widget.getLayoutProperties();
      widget.destroy();
      this.setModified(true);
      var board = this.getChildControl("board");
      // add spacer as replacement
      for(var row=layoutProps.row, lr=row+layoutProps.rowSpan||1; row < lr; row++) {
        for (var col = layoutProps.column, l = col + layoutProps.colSpan || 1; col < l; col++) {
          var current = this.__gridLayout.getCellWidget(row, col);
          if (!current) {
            board.add(new gosa.ui.core.GridCellDropbox(), {
              row    : row,
              column : col
            });
          }
        }
      }

      if (this.getSelectedWidget() === widget) {
        this.setSelectedWidget(null);
      }
    },

    /**
     * Check wether this widget can be replaces, which means its either empty aor a placeholder
     * @param widget {qx.ui.core.Widget|null}
     * @return {boolean}
     */
    __isFree: function(widget) {
      return (!widget || widget instanceof qx.ui.core.Spacer || widget instanceof gosa.ui.core.GridCellDropbox);
    },

    /**
     * Add a widget to the dashboard, triggered by the 'execute' event from an entry in the 'add' menu
     */
    _createWidget: function(ev) {
      var widgetName = "";
      if (qx.lang.Type.isString(ev)) {
        widgetName = ev.toLowerCase();
      } else {
        var button = ev.getTarget();
        widgetName = button.getUserData("widget");
      }
      var widgetData = gosa.data.DashboardController.getWidgetRegistry()[widgetName];
      var entry = {
        widget: widgetName
      };
      // find empty space in grid
      var widgetColspan = widgetData.options.defaultColspan||3;
      var widgetRowspan = widgetData.options.defaultRowspan||1;
      var placed = false;
      for(var row=1, l = this.__gridLayout.getRowCount(); row < l; row++) {
        for(var col=0, k = this.__gridLayout.getColumnCount(); col < k; col++) {

          if (col + widgetColspan > this.__columns) {
            // not enough space in this row
            break;
          }
          var widget = this.__gridLayout.getCellWidget(row, col);
          if (this.__isFree(widget)) {
            var spacers = [widget];
            var blocked = false;
            // check if there are only spacers or nothing in the cells this widgets needs
            for (var widgetRow=row, wcr=widgetRow+widgetRowspan; widgetRow < wcr; widgetRow++) {
              for (var widgetCol = col, wcl = widgetCol + widgetColspan; widgetCol < wcl; widgetCol++) {
                var followingWidget = this.__gridLayout.getCellWidget(widgetRow, widgetCol);
                if (this.__isFree(followingWidget)) {
                  if (followingWidget) {
                    spacers.push(followingWidget);
                  }
                }
                else if (widget) {
                  blocked = true;
                  break;
                }
              }
            }
            if (blocked) {
              // not enough space in this row
              break;
            }
            // replace spacer
            entry.layoutProperties = widget.getLayoutProperties();
            spacers.forEach(function(w) {
              w.destroy();
            });

            // break the outer loop
            placed = true;
            break;
          }
          else if (!widget) {
            // empty cell
            entry.layoutProperties = {
              row: row,
              column: col
            };
            // break the outer loop
            placed = true;
            break;
          }
        }
        if (placed) {
          break;
        }
      }
      if (!placed) {
        // add at the end
        entry.layoutProperties = {
          row    : row,
          column : 0
        };
      }
      entry.layoutProperties.colSpan = widgetColspan;
      entry.layoutProperties.rowSpan = widgetRowspan;
      widget = this.__addWidget(entry);
      this.setModified(true);

      // check for mandatory properties, open edit dialog then
      if (widgetData.options.settings && widgetData.options.settings.mandatory && widgetData.options.settings.mandatory.length) {
        var dialog = new gosa.ui.dialogs.EditDashboardWidget(widget);
        dialog.open();
      }
    },

    /**
     * Handle 'loaded' events from {gosa.util.DragDropHelper} to add uploaded widgets
     * @param ev {qx.event.type.Data} data event with widgets package name as payload
     */
    _onExternalLoad: function(ev) {
      this._createWidget(ev.getData());
    },

    /**
     * pre-filling with spacers to have a x-col grid
     */
    __addFirstSpacerRow: function() {
      var board = this.getChildControl("board");
      for(var i=0; i<this.__columns; i++) {
        var spacer = new gosa.ui.core.GridCellDropbox();
        spacer.addState("invisible");
        board.add(spacer, {row: 0, column: i});
        this.__gridLayout.setColumnFlex(i, 1);
      }
    },

    /**
     * Loads the dashboard settings from the backend and creates it.
     */
    draw: function() {
      this.__addFirstSpacerRow();

      // load dashboard settings from backend
      gosa.io.Rpc.getInstance().cA("loadUserPreferences", "dashboard")
      .then(function(result) {
        if (result) {
          this.__settings = result;
          var pluginsToLoad = this.__extractPluginsToLoad(result);
          var partsLoaded = pluginsToLoad.parts.length === 0;
          var scriptsLoaded = pluginsToLoad.scripts.length === 0;

          var done = function() {
            if (partsLoaded && scriptsLoaded) {
              this.refresh(true);
            }
          }.bind(this);
          if (pluginsToLoad.parts.length > 0) {
            qx.Part.require(pluginsToLoad.parts, function() {
              partsLoaded = true;
              done();
            }, this);
          }
          if (pluginsToLoad.scripts.length > 0) {
            var loader = new qx.util.DynamicScriptLoader(pluginsToLoad.scripts);
            loader.addListenerOnce("ready", function() {
              scriptsLoaded = true;
              done();
            }, this);
            loader.start();
          } else {
            done();
          }
        }
        this.__drawn = true;
      }, this);
    },

    __extractPluginsToLoad: function(settings) {
      var partsToLoad = [];
      var scriptsToLoad = [];
      var loader = qx.io.PartLoader.getInstance();
      settings.forEach(function(widgetEntry) {
        if (widgetEntry.source === "part") {
          //check if part is already loaded
          var part = loader.getPart(widgetEntry.widget);
          if (part.getReadyState() === "initialized") {
            partsToLoad.push(widgetEntry.widget);
          }
        } else if (widgetEntry.source === "external") {
          scriptsToLoad.push('/gosa/uploads/widgets/'+widgetEntry.widget+"/"+widgetEntry.widget+".js");
        }
      }, this);
      return {parts: partsToLoad, scripts: scriptsToLoad};
    },

    /**
     * Refresh the dashboard. Removes all existing widgets (if there are any) and create new ones according to the current
     * configuration.
     *
     * @param skipCleanup {Boolean?} if true skip the cleanup step before re-creating
     */
    refresh: function(skipCleanup) {
      if (!skipCleanup && this.getChildControl("board").getChildren().length > 0) {
        this.getChildControl("board").removeAll();
        // re-build in next animation frame
        qx.bom.AnimationFrame.request(qx.lang.Function.curry(this.refresh, true), this);
        this.__addFirstSpacerRow();
        return;
      }
      if (this.__settings && this.__settings.length > 0) {
        this.getChildControl("empty-info").exclude();
        this.__settings.forEach(this.__addWidget, this);
      } else {
        this.getChildControl("empty-info").show();
      }
    },

    __addWidget: function(entry) {
      var registry = gosa.data.DashboardController.getWidgetRegistry();
      var widgetName = entry.widget;
      var widget;
      var board = this.getChildControl("board");
      if (widgetName === "qx.ui.core.Spacer") {
        widget = new qx.ui.core.Spacer();
        board.add(widget, entry.layoutProperties);
        return widget;
      }
      else if (!registry[widgetName]) {
        this.warn(entry.widget+" dashboard widget not registered");
      }
      else {
        var options = registry[widgetName].options;
        if (options && options['theme'] && !this.__patchedThemes[widgetName]) {
          for (var key in options['theme']) {
            if (options['theme'].hasOwnProperty(key)) {
              if (key === "meta") {
                this.debug("patching meta theme " + options['theme'][key]);
                qx.Theme.patch(gosa.theme.Theme, options['theme'][key]);
              }
              else {
                this.debug("patching theme " + options['theme'][key]);
                qx.Theme.patch(gosa.theme[qx.lang.String.firstUp(key)], options['theme'][key]);
              }
            }
          }
          this.__patchedThemes[widgetName] = true;
        }
        //noinspection JSPotentiallyInvalidConstructorUsage
        widget = new registry[widgetName].clazz();
        if (entry.settings) {
          widget.configure(entry.settings);
        }
        widget.draw();
        this.bind("editMode", widget, "editMode");
        widget.addListener("dragstart", this._onDragStart, this);
        widget.addListener("dragend", this._onDragEnd, this);
        if (this.isEditMode()) {
          widget.addListener("tap", this._onTap, this);
          this.setSelectedWidget(widget);
        }
        widget.addListener("layoutChanged", function(ev) {
          this.__toolbarButtons['save'].setEnabled((ev.getData() === true));
          if (ev.getData() === true) {
            // add placeholders to empty cells
            for (var row = 0, lr = this.__gridLayout.getRowCount(); row < lr; row++) {
              for (var col = 0, lc = this.__gridLayout.getColumnCount(); col < lc; col++) {
                var widget = this.__gridLayout.getCellWidget(row, col);
                if (!widget) {
                  board.add(new gosa.ui.core.GridCellDropbox(), {
                    row    : row,
                    column : col
                  });
                }
              }
            }
          }
        }, this);

        // remove spacers if there are any
        var colspan = entry.layoutProperties.colSpan||1;
        var rowspan = entry.layoutProperties.rowSpan||1;
        var c, l, r, lr, currentWidget;
        for(r=entry.layoutProperties.row, lr = r + rowspan; r<lr; r++) {
          for (c = entry.layoutProperties.column, l = c + colspan; c < l; c++) {
            currentWidget = this.__gridLayout.getCellWidget(r, c);
            if (currentWidget instanceof qx.ui.core.Spacer || currentWidget instanceof gosa.ui.core.GridCellDropbox) {
              currentWidget.destroy();
            }
          }
        }
        board.add(widget, entry.layoutProperties);

        if (this.isEditMode()) {
          // check last two rows it the last one is not empty we have to add another spacer line
          // if the last two rows are empty we can remove one spacer line
          var lastLine = this.__gridLayout.getRowCount() - 1;
          var empty = true;
          for (c = 0, l = this.__gridLayout.getColumnCount(); c < l; c++) {
            currentWidget = this.__gridLayout.getCellWidget(lastLine, c);
            if (!(currentWidget instanceof qx.ui.core.Spacer || currentWidget instanceof gosa.ui.core.GridCellDropbox)) {
              empty = false;
              break;
            }
          }
          if (!empty) {
            // add another line
            for (c = 0, l = this.__gridLayout.getColumnCount(); c < l; c++) {
              board.add(new gosa.ui.core.GridCellDropbox(), {
                row    : lastLine + 1,
                column : c
              });
            }
          }
          else {
            // check 2nd last row
            lastLine--;
            for (c = 0, l = this.__gridLayout.getColumnCount(); c < l; c++) {
              currentWidget = this.__gridLayout.getCellWidget(lastLine, c);
              if (!(currentWidget instanceof qx.ui.core.Spacer || currentWidget instanceof gosa.ui.core.GridCellDropbox)) {
                empty = false;
                break;
              }
            }
            if (empty === true) {
              // remove the last line
              for (c = 0, l = this.__gridLayout.getColumnCount(); c < l; c++) {
                currentWidget = this.__gridLayout.getCellWidget(lastLine + 1, c);
                currentWidget.destroy();
              }
            }
          }
        }
        return widget;
      }
    },

    _onDragStart: function(ev) {
      qx.bom.element.Animation.animate(this.__toolbarButtons['delete'].getContentElement().getDomElement(), gosa.util.AnimationSpecs.HIGHLIGHT_DROP_TARGET_BLINK);
      this.__toolbarButtons['delete'].setEnabled(true);


      var board = this.getChildControl("board");
      // 1. extract dragged widget from current layout and add it to the root canvas
      var widget = this.__draggedWidget = ev.getCurrentTarget();
      widget.setDroppable(false);
      var props = this.__draggedWidgetsLayoutProperties = qx.lang.Object.clone(widget.getLayoutProperties());
      var bounds = widget.getBounds();
      board.remove(widget);
      var root = qx.core.Init.getApplication().getRoot();
      // check if widgets width/height are set if not do that temporarily
      if (!widget.getWidth()) {
        widget.setWidth(bounds.width);
        widget.setUserData("removeWidth", true);
      }
      if (!widget.getHeight()) {
        widget.setHeight(bounds.height);
        widget.setUserData("removeHeight", true);
      }
      qx.bom.element.Animation.animate(widget.getContentElement().getDomElement(), gosa.util.AnimationSpecs.SCALE_DRAGGED_ITEM);

      // as the scaled widgets dimensions are bisected and the widget is centered in the free space
      // we must use 1/4 as offset
      this.__dragPointerOffsetX = Math.round(bounds.width/4) - 30;
      this.__dragPointerOffsetY = Math.round(bounds.height/4) - 30;
      root.add(widget, {top: ev.getDocumentTop()-this.__dragPointerOffsetY, left: ev.getDocumentLeft()-this.__dragPointerOffsetX});

      // 2. replace the dragged widgets space with GridCellDropboxes
      for (var row=props.row, lr=row + props.rowSpan||1; row < lr; row++) {
        for (var col = props.column, l = col + props.colSpan || 1; col < l; col++) {
          board.add(new gosa.ui.core.GridCellDropbox(), {
            row    : row,
            column : col
          });
        }
      }

      // 3. bind dragged widgets position to the mouse position
      widget.addListener("drag", this._onDrag, this);
    },

    _onDrag: function(ev) {
      this.__draggedWidget.setLayoutProperties({
        top: ev.getDocumentTop()-this.__dragPointerOffsetY,
        left: ev.getDocumentLeft()-this.__dragPointerOffsetX
      });
    },

    _onDragEnd: function() {
      this.__toolbarButtons['delete'].setEnabled(false);
      gosa.ui.core.GridCellDropbox.setStartBuddy(null);
      gosa.ui.core.GridCellDropbox.resetPossibleStartBuddies();
      if (this.__draggedWidget) {
        var widget = this.__draggedWidget;
        var props = this.__draggedWidgetsLayoutProperties;
        // remove the GridCellDropboxes
        for (var row=props.row, lr=row + props.rowSpan||1; row < lr; row++) {
          for (var col = props.column, l = col + props.colSpan || 1; col < l; col++) {
            var placeholder = this.__gridLayout.getCellWidget(row, col);
            if (placeholder instanceof gosa.ui.core.GridCellDropbox) {
              placeholder.destroy();
            }
          }
        }
        // the dragged widget has not been moved around -> add it to the old place
        this.__removeDraggedWidget();
        widget.setLayoutProperties(props);
      }

      this.__dragPointerOffsetX = 0;
      this.__dragPointerOffsetY = 0;
      this.__draggedWidgetsLayoutProperties = null;

    },

    __removeDraggedWidget: function() {
      if (this.__draggedWidget) {
        this.__draggedWidget.setDroppable(true);
        this.__draggedWidget.removeListener("drag", this._onDrag, this);
        if (this.__draggedWidget.getUserData("removeWidth")) {
          this.__draggedWidget.resetWidth();
          this.__draggedWidget.setUserData("removeWidth", null);
        }
        if (this.__draggedWidget.getUserData("removeHeight")) {
          this.__draggedWidget.resetHeight();
          this.__draggedWidget.setUserData("removeHeight", null);
        }
        qx.core.Init.getApplication().getRoot().remove(this.__draggedWidget);
        // cleanup canvas layout properties from dragging
        delete this.__draggedWidget.getLayoutProperties().top;
        delete this.__draggedWidget.getLayoutProperties().left;

        this.getChildControl("board").add(this.__draggedWidget);
        qx.bom.element.Animation.animate(this.__draggedWidget.getContentElement().getDomElement(), gosa.util.AnimationSpecs.UNSCALE_DRAGGED_ITEM);
        this.__draggedWidget = null;
      }
    },

    /**
     * Save the current dashboard settings to the backend
     */
    save: function() {
      // Save settings back to the user model
      if(gosa.Session.getInstance().getUser()) {
        // collect information
        var settings = [];
        this.getChildControl("board").getChildren().forEach(function(widget) {
          if (widget.getLayoutProperties().row === 0) {
            // do not save the first spacer row
            return;
          }
          if (!(widget instanceof gosa.ui.core.GridCellDropbox) && !(widget instanceof qx.ui.core.Spacer)) {
            var packageName = gosa.util.Reflection.getPackageName(widget);
            var sourceKey = packageName+".source";
            settings.push({
              widget           : packageName,
              source           : qx.core.Environment.get(sourceKey),
              layoutProperties : widget.getLayoutProperties(),
              settings         : widget.getConfiguration()
            })
          }
        }, this);
        gosa.io.Rpc.getInstance().cA("saveUserPreferences", "dashboard", settings)
        .then(function() {
          this.__toolbarButtons['save'].setEnabled(false);
          this.__settings = settings;
          this.refresh(true);
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      }
    },

    /**
     * Handle pluginUpdate events from backend, reload the dashboard widget information
     */
    _onPluginUpdate: function() {
      // delete all upload widgets buttons (they have 'namespace' userData)
      this._createMenu.getChildren().forEach(function(button) {
        if (button.getUserData("namespace")) {
          button.destroy();
        }
      }, this);

      // add the uploaded widgets which can be downloaded from the backend
      gosa.io.Rpc.getInstance().cA("getDashboardWidgets")
      .then(function(widgets) {
        widgets.forEach(function(widget) {
          var displayName = widget.info.name;
          var button = new qx.ui.menu.Button(displayName);
          button.setUserData("namespace", widget.provides.namespace);
          this._createMenu.add(button);
          button.addListener("execute", this._loadFromBackend, this);
        }, this);
      }, this);

    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this.__gridLayout = null;
    Object.getOwnPropertyNames(this.__toolbarButtons).forEach(function(name) {
      this.__toolbarButtons[name].dispose();
    }, this);
    this.__toolbarButtons = null;
    gosa.io.Sse.getInstance().removeListener("pluginUpdate", this._onPluginUpdate, this);
    this._disposeObjects("_createMenu");
  },

  defer: function(statics) {
    // load available plugin-parts
    var parts = qx.io.PartLoader.getInstance().getParts();
    Object.getOwnPropertyNames(parts).forEach(function(partName) {
      if (partName.startsWith("gosa.plugins.")) {
        statics.registerPart(parts[partName]);
      }
    }, this);
  }
});
