/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

 ************************************************************************ */

/* ************************************************************************

#asset(cute/*)

 ************************************************************************ */

/**
 * This is the main application class of your custom application "cute"
 */
qx.Class.define("cute.ui.Renderer",
{
  extend : qx.ui.container.Composite,

  include: [
      cute.ui.mixins.QLineEditWidget,
      cute.ui.mixins.QComboBoxWidget,
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

    // Tabstops
    this._tabstops = new Array();
  },

  properties :
  {
    title_: { init: "Unknown", inheritable : true },
    properties_: { init: null, inheritable : true },
    attributes_: { init: null, inheritable : true }
  },

  events: {
    "done": "qx.event.type.Event"
  },

  statics :
  {

    getWidget : function(cb, context, obj, ui_definition)
    {
      var properties = {};
      var members = {};

      var getApplyMethod = function(name){
        var func = function(value){
          if (this._widgets[name + "Edit"]) {
            this.setWidgetValue(name + "Edit", value);
          }
        };
        return(func);
      }

      // Check if there's an override for the definitions
      if (ui_definition) {
        context.warn("*** overriding object ui by user provided template");
        ui_definition = {'ContainerObject': ui_definition};
      } else {
        ui_definition = obj.templates;
      }

      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(attributes) {

        if(!attributes){
          this.error("RPC call failed: got no attributes");
          return;
        }

        // Setup attributes
        for(var name in attributes){
          var upperName = name.charAt(0).toUpperCase() + name.slice(1);
          var applyName = "_apply_" + upperName;
          var prop = {nullable: true, apply: applyName, event: "changed" + upperName};
          members[applyName] = getApplyMethod(name);
          properties[name] = prop;
        }
 
        // Configure widget
        var name = obj.baseType + "Object";
        var def = {extend: cute.ui.Renderer, properties: properties, members: members};
        var clazz = qx.Class.define(name, def);

        // Generate widget and place configure it to contain itself
        var widget = new clazz();
        widget._object = obj;
        widget.setAttributes_(attributes);
        widget.configure(ui_definition);

        // Connect to the object event 'propertyUpdateOnServer' to be able to act on property changes.
        // e.g. set an invalid-decorator for specific widget.
        obj.addListener("propertyUpdateOnServer", widget.actOnEvents, widget);

        cb.apply(context, [widget]);
      }, this, "dispatchObjectMethod", obj.uuid, "get_attributes", true);
    }
  },

  members :
  {

    _property_timer: null,
    _object: null,

    /* Create upate function for each widget to ensure that values are transmittet to
     * the server after a given period of time.
     */
    __timedPropertyUpdater: function(name, userInput){
      var func = function(value){
        var timer = qx.util.TimerManager.getInstance();
        userInput.addState("modified");
        if(this._property_timer[name]){
          timer.stop(this._property_timer[name]);
          this._property_timer[name] = null;
        }
        this._property_timer[name] = timer.start(function(){
          this.set(name, userInput.getValue());
          userInput.removeState("modified");
          timer.stop(this._property_timer[name]);
          this._property_timer[name] = null;
        }, null, this, null, 2000);
      }
      return func;
    },

    /* This method returns a method which directly updates the property-value for the object.
    * */
    __propertyUpdater: function(name, userInput){
      var func = function(value){
        var timer = qx.util.TimerManager.getInstance();
        if(this._property_timer[name]){
          timer.stop(this._property_timer[name]);
          this._property_timer[name] = null;
        }
        if(userInput.hasState("modified")){
          userInput.removeState("modified");
          this.set(name, userInput.getValue());
        }
      }
      return func;
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
            
            if(name + "Edit" in this._widgets){
              var widget = this._widgets[name + "Edit"];
              widget.setValid(data['success']);
              if(!data['success']){
                widget.setInvalidMessage(data['error']['message']);
              }else{
                widget.setInvalidMessage("");
              }
            }
          }; break;
      }
    },

    configure : function(ui_definition)
    {
      var container;

      var size = qx.lang.Object.getKeys(ui_definition).length;

      if (size > 1) {
         container = new qx.ui.tabview.TabView();
         this.add(container);
      }

      //TODO: order ui
      for (var i in ui_definition) {

        // Skip empty definitions
        if (!ui_definition[i]) {
          continue;
        }

        var info = this.processUI(parseXml(ui_definition[i]).childNodes);
        if (info) {
          // Take over properties of base type
          if (this.baseType == i || i == "ContainerObject") {
            this.setProperties_(info['properties']);
          }

          if (size > 1) {
            var page = new qx.ui.tabview.Page(this.tr(info['widget'].title_));
            page.setLayout(new qx.ui.layout.VBox());
            page.add(info['widget']);
            container.add(page);
          } else {
             this.add(info['widget']);
          }
        } else {
          this.info("*** no widget found for '" + i + "'");
        }
      }

      // Setup tabstop handling
      for (var i= 0; i<this._tabstops.length; i++) {
          var w = this._tabstops[i];
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
  
      // Handle type independent widget settings
      var attributes = this.getAttributes_();
      for(var name in attributes){
        var attrs = attributes[name];

        if (this._widgets[name + "Edit"]) {
          var widget = this._widgets[name + "Edit"];

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

      var okButton = new qx.ui.form.Button(this.tr("OK"), "icon/22/actions/dialog-apply.png");
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

          } else {
            this.error("*** unknown layout type '" + layout_type + "'!");
            continue;
          }

          // Inspect layout items
          for (var j=0; j<node.childNodes.length; j++) {

            var topic = node.childNodes[j];
            if (topic.nodeType == 1 && topic.nodeName == "item") {

              if (layout_type == "QGridLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt['widget'], {row: row, column: column});
                widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties']));
                widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties']));

              } else if (layout_type == "QFormLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt['widget'], {row: row, column: column});
                widget.getLayout().setColumnFlex(column, this.extractHFlex(wdgt['properties'], 1));
                widget.getLayout().setRowFlex(row, this.extractVFlex(wdgt['properties'], 1));

              } else if (layout_type == "QHBoxLayout") {
                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt['widget'], {flex: this.extractHFlex(wdgt['properties'])});
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
            }
          }

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

        } else {
          this.log("*** unknown layout type '" + layout_type + "'!");
          return null;
        }

        // Inspect layout items
        for (var j=0; j<layout.childNodes.length; j++) {

          var topic = layout.childNodes[j];
          if (topic.nodeType == 1 && topic.nodeName == "item") {

            if (layout_type == "QGridLayout") {
              var column = parseInt(topic.getAttribute("column"));
              var row = parseInt(topic.getAttribute("row"));
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt['widget'], {row: row, column: column});
              widget.getLayout().setColumnFlex(column, 1);

            } else if (layout_type == "QFormLayout") {
              var column = parseInt(topic.getAttribute("column"));
              var row = parseInt(topic.getAttribute("row"));
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt['widget'], {row: row, column: column});

            } else if (layout_type == "QHBoxLayout") {
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
      var type = this._widgets[name].classname;

      if (type == "qx.ui.form.TextField") {
        if (value) {
          this._widgets[name].setValue("" + value);
        } else {
          this._widgets[name].setValue("");
        }
      }

      else if (type == "qx.ui.form.VirtualSelectBox") {
        var values = this.getAttributes_()[name.slice(0, name.length - 4)]['values'];
        if (value && values.indexOf(value) >= 0) {
          this._widgets[name].setSelection(new qx.data.Array([value]));
        }
      }

      else if (type == "qx.ui.form.VirtualComboBox") {
        var values = this.getAttributes_()[name.slice(0, name.length - 4)]['values'];
        if (value && values.indexOf(value) >= 0) {
          this._widgets[name].setValue(value);
        }
      }

      else {
        this.error("*** no knowledge about how to handle widget of type '" + type + "'");
      }
    },

    setWidgetInvalidMessage : function(name, message)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setInvalidMessage(message);
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetValid: function(name, flag)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setValid(flag);
      } else {
        this.error("*** cannot set valid flag for non existing widget '" + name + "'!");
      }
    },

    resetWidgetInvalidMessage : function(name)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].resetInvalidMessage();
      } else {
        this.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetRequiredInvalidMessage : function(name, message)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setRequiredInvalidMessage(message);
      } else {
        this.error("*** cannot set required message for non existing widget '" + name + "'!");
      }
    },

    setWidgetRequired: function(name, flag)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setRequired(flag);
      } else {
        this.error("*** cannot set required flag for non existing widget '" + name + "'!");
      }
    },

    resetWidgetRequiredInvalidMessage : function(name)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].resetRequiredInvalidMessage();
      } else {
        this.error("*** cannot set required message for non existing widget '" + name + "'!");
      }
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
    }

  }
});
