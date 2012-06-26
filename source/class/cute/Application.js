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
qx.Class.define("cute.Application",
{
  extend : qx.application.Standalone,



  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
    /**
     * This method contains the initial application code and gets called 
     * during startup of the application
     * 
     * @lint ignoreDeprecated(alert)
     */
    main : function()
    {
      // Call super class
      this.base(arguments);

      // Enable logging in debug variant
      if (qx.core.Environment.get("qx.debug"))
      {
        // support native logging capabilities, e.g. Firebug for Firefox
        qx.log.appender.Native;
        // support additional cross-browser console. Press F7 to toggle visibility
        qx.log.appender.Console;
      }

      /*
      -------------------------------------------------------------------------
        Below is your actual application code...
      -------------------------------------------------------------------------
      */

      // Create a button
      var process = new qx.ui.form.Button("Analyze");
      var text = new qx.ui.form.TextArea();
      text.setWrap(false);

      // Document is the application root
      var doc = this.getRoot();

      // Add button to document at fixed coordinates
      doc.add(text, {left: 10, top: 10, right: 10, bottom: 150});
      doc.add(process, {left: 10, bottom: 100});

      // Load data
      var req = new qx.bom.request.Xhr();
      req.onload = function() { text.setValue(req.responseText); }
      req.open("GET", "test.ui");
      req.send();

      // Add an event listener and process known elements
      process.addListener("execute", function(e) {
        this.processDocument(parseXml(text.getValue()).childNodes);
      }, this);

    },

 
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

       // TODO: pass properties
       var method = "process" + clazz + "Widget"
       if (method in this) {
         this[method]('test');
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
