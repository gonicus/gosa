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
    search: null,
    tree: null,
    work: null,
    settings: null,

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
        qx.dev.Profile;  // jshint ignore:line

        // support native logging capabilities, e.g. Firebug for Firefox
        qx.log.appender.Native;  // jshint ignore:line
        // support additional cross-browser console. Press F7 to toggle visibility
        qx.log.appender.Console;  // jshint ignore:line

        // Include debug object to enable disposer level debugging
        qx.dev.Debug;  // jshint ignore:line
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

      // If there're offline capabilities available, connect if we're fully
      // cached, only.
      if (window.applicationCache) {
        var appCache = window.applicationCache;
        var connecting = false;
        var updateAvailable = false;
        var that = this;

        appCache.addEventListener('cached', function() {
          connecting = true;
          that.hideSplash();
        }, false);

        appCache.addEventListener('noupdate', function() {
          connecting = true;
          that.hideSplash();
        }, false);

        appCache.addEventListener('updateready', function() {
          updateAvailable = true;
          that.showUpdateHint();
        }, false);

        if (window.applicationReady && !connecting) {
          this.hideSplash();
        }

        if (window.updateAvailable || updateAvailable) {
          this.showUpdateHint();
        }

        // Start a fallback to check if the user has disabled the cache
        var timer = qx.util.TimerManager.getInstance();
        timer.start(function(userData, timerId)
        {
          try {
            if (appCache.status == appCache.UNCACHED) {
              appCache.update();
            }
          } catch(err) {
            if (err.name == "NS_ERROR_DOM_SECURITY_ERR" ||
                err.name == "NS_ERROR_DOM_INVALID_STATE_ERR" ||
                err.message == "INVALID_STATE_ERR") {
              this.hideSplash();
            }
          }
        }, 0, this, null, 2000);
      }

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
      loadingDialog.setWidth(360);
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
      var search = this.search = new gosa.view.Search(this);
      var tree = this.tree = new gosa.view.Tree(this);
      var work = this.work = new gosa.view.Workflows(this);
      var settings = this.settings = new gosa.view.Settings(this);
      pluginView.add(search);
      pluginView.add(tree);
      pluginView.add(work);
      pluginView.add(settings);

      // Initialize SSE messaging
      var messaging = gosa.io.Sse.getInstance();
      messaging.reconnect();

      doc.add(pluginView, {left: 3, right: 3, top: 52, bottom: 4});

      // Hide Splash - initialized by index.html
      if (qx.core.Environment.get("qx.debug") || !window.applicationCache || window.location.protocol.indexOf("https") === 0) {
        this.hideSplash();
      }

      // Base settings
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
      rpc.cA("getSessionUser").then(function(userid) {

        return new qx.Promise(function(resolve, reject) {
          var jobCounter = 0;
          var allJobsStarted = false;
          gosa.Session.getInstance().setUser(userid);

          function done() {
            jobCounter--;
            if (jobCounter === 0 && allJobsStarted) {
              resolve();
            }
          }

          // retrieve possible commands/methods
          jobCounter++;
          rpc.cA("getAllowedMethods").then(function(result) {
            gosa.Session.getInstance().setCommands(result);
            done();
          }).catch(function() {
            (new gosa.ui.dialogs.Error(this.tr("Unable to receive commands."))).open();
            done();
          }, this);

          // load translation
          jobCounter++;
          loadingDialog.setLabel(this.tr("Loading translation"));
          rpc.cA("getTemplateI18N", locale)
          .then(function(result) {
            qx.locale.Manager.getInstance().addTranslation(qx.locale.Manager.getInstance().getLocale(), result);
            done();
          })
          .catch(function() {
            this.__handleRpcError(loadingDialog, this.tr("Fetching translations failed."));
            done();
          }, this);

          // Fetch base
          jobCounter++;
          loadingDialog.setLabel(this.tr("Loading base"));
          rpc.cA("getBase")
          .then(function(result) {
            gosa.Session.getInstance().setBase(result);
            done();
          })
          .catch(function() {
            this.__handleRpcError(loadingDialog, this.tr("Fetching base failed."));
            done();
          }, this);

          // Add prefetching of the gui templates - one job per object-type.

          // Request a list of all available object-types to be able
          // to prefetch their gui-templates.
          rpc.cA("getAvailableObjectNames")
          .then(function(result) {
            var promises = [];
            result.forEach(function(name) {
              jobCounter++;
              loadingDialog.setLabel(this.tr("Loading %1 templates", name));
              promises.push(rpc.cA("getGuiDialogs", name)
              .then(function(dialogs) {
                this.__checkForActionsInUIDefs(dialogs, name);

                var dialogMap = {};
                dialogs.forEach(function(dialog) {
                  dialogMap[gosa.util.Template.getDialogName(dialog)] = dialog;
                });

                gosa.data.TemplateRegistry.getInstance().addDialogTemplates(dialogMap);
                done();
              }, this)
              .catch(function() {
                this.__handleRpcError(loadingDialog, this.tr("Fetching dialog templates failed."));
                done();
              }, this));

              jobCounter++;
              promises.push(rpc.cA("getGuiTemplates", name)
              .then(function(templates) {
                this.__checkForActionsInUIDefs(templates, name);
                gosa.data.TemplateRegistry.getInstance().addTemplates(name, templates);
                gosa.util.Template.fillTemplateCache(name);
                done();
              }, this)
              .catch(function() {
                this.__handleRpcError(loadingDialog, this.tr("Fetching templates failed."));
                done();
              }, this));
              allJobsStarted = true;
              return qx.Promise.all(promises);
            }, this);
          }, this)
          .catch(qx.lang.Function.curry(this.__handleRpcError, loadingDialog, this.tr("Fetching object description failed.")));
        }, this);
      }, this)
      .then(function() {
        // all rpcs done
        this.getRoot().setBlockerColor("#000000");
        this.getRoot().setBlockerOpacity(0.5);
        loadingDialog.close();
        this.search.updateFocus();

        // Handle URL actions
        this.__handleUrl(this._history.getState());
      }, this);
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
        if(this.__actions[id].action == action){
          var act = this.__actions[id];
          act.func.apply(act.context, [action, url.split(gosa.Config.actionDelimiter), url, act.userData]);
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
      gosa.proxy.ObjectFactory.openObject(oid).then(function(obj) {
        gosa.ui.Renderer.executeAction(userData.dialog, userData.target, obj, null);
      })
      .catch(function(error) {
        new gosa.ui.dialogs.Error(error.message).open();
      });
    },

    /**
     * @lint ignoreDeprecated(confirm)
     */
    showUpdateHint : function()
    {
      var reload = confirm(this.tr("There is a new version of this application available.") + "\n\n" +
                           this.tr("Do you want to reload in order to activate it?"));

      if (reload) {
        location.reload();
      } else {
        this.hideSplash();
      }
    },

    hideSplash : function()
    {
      // Hide Splash - initialized by index.html
      var splash = document.getElementById("splash");
      if (splash !== null || splash !== undefined) {
        splash.style.visibility = 'hidden';
      }
    },

    __handleRpcError: function(loadingDialog, message) {
      var d = new gosa.ui.dialogs.Error(message);
      d.open();
      d.addListener("close", function(){
        loadingDialog.open();
        gosa.Session.getInstance().logout();
      }, this);
    }
  }
});
