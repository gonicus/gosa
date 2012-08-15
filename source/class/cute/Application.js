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
        Create basic tabbed clacks view
      -------------------------------------------------------------------------
      */

      // Document is the application root
      var doc = this.getRoot();
      this.getRoot().setBlockerColor("#000000");
      this.getRoot().setBlockerOpacity(0.5);
      var pluginView = new qx.ui.tabview.TabView();
      pluginView.setBarPosition("left");

      // Create application header and toolbar
      var header = new qx.ui.basic.Atom("Logo");
      header.setBackgroundColor("black");
      header.setTextColor("white");
      header.setHeight(48);
      header.setPadding(5);
      header.setFont(qx.bom.Font.fromString("sans-serif 28"));
      doc.add(header, {left: 0, right: 0, top: 0});

      //TODO: add one static plugin for testing
      var search = new cute.view.Search;
      pluginView.add(search);

      // Initialize websocket messaging
      var messaging = cute.io.WebSocket.getInstance();
      messaging.reconnect();

      doc.add(pluginView, {left: 0, right: 0, top: 50, bottom: 0});

      // Hide Splash - initialized by index.html
      var splash = document.getElementById("splash");
      if (splash != null) {
        splash.style.visibility = 'hidden';
      }
    }
  }
});
