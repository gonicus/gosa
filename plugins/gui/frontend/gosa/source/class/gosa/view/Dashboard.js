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
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/dashboard");
    this._setLayout(new qx.ui.layout.VBox());
    this.__gridLayout = new qx.ui.layout.Grid(5, 5);
    this.__columns = 6;
    this.__patchedThemes = {};

    this.addListener("appear", function() {
      if (!this.__drawn) {
        this.draw();
      }
    }, this);
    this.getChildControl("edit-mode");
    var board = this.getChildControl("board");
    board.addListener("resize", this._onGridResize, this);
    if (board.getBounds()) {
      this._onGridResize();
      this._applyDragListeners();
    } else {
      board.addListenerOnce("appear", function() {
        this._onGridResize();
        this._applyDragListeners();
      }, this);
    }

    this.addListener("longtap", function() {
      this.setEditMode(true);
    }, this);
    gosa.io.Sse.getInstance().addListener("pluginUpdate", this._onPluginUpdate, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __registry: {},
    __parts: {},
    __columns: null,
    __drawn: null,

    /**
     * Register a loaded dashboard widget for usage
     *
     * @param widgetClass {Class} Main widget class
     * @param options {Map} additional configuration options
     */
    registerWidget: function(widgetClass, options) {
      qx.core.Assert.assertTrue(qx.Interface.classImplements(widgetClass, gosa.plugins.IPlugin),
                                widgetClass+" does not implement the gosa.plugins.IPlugin interface");
      qx.core.Assert.assertString(options.displayName, "No 'displayName' property found in options");

      var entry = {
        clazz: widgetClass,
        options: options
      };

      var packageName = gosa.util.Reflection.getPackageName(widgetClass);

      var Env = qx.core.Environment;
      var sourceKey = packageName+".source";

      var sourceEnv = Env.get(sourceKey);
      if (!sourceEnv) {
        Env.add(sourceKey, "builtin");
      }

      if (sourceEnv === "part") {
        // plugin loaded from part
        delete this.__parts[packageName];
      }

      this.__registry[packageName] = entry;
    },

    getWidgetRegistry: function() {
      return this.__registry;
    },

    /**
     * Register an (unloaded) part that provides a dashboard widget
     * @param part {qx.ui.part.Part}
     */
    registerPart: function(part) {
      // generate the widget name from the part name
      var widgetName = qx.lang.String.firstUp(part.getName().replace("gosa.plugins.",""));
      qx.core.Environment.add(part.getName()+".source", "part");
      this.__parts[part.getName()] = widgetName;
    },

    getPartRegistry: function() {
      return this.__parts;
    }
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
    },

    editMode: {
      check: "Boolean",
      init: false,
      event: "changeEditMode",
      apply: "_applyEditMode"
    },

    uploadMode: {
      check: "Boolean",
      init: false,
      apply: "_applyUploadMode"
    },

    /**
     * Flag to determine modifications during editing mode
     */
    modified: {
      check: "Boolean",
      init: false,
      event: "changeModified"
    },

    selectedWidget: {
      check: "gosa.plugins.AbstractDashboardWidget",
      nullable: true,
      apply: "_applySelectedWidget"
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

    /**
     * Apply dragover/-leave listeners to the dashboard to recognize File uploads via Drag&Drop
     */
    _applyDragListeners: function() {
      var element = this.getContentElement().getDomElement();
      element.ondragexit = function() {
        this.setUploadMode(false);
      }.bind(this);

      element.ondragenter = function(ev) {
        if (ev.dataTransfer && ev.dataTransfer.items.length > 0) {
          // we have something to drop
          this.setUploadMode(true);
          ev.dataTransfer.effectAllowed = "none";
          ev.preventDefault();
        }
      }.bind(this);

      element.ondragover = function(ev) {
        ev.preventDefault();
      };

      element.ondragend = function() {
        this.setUploadMode(false);
      }.bind(this);

      element.ondrop = function(ev) {
        ev.preventDefault();
      };
    },

    // property apply
    _applyUploadMode: function(value) {
      if (value === true) {
        this.getChildControl("toolbar").exclude();
        this.getChildControl("upload-dropbox").show();
      } else {
        this.getChildControl("toolbar").show();
        this.getChildControl("upload-dropbox").exclude();
      }
    },

    // property apply
    _applyEditMode: function(value) {
      var grid = this.__gridLayout;
      var board = this.getChildControl("board");
      var row, column, widget, lr, lc;

      if (value) {
        this.getChildControl("toolbar").show();
        this.getChildControl("empty-info").exclude();
        this.getChildControl("board").addListener("tap", this._onTap, this);
        this.getChildControl("board").getChildren().forEach(function(child) {
          if (child instanceof gosa.plugins.AbstractDashboardWidget) {
            child.addListener("tap", this._onTap, this);
          }
        }, this);

        // add dropboxes to empty cells + one additional row
        for (row=1, lr = grid.getRowCount()+1; row < lr; row++) {
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
        this.getChildControl("toolbar").exclude();
        this.getChildControl("board").getChildren().forEach(function(child) {
          if (child instanceof gosa.plugins.AbstractDashboardWidget) {
            child.removeListener("tap", this._onTap, this);
          }
        }, this);
        this.getChildControl("board").removeListener("tap", this._onTap, this);
        this.setSelectedWidget(null);
        this.setModified(false);

        // remove the grid dropboxes
        for (row=1, lr = grid.getRowCount()+1; row < lr; row++) {
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
      var col, l;

      // free space
      for (col=data.props.column, l=data.props.column+oldProps.colSpan||1; col<l; col++) {
        var old = this.__gridLayout.getCellWidget(data.props.row, col);
        if (old && old !== data.widget) {
          old.destroy();
        }
      }

      if (data.widget === this.__draggedWidget) {
        this.__removeDraggedWidget();
      }

      data.widget.setLayoutProperties({row: data.props.row, column: data.props.column, colSpan: oldProps.colSpan, rowSpan: oldProps.rowSpan});

      // add placeholders on old widgets place
      var board = this.getChildControl("board");
      for (col=oldProps.column, l=oldProps.column+oldProps.colSpan||1; col<l; col++) {
        var cur = this.__gridLayout.getCellWidget(oldProps.row, col);
        if (!cur) {
          board.add(new gosa.ui.core.GridCellDropbox(), {
            row    : oldProps.row,
            column : col
          });
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

    /**
     * Recalculate grid column width/row height
     */
    _onGridResize: function() {
      // var bounds = this.getChildControl("board").getBounds();
      // console.log(bounds.width);
      // var totalSpacing = (this.__columns-1) * this.__gridLayout.getSpacingX();
      // console.log(totalSpacing);
      // var columnSize = Math.floor((bounds.width - totalSpacing) / this.__columns);
      // console.log(columnSize);
      // // apply size to columns
      // for (var i=0, l = this.__gridLayout.getColumnCount(); i < l; i++) {
      //   this.__gridLayout.setColumnWidth(i, columnSize);
      // }
    },

    _applySelectedWidget: function(value, old) {
      if (old) {
        old.removeState("selected");
      }
      if (value) {
        value.addState("selected");
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

        case "header":
          control = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          this._addAt(control, 0);
          break;

        case "edit-mode":
          control = new qx.ui.form.Button(null, "@Ligature/gear");
          control.setZIndex(1000);
          this.getChildControl("header").add(control, {top: 0, right: 0});
          control.addListener("execute", function() {
            this.toggleEditMode();
          }, this);
          break;

        case "toolbar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(5, "center"));
          control.exclude();
          this.__fillToolbar(control);
          this.getChildControl("header").add(control, {edge: 0});
          break;

        case "upload-dropbox":
          control = new qx.ui.container.Composite(new qx.ui.layout.Atom().set({center: true}));
          var dropBox = new qx.ui.basic.Atom(this.tr("Drop file here to add it to the available widgets."), "@Ligature/upload/64");
          dropBox.addListener("appear", this.__setUploadTarget, this);
          control.add(dropBox);
          control.exclude();
          this.getChildControl("header").add(control, {edge: 0});
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

      gosa.io.Rpc.getInstance().cA("registerUploadPath", "widgets")
      .then(function(result) {
        var path = result[1];
        var uploader = new gosa.util.UploadMgr(uploadButton, path);
      }, this);
      menu.add(uploadButton);
      menu.add(new qx.ui.menu.Separator());

      var registry = gosa.view.Dashboard.getWidgetRegistry();
      Object.getOwnPropertyNames(registry).forEach(function(name) {
        var entry = registry[name];
        var button = new qx.ui.menu.Button(entry.options.displayName, entry.options.icon);
        button.setAppearance("icon-menu-button");
        button.setUserData("widget", name);
        menu.add(button);
        button.addListener("execute", this._createWidget, this);
      }, this);

      // add the unloaded parts (loaded parts are already in the registry
      var parts = gosa.view.Dashboard.getPartRegistry();
      Object.getOwnPropertyNames(parts).forEach(function(name) {
        var displayName = parts[name];
        var button = new qx.ui.menu.Button(displayName);
        button.setUserData("part", name);
        menu.add(button);
        button.addListener("execute", this._loadPart, this);
      }, this);

      // add the uploaded widgets which can be downloaded from the backend
      gosa.io.Rpc.getInstance().cA("getDashboardWidgets")
      .then(function(widgets) {
        widgets.forEach(function(widget) {
          if (!gosa.view.Dashboard.getWidgetRegistry()[widget.provides.namespace]) {
            var displayName = widget.info.name;
            var button = new qx.ui.menu.Button(displayName);
            button.setUserData("namespace", widget.provides.namespace);
            menu.add(button);
            button.addListener("execute", this._loadFromBackend, this);
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
        this.getChildControl("board").removeAll();
        this.setModified(true);
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

    __setUploadTarget: function(ev) {
      var element = ev.getTarget().getContentElement().getDomElement();
      element.ondrop = function(e) {
        gosa.util.DragDropHelper.getInstance().onHtml5Drop.call(gosa.util.DragDropHelper.getInstance(), e);
        element.ondragexit();
        this.setUploadMode(false);
      }.bind(this);
      element.ondragexit = function(ev) {
        if (ev) {
          ev.dataTransfer.effectAllowed = "none";
        }
        qx.bom.element.Animation.animate(element, gosa.util.AnimationSpecs.UNHIGHLIGHT_DROP_TARGET);
        return false;
      };
      element.ondragenter = function(ev) {
        ev.dataTransfer.effectAllowed = "copy";
        qx.bom.element.Animation.animate(element, gosa.util.AnimationSpecs.HIGHLIGHT_DROP_TARGET);
        return false;
      };
    },

    __deleteWidget: function(widget) {
      var layoutProps = widget.getLayoutProperties();
      widget.destroy();
      this.setModified(true);
      var board = this.getChildControl("board");
      // add spacer as replacement
      for(var col=layoutProps.column, l=col+layoutProps.colSpan||1; col < l; col++) {
        var current = this.__gridLayout.getCellWidget(layoutProps.row, col);
        if (!current) {
          board.add(new gosa.ui.core.GridCellDropbox(), {
            row    : layoutProps.row,
            column : col
          });
        }
      }

      if (this.getSelectedWidget() === widget) {
        this.setSelectedWidget(null);
      }
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
      var widgetData = gosa.view.Dashboard.getWidgetRegistry()[widgetName];
      var entry = {
        widget: widgetName
      };
      // find empty space in grid
      var widgetColspan = widgetData.options.defaultColspan||3;
      var placed = false;
      for(var row=1, l = this.__gridLayout.getRowCount(); row < l; row++) {
        for(var col=0, k = this.__gridLayout.getColumnCount(); col < k; col++) {

          if (col + widgetColspan > this.__columns) {
            // not enough space in this row
            break;
          }
          var widget = this.__gridLayout.getCellWidget(row, col);
          if (widget instanceof qx.ui.core.Spacer || widget instanceof gosa.ui.core.GridCellDropbox) {
            var spacers = [widget];
            var blocked = false;
            // check if there are only spacers or nothing in the cells this widgets needs
            for (var widgetCol=col+1, wcl=widgetCol-1+widgetColspan; widgetCol < wcl; widgetCol++) {
              var followingWidget = this.__gridLayout.getCellWidget(row, widgetCol);
              if (followingWidget instanceof qx.ui.core.Spacer || followingWidget instanceof gosa.ui.core.GridCellDropbox) {
                spacers.push(followingWidget);
              } else if (widget) {
                blocked = true;
                break;
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
      entry.layoutProperties.colSpan = widgetData.options.defaultColspan || 3;
      this.__addWidget(entry);
      this.setModified(true);
    },

    /**
     * Load a widget plugin part and create the widget afterwards
     * @param ev {Event} execute event from button
     */
    _loadPart: function(ev) {
      var button = ev.getTarget();
      var partName = button.getUserData("part");
      var part = qx.io.PartLoader.getInstance().getPart(partName);
      if (part.getReadyState() === "initialized") {
        // load part
        qx.Part.require(partName, function() {
          // part is loaded
          this._createWidget(partName);
        }, this);
      }
    },

    /**
     * Load uploaded widget from backend
     * @param ev {Event} with widgets namespace as payload
     */
    _loadFromBackend: function(ev) {
      var button = ev.getTarget();
      var namespace = button.getUserData("namespace");
      var loader = new qx.util.DynamicScriptLoader(['/gosa/uploads/widgets/'+namespace+'/'+namespace+".js"]);
      loader.addListenerOnce("ready", function() {
        this._createWidget(namespace);
      }, this);
      loader.addListener('failed',function(e){
        var data = e.getData();
        this.error("failed to load "+data.script);
      });
      loader.start();
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
      var board = this.getChildControl("board");
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
      var registry = gosa.view.Dashboard.getWidgetRegistry();
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
        var c, l, currentWidget;
        for(c=entry.layoutProperties.column, l = c + colspan; c<l; c++) {
          currentWidget = this.__gridLayout.getCellWidget(entry.layoutProperties.row, c);
          if (currentWidget instanceof qx.ui.core.Spacer || currentWidget instanceof gosa.ui.core.GridCellDropbox) {
            currentWidget.destroy();
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
      this.__dragPointerOffsetX = Math.round(bounds.width/4);
      this.__dragPointerOffsetY = Math.round(bounds.height/4);
      root.add(widget, {top: ev.getDocumentTop()-this.__dragPointerOffsetY, left: ev.getDocumentLeft()-this.__dragPointerOffsetX});

      // 2. replace the dragged widgets space with GridCellDropboxes
      for (var col=props.column, l=col + props.colSpan||1; col < l; col++) {
        board.add(new gosa.ui.core.GridCellDropbox(), {row: props.row, column: col});
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
      if (this.__draggedWidget) {
        var widget = this.__draggedWidget;
        var board = this.getChildControl("board");
        var props = this.__draggedWidgetsLayoutProperties;
        // remove the GridCellDropboxes
        for (var col=props.column, l=col + props.colSpan||1; col < l; col++) {
          var placeholder = this.__gridLayout.getCellWidget(props.row, col);
          if (placeholder instanceof gosa.ui.core.GridCellDropbox) {
            placeholder.destroy();
          }
        }
        // the dragged widget has not been moved around -> add it ti the old place
        this.__removeDraggedWidget();
        widget.setLayoutProperties(props);
      }

      this.__dragPointerOffsetX = 0;
      this.__dragPointerOffsetY = 0;
      this.__draggedWidgetsLayoutProperties = null;
    },

    __removeDraggedWidget: function() {
      if (this.__draggedWidget) {
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
