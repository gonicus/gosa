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

      // Create action bar
      var dn_list = new qx.ui.form.VirtualSelectBox();
      var commit = new qx.ui.form.Button("Commit");
      var close = new qx.ui.form.Button("Close");
      var toggle = new qx.ui.form.ToggleButton("User defs");
      toggle.bind("value", text, "visibility", {"converter": function(inv){
          if(toggle.getValue()){
            return("visible");
          }else{
            return("hidden");
          }
        }});
      toggle.addListener("changeValue", function(){
          (toggle.getValue());
        }, this);
      var actions = new qx.ui.container.Composite(new qx.ui.layout.HBox(5));
      actions.add(toggle);
      actions.add(dn_list, {flex:1});
      actions.add(process);
      actions.add(commit);
      actions.add(close);

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

      // Add button to document at fixed coordinates
      doc.add(actions, {left: 10, top: 10, right: 10});
      doc.add(text, {left: 10, top: 40, right: 10, bottom: 50});
      //doc.add(process, {left: 10, bottom: 20});

      // Load data
      var req = new qx.bom.request.Xhr();
      req.onload = function() { text.setValue(req.responseText); }
      req.open("GET", "test.ui?c=" + Math.floor(Math.random()*100001));
      req.send();

      // Add an event listener and process known elements
      var w = null;
      var win = null;
      var _current_object = null;


      commit.addListener('click', function(){
          if(_current_object){
            _current_object.commit(function(result, error){
                if(error){
                  this.error(error.message);
                }
              }, this);
          }
        }, this);

      close.addListener('click', function(){
          if(_current_object){
            _current_object.close(function(result, error){
                if(error){
                  this.error(error.message);
                }
              }, this);
          }
        }, this);

      process.addListener("execute", function(e) {
        if (w) {
          w.destroy();
          win.destroy();
        }

        cute.proxy.ObjectFactory.openObject(function(obj){
          _current_object = obj;

          // Build widget and place it into a window
          var ui_def = undefined;
          if(toggle.getValue()){
            ui_def = text.getValue();
          }

          cute.ui.Renderer.getWidget(function(w){
            win = new qx.ui.window.Window("Object: " + obj.uuid);
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

          }, this, obj, ui_def);
        }, this, dn_list.getSelection().getItem(0));

      }, this);

    }
  }
});
