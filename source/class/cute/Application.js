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
      var process = new qx.ui.form.Button(this.tr("Open") + "...");

      // Create action bar
      var dn_list = new qx.ui.form.VirtualSelectBox();
      var actions = new qx.ui.container.Composite(new qx.ui.layout.HBox(5));
      actions.add(dn_list, {flex:1});
      actions.add(process);

      // Collect all user dns 
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(result, error){
        if(!error){
          var base = result;
          rpc.cA(function(result, error){
              var list = new qx.data.Array();
              for(var i=0;i<result.length;i++){
                list.push(result[i]['User']['DN'][0]);
              }
              dn_list.setModel(list);
            }, this, "search", "SELECT User.* BASE User SUB \"" + base + "\" ORDER BY User.uid");
          }
        }, this, "getBase");

      // Document is the application root
      var doc = this.getRoot();

      // Initialize websocket messaging
      var messaging = cute.io.WebSocket.getInstance();
      messaging.reconnect();

      // Add button to document at fixed coordinates
      doc.add(actions, {left: 10, top: 10, right: 10});

      var windowManager = new qx.ui.window.Manager();
      var desktop = new qx.ui.window.Desktop(windowManager);
      desktop.set({decorator: "main", backgroundColor: "background-pane"});
      doc.add(desktop, {left: 10, top: 45, right: 10, bottom: 10});

      // Add an event listener and process known elements
      process.addListener("execute", function(e) {
        var w = null;
        var win = null;
        var _current_object = null;

        cute.proxy.ObjectFactory.openObject(function(obj){
          _current_object = obj;

          // Build widget and place it into a window
          var ui_def = undefined;

          cute.ui.Renderer.getWidget(function(w){
            win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.uuid);
            win.setLayout(new qx.ui.layout.VBox(10));
            win.add(w);
            win.open();

            // See http://bugzilla.qooxdoo.org/show_bug.cgi?id=1770
            win.setShowMinimize(false);

            w.addListener("done", function(){
              w.destroy();
              win.destroy();
            }, this);

            win.addListener("close", function(){
              obj.close();
              w.destroy();
              win.destroy();
            }, this);

            // Position window as requested
            var props = w.getProperties_();
            desktop.add(win, {left: 5, top: 5});

          }, this, obj, ui_def);
        }, this, dn_list.getSelection().getItem(0));

      }, this);

    }
  }
});
