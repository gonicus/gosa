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
      if(document.location.href.match("clacks-server")){
        var dn = "cn=phone Huhu,ou=people,dc=example,dc=net";
      }else{
        var dn = "cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de";
      }

      // Create a button
      var process = new qx.ui.form.Button("View...");
      var text = new qx.ui.form.TextArea();
      text.setWrap(false);

      // Create action bar
      var dn_field = new qx.ui.form.TextField(dn);
      var commit = new qx.ui.form.Button("Commit");
      var close = new qx.ui.form.Button("Close");
      dn_field.set({allowGrowX: true});
      var actions = new qx.ui.container.Composite(new qx.ui.layout.HBox(5));
      actions.add(dn_field, {flex:1});
      actions.add(process);
      actions.add(commit);
      actions.add(close);

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
        	  cute.ui.Renderer.getWidget(function(w){
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

            }, this, obj, text.getValue());
        }, this, dn_field.getValue());

      }, this);

    }
  }
});
