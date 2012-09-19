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

      // Stop the loading-throbber
      //throb.stop();

      // Document is the application root
      var doc = this.getRoot();

      /* Prepare screen for loading */

      // Block the gui while we are loading gui elements like 
      // tab-templates, translations etc.
      this.getRoot().setBlockerColor("#F8F8F8");
      this.getRoot().setBlockerOpacity(1);

      // Open the loading dialog which shows the loading status.
      var loadingDialog = new cute.ui.dialogs.Loading();
      loadingDialog.open();

      /* Add base gui elements */

      var pluginView = new qx.ui.tabview.TabView();
      pluginView.setBarPosition("left");

      // Create application header and toolbar
      var header = new qx.ui.basic.Atom("", "cute/logo.png");
      header.setBackgroundColor("black");
      header.setTextColor("white");
      header.setHeight(48);
      header.setPadding(5);
      header.setFont(qx.bom.Font.fromString("sans-serif 28"));
      doc.add(header, {left: 0, right: 0, top: 0});

      //TODO: add one static plugin for testing
      var search = new cute.view.Search;
      var tree = new cute.view.Tree;
      var work = new cute.view.Workflows;
      var settings = new cute.view.Settings;
      pluginView.add(search);
      pluginView.add(tree);
      pluginView.add(work);
      pluginView.add(settings);

      // Initialize websocket messaging
      var messaging = cute.io.WebSocket.getInstance();
      messaging.reconnect();

      doc.add(pluginView, {left: 0, right: 0, top: 50, bottom: 0});

      // Hide Splash - initialized by index.html
      var splash = document.getElementById("splash");
      if (splash != null) {
        splash.style.visibility = 'hidden';
      }

      // Base settings
      var theme = cute.Config.getTheme();
      var locale;

      if (cute.Config.locale) {
          locale = cute.Config.locale;
      } else {
        locale = qx.bom.client.Locale.getLocale();
        var variant = qx.bom.client.Locale.getVariant();
        if (locale && variant) {
            locale = locale + "-" + variant;
        }
      }
    
      // Enforce login
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(result, error) {
        if (error) {
          this.error("can't determine session user: " + error);
          new cute.ui.dialogs.Error(this.tr("Can't determine session user") + ": " + error).open();
          cute.Session.user = null;
        } else {

          // This list contains all loading jobs that need to be
          // processed until the gui gets visible again.
          var queue = [];

          // Add a translation prefetch job.
          var translation = {}
          translation['message'] = this.tr("Loading translation");
          translation['context'] = this;
          translation['params'] = ["getTemplateI18N", locale, theme];
          translation['func'] = function(result, error){
              if (error) {
                this.error("Can't fetch translation catalog: " + error);
                new cute.ui.dialogs.Error(this.tr("Can't fetch translation catalog") + ": " + error).open();
              } else {
                var lm = qx.locale.Manager.getInstance();
                lm.addTranslation(qx.locale.Manager.getInstance().getLocale(), result);
                cute.Session.user = result;
              }
            }
          queue.push(translation);

          // Add prefetching of the gui templates - one job per object-type.

          // Request a list of all available object-types to be able
          // to prefetch their gui-templates.
          var that = this;
          rpc.cA(function(result, error){

              // This method creates a loading-queue entry
              // which loads the gui-templates for the given
              // object type
              // (This needs to a closure, due to the fact that 
              // 'item' will change in the loop...)
              var addFunc = function(name){
                  var data = {};
                  data['message'] = that.tr("Loading %1 template", name);
                  data['context'] = this;
                  data['params'] = ["getGuiTemplates", name, theme];
                  data['func'] = function(templates, error){
                      cute.Cache.gui_templates[name] = templates;
                    }
                  return(data);
                }

              // Append a queue entry for each kind of object.
              for(var item in result){
                queue.push(addFunc(result[item])); 
              }

              // Start the queue processing now
              this.__handleQueue(queue, loadingDialog);

            }, this, "getAvailableObjectNames");

        }
      }, this, "getSessionUser");
    },

    /* Handles the loading queue and hides the gui untill
     * all jobs are processed.
     * */
    __handleQueue: function(data, dialog){
      if(data.length){
        var item = data.pop();
        this.__triggerQueue(item, data, dialog);
      }else{
        this.getRoot().setBlockerColor("#000000");
        this.getRoot().setBlockerOpacity(0.5);
        dialog.close();
      }
    },

    /* Process a single loading queue entry.
     * */
    __triggerQueue: function(item, data, dialog){
      dialog.setLabel(item['message']);
      var callback = function(result, error){

          // Call the original callback method
          item['func'].apply(item['context'], [result, error]);

          // .. and trigger the queue processor.
          this.__handleQueue(data, dialog);
        }

      var params = [callback, this].concat(item['params']);
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA.apply(rpc, params);
    }
  }
});
