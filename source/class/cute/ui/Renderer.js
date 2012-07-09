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

        },

  properties :
  {
    title_: { init: "Unknown", inheritable : true },
    properties_: { init: null, inheritable : true },
    attributes_: { init: null, inheritable : true }
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

      //TODO: ui definitions need to be loaded just with the obj
      //      information. Development relies on passed ones.
      if (!ui_definition) {
        this.error("*** development class needs an external ui definition");
        cb.apply(context, [null]);
      }

      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(attributes) {

        // Setup attributes
        for(var name in attributes){
          var upperName = name.charAt(0).toUpperCase() + name.slice(1);
          var applyName = "_apply_" + upperName;
          var prop = {nullable: true, apply: applyName, event: "changed" + upperName};
          members[applyName] = getApplyMethod(name);
          properties[name] = prop;
        }
 
        //TODO: What name do we use later? The tab name?
        var name = "ContainerWidget"; 
        var def = {extend: cute.ui.Renderer, properties: properties, members: members};
        var clazz = qx.Class.define(name, def);

        // Generate widget and place configure it to contain itself
        var widget = new clazz();
        widget.setAttributes_(attributes);
        widget.configure(ui_definition);

        // Initialize widgets depending on type
        //TODO

        // Connect object attributes to intermediate properties
        for(var id in attributes){
          var name = attributes[id];
          obj.bind(name, widget, name);

          if(name + "Edit" in widget._widgets){
            var userInput = widget._widgets[name + "Edit"];
            if(userInput instanceof qx.ui.form.AbstractField){
              widget._widgets[name + "Edit"].addListener("input", function(){

                console.log(this.getValue());
                console.log("asdf");
              }, widget._widgets[name + "Edit"]);
            }
          }
        }
 

        // Connect intermediate properties to object attributes
        //TODO
  
        // Connect widget properties to intermediate properties / timer
        //TODO
  
        // Connect validator to properties
        //TODO
  
        // Test
        //widget.setWidgetInvalidMessage("sn", "Please enter a valid surname!");
        //widget.setWidgetValid("sn", false);
  
        cb.apply(context, [widget]);
      }, this, "dispatchObjectMethod", obj.uuid, "get_attributes", true);
    }
  },

    members :
  {
    configure : function(ui_definition)
    {
      var info = this.processUI(parseXml(ui_definition).childNodes);
      if (info) {
        this.setProperties_(info['properties']);
        this.add(info['widget']);
      } else {
        this.debug("Error: no widget found");
        return false;
      }
  
      // Handle type independen widget settings
//      var attributes = this.getAttributes_();
//      for(var name in attributes){
//        var attrs = attributes[name];
//
//        if (this._widgets[name + "Edit"]) {
//          var widget = this._widgets;
//
//          console.log("+++++++");
//          console.log(name);
//          console.log(attrs);
//
//          // Read-only?
//          if (attrs['readonly'] || attrs['depends_on'].length > 0) {
//            widget.setReadOnly(true);
//          }
//
//          // Required?
//          if (attrs['mandatory']) {
//            widget.setWidgetRequired(name, true);
//          }
//
//          // Toggler
//          //TODO: blocked_by needs to be wired
//        }
//      }


      //TODO: handle these in widget setup
      //'case_sensitive'
      //'unique'
      //'mandatory'
      //'depends_on'
      //'blocked_by'
      //'default'
      //'readonly'
      //'values'
      //'multivalue'
      //'type'

      return true;
    },

    //wire : function(name)
    //{
    //  name = name + "Edit"

    //  if (this._widgets[name]) {
    //    //console.log("----");
    //    //console.log(name);
    //    //TODO: depends on widget type
    //    //this.bind(name, this._widgets[name], "value");
    //  }
    //},

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
      this.setTitle_(this.getStringProperty('windowTitle', props));

      var widget = new qx.ui.container.Composite();
      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;

      return widget;
    },

    processQLabelWidget : function(name, props)
    {
      var label = new qx.ui.basic.Label(this.getStringProperty('text', props));

      // Set tooltip
      if (this.getStringProperty('toolTip', props)) {
        label.setToolTip(new qx.ui.tooltip.ToolTip(this.getStringProperty('toolTip', props)));
      }

      this.processCommonProperties(label, props);

      this._widgets[name] = label;
      return label;
    },

    processQLineEditWidget : function(name, props)
    {
      var widget;

      // Set echo mode
      var echomode = this.getEnumProperty('echoMode', props);
      if (echomode == "QLineEdit::Password") {
        widget = new qx.ui.form.PasswordField();
      } else if (echomode == "QLineEdit::NoEcho") {
        this.error("*** TextField NoEcho not supported!");
        return null;
      } else if (echomode == "QLineEdit::PasswordEchoOnEdit") {
        this.error("*** TextField NoEcho not supported!");
        return null;
      } else {
        widget = new qx.ui.form.TextField();
      }

      // Set placeholder
      var placeholder = this.getStringProperty('placeholderText', props);
      if (placeholder != null) {
        widget.setPlaceholder(placeholder);
      }

      // Set max length
      var ml = this.getNumberProperty('maxLength', props);
      if (ml != null) {
        widget.setMaxLength(ml);
      }

      this.processCommonProperties(widget, props);

      console.log(name + " <<<");
      this._widgets[name] = widget;
      return widget;
    },

    processQComboBoxWidget : function(name, props)
    {
      var widget;
      var editable = this.getBoolProperty('editable', props);

      if (editable) {
        widget = new qx.ui.form.VirtualComboBox();
      } else {
        widget = new qx.ui.form.VirtualSelectBox();
      }

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
        widget.setToolTip(new qx.ui.tooltip.ToolTip(tooltip));
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
