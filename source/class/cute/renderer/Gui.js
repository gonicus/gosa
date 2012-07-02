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
  extend : qx.ui.core.Widget,


  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  construct : function()
  {
    // Call super class
    this.base(arguments);

    //TODO: build factory class instead of Widget, etc. This is just a
    //      proof of concept.
  },


  members :
  {
    getWidget : function(ui_definition)
    {
      // Examine UI definition and build widget
      return this.processUI(parseXml(ui_definition).childNodes);;
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
        var node = nodes[i]

        // Skip non elements
        if (node.nodeType !== 1) {
          continue;
        }

        // Top level UI element
        if (node.nodeName == "ui") {
          if (node.getAttribute("version") !== "4.0") {
            console.error("*** UI format 4.0 is needed to continue processing!");
            return null
          }

          // Continue with processing the child nodes
          return this.processElements(node.childNodes)

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
        var node = nodes[i]

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
          widgets.push(this.processWidget(node))

        // Layout
        } else if (node.nodeName == "layout") {
          var layout_name = node.getAttribute("name");
          var layout_type = node.getAttribute("class");
          var widget = null;

          this.debug("layout '" + layout_name + "' (" + layout_type + ")");

          if (layout_type == "QGridLayout") {
            var layout = new qx.ui.layout.Grid();
            widget = new qx.ui.container.Composite(layout)

          } else if (layout_type == "QFormLayout") {
            var layout = new qx.ui.layout.Grid();
            widget = new qx.ui.container.Composite(layout)

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
                console.log("---> layout add to ", widget);
                var wdgt = this.processElements(topic.childNodes);
                widget.add(wdgt, {row: row, column: column});
		console.log("layout add <----");

              } else if (layout_type == "QFormLayout") {
                var column = parseInt(topic.getAttribute("column"));
                var row = parseInt(topic.getAttribute("row"));
                console.log("---> layout add to ", widget);
                var wdgt = this.processElements(topic.childNodes);
                console.log("---> layout adding ", wdgt);
                widget.add(wdgt, {row: row, column: column});
		console.log("layout add <----");

              }
            }
          }

          widgets.push(widget)

        } else {
          console.error("*** unexpected element '" + node.nodeName + "'");
        }

      }

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        //return {'widget': widgets[0], 'properties': null}
        return widgets[0];
      } else {
        console.info("*** migrate your GUI to use layouts instead of plain widget collections");
        // TODO: HIER
        //widget + canvas layout
        //add widgets
        //return widget
        return null
      }
    },


    processWidget : function(node)
    {
      var widgets = new Array();
      var nodes = node.childNodes

      // Extract general widget information
      var name = node.getAttribute("name")
      var clazz = node.getAttribute("class")
      var properties = new Array()
      var layout = null;

      // Process one level, watch out for nodes we know
      for (var i=0; i<nodes.length; i++) {
        var n = nodes[i]

        // Skip non elements
        if (n.nodeType !== 1) {
          continue;
        }

        // Properties
        if (n.nodeName == "property") {
          properties.push(this.processProperty(n))

        // Widget
        } else if (n.nodeName == "widget") {
          widgets.push(this.processWidget(n))

        // Layout
        } else if (n.nodeName == "layout") {
          layout = n;

        } else {
          console.error("*** unknown element '" + n.nodeName + "'");
        }
      }

      // Call process*Widget method
      var method = "process" + clazz + "Widget"
      if (method in this) {
        var widget = this[method](properties);
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
              console.log("---> layout add to ", widget);
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt, {row: row, column: column});
              console.log("layout add <----");

            } else if (layout_type == "QFormLayout") {
              var column = parseInt(topic.getAttribute("column"));
              var row = parseInt(topic.getAttribute("row"));
              console.log("---> layout add to ", widget);
              var wdgt = this.processElements(topic.childNodes);
              widget.add(wdgt, {row: row, column: column});
              console.log("layout add <----");

            }
          }
        }
      }
      
      widgets.push(widget);

      // If there is more than one widget on this level,
      // automatically return a canvas layout with these widgets.
      if (widgets.length == 1) {
        //return {'widget': widgets[0], 'properties': null}
        return widgets[0];
      } else {
        console.info("*** migrate your GUI to use layouts instead of plain widget collections");
        // TODO
        //widget + canvas layout
        //add widgets
        //return widget
        return null
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

            res[node.getAttribute('name')] = tmp
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

    processQWidgetWidget : function(props)
    {
      this.debug("-> Window");
      console.log("   Properties " + props);
      return new qx.ui.container.Composite()
    },

    processQLabelWidget : function(props)
    {
      this.debug("-> Label");
      console.log("   Properties " + props);
      return new qx.ui.basic.Label()
    },

    processQLineEditWidget : function(props)
    {
      this.debug("-> LineEdit");
      console.log("   Properties " + props);
      return new qx.ui.form.TextField()
    },

    processQComboBoxWidget : function(props)
    {
      this.debug("-> Combobox");
      console.log("   Properties " + props);
      return new qx.ui.form.ComboBox()
    }

  }
});
