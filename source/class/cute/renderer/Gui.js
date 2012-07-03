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
qx.Class.define("cute.renderer.Gui",
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
  },

  properties :
  {
    title_: { init: "Unknown", inheritable : true },
    properties_: { init: null, inheritable : true },
  },

  statics :
  {
    getWidget : function(ui_definition, obj)
    {
      var properties = {};

      //TODO: setup attributes
      //for(var attr in attributes){
      //  var name = attributes[attr];
      //  var upperName = name.charAt(0).toUpperCase() + name.slice(1);
      //  var applyName = "_apply_" + upperName;
      //  var prop = {apply: applyName, event: "changed" + upperName, nullable: true};
      //  members[applyName] = getApplyMethod(name);
      //  properties[name] = prop;
      //}

      var def = {extend: cute.renderer.Gui, properties: properties};
      var clazz = qx.Class.define(name, def);

      // Generate widget and place configure it to contain itself
      var widget = new clazz();
      widget.configure(ui_definition);

      // Connect object attributes to intermediate properties
      //TODO

      // Connect intermediate properties to object attributes
      //TODO

      // Connect widget properties to intermediate properties
      //TODO: connect by timer

      return widget;
    }
  },

  members :
  {
    configure : function(ui_definition)
    {
      var info = this.processUI(parseXml(ui_definition).childNodes);
      this.setProperties_(info['properties']);
      this.add(info['widget']);
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
            console.error("*** UI format 4.0 is needed to continue processing!");
            return null;
          }

          // Continue with processing the child nodes
          return this.processElements(node.childNodes);

        } else {
          console.error("*** unexpected element '" + node.nodeName + "'");
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
            console.log("*** unknown layout type '" + layout_type + "'!");
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
          console.error("*** unexpected element '" + node.nodeName + "'");
        }

      }

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        //TODO: null handling
        return widgets[0];
      } else {
        console.info("*** migrate your GUI to use layouts instead of plain widget collections");
        // TODO: HIER
        //widget + canvas layout
        //add widgets
        //return widget
        return null;
      }
    },

    processSpacer : function(node)
    {
      //TODO: evaluate properties
      var w = new qx.ui.core.Widget().set({height: 1, width: 1});
      return {widget: w, properties: {}};
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
          console.error("*** unknown element '" + n.nodeName + "'");
        }
      }

      // Call process*Widget method
      var method = "process" + clazz + "Widget";
      var widget;
      if (method in this) {
        widget = this[method](name, properties);
      } else {
        console.error("*** widget '" + method + "' does not exist!");
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
          console.log("*** unknown layout type '" + layout_type + "'!");
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
        //TODO: null handling
        return widgets[0];
      } else {
        console.info("*** migrate your GUI to use layouts instead of plain widget collections");
        // TODO
        //widget + canvas layout
        //add widgets
        //return widget
        return null;
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
        console.error("*** TextField NoEcho not supported!");
        return null;
      } else if (echomode == "QLineEdit::PasswordEchoOnEdit") {
        console.error("*** TextField NoEcho not supported!");
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

      this._widgets[name] = widget;
      return widget;
    },

    processQComboBoxWidget : function(name, props)
    {
      var widget = new qx.ui.form.ComboBox();
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

    setWidgetInvalidMessage : function(name, message)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setInvalidMessage(message);
      } else {
        console.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetValid: function(name, flag)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setValid(flag);
      } else {
        console.error("*** cannot set valid flag for non existing widget '" + name + "'!");
      }
    },

    resetWidgetInvalidMessage : function(name)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].resetInvalidMessage();
      } else {
        console.error("*** cannot set invalid message for non existing widget '" + name + "'!");
      }
    },

    setWidgetRequiredInvalidMessage : function(name, message)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setRequiredInvalidMessage(message);
      } else {
        console.error("*** cannot set required message for non existing widget '" + name + "'!");
      }
    },

    setWidgetRequired: function(name, flag)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].setRequired(flag);
      } else {
        console.error("*** cannot set required flag for non existing widget '" + name + "'!");
      }
    },

    resetWidgetRequiredInvalidMessage : function(name)
    {
      name = name + "Edit";
      if (this._widgets[name]) {
        this._widgets[name].resetRequiredInvalidMessage();
      } else {
        console.error("*** cannot set required message for non existing widget '" + name + "'!");
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
    }

  }
});
