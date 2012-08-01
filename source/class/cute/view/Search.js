/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(cute/*)

************************************************************************ */

qx.Class.define("cute.view.Search",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    // Call super class
    this.base(arguments, "", "resource/cute/icons/search.png");

    this._excludeChildControl("label");
    this.setLayout(new qx.ui.layout.Canvas());

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
          }, this, "search", "SELECT User.* BASE User SUB \"" + base + "\" ORDER BY User.sn");
        }
      }, this, "getBase");

    // Initialize websocket messaging
    var messaging = cute.io.WebSocket.getInstance();
    messaging.reconnect();

    // Add button to document at fixed coordinates
    this.add(actions, {left: 10, top: 0, right: 10});

    var windowManager = new qx.ui.window.Manager();

    // Add an event listener and process known elements
    process.addListener("execute", function(e) {
      var w = null;
      var win = null;
      var _current_object = null;

      cute.proxy.ObjectFactory.openObject(function(obj){
        _current_object = obj;

        // Build widget and place it into a window
        cute.ui.Renderer.getWidget(function(w){
          win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.uuid);
          win.setLayout(new qx.ui.layout.VBox(10));
          win.add(w);
          win.addListener("appear", win.center, win);
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
          var doc = qx.core.Init.getApplication().getRoot();
          doc.add(win);

        }, this, obj);
      }, this, dn_list.getSelection().getItem(0));

    }, this);
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
  }
});
