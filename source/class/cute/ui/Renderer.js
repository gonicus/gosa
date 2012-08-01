/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

 ************************************************************************ */

/* ************************************************************************

#asset(cute/*)
#asset(qx/icon/${qx.icontheme}/22/actions/dialog-ok.png)
#asset(qx/icon/${qx.icontheme}/22/actions/dialog-cancel.png)

 ************************************************************************ */

/**
 * This is the main application class of your custom application "cute"
 */
qx.Class.define("cute.ui.Renderer",
{
  extend : qx.ui.container.Composite,

  include: [
      cute.ui.mixins.QLineEditWidget,
      cute.ui.mixins.QPlainTextEditWidget,
      cute.ui.mixins.QDateEditWidget,
      cute.ui.mixins.QComboBoxWidget,
      cute.ui.mixins.QGraphicsViewWidget,
      cute.ui.mixins.QCheckBoxWidget,
      cute.ui.mixins.QListWidgetWidget,
      cute.ui.mixins.QSpinBoxWidget,
      cute.ui.mixins.QLabelWidget
    ],

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  construct : function()
  {
    // Call super class
    this.base(arguments);
    this.setLayout(new qx.ui.layout.VBox());

    // Widget store
    this._widgets = {};
    this._property_timer = {};

    // Flex map
    this._flexMap = {
      "Fixed": 0,
      "Ignored": 0,
      "Minimum": 0,
      "Maximum": 10,
      "Preferred": 1,
      "Expanding": 4,
      "MinimumExpanding": 2
    };

    // Tabstops, bindings and resources
    this._tabstops = new Array();
    this._current_tabstops = new Array();
    this._bindings = {};
    this._current_bindings = {};
    this._resources = {};
  },

  properties :
  {
    modified : {init: false, check: "Boolean", "apply": "__applyModified"},
    title_: { init: "Unknown", inheritable : true },
    icon_: { init: null, inheritable : true },
    properties_: { init: null, inheritable : true },
    attributeDefinitions_: { init: null, inheritable : true }
  },

  events: {
    "done": "qx.event.type.Event"
  },

  statics :
  {

    classes: null,

    /* A static method that returns a gui widget for the given object,
     * including all properties, tabs (extensions).
     * */
    getWidget : function(cb, context, obj)
    {
      // Initialize meta-class cache
      if(!cute.ui.Renderer.classes){
        cute.ui.Renderer.classes = {};
      }

      // Check if there's an override for the definitions
      // If not, use the objects gui templates.
      var use_cached = true;
      ui_definition = obj.templates;

      // Check if we can use a cached gui here.
      if(use_cached && obj.classname in cute.ui.Renderer.classes){
        var clazz = cute.ui.Renderer.classes[obj.classname];
      }else{

        // This method returns an apply-method for the given attribute
        // (We unfortunately require it this way, due to reference handling in loops)
        var getApplyMethod = function(name){
          var func = function(value){
            var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
            if (this._widgets[widgetName]) {
              this.setWidgetValue(widgetName, value);
            }
          };
          return(func);
        }

        // Prepare meta-class properties here.
        var properties = {};
        var members = {};

        // Prepare the property list for the meta-class we are going to create.
        // Add each remote-object-property as qooxdoo-property and add its setter-method too.
        for(var name in obj.attribute_data){
          var upperName = name.charAt(0).toUpperCase() + name.slice(1);
          var applyName = "_apply_" + upperName;
          var prop = {nullable: true, apply: applyName, event: "changed" + upperName};
          members[applyName] = getApplyMethod(name);
          properties[name] = prop;
        }

        // Finaly create the meta-class
        var name = obj.baseType + "Object";
        var def = {extend: cute.ui.Renderer, properties: properties, members: members};
        var clazz = qx.Class.define(name, def);

        // Store generated meta-class in the class-cache to speed up opening the next gui.
        if(use_cached){
          cute.ui.Renderer.classes[obj.classname] = clazz;
        }
      }

      // Create an instance of the just created meta-class, set attribute-definitions and
      // generate the gui-widget out of the ui_definitions.
      var widget = new clazz();
      widget._object = obj;
      widget.setAttributeDefinitions_(obj.attribute_data);
      widget.configure(ui_definition);

      // Connect to the object event 'propertyUpdateOnServer' to be able to act on property changes.
      // e.g. set an invalid-decorator for specific widget.
      obj.addListener("propertyUpdateOnServer", widget.actOnEvents, widget);

      cb.apply(context, [widget]);
    }
  },

  members :
  {
    _object: null,
    _tabstops: null,
    _bindings: null,
    _resources: null,
    __okBtn: null,
    __cancelBtn: null,


    /* Establish bindings between object-properties and master-widget input fields.
     * */
    processBindings: function(bindings){

      for(var widgetName in bindings){
        var propertyName = bindings[widgetName];

        // We do not have such a widget!
        if(!(widgetName in this._widgets)){
          this.error("*** found binding info for '"+widgetName+"' but no such widget was created! ***");
          continue;
        }

        var method = "process" + this._widgets[widgetName].name + "Binding";
        if (method in this) {
          try{
            this[method](widgetName, propertyName);
          }catch(e){
            this.error("*** failed to establish widget bindings for '"+ widgetName +"' ***");
          }
        } else {
          this.error("*** widget '" + method + "' does not exist!");
        }
      }
    },




    processTabStops: function(tabstops){
      console.log(tabstops);
      for (var i= 0; i< tabstops.length; i++) {
        var w = tabstops[i];
        if (i == 0) {

          // Safari needs the timeout
          // iOS and Firefox need it called immediately
          // to be on the save side we do both
          var _self = this;
          var q = w;
          setTimeout(function() {
            _self._widgets[q].focus();
          });

          this._widgets[w].focus();
        }
        if (this._widgets[w]) {
          this._widgets[w].setTabIndex(i + 1);
        }
      }
    },

    /* This method acts on events send by the remote-object which was used to create this gui-widget.
     * */
    actOnEvents: function(e){
      switch(e.getType()){

        /* This event tells us that a property-change on the server-side has finished.
         * Now check its result and set decorator for the widgets accordingly.
         * */
        case "propertyUpdateOnServer": {
            var data = e.getData();
            var name = data['property'];
            if(data['success']){
              this.resetWidgetInvalidMessage(name)
              this.setWidgetValid(name, true);
            }else{
              this.setWidgetInvalidMessage(name, data['error']['message'])
              this.setWidgetValid(name, false);
            }
          }; break;
      }
    },

    /* Configure this widget for the given ui_defintion.
     * The ui_definition is parsed and qooxdoo-object are created for
     * each found xml-tag.
     * */
    configure : function(ui_definition)
    {

      // If there are extensions or more than one gui-page 
      // available for this object, then put all pages into a tab-page.
      var container;
      var size = qx.lang.Object.getKeys(ui_definition).length;
      container = new cute.ui.tabview.TabView();
      container.setMaxWidth(800);
      this.add(container);

      // Create a list of tab-names and order them
      var exten_list = new Array(this._object.baseType);
      var tmp = qx.lang.Object.getKeys(this._object.extensionTypes);
      tmp.sort();
      exten_list = exten_list.concat(tmp);

      // Detect the theme
      var theme = "default";
      if (cute.Config.theme) {
        theme = cute.Config.theme;
      }

      // Walk through each tab
      for (var ext_key in exten_list) {
        var extension = exten_list[ext_key];

        // Skip empty definitions or disabled ones.
        if (!ui_definition[extension] || 
            (!this._object.extensionTypes[extension] && extension != this._object.baseType)) {
          continue;
        }

        // Process eacht tab of the current extension
        for (var tab=0; tab<ui_definition[extension].length; tab++) {

          // Clean-up values that were collected per-loop.
          this._current_bindings = {};
          this._current_tabstops = new Array();

          // Parse the ui definition of the object
          var ui_def = parseXml(ui_definition[extension][tab]).childNodes;

          // Find resources (e.g. image-paths) before we do anything more
          for (var q=0; q<ui_def.length; q++) {
            for (var r=0; r<ui_def[q].childNodes.length; r++) {
              if (ui_def[q].childNodes[r].nodeName == "resources") {
                var resources = ui_def[q].childNodes[r];

                for (var j=0; j<resources.childNodes.length; j++) {
                  var topic = resources.childNodes[j];
                  if (topic.nodeName != "resource") {
                    continue;
                  }
      
                  var loc = topic.getAttribute("location");
                  var files = {};
                  for (var f in topic.childNodes) {
                    var item = topic.childNodes[f];
                    if (item.nodeName == "file") {
                      files[":/" + item.firstChild.nodeValue] = "resource/clacks/" + theme + "/" + item.firstChild.nodeValue;
                    }
                  }
      
                  this._resources[loc] = files;
                }
              }
            }
          }

          var info = this.processUI(ui_def);

          if (info) {
            // Take over properties of base type
            if (this._object.baseType == extension || extension == "ContainerObject") {
              this.setProperties_(info['properties']);
            }

            var page = new qx.ui.tabview.Page(this.tr(info['widget'].title_), info['widget'].icon_);
            page.setLayout(new qx.ui.layout.VBox());
            page.add(info['widget']);

            if (extension != this._object.baseType) {
              page.setShowCloseButton(true);
              page.setUserData("type", extension);

              var closeButton = page.getButton();
              closeButton.getChildControl("close-button").setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove extension")));
              closeButton.removeListener("close", page._onButtonClose, page);
              closeButton.addListener("close", function() {
                var type = page.getUserData("type");

                this._object.retract(function(result, error) {
                  if (error) {
                    this.error(error.message);
                    alert(error.message);
                  } else {
                    //TODO: unbind unused properties
                    page.fireEvent("close");
                    this.setModified(true);
                  }
                }, this, type);
              }, this);
            }

            container.add(page);

            // Connect this master-widget with the object properties.
            this.processBindings(this._current_bindings);
            this.processTabStops(this._current_tabstops);

          } else {
            this.info("*** no widget found for '" + extension + "'");
          }
        }

      }

      // Setup tool menu
      //TODO: fill with proper values
      var toolMenu = new qx.ui.menu.Menu();
      var extendMenu = new qx.ui.menu.Menu();
      var extendButton = new qx.ui.menu.Button(this.tr("Extend"));

      toolMenu.add(extendButton);

      //TODO: fill actions - currently unknown to the server side object
      //var actionsButton = new qx.ui.menu.Button(this.tr("Actions"));
      //toolMenu.add(actionsButton);

      container.getChildControl("bar").setMenu(toolMenu);
  
      // Handle type independent widget settings
      var attribute_defs = this.getAttributeDefinitions_();
      for(var name in attribute_defs){
        var attrs = attribute_defs[name];

        var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);

        if (widgetName){
          var widget = this._widgets[widgetName];

          // Read-only?
          if (attrs['readonly'] === true || attrs['depends_on'].length > 0) {
            widget.setEnabled(false);
          }

          // Required?
          if (attrs['mandatory'] === true) {
            this.setWidgetRequired(name, true);
          }

          // Toggler
          if (qx.lang.Object.getKeys(attrs['blocked_by']).length > 0) {
            //TODO: blocked_by needs to be wired
            console.log("**** blocked_by handling for " + name);
            console.log(attrs['blocked_by']);
          }
        }
      }

      // Add button static button line for the moment
      var paneLayout = new qx.ui.layout.HBox().set({
        spacing: 4,
        alignX : "right"
      });
      var buttonPane = new qx.ui.container.Composite(paneLayout).set({
        paddingTop: 11
      });

      var okButton = new qx.ui.form.Button(this.tr("OK"), "icon/22/actions/dialog-ok.png");
      this.__okBtn = okButton;
      this.__okBtn.setEnabled(false);
      okButton.addState("default");
      buttonPane.add(okButton);

      okButton.addListener("click", function() {
        this._object.commit(function(result, error){
                if(error){
                  this.error(error.message);
                }
              }, this);
        this._object.close(function(result, error){
                if(error){
                  this.error(error.message);
                }
              }, this);
        this.fireEvent("done");
      }, this);

      var cancelButton = new qx.ui.form.Button(this.tr("Cancel"), "icon/22/actions/dialog-cancel.png");
      this.__cancelBtn = cancelButton;
      buttonPane.add(cancelButton);

      cancelButton.addListener("click", function() {
        this._object.close(function(result, error){
                if(error){
                  this.error(error.message);
                }
              }, this);
        this.fireEvent("done");
      }, this);

      this.add(buttonPane);

      return true;
    },


    /**
     * This method contains the initial application code and gets called 
     * during startup of the application
     * 
     * @lint ignoreDeprecated(alert)
     */

    processUI : function(nodes)
    {
      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var node = nodes[i];

        // Skip non elements
        if (node.nodeType !== 1) {
          continue;
        }

        // Top level UI element
        if (node.nodeName == "ui") {
          if (node.getAttribute("version") !== "4.0") {
            this.error("*** UI format 4.0 is needed to continue processing!");
            return null;
          }

          // Continue with processing the child nodes
          return this.processElements(node.childNodes);

        } else {
          this.error("*** unexpected element '" + node.nodeName + "'");
        }
      }

      return null;
    },

    processElements : function(nodes)
    {
      var widgets = new Array();

      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var node = nodes[i];

        // Skip non elements
        if (node.nodeType !== 1) {
          continue;
        }

        // Class
        if (node.nodeName == "class") {
          this.name = node.firstChild.nodeValue;
          this.debug("setting widget name to '" + this.name + "'");

        // Widget
        } else if (node.nodeName == "widget") {
          widgets.push(this.processWidget(node));

        // Spacer
        } else if (node.nodeName == "spacer") {
          widgets.push(this.processSpacer(node));

        // Layout
        } else if (node.nodeName == "layout") {
          var layout_name = node.getAttribute("name");
          var layout_type = node.getAttribute("class");
          var widget = null;
          var properties = {};

          this.debug("layout '" + layout_name + "' (" + layout_type + ")");

          if (layout_type == "QGridLayout") {
            var layout = new qx.ui.layout.Grid();
            widget = new qx.ui.container.Composite(layout);

          } else if (layout_type == "QFormLayout") {
            var layout = new qx.ui.layout.Grid();
            layout.setColumnFlex(1, 1);
            widget = new qx.ui.container.Composite(layout);

          } else if (layout_type == "QHBoxLayout") {
            var layout = new qx.ui.layout.HBox();
            widget = new qx.ui.container.Composite(layout);

          } else if (layout_type == "QVBoxLayout") {
            var layout = new qx.ui.layout.VBox();
            widget = new qx.ui.container.Composite(layout);

          } else {
            this.error("*** unknown layout type '" + layout_type + "' in processElements()!");
            continue;
          }

          // Inspect layout items
          for (var j=0; j<node.childNodes.length; j++) {

            var topic = node.childNodes[j];
            if (topic.nodeType == 1 && topic.nodeName == "item") {

              if (layout_type == "QGridLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                var colspan = parseInt(topic.getAttribute("colspan"));
                var rowspan = parseInt(topic.getAttribute("rowspan"));
                var wdgt = this.processElements(topic.childNodes);
                var pos = {row: row, column: column}
                if (colspan) {
                  pos['colSpan'] = colspan;
                }
                if (rowspan) {
                  pos['rowSpan'] = rowspan;
                }
                widget.add(wdgt['widget'], pos);
                widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties']));
                widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties']));

              } else if (layout_type == "QFormLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                var colspan = parseInt(topic.getAttribute("colspan"));
                var rowspan = parseInt(topic.getAttribute("rowspan"));

                var pos = {row: row, column: column}
                if (colspan) {
                  pos['colSpan'] = colspan;
                }
                if (rowspan) {
                  pos['rowSpan'] = rowspan;
                }

                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt['widget'], pos);
                widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties'], 1));
                widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties'], 1));

              } else if (layout_type == "QHBoxLayout") {
                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractHFlex(wdgt['properties'])});

              } else if (layout_type == "QVBoxLayout") {
                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractVFlex(wdgt['properties'])});
              }
            }

            if (topic.nodeType == 1 && topic.nodeName == "property") {
              var tmp = this.processProperty(topic);
              for (var item in tmp) {
                properties[item] = tmp[item];
              }
            }

            if (layout_type == "QGridLayout") {
              layout.setSpacing(5);

            } else if (layout_type == "QFormLayout") {
              var hs = 3;
              var vs = 3;

              if (properties['labelAlignment']) {
                var align = this.getSetProperty('labelAlignment', properties);
                var h = "center";
                var v = "middle";

                if (align.indexOf("Qt::AlignLeft") != -1) {
                  h = "left";
                }
                if (align.indexOf("Qt::AlignRight") != -1) {
                  h = "right";
                }
                if (align.indexOf("Qt::AlignTop") != -1) {
                  v = "top";
                }
                if (align.indexOf("Qt::AlignBottom") != -1) {
                  v = "bottom";
                }

                layout.setColumnAlign(0, h, v);
              } else {
                layout.setColumnAlign(0, "right", "top");
              }

              if (properties['horizontalSpacing']) {
                hs = this.getNumberProperty('horizontalSpacing', properties);
                if (hs < 0) {
                  hs = 3;
                }
              }

              if (properties['verticalSpacing']) {
                vs = this.getNumberProperty('verticalSpacing', properties);
                if (vs < 0) {
                  vs = 3;
                }
              }

              layout.setSpacingX(3 + hs);
              layout.setSpacingY(3 + vs);
            }
          }

          widgets.push({widget: widget, properties: properties});

        // Collect tabstops
        } else if (node.nodeName == "tabstops") {

          for (var j=0; j<node.childNodes.length; j++) {

            var topic = node.childNodes[j];
            if (topic.nodeType == 1 && topic.nodeName == "tabstop") {
              this._tabstops.push(topic.firstChild.nodeValue);
              this._current_tabstops.push(topic.firstChild.nodeValue);
            }
          }

        // Collect bindings
        } else if (node.nodeName == "connections") {

          for (var j=0; j<node.childNodes.length; j++) {
            var topic = node.childNodes[j];
            if (topic.nodeType != 1) {
              continue;
            }

            var sender = null;
            var slot = null;

            for (var k=0; k<topic.childNodes.length; k++) {
              if (topic.childNodes[k].nodeName == "sender") {
                sender = topic.childNodes[k].firstChild.nodeValue;
              }
              if (topic.childNodes[k].nodeName == "slot") {
                slot = topic.childNodes[k].firstChild.nodeValue;
              }
            }
            this._bindings[sender] = slot.slice(9, slot.length - 2);
            this._current_bindings[sender] = slot.slice(9, slot.length - 2);
            
          }

        // Ignore resources - they're already processed
        } else if (node.nodeName == "resources") {

        } else {
          this.error("*** unexpected element '" + node.nodeName + "'");
        }

      }

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        if (widgets[0]) {
          return widgets[0];
        } else {
          return null;
        }
      } else {
        this.info("*** migrate your GUI to use layouts instead of plain widget collections");

        var base = new qx.ui.container.Composite(new qx.ui.layout.Canvas());

        for (var i in widgets) {
          if (widgets[i]){
            // Set geometry
            var x = 0;
            var y = 0;
            var geometry = this.getGeometryProperty('geometry', widgets[i]['properties']);
            if (geometry) {
              x = geometry['x'];
              y = geometry['y'];
            }
            base.add(widgets[i]['widget'], {left: x, top: y});
          }
        }

        return {widget: base, properties: {}};
      }
    },

    processSpacer : function(node)
    {
      var w = new qx.ui.core.Widget();

      // Evaluate properties
      var properties = {};
      for (var i= 0; i<node.childNodes.length; i++) {
        var n = node.childNodes[i];
        if (n.nodeName == "property") {
          var tmp = this.processProperty(n);

          for (var item in tmp) {
            properties[item] = tmp[item];
          }
        }
      }

      // Handle size hint
      var sizeHint = this.getSizeProperty('sizeHint', properties);
      var sw = 1;
      var sh = 1;
      if (sizeHint) {
        sw = sizeHint['width'];
        sh = sizeHint['height'];
      }
      w.setWidth(sw);
      w.setHeight(sh);

      return {widget: w, properties: properties};
    },

    processWidget : function(node)
    {
      var widgets = new Array();
      var nodes = node.childNodes;

      // Extract general widget information
      var name = node.getAttribute("name");
      var clazz = node.getAttribute("class");
      var properties = {};
      var layout = null;

      this.debug("processing widget " + name);

      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var n = nodes[i];

        // Skip non elements
        if (n.nodeType !== 1) {
          continue;
        }

        // Properties
        if (n.nodeName == "property") {
          var tmp = this.processProperty(n);
          for (var item in tmp) {
            properties[item] = tmp[item];
          }

          // Widget
        } else if (n.nodeName == "widget") {
          widgets.push(this.processWidget(n));

          // Layout
        } else if (n.nodeName == "layout") {
          layout = n;

        } else {
          this.error("*** unknown element '" + n.nodeName + "'");
        }
      }

      // Call process*Widget method
      var method = "process" + clazz + "Widget";
      var widget;
      if (method in this) {
        widget = this[method](name, properties);
      } else {
        this.error("*** widget '" + method + "' does not exist!");
        return null;
      }

      // Process one level, watch out for nodes we know
      if (layout != null) {
        var layout_name = layout.getAttribute("name");
        var layout_type = layout.getAttribute("class");

        this.debug("layout '" + layout_name + "' (" + layout_type + ")");

        if (layout_type == "QGridLayout") {
          widget.setLayout(new qx.ui.layout.Grid());

        } else if (layout_type == "QFormLayout") {
          widget.setLayout(new qx.ui.layout.Grid());

        } else if (layout_type == "QHBoxLayout") {
          widget.setLayout(new qx.ui.layout.HBox());

        } else if (layout_type == "QVBoxLayout") {
          widget.setLayout(new qx.ui.layout.VBox());

        } else {
          this.log("*** unknown layout type '" + layout_type + "' in processWidget()!");
          return null;
        }

        // Inspect layout items
        for (var j=0; j<layout.childNodes.length; j++) {

          var topic = layout.childNodes[j];
          if (topic.nodeType == 1 && topic.nodeName == "item") {

            if (layout_type == "QGridLayout") {
              var column = parseInt(topic.getAttribute("column"));
              var row = parseInt(topic.getAttribute("row"));
              var colspan = parseInt(topic.getAttribute("colspan"));
              var rowspan = parseInt(topic.getAttribute("rowspan"));
              var pos = {row: row, column: column}
              if (colspan) {
                pos['colSpan'] = colspan;
              }
              if (rowspan) {
                pos['rowSpan'] = rowspan;
              }
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt['widget'], pos);
              widget.getLayout().setColumnFlex(column, 1);

            } else if (layout_type == "QFormLayout") {
              var column = parseInt(topic.getAttribute("column"));
              var row = parseInt(topic.getAttribute("row"));
              var colspan = parseInt(topic.getAttribute("colspan"));
              var rowspan = parseInt(topic.getAttribute("rowspan"));
              if (colspan) {
                pos['colSpan'] = colspan;
              }
              if (rowspan) {
                pos['rowSpan'] = rowspan;
              }
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt['widget'], pos);

            } else if (layout_type == "QHBoxLayout") {
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt['widget']);

            } else if (layout_type == "QVBoxLayout") {
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt['widget']);
            }
          }
        }
      }

      widgets.push({widget: widget, properties: properties});

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        if (widgets[0]['widget']) {
          return widgets[0];
        } else {
          return null;
        }
      } else {
        this.info("*** migrate your GUI to use layouts instead of plain widget collections");

        var base = new qx.ui.container.Composite(new qx.ui.layout.Canvas());

        for (var i in widgets) {
          if (widgets[i]){
            // Set geometry
            var x = 0;
            var y = 0;
            var geometry = this.getGeometryProperty('geometry', widgets[i]['properties']);
            if (geometry) {
              x = geometry['x'];
              y = geometry['y'];
            }
            base.add(widgets[i]['widget'], {left: x, top: y});
          }
        }

        return {widget: base, properties: {}};
      }
    },

    processProperty : function(node)
    {
      var res = {};

      // Transform XML tree to hash
      for (var i = 0; i<node.childNodes.length; i++) {
        if (node.childNodes[i].nodeType === 1) {
          var topic = node.childNodes[i];
          var tmp = {};

          // Move attributes
          for (var a = 0; a < topic.attributes.length; a++) {
            tmp["_" + topic.attributes[a].nodeName] = topic.attributes[a].nodeValue;
          }

          if (node.nodeName == "property") {
            if (topic.childNodes && topic.childNodes.length != 1) {
              tmp[topic.nodeName] = this.processProperty(topic);
            } else {
              tmp[topic.nodeName] = topic.firstChild.nodeValue;
            }

            res[node.getAttribute('name')] = tmp;
          } else {
            if (topic.childNodes && topic.childNodes.length != 1) {
              res[topic.nodeName] = this.processProperty(topic);
            } else {
              res[topic.nodeName] = topic.firstChild.nodeValue;
            }
          }
        }
      }

      return res;
    },

    processQWidgetWidget : function(name, props)
    {
      var widget = new qx.ui.container.Composite();
      widget.title_ = this.getStringProperty('windowTitle', props);
      widget.icon_ = this.getIconProperty('windowIcon', props);
      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;

      return widget;
    },

    processQGroupBoxWidget : function(name, props)
    {
      var title = this.getStringProperty('title', props);
      //TODO: create a group box with icons
      var widget = new qx.ui.groupbox.GroupBox(this.tr(title));
      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;

      return widget;
    },

    processCommonProperties : function(widget, props)
    {
      // Set geometry
      var geometry = this.getGeometryProperty('geometry', props);
      if (geometry) {
        widget.setWidth(geometry['width']);
        widget.setHeight(geometry['height']);
      }

      // Set tooltip
      var tooltip = this.getStringProperty('toolTip', props);
      if (tooltip != null) {
        widget.setToolTip(new qx.ui.tooltip.ToolTip(this.tr(tooltip)));
      }

      // Set ro mode
      var readonly = this.getBoolProperty('readOnly', props);
      if (readonly != null) {
        widget.setReadOnly(readonly);
      }

      // Set maximum size
      var size = this.getSizeProperty('maximumSize', props);
      if (size != null) {
        widget.setMaxWidth(size['width']);
        widget.setMaxHeight(size['height']);
      }

      // Set minimum size
      var size = this.getSizeProperty('minimumSize', props);
      if (size != null) {
        widget.setMinWidth(size['width']);
        widget.setMinHeight(size['height']);
      }
    },

    setWidgetValue : function(name, value) {
      this._widgets[name].setValue(value.copy());
    },

    setWidgetInvalidMessage : function(name, message)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setInvalidMessage(message);
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetValid: function(name, flag)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setValid(flag);
      } else {
        this.error("*** cannot set valid flag for non existing widget '" + name + "'!");
      }
    },

    resetWidgetInvalidMessage : function(name)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].resetInvalidMessage();
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetRequired: function(name, flag)
    {
      var widgetName = qx.lang.Object.getKeyFromValue(this._bindings, name);
      if (this._widgets[widgetName]) {
        this._widgets[widgetName].setRequired(flag);
      } else {
        this.error("*** cannot set required flag for non existing widget '" + name + "'!");
      }
    },

    getIconProperty : function(what, props)
    {
      if (props[what] && props[what]['iconset']['normaloff']) {
        var resource = props[what]['_resource'];

        if (this._resources[resource]) {
          return this._resources[resource][props[what]['iconset']['normaloff']];
        }
      }

      return null;
    },

    getStringProperty : function(what, props)
    {
      if (props[what] && props[what]['string']) {
        return props[what]['string'];
      }

      return null;
    },

    getBoolProperty : function(what, props)
    {
      if (props[what] && props[what]['bool']) {
        return props[what]['bool'] == "true";
      }

      return null;
    },

    getSizeProperty : function(what, props)
    {
      if (props[what] && props[what]['size']) {
        return {'height': parseInt(props[what]['size']['height']), 'width': parseInt(props[what]['size']['width'])};
      }

      return null;
    },

    getSizePolicyProperty : function(what, props)
    {
      if (props[what] && props[what]['sizepolicy']) {
        return {'horstretch': parseInt(props[what]['sizepolicy']['horstretch']), 'verstretch': parseInt(props[what]['sizepolicy']['verstretch'])};
      }

      return null;
     },

    getGeometryProperty : function(what, props)
    {
      if (props[what] && props[what]['rect']) {
        return {
          'x': parseInt(props[what]['rect']['x']),
          'y': parseInt(props[what]['rect']['y']),
          'height': parseInt(props[what]['rect']['height']),
          'width': parseInt(props[what]['rect']['width'])}
      }

      return null;
    },

    getNumberProperty : function(what, props)
    {
      if (props[what] && props[what]['number']) {
        return parseInt(props[what]['number']);
      }

      return null;
    },

    getSetProperty : function(what, props)
    {
      if (props[what] && props[what]['set']) {
        return props[what]['set'].split("|");
      }
      return null;
    },

    getEnumProperty : function(what, props)
    {
      if (props[what] && props[what]['enum']) {
        return props[what]['enum'];
      }
      return null;
    },

    extractHFlex : function(props, dflt)
    {
      if (!dflt) {
        dflt = 1;
      }

      // Take a look at the size type
      var sizeType = this.getEnumProperty("sizeType", props);
      if (sizeType) {
        dflt = this._flexMap[sizeType.replace(/QSizePolicy::/, "")];
      }

      // Take a look at the sizePolicy
      var sizePolicy = this.getSizePolicyProperty("sizePolicy", props);
      if (sizePolicy) {
        dflt = sizePolicy['horstretch'];
      }

      return dflt;
    },

    extractVFlex : function(props, dflt)
    {
      if (!dflt) {
        dflt = 1;
      }

      // Take a look at the size type
      var sizeType = this.getEnumProperty("sizeType", props);
      if (sizeType) {
        dflt = this._flexMap[sizeType.replace(/QSizePolicy::/, "")];
      }

      // Take a look at the sizePolicy
      var sizePolicy = this.getSizePolicyProperty("sizePolicy", props);
      if (sizePolicy) {
        dflt = sizePolicy['verstretch'];
      }

      return dflt;
    },

    /* Applies the modified state for this widget
     * */
    __applyModified: function(value){
      this.debug("modified: ", value);
      this.__okBtn.setEnabled(true);
    }
  }
});
