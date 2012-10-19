/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

/**
 * This is the main application class of your custom application "gosa"
 */

qx.Class.define("gosa.Application",
{
  extend : qx.application.Standalone,

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {

    __actions: null,

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

      this.__actions = [];

      // Enable logging in debug variant
      if (qx.core.Environment.get("qx.debug"))
      {
        // support native logging capabilities, e.g. Firebug for Firefox
        qx.log.appender.Native;
        // support additional cross-browser console. Press F7 to toggle visibility
        qx.log.appender.Console;

        // Include debug object to enable disposer level debugging
        qx.dev.Debug;
      }

      /*
      -------------------------------------------------------------------------
        Create basic tabbed clacks view
      -------------------------------------------------------------------------
      */

      // Optionally register protocol handler for clacks
      //var reg_path = window.location.origin + window.location.pathname;
      //if (navigator.registerProtocolHandler) {
      //  navigator.registerProtocolHandler('web+gosa', reg_path + '#%s', this.tr('GOsa protocol handler'));
      //}

      // Document is the application root
      var doc = this.getRoot();
      doc.setDecorator("background");

      /* Prepare screen for loading */

      // Block the gui while we are loading gui elements like 
      // tab-templates, translations etc.
      doc.setBlockerColor("#F8F8F8");
      doc.setBlockerOpacity(1);

      // Open the loading dialog which shows the loading status.
      var loadingDialog = new gosa.ui.dialogs.Loading();
      loadingDialog.open();

      /* Add base gui elements */

      var pluginView = new qx.ui.tabview.TabView();
      pluginView.setBarPosition("left");

      // Create application header and toolbar
      //
      var header = new gosa.ui.Header();
      doc.add(header, {left: 0, right: 0, top: 0});
      gosa.Session.getInstance().bind("cn", header, "loggedInName");

      //TODO: remove static view registration later on
      var search = new gosa.view.Search;
      var tree = new gosa.view.Tree;
      var work = new gosa.view.Workflows;
      var settings = new gosa.view.Settings;
      pluginView.add(search);
      pluginView.add(tree);
      pluginView.add(work);
      pluginView.add(settings);

      // Initialize websocket messaging
      var messaging = gosa.io.WebSocket.getInstance();
      messaging.reconnect();

      doc.add(pluginView, {left: 3, right: 3, top: 52, bottom: 4});

      // Hide Splash - initialized by index.html
      var splash = document.getElementById("splash");
      if (splash != null) {
        splash.style.visibility = 'hidden';
      }

      // Base settings
      var theme = gosa.Config.getTheme();
      var locale = gosa.Tools.getLocale();

      // Back button and bookmark support
      this._history = qx.bom.History.getInstance();
      this._history.addListener("changeState", function(e){this.__handleUrl(e.getData());}, this);

      // Register openObject action to allow to open object using urls
      this.addUrlAction("openObject", function(action, urlParts){
          search.openObject(urlParts[1]);
        }, this);

   
      // Enforce login
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA(function(userid, error) {
        if (error) {
          loadingDialog.close();
          var d = new gosa.ui.dialogs.Error(this.tr("Insufficient permissions!"));
          d.open();
          d.addListener("close", function(){
              loadingDialog.open();
              gosa.Session.getInstance().logout();
            }, this);
        } else {
          gosa.Session.getInstance().setUser(userid);

          // This list contains all loading jobs that need to be
          // processed until the gui gets visible again.
          var queue = [];

          // Add a translation prefetch job.
          var translation = {};
          translation['message'] = this.tr("Loading translation");
          translation['context'] = this;
          translation['params'] = ["getTemplateI18N", locale, theme];
          translation['func'] = function(result, error){
              if (error) {
                var d = new gosa.ui.dialogs.Error(this.tr("Cannot fetch translations. Insufficient permissions!"));
                d.open();
                d.addListener("close", function(){
                    loadingDialog.open();
                    gosa.Session.getInstance().logout();
                  }, this);
                return(false);
              } else {
                var lm = qx.locale.Manager.getInstance();
                lm.addTranslation(qx.locale.Manager.getInstance().getLocale(), result);
                return(true);
              }
            };
          queue.push(translation);

          // Fetch base
          var get_base = {};
          get_base['message'] = this.tr("Loading base");
          get_base['context'] = this;
          get_base['params'] = ["getBase"];
          get_base['func'] = function(result, error){
              if (error) {
                var d = new gosa.ui.dialogs.Error(this.tr("Cannot fetch base. Insufficient permissions!"));
                d.open();
                d.addListener("close", function(){
                    loadingDialog.open();
                    gosa.Session.getInstance().logout();
                  }, this);
                return(false);
              } else {
                gosa.Session.getInstance().setBase(result);
                return(true);
              }
            };
          queue.push(get_base);

          // Add prefetching of the gui templates - one job per object-type.

          // Request a list of all available object-types to be able
          // to prefetch their gui-templates.
          var that = this;
          rpc.cA(function(result, error){

              if(error){
                var d = new gosa.ui.dialogs.Error(this.tr("Cannot fetch object details. Insufficient permissions!"));
                d.open();
                d.addListener("close", function(){
                    loadingDialog.open();
                    gosa.Session.getInstance().logout();
                  }, this);
              }else{

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
                      if(error){
                        var d = new gosa.ui.dialogs.Error(this.tr("Cannot gui templates. Insufficient permissions!"));
                        d.open();
                        d.addListener("close", function(){
                            loadingDialog.open();
                            gosa.Session.getInstance().logout();
                          }, this);
                        return(false);
                      }else{
                        this.__checkForActionsInUIDefs(templates, name);
                        gosa.Cache.gui_templates[name] = templates;
                        return(true);
                      }
                    };
                    return(data);
                  };

                // Append a queue entry for each kind of object.
                for(var item in result){
                  queue.push(addFunc.apply(this, [result[item]])); 
                }

                // Start the queue processing now
                this.__handleQueue(queue, loadingDialog);
              }

            }, this, "getAvailableObjectNames");

        }
      }, this, "getSessionUser");
    },


    /* Registers a new UI-handler for the given 'action'.
     * Once the action was passed via that browsers address
     * the given 'func'tion will be called in the given context.
     */
    addUrlAction: function(action, func, context, userData){
      var item = {
        'userData': userData, 
        'action': action, 
        'context': context, 
        'func': func};
      this.__actions.push(item);
    },


    /* This method parses the given list of ui-definitions and tries
     * to find actions, that may also be triggered from the browsers
     * address bar.
     * 
     * E.g. the 'User' action 'Change_password' should also be triggerable
     * by passing the url "https://clacks-server/index.html#Change_password:UUID"
     * to the address bar.
     * 
     * This method registers an URL-handler for each found ui-action.
     */
    __checkForActionsInUIDefs: function(ui_defs, objectName){

      // Parse each template and create a 
      for(var item_id in ui_defs){
        var doc = new qx.xml.Document.fromString(ui_defs[item_id]);
        var res = doc.firstChild.getElementsByTagName("action");
        for(var i=0; i<res.length; i++){
          var action = null;
          var dialogName = null;
          var target = null;
          action = res[i].getAttribute("name").replace(/^action/, "");
          var props = res[i].getElementsByTagName("property");
          for(var e=0; e<props.length; e++){
            if(props[e].nodeName == "property" && props[e].getAttribute("name") == "dialog"){
              dialogName = props[e].getElementsByTagName("string")[0].firstChild.nodeValue;
              break;
            }
            if(props[e].nodeName == "property" && props[e].getAttribute("name") == "target"){
              target = props[e].getElementsByTagName("string")[0].firstChild.nodeValue;
              break;
            }
          }
          if(action){
            this.addUrlAction(action, this.__handleUiDefinedAction, this, {'dialog': dialogName, 'object': objectName, 'target': target});
          }
        }
      }
    },


 
    /* Checks the given url for actions and call the registrars
     * callback method - If it was registered using this.addUrlAction(). 
     */  
    __handleUrl: function(url){
      var action = url.split(gosa.Config.actionDelimiter)[0];
      var found = false;
      for(var id in this.__actions){
        if(this.__actions[id]['action'] == action){
          var act = this.__actions[id];
          act['func'].apply(act['context'], [action, url.split(gosa.Config.actionDelimiter), url, act['userData']]);
          found = true;
        }
      }
      if(found){
        this._history.setState("");
      }
    },


    /* This is an URL action-handler that performs ui-actions.
     * UI-actions are actions that are defined in the ui-templates
     * of an object. 
     * E.g. the Change_password action of the User object will
     *   open a dialog to allow password changes for the given ui.
     */
    __handleUiDefinedAction: function(action, parsed, url, userData){
      var oid = parsed[1];
      gosa.proxy.ObjectFactory.openObject(function(obj, error){
          if(error){
            new gosa.ui.dialogs.Error(error.message).open();
          }else{
            gosa.ui.Renderer.executeAction(userData['dialog'], userData['target'], obj, null);
          }
        }, this, oid);
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

        // Handle URL actions
        this.__handleUrl(this._history.getState());
      }
    },

    /* Process a single loading queue entry.
     * */
    __triggerQueue: function(item, data, dialog){
      dialog.setLabel(item['message']);
      var callback = function(result, error){

          // Call the original callback method
          if(item['func'].apply(item['context'], [result, error])){

            // .. and trigger the queue processor.
            this.__handleQueue(data, dialog);
          }
        };

      var params = [callback, this].concat(item['params']);
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA.apply(rpc, params);
    }
  }
});
