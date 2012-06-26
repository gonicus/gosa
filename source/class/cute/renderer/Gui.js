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
  construct : function(ui_definition)
  {
    // Call super class
    this.base(arguments);

    this.processDocument(parseXml(ui_definition).childNodes);
  },


  members :
  {
    /**
     * This method contains the initial application code and gets called 
     * during startup of the application
     * 
     * @lint ignoreDeprecated(alert)
     */
 
    processDocument : function(nodes)
    {
        // Process one level, watch out for nodes we know
        for (var i=0; i<nodes.length; i++) {
          var node = nodes[i]

          // Skip non elements
          if (node.nodeType !== 1) {
            continue;
          }
          this.debug("Element:", node.nodeName);

          // Top level UI element
          if (node.nodeName == "ui") {
            if (node.getAttribute("version") !== "4.0") {
              alert("UI format 4.0 is needed to continue processing!");
              exit();
            }

            // Continue with processing the child nodes
            this.processDocument(node.childNodes)
          }

          // Class
	  else if (node.nodeName == "class") {
            this.debug("Class '" + node.firstChild.nodeValue + "'");
	  }

          // Widget
	  else if (node.nodeName == "widget") {
            var more = this.processWidget(node)
            this.processDocument(more)
	  }

          // Layout
	  else if (node.nodeName == "layout") {
	    // -> process items
            //<layout name="gridLayout" class="QGridLayout">
            //<item column="0" row="0">
	  }

	  else {
            this.debug("*** unknown element '" + node.nodeName + "'");
	  }

       }
    },


    processWidget : function(node)
    {
      var more = new Array()
      var nodes = node.childNodes

      // Extract general widget information
      var name = node.getAttribute("name")
	var clazz = node.getAttribute("class")
	var properties = new Array()

        // Process one level, watch out for nodes we know
        for (var i=0; i<nodes.length; i++) {
          var n = nodes[i]

          // Skip non elements
          if (n.nodeType !== 1) {
            continue;
          }

          // Properties
          if (n.nodeName == "property") {
            var attr_name = n.getAttribute("name")

            if (attr_name == "geometry") {
              properties.push(this.processGeometryProperty(n))
	    } else if (attr_name == "windowTitle") {
              properties.push(this.processStringProperty(n))
	    } else {
              alert("Unknown property '" + attr_name + "'!");
              exit();
	    }

	  } else {
            more.push(n);
	  }
       }

       // Call processXXXWidget method
       var method = "process" + clazz + "Widget"
       if (method in this) {
         this[method](properties);
       } else {
	 this.debug("*** widget '" + method + "' does not exist!");
       }

       return more;
    },

    processGeometryProperty : function(node)
    {
      var res = {}
      // TODO: node 2 hash
      res[node.getAttribute("name")] = null
      return res
    },

    processStringProperty : function(node)
    {
      var res = {}
      res[node.getAttribute("name")] = node.childNodes[1].firstChild.nodeValue;
      this.debug("  " + node.getAttribute("name") + " = " + node.childNodes[1].firstChild.nodeValue);
      return res;
    },

    processQWidgetWidget : function(props)
    {
      this.debug("-> Window");
    },

    processQLabelWidget : function(props)
    {
      this.debug("-> Label");
    },

    processQLineEditWidget : function(props)
    {
      this.debug("-> LineEdit");
    }

  }
});
