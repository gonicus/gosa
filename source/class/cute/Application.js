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
      var process = new qx.ui.form.Button("View...");
      var text = new qx.ui.form.TextArea();
      text.setWrap(false);

      // Document is the application root
      var doc = this.getRoot();

      // Add button to document at fixed coordinates
      doc.add(text, {left: 10, top: 10, right: 10, bottom: 50});
      doc.add(process, {left: 10, bottom: 20});

      // Load data
      var req = new qx.bom.request.Xhr();
      req.onload = function() { text.setValue(req.responseText); }
      req.open("GET", "test.ui?c=" + Math.floor(Math.random()*100001));
      req.send();

      // Add an event listener and process known elements
      var w = null;
      var win = null;
      process.addListener("execute", function(e) {
        if (w) {
          w.destroy();
	  win.destroy();
	}

      cute.proxy.ObjectFactory.openObject(function(obj){

          // Build widget and place it into a window
      	  w = cute.ui.Renderer.getWidget(obj, text.getValue());
      	  win = new qx.ui.window.Window(w.getTitle_());
      	  win.setModal(true);
      	  win.setLayout(new qx.ui.layout.VBox(10));
      	  win.add(w);
      	  win.open();
      
          // Position window as requested
      	  var props = w.getProperties_();
      	  if (props['geometry']) {
      	    doc.add(win, {
      	  	  left: parseInt(props['geometry']['rect']['x']),
      	  	  top: parseInt(props['geometry']['rect']['y'])});
      	  } else {
      	    doc.add(win, {left: 0, top: 0});
          }

        }, this, "cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de");

      }, this);

    }
  }
});
