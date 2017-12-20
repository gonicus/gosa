/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

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
     STATICS
  *****************************************************************************
  */
  statics : {
    instance: null,

    showPage: function(name) {
      if (this.instance) {
        this.instance.showPage(name);
      }
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
    __actions: null,
    __desktop: null,
    __tabView: null,

    showPage: function(name) {
      var pageInstance = gosa.view[qx.lang.String.firstUp(name)] ? gosa.view[qx.lang.String.firstUp(name)].getInstance() : null;
      if (pageInstance) {
        this.__tabView.setSelection([pageInstance]);
      } else {
        this.error(this.tr("Page %1 not found", name));
      }
    },

    /**
     * This method contains the initial application code and gets called
     * during startup of the application
     *
     * @lint ignoreDeprecated(alert)
     */
    main : function()
    {
      // Add the context menu mixin to the Table class
      qx.Class.include(qx.ui.table.Table, qx.ui.table.MTableContextMenu);

      // Call super class
      this.base(arguments);
      this.self(arguments).instance = this;

      // patch handler for xsrf
      qx.Class.patch(com.zenesis.qx.upload.XhrHandler, gosa.upload.MXhrHandler);

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
        Create basic tabbed gosa view
      -------------------------------------------------------------------------
      */

      // catch all click events to catch web+gosa:// protocol links
      window.onclick = function(ev) {
        if (ev.target.tagName.toLowerCase() === "a" && qx.bom.element.Attribute.get(ev.target, "href")) {
          var url = qx.bom.element.Attribute.get(ev.target, "href").replace(/<\/?b>/g, '');
          if (url.startsWith("web+gosa://")) {
            var parts = qx.util.Uri.parseUri(url);
            var action = parts.query;
            var dn = parts.host;
            var extension = parts.path.startsWith("/") ? parts.path.substring(1) : parts.path;

            if (action === "edit") {
              var qxWidget = qx.ui.core.Widget.getWidgetByElement(ev.target);
              while (!(qxWidget instanceof gosa.ui.SearchListItem)) {
                qxWidget = qxWidget.getLayoutParent();
                if (!qxWidget) {
                  break;
                }
              }
              if (qxWidget) {
                qxWidget.setIsLoading(true);
              }
              gosa.ui.controller.Objects.getInstance().openObject(dn).then(function(widget) {
                if (qxWidget) {
                  qxWidget.setIsLoading(false);
                }
                var context = widget.getController().getContextByExtensionName(extension);
                if (context) {
                  widget.openTab(context);
                }
              });
            } else {
              this.warning("unhandled action type: ", action);
            }

            ev.preventDefault();
            ev.stopPropagation();
          }
        }
      };

      // Base settings
      var locale = gosa.Tools.getLocale();
      qx.io.PartLoader.require([locale], function() {
        // Open the loading dialog which shows the loading status.
        var loadingDialog = new gosa.ui.dialogs.Loading();
        loadingDialog.open();

        /* Add base gui elements */

        var pluginView = this.__tabView = new qx.ui.tabview.TabView();
        pluginView.setBarPosition("left");
        var desktop = gosa.ui.controller.Objects.getInstance().getDesktop();
        desktop.add(pluginView, {edge: 0});


        // Create application header and toolbar
        //
        var header = gosa.ui.Header.getInstance();
        doc.add(header, {left: 0, right: 0, top: 0});
        gosa.Session.getInstance().bind("cn", header, "loggedInName");
        gosa.Session.getInstance().bind("imageURL", header, "imageURL");

        var search = gosa.view.Search.getInstance();
        var dashboard = gosa.view.Dashboard.getInstance();
        var tree = gosa.view.Tree.getInstance();
        var work = gosa.view.Workflows.getInstance();
        var settings = gosa.view.Settings.getInstance();

        pluginView.add(search);
        pluginView.add(dashboard);
        pluginView.add(tree);
        pluginView.add(work);
        pluginView.add(settings);

        doc.add(desktop, {left: 3, right: 3, top: 48, bottom: 4});

        // Hide Splash - initialized by index.html
        if (qx.core.Environment.get("qx.debug") || window.applicationCache || window.location.protocol.indexOf("https") === 0) {
          this.hideSplash();
        }

        // Back button and bookmark support
        this._history = qx.bom.History.getInstance();
        this._history.addListener("changeState", function(e){this.__handleUrl(e.getData());}, this);

        // Register openObject action to allow to open object using urls
        this.addUrlAction("openObject", function(action, urlParts){
          gosa.ui.controller.Objects.getInstance().openObject(urlParts[1]);
        }, this);

        var req = qx.util.Uri.parseUri(window.location.href);
        if (req.queryKey.pwruid) {
          // password recovery request -> open dialog
          var dialog = new gosa.ui.dialogs.PasswordRecovery("questions", {
            'uuid': req.queryKey.pwruid,
            'uid': req.queryKey.uid
          });
          dialog.addListener("close", function() {
            window.location.href = window.location.href.split("?")[0];
          }, this);
          dialog.open();
          return;
        }

        // Initialize SSE messaging
        var messaging = gosa.io.Sse.getInstance();
        messaging.reconnect();

        // Enforce login
        var rpc = gosa.io.Rpc.getInstance();
        rpc.cA("getSessionUser").then(function(userid) {

          gosa.Session.getInstance().setUser(userid);

          var promises = [];

          // retrieve possible commands/methods
          promises.push(
          rpc.cA("getAllowedMethods").then(function(result) {
            gosa.Session.getInstance().setCommands(result);
          }, function() {
            (new gosa.ui.dialogs.Error(qx.locale.Manager.tr("Unable to receive commands."))).open();
          })
          );

          // load the setting handler information from backend
          gosa.data.SettingsRegistry.load();

          // load translation
          promises.push(
          rpc.cA("getTemplateI18N", locale)
          .then(function(result) {
            qx.locale.Manager.getInstance().addTranslation(qx.locale.Manager.getInstance().getLocale(), result);
          }, this)
          .catch(function(error) {
            this.error(error);
            this.__handleRpcError(loadingDialog, this.tr("Fetching translations failed."));
          }, this)
          );

          // Fetch base
          promises.push(
          rpc.cA("getBase")
          .then(function(result) {
            gosa.Session.getInstance().setBase(result);
          }, this)
          .catch(function(error) {
            this.error(error);
            this.__handleRpcError(loadingDialog, this.tr("Fetching base failed."));
          }, this)
          );

          // Add prefetching of the gui templates - one job per object-type.

          // Request a list of all available object-types to be able
          // to prefetch their gui-templates.
          promises.push(
          rpc.cA("getAvailableObjectNames")
          .then(function(result) {
            var dialogPromises = [];
            var templatePromises = [];
            var names = [];
            result.forEach(function(name) {
              dialogPromises.push(rpc.cA("**getGuiDialogs", name));
              templatePromises.push(rpc.cA("**getGuiTemplates", name));
              names.push(name);
            }, this);
            return qx.Promise.all([names, qx.Promise.all(dialogPromises), qx.Promise.all(templatePromises)]);
          }, this)
          .catch(function(error) {
            this.error(error);
            this.__handleRpcError(loadingDialog, this.tr("Fetching object description failed."));
          }, this)
          .spread(function(names, dialogs, templates) {
            names.forEach(function(name, index) {
              this.__checkForActionsInUIDefs(dialogs[index], name);

              var dialogMap = {};
              dialogs[index].forEach(function(dialog) {
                dialogMap[gosa.util.Template.getDialogName(dialog)] = dialog;
              });

              gosa.data.TemplateRegistry.getInstance().addDialogTemplates(dialogMap);

              this.__checkForActionsInUIDefs(templates[index], name);
              gosa.data.TemplateRegistry.getInstance().addTemplates(name, templates[index]);
              gosa.util.Template.fillTemplateCache(name);
            }, this);
          }, this)
          .catch(function(error) {
            this.error(error);
            this.__handleRpcError(loadingDialog, this.tr("Fetching templates failed."));
          }, this)
          );
          return qx.Promise.all(promises);
        }, this)
        .then(function() {
          // all rpcs done
          this.getRoot().setBlockerColor("#000000");
          this.getRoot().setBlockerOpacity(0.5);
          loadingDialog.close();
          gosa.view.Search.getInstance().updateFocus();

          // Handle URL actions
          this.__handleUrl(this._history.getState());

          gosa.io.Rpc.getInstance().setCollectCommands(false);
        }, this)
        .catch(function(error) {
          // getSessionUser failed
          this.error(error);
          this.__handleRpcError(loadingDialog, error);
        }, this);
      }, this);

      // Document is the application root
      var doc = this.getRoot();
      doc.setDecorator("background");

      // Block the gui while we are loading gui elements like
      // tab-templates, translations etc.
      doc.setBlockerColor("lightgray-dark");
      doc.setBlockerOpacity(1);
    },

    /**
     * Overloaded close method, closes open objects
     */
    close : function() {
      // close all open objects, before the application unloads
      gosa.ui.controller.Objects.getInstance().closeAllObjects();
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
     * by passing the url "https://gosa-server/index.html#Change_password:UUID"
     * to the address bar.
     *
     * This method registers an URL-handler for each found ui-action.
     */
    __checkForActionsInUIDefs: function(ui_defs, objectName){

      // Parse each template and create a
      for(var item_id in ui_defs){
        var template = qx.lang.Json.parse(ui_defs[item_id]);
        if (template && template.extensions && template.extensions.actions) {
          var res = template.extensions.actions;
          for (var i = 0; i < res.length; i++) {
            var action = res[i].name.replace(/^action/, "");
            var dialogName = res[i].dialog;
            var target = res[i].target;
            if (action) {
              this.addUrlAction(action, this.__handleUiDefinedAction, this, {
                'dialog' : dialogName,
                'object' : objectName,
                'target' : target
              });
            }
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


    /**
     * This is an URL action-handler that performs ui-actions.
     * UI-actions are actions that are defined in the ui-templates
     * of an object.
     * E.g. the Change_password action of the User object will
     *   open a dialog to allow password changes for the given ui.
     */
    __handleUiDefinedAction: function(action, parsed, url, userData){
      var oid = parsed[1];
      gosa.proxy.ObjectFactory.openObject(oid).then(function(obj) {
        gosa.engine.ExtensionManager.getInstance().handleExtension("actions", [userData], obj, null);
        // gosa.ui.Renderer.executeAction(userData.dialog, userData.target, obj, null);
      })
      .catch(function(error) {
        new gosa.ui.dialogs.Error(error).open();
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

    __handleRpcError: function(loadingDialog, error) {
      var d = new gosa.ui.dialogs.Error(error);
      d.open();
      d.addListener("close", function(){
        loadingDialog.open();
        gosa.Session.getInstance().logout()
        .catch(function(error) {
          this.__handleRpcError(loadingDialog, error)
        }, this);
      }, this);
    }
  }
});
